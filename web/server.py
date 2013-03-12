#!/usr/bin/python

import os,sys
sys.path.insert(0, '../lib')

import ConfigParser
import pprint
import random
from libs.thirdparty.bottle import route, run, response, request, static_file


# Store current working directory
pwd = os.path.dirname(__file__)
config_fpath = pwd+'/server.cfg'

global config
global monitor

defaults = {'prompt': ''}
config = ConfigParser.ConfigParser(defaults)
config.read(os.path.expanduser(config_fpath))
server_conn_key = "server " + ( 
                      config.get('server','connection')
                  )
config = dict(config.items(server_conn_key))

@route('/')
def home_page():
    global config
    return static_file('index.html', root=config['static_path'])

@route('/ajax/<filepath:path>',['GET','POST'])
def ajax_request(filepath):
    global config
    cmd = request.forms.get('cmd')

    # Get a bead on the serial port
    #s = SerialEventMonitor( 'ttyVirtualS1', 
    #                      9600, 
    #                      timeout=1 )

    return { 
      'status': 'success!',
      'output': cmd,
    }

@route('/<filepath:path>')
def server_static(filepath):
    global config
    return static_file(filepath, root=config['static_path'])

run(host='localhost', port=8081)


