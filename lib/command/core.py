import doctest
from thirdparty import docopt
import shlex
import re

def docopt_parse(doc, argv=None, help=True, version=None, options_first=False):
    """ docopt.docopt extracted to remove sys.exit()s when encountering
        things like -h
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

class Command(object):

    def __init__(self):
      self.name = self.commandset_name()

    def commandset_name(self):
      return type(self).__name__[7:].lower()

    def commandset_synopsis(self):
      match = re.search('([^\s\n][^\n]*)\n',self.__doc__)
      return match.group(1)

    def parse(self,argv,core=None):
      attrs = docopt_parse(self.__doc__,argv)
      return self.run(attrs,core)

    def run(self,attrs,core=None):
      return attrs

    def unload(self,*args,**kwargs):
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
      return command_obj.name

    def commandset_remove(self,name,*arg,**kwargs):
      if name in self.commandset_registry:
        self.commandset_registry.pop(name).unload(*arg,**kwargs)

    def commandset_list(self):
      return self.commandset_registry.keys()

    def parse(self,s,core=None):
      argv = shlex.split(s)
      commandset_name = argv[0]
      if commandset_name in self.commandset_registry:
          command_parser = self.commandset_registry[commandset_name]
          argv.pop(0)
          return command_parser.parse(argv,core)
      attrs = docopt_parse(CommandParser.default_commands,argv=argv)
      return attrs


class CommandRunner(CommandParser):

    def execute(self,s,core=None):
      attrs = self.parse(s,core)
      result = self.run(attrs,core)
      return result

    def run(self,attrs,core=None):
      if not core: return
      if attrs['<command>'] in self.commandset_registry:
        help_text = self.commandset_registry[attrs['<command>']].__doc__
        return { 'attrs': attrs, 'output': help_text }

      help_text = self.default_commands
      for (commandset_name,commandset) in self.commandset_registry.iteritems():
        synopsis = commandset.commandset_synopsis()
        help_text += "{commandset_name:15} {synopsis}".format(
                          commandset_name=commandset_name,
                          synopsis=synopsis,
                        )

      return { 'attrs': attrs, 'output': help_text }

if __name__ == "__main__":
  import doctest
  doctest.testmod()


