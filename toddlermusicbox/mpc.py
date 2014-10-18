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

    
class MPC(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self, params):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        
        self.host = params['MPD_HOST']
        self.port = params['MPD_PORT']
        self.loop = True
        self.mpc = mpd.MPDClient()
        self.doConnect = True
        
        self.syncMPD = False
        self.idle = False
        
    def connect(self):
        try:
            self.mpc.connect(self.host, self.port)
            self.doConnect = False
            print('MPC: connected')
        except mpd.ConnectionError as e:
            print("ConnectionError:", e)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            self.doConnect = True
        
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

    def updateStatus(self):
        self.status = self.mpc.status()
        self.stats = self.mpc.stats()
        self.currentsong = self.mpc.currentsong()
    
    def process(self, fd):
        '''Process init/timeout/mpd/stdin events. Called in main loop.'''

        if fd == 'init' or fd == 'mpd':
            self.syncMPD = True

        if self.syncMPD:
            events = self.try_leave_idle()

            self.updateStatus()

            if events and 'player' in events:
                print('Status: ', self.status['state'])
                print('Current: ', self.currentsong)

        self.try_enter_idle()
        
    def run(self):
        
        self.loop = True
        while self.loop:
            
            if self.doConnect:
                self.connect()
                time.sleep(1)
            else:
                try:
                    poll = select.poll()
                    poll.register(self.mpc.fileno(), select.POLLIN)
                    poll.register(0, select.POLLIN)
                    while self.loop:
                        responses = poll.poll(200)
                        if not responses:
                            self.process(fd='timeout')
                        else:
                            for fd, event in responses:
                                if fd == self.mpc.fileno() and event & select.POLLIN:
                                    self.process(fd='mpd')
                except mpd.ConnectionError:
                    print('MPC: Connection lost')
                    self.mpc.disconnect()
                    self.doConnect = True 
           
        