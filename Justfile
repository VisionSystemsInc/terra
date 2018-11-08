#!/usr/bin/env bash

source "${VSI_COMMON_DIR}/linux/just_env" "$(dirname "${BASH_SOURCE[0]}")"/'terra'.env
cd "${TERRA_CWD}"

# Plugins
source "${VSI_COMMON_DIR}/linux/docker_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_docker_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_git_functions.bsh"

# Main function
function caseify()
{
  local just_arg=$1
  shift 1
  case ${just_arg} in
    build) # Build Docker image
      if [ "$#" -gt "0" ]; then
        Docker-compose "${just_arg}" ${@+"${@}"}
        extra_args+=$#
      else
        (justify build_recipes gosu tini vsi pipenv)
        Docker-compose build
        (justify docker-compose clean venv)
        (justify _post_build)
      fi
      ;;
    _post_build)
      image_name=$(docker create ${TERRA_DOCKER_REPO}:terra_${TERRA_USERNAME})
      docker cp ${image_name}:/venv/Pipfile.lock "${TERRA_CWD}/Pipfile.lock"
      docker rm ${image_name}
      ;;
    run_terra) # Run terra
      Just-docker-compose run terra ${@+"${@}"}
      extra_args+=$#
      ;;
    run_compile) # Run compiler
      Just-docker-compose run compile nopipenv ${@+"${@}"}
      extra_args+=$#
      ;;
    compile) # Compile terra
      Just-docker-compose run compile
      extra_args+=$#
      ;;
    test) # Run unit tests
      Just-docker-compose run -w "${TERRA_BUILD_DIR_DOCKER}/${TERRA_BUILD_TYPE}" compile nopipenv ctest ${@+"${@}"}
      ;;
    sync) # Synchronize the many aspects of the project when new code changes \
          # are applied e.g. after "git checkout"
      if [ ! -e "${TERRA_CWD}/.just_synced" ]; then
        # Add any commands here, like initializing a database, etc... that need
        # to be run the first time sync is run.
        touch "${TERRA_CWD}/.just_synced"
      fi
      Docker-compose down
      (justify git_submodule-update) # For those users who don't remember!
      (justify build)
      ;;
    clean_all) # Delete all local volumes
      ask_question "Are you sure? This will remove packages not in Pipfile!" n
      (justify docker-compose clean venv)
      ;;
    *)
      defaultify "${just_arg}" ${@+"${@}"}
      ;;
  esac
}

if ! command -v justify &> /dev/null; then caseify ${@+"${@}"};fi
