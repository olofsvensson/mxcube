"""Class for cameras connected to Lima Tango Device Servers
"""
from HardwareRepository import BaseHardwareObjects
from HardwareRepository import CommandContainer
from HardwareRepository import HardwareRepository
from HardwareRepository.HardwareObjects.Camera import JpegType, BayerType, MmapType, RawType, RGBType
from Qub.CTools import pixmaptools
import gevent
import logging
import os
import time
import sys
import PyTango
import numpy
import struct

class SimulateVideo(BaseHardwareObjects.Device, BaseHardwareObjects.DeviceContainer):
    def __init__(self, name):
        BaseHardwareObjects.Device.__init__(self, name)
        BaseHardwareObjects.DeviceContainer.__init__(self)
        self.__brightnessExists = False
        self.__contrastExists = False
        self.__gainExists = False
        self.__gammaExists = False
        self.__polling = None
        self._height = 600
        self._width = 400
        
    def init(self):
        self.setIsReady(True)

    def imageType(self):
        return BayerType("RG16")

    def _get_last_image(self):
#        raw_buffer = numpy.fromstring(img_data[1][32:], numpy.uint16)
        raw_buffer = numpy.linspace(0, 255, self._width * self._height)
        self.scaling.autoscale_min_max(raw_buffer, self._width, self._height, pixmaptools.LUT.Scaling.BAYER_RG16)
        validFlag, qimage = pixmaptools.LUT.raw_video_2_image(raw_buffer,
                                                              self._width, self._height,
                                                              pixmaptools.LUT.Scaling.BAYER_RG16,
                                                              self.scaling)
        if validFlag:
            return qimage

     
    def _do_polling(self, sleep_time):
        time.sleep(sleep_time)

    def connectNotify(self, signal):
        pass

    #############   CONTRAST   #################
    def contrastExists(self):
        return self.__contrastExists

    #############   BRIGHTNESS   #################
    def brightnessExists(self):
        return self.__brightnessExists

    #############   GAIN   #################
    def gainExists(self):
        return self.__gainExists

    #############   GAMMA   #################
    def gammaExists(self):
        return self.__gammaExists

    #############   WIDTH   #################
    def getWidth(self):
        """tango"""
        return self._width

    def getHeight(self):
        """tango"""
        return self._height
    
    def setSize(self, width, height):
        """Set new image size

        Only takes width into account, because anyway
        we can only set a scale factor
        """
        return

    def takeSnapshot(self, *args, **kwargs):
        """tango"""
        return True

    def setLive(self, mode):
        """tango"""
        if mode:
            self.video_live=True
        else:
            self.video_live=False

    def setExposure(self, exposure):
        pass

