#!/usr/bin/python

"""
Inserts dummy commands into a pipe

Note that pseudo ports have to be created before this works properly:

See:

http://stackoverflow.com/questions/2500420/fake-serial-communication-under-linux

Essentially, run: 

socat PTY,link=`pwd`/ttyVirtualS0,echo=0 PTY,link=`pwd`/ttyVirtualS1,echo=0

"""

import serial
import time
import datetime

ser = serial.Serial('ttyVirtualS0', 9600, timeout=1)

while 1:
  s = "The time is now: "+datetime.datetime.now().isoformat()
  print s
  ser.write(s+"\n")
  time.sleep(0.5)


