import threading
import Queue
import datetime
import pdb

# ##################################################
# ##################################################

class NotImplementedException(Exception): pass
class RequiresSubclassImplementation(Exception): pass

# ##################################################
# Event Consumer Functions should have the property
# func._event_slots = {
#
#    # if the consumption event is only on certain
#    # situations
#    'slot_name': lambda event: return True, 
#
#    # if there are no conditions and we accept
#    # all events with the slot_name...
#    'slot_name': None
#
#    ...
#
# }
# ##################################################

class EventSlots(object):

  def events(self,condition,events,func):
    event_slots = {}
    for event_slot in events:
      event_slots[event_slot] = condition
    func._event_slots = event_slots
    return func

  def _getattr_helper(self,condition,events):
    return lambda func: self.events(condition,events,func)

  def __getattr__(self,k):
    return lambda condition: self._getattr_helper(condition,[k])

class EventSlotsBasic(EventSlots):

  def __init__(self):
    self.when = EventSlots()

  def _getattr_helper(self,func,events):
    return self.events(None,events,func)

consume = EventSlotsBasic()

# ##################################################
# ##################################################

class Event(object):
  def __init__(self,event_type,data=None,event_source=None):
    self.type = event_type
    self.data = data
    self.source = event_source
    self.datetime = datetime.datetime.now()


# ##################################################
# ##################################################

class EventQueue(Queue.Queue,object):
  def __init__(self,*args,**kwargs):
    super(EventQueue,self).__init__(*args,**kwargs)

  def __getattribute__(self,k):
    try:
      return super(EventQueue,self).__getattribute__(k)
    except AttributeError:
      return lambda *args,**kwargs: Event(k,*args,**kwargs)

# ##################################################
# ##################################################

# event_bus is the Queue that will be used to transmit
# information to the main dispater. The dispatcher will
# then dispatch the message to all interested parties

class Threading(threading.Thread):

  def __init__(self,timeout=0.1,*args,**kwargs):
    self._terminate = False
    self.timeout = timeout
    super(Threading,self).__init__(*args,**kwargs)
    for k,v in kwargs.iteritems():
      setattr(self,k,v) 
    self.daemon = True
    self.init(*args,**kwargs)

  def init(self,*args,**kwargs):
    pass

  def terminate(self):
    self._terminate = True

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

# ##################################################
# Event Threads
# ##################################################

def event_thread(thread_class):
  """ Iterate through the thread_class to find
      and tabulate all the consumer functions into
      the property _event_handlers to be set. 
      The _event_handlers structure should look
      like:

      self._event_handlers = {
        'slot_name': { 
                     'attr_name': lambda event: return True, 
                     ...
                     },
      }

  """

  _event_handlers = {}

  # First do the super classes
  for base in thread_class.__bases__:
    if '_event_handlers' in dir(base):
      _base_event_handlers = getattr(base,'_event_handlers')
      for name, attrs in  _base_event_handlers.iteritems():
        _event_handlers.setdefault(name,{})\
                       .update(attrs)

  # Then do the local class as it'll handle overrides
  for attr_name in dir(thread_class):
    attr = getattr(thread_class,attr_name)
    if not '_event_slots' in dir(attr):
      continue

    # If we're here, this attribute is a consumer
    _event_slots = getattr(attr,'_event_slots')

    # Build the struct for this level
    for (name,condition) in _event_slots.iteritems():
      _event_handlers.setdefault(name,{})[attr_name] = condition

  thread_class._event_handlers = _event_handlers
  thread_class._event_handler_type = 'thread'

  return thread_class

class EventThread(Threading):
  """ Basic thread unit. While capable of being both a producer
      or a consumer, these objects will primarily be used in a
      single mode.

      self._event_handlers = {
        'slot_name': { 
                     'attr_name': lambda event: return True, 
                     ...
                     },
      }

  """


  # _event_handlers:  all event slots and functions associated
  # _event_handler_type: that it's a thread

  def __init__(self,runnable,event_queue,*args,**kwargs):
    super(EventThread,self).__init__(*args,**kwargs)
    self.event_queue = event_queue
    self.local_event_queue = EventQueue()
    self.parent = runnable
    self.init(*args,**kwargs)

  def init(self,*args,**kwargs):
    pass

  def signal_emit(self,event):
    self.event_queue.put(event)
    return event

  def receive_event(self,event):
    if event.type in self._event_handlers or \
      'ALL' in self._event_handlers:
      self.local_event_queue.put(event)

  def poll(self):
    try:
      event = self.local_event_queue.get(True,self.timeout)
      if event.type in self._event_handlers:
        for attr_name,condition in self._event_handlers[event.type].iteritems():
          if condition == None or condition(self,event):
            getattr(self,attr_name)(event)
      if event.type != 'ALL' and 'ALL' in self._event_handlers:
        for attr_name,condition in self._event_handlers['ALL'].iteritems():
          if condition == None or condition(self,event):
            getattr(self,attr_name)(event)

    except Queue.Empty:
      if self._terminate:
        return

  def event_source(self,k,*args,**kwargs):
    return type(self).__name__

  def _attrib_emit(self,k,*args,**kwargs):
    if not kwargs.get('event_source',False):
      kwargs['event_source'] = self.event_source(k,*args,**kwargs)
    return self.signal_emit(Event(k,*args,**kwargs))

  def __getattr__(self,k):
    if k == 'emit': return self
    return lambda *args,**kwargs: self._attrib_emit(k,*args,**kwargs)


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

class EventRunnable(object):

  # Prepped by decorator:
  #
  # self._event_classes = {
  #    'thread': set(attribname),
  #    ...
  # }
  #

  def __init__(self,*args,**kwargs):
    self.timeout = kwargs.get('timeout')
    self.init(*args,**kwargs)

    self.event_core = None
    self.event_threads = set()
    self._event_threads_lookup = {}

  def init(self,*args,**kwargs):
    pass

  def threads(self):
    return self._event_classes.get('thread',set())

  def thread_get(self,thread_name):
    return self._event_threads_lookup.get(thread_name,False)

  def terminate(self):
    for thread in self.event_threads:
      thread.terminate()
    self.unload()

  def unload(self):
    self.event_core = None
    self.event_threads = set()
    self._event_threads_lookup = {}

  def start(self,event_core):
    event_queue = event_core.event_queue
    threads = []
    threads_lookup = {}

    for thread_name in self.threads():
      thread_class = getattr(self,thread_name)
      thread_obj = thread_class(self,event_queue)
      thread_obj.start()
      threads.append(thread_obj)
      threads_lookup[thread_name] = thread_obj

    self.event_core = event_core
    self.event_threads = threads
    self._event_threads_lookup = threads_lookup

    return threads

  def runnable_add(self,*args,**kwargs):
    return self.event_core.runnable_add(*args,**kwargs)

# ##################################################
# Main Handler
# ##################################################

class EventDispatch(Threading):
  """ Handles:
        * main loop
        * add/remove of runnables
        * dispatches events to dependant threads 

      Internal structures:
        self.event_queue - the primary event queue used to 
                            pass messages around

        self.event_runnables - set of all the running
                                runnable objets

  """

  def __init__(self,
                *args,
                **kwargs
                ):
    super(EventDispatch,self).__init__(*args,**kwargs)

    self.daemon = False

    self.event_queue = EventQueue()

    self.event_threads = set()
    self.event_runnables = set();

  #######################################################
  # Events
  #######################################################

  def propagate_event(self,event):
    for thread in self.event_threads:
      thread.receive_event(event)

  def terminate(self):
    super(EventDispatch,self).terminate()
    for runnable in self.event_runnables:
      runnable.terminate()
    self.event_runnables = set()

  #######################################################
  # Event Threads
  #######################################################

  def thread_add(self,thread):
    self.event_threads.add(thread)

  #######################################################
  # Event Runnable
  #######################################################

  def runnable_add(self,runnable_class,*args,**kwargs):
    if not 'timeout' in kwargs: 
      kwargs['timeout'] = self.timeout
    runnable_obj = runnable_class(*args,**kwargs)
    threads = runnable_obj.start(self)
    for thread in threads:
      self.thread_add(thread)
    self.event_runnables.add(runnable_obj)
    return runnable_obj

  def runnable_remove(self,ident):
    raise NotImplementedException();

  #######################################################
  # Event Threads
  #######################################################
  def run(self):
    while 1:
      try:
        event = self.event_queue.get(True,self.timeout)
        self.propagate_event(event)
      except Queue.Empty:
        if self._terminate:
          return




