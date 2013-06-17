#!/usr/bin/python

import sys; sys.path.append('..')

import os.path
import unittest
import time
import StringIO

from boop.event import *
from boop.event.ports import *
import testdata

test_data_path = os.path.dirname(testdata.__file__)

class BoopEventStringIO(StringIO.StringIO):
  def __init__(self,*args,**kwargs):
    self.timeout = kwargs['timeout']
    del kwargs['timeout']
    StringIO.StringIO.__init__(self,*args)

  def read(self,read_size):
    data = StringIO.StringIO.read(self,read_size)
    if data: return data
    time.sleep(self.timeout)
    return None

  def write(self,s):
    position = self.tell()
    result = StringIO.StringIO.write(self,s)
    self.seek(position)
    return result
    

class TestPortBoopEvents(unittest.TestCase):

  class BoopEventDispatchTest(BoopEventDispatch): pass

  @event_runnable
  class StringIOBoopEventRunnable(IPortBoopEventRunnable):
    port_class = BoopEventStringIO

  @event_runnable
  class StringIOListenBoopEventRunnable(IPortListenBoopEventRunnable):
    pass

  @event_runnable
  class SignalInterceptRunner(BoopEventRunnable):
    @event_thread
    class SignalInterceptThread(BoopEventThread):
      name = 'intercept'
      def init(self,*args,**kwargs):
        self.captures = []
      @consume.PORT_READ
      def on_signal_read(self,event):
        self.captures.append(event)

  def test_event_ports(self):

    # Start up the dispatcher
    ctx = {'mycontext':'nothing special'}
    ds = self.BoopEventDispatchTest(context=ctx)
    self.assertIsInstance(ds,self.BoopEventDispatchTest)

    ds.start()

    # Hook up the event capture
    si = ds.runnable_add(self.SignalInterceptRunner)
    self.assertIsInstance(si,BoopEventRunnable)

    # Hook the String IO runnable
    rn = ds.runnable_add(self.StringIOBoopEventRunnable, 'hello world')
    self.assertIsInstance(rn,IPortBoopEventRunnable)

    # Did we get a signal?
    time.sleep(0.1)
    th = si.thread_byinstancename('intercept')
    self.assertIsInstance(th,BoopEventThread)
    self.assertIsInstance(th.captures[0],BoopEvent)

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

