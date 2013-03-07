from event_handler import *
import serial

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

  def __init__(self):
    super(SerialEventNode,self).__init__()
    self.start()
    self.add_source( SerialEventSource,
                      'ttyVirtualS1', 
                      9600, 
                      timeout=1
                      )


  def receive_event(self,event):
    print "Received!",event.data
    return False


s = SerialEventNode()
time.sleep(10)
s.terminate()
