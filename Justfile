#!/usr/bin/env bash

source "${VSI_COMMON_DIR}/linux/just_env" "$(dirname "${BASH_SOURCE[0]}")"/'terra.env'
cd "${TERRA_CWD}"

# Plugins
source "${VSI_COMMON_DIR}/linux/docker_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_docker_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_git_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_sphinx_functions.bsh"
source "${VSI_COMMON_DIR}/linux/colors.bsh"

function Pipenv()
{
  local rv=0
  if [[ ${TERRA_LOCAL-} == 1 ]]; then
    PIPENV_PIPFILE="${TERRA_CWD}/Pipfile" pipenv ${@+"${@}"} || rv=$?
    return $rv
  else
    justify run pipenv ${@+"${@}"} || rv=$?
    return $rv
  fi
}

# Main function
function caseify()
{
  local just_arg=$1
  shift 1
  case ${just_arg} in
    --local) # Run terra command locally
      export TERRA_LOCAL=1
      ;;
    build) # Build Docker image
      if [ "$#" -gt "0" ]; then
        Docker-compose "${just_arg}" ${@+"${@}"}
        extra_args=$#
      else
        justify build recipes-auto "${TERRA_CWD}"/docker/*.Dockerfile
        Docker-compose build
        justify docker-compose clean venv
        justify _post_build
        justify build services
      fi
      ;;
    _post_build)
      image_name=$(docker create ${TERRA_DOCKER_REPO}:terra_${TERRA_USERNAME})
      docker cp ${image_name}:/venv/Pipfile.lock "${TERRA_CWD}/Pipfile.lock"
      docker rm ${image_name}
      ;;
    python) # Run host terra python
      Pipenv run python ${@+"${@}"}
      extra_args=$#
      ;;
    run_terra) # Run command (arguments) in terra container
      local rv=0
      Just-docker-compose run terra ${@+"${@}"} || rv=$?
      extra_args=$#
      return $rv
      ;;
    ## run) # Run terra cli (first argument is which cli, "dsm" for example)
    #   # Just-docker-compose run terra ${@+"${@}"}
    #   Pipenv run python -m terra.apps.cli ${@+"${@}"}
    #   extra_args=$#
    #   ;;

    build_redis) #
      justify build services redis
      ;;
    build_services) # Build redis services
      Docker-compose -f "${TERRA_CWD}/docker-compose.yml" build ${@+"${@}"}
      extra_args=$#
      ;;
    run_redis) # Run redis
      Just-docker-compose -f "${TERRA_CWD}/docker-compose.yml" run redis ${@+"${@}"}
      extra_args=$#
      ;;

    run_celery-local) # Run celery on the host
      Pipenv run celery -A terra.executor.celery.app worker --loglevel=INFO -n local@%h
      ;;

    run_celery-docker) # Run celery in the docker
      justify run bash -c "celery -A terra.executor.celery.app worker --loglevel=INFO -n docker@%h"
      ;;

    generate-redis-browser-hash) # Generate a redis browser hash
      touch "${TERRA_REDIS_BROWSER_SECRET_FILE}"
      Docker run -it --rm --mount type=bind,source="$(real_path "${TERRA_REDIS_BROWSER_SECRET_FILE}")",destination=/hash_file  python:3 sh -c "
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
    run_redis-browser) # Run redis-browser
      if [ ! -s "${TERRA_REDIS_BROWSER_SECRET_FILE}" ]; then
        justify generate_redis_browser_hash
      fi
      Docker-compose -f "${TERRA_CWD}/docker-compose-main.yml" run --service-ports redis-browser
      ;;

    up) # Start redis (and any other services) in the background.
      Just-docker-compose -f "${TERRA_CWD}/docker-compose.yml" up -d
      ;;
    deploy) # Deploy services on a swarm
      Docker-compose -f "${TERRA_CWD}/docker-compose.yml" \
                     -f "${TERRA_CWD}/docker-compose-swarm.yml" config | \
          Docker stack deploy -c - terra
      ;;

    test) # Run unit tests
      echo "${YELLOW}Running ${GREEN}python ${YELLOW}Tests${NC}"
      # Just-docker-compose run terra python -m unittest discover "${TERRA_TERRA_DIR_DOCKER}/terra"
      Pipenv run bash -c 'python -m unittest discover "${TERRA_TERRA_DIR}/terra"'
      extra_args=$#
      ;;
    pep8) # Check for pep8 compliance in ./terra
         Just-docker-compose run test bash -c \
          "if ! command -v autopep8 >& /dev/null; then
             pipenv install --dev;
           fi;
           autopep8 --indent-size 2 --recursive --exit-code --diff \
                    --global-config ${TERRA_TERRA_DIR_DOCKER}/autopep8.ini \
                    ${TERRA_TERRA_DIR_DOCKER}/terra"
      ;;
    pep8_local) # Check pep8 compliance without using docker
      if ! Pipenv run command -v autopep8 >& /dev/null; then
        Pipenv install --dev --keep-outdated
      fi
      Pipenv run autopep8 --indent-size 2 --recursive --exit-code --diff \
                          --global-config "${TERRA_CWD}/autopep8.ini" \
                          "${TERRA_TERRA_DIR}/terra"
      ;;
    sync) # Synchronize the many aspects of the project when new code changes \
          # are applied e.g. after "git checkout"
      if [ ! -e "${TERRA_CWD}/.just_synced" ]; then
        # Add any commands here, like initializing a database, etc... that need
        # to be run the first time sync is run.
        touch "${TERRA_CWD}/.just_synced"
      fi
      justify build
      Pipenv install --keep-outdated
      ;;
    dev_sync) # Developer's extra sync
      Pipenv install --dev --keep-outdated
      ;;
    dev_update) # Developer: Update python packages
      Pipenv install --dev
      ;;
    clean_all) # Delete all local volumes
      ask_question "Are you sure? This will remove packages not in Pipfile!" n
      justify docker-compose clean venv
      ;;

    # command: bash -c "touch /tmp/watchdog; while [ -e /tmp/watchdog ]; do rm /tmp/watchdog; sleep 1000; done"
    # vscode) # Execute vscode magic in a vscode container
    #   local container="$(docker ps -q -f "label=com.docker.compose.service=vscode" -f "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}")"
    #   if [ -z "${container}" ]; then
    #     Just-docker-compose -f "${C3D_CWD}/docker-compose.yml" up -d vscode
    #     container="$(docker ps -q -f "label=com.docker.compose.service=vscode" -f "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}")"
    #   fi
    #   local flags=""
    #   if [ -t 0 ]; then
    #     flags="-t"
    #   fi
    #
    #   # Keep the container going for another 1000 seconds and execute command
    #   # specified. $1 is sent first to be $0
    #   docker exec -u user -i ${flags} "${container}" bash -c 'touch /tmp/watchdog; ${@+"${@}"}' # ${@+"${1}"} ${@+"${@}"}
    #
    #   extra_args+=$#
    #   ;;

    ipykernel) # Start a jupyter kernel in runserver
      # Example kernel.json
      # {
      # "display_name": "terra",
      # "argv": [
      #  "python", "-m", "docker_proxy_kernel",
      #  "-f", "{connection_file}",
      #  "--cmd", "['/home/noah/git/terra/external/vsi_common/linux/just', 'ipykernel']"
      # ],
      # "env": {"JUSTFILE": "/home/noah/git/terra/Justfile"},
      # "language": "python"
      # }
      Just-docker-compose run -T --service-ports ipykernel \
          pipenv run python -m ipykernel_launcher ${@+"${@}"} > /dev/null
      extra_args=$#
      ;;
    *)
      defaultify "${just_arg}" ${@+"${@}"}
      ;;
  esac
}

if ! command -v justify &> /dev/null; then caseify ${@+"${@}"};fi
