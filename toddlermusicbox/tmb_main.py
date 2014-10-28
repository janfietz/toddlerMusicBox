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
import os
import re
import select, sys, getopt
import time, threading
from tmb_module_mpc import MPCModule
import collections
import logging
import signal


# ------------------------------
# global configuration
# ------------------------------
# Where conf files lie. Order IS important.
conf_files = [os.path.expanduser('~/.tmb/tmb.conf'), '/etc/tmb.conf']
# global conf
conf = {}
def read_conf():
	'''Read global configurations from file.'''
	
	conf['MPC_MPD_HOST'] = 'localhost'
	conf['MPC_MPD_PORT'] = 6600
	
	for cf in conf_files:
		if not os.path.isfile(cf):
			continue
		with open(cf, 'rt') as f:
			l_cnt = 0
			for l in f:
				l_cnt += 1
				if l.startswith('#'):
					continue
				m = re.match(r'(\S+)\s+(\S+)', l)
				if not m:
					continue
				g = m.groups()
				if g[0] == 'MPC_MPD_HOST':
					conf[g[0]] = g[1]
				elif g[0] == 'MPC_MPD_PORT':
					conf[g[0]] = int(g[1])
				else:
					raise Exception('Unknows option {} in conf file {}, line {}'.format(g[0], cf, l_cnt))
		break

class ToddlerMusicBox():
	'''Main class'''

	eventQueue = collections.deque()
	
	def __init__(self):
		self.loop = False
		self.modules = []
		

	def __enter__(self):

		'''Create Modules'''
		self.modules.append(MPCModule(conf))

		return self

	def __exit__(self, type, value, traceback):
		self.loop = False

	def _on_player(self, args):
		logging.info('Status: %s', args['status']['state'])
		if len(args['current']):
			logging.info('Current Song: %s - %s', args['current']['artist'] , args['current']['title'])
		
	def _processEvent(self, event):
		try:
			getattr(self, "_on_%s" % event['type'])(event['args'])
		except AttributeError as e:
			print(e)
		
    
	def main_loop(self):

		self.loop = True

		logging.debug("Start modules")
		for module in self.modules:
			module.start()
		
		try:
			while self.loop:
				try:
					processQueue = True
					while processQueue:
						self._processEvent(ToddlerMusicBox.eventQueue.popleft())
				except IndexError:
					pass
				time.sleep(0.1)
		except KeyboardInterrupt:
			self.loop = False

		logging.debug("Stop modules")
		for module in reversed(self.modules):
			module.stop()

	def main(self, argv):
		loglevel = 'WARNING'
		try:
			opts, args = getopt.getopt(argv,"hi:o:",["loglevel="])
		except getopt.GetoptError:
			print 'toddlermusicbox --loglevel <level>'
			sys.exit(2)
		for opt, arg in opts:
			if opt == '-h':
		 		print 'toddlermusicbox --loglevel <DEBUG|INFO|WARNING|ERROR>'
		 		sys.exit()
			elif opt in ("--loglevel"):
		 		loglevel = arg

		numeric_level = getattr(logging, loglevel.upper(), None)
		if not isinstance(numeric_level, int):
			raise ValueError('Invalid log level: %s' % loglevel)
		logging.basicConfig(format='%(message)s', level=numeric_level)

		self.main_loop()
