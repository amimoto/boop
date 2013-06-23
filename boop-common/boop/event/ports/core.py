from boop.event import *
import time

@event_thread
class IPortBoopEventListener(BoopEventThread):

  def event_source(self,k,*args,**kwargs):
    return self.parent.port_name

  @consume.PORTS_CONNECTED
  def report(self,event):
    self.emit.PORTS_CONNECTED_REPLY()

  def poll(self):
    if not self._terminate and self.parent:
      data = self.parent.port_obj.read(self.parent.read_size)
      if data: 
        self.PORT_READ(data)

def port_event_for_me_or_all(self,event):
  if for_me_or_all(self,event) \
    or self.parent.port_name == None \
    or event.target == None \
    or event.target == self.parent.port_name:
      return True
  return False

@event_thread
class IPortBoopEventReceiver(BoopEventThread):

  @consume.when.PORT_SEND(port_event_for_me_or_all)
  def send(self,event):
    if self.parent.send_callback:
      self.parent.send_callback(self,event)
    self.parent.port_obj.write(event.data)

  @consume.when.PORT_READ(port_event_for_me_or_all)
  def received_data(self,event):
    if self.parent.receive_callback:
      self.parent.receive_callback(self,event)


PORT_INDEX = 0

class BoopPortRunnable(BoopEventRunnable):
  """ base definition of a port

      With ports, the _instance_name is kept
      separate than the port_name.

  """

  port_class = None
  counter = 0

  @event_thread
  class IPortBoopEventListener(IPortBoopEventListener): 
    name = 'port_listener'

  @event_thread
  class IPortBoopEventReceiver(IPortBoopEventReceiver): 
    name = 'port_receiver'

  def send(self,s):
    self.thread_byinstancename('port_receiver')\
          .emit.PORT_SEND(s,target=self.port_name)

  def port_class_start(self,*args,**kwargs):
    global PORT_INDEX
    PORT_INDEX += 1
    self._index = PORT_INDEX
    self.port_obj = self.port_class(*args,**kwargs)

  def init(self,
              receive_callback=None,
              send_callback=None,
              *args,**kwargs):
    self.port_name = kwargs.get('name',None)
    self.port_class_start(*args,**kwargs)
    port_key = kwargs.pop('key',None)
    self.receive_callback = receive_callback
    self.port_key = port_key or self._index
    self.send_callback = send_callback
    self.read_size = kwargs.get('read_size',-1)
    kwargs['timeout'] = self.timeout



##################################################
#### BoopEvent Listener
#### This is ever so slightly different than a 
#### SerialBoopEventRunnable as it does not directly
#### handle the port
#### This is meant to be used in conjunction with 
#### a SerialBoopEventRunnable similar to a client/server
#### architecture
##################################################

@event_runnable
class BoopPortListenRunnable(BoopEventRunnable):

  @event_thread
  class IPortBoopEventReceiver(IPortBoopEventReceiver): 
    name = 'port_receiver'

    @consume.when.PORT_SEND(port_event_for_me_or_all)
    def send(self,event):
      if self.parent.send_callback:
        self.parent.send_callback(self,event)

  def send(self,s):
    self.thread_byinstancename('port_receiver')\
        .emit.PORT_SEND( s,event_source=self.port_name )

  def init(self,
              port_name,
              receive_callback=None,
              send_callback=None,
              *args,**kwargs):
    self.port_name = port_name
    self.receive_callback = receive_callback
    self.send_callback = send_callback


