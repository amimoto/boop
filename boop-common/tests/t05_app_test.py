#!/usr/bin/python

import sys; sys.path.append('..')

from boop.app import *
from boop.app.tools import *
from boop.event import *
from boop.common import *
from boop.command import *
import boop.command.core
import os.path

import testdata

import unittest
import shlex
import os
import time

test_data_path = os.path.dirname(testdata.__file__)

class TestBoopCommandSet(unittest.TestCase):

  @boop_commandset
  class BoopBoopCommandSetTest(BoopCommandSet):
    """
    Test Documentation

    Usage:
      speed wing <sparrow>

    """
    name = "speed"

  def test_plugin_command_set(self):
    ctx = BoopContext()
    pcs = self.BoopBoopCommandSetTest(context=ctx)
    self.assertIsInstance(pcs,BoopCommandSet)
    self.assertIs(pcs._plugin_class_type,'commandset')
    self.assertIs(pcs._plugin_start,'auto')
    self.assertIsInstance(pcs._context,BoopContext)
    self.assertIs(pcs.instance_name(),'speed')

class TestBoopEventRunnable(unittest.TestCase):
  @boop_runnable
  class BoopEventRunnableTest(BoopEventRunnable):
    name = "zoom"

  def test_plugin_event_runnable(self):
    ctx = BoopContext()
    per = self.BoopEventRunnableTest(context=ctx)
    self.assertIsInstance(per,BoopEventRunnable)
    self.assertIs(per._plugin_class_type,'runnable')
    self.assertIs(per._plugin_start,'auto')
    self.assertIsInstance(per._context,BoopContext)
    self.assertIs(per.instance_name(),'zoom')

if __name__ == '__main__':
  try:
    unittest.main()
  except Exception:
    pass

