from boop.common import *
from boop.event.thread import *

# ##################################################
# Event Runnable
# Brings Produces and Threads under one roof
# ##################################################

def event_runnable(runnable_class):
  """ Summarize the slots and event handlers found
      in the runnable class.

      runnable._event_classes = {
        'event_handler_type': {
          'slot_name': {
            'class_name': {
              'attr_name': condition
            }
          }
        }
      }
  """

  _event_classes = {}

  for base in runnable_class.__bases__:
    if '_event_classes' in dir(base):
      _base_event_classes = getattr(base,'_event_classes')
      for event_handler_type, attr_names in  _base_event_classes.iteritems():
        for attr_name in attr_names:
          _event_classes.setdefault(event_handler_type,set()).add(attr_name)

  for attr_name in dir(runnable_class):
    attr = getattr(runnable_class,attr_name)
    if '_event_handler_type' in dir(attr):
      event_handler_type = getattr(attr,'_event_handler_type')
      _event_classes.setdefault(event_handler_type,set()).add(attr_name)

  runnable_class._event_classes = _event_classes 
  runnable_class._event_handler_type = 'runnable'

  return runnable_class

class BoopEventRunnable(BoopBase):

  # Prepped by decorator:
  #
  # self._event_classes = {
  #    'thread': set(attribname),
  #    ...
  # }
  #

  name = None

  def __init__(self,*args,**kwargs):
    super(BoopEventRunnable,self).__init__(*args,**kwargs)
    self.timeout = kwargs.get('timeout',0.1)
    self._context = kwargs.pop('context',None)
    self._event_threads_lookup = {}
    self.event_core = None
    self.event_threads = set()

  def threads(self):
    return self._event_classes.get('thread',set())

  def thread_byinstancename(self,thread_name):
    return self._event_threads_lookup.get(thread_name,False)

  def terminate(self):
    for thread in self.event_threads:
      thread.terminate()
    self.unload()
    self.event_core = None
    self.event_threads = set()
    self._event_threads_lookup = {}
    self._context = None

  def unload(self):
    """ Automatically called when terminate has been
        called on the object.
        Override for your own purposes.
    """
    pass

  def start(self,event_core,context=None):
    event_queue = event_core.event_queue
    threads = []
    threads_lookup = {}
    context = context or self._context

    for thread_name in self.threads():
      thread_class = getattr(self,thread_name)
      thread_obj = thread_class(self,event_queue,context)
      thread_obj.start()
      threads.append(thread_obj)

      thread_instance_name = thread_obj.instance_name()
      threads_lookup[thread_instance_name] = thread_obj

    self.event_core = event_core
    self.event_threads = threads
    self._event_threads_lookup = threads_lookup

    return threads

  @staticmethod
  def runnable_name(obj):
    """ Lower casename of the class. Can be overriden for 
        other special purposes.
    """
    if isinstance(obj, (type, types.ClassType)):
      return obj.__name__
    else:
      return type(obj).__name__

  def instance_name(self):
    return self.name

  def runnable_add(self,*args,**kwargs):
    return self.event_core.runnable_add(self._context,*args,**kwargs)


