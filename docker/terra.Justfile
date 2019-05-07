#!/usr/bin/env false bash

function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    # default CMD
    compile)
      mkdir -p "${TERRA_BUILD_DIR}/${TERRA_BUILD_TYPE}"
      pushd "${TERRA_BUILD_DIR}/${TERRA_BUILD_TYPE}" &> /dev/null
        if [ ! -f cmake_successfully_generated ] || [ "${TERRA_FORCE_RUN_CMAKE-}" == "1" ]; then
          cmake -G Ninja "${TERRA_SOURCE_DIR}" \
                "-DCMAKE_BUILD_TYPE=${TERRA_BUILD_TYPE}" \
                "-DCMAKE_INSTALL_PREFIX=${TERRA_INSTALL_DIR}" \
                "-DPYTHON_SITE=${TERRA_INSTALL_DIR}/lib/python3/site-packages"
          touch cmake_successfully_generated # Mark that the build files have successfully been created
        fi
        ninja
        ninja install
      popd &> /dev/null
      ;;
    test)
      :
      ;;
    pep8_nopipenv) # Run with out pipenv
      exec "${@}"
      ;;
    *)
      exec pipenv run "${cmd}" ${@+"${@}"}
      ;;
  esac
}