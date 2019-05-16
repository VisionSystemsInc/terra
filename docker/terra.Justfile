#!/usr/bin/env false bash

function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    test)
      : #TODO
      ;;
    nopipenv) # Run with out pipenv
      exec "${@}"
      ;;
    *)
      exec pipenv run "${cmd}" ${@+"${@}"}
      ;;
  esac
}