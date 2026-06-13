# Production frontend image: build the Next.js app, then run `next start`.
# Dev compose uses node:20-alpine + `npm run dev` directly with a bind mount;
# this image is for prod compose / standalone deploys.

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Build with the same NEXT_PUBLIC_API_BASE_URL that runtime will use
# (NEXT_PUBLIC_* vars are inlined at build time per Next.js 16 docs).
ARG NEXT_PUBLIC_API_BASE_URL=/api
ARG NEXT_PUBLIC_GA_MEASUREMENT_ID=
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_GA_MEASUREMENT_ID=$NEXT_PUBLIC_GA_MEASUREMENT_ID
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/public         ./public
COPY --from=builder /app/.next          ./.next
COPY --from=builder /app/node_modules   ./node_modules
COPY --from=builder /app/package.json   ./package.json
EXPOSE 3000
CMD ["npm", "run", "start", "--", "-p", "3000", "-H", "0.0.0.0"]
