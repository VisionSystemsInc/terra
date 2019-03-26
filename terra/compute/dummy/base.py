from terra.compute.base.base import BaseCompute
# from terra import settings
from terra.compute.utils import load_service

class Compute(BaseCompute):
  ''' Dummy Computing Service Model
  '''

  def create(self, service_class):
    print("create: " + str(load_service(service_class)))

  def start(self, service_class):
    print("start: " + str(load_service(service_class)))

  def run(self, service_class):
    service = load_service(service_class)
    print("run: " + str(service))
    service = service()
    service.pre_run()
    self.create(service_class)
    self.start(service_class)
    service.post_run()

  def stop(self, service_class):
    print("stop: " + str(load_service(service_class)))

  def remove(self, service_class):
    print("remove: " + str(load_service(service_class)))


class DummyService:
  def pre_run(self):
    print("pre run: " + str(self))

  def post_run(self):
    print("post run: " + str(self))
