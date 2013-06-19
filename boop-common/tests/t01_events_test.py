#!/usr/bin/python

import sys; sys.path.append('..')

from boop.event import *
from boop.common import *

import unittest
import time

class TestEvent(unittest.TestCase):

  def test_context(self):
    """ Check to see that the context object can be handled
        apporopriately
    """
    ctx = BoopContext({'left':'green'},  war='peace')
    self.assertIsInstance(ctx,BoopContext)
    self.assertEqual(ctx.war,'peace')
    self.assertEqual(ctx.left,'green')
    with self.assertRaises( AttributeError ) as e:
      ctx.peace
    ctx.GLOBAL_VALUE = 'mynewvalue'
    self.assertEqual(ctx._global_data['GLOBAL_VALUE'],'mynewvalue')

    ctx['freedom'] = 'slavery'
    self.assertEqual(ctx.freedom,'slavery')
    self.assertEqual(ctx['freedom'],'slavery')

    ctx_copy = ctx.copy()
    ctx.new = 'old'
    self.assertEqual(ctx.new,'old')
    with self.assertRaises( AttributeError ) as e:
      ctx_copy.new

    self.assertEqual(ctx_copy.GLOBAL_VALUE,'mynewvalue')

    ctx.GLOBAL = 'domination!'
    self.assertEqual(ctx_copy.GLOBAL,'domination!')

  def test_event(self):
    """ Check that the we can instantiate events and values get stored
    """
    ev = BoopEvent(
                'event_type',
                data='data',
                local_only=True,
                source='source',
                target='target',
                meta_data='metadata',
              )

    self.assertIsInstance(ev,BoopEvent)

    self.assertIs(ev.type,'event_type')
    self.assertIs(ev.data,'data')
    self.assertIs(ev.local_only, True)
    self.assertIs(ev.source,'source')
    self.assertIs(ev.target,'target')
    self.assertIs(ev.meta_data,'metadata')



class TestBoopEventQueue(unittest.TestCase):
  def test_event_queue(self):
    """ Check if we can create and use BoopEventQueue objects 
    """
    qu = BoopEventQueue()

    self.assertIsInstance(qu,BoopEventQueue)
    qu.put('test')
    qu.put('test2')

    v = qu.get()
    self.assertIs(v,'test')
    v = qu.get()
    self.assertIs(v,'test2')


class TestBoopEventThread(unittest.TestCase):

  @event_thread
  class BoopEventThreadTest(BoopEventThread):

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

    ctx = {}
    qu = BoopEventQueue()
    et = self.BoopEventThreadTest(
            'Runnable',
            qu,
            ctx,
            'instance_name',
            timeout=0.01
          )

    self.assertIsInstance(et,self.BoopEventThreadTest)

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
    self.assertIsInstance(ev,BoopEvent)
    self.assertIs(ev.type,'TEST_SIGNAL')

    # pretend to be the dispatcher and inject the 
    # event into the incoming queue
    ev = qu.get()
    self.assertIsInstance(ev,BoopEvent)
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
    self.assertIsInstance(ev,BoopEvent)
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

class TestBoopEventRunnable(unittest.TestCase):

  @event_runnable
  class BoopEventRunnableTest(BoopEventRunnable):

    @event_thread
    class BoopEventThreadTest(BoopEventThread):

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

    rn = self.BoopEventRunnableTest()

    self.assertIsInstance(rn,self.BoopEventRunnableTest)

    # Thread should not be running yet
    tr = rn.thread_byinstancename('euonia')
    self.assertIs(tr,False)

    ctx = BoopContext()
    ds = BoopEventDispatch(context=ctx)
    threads = rn.start(ds)

    # Start should return a structure with our new thread
    self.assertIs(len(threads),1)

    # Can we actually do a lookup by thread?
    tr = rn.thread_byinstancename('euonia')
    self.assertIsInstance(tr,self.BoopEventRunnableTest.BoopEventThreadTest)

    # Done for now
    rn.terminate()
    time.sleep(0.1)


class TestBoopEventDispatch(unittest.TestCase):

  @event_runnable
  class BoopEventRunnableTest(BoopEventRunnable):

    @event_thread
    class BoopEventThreadTest(BoopEventThread):

      data = None
      cdata = None
      mdata = None

      ctx = None

      _instance_name = 'euonia'

      @consume.TEST_SIGNAL
      def consume_test_signal(self,event):
        self.data = event.data
        self.ctx = self._context.test

      @consume.when.TEST_SIGNAL(lambda s,e:e.data == 'tock')
      def consume_test_signal_conditional(self,event):
        self.cdata = event.data

      @consume.when.TEST_SIGNAL(for_only_me)
      def consume_test_signal_mine(self,event):
        self.mdata = event.data


  class BoopEventDispatchTest(BoopEventDispatch): pass

  def test_event_dispatch(self):
    """ Check to see if we can't instantiate and use BoopEventDispatch objects
    """
    ctx = BoopContext({ 'test': 'foo' })
    ds = self.BoopEventDispatchTest(context=ctx)
    self.assertIsInstance(ds,self.BoopEventDispatchTest)

    ds.start()

    rn = ds.runnable_add(self.BoopEventRunnableTest)

    # Can we actually do a lookup by thread?
    et = rn.thread_byinstancename('euonia')
    self.assertIsInstance(et,self.BoopEventRunnableTest.BoopEventThreadTest)
    self.assertIsInstance(rn,self.BoopEventRunnableTest)

    # Sound be nothing in data as of yet...
    self.assertIs(et.data,None)

    # Inject an event
    ev = ds.emit.TEST_SIGNAL('tick')
    self.assertIsInstance(ev,BoopEvent)
    self.assertIs(ev.type,'TEST_SIGNAL')

    # Let's see if it's reached its destination
    time.sleep(0.1)
    self.assertIs(et.data,'tick')

    # Let's see if the context is correct
    # this ensures the context from the dispatch is passed along
    # to the event
    self.assertIs(et.ctx,'foo')

    ds.terminate()
    time.sleep(0.1)


if __name__ == '__main__':
    unittest.main()
