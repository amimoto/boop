from __future__ import absolute_import
from event.core import *
from event.ports.core import *
from serial import Serial

@event_runnable
class SerialEventRunnable(IPortEventRunnable):

  port_class = Serial

  def init(self,port_name,*args,**kwargs):
    kwargs['timeout'] = self.timeout
    self.read_size = kwargs.get('read_size',1000)
    super(SerialEventRunnable,self).init(port_name,*args,**kwargs)


