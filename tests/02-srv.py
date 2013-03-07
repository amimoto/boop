#!/usr/bin/python

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
    d = self.queue.get(True,None)
    print "RECEIVED!", d


# ##################################################
# ##################################################

def EVENT_TICK(): pass
def EVENT_REGISTER(): pass

# ##################################################
# ##################################################

class Server():

    class MonitorClass(threading.Thread):
      def __init__(self, event_queue, delay=1, iterations=5):
        super(Server.MonitorClass,self).__init__()
        self.iterations = iterations
        self.event_queue = event_queue
        self.delay = delay

      def run(self):
        for i in range(self.iterations):
          time.sleep(self.delay)
          self.event_queue.put(EVENT_TICK)

    class ServerClass(threading.Thread):
      def __init__(self, srv_queue):
        super(Server.ServerClass,self).__init__()
        self.srv_queue = srv_queue
        self.clients = []
        self.monitor_queue = Queue.Queue()
        self.iterations = 5
        self.delay = 1

      def trigger_event(self,event):
        for cli in self.clients:
            cli.trigger_event(event)

      def run(self):
        mc = Server.MonitorClass(self.monitor_queue)
        mc.start()

        for i in range(self.iterations):
          event = self.monitor_queue.get(True,None)
          if event == EVENT_TICK:
            now = datetime.datetime.now()
            time.sleep(self.delay)
            self.trigger_event(now)
          elif event == EVENT_REGISTER:
            pass

      def register_event(self, obj):
        self.monitor_queue.put(EVENT_REGISTER)

    # ##################################################
    # ##################################################

    def start_server(self):
        srv_queue = Queue.Queue()
        self.srv_queue = srv_queue
        self.server = self.ServerClass(srv_queue)
        self.server.start()

    def start_client(self,client):
        client.start()
        self.server.clients.append(client)
        return client

s = Server()
c = Client()
s.start_server()
s.start_client(c)


