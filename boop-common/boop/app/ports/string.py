from boop.event import *
from boop.event.ports.string import *
from boop.command import *
from boop.app import *

@boop_plugin
class PortStringPlugin(BoopPlugin):
  """ This provides StringIO async handling for Boop. This probably won't be used 
      by anyone and will more be used by the test system. Who knows though...

      boop.event.ports.string provides the event handlers. This module, 
      boop.app.ports.string wraps the event handlers into a single object with
      a commandset to handle interactions with the port.
  """

  def init(self,*args,**kwargs):
    print "INIT PortStringPlugin:", args, kwargs

  @boop_commandset
  class PluginSerialCommandSet(BoopCommandSet):
    name = "stringserial"

    @command
    def string_open(self,attrs):
      """
      Usage:
        stringserial open
      """

  @boop_runnable.opts(start='manual')
  class PortStringRunnable(StringBoopEventRunnable):
    pass

  def send(self,s):
    self.object_byinstancename('').send(s)

