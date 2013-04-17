import types

class BoopNotExists(Exception): pass

class BoopBase(object):

  _instance_name = None

  def __init__( self,
                instance_name=None,
                *args,
                **kwargs):

    self._instance_name = instance_name or self.instance_name()

    self.init(*args,**kwargs)

  def init(self,*args,**kwargs):
    pass

  def instance_name(self):
    if self._instance_name != None:
      return self._instance_name
    elif 'name' in dir(self):
      return getattr(self,'name')
    elif isinstance(self, (type, types.ClassType)):
      return self.__name__
    else:
      return type(self).__name__


