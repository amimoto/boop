#!/bin/bash

socat PTY,link=`pwd`/ttyVirtualS0,echo=0 PTY,link=`pwd`/ttyVirtualS1,echo=0
