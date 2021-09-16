#!/usr/bin/env false bash

function redis_cli()
{
  REDISCLI_AUTH="$(cat "${TERRA_REDIS_SECRET_FILE}")" redis-cli -h "${TERRA_REDIS_HOSTNAME}" -p "${TERRA_REDIS_PORT}" ${@+"${@}"}
}

function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    redis-server) # Run redis server
      local conf="$(mktemp -u)"
      # Set password
      printf 'requirepass %s\n' "$(cat "${TERRA_REDIS_SECRET_FILE}")" > "${conf}"
      # Set port
      echo "port ${TERRA_REDIS_PORT}" >> "${conf}"
      # Start redis
      redis-server "${conf}"
      ;;
    redis-ping) # Ping the redis server
      JUST_IGNORE_EXIT_CODES=1
      redis_cli ping
      ;;
    redis-monitor) # Monitor all messages on the redis server
      JUST_IGNORE_EXIT_CODES=1
      redis_cli monitor
      ;;
    *)
      exec "${cmd}" ${@+"${@}"}
      ;;
  esac
}