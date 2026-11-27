FROM node:22-alpine AS build

ENV NUXT_TELEMETRY_DISABLED=1

WORKDIR /app

# Копируем всё сразу: postinstall-хук `nuxt prepare` требует исходники.
COPY . .

# npm install (а не ci), чтобы подтянулись platform-specific optional-зависимости
# под linux/musl, которых нет в lock-файле, собранном на Windows.
RUN npm install --no-audit --no-fund

RUN NODE_OPTIONS=--max-old-space-size=1536 npm run build

FROM node:22-alpine AS runtime

ENV NODE_ENV=production NUXT_TELEMETRY_DISABLED=1

WORKDIR /app

COPY --from=build /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
