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
        self._resetCnt = 0

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
            self._getPrompt()

    def noEffect(self):
        logging.debug('EXT: disable effect')
        if self._getPrompt():
            self._serialDevice.write('noeffect\n\r')
            data = self._serialDevice.read(8)
            self._getPrompt()

    def hideControls(self):
        logging.debug('EXT: hide controls')
        if self._getPrompt():
            self._serialDevice.write('hidecontrols\n\r')
            data = self._serialDevice.read(13)
            self._getPrompt()

    def showControls(self):
        logging.debug('EXT: show controls')
        if self._getPrompt():
            self._serialDevice.write('showcontrols\n\r')
            data = self._serialDevice.read(13)
            self._getPrompt()

    def setPlayMode(self, mode):
        logging.debug('EXT: set play mode %d', mode)
        if self._getPrompt():
            self._serialDevice.write('playmode {}\n\r'.format(mode))
            data = self._serialDevice.read(10)
            self._getPrompt()

    def setVolume(self, volume):
        logging.debug('EXT: set volume %d', volume)
        if self._getPrompt():
            self._serialDevice.write('volume {}\n\r'.format(volume))
            data = self._serialDevice.read(10)
            self._getPrompt()

    def _process(self, task):
        if task['target'] == 'self':
            func = getattr(self, task['function'])
            func(*task['arguments'])

    def _sendEvent(self):
        tmb_main.ToddlerMusicBox.eventQueue.append(dict(sender = self, type = 'nfc', args = dict(uid = self._uid)))

    def _getPrompt(self):
        if self._serialDevice:
            while True:
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
            data = self._serialDevice.read(3)
            data = self._serialDevice.read(30)
            lines = data.splitlines()
            for line in lines:
                idx = line.find('[')
                if idx >= 0:
                    uid = line[:idx]

        if uid == None:
            uid = ''
        else:
            self._resetCnt = 5

        if uid == '':
            self._resetCnt += 1

        if (uid != self._uid) and (self._resetCnt == 5):
            logging.error('NFC: uid %s', uid)
            self._uid = uid
            self._sendEvent()

        if self._resetCnt == 5:
            self._resetCnt = 0

    def run(self):

        self.loop = True

        openPort = False
        while self.loop:
            try:
                if openPort == False:
                    self._serialDevice = serial.Serial(self._device, 38400, timeout = 0.1)
                    logging.info('EXT: opened device: %s', self._device)
                    openPort = True

                    self.showControls()
            except:
                self._serialDevice = None

            try:
                try:
                    while self.loop:
                        task = self.tasks.get_nowait()
                        self._process(task)
                except Queue.Empty:
                    pass

                self._updateId()
            except serial.SerialException:
                self._serialDevice.close()
                logging.info('EXT: closed device: %s', self._device)
                self._serialDevice = None
                openPort = False

            time.sleep(1/15.0)

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
    def hideControls(self):
        self._thread.addTask(dict(
                            target = 'self',
                            function = 'hideControls',
                            arguments = []
                            ))

    def showControls(self):
        self._thread.addTask(dict(
                            target = 'self',
                            function = 'showControls',
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
