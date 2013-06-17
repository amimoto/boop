from boop.app.common import *
from boop.command import *

##################################################
## COMMANDSET
##################################################

def boop_commandset(commandset_class,*args,**kwargs):
  """ Decorator to tag a Commandset class in a plugin

      start='auto' start automatically when plugin starts
      start='manual' do not start. will be handled by user code

      For registration of commandset classes, run this decorator

      @boop_commandset
      class MyClass(BoopPluginCommandSet):
        ...

      By default all commandsets are _started up when the 
      plugin is loaded. To prevent that do the following:

      @boop_commandset.opts(start='manual')
      class MyClass(EventAppCommand):
        ...

  """
  commandset_class = commandset(commandset_class)
  return plugin_class(commandset_class,'commandset',*args,**kwargs)

# Setup some syntax sugar to allow for @plugin_commandset AND
# @plugin_commandset.opts(kwargs)
boop_commandset.opts = lambda *args,**kwargs: \
                          lambda x: boop_commandset(x,*args,**kwargs)

