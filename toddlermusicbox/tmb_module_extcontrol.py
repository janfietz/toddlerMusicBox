'''
Created on Nov 10, 2015

@author: jan
'''
import time, threading
import tmb_module, tmb_main
import logging
import collections
import Queue
import serial

class EXTThread(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self, device):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)

        self._loop = True
        self._uid = None

        self._device = device
        self._serialDevice = None

        self.tasks = Queue.Queue()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value):
        self._loop = value

    def addTask(self, task):
        self.tasks.put_nowait(task)

    def nextEffect(self):
        logging.debug('EXT: next effect')
        if self._getPrompt():
            self._serialDevice.write('nexteffect\n\r')
            data = self._serialDevice.read(9)

    def noEffect(self):
        logging.debug('EXT: disable effect')


    def setPlayMode(self, mode):
        logging.debug('EXT: set play mode %d', mode)
        if self._getPrompt():
            self._serialDevice.write('playmode {}\n\r'.format(mode))
            data = self._serialDevice.read(10)

    def setVolume(self, volume):
        logging.debug('EXT: set volume %d', volume)

    def _process(self, task):
        if task['target'] == 'self':
            func = getattr(self, task['function'])
            func(*task['arguments'])

    def _sendEvent(self):
        tmb_main.ToddlerMusicBox.eventQueue.append(dict(sender = self, type = 'nfc', args = dict(uid = self._uid)))

    def _getPrompt(self):
        if self._serialDevice:
            self._serialDevice.write('\r\n')

            data = self._serialDevice.read(10)
            if "ch>" in data:
                return True
            logging.debug('EXT: promp answer %s', data)
        return False
    def _updateId(self):

        uid = self._uid

        if self._getPrompt():
            self._serialDevice.write('uid\n\r')
            data = self._serialDevice.read(22)
            #logging.debug('EXT: uid answer %s', data)

        if uid == None:
            uid = ''

        if uid != self._uid:
            logging.debug('NFC: uid %s', uid)
            self._uid = uid
            self._sendEvent()



    def run(self):

        self.loop = True

        openPort = False
        while self.loop:
            try:
                if openPort == False:
                    self._serialDevice = serial.Serial(self._device, 38400, timeout = 0.1)
                    logging.debug('EXT: opened device: %s', self._device)
                    openPort = True
            except serial.SerialException:
                self._serialDevice = None

            try:
                while self.loop:
                    task = self.tasks.get_nowait()
                    self._process(task)

            except Queue.Empty:
                pass
            self._updateId()

            time.sleep(1/10.0)

class EXTModule(tmb_module.TMB_Module):

    PLAY = 0
    PAUSE = 1
    STOP = 2
    NOSELECTED = 3

    def __init__(self, config):
        '''
        Constructor
        '''

        self._device = config.get('ext', 'device')

        tmb_module.TMB_Module.__init__(self, config)

    def start(self):
        tmb_module.TMB_Module.start(self)


        self._thread = EXTThread(self._device)

        self._thread.start()

    def stop(self):
        self._thread.loop = False
        self._thread.join()

        tmb_module.TMB_Module.stop(self)

    def update(self):
        tmb_module.TMB_Module.update(self)

    def nextEffect(self):
        self._thread.addTask(dict(
                                target = 'self',
                                function = 'nextEffect',
                                arguments = []
                                ))

    def noEffect(self):
        self._thread.addTask(dict(
                                target = 'self',
                                function = 'nextEffect',
                                arguments = []
                                ))

    def setPlayMode(self, mode):
        self._thread.addTask(dict(
                                target = 'self',
                                function = 'setPlayMode',
                                arguments = [mode]
                                ))
    def setVolume(self, volume):
        self._thread.addTask(dict(
                                target = 'self',
                                function = 'setVolume',
                                arguments = [volume]
                                ))
