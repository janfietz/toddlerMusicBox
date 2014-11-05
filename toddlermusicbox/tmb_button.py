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

class TMB_Button(Object):
    '''
    classdocs
    '''

    def __init__(self, params):
        '''
        Constructor
        '''
        self._pressed = TMB_Button_StatePressed(self)
        self._unpressed = TMB_Button_StateUnpressed(self)

        self._stateMachine = TMB_Button_StateMachine(self._unpressed)

    @property
    def pressedState(self):
        return self._pressed

    @property
    def unpressedState(self):
        return self._unpressed

    def update(self):
        self._stateMachine.run()

class TMB_Button_State(Object):
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

    def leave(self):
        pass

    def next(self):
        if not self.button.pressed():
            return self.button.unpressedState
        return self.button.pressedState

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
        pass

    def run(self):
        pass

    def leave(self):
        pass

class TMB_Button_StateUnpressed(Object):
    '''
    classdocs
    '''

    def __init__(self, params):
        '''
        Constructor
        '''
        pass

    def enter(self):
        pass

    def run(self):
        pass

    def leave(self):
        pass

class TMB_Button_StateMachine(Object):
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


