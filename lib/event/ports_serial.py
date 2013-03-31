from core import *
import serial

# FIXME: need better names for the serial port classes
#        right now they're confusing.
#        Listener vs Receiver? wazzat mean?

@event_thread
class SerialPortEventListener(EventThread):

  def event_source(self,k,*args,**kwargs):
    return self.parent.serial_port_path

  def poll(self):
    data = self.parent.serial_port.read(self.parent.read_size)
    if data: 
      self.SERIAL_READ(data)

@event_thread
class SerialPortEventReceiver(EventThread):

  #FIXME
  #@consume.when.SERIAL_SEND(lambda s,e:s.parent.serial_port_path==e.source)
  @consume.SERIAL_SEND
  def send(self,event):
    self.parent.serial_port.write(event.data)

  @consume.when.SERIAL_READ(lambda s,e:s.parent.serial_port_path==e.source)
  def received_data(self,event):
    pass

@event_runnable
class SerialPortRunnable(EventRunnable):

  @event_thread
  class SerialPortEventListener(SerialPortEventListener): pass

  @event_thread
  class SerialPortEventReceiver(SerialPortEventReceiver): pass

  def init(self,serial_port_path,*args,**kwargs):
    self.read_size = kwargs.get('read_size',1000)
    kwargs['timeout'] = self.timeout
    self.serial_port_path = serial_port_path
    self.serial_port = serial.Serial(serial_port_path,*args, **kwargs)


