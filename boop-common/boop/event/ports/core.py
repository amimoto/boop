from event.core import *

@event_thread
class IPortEventListener(EventThread):

  def event_source(self,k,*args,**kwargs):
    return self.parent.port_name

  @consume.PORTS_CONNECTED
  def report(self,event):
    self.emit.PORTS_CONNECTED_REPLY()

  def poll(self):
    data = self.parent.port_obj.read(self.parent.read_size)
    if data: 
      self.PORT_READ(data)

@event_thread
class IPortEventReceiver(EventThread):

  @consume.when.PORT_SEND(for_me)
  def send(self,event):
    if self.parent.send_callback:
      self.parent.send_callback(self,event)
    self.parent.port_obj.write(event.data)

  @consume.when.PORT_READ(for_me)
  def received_data(self,event):
    if self.parent.receive_callback:
      self.parent.receive_callback(self,event)


class IPortEventRunnable(EventRunnable):
  """ base definition of a port
  """

  port_class = None

  @event_thread
  class IPortEventListener(IPortEventListener): pass

  @event_thread
  class IPortEventReceiver(IPortEventReceiver): pass

  def send(self,s):
    self.thread_get('IPortEventListener').emit.PORT_SEND(s,event_target=self.port_name)

  def init(self,
              port_name=None,
              receive_callback=None,
              send_callback=None,
              *args,**kwargs):
    self.port_name = port_name
    self.port_obj = self.port_class(port_name,*args,**kwargs)
    self.receive_callback = receive_callback
    self.send_callback = send_callback
    self.read_size = kwargs.get('read_size',1000)
    kwargs['timeout'] = self.timeout



##################################################
#### Event Listener
#### This is ever so slightly different than a 
#### SerialEventRunnable as it does not directly
#### handle the port
#### This is meant to be used in conjunction with 
#### a SerialEventRunnable similar to a client/server
#### architecture
##################################################

@event_runnable
class IPortListenEventRunnable(EventRunnable):

  @event_thread
  class IPortEventReceiver(IPortEventReceiver): 

    @consume.when.PORT_SEND(for_me)
    def send(self,event):
      if self.parent.send_callback:
        self.parent.send_callback(self,event)

  def send(self,s):
    self.thread_get('IPortEventReceiver')\
        .emit.PORT_SEND( s,event_source=self.port_name )

  def init(self,
              port_name,
              receive_callback=None,
              send_callback=None,
              *args,**kwargs):
    self.port_name = port_name
    self.receive_callback = receive_callback
    self.send_callback = send_callback


