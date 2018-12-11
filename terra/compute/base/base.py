

class BaseCompute:
  ''' Base Computing Service Model
  '''

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
