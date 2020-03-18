from terra import settings
from terra.logger import getLogger
logger = getLogger(__name__)


class BaseWorkflow:
  '''
  The base class for all Terra Workflows
  '''

  def run(self):
    pass


class PipelineWorkflow:
  '''
  A simple workflow that runs a set of services, serially.

  self.pipeline need to be set to a list of services calls.
  '''

  def __init__(self):
    self.pipeline = list()

  # locate index of service name in workflow pipeline
  def service_index(self, service_name=None, default_index=0):

    # default output
    if not service_name:
      return default_index

    # pipeline names
    pipeline_names = [s.__name__ for s in self.pipeline]
    pipeline_names_lower = [s.lower() for s in pipeline_names]

    # locate index
    try:
      return pipeline_names_lower.index(service_name.lower())
    except ValueError as err:
      newerr = ValueError(f"Could not find service {service_name}"
                          f" in {pipeline_names}")
      raise newerr from err

  # run main workflow
  def run(self):

    # pipeline start/end
    start_index = self.service_index(settings.service_start, 0)
    end_index = self.service_index(settings.service_end,
                                   len(self.pipeline) - 1)

    if (start_index > end_index):
      raise ValueError(
          f"Start service {self.pipeline[start_index].__name__} "
          f"must precede end service {self.pipeline[end_index].__name__}"
      )

    # slice pipeline to requested services
    pipeline = self.pipeline[start_index:end_index + 1]
    logger.info(f'PIPELINE - {[s.__name__ for s in pipeline]}')

    # Run the pipeline
    for service in pipeline:
      service()
