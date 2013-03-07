#!/usr/bin/python

import threading
import datetime
import time
import Queue

class ServerClient():

    class RequestClass(threading.Thread):
      def __init__(self, queue):
        super(ServerClient.RequestClass,self).__init__()
        self.queue = queue

      def run(self):
        d = self.queue.get(True,None)
        print "RECEIVED!", d


    class ServerClass(threading.Thread):
      def __init__(self, queue):
        super(ServerClient.ServerClass,self).__init__()
        self.queue = queue
        self.iterations = 5
        self.delay = 1

      def trigger_event(self,datetime):
        self.queue.put(datetime)

      def run(self):
        for i in range(self.iterations):
          now = datetime.datetime.now()
          # print "%s says Hello World at time: %s\n" % (self.getName(), now)
          time.sleep(self.delay)
          self.trigger_event(now)


    def run(self):
        queue = Queue.Queue()
        self.queue = queue

        s = self.ServerClass(queue)
        s.start()

        t = self.RequestClass(queue)
        t.start()

        t2 = self.RequestClass(queue)
        t2.start()

sc = ServerClient()
sc.run()
