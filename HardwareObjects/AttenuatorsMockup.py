from HardwareRepository.BaseHardwareObjects import Device

class AttenuatorsMockup(Device):
    def __init__(self, *args):
        Device.__init__(self, *args)
        self.state = Device.READY
        self.labels  = []
        self.bits    = []
        self.attno   = 0
        self.getValue = self.get_value 
        self.attState = 0       
        self._transmission = 100

    def getAttState(self):
        return self.attState

    def getAttFactor(self):
        return self._transmission

    def get_value(self):
        return self.getAttFactor()

    def set_value(self, value):
        return

    def getAtteConfig(self):
        self.attno = len( self['atte'] )

        for att_i in range( self.attno ):
           obj = self['atte'][att_i]
           self.labels.append( obj.label )
           self.bits.append( obj.bits )

    def setTransmission(self, transmission_percent):
        self._transmission = transmission_percent
        self.emit('attFactorChanged', (transmission_percent, )) 
