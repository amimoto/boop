#!/usr/bin/python

import sys; sys.path.append('..')

from boop.app import *
from boop.app.ports.file import *

import testdata

import unittest
import os.path
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


  @boop_plugin
  class PluginEventCapture(BoopPlugin):

    @boop_runnable
    class RunnableEventCapture(BoopEventRunnable):
      name = "running"

      @event_thread
      class ThreadEventCapture(BoopEventThread):
        name = 'intercept'

        def init(self,*args,**kwargs):
          self.captures = []

        @consume.PORT_READ
        def on_signal_read(self,event):
          self.captures.append(event)

  def test_file_plugin(self):

    ctx = BoopContext(debug=True)
    ea = self.EventAppTest(
                  test_data_path,
                  context=ctx,
                  plugins=[]
                )

    # Delete the log.txt file if it exists
    log_fpath = test_data_path+'/t07_log.txt'
    try:
      os.unlink(log_fpath)
    except OSError: pass

    # Create a new file
    log_fh = open(log_fpath,'w')

    # Start the main app
    ea.start()

    # Start the event capture plugin
    si = ea.plugin_add(self.PluginEventCapture)
    self.assertIsInstance(si,self.PluginEventCapture)

    # Rack the port post-lauch
    psa = ea.plugin_add(BoopFilePlugin)
    self.assertIsInstance(psa,BoopFilePlugin)

    # Let's open the file
    ea.execute('f open %s'%log_fpath)

    # Let's send some data in!
    log_fh.write('mew mew mew')
    log_fh.close()

    # Wait for the message to propagate
    time.sleep(0.2)

    # Did we get the message?
    time.sleep(0.1)
    r = si.object_byinstancename('running')
    th = r.thread_byinstancename('intercept')
    self.assertIsInstance(th,BoopEventThread)
    self.assertIsInstance(th.captures[0],BoopEvent)
    self.assertEquals(th.captures[0].data,'mew mew mew')

    # Create a new write file
    log_fpath2 = log_fpath + ".2"
    ea.execute('f open -w %s'%log_fpath2)
    r = ea.execute('f list')
    self.assertRegexpMatches(r,'t07_log.txt')

    # Okay, let's try and send a message
    r = ea.execute('f writeln "top"')
    r = ea.execute('f writeln "bottom"')
    time.sleep(0.1)
    with open(log_fpath2) as f:
      r = f.read()
    self.assertEquals(r,'top\nbottom\n')

    # Done!
    ea.terminate()


if __name__ == '__main__':
  try:
    unittest.main()
  except Exception:
    pass

