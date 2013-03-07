#!/usr/bin/python

import serial
import threading
import datetime
import time
import Queue

# ##################################################
# ##################################################

class Client(threading.Thread):
  def __init__(self):
    super(Client,self).__init__()
    self.message_queue = Queue.Queue()

  def trigger_event(self,event):
    self.message_queue.put(event)

  def run(self):
    while 1:
      d = self.message_queue.get(True,None)
      if d == EVENT_TERMINATE:
        return
      else:
        print "M:",d


# ##################################################
# ##################################################

def EVENT_READ(): pass
def EVENT_REGISTER(): pass
def EVENT_TERMINATE(): pass

class Event():
  def __init__(self,event_type,data=None):
    self.type = event_type
    self.data = data


# ##################################################
# ##################################################

class EventFactory(threading.Thread):
  def __init__(self,event_queue):
    super(EventFactory,self).__init__()
    self.event_queue = event_queue
    self.message_queue = Queue.Queue()

  def trigger_event(self,event,data=None):
    self.event_queue.put(Event(event,data))

  def stop(self):
    self.message_queue.put(Event(EVENT_TERMINATE))

  def handle_messages(self):
    try:
      message = self.message_queue.get(False)
      return message.type == EVENT_TERMINATE
    except Queue.Empty:
      return False

# ##################################################
# ##################################################

class SerialEventFactory(EventFactory):
  def __init__(self,event_queue,*args,**kwargs):
    super(SerialEventFactory,self).__init__(event_queue)
    self.serial = serial.Serial(*args, **kwargs)

  def run(self):
    while 1:
      s = self.serial.readline()
      if self.handle_messages():
        return
      if s:
        self.trigger_event(EVENT_READ,s)


# ##################################################
# ##################################################

class EventHandler(threading.Thread):
  def __init__(self):
    super(EventHandler,self).__init__()
    event_queue = Queue.Queue()
    self.event_queue = event_queue
    self.clients = []
    self.event_factories = []
    self.event_queue = Queue.Queue()

  def trigger_event(self,event):
    for cli in self.clients:
        cli.trigger_event(event)

  def run(self):
    while 1:
      event = self.event_queue.get(True,None)
      if event.type == EVENT_READ:
        self.trigger_event(event.data)
      elif event.type == EVENT_REGISTER:
        pass
      elif event.type == EVENT_TERMINATE:
        return

  def register_event(self, obj):
    self.event_queue.put(Event(EVENT_REGISTER))

  def start_event_factory(self,factory_class,*args,**kwargs):
    factory = factory_class(self.event_queue,*args,**kwargs)
    factory.start()
    self.event_factories.append(factory)

  def start_client(self,client):
    client.start()
    self.clients.append(client)
    return client

  def stop(self):
    self.event_queue.put(Event(EVENT_TERMINATE))
    for cli in self.clients:
        cli.trigger_event(EVENT_TERMINATE)
    for factory in self.event_factories:
        factory.stop()

s = EventHandler()
s.start()

s.start_event_factory(
  SerialEventFactory,
    'ttyVirtualS1', 9600, timeout=1
  )

c = Client()
s.start_client(c)

#c2 = Client()
#s.start_client(c2)

time.sleep(10)

s.stop()
