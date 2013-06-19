from __future__ import absolute_import
from boop.common import *
from boop.event import *
from boop.event.ports.core import *
import os

class BoopFile(BoopBase):
  _file = None
  _injected_reads = None

  def __init__(self,*args,**kwargs):
    if kwargs.get('name',False):
      self.open(*args,**kwargs)

  def open(self,name,*args,**kwargs):

    open_kwargs = kwargs_filter(kwargs,'mode', 'buffering') 
    self._file = open(name,*args,**open_kwargs)
    if kwargs.pop('seek_end',True):
      self._file.seek(os.path.getsize(name))
    self._injected_reads = []
    self._position = 0

  def read(self,size=None):
    # FIXME: Injected reads do not listen 
    #        to read size
    if self._injected_reads:
      return self._injected_reads.pop(0)
    result = self._file.read(size)
    return result

  def write(self,data):
    result = self._file.write(data)
    self._injected_reads.append(data)
    return result

  def __getattr__(self,attr):
    if self._file:
      return getattr(self._file,attr)
    if attr in dir(file):
      raise Exception('File has not been opened yet.')

@event_runnable
class FileBoopEventRunnable(IPortBoopEventRunnable):
  port_class = BoopFile

@event_runnable
class FileListenBoopEventRunnable(IPortListenBoopEventRunnable):
  pass

