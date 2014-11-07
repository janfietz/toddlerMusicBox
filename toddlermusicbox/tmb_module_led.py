'''
Created on Oct 18, 2014

@author: jan
'''
import time, threading
import tmb_module, tmb_main
import logging
import collections
import Queue

use_ledmodule = True
try:
    from neopixel import *
except ImportError:
    logging.exception("Error importing neopixel!")
    use_ledmodule = False
    


class LedThread(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self, strip):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        
        self._loop = True
        self._strip = strip

        self.tasks = Queue.Queue()

    @property
    def loop(self):
        return self._loop
    
    @loop.setter
    def loop(self, value):
        self._loop = value

    def addTask(self, task):
        self.tasks.put_no_wait(task)

    def _process(self, task):
        exec('self._strip.' + task.popleft())

    def run(self):
    
        self.loop = True
        while self.loop:
            try:
                task = self.tasks.get(block = True, timeout = 1)
                self._process(task)
            except Queue.Empty:
                pass 
                

class LedModule(tmb_module.TMB_Module):
    
    def __init__(self, config):
        '''
        Constructor
        '''
        tmb_module.TMB_Module.__init__(self, config)
        
        self._count = config.getint('led', 'count')
        self._pin = config.getint('led', 'pin')
        self._frequenz = config.getint('led', 'frequenz')
        self._dma = config.getint('led', 'dma')
        self._invert = config.getboolean('led', 'invert')
        self._strip = None
                
    def start(self):
        tmb_module.TMB_Module.start(self)
        
        if not use_ledmodule:
            return
        self._strip = Adafruit_NeoPixel(self._count, self._pin, self._frequenz, self._dma, self._invert)
        self._strip.begin()

        ''' initialize led '''
        self._strip.setBrightness(200)
        for i in range(self._count):
            self._strip.setPixelColor(i, Color(0,0,255))
        self._strip.show()

        self._thread = LedThread(self._strip)
        
        self._thread.start()
        
    def stop(self):
        if use_ledmodule:
            self._thread.loop = False
            self._thread.join()
        
        tmb_module.TMB_Module.stop(self)

    def setBrightness(self, brightness):
        if use_ledmodule:
            self.thread.setBrightness('setBrightness({})'.format(brightness))

    def setLedColor(self, n, color):
        if use_ledmodule:
            self.thread.setBrightness('setPixelColor({}, {})'.format(n, color))

    def show(self):
        if use_ledmodule:
            self.thread.setBrightness('show()')

        
         