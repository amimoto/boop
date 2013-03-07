#!/usr/bin/python

import serial
import threading
import datetime
import time
import Queue
import unittest

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

class EventSource(threading.Thread):
  def __init__(self,event_queue):
    super(EventSource,self).__init__()
    self.event_queue = event_queue
    self.message_queue = Queue.Queue()

  def inject_event(self,event,data=None):
    self.event_queue.put(Event(event,data))

  def terminate(self):
    self.message_queue.put(Event(EVENT_TERMINATE))

  def handle_messages(self):
    try:
      message = self.message_queue.get(False)
      return message.type == EVENT_TERMINATE
    except Queue.Empty:
      return False

# ##################################################
# ##################################################

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

class EventNode(threading.Thread):

  def __init__(self,event_sources=None,event_consumers=None):
    super(EventNode,self).__init__()
    self.message_queue = Queue.Queue()
    self.event_queue = Queue.Queue()
    if event_sources == None: event_sources = set()
    self.event_sources = event_sources
    if event_consumers == None: event_consumers = set()
    self.event_consumers = event_consumers


  #######################################################
  # Events
  #######################################################

  def receive_event(self,event):
    return True

  def propagate_event(self,event):
    for consumer in self.event_consumers:
      consumer.receive_event(event)

  def inject_event(self,event):
    self.event_queue.put(event)

  def terminate(self):
    self.inject_event(Event(EVENT_TERMINATE))

  #######################################################
  # Messages
  #######################################################

  def inject_message(self,message):
    self.message_queue.put(message)

  #######################################################
  # Consumer management
  #######################################################

  def add_consumer(self,consumer):
    self.event_consumers.append(consumer)

  def remove_consumer(self,node):
    self.event_consumers.remove(consumer)

  #######################################################
  # Event Generation
  #######################################################

  def add_source(self,source_class,*args,**kwargs):
    source = source_class(self.event_queue,*args,**kwargs)
    source.start()

  def remove_source(self,source):
    source.terminate()

  #######################################################
  #######################################################

  def run(self):
    while 1:
      message = self.event_queue.get(True,None)
      if message.type == EVENT_TERMINATE:
        self.terminate()
        return
      elif self.receive_event(message):
        self.propagate_event(message)

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

# ##################################################
# ##################################################


s = SerialEventNode()
time.sleep(10)
s.terminate()
