
from HardwareRepository.BaseHardwareObjects import Device

class WagoPneuMockup(Device):
    
    def __init__(self, name):
        Device.__init__(self, name)
        self.wagoState = "in"


    def init(self):
        pass

    def valueChanged(self, deviceName, value):
        
        self.wagoState = value

        self.emit('wagoStateChanged', (self.wagoState, ))
        
    
    def getWagoState(self):
        return self.wagoState 


    def wagoIn(self):
        self.wagoState = "in"
            
    def wagoOut(self):
        self.wagoState = "out"
