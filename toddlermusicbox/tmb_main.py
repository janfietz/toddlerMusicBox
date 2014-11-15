# -*- coding: utf-8 -*-
#
# toddlermusicbox
#
# Copyright (C) 2014 Jan Fietz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import locale
import os, io
import re
import select, sys
import argparse
import time, threading
import collections
import logging
import signal
import ConfigParser
from tmb_module_mpc import MPCModule
from tmb_module_led import LedModule
from tmb_module_input import InputModule


# ------------------------------
# global configuration
# ------------------------------
# Where conf files lie. Order IS important.
defaults = """
[mpc]
enable=true
mpd_host=localhost
mpd_port=6600
[led]
enable=true
count=2
pin=18
frequenz=800000
dma=6
invert=False
[led_0]
name=play
[led_1]
name=next
[led_2]
name=previous
[led_3]
name=vol_up
[led_4]
name=vol_down
[input]
enable=true
count=5
bounce=20
[input_1]
channel=11
action=play
[input_2]
channel=15
action=next
[input_3]
channel=13
action=previous
[input_4]
channel=16
action=vol_down
[input_5]
channel=18
action=vol_up
"""
	
conf_files = [os.path.expanduser('~/.tmb/tmb.conf'), '/etc/tmb.conf']
# global conf
conf = ConfigParser.RawConfigParser(allow_no_value=True)
def read_conf():
	'''Read default values.'''
	conf.readfp(io.BytesIO(defaults))
	'''Read global configurations from file.'''
	conf.read(conf_files)
	

class ToddlerMusicBox():
	'''Main class'''

	eventQueue = collections.deque()
	
	def __init__(self):
		self.loop = False
		self.modules = []

		self._playerstate = 'none'

	def __enter__(self):

		'''Create Modules'''
		if conf.getboolean('mpc', 'enable'):
			self.mpc = MPCModule(conf)
			self.modules.append(self.mpc)

		if conf.getboolean('led', 'enable'):
			self.led = LedModule(conf)
			self.modules.append(self.led)
	
		if conf.getboolean('input', 'enable'):
			self.input = InputModule(conf)
			self.modules.append(self.input)
		return self

	def __exit__(self, type, value, traceback):
		self.loop = False

	def _on_player(self, args):
		logging.info('Status: %s', args['status']['state'])
		playerStateChanged = self._playerstate != args['status']['state']
		self._playerstate = args['status']['state']
		if len(args['current']):
			logging.info('Current Song: %s - %s', args['current']['artist'] , args['current']['title'])

		if playerStateChanged and self._playerstate == 'play':
			self.led.setFadeLedColorRGB('play', 0, 255, 0)
		if playerStateChanged and self._playerstate == 'stop':
			self.led.setFadeLedColorRGB('play', 255, 0, 0)
		if playerStateChanged and self._playerstate == 'pause':
			self.led.setFadeLedColorRGB('play', 0, 0, 255)
	
	def _on_input(self, args):
		logging.info('action: %s %s', args['action'], args['state'])
		if args['action'] == 'play':
			if args['state'] == 'unpressed':
				self.mpc.toggle()
				
		if args['action'] == 'next':
			if args['state'] == 'unpressed':
				self.mpc.next()

		if args['action'] == 'previous':
			if args['state'] == 'unpressed':

				self.mpc.previous()

		if args['action'] == 'vol_up':
			if args['state'] == 'pressed':
				self.mpc.volume(5)
				
		if args['action'] == 'vol_down':
			if args['state'] == 'pressed':
				self.mpc.volume(-10)
		
	def _processEvent(self, event):
		try:
			getattr(self, "_on_%s" % event['type'])(event['args'])
		except AttributeError as e:
			logging.error(e)
    
	def main_loop(self):

		self.loop = True

		logging.debug("Start modules")
		for module in self.modules:
			logging.debug('Start %s', type(module).__name__)
			module.start()
		
		try:
			while self.loop:
				try:
					processQueue = True
					while processQueue:
						self._processEvent(ToddlerMusicBox.eventQueue.popleft())
				except IndexError:
					pass

				for module in self.modules:
					module.update()
			
				time.sleep(0.1)
		except KeyboardInterrupt:
			self.loop = False

		logging.debug("Stop modules")
		for module in reversed(self.modules):
			module.stop()
			logging.debug('Stopped %s', type(module).__name__)

	def main(self, argv):
		loglevel = 'WARNING'
		
		parser = argparse.ArgumentParser(description='toddlerMusicBox options')
		parser.add_argument('--loglevel', default='WARNING', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
						help='Set process verbosity')
		parser.add_argument('--version', action='version', version='%(prog)s 0.1')
		args = parser.parse_args()

		numeric_level = getattr(logging, args.loglevel.upper(), None)
		if not isinstance(numeric_level, int):
			raise ValueError('Invalid log level: %s' % loglevel)
		logging.basicConfig(format='%(message)s', level=numeric_level)

		self.main_loop()
