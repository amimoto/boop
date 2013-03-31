from event import *
from command import *

class CommandSerial(Command):
    """
    Commands associated with serial ports.

    Usage:
       serial list
       serial open serial <serial_device> [<baud_rate> [<timeout>]]
       serial close
    """

    def run(self,attrs,core):
      if attrs['list']:
        import thirdparty.serial.tools.list_ports
        comports = thirdparty.serial.tools.list_ports.comports()
        comport_data = ''
        for (dev_path,dev_name,dev_type) in comports:
          comport_data += "{dev_path:15} {dev_name}\n".format(
                            dev_path=dev_path,
                            dev_name=dev_name,
                            dev_type=dev_type
                          )
        core.put_incoming(comport_data)

      elif attrs['close']:
        core.close_port()

      elif attrs['open']:
        kwargs = {}
        args = []
        if attrs['<baud_rate>']:
          args.append(attrs['<baud_rate>'])
        if attrs['<timeout>']:
          kwargs['timeout'] = attrs['<timeout>']

        core.create_port(
            attrs['serial_device'],
            *args, **kwargs
        )

      return attrs

