#!/usr/bin/env false bash

function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    redis-server) # Run redis server
      local conf="$(mktemp -u)"
      echo -n "requirepass " | cat - "/run/secrets/${TERRA_REDIS_SECRET}" > "${conf}"
      redis-server "${conf}"
      ;;
    *)
      exec "${cmd}" ${@+"${@}"}
      ;;
  esac
}