from __future__ import absolute_import
from boop.event import *
from boop.event.ports.core import *
from StringIO import StringIO

class BoopStringIO(StringIO):
  def __init__(self,*args,**kwargs):
    print "INIT:",args,kwargs
    super(BoopStringIO,self).__init__(*args,**kwargs)

  def read(self,*args,**kwargs):
    print "READING:", args, kwargs
    res = super(BoopStringIO,self).read(*args,**kwargs)
    return res

  def write(self,*args,**kwargs):
    print "WRITING:", args, kwargs
    pos = self.tell()
    res = super(BoopStringIO,self).write(*args,**kwargs)
    self.seek(pos)
    return res

@event_runnable
class StringBoopEventRunnable(IPortBoopEventRunnable):
  port_class = BoopStringIO

@event_runnable
class StringListenBoopEventRunnable(IPortListenBoopEventRunnable):
  pass


