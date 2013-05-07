import sys; sys.path.append('..')

from boop.event import *
from boop.event.log import *
import os.path

import testdata

import unittest
import time

test_data_path = os.path.dirname(testdata.__file__)

class TestEventLog(unittest.TestCase):

  class EventDispatchTest(EventDispatch): pass

  @event_runnable
  class EventLoggerRunnableTest(EventLoggerRunnable):
    pass

  def setUp(self):
    self.dsn = test_data_path + "/log.db"
    if os.path.isfile(self.dsn):
      os.unlink(self.dsn)

  def tearDown(self):
      if os.path.isfile(self.dsn):
        os.unlink(self.dsn)

  def test_event_log(self):
    global test_data_path

    # Start up the dispatcher
    ds = self.EventDispatchTest()
    self.assertIsInstance(ds,self.EventDispatchTest)
    self.assertFalse(ds.started)

    # Are we started?
    ds.start()
    time.sleep(0.1)
    self.assertTrue(ds.started)

    # Hook a logging runnable
    rn = ds.runnable_add(self.EventLoggerRunnableTest, self.dsn)
    self.assertIsInstance(rn,EventLoggerRunnable)

    # Create an event to log it
    ev = ds.emit.EVENT_SUBMIT()
    self.assertIsInstance(ev,Event)
    time.sleep(0.1)

    # Kill the dispatch
    ds.terminate()
    time.sleep(0.1)

    # Now let's connect to the log and pull that last event out

    # Start up the dispatcher
    ds = self.EventDispatchTest()
    self.assertIsInstance(ds,self.EventDispatchTest)
    self.assertFalse(ds.started)

    # Are we started?
    ds.start()
    time.sleep(0.1)
    self.assertTrue(ds.started)

    # Hook a logging runnable
    rn = ds.runnable_add(self.EventLoggerRunnableTest, self.dsn)
    self.assertIsInstance(rn,EventLoggerRunnable)

    # Try and fetch the last record
    r = rn.events_from()[0]
    self.assertEquals(r.event_type,'EVENT_SUBMIT')

    # Kill the dispatch
    ds.terminate()
    time.sleep(0.1)




if __name__ == '__main__':
  try:
    unittest.main()
  except Exception:
    pass

