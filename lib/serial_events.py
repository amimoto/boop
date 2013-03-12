from event_handler import *
import serial
import StringIO
import os

class SerialEventSource(EventSource):
  def __init__(self,event_queue,*args,**kwargs):
    super(SerialEventSource,self).__init__(event_queue)
    self.serial = serial.Serial(*args, **kwargs)

  def run(self):
    while 1:
      s = self.serial.readline()
      if self.handle_messages():
        return
      if s:
        self.inject_event(EVENT_READ,s)

# ##################################################
# ##################################################


class SerialEventNode(EventNode):

  def __init__(self,*args,**kwargs):
    super(SerialEventNode,self).__init__()
    self.start()
    self.serial_buffer = StringIO.StringIO()
    self.add_source( SerialEventSource,
                      *args,
                      **kwargs
                     )

  def receive_event(self,event):
    self.serial_buffer.seek(0,os.SEEK_END)
    self.serial_buffer.write(event.data)
    self.serial_buffer.seek(0)
    return True

  def write(self,*args,**kwargs):
    return self.serial.write(*args,**kwargs)

  def read(self,*args,**kwargs):
    self.write.read(*args,**kwargs)
    
  def readlines(self,*args,**kwargs):
    self.write.readlines(*args,**kwargs)
    

