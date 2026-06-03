#!/usr/bin/env bash
# Adjust the PostgreSQL sequence used by users.id.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/cclilshy/sub2api/refs/heads/override/main/override/deploy/adjust-user-id-sequence.sh | bash -s -- --next 10000
#   curl -sSL https://raw.githubusercontent.com/cclilshy/sub2api/refs/heads/override/main/override/deploy/adjust-user-id-sequence.sh | bash -s -- --next 10000 --dry-run

set -euo pipefail

NEXT_VALUE=""
DRY_RUN=false
COMPOSE_FILE=""
SERVICE="postgres"

usage() {
  cat <<'USAGE'
Usage: adjust-user-id-sequence.sh --next <id> [--dry-run] [-f docker-compose.local.yml] [--service postgres]

Options:
  --next <id>       Requested next users.id value. The script will use the real
                    safe value: max(MAX(users.id)+1, <id>).
  --dry-run         Print what would be applied without changing the sequence.
  -f, --file <file> Compose file to use. Defaults to docker-compose.local.yml
                    when present, otherwise docker-compose.yml/default compose.
  --service <name>  PostgreSQL compose service name. Defaults to postgres.
  -h, --help        Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --next)
      NEXT_VALUE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -f|--file)
      COMPOSE_FILE="${2:-}"
      shift 2
      ;;
    --service)
      SERVICE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${NEXT_VALUE}" ]]; then
  echo "--next is required" >&2
  usage >&2
  exit 2
fi

if ! [[ "${NEXT_VALUE}" =~ ^[0-9]+$ ]]; then
  echo "--next must be a non-negative integer" >&2
  exit 2
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required" >&2
  exit 1
fi

compose=(docker compose)
if [[ -n "${COMPOSE_FILE}" ]]; then
  compose+=(-f "${COMPOSE_FILE}")
elif [[ -f docker-compose.local.yml ]]; then
  compose+=(-f docker-compose.local.yml)
elif [[ -f docker-compose.yml ]]; then
  compose+=(-f docker-compose.yml)
fi

if ! "${compose[@]}" ps "${SERVICE}" >/dev/null 2>&1; then
  echo "PostgreSQL service '${SERVICE}' was not found. Use --service if your compose service has another name." >&2
  exit 1
fi

psql=("${compose[@]}" exec -T "${SERVICE}" sh -ceu 'exec psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' sh)

if [[ "${DRY_RUN}" == true ]]; then
  "${psql[@]}" <<SQL
WITH current_state AS (
  SELECT
    pg_get_serial_sequence('users', 'id') AS sequence_name,
    COALESCE(MAX(id), 0)::bigint AS max_user_id
  FROM users
)
SELECT
  sequence_name,
  max_user_id,
  ${NEXT_VALUE}::bigint AS requested_next_value,
  GREATEST(max_user_id + 1, ${NEXT_VALUE}::bigint) AS resolved_next_value
FROM current_state;
SQL
  exit 0
fi

"${psql[@]}" <<SQL
BEGIN;
LOCK TABLE users IN EXCLUSIVE MODE;

WITH current_state AS (
  SELECT
    pg_get_serial_sequence('users', 'id') AS sequence_name,
    COALESCE(MAX(id), 0)::bigint AS max_user_id
  FROM users
), resolved AS (
  SELECT
    sequence_name,
    max_user_id,
    ${NEXT_VALUE}::bigint AS requested_next_value,
    GREATEST(max_user_id + 1, ${NEXT_VALUE}::bigint) AS resolved_next_value
  FROM current_state
), applied AS (
  SELECT
    sequence_name,
    max_user_id,
    requested_next_value,
    resolved_next_value,
    setval(
      sequence_name::regclass,
      CASE WHEN resolved_next_value <= 1 THEN 1 ELSE resolved_next_value - 1 END,
      resolved_next_value > 1
    ) AS sequence_last_value
  FROM resolved
)
SELECT
  sequence_name,
  max_user_id,
  requested_next_value,
  resolved_next_value,
  sequence_last_value
FROM applied;

COMMIT;
SQL
