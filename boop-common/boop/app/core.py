from boop.common import *
from boop.event.log import *
from boop.app.common import *
from boop.app.runnable import *
from boop.app.commandset import *
from boop.app.plugin import *
from boop.command import *
import types

__all__ = [
  'boop_commandset',
  'BoopCommandSet',

  'boop_runnable',
  'BoopEventRunnable',

  'boop_plugin',
  'BoopPlugin',

  'BoopApp',
  'BoopAppNotStartedException',
]

##################################################
## APP
##################################################

class BoopApp(BoopBase):
  """
  Main class that allows the set-up various events and an interface
  to control them.

  data_path = path to a directory where the class can save data files such as 
              the event log
  """

  def __init__(self,
                data_path=None,
                command_class=BoopCommandSetDispatch,
                event_class=BoopEventDispatch,
                event_log_class=BoopEventLoggerRunnable,
                events_log_dsn=None,
                plugins=None,
                context=None,
                *args,
                **kwargs
                ):

    if context == None:
      context = BoopContext()

    self._context = context
    self._context.app = self

    self._started = False
    self._terminate = False

    # TODO: '_' prefix most of these internal values
    self.events = None
    self.commands = None
    self.plugins = {}


    self.event_class = event_class
    self.command_class = command_class
    if plugins == None: plugins = []
    self.plugins_to_start = plugins

    self.data_path = data_path
    self.events_log_dsn = events_log_dsn
    if not events_log_dsn and data_path:
      self.events_log_dsn = data_path + "/log.db"

    self.init(*args,**kwargs)

  def init(self,*args,**kwargs):
    pass

  def execute(self,s):
    if not self._started: raise BoopAppNotStartedException()
    # TODO provide some way for plugins to override this?
    return self.commands.execute(s)

  def class_start(self,helper_class,parent_plugin,*args,**kwargs):
    if not self._started: raise BoopAppNotStartedException()
    context = self._context.copy(
                  plugin=parent_plugin
                )
    if helper_class._plugin_class_type == 'commandset':
      return self.commandset_add(
                  helper_class,
                  context,
                  *args,
                  **kwargs
                  )
    elif helper_class._plugin_class_type == 'runnable':
      return self.runnable_add(
                  helper_class,
                  context,
                  None,
                  *args,
                  **kwargs
                  )

  def runnable_add(self,*args,**kwargs):
    if not self._started: raise BoopAppNotStartedException()
    return self.events.runnable_add(*args,**kwargs)

  def commandset_add(self,commandset_class,*args,**kwargs):
    if not self._started: raise BoopAppNotStartedException()
    return self.commands.commandset_add(commandset_class,*args,**kwargs)

  def commandset_remove(self,*args,**kwargs):
    if not self._started: raise BoopAppNotStartedException()
    return self.commands.commandset_remove(*args,**kwargs)

  def commandset_list(self,*args,**kwargs):
    if not self._started: raise BoopAppNotStartedException()
    return self.commands.commandset_list(*args,**kwargs)

  def plugin_add(self,plugin_class,*args,**kwargs):
    """ Add a new plugin object to the application.
        Automatically start all helper classes that have been tagged auto
    """
    if not self._started: raise BoopAppNotStartedException()
    kwargs.setdefault('debug',self._debug)
    plugin_obj = plugin_class(
                        self._context,
                        *args,
                        **kwargs )
    instance_name = plugin_obj.instance_name()
    self.plugins[instance_name] = plugin_obj
    plugin_obj.start(*args,**kwargs)
    return plugin_obj

  def plugin_remove(self,plugin_obj):
    if not self._started: raise BoopAppNotStartedException()
    try:
      self.plugins.remove(plugin_obj)
    except KeyError:
      pass
    return plugin_obj

  def plugin_byinstancename(self,instance_name):
    if not self._started: raise BoopAppNotStartedException()
    if instance_name in self.plugins:
      return self.plugins[instance_name]
    return None

  def start(self):
    self.events = self.event_class(debug=self._debug)
    self.events.start()
    self.commands = self.command_class(self._context)
    self._started = True
    if self.events_log_dsn:
      self.events_log = self.runnable_add(
                                BoopEventLoggerRunnable,
                                self.events_log_dsn )
    for plugin_class in self.plugins_to_start:
      self.plugin_add(plugin_class)

  def terminate(self):
    self._terminate = True
    if self._started:
      self.events.terminate()
      for plugin_name,plugin_obj in self.plugins.iteritems():
        plugin_obj.terminate()
      self.plugins = {}

  def _attrib_emit(self,k,*args,**kwargs):
    if not kwargs.get('source',False):
      kwargs['source'] = self.events.event_source(k,*args,**kwargs)
    return self.events.signal_emit(BoopEvent(k,*args,**kwargs))

  def stall_loop(self):
    while self._terminate == False: 
      time.sleep(0.1)

  def __getattr__(self,k):
    if k == 'emit': return self.events
    return lambda *args,**kwargs: self._attrib_emit(k,*args,**kwargs)


  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.terminate()

