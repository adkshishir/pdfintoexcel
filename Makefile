.DEFAULT_GOAL := help
COMPOSE      := docker compose -f infrastructure/docker-compose.yml
COMPOSE_PROD := $(COMPOSE) -f infrastructure/docker-compose.prod.yml

.PHONY: help up down restart logs ps build shell-backend shell-worker shell-db migrate test test-backend lint frontend-build prod-up prod-down prod-logs prod-migrate

help:  ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

## ---- dev (compose) ----
up:           ## start the dev stack (rebuild if needed)
	$(COMPOSE) up --build -d
down:         ## stop the dev stack (keeps volumes)
	$(COMPOSE) down
restart:      ## restart all services
	$(COMPOSE) restart
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
prod-logs:    ## tail prod logs
	$(COMPOSE_PROD) logs -f --tail=200
prod-migrate: ## alembic upgrade on prod stack (after deploy or new migrations)
	$(COMPOSE_PROD) exec backend alembic upgrade head
