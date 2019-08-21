Adding Apps
===========

The main repo should be an app repo and include terra as a submodule. This will include vsi_common in terra, typically ``{terra app}/external/terra/external/vsi_common``.

The app should add Terra's ``Justfile`` as a plugin.

In order for the app to show up in the terra docker (not currently used), the app's settings file should include

.. rubric:: Example:

.. code:: bash

    TERRA_APP1_DIR=${TERRA_APP1_CWD}
    TERRA_APP1_DIR_DOCKER=/src1

    TERRA_APP2_DIR=${TERRA_APP2_CWD}
    TERRA_APP2_DIR_DOCKER=/src2

    set_temp_array TERRA_TERRA_VOLUMES "${TERRA_APP1_DIR}:${TERRA_APP1_DIR_DOCKER}" "${TERRA_APP2_DIR}:${TERRA_APP2_DIR_DOCKER}"
    TERRA_TERRA_VOLUMES=(${JUST_TEMP_ARRAY+"${JUST_TEMP_ARRAY[@]}"})

    TERRA_PYTHONPATH="${TERRA_APP1_DIR_DOCKER}:${TERRA_APP2_DIR_DOCKER}"

    : ${TERRA_CELERY_MAIN_NAME=appname}
    TERRA_CELERY_INCLUDE='["app1.tasks", "app2.tasks"]'
