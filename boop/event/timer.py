from core import *
import serial
import time
import datetime
import random

@event_runnable
class TickRunnable(EventRunnable):

  @event_thread
  class TickEventThread2(EventThread):
    @consume.TICK
    def receive_tick(self,event):
      print "EMIT"
      self.emit.NEWSIG()

  @event_thread
  class TickEventThread5(EventThread):
    @consume.when.NEWSIG(lambda *event:random.random()<0.5)
    def receive_tick(self,event):
      print "CONDITIONAL!"

  @event_thread
  class TickEventThread1(EventThread):
    def poll(self):
      time.sleep(1)
      self.emit.TICK(datetime.datetime.now())

if __name__ == "__main__":
  ed = EventDispatch()
  try:
    ed.start()
    ed.add_runnable(TickRunnable)
    time.sleep(2)
    print "**************************************************"
    print "**************************************************"
    print "*************** TERMINATE ************************"
    print "**************************************************"
    print "**************************************************"
    print ">>>>:",ed
  except KeyboardInterrupt:
    pass

  ed.terminate()

