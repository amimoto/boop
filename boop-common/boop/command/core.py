from boop.common import *
from boop.command.docopt import BoopDocOpt
import shlex
import re
import textwrap
import types
import StringIO
import sys


__all__ = ['CommandRunner','CommandParser','CommandSet','commandset']


def cs_command(command_func):
  doc = command_func.__doc__
  command_func._boop_docopt = BoopDocOpt(doc)
  command_func._command_type = 'commandset'
  return command_func

def cs_commandset(commandset_class):
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

class CS(BoopBase):

  _instance_pattern = None

  def __init__( self,
                instance_pattern=None,
                *args,
                **kwargs):
    super(CS,self).__init__(*args,**kwargs)

    self._instance_pattern = instance_pattern or self.instance_pattern()
    self._regex = re.compile(self.instance_pattern())

    for l in self._boop_docopts:
      l['docopt'].name(self._instance_name)
      l['docopt'].pattern(self._instance_pattern)


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

class CSD(BoopBase):

  def __init__(self,commandsets=[],*args,**kwargs):
    super(CSD,self).__init__(*args,**kwargs)
    self._commandsets = []
    for commandset in commandsets:
      self.commandset_add(commandset)

  def commandset_add(self,commandset):
    self._commandsets.append({
      'name': commandset._instance_name,
      'commandset': commandset,
    })

  def execute(self,s,context):
    args = shlex.split(s)
    if not args: return None
    command = args[0]
    for cs_info in self._commandsets:
      cs = cs_info['commandset']
      if cs.match(command):
        return cs.execute(args,context)

    return None

def docopt_parse(doc, argv=None, help=True, version=None, options_first=False):
  """ docopt.docopt extracted to remove sys.exit()s when encountering
      things like -h

      Extracted from docopt to avoid calling the extras function (returns
      the help text)

  """

  '''
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
  '''
  return {}



class HandleSlots(object):
  """
  Hook Functions should have the property
  func._hook_slots = {

     # if the consumption hook is only on certain
     # situations
     'slot_name': lambda hook: return True, 

     # if there are no conditions and we accept
     # all hooks with the slot_name...
     'slot_name': None

     ...

  }
  """

  def hook(self,condition,hooks,func):
    hook_slots = {}
    for hook_slot in hooks:
      hook_slots[hook_slot] = condition
    func._hook_slots = hook_slots
    return func

  def when(self,condition):
    return lambda func: self.hook(condition,['ALL'],func)

  def __getattr__(self,k):
    return lambda func: self.hook(None,[k.lower()],func)

handle = HandleSlots()

# ##################################################
# Command set decorators
# ##################################################
def commandset(commandset_class):
  # Go through the parent classes and look for a __doc__ if the
  # current doesn't have one

  _hook_handlers = {}

  # First do the super classes
  for base in commandset_class.__bases__:
    if '_hook_handlers' in dir(base):
      _base_hook_handlers = getattr(base,'_hook_handlers')
      for name, attrs in  _base_hook_handlers.iteritems():
        _hook_handlers.setdefault(name,{})\
                       .update(attrs)

  # Then do the local class as it'll handle overrides
  for attr_name in dir(commandset_class):
    attr = getattr(commandset_class,attr_name)
    if not '_hook_slots' in dir(attr):
      continue

    # If we're here, this attribute is a consumer
    _hook_slots = getattr(attr,'_hook_slots')

    # Build the struct for this level
    for slot_name,condition in _hook_slots.iteritems():
      _hook_handlers.setdefault(slot_name,{})[attr_name] = condition

  commandset_class._hook_handlers = _hook_handlers

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

class CommandSet(BoopBase):
  """
  CommandSet classes define and handle the execution of commands.

  Commands are defined in docopt format (unless overriden) and handled
  via the execute/hook mechanism.

  An example class definition may look thus:

  @commandset
  class MyCommandSet(CommandSet):
    '''
    My Example Command Set

    Usage:

      say howdy
      say hello <name>
      say goodbye <name>

    '''
    name = 'say'

  In this case there are three commands defined. Two of the commands expect
  a parameter. If this object were to use a command dispatch, the name (currently
  'say') would be used by the dispatcher to where incoming commands should go. (eg.
  perhaps there's another commandset object defining 'run')
  
  For a commandset to receive the parsed arguments and act upon them, there are
  two mechanisms. One is to override def execute(self,parsed_attribs,parent), however,
  there happens to be a method that's a bit more syntactically elegant.

  Extending our previous example:

    ... [snip] ...

    name = 'say'

    @handle.HOWDY
    def howdy(self,attrs,parent):
      print "Howdy!"

    @handle.HELLO
    def hello(self,attrs,parent):
      print "Hello", attrs['<name>']

    @handle.when(lambda s,a,p:'goodbye' in a)
    def goodbye(self,attrs,parent):
      print "Hello", attrs['<name>']

  self._hook_handlers = {
     'hook_name': {
                  'attr_name': lambda self,attrs,parent: return True
                  ... 
                  },
  }


  """


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

    pass
    # FIXME
    #attrs = docopt_parse(self.doc,argv=argv[1:])
    #return attrs

  def execute(self,attrs,parent):
    """ With the attributes that parse has yielded,
        execute what actions have been requested
    """

    # We redirect stdout to a stringio object so 
    # a number of sub execute scan be processed
    capture_io = StringIO.StringIO()
    previous_io = sys.stdout
    sys.stdout = capture_io

    # First hit all elements for that slot
    for hook_name,handlers in self._hook_handlers.iteritems():
      if hook_name in attrs:
        for attr_name,func in handlers.iteritems():
          if func == None or func(self,attrs,parent):
            getattr(self,attr_name)(attrs,parent)

    # Then handle all the "ALL" hits
    if 'ALL' in self._hook_handlers:
      for attr_name,func in self._hook_handlers['ALL'].iteritems():
        if func == None or func(self,attrs,parent):
          getattr(self,attr_name)(attrs,parent)
  
    sys.stdout = previous_io
    output = capture_io.getvalue().rstrip()
    return output

  def unload(self):
    """ Called when this object is destroyed
    """
    return


class CommandParser(BoopBase):
  """
  >>> cparser = CommandParser()
  >>> result = cparser.parse("-h")
  >>> result['-h']
  True

  """

  default_commands = """
  Usage:
     > help [<command>]

  Where command can be any of the following:

  """

  def init(self,commandsets=None,*arg,**kwargs):
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
      command_obj = self.commandset_registry[commandset_name]
      return command_obj.parse(argv,parent)
    attrs = docopt_parse(CommandParser.default_commands,argv=argv)
    return attrs


class CommandRunner(CommandParser):

  def help(self,argv,parent):
    commandset_name = argv[1]
    if commandset_name in self.commandset_registry:
      commandset = self.commandset_registry[commandset_name]
      attrs = commandset.parse(argv,parent)
      output = textwrap.dedent(commandset.doc)
      return {
        'attrs': attrs,
        'output': output
      }

  def execute(self,s,parent=None):
    argv = shlex.split(s)

    # Requesting help?
    if argv[0] == 'help':
      if len(argv)>1:
        return self.help(argv,parent)

      # TODO help for commandsets
      attrs = docopt_parse(CommandParser.default_commands,argv=argv)
      help_text = textwrap.dedent(self.default_commands)
      for (commandset_name,commandset) in self.commandset_registry.iteritems():
        synopsis = commandset.commandset_synopsis()
        help_text += "{commandset_name:15} {synopsis}\n".format(
                          commandset_name=commandset_name,
                          synopsis=synopsis,
                        )


      help_text = textwrap.dedent(help_text)
      return { 'attrs': attrs, 'output': help_text }

    # Executing a command?
    commandset_name = argv[0]
    if commandset_name in self.commandset_registry:
      commandset = self.commandset_registry[commandset_name]
      attrs = commandset.parse(argv,parent)
      output = commandset.execute(attrs,parent)
      return { 'attrs': attrs, 'output': output }

    # FIXME: better error message
    raise Exception('Cannot handle ecommand')


