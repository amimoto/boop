import doctest
from thirdparty import docopt
import shlex

command_registry = {}

def command(obj):
  obj()
  return obj

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
      command_name = type(self).__name__[7:].lower()
      command_registry[command_name] = self
      pass

    def parse(self,s,core=None):
      attrs = docopt_parse(self.__doc__,shlex.split(s))
      return self.run(attrs,core)

    def run(self,attrs,core=None):
      return attrs

class CommandParser(object):
    """
    >>> cparser = CommandParser()
    >>> result = cparser.parse("-h")
    >>> result['-h']
    True

    """

    default_commands = """
    Usage:
       > -h|--help|help

    """

    def parse(self,s,core=None):
      global command_registry
      argv = shlex.split(s)
      command_name = argv[0]
      if command_name in command_registry:
          argv.pop(0)
          command_parser = command_registry[command_name]
          return command_parser.parse(s,core)
      result = docopt_parse(CommandParser.default_commands,argv=argv)
      return result

if __name__ == "__main__":
  import doctest
  doctest.testmod()


