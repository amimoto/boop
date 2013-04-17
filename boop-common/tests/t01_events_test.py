from boop.event import *

import unittest
import time

class TestEvent(unittest.TestCase):

  def test_event(self):
    """ Check that the we can instantiate events and values get stored
    """
    ev = Event(
                'event_type',
                data='data',
                local_only=True,
                source='source',
                target='target',
                meta_data='metadata',
              )

    self.assertIsInstance(ev,Event)

    self.assertIs(ev.type,'event_type')
    self.assertIs(ev.data,'data')
    self.assertIs(ev.local_only, True)
    self.assertIs(ev.source,'source')
    self.assertIs(ev.target,'target')
    self.assertIs(ev.meta_data,'metadata')



class TestEventQueue(unittest.TestCase):
  def test_event_queue(self):
    """ Check if we can create and use EventQueue objects 
    """
    qu = EventQueue()

    self.assertIsInstance(qu,EventQueue)
    qu.put('test')
    qu.put('test2')

    v = qu.get()
    self.assertIs(v,'test')
    v = qu.get()
    self.assertIs(v,'test2')


class TestEventThread(unittest.TestCase):

  @event_thread
  class EventThreadTest(EventThread):

    data = None
    cdata = None
    mdata = None

    name = 'euonia'

    @consume.TEST_SIGNAL
    def consume_test_signal(self,event):
      self.data = event.data

    @consume.when.TEST_SIGNAL(lambda s,e:e.data == 'tock')
    def consume_test_signal_conditional(self,event):
      self.cdata = event.data

    @consume.when.TEST_SIGNAL(for_only_me)
    def consume_test_signal_mine(self,event):
      self.mdata = event.data


  def test_event_thread(self):

    qu = EventQueue()
    et = self.EventThreadTest(
            'Runnable',
            qu,
            'instance_name',
            timeout=0.01
          )

    self.assertIsInstance(et,self.EventThreadTest)

    # Make sure we have a handle name
    self.assertIs(et.instance_name(),'instance_name')

    # Nothing in the data store
    self.assertIs(et.data,None)
    self.assertIs(et.cdata,None)
    self.assertIs(et.mdata,None)

    # Start the thread
    et.start()

    # Inject an event
    ev = et.emit.TEST_SIGNAL('tick')
    self.assertIsInstance(ev,Event)
    self.assertIs(ev.type,'TEST_SIGNAL')

    # pretend to be the dispatcher and inject the 
    # event into the incoming queue
    ev = qu.get()
    self.assertIsInstance(ev,Event)
    et.receive_event(ev) 
    time.sleep(0.1)

    # Did it get registered?
    self.assertIs(et.data,'tick')

    # Make sure it didn't get registered to the conditional
    # handler
    self.assertIs(et.cdata,None)
    self.assertIs(et.mdata,None)

    # Now inject an event that will match the conditional
    ev = et.emit.TEST_SIGNAL('tock')
    self.assertIs(ev.type,'TEST_SIGNAL')

    # pretend to be the dispatcher and inject the 
    # event into the incoming queue
    ev = qu.get()
    self.assertIsInstance(ev,Event)
    et.receive_event(ev) 
    time.sleep(0.1)

    # Did it get registered?
    self.assertIs(et.data,'tock')

    # Did the conditional handler get it?
    self.assertIs(et.cdata,'tock')

    # Didn't get to the target handler right?
    self.assertIs(et.mdata,None)

    # Done here
    et.terminate()

    # Give the thread a chance to shutdown
    time.sleep(0.1)

class TestEventRunnable(unittest.TestCase):

  @event_runnable
  class EventRunnableTest(EventRunnable):

    @event_thread
    class EventThreadTest(EventThread):

      data = None
      cdata = None
      mdata = None

      _instance_name = 'euonia'

      @consume.TEST_SIGNAL
      def consume_test_signal(self,event):
        self.data = event.data

      @consume.when.TEST_SIGNAL(lambda s,e:e.data == 'tock')
      def consume_test_signal_conditional(self,event):
        self.cdata = event.data

      @consume.when.TEST_SIGNAL(for_only_me)
      def consume_test_signal_mine(self,event):
        self.mdata = event.data

  def test_runnable(self):
    """ Check that we can instantiate runnables and launch them
    """

    rn = self.EventRunnableTest()

    self.assertIsInstance(rn,self.EventRunnableTest)

    # Thread should not be running yet
    tr = rn.thread_get('euonia')
    self.assertIs(tr,False)

    ds = EventDispatch()
    threads = rn.start(ds)

    # Start should return a structure with our new thread
    self.assertIs(len(threads),1)

    # Can we actually do a lookup by thread?
    tr = rn.thread_get('euonia')
    self.assertIsInstance(tr,self.EventRunnableTest.EventThreadTest)

    # Done for now
    rn.terminate()
    time.sleep(0.1)


class TestEventDispatch(unittest.TestCase):

  @event_runnable
  class EventRunnableTest(EventRunnable):

    @event_thread
    class EventThreadTest(EventThread):

      data = None
      cdata = None
      mdata = None

      _instance_name = 'euonia'

      @consume.TEST_SIGNAL
      def consume_test_signal(self,event):
        self.data = event.data

      @consume.when.TEST_SIGNAL(lambda s,e:e.data == 'tock')
      def consume_test_signal_conditional(self,event):
        self.cdata = event.data

      @consume.when.TEST_SIGNAL(for_only_me)
      def consume_test_signal_mine(self,event):
        self.mdata = event.data


  class EventDispatchTest(EventDispatch): pass

  def test_event_dispatch(self):
    """ Check to see if we can't instantiate and use EventDispatch objects
    """
    ds = self.EventDispatchTest()
    self.assertIsInstance(ds,self.EventDispatchTest)

    ds.start()

    rn = ds.runnable_add(self.EventRunnableTest)

    # Can we actually do a lookup by thread?
    et = rn.thread_get('euonia')
    self.assertIsInstance(et,self.EventRunnableTest.EventThreadTest)
    self.assertIsInstance(rn,self.EventRunnableTest)

    # Sound be nothing in data as of yet...
    self.assertIs(et.data,None)

    # Inject an event
    ev = ds.emit.TEST_SIGNAL('tick')
    self.assertIsInstance(ev,Event)
    self.assertIs(ev.type,'TEST_SIGNAL')

    # Let's see if it's reached its destination
    time.sleep(0.1)
    self.assertIs(et.data,'tick')

    ds.terminate()
    time.sleep(0.1)


if __name__ == '__main__':
    unittest.main()
