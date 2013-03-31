from event import *
from command import *


class EventsApp(object):

  def __init__(self,event_class=EventDispatch,command_class=CommandRunner):
    self.events = event_class()
    self.commands = command_class()

  def parse(self,s):
    return self.commands.execute(s,self)

  def commandset_add(self,*args,**kwargs):
    return self.command.commandset_add(*args,**kwargs)

  def commandset_remove(self,*args,**kwargs):
    return self.command.commandset_remove(*args,**kwargs)

  def commandset_list(self,*args,**kwargs):
    return self.command.commandset_list(*args,**kwargs)

if __name__ == "__main__":
  ev = EventsApp()
  print ev.parse('-h')['output']


