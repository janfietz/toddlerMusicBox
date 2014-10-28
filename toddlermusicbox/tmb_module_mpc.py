'''
Created on Oct 18, 2014

@author: jan
'''
import locale
import mpd
import os
import re
import select, sys
import time, threading
import tmb_module, tmb_main
import logging
import collections

        
class MPCThread(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self, mpc, host, port):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        
        self._host = host
        self._port = port
        self._mpc = mpc
        
        self._doConnect = True
        self._loop = True
        self._syncMPD = False
        self._idle = False

        self.tasks = collections.deque()

    @property
    def loop(self):
        return self._loop
    
    @loop.setter
    def loop(self, value):
        self._loop = value

    def addTask(self, task):
        self.tasks.append(task)
       
    def _connect(self):
        try:
            self._mpc.connect(self._host, self._port)
            self._doConnect = False
            self._updateStatus()
            tmb_main.ToddlerMusicBox.eventQueue.append(dict(sender = self, type = 'player', args = dict(status = self.status, current = self.currentsong)))
            logging.info('MPC: connected')
        except mpd.ConnectionError as e:
            logging.warning('ConnectionError: %s', e)
        except:
            logging.debug('Unexpected error: %s', sys.exc_info()[0])
            self._doConnect = True
        
    def _enter_idle(self):
        '''Enter idle state. Must be called outside idle state.

        No return value.'''
        self._mpc.send_idle()
        self._idle = True

    def _leave_idle(self):
        '''Leave idle state. Must be called inside idle state.
        Return Value: Events received in idle state.'''
        self._mpc.send_noidle()
        self._idle = False
        try:
            return self._mpc.fetch_idle()
        except mpd.PendingCommandError:
            # return None if nothing received
            return None

    def _try_enter_idle(self):
        if not self._idle:
            self._enter_idle()
    
    def _try_leave_idle(self):
        if self._idle:
            return self._leave_idle()

    def _updateStatus(self):
        self.status = self._mpc.status()
        self.stats = self._mpc.stats()
        self.currentsong = self._mpc.currentsong()
    
    def _process(self, fd):
        '''Process init/timeout/mpd events. Called in main loop.'''

        self._syncMPD = True
        notify = False
        if self._syncMPD:
            events = self._try_leave_idle()
            if events:
                notify = True

            if self.tasks:
                notify = True
                self._mpc.command_list_ok_begin()
                try:
                    processQueue = True
                    while processQueue:
                        exec('self._mpc.' + task.popleft())
                except IndexError:
                    pass
                self._mpc.command_list_end()

            self._updateStatus()

        
        self._syncMPD = False
        self._try_enter_idle()
        
        if notify:
            tmb_main.ToddlerMusicBox.eventQueue.append(dict(sender = self, type = 'player', args = dict(status = self.status, current = self.currentsong)))

    def run(self):
        
        self.loop = True
        while self.loop:
            
            if self._doConnect:
                self._connect()
                time.sleep(1)
            else:
                try:
                    poll = select.poll()
                    poll.register(self._mpc.fileno(), select.POLLIN)
                    while self._loop:
                        responses = poll.poll(200)
                        if not responses:
                            self._process(fd='timeout')
                        else:
                            for fd, event in responses:
                                if fd == self._mpc.fileno() and event & select.POLLIN:
                                    self._process(fd='mpd')
                except mpd.ConnectionError:
                    logging.info('MPC: disconnected')
                    self._mpc.disconnect()
                    self._doConnect = True 
           
class MPCModule(tmb_module.TMB_Module):
    
    def __init__(self, config):
        '''
        Constructor
        '''
        tmb_module.TMB_Module.__init__(self, config)
        
        self.host = config.get('mpc', 'mpd_host')
        self.port = config.getint('mpc', 'mpd_port')
        
                
    def start(self):
        tmb_module.TMB_Module.start(self)
        
        self.mpc = mpd.MPDClient()
        self.thread = MPCThread(self.mpc, self.host, self.port)
        
        self.thread.start()
        
    def stop(self):
        print("Stop MPCModule")
        self.thread.loop = False
        self.thread.join()
        tmb_module.TMB_Module.stop(self)

    def play(self):
        self.thread.addTask('play()')

    def toggle(self):
        self.thread.addTask('pause()')

    def next(self):
        self.thread.addTask('next()')
    def previous(self):
        self.thread.addTask('previous()')

    def ls(self):
        pass
    def add(self, album):
        self.thread.addTask('add({})'.format(album))
    def clear(self):
        self.thread.addTask('clear()')

        
         