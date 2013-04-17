import sys; sys.path.append('..')

from boop.app import *
from boop.event import *
from boop.common import *
import boop.command.core
import os.path

import testdata

import unittest
import shlex
import os
import time

test_data_path = os.path.dirname(testdata.__file__)

class TestPluginCommandSet(unittest.TestCase):

  @plugin_commandset
  class PluginCommandSetTest(PluginCommandSet):
    """
    Test Documentation

    Usage:
      speed wing <sparrow>

    """
    name = "speed"

  def test_plugin_command_set(self):
    pcs = self.PluginCommandSetTest('app','plugin')
    self.assertIsInstance(pcs,PluginCommandSet)
    self.assertIs(pcs._plugin_class_type,'commandset')
    self.assertIs(pcs._plugin_start,'auto')
    self.assertIs(pcs.app,'app')
    self.assertIs(pcs.instance_name(),'speed')
    self.assertIs(pcs.plugin,'plugin')

class TestPluginEventRunnable(unittest.TestCase):
  @plugin_runnable
  class PluginEventRunnableTest(PluginEventRunnable):
    name = "zoom"

  def test_plugin_event_runnable(self):
    per = self.PluginEventRunnableTest('app','plugin')
    self.assertIsInstance(per,PluginEventRunnable)
    self.assertIs(per._plugin_class_type,'runnable')
    self.assertIs(per._plugin_start,'auto')
    self.assertIs(per.app,'app')
    self.assertIs(per.instance_name(),'zoom')
    self.assertIs(per.plugin,'plugin')

class TestEventsApp(unittest.TestCase):

  class EventAppTest(EventsApp):
    def __init__(self,*args,**kwargs):
      super(TestEventsApp.EventAppTest,self).__init__(*args,**kwargs)
      if os.path.isfile(self.events_log_dsn):
        os.unlink(self.events_log_dsn)

    def terminate(self):
      super(TestEventsApp.EventAppTest,self).terminate()
      if os.path.isfile(self.events_log_dsn):
        os.unlink(self.events_log_dsn)

  @plugin_app
  class PluginEventsAppTest(PluginEventsApp):
    name = "zap"

    @plugin_commandset
    class PluginCommandSetTest(PluginCommandSet):
      """
      Usage:
        speed wing <sparrow>
      """
      name = "speed"

    @plugin_commandset.opts(start='manual')
    class PluginCommandSetTest2(PluginCommandSet):
      """
      Usage:
        span wing <sparrow>
      """
      name = "span"

    @plugin_runnable
    class PluginEventRunnableTestZoom(PluginEventRunnable):
      name = "zoom"

      @event_thread
      class EventThreadTest(EventThread):

        name = "potato"

        data = None
        cdata = None
        mdata = None

        @consume.TEST_SIGNAL
        def consume_test_signal(self,event):
          self.data = event.data

        @consume.when.TEST_SIGNAL(lambda s,e:e.data == 'tock')
        def consume_test_signal_conditional(self,event):
          self.cdata = event.data

        @consume.when.TEST_SIGNAL(for_only_me)
        def consume_test_signal_mine(self,event):
          self.mdata = event.data


  @plugin_app
  class PluginEventsAppTest2(PluginEventsApp):
    name = "paz"

    @plugin_commandset
    class PluginCommandSetTest(PluginCommandSet):
      """
      Usage:
        speed wing <sparrow>
      """
      name = "speed"

    @plugin_commandset.opts(start='manual')
    class PluginCommandSetTest2(PluginCommandSet):
      """
      Usage:
        span wing <sparrow>
      """
      name = "span"

  def test_event_app(self):

    global test_data_path 

    ea = self.EventAppTest(
                test_data_path,
                plugins=[
                  self.PluginEventsAppTest,
                  self.PluginEventsAppTest2
                ]
              )

    # There are going to be two plugins in the app.
    # The plugins should have instance names of 
    # "zap" and "paz"
    with self.assertRaises( EventsAppNotStartedException ) as e:
      pe = ea.plugin_byinstancename("zap")

    # Start the main app
    ea.start()

    # Plugin should be launched
    pe = ea.plugin_byinstancename("zap")
    pe2 = ea.plugin_byinstancename("paz")
    self.assertIsInstance(pe,PluginEventsApp)
    self.assertIsInstance(pe2,PluginEventsApp)

    # Now the commandset should be declared
    cs = pe.object_byinstancename('speed')
    self.assertIsInstance(cs,PluginCommandSet)

    # However, the second commandset should be set to manual 
    # launch so should not be instantiated in the plugin yet
    with self.assertRaises( BoopNotExists ) as e:
      pe.object_byinstancename('span')

    # Can we get the runnable object?
    re = pe.object_byinstancename('zoom')
    self.assertIsInstance(re,PluginEventRunnable)

    self.assertIs(re._plugin_start,'auto')

    # Inject an event
    ev = ea.emit.TEST_SIGNAL('tick')
    self.assertIsInstance(ev,Event)
    self.assertIs(ev.type,'TEST_SIGNAL')

    # Let's see if it's reached its destination
    time.sleep(0.1)

    tr = re.thread_get('potato')
    self.assertIsInstance(tr,EventThread)
    self.assertIs(tr.data,'tick')


    ea.terminate()

if __name__ == '__main__':
  try:
    unittest.main()
  except Exception:
    pass

