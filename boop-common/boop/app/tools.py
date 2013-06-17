from boop.app.core import *
from boop.command import *

__all__ = [
  'PluginHelpApp'
]


@boop_plugin
class PluginHelpApp(BoopPlugin):

  @boop_commandset
  class PluginHelpCommandSet(BoopCommandSet):
    """ Application Help
    """

    name = 'help'

    @command
    def help_simple(self,attrs):
      """
      Usage:
        help
      """
      return self._context.app.commands.help()

    @command
    def help_context(self,attrs):
      """
      Usage:
        help <key> ...
      """
      return self._context.app.commands.help(" ".join(attrs['<key>']))




