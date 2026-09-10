# syntax=docker/dockerfile:1.7
FROM node:24.21.0-alpine3.24@sha256:333f6b3eca25980d5682c26207665b93c9417786b21760b2764d5821d9704c8a AS builder
RUN apk add --no-cache --upgrade 'libcrypto3=3.5.8-r0' 'libssl3=3.5.8-r0'

WORKDIR /workspace
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run verify

FROM node:24.21.0-alpine3.24@sha256:333f6b3eca25980d5682c26207665b93c9417786b21760b2764d5821d9704c8a AS runtime
# The standalone runtime invokes node directly; keep package managers only in the builder.
RUN apk add --no-cache --upgrade 'libcrypto3=3.5.8-r0' 'libssl3=3.5.8-r0' \
    && rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack /opt/yarn-v1.22.22 \
    && rm -f /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack /usr/local/bin/yarn /usr/local/bin/yarnpkg
ARG VERSION=unknown
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown

LABEL org.opencontainers.image.title="Kira Source Admin Studio" \
      org.opencontainers.image.description="Private operator dashboard for Kira source catalogs" \
      org.opencontainers.image.source="https://github.com/kira-manga/kira-admin" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}"

ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=8080 \
    NEXT_TELEMETRY_DISABLED=1
WORKDIR /app
COPY --from=builder --chown=node:node /workspace/.next/standalone ./
COPY --from=builder --chown=node:node /workspace/.next/static ./.next/static
RUN mkdir -p .next/cache && chown -R node:node .next/cache
USER node
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
CMD ["node", "server.js"]
