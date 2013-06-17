from boop.common import *
from boop.app.common import *

##################################################
## PLUGIN
##################################################

def boop_plugin(plugin_class):
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


class BoopPlugin(BoopBase):
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

  def __init__(self,context,*args,**kwargs):
    """ Load any special values into the plugin handler
    """
    self._context = context
    self._active_classes = {}
    super(BoopPlugin,self).__init__(*args,**kwargs)

  def class_start(self,helper_class,*args,**kwargs):
    plugin_class_type = helper_class._plugin_class_type
    helper_obj = self._context.app.class_start(helper_class,self._context,*args,**kwargs)
    self._active_classes.setdefault(plugin_class_type,set()).add(helper_obj)
    return helper_obj

  def terminate(self):
    for plugin_class_type, plugin_class_objects in self._active_classes.iteritems():
      for helper_obj in plugin_class_objects:
        helper_obj.terminate()

  def class_byname(self,name):
    """ Locate a class by name
    """
    for helper_classes in self._plugin_classes.values():
      for helper_class_name, helper_class in helper_classes.iteritems():
        if helper_class.name == name:
          return helper_class
    return EventsAppNotStartedException()

  def class_start_byname(self,name,*args,**kwargs):
    helper_class = self.class_byname(name)
    return self.class_start(helper_class,*args,**kwargs)

  def object_byinstancename(self,instance_name):
    for helper_name,helper_objects in self._active_classes.iteritems():
      for helper_obj in helper_objects:
        if helper_obj.instance_name() == instance_name:
          return helper_obj
    raise BoopNotExists()

  def start(self,*args,**kwargs):
    """ Start whatever is required for basic functionality
        of this plugin. Usually a commandset injected into
        the parent application
    """

    for commandset,commandset_class in self.commandsets().iteritems():
      if commandset_class._plugin_start == 'auto':
        kwargs.setdefault('debug',self._debug)
        self.class_start(commandset_class,*args,**kwargs)

    for runnable,runnable_class in self.runnables().iteritems():
      if runnable_class._plugin_start == 'auto':
        kwargs.setdefault('debug',self._debug)
        self.class_start(runnable_class,*args,**kwargs)

  def runnable_add(self,runnable,*args,**kwargs):
    return self._context.app.runnable_add(runnable,*args,**kwargs)

  def commandset_add(self,commandset,*args,**kwargs):
    return self._context.app.commandset_add(commandset,self,*args,**kwargs)

  def commandsets(self):
    return self._plugin_classes.get('commandset',{})

  def runnables(self):
    return self._plugin_classes.get('runnable',{})


