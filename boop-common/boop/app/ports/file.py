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

  def init(self,*args,**kwargs):
    self._open_files = {}
    self._selected_file = None
    super(BoopFilePlugin,self).init(*args,**kwargs)

  @boop_runnable.opts(start='manual')
  class FileRunnable(BoopFileRunnable):
    name = 'filerunnable'

  @boop_commandset
  class FileCommandSet(BoopCommandSet):
    name = "f"


    @command
    def file_list(self,attrs):
      """
      List currently opened files.

      Usage:
        f list
      """

      # FIXME: Do I really want this setup?
      # Maybe better to override __str__ in FileRunnable?
      report = ''
      for fpath, fobj in self.plugin._open_files.iteritems():
        report += "{port_key}: {fpath}\n".format(
                          port_key=fobj.port_key,
                          fpath=fpath
                        )

      return report


    @command
    def file_select(self,attrs):
      """
      Usage:
        f select <data> ...
      """
      fpath = attrs['<file path>']
      fobj = self.plugin.class_start(self.plugin.FileRunnable,name=fpath)
      self.plugin._open_files[fpath] = fobj
      return "Success!"

    @command
    def file_open(self,attrs):
      """
      Open a new file for reading. Requires the path to the file.

      Usage:
        f open [-w] <file path>
      """
      fpath = attrs['<file path>']
      kwargs = {'name':fpath}
      if attrs['-w']: kwargs['mode'] = 'w+'
      fobj = self.plugin.class_start(self.plugin.FileRunnable,**kwargs)
      self.plugin._open_files[fpath] = fobj
      self.plugin._selected_file = fobj
      return "OK"


    @command
    def file_write(self,attrs):
      """
      Usage:
        f writeln <data> ...
        f write <data> ...
      """
      data = " ".join(attrs['<data>'])
      if attrs['writeln']:
        data += "\n"
      self.plugin._selected_file.send(data)
      return "OK"

  def send(self,s):
    self.object_byinstancename('').send(s)

