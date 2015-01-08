#!/usr/bin/env python
import sys
import os

MXCUBE_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
MXCUBE_GUI_FILE = os.path.join(MXCUBE_ROOT, "mxcube.gui")

sys.path.insert(0, MXCUBE_ROOT)
os.environ["CUSTOM_BRICKS_PATH"]=os.path.join(MXCUBE_ROOT, "Bricks")
os.environ["CUSTOM_HARDWARE_OBJECTS_PATH"]=os.path.join(MXCUBE_ROOT, "HardwareObjects")

from BlissFramework import startGUI

startGUI.run(MXCUBE_GUI_FILE)

