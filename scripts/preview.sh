#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
cmd=${1:-up}
case "$cmd" in up|status|logs|seed|down) ;; *) echo 'Usage: scripts/preview.sh [up|status|logs|seed|down]' >&2; exit 2;; esac
command -v docker >/dev/null || { echo 'Install Docker with Compose first.' >&2; exit 1; }
docker compose version >/dev/null
docker info >/dev/null 2>&1 || { echo 'Docker daemon unavailable.' >&2; exit 1; }
compose=(docker compose -p "${MGTS_PREVIEW_PROJECT:-mgts-preview}" -f compose.preview.yml)
case "$cmd" in
 up)
   "${compose[@]}" up --build --detach --wait --wait-timeout 300
   "${compose[@]}" ps
   printf 'Ready: http://127.0.0.1:%s/ (isolated preview; real API; worker disabled)\n' "${MGTS_PREVIEW_PORT:-3300}"
   ;;
 seed) "${compose[@]}" exec -T backend python seed.py ;;
 status) "${compose[@]}" ps ;;
 logs) "${compose[@]}" logs --tail 100 ;;
 down) "${compose[@]}" down; echo 'Stopped; data volumes preserved.' ;;
esac
