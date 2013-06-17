#!/usr/bin/python

import sys; sys.path.append('..')

from boop.app import *
from boop.app.tools import *
from boop.app.ports.string import *
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

class TestStringSerialPlugin(unittest.TestCase):

  class EventAppTest(BoopApp):
    def __init__(self,*args,**kwargs):
      super(type(self),self).__init__(*args,**kwargs)
      if os.path.isfile(self.events_log_dsn):
        os.unlink(self.events_log_dsn)

    def terminate(self):
      super(type(self),self).terminate()
      if os.path.isfile(self.events_log_dsn):
        os.unlink(self.events_log_dsn)

  def test_string_serial_plugin(self):

    global test_data_path 

    ea = self.EventAppTest(test_data_path,debug=True)

    # Start the main app
    ea.start()

    # Send a message out
    psa = ea.plugin_add(PortStringPlugin,initial='May the schwartz be with you.')
    ev = ea.emit.PORT_SEND('tick')

    # Wait for the message to propagate
    time.sleep(0.2)

    # Did we get the message?

    # Done!
    ea.terminate()


if __name__ == '__main__':
  try:
    unittest.main()
  except Exception:
    pass

