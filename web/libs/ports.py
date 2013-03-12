import serial_events


class SerialEventMonitor(serial_events.SerialEventNode):
  def __init__(self,event_queue,*args,**kwargs):
    super(SerialEventMonitor,self).__init__(event_queue)

  def receive_event(self,event):
    super(SerialEventMonitor,self).receive_event(event)
    self.incoming_queue.put(event)
    return True

def create_port(*args,**kwargs):
  return SerialEventMonitor(*args,**kwargs)



