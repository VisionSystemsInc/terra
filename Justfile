#!/usr/bin/env bash

source "${VSI_COMMON_DIR}/linux/just_files/just_env" "$(dirname "${BASH_SOURCE[0]}")"/'terra.env'

# Plugins
source "${VSI_COMMON_DIR}/linux/ask_question"
source "${VSI_COMMON_DIR}/linux/command_tools.bsh"
source "${VSI_COMMON_DIR}/linux/just_files/docker_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_files/just_docker_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_files/just_singularity_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_files/just_git_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_files/just_sphinx_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_files/just_makeself_functions.bsh"
# source "${VSI_COMMON_DIR}/linux/just_files/just_pyinstaller_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_files/just_ci_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_files/just_install_functions.bsh"
source "${VSI_COMMON_DIR}/linux/dir_tools.bsh"
source "${VSI_COMMON_DIR}/linux/python_tools.bsh"
source "${VSI_COMMON_DIR}/linux/aliases.bsh"
source "${VSI_COMMON_DIR}/linux/web_tools.bsh"

# Make terra's justfile a plugin if it is not the main Justfile
if [ "${JUSTFILE}" != "${BASH_SOURCE[0]}" ]; then
  JUST_HELP_FILES+=("${BASH_SOURCE[0]}")
else
  cd "${TERRA_TERRA_DIR}"
  # Allow terra to be run as a non-plugin too
  function caseify()
  {
    defaultify ${@+"${@}"}
  }
fi

# Always add this to the list, because of how the caseify above works
JUST_DEFAULTIFY_FUNCTIONS+=(terra_caseify)

function Terra_Pipenv()
{
  local answer_continue="${answer_continue-}"

  if [ "${TERRA_LOCAL-}" = "1" ]; then
    if [ -n "${VIRTUAL_ENV+set}" ] || [ -n "${CONDA_DEFAULT_ENV+set}" ]; then
      echo "Warning: You appear to be in a virtual/conda env" >&2
      echo "This can interfere with terra and cause unexpected consequences" >&2
      echo "Deactivate external virtual/conda envs before running just" >&2
      ask_question "Continue anyways?" answer_continue n
      if [ "${answer_continue}" == "0" ]; then
        JUST_IGNORE_EXIT_CODES=1
        echo "Exiting..." >&2
        return 1
      fi
    fi
    ${DRYRUN} env PIPENV_PIPFILE="${TERRA_PIPENV_PIPFILE-${TERRA_TERRA_DIR}/Pipfile}" "${PIPENV_EXE-${TERRA_TERRA_DIR}/build/pipenv/bin/pipenv}" ${@+"${@}"} || return $?
  else
    Just-docker-compose -f "${TERRA_TERRA_DIR}/docker-compose-main.yml" run ${TERRA_PIPENV_IMAGE-terra} pipenv ${@+"${@}"} || return $?
  fi
}

# Main function
function terra_caseify()
{
  local just_arg=$1
  shift 1
  case ${just_arg} in
    --local) # Run terra command locally
      export TERRA_LOCAL=1
      ;;

    # # terra) # Run terra core target
    #   terra_caseify terra_cmd ${@+"${@}"}
    #   # extra_args=$#
    #   ;;

    ### Building docker images ###
    terra_build) # Build Docker image
      if [ "$#" -gt "0" ]; then
        Docker compose build ${@+"${@}"}
        extra_args=$#
      else
        justify build recipes-auto "${TERRA_TERRA_DIR}/docker/"*.Dockerfile
        Docker compose -f "${TERRA_TERRA_DIR}/docker-compose-main.yml" build
        if [ "${TERRA_LOCAL-}" = "0" ]; then
          COMPOSE_FILE="${TERRA_TERRA_DIR}/docker-compose-main.yml" justify docker compose clean terra-venv
        fi
        justify terra build-services
      fi
      ;;

    ci_load) # Load images and rebuild from dockerhub cache
      justify ci load-recipes-auto "${TERRA_TERRA_DIR}/docker/terra.Dockerfile"
      justify ci load-services "${TERRA_TERRA_DIR}/docker-compose-main.yml" terra terra_pipenv ${@+"${@}"}
      # terra_pipenv is needed for `justify terra pipenv sync --dev` in terra_pep8
      extra_args=$#
      ;;

    terra_build-services) # Build services. Takes arguments that are passed to the \
                    # docker buildx bake command, such as "redis"
      Docker buildx bake -f "${TERRA_TERRA_DIR}/docker-compose.yml" ${@+"${@}"}
      extra_args=$#
      ;;

    terra_build-singular) # Build singularity images for terra
      # If a terra project calls build, it would "terra build-singular", but
      # when that same terra project calls sync, it would call it's own build
      # plus terra sync-singular, which would call this a second time. This is
      # a check to make sure build-singular is only done once.
      if [ "${TERRA_JUST_BUILD_SINGULAR-}" = "1" ]; then
        return 0
      fi
      TERRA_JUST_BUILD_SINGULAR=1

      justify build recipes-auto "${TERRA_CWD}"/docker/*.Dockerfile
      justify terra build-services

      for image in "${TERRA_DOCKER_REPO}:redis_${TERRA_USERNAME}"; do
        justify singular-compose import redis "${TERRA_DOCKER_REPO}:redis_${TERRA_USERNAME}"
      done
      ;;

    terra_up-redis-singular) # Start redis in singularity
      mkdir -p "${TERRA_REDIS_DIR_HOST_SINGULAR}"
      justify singular-compose instance start redis
      ;;

    terra_redis-ping-singular) # Ping the redis server, to see if it is up
      SINGULARITY_IGNORE_EXIT_CODES=1
      justify singular-compose exec redis bash /vsi/linux/just_files/just_entrypoint.sh redis-ping
      ;;

    terra_down-redis-singular) # Stop redis in singularity
      justify singular-compose instance stop redis
      ;;

    ### Running containers ###
    run) # Run python module/cli in terra
      # 2 is the exit code of an error in arg parsing
      # 62 for any other terra error
      local JUST_IGNORE_EXIT_CODES=${JUST_IGNORE_EXIT_CODES-'2$|^62'}
      if [ "${JUST_RODEO-}" = "1" ]; then
        extra_args=$#
        local app_name="${1}"
        shift 1
        ${DRYRUN} "${TERRA_RUN_DIR}/${app_name}" ${@+"${@}"}
      else
        Terra_Pipenv run python -m ${@+"${@}"}
        extra_args=$#
      fi
      ;;
    run_pdb) # Run pdb module/cli in terra
      Terra_Pipenv run python -m pdb -m ${@+"${@}"}
      extra_args=$#
      ;;
    terra_run) # Run command (arguments) in terra
      local rv=0
      Terra_Pipenv run ${@+"${@}"} || rv=$?
      extra_args=$#
      return $rv
      ;;

    terra_run-nopipenv) # Run terra command not in pipenv
      if [ "${TERRA_LOCAL-}" = "1" ]; then
        ${@+"${@}"}
      else
        Just-docker-compose -f "${TERRA_CWD}/docker-compose-main.yml" run ${terra_service_name-terra} nopipenv ${@+"${@}"} || rv=$?
      fi
      extra_args=$#
      ;;

    terra_celery) # Starts a celery worker

      # node name (including node location)
      local node_name
      if [ "${TERRA_LOCAL-}" = "1" ]; then
        node_name="terra-local@%h"
      else
        node_name="terra-container@%h"
      fi

      # Untested
      if [ "${OS-}" = "Windows_NT" ]; then
        # https://www.distributedpython.com/2018/08/21/celery-4-windows/
        local FORKED_BY_MULTIPROCESSING
        export FORKED_BY_MULTIPROCESSING=1
      fi

      # We might be able to use CELERY_LOADER to avoid the -A argument
      Terra_Pipenv run python -m celery \
                              -A terra.executor.celery.app worker \
                              --loglevel="${TERRA_CELERY_LOG_LEVEL-INFO}" \
                              -n "${node_name}" \
                              ${TERRA_CELERY_WORKERS+ -c ${TERRA_CELERY_WORKERS}} \
                              -Q "$(IFS=','; echo "${TERRA_CELERY_QUEUES[*]}")" \
                              -I "$(IFS=','; echo "${TERRA_CELERY_INCLUDE[*]}")"
      ;;

    terra_celery-status) # Get the status on all celery workers currently connected
      Terra_Pipenv run python -m celery \
                              -A terra.executor.celery.app status
      ;;

    run_flower) # Start the flower server
      if ! Terra_Pipenv run python -m flower &> /dev/null; then
        justify terra pipenv sync --dev
      fi
      # Flower doesn't actually need the tasks loaded in the app, so clear it
      TERRA_CELERY_INCLUDE='[]' Terra_Pipenv run python -m celery \
                                                        -A terra.executor.celery.app flower
      ;;
    shutdown_celery) # Shuts down all celery workers on all nodes
      Terra_Pipenv run python -c "from terra.executor.celery import app; app.control.broadcast('shutdown')"
      ;;

    ### Run Debugging containers ###
    generate-redis-commander-hash) # Generate a redis commander hash
      touch "${TERRA_REDIS_COMMANDER_SECRET_FILE}"
      Docker run -it --rm --mount type=bind,source="$(real_path "${TERRA_REDIS_COMMANDER_SECRET_FILE}")",destination=/hash_file  python:3 sh -c "
        pip install bcrypt
        python -c 'if 1:
          import bcrypt,getpass
          pass1 = getpass.getpass(\"Enter a password: \")
          hash1 = bcrypt.hashpw(pass1.encode(), bcrypt.gensalt(rounds=10))
          with open(\"/hash_file\", \"wb\") as fid:
            fid.write(hash1)
        '
      "
      ;;

    terra_redis-monitor) # Monitor all messages sent/received from redis
      Just-docker-compose -f "${TERRA_CWD}/docker-compose.yml" exec redis bash /vsi/linux/just_files/just_entrypoint.sh redis-monitor
      ;;

    terra_redis-ping) # Ping the redis server, to see if it is up
      JUST_IGNORE_EXIT_CODES=1
      Just-docker-compose -f "${TERRA_CWD}/docker-compose.yml" exec redis bash /vsi/linux/just_files/just_entrypoint.sh redis-ping
      ;;

    run_redis-commander) # Run redis-commander
      if [ ! -s "${TERRA_REDIS_COMMANDER_SECRET_FILE}" ]; then
        justify generate-redis-commander-hash
      fi
      Docker compose -f "${TERRA_CWD}/docker-compose-main.yml" up -d redis-commander
      Docker compose -f "${TERRA_CWD}/docker-compose-main.yml" logs -f redis-commander
      ;;

    ### Deploy command ###
    terra_up) # Start redis (and any other services) in the background.
      Just-docker-compose -f "${TERRA_CWD}/docker-compose.yml" up -d
      ;;
    terra_down) # Stop redis (and any other services) in the background.
      Just-docker-compose -f "${TERRA_CWD}/docker-compose.yml" down
      ;;


    ### Testing ###
    terra_test) # Run unit tests
      source "${VSI_COMMON_DIR}/linux/colors.bsh"
      echo "${YELLOW}Running ${GREEN}python ${YELLOW}Tests${NC}"
      JUST_IGNORE_EXIT_CODES=1
      if [ "${#}" = "0" ]; then
        # Use bash -c So that TERRA_TERRA_DIR is evaluated correctly inside the environment
        Terra_Pipenv run env TERRA_UNITTEST=1 bash -c 'python -m unittest discover "${TERRA_TERRA_DIR}/terra"'
      else
        Terra_Pipenv run env TERRA_UNITTEST=1 python -m unittest "${@}"
      fi
      extra_args=$#
      ;;
    # Ideas
    terra_coverage) # Run coverage on terra
      local report_rcfile="${TERRA_CWD}/.coveragerc"
      if [ "${OS-}" = "Windows_NT" ]; then
        report_rcfile="${TERRA_CWD}/.coveragerc_nt"
      fi
      pushd "${TERRA_CWD}" &> /dev/null # Not needed because of a cd line above
        Terra_Pipenv run env TERRA_UNITTEST=1 bash -c "coverage run && coverage report -m --rcfile '${report_rcfile}'"
      popd &> /dev/null # but added this so an app developer would know to add it
      ;;

    # How do I know what error code causes a problem in autopep8? You don't!
    # At least not as far as I can tell.
    terra_autopep8) # Check PEP 8 compliance in ./terra using autopep8
      echo "Checking for autopep8..."
      if ! Terra_Pipenv run sh -c "command -v autopep8" &> /dev/null; then
        justify terra pipenv sync --dev
      fi

      echo "Running autopep8..."
      Terra_Pipenv run bash -c 'autopep8 --global-config "${TERRA_TERRA_DIR}/autopep8.ini" --ignore-local-config \
                                "${TERRA_TERRA_DIR}/terra"'
      ;;
    terra_flake8) # Check PEP 8 compliance in ./terra using flake8
      echo "Running flake8..."
      Terra_Pipenv run bash -c 'cd ${TERRA_TERRA_DIR};
                                flake8 \
                                "${TERRA_TERRA_DIR}/terra"'
      ;;

    terra_pep8) # Run PEP 8 tests
      justify terra autopep8 flake8
      ;;

    ### Syncing ###
    terra_sync) # Synchronize the many aspects of the project when new code changes \
          # are applied e.g. after "git checkout"
      if [ ! -e "${TERRA_CWD}/.just_synced" ]; then
        # Add any commands here, like initializing a database, etc... that need
        # to be run the first time sync is run.
        touch "${TERRA_CWD}/.just_synced"
      fi

      if [ -z "${TERRA_SKIP_DOCKER_COMPOSE_CHECK+set}" ] && ! "${DOCKER_COMPOSE[@]}" &> /dev/null; then
        source "${VSI_COMMON_DIR}/linux/colors.bsh"
        echo "${RED}The docker compose plugin does not appear to be installed.${NC}"
        echo "Please have IT install the 'docker-compose-plugin' or install a local copy in your home directory:"

        local plugin_dir=${DOCKER_CONFIG-~/.docker}/cli-plugins
        local ver=v2.20.3
        local url
        local filename=${plugin_dir}/docker-compose
        echo "${YELLOW}mkdir -p ${plugin_dir}"
        if [ "${OS-}" = "Windows_NT" ]; then
          filename=${filename}.exe
          url="https://github.com/docker/compose/releases/download/${ver}/docker-compose-windows-x86_64.exe"
        elif [[ ${OSTYPE-} = darwin* ]]; then
          if [ "${HOSTTYPE}" = "x86_64" ]; then
            url="https://github.com/docker/compose/releases/download/${ver}/docker-compose-darwin-x86_64"
          else
            url="https://github.com/docker/compose/releases/download/${ver}/docker-compose-darwin-aarch64"
          fi
        else
          url="https://github.com/docker/compose/releases/download/${ver}/docker-compose-linux-x86_64"
        fi
        echo "curl -Lo \"${filename}\" \"${url}\""
        echo "chmod 755 \"${filename}\""
        echo "${NC}"
        JUST_IGNORE_EXIT_CODES=1
        "${DOCKER_COMPOSE[@]}"
      fi

      justify git_submodule-update # For those users who don't remember!

      if [ "${TERRA_LOCAL-}" = "0" ]; then
        COMPOSE_FILE="${TERRA_CWD}/docker-compose-main.yml" justify docker compose clean terra-venv
        justify terra sync-pipenv
        justify terra build-services
      else
        justify terra sync-pipenv
        local pipenv_dir="$(Terra_Pipenv --venv)"
      fi
      ;;

    terra_sync-singular) # Synchronize the many aspects of the project when new code changes \
                         # are applied e.g. after "git checkout" for a singularity build
      justify git_submodule-update # For those users who don't remember!
      justify terra_sync-pipenv
      if "${DOCKER_COMPOSE[@]}" &> /dev/null; then
        justify terra_build-singular
      fi
      ;;

    terra_sync-pipenv) # Synchronize the local pipenv for terra. You normally \
                       # don't call this directly
      if ! command "${PIPENV_EXE-${TERRA_CWD}/build/pipenv/bin/pipenv}" &> /dev/null; then
        add_to_local=y justify terra setup --dir "${TERRA_CWD}/build/pipenv" --download
        # since I want to continue without re-sourcing local.env
        export PATH="${TERRA_CWD}/build/pipenv/bin:${PATH}"
      fi

      if [ -z "${PYTHON_EXE+set}" ]; then
        local PYTHON_EXE=$(command -v python)
      fi
      local pipenv_args=(--python "${PYTHON_EXE}")

      TERRA_PIPENV_IMAGE=terra_pipenv Terra_Pipenv "${pipenv_args[@]}" sync ${@+"${@}"}
      extra_args=$#
      ;;

    terra_setup) # Setup pipenv using system python and/or conda
      local output_dir
      local conda_exe
      local python_exe
      local download_conda=0
      local conda_install

      : ${PYTHON_VERSION=${TERRA_PYTHON_VERSION:-3.12.9}}
      : ${PIPENV_VERSION=${TERRA_PIPENV_VERSION:-2024.4.1}}
      : ${VIRTUALENV_VERSION=${TERRA_VIRTUALENV_VERSION:-20.29.0}}

      parse_args extra_args --dir output_dir: --python python_exe: --conda conda_exe: --download download_conda --conda-install conda_install: -- ${@+"${@}"}

      if [ -z "${output_dir:+set}" ]; then
        echo "--dir must be specified" >& 2
        exit 2
      fi

      if [ -n "${conda_install:+set}" ]; then
        download_conda=1
      fi

      mkdir -p "${output_dir}"
      # relative to absolute
      output_dir="$(cd "${output_dir}"; pwd)"

      local use_conda
      local platform_bin

      if [ "${OS-}" = "Windows_NT" ]; then
        platform_bin=Scripts
      else
        platform_bin=bin
      fi

      local installer_args
      local python_activate
      local python_version
      local conda_python_extra_args

      if [ -n "${python_exe:+set}" ]; then
        :
      elif [ -n "${conda_exe:+set}" ]; then
        use_conda=1
      elif [ "${download_conda}" != "0" ]; then
        use_conda=1
      elif command -v python3 &> /dev/null; then
        python_exe="$(command -v python3)"
      elif command -v python &> /dev/null; then
        python_exe="$(command -v python)"
      else
        use_conda=1
      fi

      if [ "${use_conda-}" = "1" ]; then
        installer_args=()

        if [ "${download_conda}" != "0" ]; then
          installer_args+=("--download")
        fi
        if [ -n "${conda_install:+set}" ]; then
          installer_args+=("--conda-install" "${conda_install}")
        fi
        if [ -n "${conda_exe:+set}" ]; then
          installer_args+=("--conda" "${conda_exe}")
        fi

        # sets python_exe
        conda-python-install --dir "${output_dir}/.python" ${installer_args[@]+"${installer_args[@]}"}
      fi

      # Make sure python is 3.7 or newer
      local python_version="$("${python_exe}" --version 2>&1 | awk '{print $2}')"
      source "${VSI_COMMON_DIR}/linux/requirements.bsh"
      if ! meet_requirements "${python_version}" '>=3.7'; then
        echo "Python version ${python_version} does not meet the expected requirements" >&2
        echo "Consider adding the --download flag" >&2
        read -srn1 -d '' -p "Press any key to continue, or Ctrl+C to stop"
        echo
      fi

      installer_args=()
      if [ -n "${python_activate:+set}" ]; then
        installer_args+=("--python-activate" "${python_activate}")
      fi
      pipenv-install --python "${python_exe}" --dir "${output_dir}" ${installer_args[@]+"${installer_args[@]}"}

      local add_to_local="${add_to_local-}"
      echo "" >&2
      ask_question "Do you want to add \"${output_dir}/${platform_bin}\" to your local.env automatically?" add_to_local y
      if [ "${add_to_local}" == "1" ]; then
        echo $'\n'"PATH=\"${output_dir}/${platform_bin}:\${PATH}\"" >> "${TERRA_CWD}/local.env"
        echo "PIPENV_EXE=\"${output_dir}/${platform_bin}/pipenv\"" >> "${TERRA_CWD}/local.env"
      fi
      ;;

    terra_newapp) # Generate a new terra app. Required: --AppName for the application name \
                  # in CamelCase (e.g GenerateCatGraph), --module.path for the module path \
                  # (e.g. foobar.cat). See --help for more information.
      justify terra pipenv run python -m terra.utils.new ${@+"${@}"}
      extra_args="${#}"
      ;;

    terra_pipenv) # Run pipenv commands in Terra's pipenv container. Useful for \
                  # installing/updating pipenv packages into terra
      TERRA_PIPENV_IMAGE=terra_pipenv Terra_Pipenv ${@+"${@}"}
      extra_args=$#
      ;;

    terra_clean-all) # Delete all local volumes
      local answer_clean_all="${answer_clean_all-}"
      ask_question "Are you sure? This will remove packages not in Pipfile!" answer_clean_all
      [ "${answer_clean_all}" == "0" ] && return 1
      COMPOSE_FILE="${TERRA_CWD}/docker-compose-main.yml" justify docker compose clean terra-venv
      COMPOSE_FILE="${TERRA_CWD}/docker-compose.yml" justify docker compose clean terra-redis
      if [ "${TERRA_LOCAL-}" = "1" ]; then
        Terra_Pipenv --rm
      fi
      ;;

    terra_pyinstaller) # Deploy terra using pyinstaller
      if ! Terra_Pipenv run sh -c "command -v pyinstaller" &> /dev/null; then
        justify terra pipenv sync --dev
      fi
      local indirect
      local app_prefix
      local terra_apps
      for app_prefix in ${TERRA_APP_PREFIXES[@]+"${TERRA_APP_PREFIXES[@]}"}; do
        if [ "${app_prefix}" ==  "TERRA" ]; then
          continue
        fi
        indirect="${app_prefix}_APPS[@]"
        terra_apps=(${!indirect+"${!indirect}"})
        array_to_python_ast_list_of_strings terra_apps ${terra_apps[@]+"${terra_apps[@]}"}
        declare -x TERRA_APPS="${terra_apps}"

        TERRA_UNITTEST=1 Terra_Pipenv run pyinstaller --noconfirm "${TERRA_CWD}/freeze/terra.spec"
      done
      ;;
    #   local app_prefix
    #   local terra_rel
    #   local indirect
    #   local indirect2
    #   local terra_apps

    #   declare -x PYINSTALLER_PYTHON_VERSION=3.6.9
    #   declare -x PYINSTALLER_VERSION=3.6
    #   declare -x PYINSTALLER_IMAGE="vsiri/pyinstaller:${PYINSTALLER_PYTHON_VERSION}-${PYINSTALLER_VERSION}"

    #   justify pyinstaller build

    #   for app_prefix in ${TERRA_APP_PREFIXES[@]+"${TERRA_APP_PREFIXES[@]}"}; do
    #     indirect="${app_prefix}_CWD"

    #     local TERRA_PYINSTALLER_SRC_DIR="${TERRA_PYINSTALLER_SRC_DIR-${!indirect}}"
    #     local TERRA_PYINSTALLER_DIST_DIR="${TERRA_PYINSTALLER_DIST_DIR-${TERRA_PYINSTALLER_SRC_DIR}/dist}"

    #     indirect2="${app_prefix}_JUST_SETTINGS"
    #     indirect2="${!indirect2-${JUST_SETTINGS}}"
    #     terra_rel="$(relative_path "${!indirect}" "$(dirname "${indirect2}")")"
    #     local VSI_COMMON_JUST_SETTINGS="${VSI_COMMON_JUST_SETTINGS-/src/${terra_rel}/$(basename "${indirect2}")}"


    #     terra_rel="$(relative_path "${TERRA_CWD}" "${!indirect}")"

    #     indirect="${app_prefix}_APPS[@]"
    #     terra_apps=(${!indirect+"${!indirect}"})
    #     array_to_python_ast_list_of_strings terra_apps ${terra_apps[@]+"${terra_apps[@]}"}
    #     local DOCKER_COMPOSE_EXTRA_RUN_ARGS=(-e TERRA_APPS="${terra_apps}")

    #     local terra_venv_volume="${COMPOSE_PROJECT_NAME}_terra-venv"
    #     if ! docker inspect "${terra_venv_volume}" &> /dev/null; then
    #       echo "Volume ${terra_venv_volume} does not exist. Needs to be initialized by running a terra command :TODO" >&2
    #       JUST_IGNORE_EXIT_CODES=1
    #       return 1
    #     fi

    #     indirect2="${app_prefix}_VENV_DIR"
    #     local TERRA_PYINSTALLER_VENV_DIR="${!indirect2-}"
    #     if [ -n "${TERRA_PYINSTALLER_VENV_DIR}" ]; then
    #       TERRA_PYINSTALLER_VOLUMES=("${TERRA_PYINSTALLER_VENV_DIR}:/venv")
    #     fi

    #     justify pyinstaller run bash # pyinstaller /src/${terra_rel}/freeze/terra.spec
    #   done
    #   ;;

    terra_makeself) # Create terra makeself, then append to it
      local include_unit_tests
      parse_args extra_args --tests include_unit_tests -- ${@+"${@}"}
      local tests_args=()
      if [ "${include_unit_tests}" != "0" ]; then
        tests_args=(--tests)
      fi

      local tar_extra="--exclude=./docs --exclude=./external --exclude ./terra"

      justify makeself just-project ${tests_args[@]+"${tests_args[@]}"}
      justify makeself add-git-files "${TERRA_CWD}" "${tar_extra}"
      ;;

    ### Other ###
    # command: bash -c 'touch /tmp/watchdog; while [ -e "/tmp/watchdog" ]; do rm /tmp/watchdog; sleep 1000; done'
    # terra_vscode) # Execute vscode magic in a vscode container
    #   local container="$(docker ps -q -f "label=com.docker.compose.service=vscode" -f "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}")"
    #   if [ -z "${container}" ]; then
    #     Just-docker-compose -f "${C3D_CWD}/docker-compose.yml" up -d vscode
    #     container="$(docker ps -q -f "label=com.docker.compose.service=vscode" -f "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}")"
    #   fi
    #   local flags=""
    #   if [ -t "0" ]; then
    #     flags="-t"
    #   fi
    #
    #   # Keep the container going for another 1000 seconds and execute command
    #   # specified. $1 is sent first to be $0
    #   docker exec -u user -i ${flags} "${container}" bash -c 'touch /tmp/watchdog; ${@+"${@}"}' # ${@+"${1}"} ${@+"${@}"}
    #
    #   extra_args+=$#
    #   ;;

    terra_ipykernel) # Start a jupyter kernel in runserver. You must have run \
                     # just terra pipenv sync --dev for this to work.
      # Example kernel.json
      # {
      # "display_name": "terra",
      # "argv": [
      #  "python", "-m", "docker_proxy_kernel",
      #  "-f", "{connection_file}",
      #  "--cmd", "['{source dir}/terra/external/vsi_common/linux/just', 'terra', 'ipykernel']"
      # ],
      # "env": {"JUSTFILE": "{source dir}/terra/Justfile"},
      # "language": "python"
      # }
      Just-docker-compose -f "${TERRA_CWD}/docker-compose-main.yml" \
          run -T --service-ports ipykernel \
          pipenv run python -m ipykernel_launcher ${@+"${@}"} > /dev/null
      extra_args=$#
      ;;
    *)
      plugin_not_found=1
      ;;
  esac
  return 0
}

if ! command -v justify &> /dev/null; then caseify ${@+"${@}"};fi
