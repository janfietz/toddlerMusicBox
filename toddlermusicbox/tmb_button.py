# -*- coding: utf-8 -*-
#
# tmb_button
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
import tmb_main
import collections
import logging
from threading import Lock

class TMB_Button(object):
    '''
    classdocs
    '''

    def __init__(self, section, config):
        '''
        Constructor
        '''
        
        self._channel = config.getint(section, 'channel')
        self._action = config.get(section, 'action')
        
        self._pressed = TMB_Button_StatePressed(self)
        self._unpressed = TMB_Button_StateUnpressed(self)

        self._stateMachine = TMB_Button_StateMachine(self._unpressed)
        self._mutex = Lock()

    @property
    def channel(self):
        return self._channel
    
    @property
    def action(self):
        return self._action
    
    @property
    def pressedState(self):
        return self._pressed

    @property
    def unpressedState(self):
        return self._unpressed

    def update(self):
        self._stateMachine.run()

    def switchState(self, channel):
        self._mutex.acquire()
        logging.debug('Button: %s switchState channel: %i', self.action, channel)
        self._stateMachine.run()
        self._mutex.release()

class TMB_Button_State(object):
    '''
    classdocs
    '''

    def __init__(self, button):
        '''
        Constructor
        '''
        self.button = button

    def enter(self):
        pass

    def run(self):
        pass
    
    def leave(self):
        pass

    def next(self):
        pass

class TMB_Button_StatePressed(TMB_Button_State):
    '''
    classdocs
    '''

    def __init__(self, button):
        '''
        Constructor
        '''
        TMB_Button_State.__init__(self, button)

    def enter(self):
        logging.debug('Button: %s enter state pressed.', self.button.action)
        tmb_main.ToddlerMusicBox.eventQueue.append(dict(sender = self, type = 'input', args = dict(action = self.button.action, state = 'pressed')))

    def run(self):
        pass

    def leave(self):
        logging.debug('Button: %s leave state pressed.', self.button.action)
    
    def next(self):
        return self.button.unpressedState

class TMB_Button_StateUnpressed(TMB_Button_State):
    '''
    classdocs
    '''

    def __init__(self, button):
        '''
        Constructor
        '''
        TMB_Button_State.__init__(self, button)

    def enter(self):
        logging.debug('Button: %s enter state unpressed.', self.button.action)
        tmb_main.ToddlerMusicBox.eventQueue.append(dict(sender = self, type = 'input', args = dict(action = self.button.action, state = 'unpressed')))

    def run(self):
        pass

    def leave(self):
        logging.debug('Button: %s leave state unpressed.', self.button.action)

    def next(self):
        return self.button.pressedState

class TMB_Button_StateMachine(object):
    '''
    classdocs
    '''

    def __init__(self, initial):
        '''
        Constructor
        '''
        self.currentState = initial

    def run(self):
        nextState = self.currentState.next()
        if nextState != self.currentState:
            self.currentState.leave()
            self.currentState = nextState
            self.currentState.enter()
        self.currentState.run()


