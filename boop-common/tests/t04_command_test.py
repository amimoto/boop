#!/usr/bin/python

import sys; sys.path.append('..')

import boop.command.docopt
from boop.command import *

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
      --switch3   another switchy task three
      
  """

  def test_tokenize(self):

    argv = [ 'mycommand', 'option2', 'thisparam' ]

    dcf = boop.command.docopt.BoopDocOpt(self.doc,'mycommand')
    self.assertIsInstance(dcf,boop.command.docopt.BoopDocOpt)

    synopsis = dcf.synopsis_extract()
    self.assertEquals(synopsis,'Handle some subcommand here')

    usage = dcf.usage_extract()
    self.assertRegexpMatches(usage,'{name}')
    self.assertNotRegexpMatches(usage,'switchy')

    options = dcf.options_extract()
    self.assertRegexpMatches(options,'--switch1')
    self.assertNotRegexpMatches(options,'option1')

    options_rec = dcf.options_parse()
    self.assertTrue(len(options_rec), 3)
    for option in options_rec:
      self.assertIsInstance(option,boop.command.docopt.Option)

    argv = [ 'potato', 'hot', 'pass', 'on' ]
    attrs = dcf.parse(argv)
    self.assertEqual(attrs,None)

    argv = [ 'mycommand', 'option2', 'junk', 'options:' ]
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


  @commandset
  class CS(CommandSet):
    """ My test CommandSet
    """

    @command
    def d(self,attrs,context):
      """
      First item
      Usage:
        {name} hello <name>
        {name} hello2 <name> --opt
      Options:
        --opt  some sort of option!
      """
      return "Hello "+attrs['<name>']
    @command
    def e(self,attrs,context):
      """
      Second item
      Usage:
        {name} goodbye <name>
        {name} goodbye2 <name> --sniff
      Options:
        --sniff   be all sad and, stuff
      """
      return "Goodbye "+attrs['<name>']

  class CSD(CommandSetDispatch):
    pass

  def test_cs(self):
    c = self.CS(instance_name='say')
    self.assertIsInstance(c,CommandSet)

    argv = ['say','hello','nemo']
    result = c.execute(argv,{})
    self.assertEqual(result,'Hello nemo')

    c = self.CS(instance_name='/NUMBER',instance_pattern='^\/\d+$')
    result = c.execute('/1 goodbye megatron',{})
    self.assertEqual(result,'Goodbye megatron')

    # Handle the commandset help
    help_text = c.help()
    self.assertTrue(re.search('hello',help_text) \
                and re.search('goodbye',help_text) \
                and re.search('NUMBER',help_text) \
                )

    # context help
    help_text = c.help('/NUMBER o')
    self.assertTrue(re.search('hello',help_text) \
                and re.search('goodbye',help_text) \
                )

    help_text = c.help('/NUMBER sniff')
    self.assertTrue(re.search('goodbye',help_text) \
                and not re.search('hello',help_text) \
                )


  def test_csd(self):
    csd = self.CSD(commandsets=[
            self.CS(
              instance_name='/number',
              instance_pattern='^\/\d+$'
            )
          ])
    self.assertIsInstance(csd,CommandSetDispatch)
    result = csd.execute('/1 goodbye megatron',{})
    self.assertEqual(result,'Goodbye megatron')


if __name__ == '__main__':
    unittest.main()

