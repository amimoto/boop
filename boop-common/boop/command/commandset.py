from boop.common import *
from boop.command.docopt import BoopDocOpt
import re
import textwrap

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

class BoopCommandSet(BoopBase):
  """ Holds a collection of command definitions 
      and implementations that are thematically
      unified.
  """

  _instance_pattern = None
  _context = None
  _regex = None
  _indent = None

  def __init__( self,
                context,
                instance_pattern=None,
                *args,
                **kwargs):
    super(BoopCommandSet,self).__init__(*args,**kwargs)

    self._instance_pattern = instance_pattern or self.instance_pattern()
    self._regex = re.compile(self.instance_pattern())
    self._context = context
    self._indent = '  '

    for l in self._boop_docopts:
      l['docopt'].name(self._instance_name)
      l['docopt'].pattern(self._instance_pattern)

  def context(self):
    """ Returns any application related data
    """
    return self._context

  def help_synopsis(self):
    # FIXME this should have a more robust way of
    # extracting the one-liner
    split = re.split('\n', self.__doc__ or '')
    for l in split:
      l = l.strip()
      if l: return l
    return ''

  def help(self,target=None):

    # FIXME: what to do with the self.__doc__?
    help_text = textwrap.dedent(self.__doc__).strip()+"\n\n"
    help_text += "Usage:\n"

    # If we are trying to match a specific pattern
    # FIXME: give detailed help if there's just one match
    options = {}
    for l in self._boop_docopts:
      docopt = l['docopt']
      usage = docopt.help_usage(target)
      if usage: 
        # synopsis = docopt.synopsis_extract()
        indent = self._indent
        # if synopsis:
        #   help_text += indent+synopsis+"\n"
        #   indent += self._indent
        for default in docopt.options_parse():
          options[str(default)] = default
        for l in usage:
          help_text += indent+" ".join(l)+"\n"

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

  def execute(self,argv):
    for l in self._boop_docopts:
      attrs = l['docopt'].parse(argv)
      if attrs:
        return getattr(self,l['attr_name'])(attrs)
    return None

  def unload(self):
    super(BoopPluginBoopCommandSet,self).unload()
    self._context= None

  def __getattr__(self,attr):
    if attr in self._context:
      return getattr(self._context,attr)
    raise AttributeError(
              "%s does not have attribute %s"%(
              type(self).__name__,
              attr
            ))


