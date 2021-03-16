==========
Terra Apps
==========

An app in terra consists of 6 layers

#. A CLI is typically a ``__main__.py``. The main goal of an CLI is to setup settings and call the next layer, a workflow.

  .. rubric:: Example:

  .. code:: python

    from terra import settings

    def main(args=None):
      args = get_parser().parse_args(args)

      # settings
      env['TERRA_SETTINGS_FILE'] = args.settings_file
      settings.add_templates(example_templates)

      # Run workflow
      from .workflows import ExampleWorkflow
      ExampleWorkflow().example()

    if __name__ == "__main__":
      main()

2. The next layer is a workflow. A workflow lays out the order of services (often via stages) to be called:

  .. rubric:: Example:

  .. code:: python

     from terra.compute import compute

     class ExampleWorkflow:
       def example(self):
         compute.run('example.services.example1')

3. A stage is an optional but often utilized part of a workflow. Instead of calling services directly from the workflow, the workflow calls methods that have a ``@resumable`` decorator on them, these functions are made resumable and skip-able. Stages are useful as they let you rerun a workflow, resuming after the last stage that successfully finished.

  .. rubric:: Example:

  .. code:: python

     from terra.compute import compute
     from terra.utils.workflow import resumable

     class ExampleWorkflow:
       def example(self):
         self.example_step()
       @resumable
       def example_step(self)
         compute.run('example.services.example1')

4. The next two layers make up the service, consisting of an abstracted "service runner" and a "service definition". While a "service runner" is the actual algorithm that gets run, a "service definition" is a thin wrapper that explains how to run the "service runner" in a specific :ref:`compute`. The "service definition" is the abstraction layer that allows us to just say `compute.run("service.name")` and the "service runner" is run utilizing the appropriate compute.

  .. rubric:: Example:

  .. code:: bash

     # Example of calling a service runner directly: example.service1
     python -m example.service1

     # Example of calling using a virtualenv
     pipenv run python -m example.service1

     # Example of calling using a docker
     docker run -it --rm -v /data/stuff:/images service1_image pipenv run python -m example.service1

5. The "service runner" executed by the "service definition" is the actual algorithm that gets run. It must use the settings to get any paths to files or directories it will access, so that terra can perform any necessary :ref:`path translations <settings-path-translation>`. Technically the service runner does not need to be python, as the primary interface is a json file, environment variables, and a single CLI call. But then non-python apps would not be able to take full advantage of the executor layer.
#. The final terra app layer is the "task". If there are functions that can be called independently in parallel, :ref:`tasks <executor>` offer a single abstract API that will run your function in parallel.

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

    set_array_default TERRA_TERRA_VOLUMES "${TERRA_APP1_DIR}:${TERRA_APP1_DIR_DOCKER}" "${TERRA_APP2_DIR}:${TERRA_APP2_DIR_DOCKER}"

    TERRA_APP_PREFIXES+=(TERRA_APP1 TERRA_APP2)
    : ${TERRA_APP1_JUST_SETTINGS=${BASH_SOURCE[0]}}

    # Optional
    # : ${TERRA_CELERY_MAIN_NAME=appname}

    set_array_default TERRA_CELERY_INCLUDE=(app1.tasks app2.tasks)
    array_to_python_ast_list_of_strings TERRA_CELERY_INCLUDE ${TERRA_CELERY_INCLUDE[@]+"${TERRA_CELERY_INCLUDE[@]}"}
    : ${TERRA_CELERY_SERVICE=app1_celery}
