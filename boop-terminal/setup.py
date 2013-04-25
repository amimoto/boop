#!/usr/bin/env python

import sys
from setuptools import setup

if sys.version_info < (2, 4):
  sys.stderr.write('Requires >Python 2.4\n')
  sys.exit(1)

setup(
    name='Boop Curses',
    version='0.1',
    description='Add-on for Curses based interactions in trivial event handling toy',
    author='Aki Mimoto',
    author_email='amimoto@gmail.com',
    license='MIT License',
    platforms='Linux',
    url='https://github.com/amimoto/boop',
    packages=[
                ],
    test_suite='tests'
    )


