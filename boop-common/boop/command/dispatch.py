from boop.common import *
from boop.command.commandset import *
import shlex
import types
import StringIO
import sys


class BoopCommandSetDispatch(BoopBase):
  """ Available commands.
  """

  def __init__(self,context,*args,**kwargs):
    super(BoopCommandSetDispatch,self).__init__(*args,**kwargs)
    self._commandsets = []
    self._indent = '  '
    self._context = context

  def commandset_add(self,commandset_class,context=None,*args,**kwargs):
    commandset_obj = commandset_class(
                        context=context or self._context.copy(),
                        *args,
                        **kwargs
                      )
    self._commandsets.append({
      'name': commandset_obj._instance_name,
      'commandset': commandset_obj,
    })
    return commandset_obj

  def execute(self,s):
    args = shlex.split(s)
    if not args: return None
    command = args[0]
    for cs_info in self._commandsets:
      cs = cs_info['commandset']
      if cs.match(command):
        return cs.execute(args)

    return None

  def help(self,target=None):

    # FIXME: what to do with the self.__doc__?
    help_text = textwrap.dedent(self.__doc__).strip()+"\n\n"

    # If there is no target, just return a list of commands
    if not target:
      for cs_info in self._commandsets:
        help_text += self._indent \
                      + cs_info['name'] \
                      + "  " \
                      + cs_info['commandset'].help_synopsis() \
                      + "\n"

    # If there is a target, we need to query the commandsets
    else:
      # elements = re.split('\s+',target.strip())
      # return repr(target)

      elements = re.split('\s+',target)
      command = elements[0]

      for cs_info in self._commandsets:
        if cs_info['name'] == command:
          help_text = cs_info['commandset'].help(target)

    return help_text
      

