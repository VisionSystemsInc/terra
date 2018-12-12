from terra.compute.base.base import BaseCompute

class Compute(BaseCompute):
  ''' Dummy Computing Service Model
  '''

  def create(self):
    print("create")

  def start(self):
    print("start")

  def run(self):
    print("run")
    self.create()
    self.start()

  def stop(self):
    print("stop")

  def remove(self):
    print("remove")
