#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then # If being sourced
  set -euE
fi
source "${VSI_COMMON_DIR}/linux/just_env" "$(dirname "${BASH_SOURCE[0]}")"/'vxl'.env
cd "${VXL_CWD}"

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
      image_name=$(docker create ${VXL_DOCKER_REPO}:vxl_${VXL_USERNAME})
      docker cp ${image_name}:/venv/Pipfile.lock "${VXL_CWD}/Pipfile.lock"
      docker rm ${image_name}
      ;;
    run_vxl) # Run vxl
      Just-docker-compose run vxl ${@+"${@}"}
      extra_args+=$#
      ;;
    compile) # Compile vxl
      Just-docker-compose run vxl compile ${@+"${@}"}
      extra_args+=$#
      ;;
    test) # Run unit tests
      Just-docker-compose run -w "${VXL_BUILD_DIR_DOCKER}" vxl ctest ${@+"${@}"}
      ;;
    sync) # Synchronize the many aspects of the project when new code changes \
          # are applied e.g. after "git checkout"
      if [ ! -e "${VXL_CWD}/.just_synced" ]; then
        # Add any commands here, like initializing a database, etc... that need
        # to be run the first time sync is run.
        touch "${VXL_CWD}/.just_synced"
      fi
      (justify _sync)
      # Add any extra steps run when syncing everytime
      ;;
    _sync)
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
