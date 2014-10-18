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
import mpd
import os
import re
import select, sys
import time, threading

# ------------------------------
# global configuration
# ------------------------------
# Where conf files lie. Order IS important.
conf_files = [os.path.expanduser('~/.tmb/tmb.conf'), '/etc/tmb.conf']
# global conf
conf = {}
def read_conf():
	'''Read global configurations from file.'''
	
	conf['MPD_HOST'] = 'localhost'
	conf['MPD_PORT'] = 6600
	
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
				if g[0] == 'MPD_HOST':
					conf[g[0]] = g[1]
				elif g[0] == 'MPD_PORT':
					conf[g[0]] = int(g[1])
				else:
					raise Exception('Unknows option {} in conf file {}, line {}'.format(g[0], cf, l_cnt))
		break

class ToddlerMusicBox():
	'''Main class'''

	def __init__(self):
		self.loop = False
		self.syncMPD = False
		self.idle = False

	def _init_mpd(self, host, port):
		self.mpc = mpd.MPDClient()
		self.mpc.connect(host, port)

	def __enter__(self):
		self._init_mpd(conf['MPD_HOST'], conf['MPD_PORT'])
		self.updateMpcStatus()

		return self

	def __exit__(self, type, value, traceback):
		self.loop = False

	def enter_idle(self):
		'''Enter idle state. Must be called outside idle state.

		No return value.'''
		self.mpc.send_idle()
		self.idle = True

	def leave_idle(self):
		'''Leave idle state. Must be called inside idle state.
		Return Value: Events received in idle state.'''
		self.mpc.send_noidle()
		self.idle = False
		try:
			return self.mpc.fetch_idle()
		except mpd.PendingCommandError:
			# return None if nothing received
			return None

	def try_enter_idle(self):
		if not self.idle:
			self.enter_idle()
	
	def try_leave_idle(self):
		if self.idle:
			return self.leave_idle()

	def updateMpcStatus(self):
		self.status = self.mpc.status()
		self.stats = self.mpc.stats()
		self.currentsong = self.mpc.currentsong()

	def update(self):
		self.updateMpcStatus()

	def process(self, fd):
		'''Process init/timeout/mpd/stdin events. Called in main loop.'''

		if fd == 'init' or fd == 'mpd':
			self.syncMPD = True

		if self.syncMPD:
			events = self.try_leave_idle()

			self.update()

			if events and 'player' in events:
				print('Status: ', self.status['state'])
				print('Current: ', self.currentsong)

		self.try_enter_idle()

	def main_loop(self):

		poll = select.poll()
		poll.register(self.mpc.fileno(), select.POLLIN)
		poll.register(0, select.POLLIN)

		self.loop = True
		while self.loop:
			responses = poll.poll(200)
			if not responses:
				self.process(fd='timeout')
			else:
				for fd, event in responses:
					if fd == self.mpc.fileno() and event & select.POLLIN:
						self.process(fd='mpd')
				
