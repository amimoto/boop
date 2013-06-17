from boop.common import *
from boop.event.event import *
from boop.event.queue import *

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

class BoopEventThread(BoopBaseThread):
  """ Basic thread unit. While capable of being both a producer
      or a consumer, these objects will primarily be used in a
      single mode.

      self._event_handlers = {
        'slot_name': { 
                     'attr_name': lambda event: return True, 
                     ...
                     },
      }

      BoopEventThread class declarations should have the event_thread
      decorator applied 

      @event_thread
      class MyEvThread(BoopEventThread):
        pass
      

      Event hooks can be applied to functions in the BoopEventThread
      by applying the consumes decorator


      @event_thread
      class MyEvThread(BoopEventThread):

        @consume.MY_EVENT
        def my_event_handler(self,event):
          # your code
      

  """
  # _event_handlers:  all event slots and functions associated
  # _event_handler_type: that it's a thread

  def __init__( self,
                runnable,
                event_queue,
                context,
                *args,
                **kwargs
                ):
    super(BoopEventThread,self).__init__(*args,**kwargs)
    self.event_queue = event_queue
    self.local_event_queue = BoopEventQueue()
    self.parent = runnable
    self._context = context

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
    if not kwargs.get('source',False):
      kwargs['source'] = self.event_source(k,*args,**kwargs)
    return self.signal_emit(BoopEvent(k,*args,**kwargs))

  def __getattr__(self,k):
    if k == 'emit': return self
    return lambda *args,**kwargs: self._attrib_emit(k,*args,**kwargs)

  def terminate(self):
    super(BoopEventThread,self).terminate()
    self._context = None
    self.parent = None
    self.event_queue = None
    self.local_event_queue = None

