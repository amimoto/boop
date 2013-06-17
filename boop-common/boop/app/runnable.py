from boop.app.common import *
from boop.event import *

##################################################
## RUNNABLE
##################################################

def boop_runnable(runnable_class,*args,**kwargs):
  """ Tags an EventRunnable class in a plugin

      start='auto' start automatically when plugin starts
      start='manual' do not start. will be handled by user code

      For registration of runnable classes, run this decorator

      @boop_runnable
      class MyClass(Runnable):
        ...

      By default all runnables are _started up when the 
      plugin is loaded. To prevent that do the following:

      @boop_runnable.opts(start='manual')
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
boop_runnable.opts = lambda *args,**kwargs: \
                          lambda x: boop_runnable(x,*args,**kwargs)


