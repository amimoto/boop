import Queue
import ports
import commands
import event_handler

class Core(object):

  def __init__(self):
    self.port = None
    self.incoming_queue = Queue.Queue()
    self.outgoing_queue = Queue.Queue()
    self.command_parser = commands.CommandParser()

  def write_outgoing(self,data):
    self.outgoing_queue.put()

  def create_port(self, *args, **kwargs):
    kwargs['incoming_queue'] = self.incoming_queue
    kwargs['outgoing_queue'] = self.outgoing_queue
    self.port = ports.create_port(*args,**kwargs)

  def parse(self,s):
    self.command_parser(self,s)


@commands.command
class CommandList(commands.Command):
    """
    Lists available communication ports

    Usage:
       > list [serial]
    """

    def run(self,attrs,core):
      import thirdparty.serial.tools.list_ports
      comports = thirdparty.serial.tools.list_ports.comports()
      return attrs


@commands.command
class CommandOpen(commands.Command):
    """
    Open a communication port

    Usage:
       > open serial <serial_device> [<baud_rate> [<timeout>]]
    """

    def run(self,attrs,core):

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


