#!/usr/bin/python

import sys; sys.path.append('..')

import boop.command.docopt
from boop.command import *
import boop.command.core
from boop.common import *

import unittest
import shlex
import re

class TestDocOptTweaks(unittest.TestCase):
  """
  This tests the additional parsing features we've made
  to docopt
  """

  doc = """
    Handle some subcommand here

    Usage:
      {name} option1
      {name} option2 <parameter1>
      {name} --switch1 | --switch2

    Options:
      --switch1   do some switchy task
      --switch2   another switchy task too
      
  """

  doc2 = """
    Do a barrel roll!

    Usage:
      {name} ( wing | speed ) <sparrow>

    Options:
      --counter   Go counter-clockwise
  """

  '''

  def test_tokenize(self):

    dcff = boop.command.docopt.BoopDocOpts([self.doc,self.doc2],'mycommand')
    argv = [ 'mycommand', 'option2', 'thisparam' ]

    dcf = boop.command.docopt.BoopDocOpt(self.doc,'mycommand')
    self.assertIsInstance(dcf,boop.command.docopt.BoopDocOpt)

    synopsis = dcf.extract_synopsis()
    self.assertEquals(synopsis,'Handle some subcommand here')

    usage = dcf.extract_usage()
    self.assertRegexpMatches(usage,'mycommand')
    self.assertNotRegexpMatches(usage,'switchy')

    argv = [ 'potato', 'hot', 'pass', 'on' ]
    attrs = dcf.parse(argv)
    self.assertEqual(attrs,None)

    argv = [ 'mycommand', 'option2', 'thisparam' ]
    attrs = dcf.parse(argv)
    self.assertDictEqual(attrs,{
        '--switch1': False,
        '--switch2': False,
        '<parameter1>': 'thisparam',
        'mycommand': True,
        'option1': False,
        'option2': True})
  '''

  @boop.command.core.cs_commandset
  class CS(boop.command.core.CS):

    @boop.command.core.cs_command
    def d(self,attrs,context):
      """
      First item
      Usage:
        {name} hello <name>
      """
      print "HELLO",attrs['<name>']

    @boop.command.core.cs_command
    def e(self,attrs,context):
      """
      Second item
      Usage:
        {name} goodbye <name>
      """
      print "GOODBYE",attrs['<name>']

  def test_cs(self):
    c = self.CS(instance_name='say')
    argv = ['say','hello','nemo']
    c.execute(argv,{})

    c = self.CS(instance_name='^\/\d+$')

    csd = boop.command.core.CSD(
      commandsets=[c]
    )
    csd.execute('/1 goodbye megatron',{})

'''
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
    name = 'speed'
    last_command = None

    @command
    def wing_command(self,attrs,parent):
      """
      Do a barrel roll!

      Usage:
          {name} ( wing | speed ) <sparrow>

      Options:
          --counter   Go counter-clockwise
      """
      self.last_command = attrs
      print "executed"
    
    @command
    def wing_command2(self,attrs,parent):
      self.last_command = attrs
      print "executed"


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
    self.assertEquals(r,'executed')

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

    # FIXME This should catch an exception
    with self.assertRaises( Exception ) as e:
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
'''

if __name__ == '__main__':
    unittest.main()

