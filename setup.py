#!/usr/bin/env python

import sys
from setuptools import setup

if sys.version_info < (2, 4):
  sys.stderr.write('Requires >Python 2.4\n')
  sys.exit(1)

setup(
    name='Boop',
    version='0.1',
    description='Trivial Event Handling Toy',
    author='Aki Mimoto',
    author_email='amimoto@gmail.com',
    license='MIT License',
    platforms='Linux',
    url='https://github.com/amimoto/boop',
    packages=[
                'boop',
                'boop.app',
                'boop.command',
                'boop.devices',
                'boop.devices.zaber',
                'boop.devices.zaber.ascii',
                'boop.event',
                'boop.event.ports',
                'boop.thirdparty',
                'boop.thirdparty.serial',
                'boop.thirdparty.serial.tools',
                ],
    test_suite='tests'
    )

