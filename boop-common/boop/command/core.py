from boop.common import *
from boop.command.docopt import BoopDocOpt
import shlex
import re
import textwrap
import types
import StringIO
import sys


__all__ = ['CommandSet','CommandSetDispatch','command','commandset']


def command(command_func):
  doc = command_func.__doc__
  command_func._boop_docopt = BoopDocOpt(doc)
  command_func._command_type = 'commandset'
  # FIXME: Identify potentially conflicting commandsets
  return command_func

def commandset(commandset_class):
  docopts = []
  # Then do the local class as it'll handle overrides
  for attr_name in dir(commandset_class):
    attr = getattr(commandset_class,attr_name)
    if not '_command_type' in dir(attr):
      continue
    docopt = attr._boop_docopt
    docopts.append({
      'attr_name': attr_name,
      'docopt': docopt
    })
  commandset_class._boop_docopts = docopts
  return commandset_class

class CommandSet(BoopBase):
  """ Holds a collection of command definitions 
      and implementations that are thematically
      unified.
  """

  _instance_pattern = None

  def __init__( self,
                initial_context=None,
                instance_pattern=None,
                *args,
                **kwargs):
    super(CommandSet,self).__init__(*args,**kwargs)

    self._instance_pattern = instance_pattern or self.instance_pattern()
    self._regex = re.compile(self.instance_pattern())
    self._initial_context = initial_context
    self._indent = '  '

    for l in self._boop_docopts:
      l['docopt'].name(self._instance_name)
      l['docopt'].pattern(self._instance_pattern)

  def initial_context(self):
    """ Returns any application related data
    """
    return self._initial_context

  def help(self,target=None):

    # FIXME: what to do with the self.__doc__?
    help_text = textwrap.dedent(self.__doc__).strip()+"\n\n"
    help_text += "Usage:\n"

    # If we are trying to match a specific pattern
    options = {}
    for l in self._boop_docopts:
      docopt = l['docopt']
      usage = docopt.help_usage(target) if target \
                  else docopt.help_usage(target)
      if usage: 
        help_text += self._indent+docopt.synopsis_extract()+"\n"
        for default in docopt.options_parse():
          options[str(default)] = default
        for l in usage:
          help_text += self._indent*2+" ".join(l)+"\n"

    # If there are any special options, we'll include
    # that in the output as well
    if options:
      help_text += "\nOptions:\n"
      for k in sorted(options.keys()):
        option = options[k]
        help_text += self._indent+option.description + "\n"

    return help_text


  def instance_pattern(self):
    if self._instance_pattern != None:
      return self._instance_pattern
    elif 'pattern' in dir(self):
      return getattr(self,'pattern')
    else:
      return self.instance_name()

  def match(self,s):
    return self._regex.match(s)

  def execute(self,argv,context):
    for l in self._boop_docopts:
      attrs = l['docopt'].parse(argv)
      if attrs:
        return getattr(self,l['attr_name'])(attrs,context)
    return None

class CommandSetDispatch(BoopBase):

  def __init__(self,commandsets=[],*args,**kwargs):
    super(CommandSetDispatch,self).__init__(*args,**kwargs)
    self._commandsets = []
    for commandset in commandsets:
      self.commandset_add(commandset)

  def commandset_add(self,commandset):
    self._commandsets.append({
      'name': commandset._instance_name,
      'commandset': commandset,
    })
    return commandset

  def execute(self,s,context):
    args = shlex.split(s)
    if not args: return None
    command = args[0]
    for cs_info in self._commandsets:
      cs = cs_info['commandset']
      if cs.match(command):
        return cs.execute(args,context)

    return None


