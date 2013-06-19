#!/usr/bin/python

import sys; sys.path.append('..')

import os.path
import unittest
import time
import StringIO

from boop.event import *
from boop.event.ports import *
from boop.event.ports.file import *

import testdata

test_data_path = os.path.dirname(testdata.__file__)

@event_runnable
class BoopTestFileEventCapture(BoopEventRunnable):
  @event_thread
  class BoopSignalInterceptThread(BoopEventThread):
    name = 'intercept'
    def init(self,*args,**kwargs):
      self.captures = []
    @consume.PORT_READ
    def on_signal_read(self,event):
      self.captures.append(event)


class BoopTestFileEvents(unittest.TestCase):

  def test_event_ports(self):
    # Start up the dispatcher
    ctx = BoopContext()
    ds = BoopEventDispatch(context=ctx)
    self.assertIsInstance(ds,BoopEventDispatch)

    ds.start()

    # Hook up the event capture
    si = ds.runnable_add(BoopTestFileEventCapture)
    self.assertIsInstance(si,BoopTestFileEventCapture)

    # Delete the log.txt file if it exists
    log_fpath = test_data_path+'/log.txt'
    try:
      os.unlink(log_fpath)
    except OSError: pass

    # Create a new file
    log_fh = open(log_fpath,'w')

    # Hook the String IO runnable
    rn = ds.runnable_add(FileBoopEventRunnable, name=log_fpath, mode='w+')
    self.assertIsInstance(rn,FileBoopEventRunnable)

    # Now write something to the file
    log_fh.write('test write')
    log_fh.close()

    # Did we get a signal?
    time.sleep(0.1)
    th = si.thread_byinstancename('intercept')
    self.assertIsInstance(th,BoopEventThread)
    self.assertIsInstance(th.captures[0],BoopEvent)
    self.assertEquals(th.captures[0].data,'test write')

    # Let's send a message
    rn.send("good bye cruel world")

    # Did we get a signal?
    time.sleep(0.2)
    th = si.thread_byinstancename('intercept')
    self.assertIsInstance(th,BoopEventThread)
    self.assertIsInstance(th.captures[1],BoopEvent)

    # Kill the dispatch
    ds.terminate()
    time.sleep(0.1)



if __name__ == '__main__':
  try:
    unittest.main()
  except Exception:
    pass

