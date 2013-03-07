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
    self.queue = Queue.Queue()

  def trigger_event(self,event):
    self.queue.put(event)

  def run(self):
    while 1:
      d = self.queue.get(True,None)
      print "RECEIVED!", d


# ##################################################
# ##################################################

def EVENT_READ(): pass
def EVENT_REGISTER(): pass

class Event():
  def __init__(self,event_type,data=None):
    self.type = event_type
    self.data = data

# ##################################################
# ##################################################

class Server():

    class SerialMonitor(threading.Thread):
      def __init__(self, serial, event_queue):
        super(Server.SerialMonitor,self).__init__()
        self.serial = serial
        self.event_queue = event_queue

      def run(self):
        while 1:
          s = self.serial.readline()
          self.event_queue.put(Event(EVENT_READ,s))

    class EventHandler(threading.Thread):
      def __init__(self, event_queue):
        super(Server.EventHandler,self).__init__()
        self.event_queue = event_queue
        self.clients = []
        self.monitor_queue = Queue.Queue()
        self.serial = serial.Serial('ttyVirtualS1', 9600, timeout=10)

      def trigger_event(self,event):
        for cli in self.clients:
            cli.trigger_event(event)

      def run(self):
        mc = Server.SerialMonitor(self.serial,self.monitor_queue)
        mc.start()

        while 1:
          event = self.monitor_queue.get(True,None)
          if event.type == EVENT_READ:
            self.trigger_event(event.data)
          elif event.type == EVENT_REGISTER:
            pass

      def register_event(self, obj):
        self.monitor_queue.put(Event(EVENT_REGISTER))

    # ##################################################
    # ##################################################

    def start_server(self):
        event_queue = Queue.Queue()
        self.event_queue = event_queue
        self.event_handler = self.EventHandler(event_queue)
        self.event_handler.start()

    def start_client(self,client):
        client.start()
        self.event_handler.clients.append(client)
        return client

s = Server()
c = Client()
s.start_server()
s.start_client(c)

c2 = Client()
s.start_client(c2)

