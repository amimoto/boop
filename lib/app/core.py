from event import *
from event.log import *
from command import *
import types

__all__ = [
  'event_app_plugin',
  'EventsAppPlugin',
  'EventsApp',
  'PluginCommandSet',
  'plugin_commandset',
  'plugin_runnable',
  'PluginEventRunnable',
]


def plugin_class(plugin_class,plugin_class_type,start='auto'):
  """ Decorator to tag a Plugin class in a plugin

      plugin_class_type must be the type of class (ie. commandset or runnable)

      start='auto' start automatically when plugin starts
      start='manual' do not start. will be handled by user code

      This is more of a template decorator. See individual implementations
      below

  """
  plugin_class._plugin_class_type = plugin_class_type
  plugin_class._plugin_start = start

  return plugin_class

##################################################
## RUNNABLE
##################################################

def plugin_runnable(runnable_class,*args,**kwargs):
  """ Tags an EventRunnable class in a plugin

      start='auto' start automatically when plugin starts
      start='manual' do not start. will be handled by user code

      For registration of runnable classes, run this decorator

      @plugin_runnable
      class MyClass(Runnable):
        ...

      By default all runnables are started up when the 
      plugin is loaded. To prevent that do the following:

      @plugin_runnable.opts(start='manual')
      class MyClass(Runnable):
        ...

  """
  runnable_class = event_runnable(runnable_class)

  if not 'name' in dir(runnable_class):
    for base in runnable_class.__bases__:
      if 'runnable_name' in dir(base):
        runnable_class.name = base.runnable_name(runnable_class)
        break

  return plugin_class(runnable_class,'runnable',*args,**kwargs)

# Setup some syntax sugar to allow for @plugin_runnable AND
# @plugin_runnable.opts(kwargs)
plugin_runnable.opts = lambda *args,**kwargs: \
                          lambda x: plugin_runnable(x,*args,**kwargs)

@event_runnable
class PluginEventRunnable(EventRunnable):
    def init(self,app,plugin,*args,**kwargs):
      super(PluginEventRunnable,self).init(*args,**kwargs)
      self.plugin = plugin
      self.app = app
      self.instance_name = self.instance_name()

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

    def unload(self):
      super(PluginEventRunnable,self).unload()
      self.app = None
      self.plugin = None


##################################################
## COMMANDSET
##################################################

def plugin_commandset(commandset_class,start='auto'):
  """ Decorator to tag a Commandset class in a plugin

      start='auto' start automatically when plugin starts
      start='manual' do not start. will be handled by user code

      For registration of commandset classes, run this decorator

      @plugin_commandset
      class MyClass(PluginCommandSet):
        ...

      By default all commandsets are started up when the 
      plugin is loaded. To prevent that do the following:

      @plugin_commandset.opts(start='manual')
      class MyClass(EventAppCommand):
        ...

  """
def plugin_commandset(commandset_class,*args,**kwargs):
  commandset_class = commandset(commandset_class)
  return plugin_class(commandset_class,'commandset',*args,**kwargs)

# Setup some syntax sugar to allow for @plugin_commandset AND
# @plugin_commandset.opts(kwargs)
plugin_commandset.opts = lambda *args,**kwargs: \
                          lambda x: plugin_commandset(x,*args,**kwargs)


class PluginCommandSet(CommandSet):
    """ Link in the CommandSet functionality into the plugin
        This shouldn't change the behaviour of the command
        class as much as allow it access to the app and 
        plugin datastructures
    """

    name = "serial"

    def init(self,app,plugin):
      self.plugin = plugin
      self.app = app
      self.instance_name = self.instance_name()

    def instance_name(self):
      return self.name

    def unload(self):
      super(PluginCommandSet,self).unload()
      self.app = None
      self.plugin = None

##################################################
## PLUGIN
##################################################

def event_app_plugin(plugin_class):
  plugin_classes = {}

  # Load up parent plugin classes first
  for base in plugin_class.__bases__:
    if '_event_handlers' in dir(base):
      _base_plugin_classes = getattr(base,'_plugin_classes')
      for plugin_class_type,registry in _base_plugin_classes.iteritems():
        plugin_classes[plugin_class_type] = registry.copy()

  # The override the parent runnable classes
  for attr_name in dir(plugin_class):
    attr = getattr(plugin_class,attr_name)
    if '_plugin_class_type' in dir(attr):
      plugin_class_type = getattr(attr,'_plugin_class_type')
      plugin_classes.setdefault(plugin_class_type,{})[attr_name] = attr

  plugin_class._plugin_classes = plugin_classes

  return plugin_class

class EventsAppPlugin(object):
  """ A method to package runnables and commandsets to 
      add features to EventsApp objects.

      While plugins could actually be made as
      sub-apps, I am also targetting lower-end 
      hardware so I'm trying to setup an architechture
      that is a compromise between lightweight and
      full-featured.

      Some magical classes end up being defined:

      self._plugin_classes = {
        'runnable': {
                    'name of class tagged runnable': class,
                    ...,
                  },
        'commandset': {
                    'name of class tagged commandset': class,
                    ...,
                  },
      }

      self._active_classes = {
        'runnable': set( class, ... ),
        'commandset': set( class, ...  )
      }

  """

  def __init__(self,app,*args,**kwargs):
    """ Load any special values into the plugin handler
    """
    self.app = app
    self._active_classes = {}

  def class_start(self,helper_class,*args,**kwargs):
    plugin_class_type = helper_class._plugin_class_type
    helper_obj = self.app.class_start(helper_class,self,*args,**kwargs)
    self._active_classes.setdefault(plugin_class_type,set()).add(helper_obj)
    return helper_obj

  def class_byname(self,name):
    """ Locate a class by name
    """
    for helper_classes in self._plugin_classes.values():
      for helper_class_name, helper_class in helper_classes.iteritems():
        if helper_class.name == name:
          return helper_class
    return Exception('Missing class '+name)

  def class_start_byname(self,name,*args,**kwargs):
    helper_class = self.class_byname(name)
    return self.class_start(helper_class,*args,**kwargs)

  def object_byinstancename(self,instance_name):
    for helper_name,helper_objects in self._active_classes.iteritems():
      for helper_obj in helper_objects:
        if helper_obj.instance_name == instance_name:
          return helper_obj
    return Exception('Missing object '+name)

  def start(self):
    """ Start whatever is required for basic functionality
        of this plugin. Usually a commandset injected into
        the parent application
    """

    for commandset,commandset_class in self.commandsets().iteritems():
      if commandset_class._plugin_start == 'auto':
        self.class_start(commandset_class)

    for runnable,runnable_class in self.runnables().iteritems():
      if runnable_class._plugin_start == 'auto':
        self.class_start(commandset_class)

  def runnable_add(self,runnable,*args,**kwargs):
    return self.app.runnable_add(runnable,*args,**kwargs)

  def commandset_add(self,commandset,*args,**kwargs):
    return self.app.commandset_add(commandset,self,*args,**kwargs)

  def commandsets(self):
    return self._plugin_classes['commandset']

  def runnables(self):
    return self._plugin_classes['runnable']


##################################################
## APP
##################################################

class EventsApp(object):
  """
  Main class that allows the set-up various events and an interface
  to control them.

  data_path = path to a directory where the class can save data files such as 
              the event log
  """

  def __init__(self,
                data_path,
                command_class=CommandRunner,
                event_class=EventDispatch,
                event_log_class=EventLoggerRunnable,
                ):

    self.data_path = data_path
    self.events = event_class()
    self.events_log_dsn = data_path + "/log.db"
    self.commands = command_class()
    self.plugins = set()
    self.started = False

  def execute(self,s):
    # TODO some way for plugins to override this?
    return self.commands.execute(s,self)

  def class_start(self,helper_class,plugin,*args,**kwargs):
    if helper_class._plugin_class_type == 'commandset':
      return self.commandset_add(helper_class,self,plugin,*args,**kwargs)
    elif helper_class._plugin_class_type == 'runnable':
      return self.runnable_add(helper_class,self,plugin,*args,**kwargs)

  def runnable_add(self,*args,**kwargs):
    return self.events.runnable_add(*args,**kwargs)

  def commandset_add(self,*args,**kwargs):
    return self.commands.commandset_add(*args,**kwargs)

  def commandset_remove(self,*args,**kwargs):
    return self.commands.commandset_remove(*args,**kwargs)

  def commandset_list(self,*args,**kwargs):
    return self.commands.commandset_list(*args,**kwargs)

  def plugin_add(self,plugin_class,*args,**kwargs):
    plugin_obj = plugin_class(self,*args,**kwargs)
    self.plugins.add(plugin_obj)
    plugin_obj.start()
    return plugin_obj

  def plugin_remove(self,plugin_obj):
    try:
      self.plugins.remove(plugin_obj)
    except KeyError:
      pass
    return plugin_obj

  def start(self):
    self.events.start()
    self.events_log = self.runnable_add(EventLoggerRunnable,self.events_log_dsn)
    self.started = True

  def terminate(self):
    if self.started:
      self.events.terminate()


