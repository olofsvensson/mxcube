from HardwareRepository.BaseHardwareObjects import Equipment
import numpy
import logging

class PhotonFluxMockup(Equipment):
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)
        self.current_flux = 1.0e12

    def init(self):
        pass
    
    def connectNotify(self, signal):
        if signal == "valueChanged":
            self.emitValueChanged()

    def shutterStateChanged(self, _):
        self.countsUpdated(1e10)

    def updateFlux(self, _):
        self.countsUpdated(1e10, ignore_shutter_state=True)

    def countsUpdated(self, counts, ignore_shutter_state=False):
        if not ignore_shutter_state and self.shutter.getShutterState()!="opened":
            self.emitValueChanged(0)
            return
 
        flux = 1.2e12
        self.emitValueChanged("%1.3g" % flux)

    def getCurrentFlux(self):
        return self.current_flux

    def emitValueChanged(self, counts=None):
        if counts is None:
#            self.current_flux = None
            self.emit("valueChanged", ("?", ))
        else:
            self.current_flux = float(counts)
            self.emit("valueChanged", (counts, ))
