#!/usr/bin/python

import sys; sys.path.append('..')

from boop.event import *
from boop.common import *
from boop.command import *
from boop.app import *
from boop.app.tools import *
import os.path

import testdata

import unittest
import shlex
import os
import time

test_data_path = os.path.dirname(testdata.__file__)


class TestEventsApp(unittest.TestCase):

  class EventAppTest(BoopApp):
    def __init__(self,*args,**kwargs):
      super(TestEventsApp.EventAppTest,self).__init__(*args,**kwargs)
      if os.path.isfile(self.events_log_dsn):
        os.unlink(self.events_log_dsn)

    def terminate(self):
      super(TestEventsApp.EventAppTest,self).terminate()
      if os.path.isfile(self.events_log_dsn):
        os.unlink(self.events_log_dsn)

  @boop_plugin
  class PluginEventsAppTest(BoopPlugin):
    name = "zap"

    @boop_commandset
    class ZapBoopCommandSetTest(BoopCommandSet):
      """ Is that a dead parrot?!
      """
      name = "speed"

      @command
      def handle_wing(self,attrs):
        """
        Usage:
          speed wing <sparrow>
        """
        return "WINGY"

    @boop_commandset.opts(start='manual')
    class ZapBoopCommandSetTest2(BoopCommandSet):
      """ Pining for the fjords, she is
      """

      name = "span"

      @command
      def handle_span(self,attrs):
        """
        Usage:
          span wing <sparrow>
        """
        return 'spanwing'

    @boop_runnable
    class BoopEventRunnableTestZoom(BoopEventRunnable):
      name = "zoom"

      @event_thread
      class BoopEventThreadTest(BoopEventThread):

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


  @boop_plugin
  class PluginEventsAppTest2(BoopPlugin):
    name = "paz"

    @boop_commandset
    class PazBoopCommandSetTest(BoopCommandSet):
      """ Hello world?
      """

      name = "speed2"

      @command
      def d(self,attrs):
        """
        Quickness!

        Usage:
          speed2 wing <sparrow>
        """
        return "speed2"

    @boop_commandset.opts(start='manual')
    class PazBoopCommandSetTest2(BoopCommandSet):
      """ Additional support commands
      """

      name = "span2"
      @command
      def d(self,attrs):
        """
        Usage:
          span2 wing <sparrow>
        """
        return "span2"

  def test_event_app(self):

    global test_data_path 
    ctx = BoopContext()
    ea = self.EventAppTest(
                test_data_path,
                context=ctx,
                plugins=[
                  self.PluginEventsAppTest,
                  self.PluginEventsAppTest2
                ]
              )

    # There are going to be two plugins in the app.
    # The plugins should have instance names of 
    # "zap" and "paz"
    with self.assertRaises( BoopAppNotStartedException ) as e:
      pe = ea.plugin_byinstancename("zap")

    # Start the main app
    ea.start()

    # Plugin should be launched
    pe = ea.plugin_byinstancename("zap")
    pe2 = ea.plugin_byinstancename("paz")
    self.assertIsInstance(pe,BoopPlugin)
    self.assertIsInstance(pe2,BoopPlugin)

    # Now the commandset should be declared
    cs = pe.object_byinstancename('speed')
    self.assertIsInstance(cs,BoopCommandSet)

    # However, the second commandset should be set to manual 
    # launch so should not be instantiated in the plugin yet
    with self.assertRaises( BoopNotExists ) as e:
      pe.object_byinstancename('span')

    # Can we get the runnable object?
    re = pe.object_byinstancename('zoom')
    self.assertIsInstance(re,BoopEventRunnable)

    self.assertIs(re._plugin_start,'auto')

    # Inject an event
    ev = ea.emit.TEST_SIGNAL('tick')
    self.assertIsInstance(ev,BoopEvent)
    self.assertIs(ev.type,'TEST_SIGNAL')

    # Let's see if it's reached its destination
    time.sleep(0.1)

    tr = re.thread_byinstancename('potato')
    self.assertIsInstance(tr,BoopEventThread)
    self.assertIs(tr.data,'tick')

    # Run a command
    r = ea.execute('speed wing european')
    self.assertEquals(r,'WINGY')

    # Add support for 'help' command
    pha = ea.plugin_add(PluginHelpApp)
    self.assertIsInstance(pha,PluginHelpApp)

    # Check that the add command exists
    r = ea.execute('help')
    self.assertRegexpMatches(r,'Available commands')
    self.assertRegexpMatches(r,'speed')
    self.assertRegexpMatches(r,'help')

    # FIXME: What to do when multiple commandsets are competing
    #        for the same command? should it die? should it throw
    #        an error?

    ea.terminate()



if __name__ == '__main__':
  try:
    unittest.main()
  except Exception:
    pass

