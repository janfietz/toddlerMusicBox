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
import select, sys
import time, threading
from tmb_module_mpc import MPCModule
import collections

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
		print("Status: ", args['status']['state'])
		if len(args['current']):
			print("Current Song: ", args['current']['artist'] , "-", args['current']['title'])
		
	def _processEvent(self, event):
		try:
			getattr(self, "_on_%s" % event['type'])(event['args'])
		except AttributeError as e:
			print(e)
		

	def main_loop(self):

		self.loop = True

		for module in self.modules:
			module.start()
		
		while self.loop:
			try:
				processQueue = True
				while processQueue:
					self._processEvent(ToddlerMusicBox.eventQueue.popleft())

				for module in modules:
					module.update()

			except IndexError:
				pass
			time.sleep(0.1)

		for module in modules:
			module.stop()
				
