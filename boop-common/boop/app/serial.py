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

  def send(self,s):
    self.object_byinstancename('SerialListenEventRunnable').send(s)

##################################################
#### Event Listener
#### This is ever so slightly different than a 
#### SerialEventRunnable as it does not directly
#### handle the port
##################################################

@event_app_plugin
class SerialClientEventsAppPlugin(EventsAppPlugin):

  @plugin_runnable
  class SerialListenEventRunnable(PluginEventRunnable,SerialListenEventRunnable): 
    pass

  def send(self,s):
    self.object_byinstancename('SerialListenEventRunnable').send(s)

