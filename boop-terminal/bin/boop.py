#!/usr/bin/python

import os,sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../boop-common/')

import textwrap

import curses
import curses.panel
import curses.ascii
import curses.textpad
import datetime
import time

from boop.event import *
from boop.app import *
from boop.command import *
from boop.app.tools import *

##################################################

class res:
  UI_STATUS_BAR_LEFT_DEFAULT = "Ready"
  UI_STATUS_BAR_CENTER_DEFAULT = ""
  UI_STATUS_BAR_RIGHT_DEFAULT = "'help' for online help"

##################################################
### Terminal
##################################################

class WindowTerminal(object):
  def __init__(self,parent):
    self._parent = parent
    self._terminal = curses.newwin(
                      parent.screen_height-1,
                      parent.screen_width,
                      0,0
                      )
    self._terminal.scrollok(True)

  def ui_terminal_data(self,s):
    self._terminal.addstr(s)

  def refresh(self):
    self._terminal.refresh()


##################################################
### Status bar
##################################################

class WindowStatusBar(object):
  def __init__(
              self,
              parent,
              left_text='',
              center_text='',
              right_text='',
              ):
    self._status_bar = curses.newwin(
                      1,
                      parent.screen_width,
                      parent.screen_height-2,0
                      )
    self._left_text = left_text
    self._center_text = center_text
    self._right_text = right_text
    self._status_bar_panel = curses.panel.new_panel(self._status_bar)
    self._status_bar_width = parent.screen_width

  def status_string(self,left,center,right,width):
    s = center.center(width)
    s = s[0:-len(right)] + right
    s = left + s[len(left):]
    return s

  def string_left(self,s):
    self._left_text = s

  def string_center(self,s):
    self._center_text = s

  def string_right(self,s):
    self._right_text = s

  def refresh(self):
    # FIXME: curses seems to throw an error if text goes to the 
    #        edge of the panel
    status_string = self.status_string(
          self._left_text,
          self._center_text,
          self._right_text,
          self._status_bar_width-1 
        )

    self._status_bar.bkgd(ord(' '),curses.A_REVERSE)
    self._status_bar.clear()
    self._status_bar.addstr(0, 0, status_string, curses.A_REVERSE)
    self._status_bar.refresh()


##################################################
### Prompt bar
##################################################

class Textbox(curses.textpad.Textbox):

  def __init__(self,*args,**kwargs):
    curses.textpad.Textbox.__init__(self,*args,**kwargs)
    self.win.timeout(100)

  def edit(self, validate=None):
    "Edit in the widget window and collect the results."
    while 1:
      ch = self.win.getch()
      if validate:
        ch = validate(ch)
      if not ch or ch == -1:
        return None
      if not self.do_command(ch):
        break
      self.win.refresh()
    return self.gather()

class WindowPromptBar(object):
  def __init__(self,parent):
    self._prompt = curses.newwin(
                      1,
                      parent.screen_width,
                      parent.screen_height-1,0
                      )
    self._prompt.scrollok(True)
    self._prompt_text = Textbox(self._prompt)

  def ui_poll(self):
      r = self._prompt_text.edit()
      if r: self._prompt.clear()
      return r

  def refresh(self):
    self._prompt.refresh()


##################################################
### Boop Window
##################################################

class BoopWindow(object):

  def refresh(self):
    self.stdscr.refresh()
    self.terminal_refresh()
    self.status_bar_refresh()
    self.prompt_refresh()


  def terminal_refresh(self):
    self._terminal.refresh()

  def status_bar_refresh(self):
    self._status_bar.refresh()

  def prompt_refresh(self):
    self._prompt.refresh()

  def register_window_geometry(self):
    self.screen_height,self.screen_width = self.stdscr.getmaxyx()
    self.refresh()

  def __init__(self):
    self.stdscr = curses.initscr()
    self.screen_height,self.screen_width = self.stdscr.getmaxyx()
    self._terminal = WindowTerminal(self)
    self._status_bar = WindowStatusBar(
                          self,
                          res.UI_STATUS_BAR_LEFT_DEFAULT,
                          res.UI_STATUS_BAR_CENTER_DEFAULT,
                          res.UI_STATUS_BAR_RIGHT_DEFAULT
                        )
    self._prompt = WindowPromptBar(self)

    self.running = True

    self.register_window_geometry()

    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.use_default_colors()

    # .1s timeout on potentially blocking funs
    self.stdscr.timeout(100) 

    # Let curses interpret multibyte keyboard sequences for us
    self.stdscr.keypad(1)

    # Now start the UI monitoring thread
    event_dispatch = EventDispatch()
    self._app_event_dispatch = event_dispatch

  def ui_status_data(self,s):
    self._status_bar.string_left(s)

  def ui_poll(self):
    return self._prompt.ui_poll()

  def ui_terminal_data(self,s):
    self._terminal.ui_terminal_data(s)

  def terminate(self):
    self.stdscr.keypad(0)
    curses.nocbreak()
    curses.echo()
    curses.endwin()
    self.running = False


##################################################
### Event Handler
##################################################

@plugin_app
class BoopAppPlugin(PluginEventsApp):
  name = 'boop-terminal'

  def init(self,gui_class=BoopWindow,gui_class_arguments=None,*args,**kwargs):
    super(BoopAppPlugin,self).init(*args,**kwargs)
    if not gui_class_arguments:
      gui_class_arguments = []
    gui = gui_class(*gui_class_arguments)
    self._gui = gui

  def terminate(self):
    self._gui.terminate()

  @plugin_commandset
  class BoopAppDebugCommands(PluginCommandSet):
    """
    Debugging and underlying structure inspection
    """
    name = "debug"

    @command
    def handle_dump(self,attrs,parent):
      """
      Usage:
        debug dump 
      """
      return parent.events.debug_tree()

  @plugin_commandset
  class BoopAppSerialCommands(PluginCommandSet):
    """
    Manage serial port connections
    """
    name = "serial"

    @command
    def handle_connect(self,attrs,parent):
      """
      Usage:
        serial connect <serial_port>
      """
      return "executed"

  @plugin_runnable
  class BoopCore(PluginEventRunnable):
    name = 'boop-core-runnable'

    @event_thread
    class BoopCoreThread(EventThread):
      name = 'boop-core-thread'

      @consume.BOOP_COMMAND
      def command_handle(self,event):
        self.emit.UI_TERMINAL_DATA("> "+event.data+"\n")
        try:
          s = self.parent.app.execute(event.data)
          self.emit.UI_STATUS_DATA('Ready')
          if s: self.emit.UI_TERMINAL_DATA(s+"\n")
        except ValueError as ex:
          self.emit.UI_TERMINAL_DATA("PARSE ERROR"+str(ex)+"\n")
          
  @plugin_runnable
  class BoopUIRunnable(PluginEventRunnable):
    name = 'boop-ui-runnable'

    @event_thread
    class BoopUIInputThread(EventThread):
      name = 'boop-ui-input-thread'

      def input_poll(self):
        return self.parent.plugin._gui.ui_poll()

      def poll(self):
        command = self.input_poll()
        if command:
          self.emit.BOOP_COMMAND(command)
        
    @event_thread
    class BoopUIOutputThread(EventThread):
      name = 'boop-ui-output-thread'

      @consume.UI_STATUS_DATA
      def ui_status_data(self,event):
        self.parent.plugin._gui.ui_status_data(event.data)

      @consume.UI_TERMINAL_DATA
      def ui_terminal_data(self,event):
        self.parent.plugin._gui.ui_terminal_data(
          textwrap.dedent(event.data)
        )
        self.emit.UI_REFRESH()

      @consume.UI_TERMINAL_REFRESH
      def ui_terminal_refresh(self,event):
        self.parent.plugin._gui.terminal_refresh()

      @consume.UI_STATUS_BAR_REFRESH
      def ui_status_bar_refresh(self,event):
        self.parent.plugin._gui.status_bar_refresh()

      @consume.UI_PROMPT_REFRESH
      def ui_prompt_refresh(self,event):
        self.parent.plugin._gui.prompt_refresh()

      @consume.UI_REFRESH
      def ui_prompt_refresh(self,event):
        self.parent.plugin._gui.refresh()


##################################################
### Event Handler App
##################################################

class BoopApp(EventsApp):
  def init(self,*args,**kwargs):
    self.plugins_to_start.append(PluginHelpApp)
    self.plugins_to_start.append(BoopAppPlugin)

class App(object):

  def __init__(self):
    app = BoopApp()
    self._app = app
    app.start()

  def run(self):
    while 1: 
      time.sleep(0.1)

  def terminate(self):
    self._app.terminate()

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.terminate()


with App() as app:
  try:
    app.run()
  except KeyboardInterrupt:
    app.terminate()
