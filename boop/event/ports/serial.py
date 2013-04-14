from __future__ import absolute_import
from event.core import *
from event.ports.core import *
from serial import Serial

@event_runnable
class SerialEventRunnable(IPortEventRunnable):
  port_class = Serial

@event_runnable
class SerialListenEventRunnable(IPortListenEventRunnable):
  pass

