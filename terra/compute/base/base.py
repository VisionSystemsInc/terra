

class BaseService:
  pass

class BaseCompute:
  ''' Base Computing Service Model
  '''

  class DSMService(BaseService):
    pass

  def create(self):
    pass

  def start(self):
    pass

  def run(self):
    self.create()
    self.start()

  def stop(self):
    pass

  def remove(self):
    pass
