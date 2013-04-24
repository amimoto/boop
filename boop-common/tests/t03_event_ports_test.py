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

class EventStringIO(StringIO.StringIO):
  def __init__(self,*args,**kwargs):
    self.timeout = kwargs['timeout']
    del kwargs['timeout']
    StringIO.StringIO.__init__(self,*args,**kwargs)

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
    

class TestPortEvents(unittest.TestCase):

  class EventDispatchTest(EventDispatch): pass

  @event_runnable
  class StringIOEventRunnable(IPortEventRunnable):
    port_class = EventStringIO

  @event_runnable
  class StringIOListenEventRunnable(IPortListenEventRunnable):
    pass

  @event_runnable
  class SignalInterceptRunner(EventRunnable):
    @event_thread
    class SignalInterceptThread(EventThread):
      name = 'intercept'
      def init(self,*args,**kwargs):
        self.captures = []
      @consume.PORT_READ
      def on_signal_read(self,event):
        self.captures.append(event)

  def test_event_ports(self):

    # Start up the dispatcher
    ds = self.EventDispatchTest()
    self.assertIsInstance(ds,self.EventDispatchTest)

    ds.start()

    # Hook up the event capture
    si = ds.runnable_add(self.SignalInterceptRunner)
    self.assertIsInstance(si,EventRunnable)

    # Hook the String IO runnable
    rn = ds.runnable_add(self.StringIOEventRunnable, 'hello world')
    self.assertIsInstance(rn,IPortEventRunnable)

    # Did we get a signal?
    time.sleep(0.1)
    th = si.thread_byinstancename('intercept')
    self.assertIsInstance(th,EventThread)
    self.assertIsInstance(th.captures[0],Event)

    # Let's send a message
    rn.send("good bye cruel world")

    # Did we get a signal?
    time.sleep(0.1)
    th = si.thread_byinstancename('intercept')
    self.assertIsInstance(th,EventThread)

    self.assertIsInstance(th.captures[1],Event)


    # Kill the dispatch
    ds.terminate()
    time.sleep(0.1)


if __name__ == '__main__':
  try:
    unittest.main()
  except Exception:
    pass

