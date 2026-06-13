.DEFAULT_GOAL := help
COMPOSE_BASE := docker compose -f infrastructure/docker-compose.yml
# Dev: publish backend:8000 + frontend:3000 on the host; optional compose-nginx :8080.
COMPOSE      := $(COMPOSE_BASE) \
	-f infrastructure/docker-compose.dev-host-ports.yml \
	--profile compose-nginx
# Optional `infrastructure/compose.host-ports.env` sets HOST_PORT_BACKEND / HOST_PORT_FRONTEND.
COMPOSE_PROD_ENV := $(wildcard infrastructure/compose.host-ports.env)
COMPOSE_PROD := $(COMPOSE_BASE) \
	$(if $(COMPOSE_PROD_ENV),--env-file $(COMPOSE_PROD_ENV),) \
	-f infrastructure/docker-compose.prod.yml

.PHONY: help up down restart logs ps build shell-backend shell-worker shell-db migrate seed test test-backend lint frontend-build prod-up prod-down prod-logs prod-migrate

help:  ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

## ---- dev (compose) ----
up:           ## start the dev stack (rebuild if needed)
	$(COMPOSE) up --build -d
up-no-nginx:  ## start dev stack without docker nginx
	$(COMPOSE_BASE) -f infrastructure/docker-compose.dev-host-ports.yml up --build -d
down:         ## stop the dev stack (keeps volumes)
	$(COMPOSE) down
restart:      ## restart all services
	$(COMPOSE) restart
restart-no-nginx: ## restart dev services (no docker nginx)
	$(COMPOSE_BASE) -f infrastructure/docker-compose.dev-host-ports.yml restart
logs:         ## tail logs from all services (Ctrl-C to detach)
	$(COMPOSE) logs -f --tail=200
ps:           ## list running services
	$(COMPOSE) ps
build:        ## rebuild images without starting
	$(COMPOSE) build

## ---- shells ----
shell-backend: ## bash into the backend container
	$(COMPOSE) exec backend bash
shell-worker: ## bash into the worker container
	$(COMPOSE) exec worker bash
shell-db:     ## psql into the postgres container
	$(COMPOSE) exec postgres psql -U converter -d converter

## ---- ops ----
migrate:      ## run alembic upgrade head against the running stack
	$(COMPOSE) exec backend alembic upgrade head
seed:         ## idempotent DB seed (admin bootstrap + sample SEO content)
	$(COMPOSE) exec backend python -m app.scripts.seed

## ---- tests ----
test: test-backend ## run the full test suite
test-backend:  ## run backend pytest in a transient worker container
	$(COMPOSE) run --rm worker pytest -q tests/
lint:          ## frontend ESLint
	cd frontend && npx eslint src/

frontend-build: ## production build of the Next.js app (host-side)
	cd frontend && npx next build

## ---- production overlay ----
prod-up:      ## start the prod stack
	$(COMPOSE_PROD) up --build -d
prod-down:    ## stop the prod stack (keeps volumes)
	$(COMPOSE_PROD) down
prod-restart: ## restart the prod stack
	$(COMPOSE_PROD) restart
prod-restart-app: ## restart only prod frontend + backend
	$(COMPOSE_PROD) restart frontend backend
prod-logs:    ## tail prod logs
	$(COMPOSE_PROD) logs -f --tail=200
prod-migrate: ## alembic upgrade on prod stack (after deploy or new migrations)
	$(COMPOSE_PROD) exec backend alembic upgrade head
