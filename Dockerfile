FROM node:22-bookworm-slim
ENV NEXT_TELEMETRY_DISABLED=1 PNPM_HOME=/pnpm
ENV PATH=/pnpm:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
RUN corepack enable && corepack prepare pnpm@9.15.3 --activate
WORKDIR /app/moonreel/moonreel-studio
COPY moonreel/moonreel-studio/package.json moonreel/moonreel-studio/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY moonreel/moonreel-studio/ ./
COPY deploy/ /app/deploy/
RUN DATABASE_URL=postgresql://build:build@127.0.0.1:5432/build MUSE2API_KEY=build-only pnpm build
ENV NODE_ENV=production STORAGE_DIR=/var/data/studio/storage NICHES_DIR=/var/data/studio/niches
EXPOSE 10000
CMD ["node", "/app/deploy/run-studio.mjs"]
