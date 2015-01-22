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

class SimulateVideo(BaseHardwareObjects.Device):
    def __init__(self, name):
        BaseHardwareObjects.Device.__init__(self, name)
        self.__brightnessExists = False
        self.__contrastExists = False
        self.__gainExists = False
        self.__gammaExists = False
        self.__polling = None
        
    def init(self):
        self.setIsReady(True)

    def imageType(self):
        return BayerType("RG16")

    def _get_last_image(self):
        return None
    
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
        return 600

    def getHeight(self):
        """tango"""
        return 400
    
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
            self.device.video_live=True
        else:
            self.device.video_live=False

    def setExposure(self, exposure):
        pass

