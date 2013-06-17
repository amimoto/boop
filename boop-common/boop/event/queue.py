import Queue

# ##################################################
# ##################################################

class BoopEventQueue(Queue.Queue,object):
  def __init__(self,*args,**kwargs):
    super(BoopEventQueue,self).__init__(*args,**kwargs)

  def __getattribute__(self,k):
    try:
      return super(BoopEventQueue,self).__getattribute__(k)
    except AttributeError:
      return lambda *args,**kwargs: Event(k,*args,**kwargs)


