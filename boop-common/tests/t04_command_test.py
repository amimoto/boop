import sys; sys.path.append('..')

from boop.command import *
import boop.command.core

import unittest
import shlex
import re

class TestParse(unittest.TestCase):
  doc = """
    Test Documentation

    Usage:
      speed wing <sparrow>

  """

  def test_parser(self):
    s = "speed wing african"
    v = shlex.split(s)

    # Does it even parse?
    attrs = boop.command.core.docopt_parse(self.doc,argv=v[1:])
    self.assertDictEqual(attrs, {'<sparrow>': 'african', 'wing': True} )

class TestCommandSet(unittest.TestCase):

  @commandset
  class CommandSetTest(CommandSet):
    """
      Test Documentation

      Usage:
        speed wing <sparrow>

    """

    name = 'speed'
    last_command = None

    def execute(self,attrs,parent):
      self.last_command = attrs
      return "executed"


  @commandset
  class CommandSetTest2(CommandSet):
    """
      Test Documentation2

      Usage:
        span wing <sparrow>

    """

    name = 'span'
    last_command = None

    def execute(self,attrs,parent):
      self.last_command = attrs
      return "executed"


  def test_commandset(self):
    cs = self.CommandSetTest()

    self.assertIsInstance(cs,CommandSet)

    # Parse our test command
    s = "speed wing african"
    v = shlex.split(s)

    # Nothing should be stored yet
    self.assertIs(cs.last_command, None )

    attrs = cs.parse(v,'parent')
    self.assertDictEqual(attrs, {'<sparrow>': 'african', 'wing': True} )

    # Now execute our test command
    r = cs.execute(attrs,'no parent')
    self.assertIs(r,'executed')

    # Double check that the code has executed
    self.assertDictEqual(cs.last_command, {'<sparrow>': 'african', 'wing': True} )


  def test_commandparser(self):
    cp = CommandParser()

    self.assertIsInstance(cp,CommandParser)

    result = cp.parse("help")
    self.assertDictEqual(result,
                          {
                         '<command>': None,
                         'help': True})

    cs = cp.commandset_add(self.CommandSetTest)
    self.assertIsInstance(cs,CommandSet)

    attrs = cp.parse("speed wing african")
    self.assertDictEqual(attrs,
                        {'<sparrow>': 'african',
                         'wing': True})


    attrs = cp.parse("span wing african")
    self.assertDictEqual(attrs,{})

    cs2 = cp.commandset_add(self.CommandSetTest2)

    attrs = cp.parse("span wing african")
    self.assertDictEqual(attrs,
                        {'<sparrow>': 'african',
                         'wing': True})

  def test_commandrunner(self):

    cr = CommandRunner()

    self.assertIsInstance(cr,CommandParser)

    result = cr.parse("help")
    self.assertDictEqual(result,
                          {'<command>': None,
                           'help': True})

    cs = cr.commandset_add(self.CommandSetTest)
    self.assertIsInstance(cs,CommandSet)

    r = cr.execute("speed wing african",None)
    self.assertDictEqual(r,
                        {'output': 'executed', 'attrs': {'<sparrow>': 'african',
                         'wing': True}})

    r = cr.execute("span wing african")
    self.assertDictEqual(r['attrs'],{})

    cs2 = cr.commandset_add(self.CommandSetTest2)

    r = cr.execute("span wing african")
    self.assertDictEqual(r,
                        {'output': 'executed', 'attrs': {'<sparrow>': 'african',
                         'wing': True}})

    # And how about help text on the sub command?
    r = cr.execute("help span")
    self.assertTrue(re.search('Documentation2',r['output']))

if __name__ == '__main__':
    unittest.main()

