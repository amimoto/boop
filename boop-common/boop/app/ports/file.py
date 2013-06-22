from boop.event import *
from boop.event.ports.file import *
from boop.command import *
from boop.app import *

@boop_plugin
class BoopFilePlugin(BoopPlugin):
  """ This provides FileIO async handling for Boop. This probably won't be used 
      by anyone and will more be used by the test system. Who knows though...

      boop.event.ports.string provides the event handlers. This module, 
      boop.app.ports.string wraps the event handlers into a single object with
      a commandset to handle interactions with the port.
  """

  @boop_runnable.opts(start='manual')
  class FileRunnable(BoopFileRunnable):
    name = 'filerunnable'

  @boop_commandset
  class FileCommandSet(BoopCommandSet):
    name = "f"

    @command
    def string_open(self,attrs):
      """
      Usage:
        f open <file path>
      """
      fpath = attrs['<file path>']
      fobj = self.plugin.class_start(self.plugin.FileRunnable,name=fpath)
      return "Success!"

  def send(self,s):
    self.object_byinstancename('').send(s)

