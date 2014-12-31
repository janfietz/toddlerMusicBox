'''
Created on Oct 18, 2014

@author: jan
'''
import time, threading
import tmb_module, tmb_main
import logging
import collections
import Queue

use_nxpmodule = True
try:
    from nxppy import Mifare, SelectError
except ImportError:
    logging.exception("Error importing nxppy!")
    use_nxpmodule = False

class NFCThread(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        
        self._loop = True
        self._uid = None
        self._resetCnt = 0

        self.tasks = Queue.Queue()

    @property
    def loop(self):
        return self._loop
    
    @loop.setter
    def loop(self, value):
        self._loop = value

    def addTask(self, task):
        self.tasks.put_nowait(task)

    def _process(self, task):
        pass

    def _sendEvent(self):
        tmb_main.ToddlerMusicBox.eventQueue.append(dict(sender = self, type = 'nfc', args = dict(uid = self._uid)))

    def _updateId(self, mifare):
        
        uid = self._uid
        try:
            uid = mifare.select()
        except SelectError:
            uid = ''
        
        if uid == None:
            uid = ''
        if uid == '':
            self._resetCnt += 1
        else:
            self._resetCnt = 5
        if (uid != self._uid) and (self._resetCnt == 5):
            logging.debug('NFC: uid %s', uid)
            self._uid = uid
            self._sendEvent()
        if self._resetCnt == 5:
            self._resetCnt = 0

    def run(self):
        mifare = Mifare()

        self.loop = True
        while self.loop:
            
            try:
                while self.loop:
                    task = self.tasks.get_nowait()
                    self._process(task)

            except Queue.Empty:
                pass                
            self._updateId(mifare)

            time.sleep(1/10.0)

class NFCModule(tmb_module.TMB_Module):
    
    def __init__(self, config):
        '''
        Constructor
        '''
        tmb_module.TMB_Module.__init__(self, config)
                
    def start(self):
        tmb_module.TMB_Module.start(self)
        
        if not use_nxpmodule:
            return

        self._thread = NFCThread()

        self._thread.start()
        
    def stop(self):
        if use_nxpmodule:
            self._thread.loop = False
            self._thread.join()
        
        tmb_module.TMB_Module.stop(self)

    def update(self):
        tmb_module.TMB_Module.update(self)
