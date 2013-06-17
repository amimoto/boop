from __future__ import absolute_import
from boop.event.core import *
from boop.event.ports.core import *
from serial import Serial

@event_runnable
class SerialBoopEventRunnable(IPortBoopEventRunnable):
  port_class = Serial

@event_runnable
class SerialListenBoopEventRunnable(IPortListenBoopEventRunnable):
  pass

