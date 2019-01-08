from terra.compute.base.base import (
    BaseCompute, DSMService as BaseDSMService,
    ViewAngleRetrieval as BaseViewAngleRetrieval
)


class Compute(BaseCompute):
  ''' Dummy Computing Service Model
  '''

  def create(self, service_class):
    print("create: " + service_class.name)

  def start(self, service_class):
    print("start: " + service_class.name)

  def run(self, service_class):
    print("run: " + service_class.name)
    service_info = service_class()
    service_info.pre_run()
    self.create(service_class)
    self.start(service_class)
    service_info.post_run()

  def stop(self, service_class):
    print("stop: " + service_class.name)

  def remove(self, service_class):
    print("remove: " + service_class.name)


class DummyService:
  def pre_run(self):
    print("pre run: " + self.name)

  def post_run(self):
    print("post run: " + self.name)


@Compute.register
class DSMService(DummyService, BaseDSMService):
  pass


@Compute.register
class ViewAngleRetrieval(DummyService, BaseViewAngleRetrieval):
  pass
