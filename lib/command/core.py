import doctest
from thirdparty import docopt
import shlex
import re
import textwrap
import types

__all__ = ['CommandRunner','CommandParser','CommandSet','commandset']

def docopt_parse(doc, argv=None, help=True, version=None, options_first=False):
    """ docopt.docopt extracted to remove sys.exit()s when encountering
        things like -h

        Extracted from docopt to avoid calling the extras function (returns
        the help text)

    """
    if argv is None: return {}
    docopt.DocoptExit.usage = docopt.printable_usage(doc)
    options = docopt.parse_defaults(doc)
    pattern = docopt.parse_pattern(docopt.formal_usage(docopt.DocoptExit.usage), options)
    argv = docopt.parse_argv(docopt.Tokens(argv), list(options), options_first)
    pattern_options = set(pattern.flat(docopt.Option))
    for ao in pattern.flat(docopt.AnyOptions):
        doc_options = docopt.parse_defaults(doc)
        ao.children = list(set(doc_options) - pattern_options)
    matched, left, collected = pattern.fix().match(argv)
    if matched and left == []:  # better error message if left?
        return docopt.Dict((a.name, a.value) for a in (pattern.flat() + collected))
    return {}


def commandset(commandset_class):
  # Go through the parent classes and look for a __doc__ if the
  # current doesn't have one

  # FIXME It doesn't appear that __doc__ is inherited
  if '__doc__' not in dir(commandset_class) or commandset_class.__doc__ == None:
    for base in commandset_class.__bases__:
      if '__doc__' in dir(base):
        setattr(commandset_class,'doc',base.__doc__)
        break
  else:
    setattr(commandset_class,'doc',commandset_class.__doc__)

  setattr(commandset_class,'doc',textwrap.dedent(commandset_class.doc))

  if not 'name' in dir(commandset_class):
    for base in commandset_class.__bases__:
      if 'commandset_name' in dir(base):
        commandset_class.name = base.commandset_name(commandset_class)
        break

  return commandset_class

class CommandSet(object):

    def __init__(self,*args,**kwargs):
      self.init(*args,**kwargs)

    def init(self):
      pass

    @staticmethod
    def commandset_name(obj):
      """ Lower casename of the class. Can be overriden for 
          other special purposes. This is used to determine... FIXME
      """
      if isinstance(obj, (type, types.ClassType)):
        return obj.__name__
      else:
        return type(obj).__name__


    def commandset_synopsis(self):
      """ Return a one line description of what this commandset 
          does. Pulled from the doc of the object
      """
      match = re.search('([^\s\n][^\n]*)\n',self.doc)
      return match.group(1)

    def parse(self,argv,parent):
      """ Parse the argv for the command object. This returns
          just the output from docopt normally but just in case
          you want some special parsing you can handle that here
      """
      attrs = docopt_parse(self.doc,argv=argv[1:])
      return attrs

    def execute(self,attrs,parent):
      """ With the attributes that parse has yielded,
          execute what actions have been requested
      """
      return { 'attrs': attrs, 'output': self.doc }

    def unload(self):
      """ Called when this object is destroyed
      """
      return


class CommandParser(object):
    """
    >>> cparser = CommandParser()
    >>> result = cparser.parse("-h")
    >>> result['-h']
    True

    """

    default_commands = """
    Usage:
       > (-h|--help|help) [<command>]

    Where command can be any of the following:

    """

    def __init__(self,commandsets=None,*arg,**kwargs):
      self.commandset_registry = {}
      if commandsets:
        for commandset in commandsets:
          self.commandset_add(commandset,*arg,**kwargs)

    def commandset_add(self,command_class,*arg,**kwargs):
      command_obj = command_class(*arg,**kwargs)
      self.commandset_registry[command_obj.name] = command_obj
      return command_obj

    def commandset_remove(self,command_obj,*arg,**kwargs):
      name = command_obj.name
      if name in self.commandset_registry:
        self.commandset_registry.pop(name).unload(*arg,**kwargs)

    def commandset_list(self):
      return self.commandset_registry.keys()

    def parse(self,s,parent=None):
      argv = shlex.split(s)
      commandset_name = argv[0]
      if commandset_name in self.commandset_registry:
        command_parser = self.commandset_registry[commandset_name]
        argv.pop(0)
        return command_parser.parse(argv,parent)
      attrs = docopt_parse(CommandParser.default_commands,argv=argv)
      return attrs


class CommandRunner(CommandParser):

    def execute(self,s,parent):

      # No parent, no love
      if not parent: return

      # Just slamming enter? no love either
      argv = shlex.split(s)
      if not argv: return

      # Are we dealing with a sub command?
      commandset_name = argv[0]
      if commandset_name in self.commandset_registry:
        commandset = self.commandset_registry[commandset_name]
        attrs = commandset.parse(argv,parent)
        return commandset.execute(attrs,parent)

      # TODO help for commandsets
      attrs = docopt_parse(CommandParser.default_commands,argv=argv)
      help_text = self.default_commands
      for (commandset_name,commandset) in self.commandset_registry.iteritems():
        synopsis = commandset.commandset_synopsis()
        help_text += "{commandset_name:15} {synopsis}".format(
                          commandset_name=commandset_name,
                          synopsis=synopsis,
                        )

      return { 'attrs': attrs, 'output': help_text }


