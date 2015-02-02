from HardwareRepository.BaseHardwareObjects import Device
import math
import logging
import time
import gevent
import types

class MotorMockup(Device):      
    (NOTINITIALIZED, UNUSABLE, READY, MOVESTARTED, MOVING, ONLIMIT) = (0,1,2,3,4,5)

    def __init__(self, name):
        Device.__init__(self, name)
        self.motorState = MotorMockup.READY


    def init(self): 
        self.motorState = MotorMockup.READY
        self.username = self.name()
        # this is ugly : I added it to make the centring procedure happy
        self.specName = self.name()
        self.position = 0

    def getState(self):
        return self.motorState
    
    def motorLimitsChanged(self):
        self.emit('limitsChanged', (self.getLimits(), ))
                     
    def getLimits(self):
        return (-1E3, 1E3)

    def getPosition(self):
        return self.position

    def getDialPosition(self):
        return self.getPosition()

    def move(self, position):
        self.position = position
        time.sleep(1)
        self.emit('positionChanged', (self.position, ))
        self.emit('stateChanged', (self.motorState, ))
        return

    def moveRelative(self, relativePosition):
        self.move(self.getPosition() + relativePosition)

    def syncMoveRelative(self, relative_position, timeout=None):
        return self.syncMove(self.getPosition() + relative_position)

    def waitEndOfMove(self, timeout=None):
        pass

    def syncMove(self, position, timeout=None):
        self.position = position
        return

    def motorIsMoving(self):
        return self.motorState == 'MOVING'
 
    def getMotorMnemonic(self):
        return self.name()

    def stop(self):
        return
