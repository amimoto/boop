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

def _port_read_for_me(self,event):
  if self.parent.port_name == None:
    return True
  return self.parent.port_name == event.source

@event_thread
class IPortEventReceiver(EventThread):

  @consume.when.PORT_SEND(_port_read_for_me)
  def send(self,event):
    self.parent.port_obj.write(event.data)

  @consume.when.PORT_READ(_port_read_for_me)
  def received_data(self,event):
    pass


class IPortEventRunnable(EventRunnable):
  """ base definition of a port
  """

  port_class = None

  @event_thread
  class IPortEventListener(IPortEventListener): pass

  @event_thread
  class IPortEventReceiver(IPortEventReceiver): pass

  def send(self,s):
    self.thread_get('IPortEventListener').emit.PORT_SEND(s,event_source=self.port_name)

  def init(self,port_name=None,*args,**kwargs):
    self.port_name = port_name
    self.port_obj = self.port_class(port_name,*args,**kwargs)



