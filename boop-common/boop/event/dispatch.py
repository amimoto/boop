from boop.common import *
from boop.event.runnable import *

# ##################################################
# WISHLIST
# - dynamic load of EventThreads into an object?
# - I wonder if this can be easier to understand...
# ##################################################

# ##################################################
# Main Handler
# ##################################################

class BoopEventDispatch(BoopBaseThread):
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
                context=None,
                *args,
                **kwargs
                ):
    kwargs['daemon'] = False
    super(BoopEventDispatch,self).__init__(*args,**kwargs)

    if context == None: context = {}

    self.event_queue = BoopEventQueue()
    self.event_threads = set()
    self.event_runnables = set();
    self._context = context

  #######################################################
  # Events
  #######################################################

  def propagate_event(self,event):
    for thread in list(self.event_threads):
      thread.receive_event(event)

  def terminate(self):
    super(BoopEventDispatch,self).terminate()
    for runnable in list(self.event_runnables):
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
    """ Instantiate a new Runnable object and register
        it to the Dispatcher. This function is the preferred
        method of adding Runnables to Dispatchers since
        it will setup the appropriate shared variables
        (eg. communication queues)
    """
    if not self.is_alive(): raise BoopEventDispatchNotStarted()
    if not 'timeout' in kwargs: 
      kwargs['timeout'] = self.timeout
    if 'context' in kwargs:
      context = kwargs['context']
      del kwargs['context']
    else: context = self._context
    kwargs.setdefault('debug',self._debug)
    runnable_obj = runnable_class(context.copy(),*args,**kwargs)
    threads = runnable_obj.start(self)
    for thread in threads:
      self.thread_add(thread)
    self.event_runnables.add(runnable_obj)
    return runnable_obj

  def runnables(self):
    """ Returns a list of Runnable objects currently
        registered to the Dispatcher
    """
    return self.event_runnables

  def runnable_remove(self,ident):
    """ Stub entry. We don't allow the removal
        of Runnable objects from Dispatcher yet.
    """
    raise NotImplementedException();

  #######################################################
  # Event Threads
  #######################################################

  def poll(self):
    try:
      event = self.event_queue.get(True,self.timeout)
      self.propagate_event(event)
    except Queue.Empty:
      pass

  def signal_emit(self,event):
    self.event_queue.put(event)
    return event

  def event_source(self,k,*args,**kwargs):
    return type(self).__name__


  #######################################################
  # Misc
  #######################################################

  def _attrib_emit(self,k,*args,**kwargs):
    if not kwargs.get('source',False):
      kwargs['source'] = self.event_source(k,*args,**kwargs)
    ev = BoopEvent(k,*args,**kwargs)
    if self._debug: print "Emitting:",ev
    return self.signal_emit(ev)

  def __getattr__(self,k):
    if k == 'emit': return self
    return lambda *args,**kwargs: self._attrib_emit(k,*args,**kwargs)


  def debug_tree(self):
    """ Print the current dispatch's structure of 
        active objects
    """

    output = "--------------------------------------------------\n"
    output += "Dispatch:"+self._instance_name+"\n"
    for runnable in self.event_runnables:
      output += "\n Runnable: "+type(runnable).__name__+"\n"
      for thread_name,thread_obj in runnable._event_threads_lookup.iteritems():

        output += '\n   Thread "{thread_name}": {thread_type}\n'.format(
                                  thread_name=thread_name,
                                  thread_type=type(thread_obj).__name__)

        for slot_name,attrs in thread_obj._event_handlers.iteritems():
          output += "{slot_name:>22}: {attr_list}\n".format(
                  slot_name=slot_name,
                  attr_list=",".join(attrs.keys())
                )
    output += "\n--------------------------------------------------"
    return output

