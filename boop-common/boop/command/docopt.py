"""

Pythonic command-line interface parser that will make you smile.

Please note that there have been significant changes made to the 
docopt code and it is no longer compatible with the documentation.

 * http://docopt.org
 * Repository and issue-tracker: https://github.com/docopt/docopt
 * Licensed under terms of MIT license (see LICENSE-MIT)
 * Copyright (c) 2013 Vladimir Keleshev, vladimir@keleshev.com

"""
import sys
import re

from pprint import pprint as pp

__all__ = []
__version__ = '0.0.1' # This is not compatible with docopt


class DocoptLanguageError(Exception):

    """Error in construction of usage-message by developer."""


class DocoptExit(SystemExit):

    """Exit in case user invoked program with incorrect arguments."""

    usage = ''

    def __init__(self, message=''):
        SystemExit.__init__(self, (message + '\n' + self.usage).strip())


class Pattern(object):

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __hash__(self):
        return hash(repr(self))

    def fix(self):
        self.fix_identities()
        self.fix_repeating_arguments()
        return self

    def fix_identities(self, uniq=None):
        """Make pattern-tree tips point to same object if they are equal."""
        if not hasattr(self, 'children'):
            return self
        uniq = list(set(self.flat())) if uniq is None else uniq
        for i, c in enumerate(self.children):
            if not hasattr(c, 'children'):
                assert c in uniq
                self.children[i] = uniq[uniq.index(c)]
            else:
                c.fix_identities(uniq)

    def fix_repeating_arguments(self):
        """Fix elements that should accumulate/increment values."""
        either = [list(c.children) for c in self.either.children]
        for case in either:
            for e in [c for c in case if case.count(c) > 1]:
                if type(e) is Argument or type(e) is Option and e.argcount:
                    if e.value is None:
                        e.value = []
                    elif type(e.value) is not list:
                        e.value = e.value.split()
                if type(e) is Command or type(e) is Option and e.argcount == 0:
                    e.value = 0
        return self

    @property
    def either(self):
        """Transform pattern into an equivalent, with only top-level Either."""
        # Currently the pattern will not be equivalent, but more "narrow",
        # although good enough to reason about list arguments.
        ret = []
        groups = [[self]]
        while groups:
            children = groups.pop(0)
            types = [type(c) for c in children]
            if Either in types:
                either = [c for c in children if type(c) is Either][0]
                children.pop(children.index(either))
                for c in either.children:
                    groups.append([c] + children)
            elif Required in types:
                required = [c for c in children if type(c) is Required][0]
                children.pop(children.index(required))
                groups.append(list(required.children) + children)
            elif Optional in types:
                optional = [c for c in children if type(c) is Optional][0]
                children.pop(children.index(optional))
                groups.append(list(optional.children) + children)
            elif AnyOptions in types:
                optional = [c for c in children if type(c) is AnyOptions][0]
                children.pop(children.index(optional))
                groups.append(list(optional.children) + children)
            elif OneOrMore in types:
                oneormore = [c for c in children if type(c) is OneOrMore][0]
                children.pop(children.index(oneormore))
                groups.append(list(oneormore.children) * 2 + children)
            else:
                ret.append(children)
        return Either(*[Required(*e) for e in ret])


class ChildPattern(Pattern):

    def __init__(self, name, value=None):
        self.name = name
        self.value = value

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.name, self.value)

    def flat(self, *types):
        return [self] if not types or type(self) in types else []

    def match(self, left, collected=None):
        collected = [] if collected is None else collected
        pos, match = self.single_match(left)
        if match is None:
            return False, left, collected
        left_ = left[:pos] + left[pos + 1:]
        same_name = [a for a in collected if a.name == self.name]
        if type(self.value) in (int, list):
            if type(self.value) is int:
                increment = 1
            else:
                increment = ([match.value] if type(match.value) is str
                             else match.value)
            if not same_name:
                match.value = increment
                return True, left_, collected + [match]
            same_name[0].value += increment
            return True, left_, collected
        return True, left_, collected + [match]


    def dump(self,indent=0):
      return '%s%s(%r, %r)\n' % ("  "*indent, self.__class__.__name__, self.name, self.value)


class ParentPattern(Pattern):

    def __init__(self, *children):
        self.children = list(children)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join(repr(a) for a in self.children))

    def flat(self, *types):
        if type(self) in types:
            return [self]
        return sum([c.flat(*types) for c in self.children], [])

    def dump(self,indent=0):
      o = "%s%s\n" % ("  "*indent, self.__class__.__name__)
      for p in self.children:
        o += p.dump(indent+1)
      if len(self.children)>1:
        o+="\n"
      return o

class Argument(ChildPattern):

    def single_match(self, left):
        for n, p in enumerate(left):
            if type(p) is Argument:
                return n, Argument(self.name, p.value)
        return None, None

    @classmethod
    def parse(class_, source):
        name = re.findall('(<\S*?>)', source)[0]
        value = re.findall('\[default: (.*)\]', source, flags=re.I)
        return class_(name, value[0] if value else None)


class Command(Argument):

  def __init__(self, name, value=False):
    self.name = name
    self.value = value

  def single_match(self, left):
    for n, p in enumerate(left):
      if type(p) is Argument:
        if p.value == self.name:
          return n, Command(self.name, True)
        elif re.match(self.name,p.value):
          return n, Command(self.name, True)
        else:
          break
    return None, None


class Option(ChildPattern):

    def __init__(self, short=None, long=None, argcount=0, value=False):
        assert argcount in (0, 1)
        self.short, self.long = short, long
        self.argcount, self.value = argcount, value
        self.value = None if value is False and argcount else value

    @classmethod
    def parse(class_, option_description):
        short, long, argcount, value = None, None, 0, False
        options, _, description = option_description.strip().partition('  ')
        options = options.replace(',', ' ').replace('=', ' ')
        for s in options.split():
            if s.startswith('--'):
                long = s
            elif s.startswith('-'):
                short = s
            else:
                argcount = 1
        if argcount:
            matched = re.findall('\[default: (.*)\]', description, flags=re.I)
            value = matched[0] if matched else None
        return class_(short, long, argcount, value)

    def single_match(self, left):
      for n, p in enumerate(left):
        if self.name == p.name:
          return n, p
        elif re.match(self.name, p.name):
          return n, p
      return None, None

    @property
    def name(self):
      return self.long or self.short

    def __repr__(self):
      return 'Option(%r, %r, %r, %r)' % (self.short, self.long,
                                         self.argcount, self.value)


class Required(ParentPattern):

    def match(self, left, collected=None):
        collected = [] if collected is None else collected
        l = left
        c = collected
        for p in self.children:
            matched, l, c = p.match(l, c)
            if not matched:
                return False, left, collected
        return True, l, c


class Optional(ParentPattern):

    def match(self, left, collected=None):
        collected = [] if collected is None else collected
        for p in self.children:
            m, left, collected = p.match(left, collected)
        return True, left, collected


class AnyOptions(Optional):

    """Marker/placeholder for [options] shortcut."""


class OneOrMore(ParentPattern):

    def match(self, left, collected=None):
        assert len(self.children) == 1
        collected = [] if collected is None else collected
        l = left
        c = collected
        l_ = None
        matched = True
        times = 0
        while matched:
            # could it be that something didn't match but changed l or c?
            matched, l, c = self.children[0].match(l, c)
            times += 1 if matched else 0
            if l_ == l:
                break
            l_ = l
        if times >= 1:
            return True, l, c
        return False, left, collected


class Either(ParentPattern):

    def match(self, left, collected=None):
        collected = [] if collected is None else collected
        outcomes = []
        for p in self.children:
            matched, _, _ = outcome = p.match(left, collected)
            if matched:
                outcomes.append(outcome)
        if outcomes:
            return min(outcomes, key=lambda outcome: len(outcome[1]))
        return False, left, collected


class Tokens(list):

    def __init__(self, source, error=DocoptExit):
        self += source.split() if hasattr(source, 'split') else source
        self.error = error

    @staticmethod
    def from_pattern(source):
        source = re.sub(r'([\[\]\(\)\|]|\.\.\.)', r' \1 ', source)
        source = [s for s in re.split('\s+|(\S*<.*?>)', source) if s]
        return Tokens(source, error=DocoptLanguageError)

    def move(self):
        return self.pop(0) if len(self) else None

    def current(self):
        return self[0] if len(self) else None


def parse_long(tokens, options):
    """long ::= '--' chars [ ( ' ' | '=' ) chars ] ;"""
    long, eq, value = tokens.move().partition('=')
    assert long.startswith('--')
    value = None if eq == value == '' else value
    similar = [o for o in options if o.long == long]
    if tokens.error is DocoptExit and similar == []:  # if no exact match
        similar = [o for o in options if o.long and o.long.startswith(long)]
    if len(similar) > 1:  # might be simply specified ambiguously 2+ times?
        raise tokens.error('%s is not a unique prefix: %s?' %
                           (long, ', '.join(o.long for o in similar)))
    elif len(similar) < 1:
        argcount = 1 if eq == '=' else 0
        o = Option(None, long, argcount)
        options.append(o)
        if tokens.error is DocoptExit:
            o = Option(None, long, argcount, value if argcount else True)
    else:
        o = Option(similar[0].short, similar[0].long,
                   similar[0].argcount, similar[0].value)
        if o.argcount == 0:
            if value is not None:
                raise tokens.error('%s must not have an argument' % o.long)
        else:
            if value is None:
                if tokens.current() is None:
                    raise tokens.error('%s requires argument' % o.long)
                value = tokens.move()
        if tokens.error is DocoptExit:
            o.value = value if value is not None else True
    return [o]


def parse_shorts(tokens, options):
    """shorts ::= '-' ( chars )* [ [ ' ' ] chars ] ;"""
    token = tokens.move()
    assert token.startswith('-') and not token.startswith('--')
    left = token.lstrip('-')
    parsed = []
    while left != '':
        short, left = '-' + left[0], left[1:]
        similar = [o for o in options if o.short == short]
        if len(similar) > 1:
            raise tokens.error('%s is specified ambiguously %d times' %
                               (short, len(similar)))
        elif len(similar) < 1:
            o = Option(short, None, 0)
            options.append(o)
            if tokens.error is DocoptExit:
                o = Option(short, None, 0, True)
        else:  # why copying is necessary here?
            o = Option(short, similar[0].long,
                       similar[0].argcount, similar[0].value)
            value = None
            if o.argcount != 0:
                if left == '':
                    if tokens.current() is None:
                        raise tokens.error('%s requires argument' % short)
                    value = tokens.move()
                else:
                    value = left
                    left = ''
            if tokens.error is DocoptExit:
                o.value = value if value is not None else True
        parsed.append(o)
    return parsed


class Dict(dict):
    def __repr__(self):
        return '{%s}' % ',\n '.join('%r: %r' % i for i in sorted(self.items()))

class BoopDocOpt(object):

  def __init__(self,doc,name=None,pattern=None):
    self._doc = doc
    self._name = name
    self._pattern = pattern
    self._cache = {}

  def __str__(self):
    import textwrap
    return textwrap.dedent(self._doc.strip('\n'))

  def doc(self,doc=None):
    if doc:
      self._doc = doc
      self.reset()
    return self._doc

  def pattern(self,pattern=None):
    if pattern:
      self._pattern = pattern
      self.reset()
    return self._pattern

  def name(self,name=None):
    if name:
      self._name = name
      self.reset()
    return self._name

  def reset(self):
    self._cache = {}

  def dump(self):
    return self.parse_pattern().dump()

  def extract_usage(self):
    """ Extracts the base command usage information. Another 
      way of looking at is to strip out only the syntax
      information without other helpful sections such as 
      "Options:"
    """
    usage = self._cache.get('extract_usage',False)
    if not usage:
      usage_pattern = re.compile(r'(usage:)', re.IGNORECASE)
      usage_split = re.split(usage_pattern, self._doc)
      if len(usage_split) < 3:
          raise DocoptLanguageError('"usage:" (case-insensitive) not found.')
      if len(usage_split) > 3:
          raise DocoptLanguageError('More than one "usage:" (case-insensitive).')
      usage = re.split(r'\n\s*\n', ''.join(usage_split[1:]))[0].strip()
      self._cache['extract_usage'] = usage
    return usage

  def parse_argv(self,tokens, options, options_first=False):
    """Parse command-line argument vector.

    If options_first:
        argv ::= [ long | shorts ]* [ argument ]* [ '--' [ argument ]* ] ;
    else:
        argv ::= [ long | shorts | argument ]* [ '--' [ argument ]* ] ;

    """
    parsed = []
    while tokens.current() is not None:
        if tokens.current() == '--':
            return parsed + [Argument(None, v) for v in tokens]
        elif tokens.current().startswith('--'):
            parsed += parse_long(tokens, options)
        elif tokens.current().startswith('-') and tokens.current() != '-':
            parsed += parse_shorts(tokens, options)
        elif options_first:
            return parsed + [Argument(None, v) for v in tokens]
        else:
            parsed.append(Argument(None, tokens.move()))
    return parsed

  def parse_expr(self, tokens, options):
    """expr ::= seq ( '|' seq )* ;"""
    seq = self.parse_seq(tokens, options)
    if tokens.current() != '|':
        return seq
    result = [Required(*seq)] if len(seq) > 1 else seq
    while tokens.current() == '|':
        tokens.move()
        seq = self.parse_seq(tokens, options)
        result += [Required(*seq)] if len(seq) > 1 else seq
    return [Either(*result)] if len(result) > 1 else result

  def parse_seq(self, tokens, options):
    """seq ::= ( atom [ '...' ] )* ;"""
    result = []
    while tokens.current() not in [None, ']', ')', '|']:
        atom = self.parse_atom(tokens, options)
        if tokens.current() == '...':
            atom = [OneOrMore(*atom)]
            tokens.move()
        result += atom
    return result

  def parse_atom(self, tokens, options):
    """atom ::= '(' expr ')' | '[' expr ']' | 'options'
             | long | shorts | argument | command ;
    """
    token = tokens.current()
    result = []
    if token in '([':
        tokens.move()
        matching, pattern = {'(': [')', Required], '[': [']', Optional]}[token]
        result = pattern(*self.parse_expr(tokens, options))
        if tokens.move() != matching:
            raise tokens.error("unmatched '%s'" % token)
        return [result]
    elif token == 'options':
        tokens.move()
        return [AnyOptions()]
    elif token.startswith('--') and token != '--':
        return parse_long(tokens, options)
    elif token.startswith('-') and token not in ('-', '--'):
        return parse_shorts(tokens, options)
    elif token.startswith('<') and token.endswith('>') or token.isupper():
        return [Argument(tokens.move())]
    else:
        return [Command(tokens.move())]

  def parse_pattern(self):
    """
    pattern is.... something magical!
    Pattern appears to deal with switches/options
    """
    pattern = self._cache.get('pattern',False)
    if not pattern:
      source = self.parse_usage()
      options = self.parse_defaults()
      tokens = Tokens.from_pattern(source)
      result = self.parse_expr(tokens, options)
      if tokens.current() is not None:
          raise tokens.error('unexpected ending: %r' % ' '.join(tokens))
      pattern = Required(*result)
      self._cache['parse_pattern'] = pattern.fix()
    return pattern


  def parse_usage(self):
    """
    Formal usage does the magic of building a regex pattern
    STRING that selects between the various options. Note that
    this function will also drop the the initial command 
    (Since the command is the same for everything right?)
    """
    usage = self._cache.get('parse_usage',False)
    if not usage:
      token_list = []
      extract_usage = self.extract_usage().format(name=self._pattern)
      pu = extract_usage.split()[1:]  # split and drop "usage:"
      command_name = pu[0]
      token_list = [command_name,'(',]
      for token in pu[1:]:
        if token == command_name:
          token_list += [') ) | (',command_name,'(',]
        else:
          token_list.append(token)
      usage = '( ' + ' '.join(token_list) + ' ) )'
      self._cache['parse_usage'] = usage
    return usage

  def extract_synopsis(self):
    usage_pattern = re.compile(r'(usage:)', re.IGNORECASE)
    usage_split = re.split(usage_pattern, self._doc)
    return re.split(r'\n\s*\n', ''.join(usage_split[0]))[0].strip()

  def parse_defaults(self):
    options = self._cache.get('parse_defaults',False)
    if not options:
      # in python < 2.7 you can't pass flags=re.MULTILINE
      split = re.split('\n *(<\S+?>|-\S+?)', self._doc)[1:]
      split = [s1 + s2 for s1, s2 in zip(split[::2], split[1::2])]
      options = [Option.parse(s) for s in split if s.startswith('-')]
      self._cache['parse_defaults'] = options
    return options

  def parse(self, argv, options_first=False):
      pattern = self.parse_pattern()

      # [default] syntax for argument is disabled
      #for a in pattern.flat(Argument):
      #    same_name = [d for d in arguments if d.name == a.name]
      #    if same_name:
      #        a.value = same_name[0].value
      options = self.parse_defaults()
      argv = self.parse_argv(
                      Tokens(argv), 
                      list(options), 
                      options_first
                    )

      # Deal with the switches. Iterate through the pattern
      # ad populate the pattern elements with true/false settings?
      pattern_options = set(pattern.flat(Option))
      for ao in pattern.flat(AnyOptions):
          doc_options = parse_defaults(self._doc)
          ao.children = list(set(doc_options) - pattern_options)

      # pattern.fix handles some special handlings
      fixed_pattern = pattern.fix()
      matched, left, collected = fixed_pattern.match(argv)

      if matched and left == []:  # better error message if left?
          return Dict((a.name, a.value) for a in (pattern.flat() + collected))

      return None

class BoopDocOpts(object):
  def __init__(self,docopts,name):
    self._docopts = docopts

  def parse(self, argv, options_first=False):
    for docopt in self._docopts:
      r = docopt.parse(argv,options_first)
      if r:
        return [ r, docopt ]
    return None