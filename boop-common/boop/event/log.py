from boop.event.runnable import *
from boop.thirdparty.peewee import *
import time
import datetime
import random
import json
import uuid

class BoopEventTypeCharField(CharField):
  def field_attributes(self):
    return {'max_length':40}

class BoopEventSourceCharField(CharField):
  def field_attributes(self):
    return {'max_length':40}

class DeferredLoading(object):
  def __init__(self):
    self._database = None

  def load_database(self,database):
    self._database = database

  def unload_database(self):
    if self._database != None:
      try:
        self._database.close()
      except AttributeError:
        pass
      self._database = None

  def __getattr__(self,k):
    if self._database:
      return getattr(self._database,k)
    else:
      raise AttributeError()

deferred_loading_db = DeferredLoading()

class BoopEventsLogModel(Model):
  uuid = CharField()
  event_type = BoopEventTypeCharField()
  event_data = TextField()
  event_source = BoopEventSourceCharField(null=True)
  event_target = BoopEventSourceCharField(null=True)
  event_local_only = BooleanField(null=True)
  event_meta_data = TextField(null=True)
  event_datetime = DateTimeField(default=datetime.datetime.now)

  def serialize_data(self,data):
    try:
      serialized_data = json.JSONEncoder().encode(data)
      return serialized_data
    except TypeError:
      return ''

  def deserialize_data(self,serialized_data):
    try:
      data = json.JSONDecoder().decode(serialized_data)
      return data
    except TypeError:
      return None

  def __init__(self,*args,**kwargs):
    super(BoopEventsLogModel,self).__init__(*args,**kwargs)
    if kwargs.get('event'):
      event = kwargs['event']
      self.event_type = event.type
      self.event_data = self.serialize_data(event.data)
      self.event_source = event.source
      self.event_target = event.target
      self.event_meta_data = self.serialize_data(event.meta_data)
      self.event_datetime = event.datetime
      self.event_local_only = event.local_only
      self.uuid = str(uuid.uuid4())

  class Meta:
    database = deferred_loading_db 
    indexes = (
      ( ('event_datetime', 'event_source'), False ),
      ( ('event_datetime', 'event_type'), False ),
      ( ('uuid',), True ),
    )
    order_by = ('event_datetime',)

@event_thread
class BoopEventLoggerThread(BoopEventThread):

  def init(self,*args,**kwargs):
    # self.daemon = False
    pass

  def cleanup(self):
    deferred_loading_db.unload_database()

  @consume.ALL
  def consume_event(self,event):

    # Update the main runner about what's the most recent
    # event we've got logged
    if self.parent.last_datetime == None \
       or self.parent.last_datetime < event.datetime:
        self.parent.last_datetime = event.datetime
    event_log = BoopEventsLogModel(
                    event=event,
                    database=self.parent.database()
                )
    event_log.save()

@event_runnable
class BoopEventLoggerRunnable(BoopEventRunnable):

  @event_thread
  class BoopEventLoggerThread(BoopEventLoggerThread): pass

  def database_create(self,dsn,*args,**kwargs):
    database = SqliteDatabase(dsn,threadlocals=True)
    return database

  def init(self,*args,**kwargs):
    kwargs['threadlocals'] = True
    self.dsn = kwargs.pop('dsn')
    database = self.database_create(self.dsn,*args,**kwargs)
    database.connect()
    deferred_loading_db.load_database(database)
    BoopEventsLogModel.create_table("Silent Create")
    self._database = database

    # Get the most recent event entry's datetime
    self.last_datetime = None
    result = BoopEventsLogModel.select(
                  fn.Max(BoopEventsLogModel.event_datetime).alias('event_datetime')
                )
    for log_entry in result:
      self.last_datetime = log_entry.event_datetime

  def database(self):
    return self._database

  def events_from(self,from_datetime=None):
    result = None
    if from_datetime == None:
      result = BoopEventsLogModel.select()
    else:
      result = BoopEventsLogModel.select().where(
                  BoopEventsLogModel.event_datetime > from_datetime
                )

    return result

