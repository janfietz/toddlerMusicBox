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
import json
from tmb_module_mpc import MPCModule
from tmb_module_led import LedModule
from tmb_module_input import InputModule
from tmb_module_nfc import NFCModule


# ------------------------------
# global configuration
# ------------------------------
# Where conf files lie. Order IS important.
defaults = """
[mpc]
enable=true
mpd_host=localhost
mpd_port=6600
mixer_control=SPEAKER
mixer_id=0
mixer_cardidx=1
[led]
enable=true
count=5
pin=18
frequenz=800000
dma=6
invert=False
[led_0]
name=vol_up
[led_1]
name=next
[led_2]
name=play
[led_3]
name=previous
[led_4]
name=vol_down
[input]
enable=true
count=5
bounce=20
[input_1]
channel=33
action=play
[input_2]
channel=31
action=next
[input_3]
channel=36
action=previous
[input_4]
channel=37
action=vol_down
[input_5]
channel=29
action=vol_up
[nfc]
enable=true
[colortheme_default]
colors={
	"play": "0x51BD1F",
	"pause": "0xFF6D00",
	"stop": "0xE4242E",
	"emptyplaylist": "0x290002",
	"next": "0xFFD600",
	"next_inactive": "0x3E3400",
	"prev": "0xFFD600",
	"prev_inactive": "0x3E3400",
	"vol_up_100": "0x46084E",
	"vol_up_90": "0x46084E",
	"vol_up_80": "0x46084E",
	"vol_up_70": "0x46084E",
	"vol_up_60": "0x46084E",
	"vol_up_50": "0x46084E",
	"vol_up_40": "0x46084E",
	"vol_up_30": "0x46084E",
	"vol_up_20": "0x46084E",
	"vol_up_10": "0x46084E",
	"vol_up_00": "0x46084E",
	"vol_down_100": "0x46084E",
	"vol_down_90": "0x46084E",
	"vol_down_80": "0x46084E",
	"vol_down_70": "0x46084E",
	"vol_down_60": "0x46084E",
	"vol_down_50": "0x46084E",
	"vol_down_40": "0x46084E",
	"vol_down_30": "0x46084E",
	"vol_down_20": "0x46084E",
	"vol_down_10": "0x46084E",
	"vol_down_00": "0x46084E" 
	}
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
	
	defaultcolors = {
				'play': 0x0000FF,
				'pause': 0x0000FF,
				'stop':  0x0000FF,
				'emptyplaylist':  0x0000FF,
				'next':  0x0000FF,
				'next_inactive':  0x0000FF,
				'previous':  0x0000FF,
				'previous_inactive':  0x0000FF,
				'vol_up_100':  0x0000FF,
				'vol_up_90':  0x0000FF,
				'vol_up_80':  0x0000FF,
				'vol_up_70':  0x0000FF,
				'vol_up_60':  0x0000FF,
				'vol_up_50':  0x0000FF,
				'vol_up_40':  0x0000FF,
				'vol_up_30':  0x0000FF,
				'vol_up_20':  0x0000FF,
				'vol_up_10':  0x0000FF,
				'vol_up_00':  0x0000FF,
				'vol_down_100':  0x0000FF,
				'vol_down_90':  0x0000FF,
				'vol_down_80':  0x0000FF,
				'vol_down_70':  0x0000FF,
				'vol_down_60':  0x0000FF,
				'vol_down_50':  0x0000FF,
				'vol_down_40':  0x0000FF,
				'vol_down_30':  0x0000FF,
				'vol_down_20':  0x0000FF,
				'vol_down_10':  0x0000FF,
				'vol_down_00':  0x0000FF,
				}
	
	def __init__(self):
		self.loop = False
		self.modules = []

		self._mpdstatus = {}
		self._playList = []

	def __enter__(self):

		'''Create Modules'''
		if conf.getboolean('mpc', 'enable'):
			self.mpc = MPCModule(conf)
			self.modules.append(self.mpc)

		'''load default color theme'''
		#try:
		colorThemeDef = conf.get('colortheme_default', 'colors')
		self._colorTheme = json.loads(colorThemeDef)
		#except:
		#	self._colorTheme = ToddlerMusicBox.defaultcolors

		if conf.getboolean('led', 'enable'):
			self.led = LedModule(conf)
			self.modules.append(self.led)
	
		if conf.getboolean('input', 'enable'):
			self.input = InputModule(conf)
			self.modules.append(self.input)

		if conf.getboolean('nfc', 'enable'):
			self.nfc = NFCModule(conf)
			self.modules.append(self.nfc)
		
		return self

	def __exit__(self, type, value, traceback):
		self.loop = False
		
	def _queryColor(self, colorname):
		if colorname in self._colorTheme.keys():
			return int(self._colorTheme[colorname], 16)
		return 0x0000FF

	def _updateState(self):
		if 'state' in self._mpdstatus.keys():
			if self._mpdstatus['state'] == 'play':
				self.led.setFadeLedColor('play', self._queryColor('play'))
			if self._mpdstatus['state'] == 'stop':
				if len(self._playList) == 0:
					self.led.setFadeLedColor('play', self._queryColor('emptyplaylist'))
				else:
					self.led.setFadeLedColor('play', self._queryColor('stop'))
			if self._mpdstatus['state'] == 'pause':
				self.led.setFadeLedColor('play', self._queryColor('pause'))

			''' update volume '''
		self.led.setFadeLedColor('vol_up', self._queryColor('vol_up_100'))
		self.led.setFadeLedColor('vol_down', self._queryColor('vol_down_100'))

		if 'next' in self._mpdstatus.keys():
			self.led.setFadeLedColor('next', self._queryColor('next'))
		else:
			if 'repeat' in self._mpdstatus.keys():
				if self._mpdstatus['repeat']:
					self.led.setFadeLedColor('next', self._queryColor('next'))
				else:
					self.led.setFadeLedColor('next', self._queryColor('next_inactive'))
		
		self.led.setFadeLedColor('previous', self._queryColor('previous'))


	def _on_player(self, args):
		logging.info('Status: %s', args['status']['state'])
		if 'state' in self._mpdstatus.keys():
			playerStateChanged = self._mpdstatus['state'] != args['status']['state']
		else:
			playerStateChanged = True
		self._mpdstatus = args['status']
		if len(args['current']):
			logging.info('Current Song: %s - %s', args['current']['artist'] , args['current']['title'])

		if playerStateChanged:
			self._updateState()

	def _on_playlist(self, args):
		logging.info('Playlist: %i', len(args['playlist']))
		self._playList = args['playlist']
		self._updateState()
	
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

	def _on_nfc(self, args):
		if len(args['uid']) > 0:
			lsResult = self.mpc.ls()
			if lsResult:
				for entry in lsResult:
					if 'directory' in entry.keys():
						if entry['directory'] == args['uid']:
							self.mpc.clear()
							self.mpc.add(entry['directory'])
							self.mpc.play()
		else:
			self.mpc.clear()
							

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
