'''
Created on Oct 18, 2014

@author: jan
'''
import time, threading
import tmb_module, tmb_main
import logging
import collections
import Queue
from tmb_button import TMB_Button

use_inputmodule = True
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    logging.exception("Error importing RPi.GPIO!")
    use_inputmodule = False
except ImportError:
    use_inputmodule = False

class InputModule(tmb_module.TMB_Module):
    
    def __init__(self, config):
        '''
        Constructor
        '''
        tmb_module.TMB_Module.__init__(self, config)
        
        self._count = config.getint('input', 'count')
        self._bounce = config.getint('input', 'bounce')
        self._buttons = []
        for i in range(self._count):
            button = TMB_Button('input_{0}'.format(i + 1), config)
            self._buttons.append(button)
            if use_inputmodule:
                GPIO.setup(button.channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                GPIO.add_event_detect(button.channel, GPIO.BOTH, callback=button.switchState, bouncetime=self._bounce)
    
    def start(self):
        tmb_module.TMB_Module.start(self)

        if not use_inputmodule:
            return
        GPIO.setmode(GPIO.BOARD)
        
        
    def stop(self):
        print("Stop InputModule")
        if use_inputmodule:
            GPIO.cleanup()
            
            
        tmb_module.TMB_Module.stop(self)

