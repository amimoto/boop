from event import *
import event
from event.ports.serial import *

from command import *
from app import *


class SerialCommandSet(PluginCommandSet):
    """
    Manipulate and manage the serial port

    Usage:
       serial list
       serial open <serial_device> [<baud_rate> [<timeout>]]
       serial close
       serial send <text>...
    """

    name = "serial"

    def execute(self,attrs,app):
      output = ''

      # serial list
      if attrs['list']:
        import thirdparty.serial.tools.list_ports
        comports = thirdparty.serial.tools.list_ports.comports()
        for (dev_path,dev_name,dev_type) in comports:
          output += "{dev_path:15} {dev_name}\n".format(
                            dev_path=dev_path,
                            dev_name=dev_name,
                            dev_type=dev_type
                          )

      # serial close
      elif attrs['close']:
        app.close_port()

      # serial open <serial_device> [<baud_rate> [<timeout>]]
      elif attrs['open']:

        kwargs = {}
        args = []
        if attrs['<baud_rate>']:
          args.append(attrs['<baud_rate>'])
        if attrs['<timeout>']:
          kwargs['timeout'] = attrs['<timeout>']

        obj = self.plugin.class_start_byname(
                  'SerialEventRunnable',
                  attrs['<serial_device>']
                )
        self.plugin.serial_port_runnable = obj

      # serial send <text>...
      elif attrs['send']:
        if self.plugin.serial_port_runnable:
          self.plugin.serial_port_runnable.send(" ".join(attrs['<text>']))

      return { 'attrs': attrs, 'output': output }


@event_app_plugin
class SerialEventsAppPlugin(EventsAppPlugin):

  @plugin_runnable.opts(start='manual')
  class SerialEventRunnable(PluginEventRunnable,SerialEventRunnable): pass

  @plugin_commandset
  class SerialCommandSet(SerialCommandSet): pass

##################################################
#### Event Listener
##################################################

@event_thread
class SerialListenerEventReceiver(EventThread):

  @consume.SERIAL_READ
  def received_data(self,event):
    if self.parent.plugin.receive_callback:
      self.parent.plugin.receive_callback(self,event)

@plugin_runnable
class SerialListenerEventRunnable(PluginEventRunnable):

  def init(self,*args,**kwargs):
    super(SerialListenerEventRunnable,self).init(*args,**kwargs)
    self.serial_port_path = self.plugin.serial_port_path

  @event_thread
  class SerialListenerEventReceiver(SerialListenerEventReceiver): pass


@event_app_plugin
class SerialClientEventsAppPlugin(EventsAppPlugin):

  def init(self,serial_port_path=None,receive_callback=None,*args,**kwargs):
    super(SerialClientEventsAppPlugin,self).init(*args,**kwargs)
    self.serial_port_path = serial_port_path
    self.receive_callback = receive_callback

  @plugin_runnable
  class SerialListenerEventRunnable(SerialListenerEventRunnable): pass


