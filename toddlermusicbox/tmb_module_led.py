'''
Created on Oct 18, 2014

@author: jan
'''
import time, threading
import tmb_module, tmb_main
import logging
import collections

        
class LedThread(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self, mpc, host, port):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        
        self._loop = True

        self.tasks = collections.deque()

    @property
    def loop(self):
        return self._loop
    
    @loop.setter
    def loop(self, value):
        self._loop = value

    def addTask(self, task):
        self.tasks.append(task)

class LedModule(tmb_module.TMB_Module):
    
    def __init__(self, config):
        '''
        Constructor
        '''
        tmb_module.TMB_Module.__init__(self, config)
        
        self.count = config.getint('led', 'count')
        self.pin = config.getint('led', 'pin')
        self.frequenz = config.getint('led', 'frequenz')
        self.dma = config.getint('led', 'dma')
        self.invert = config.getbool('led', 'invert')
        
                
    def start(self):
        tmb_module.TMB_Module.start(self)
        self.thread = MPCThread(self.mpc, self.host, self.port)
        
        self.thread.start()
        
    def stop(self):
        print("Stop LedModule")
        self.thread.loop = False
        self.thread.join()
        tmb_module.TMB_Module.stop(self)

        
         