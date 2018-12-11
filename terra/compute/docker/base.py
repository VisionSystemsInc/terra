from terra.compute.base.base import BaseCompute

import compose
from os import environ as env


class Compute(BaseCompute):
  ''' Using docker for the computer service model, specifically docker-compose
  '''

  def __init__(self):
    self.client = docker.from_env()
    self.image_name = env['TERRA_DOCKER_REPO'] + ':terra_' + \
        os.env['TERRA_USERNAME']
    super().__init__()
