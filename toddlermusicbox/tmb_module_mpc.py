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
    @property
    def loop(self):
        return self._loop
    
    @loop.setter
    def loop(self, value):
        self._loop = value
        
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
        '''Process init/timeout/mpd/stdin events. Called in main loop.'''

        if fd == 'init' or fd == 'mpd':
            self._syncMPD = True

        if self._syncMPD:
            events = self._try_leave_idle()

            self._updateStatus()

            for event in events:
                tmb_main.ToddlerMusicBox.eventQueue.append(dict(sender = self, type = 'player', args = dict(status = self.status, current = self.currentsong)))

        self._try_enter_idle()
        
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
    
    def __init__(self, params):
        '''
        Constructor
        '''
        tmb_module.TMB_Module.__init__(self, params)
        
        self.host = params['MPC_MPD_HOST']
        self.port = params['MPC_MPD_PORT']
        
                
    def start(self):
        tmb_module.TMB_Module.start(self)
        
        self.mpc = mpd.MPDClient()
        self.thread = MPCThread(self.mpc, self.host, self.port)
        
        self.thread.start()
        
    def stop(self):
        self.thread.loop = False
        self.thread.join()
        tmb_module.TMB_Module.stop(self)
        
         