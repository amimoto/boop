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

