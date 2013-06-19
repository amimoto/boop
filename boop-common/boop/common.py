import types
import threading

class NotImplementedException(Exception): pass
class RequiresSubclassImplementation(Exception): pass
class EventDispatchNotStarted(Exception): pass
class BoopAppNotStartedException(Exception): pass
class BoopNotExists(Exception): pass

def kwargs_filter(kwargs,*args):
  """ Return a dict filtered by the keys listed
  """
  out = {}
  for k in args:
    if k in kwargs:
      out[k] = kwargs[k]
  return out

class BoopContext(object):
  _data = None

  def __init__(self,local_data=None,global_data=None,**kwargs):
    if global_data == None: 
      global_data = {}
    object.__setattr__(self,'_global_data',global_data)
    object.__setattr__(self,'_local_data',{})
    self.update(local_data,**kwargs)

  def update(self,data=None,**kwargs):
    if data == None:
      data = {}
    data = data.copy()
    data.update(kwargs)

    for k,v in data.iteritems():
      setattr(self,k,v)

  def copy(self,data=None,**kwargs):
    local_data = self._local_data.copy()
    if data:
      local_data.update(data,**kwargs)
    return BoopContext(
              local_data=local_data,
              global_data=self._global_data,
              **kwargs
            )

  def __getitem__(self,attr):
    return self.__getattr__(attr)

  def __getattr__(self,attr):
    if attr in self._local_data: 
      return self._local_data[attr]
    if attr in self._global_data: 
      return self._global_data[attr]
    raise AttributeError(
              "%s does not have attribute %s"%(
              type(self).__name__,
              attr
            ))

  def __setitem__(self,attr,value):
    return self.__setattr__(attr,value)

  def __setattr__(self,attr,value):
    if attr in('_global_data','_local_data'):
      setattr(self,attr,value)
    elif attr.isupper():
      self._global_data[attr] = value
    else: 
      self._local_data[attr] = value

class BoopBase(object):

  # The instance name should be a unique identifier
  # for each created object with BoopBase. 
  _instance_name = None
  _debug = False
  _terminate = False

  def __init__( self,
                instance_name=None,
                *args,
                **kwargs):
    timeout = kwargs.pop('timeout',0.1)
    debug = kwargs.pop('debug',False)
    try:
      super(BoopBase,self).__init__(**kwargs)
    except TypeError:
      super(BoopBase,self).__init__()
    self._debug = debug
    self._instance_name = instance_name or self.instance_name()
    self._terminate = False
    self.timeout = timeout
    self.init(*args,**kwargs)

  def init(self,*args,**kwargs):
    """ Overrideable function to handle initialization
        requirements for subclasses. useful when we don't 
        want to have to deal with so many parameters. By
        the time this has been called, things such as instance_name
        will have been pruned from the arguments
    """
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

  def terminate(self):
    self._terminate = True

class BoopBaseThread(BoopBase,threading.Thread):

  _instance_name = None

  def __init__( self,
                instance_name=None,
                daemon=False,
                *args,
                **kwargs):
    debug = kwargs.get('debug',False)
    kwargs.setdefault('verbose',debug)
    super(BoopBaseThread,self).__init__(instance_name,*args,**kwargs)
    self.daemon = daemon

  def cleanup(self):
    pass

  def poll(self):
    time.sleep(self.timeout)

  def run(self):
    while 1:
      self.poll()
      if self._terminate:
        self.cleanup()
        return

