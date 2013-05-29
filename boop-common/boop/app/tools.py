from boop.app.core import *
from boop.command import *

__all__ = [
  'PluginHelpApp'
]


@plugin_app
class PluginHelpApp(PluginEventsApp):

  @plugin_commandset
  class PluginHelpCommandSet(PluginCommandSet):
    """ Application Help
    """

    name = 'help'

    @command
    def help_simple(self,attrs,context):
      """
      Usage:
        help
      """
      return self.app.commands.help()

    @command
    def help_context(self,attrs,context):
      """
      Usage:
        help <key> ...
      """
      return self.app.commands.help(" ".join(attrs['<key>']))




