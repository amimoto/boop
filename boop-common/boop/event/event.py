import datetime

# ##################################################
# Event Consumer Functions should have the property
# func._event_slots = {
#
#    # if the consumption event is only on certain
#    # situations
#    'slot_name': lambda event: return True, 
#
#    # if there are no conditions and we accept
#    # all events with the slot_name...
#    'slot_name': None
#
#    ...
#
# }
# ##################################################

def for_only_me(self,event):
  return self._name != None \
      and self._instance_name == event.target

def for_me_or_all(self,event):
  return self._instance_name == None \
      or event.target == None \
      or self._instance_name == event.target

class BoopEventSlots(object):

  def events(self,condition,events,func):
    event_slots = {}
    for event_slot in events:
      event_slots[event_slot] = condition
    func._event_slots = event_slots
    return func

  def _getattr_helper(self,condition,events):
    return lambda func: self.events(condition,events,func)

  def __getattr__(self,k):
    return lambda condition: self._getattr_helper(condition,[k])

class BoopEventSlotsBasic(BoopEventSlots):

  def __init__(self):
    self.when = BoopEventSlots()

  def _getattr_helper(self,func,events):
    return self.events(None,events,func)

consume = BoopEventSlotsBasic()

# ##################################################
# ##################################################

class BoopEvent(object):

  def __str__(self):
    return "Event {type}: ({source}) -> ({target})".format(
                  type=self.type,
                  data=self.data,
                  source=self.source or "ANONYMOUS",
                  target=self.target or "ALL",
                  local_only=self.local_only,
                  meta_data=self.meta_data,
                  datetime=self.datetime,
              )
    
  def __init__(
              self,
              event_type,
              data=None,
              local_only=False,
              source=None,
              target=None,
              meta_data=None,
            ):
    self.type = event_type
    self.data = data
    self.source = source
    self.target = target
    self.local_only = local_only
    self.meta_data = meta_data or {}
    self.datetime = datetime.datetime.now()


