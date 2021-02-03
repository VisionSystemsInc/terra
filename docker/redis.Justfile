#!/usr/bin/env false bash

function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    redis-server) # Run redis server
      local conf="$(mktemp -u)"
      # Set password
      printf 'requirepass %s\n' "$(cat "/run/secrets/${TERRA_REDIS_SECRET}")" > "${conf}"
      # Set port
      echo "port ${TERRA_REDIS_PORT}" >> "${conf}"
      # Start redis
      redis-server "${conf}"
      ;;
    redis-ping) # Ping the redis server
      JUST_IGNORE_EXIT_CODES=1
      REDISCLI_AUTH="$(cat "/run/secrets/${TERRA_REDIS_SECRET}")" redis-cli -h "${TERRA_REDIS_HOSTNAME}" -p "${TERRA_REDIS_PORT}" ping
      ;;
    *)
      exec "${cmd}" ${@+"${@}"}
      ;;
  esac
}