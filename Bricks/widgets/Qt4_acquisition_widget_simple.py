#
#  Project: MXCuBE
#  https://github.com/mxcube.
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

import os

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import uic

import queue_model_objects_v1 as queue_model_objects
from widgets.Qt4_widget_utils import DataModelInputBinder


class AcquisitionWidgetSimple(QtGui.QWidget):
    """
    Descript. :
    """
    def __init__(self, parent = None, name = None, fl = 0, acq_params = None, 
                 path_template = None, layout = None):
        """
        Descript. :
        """ 

        QtGui.QWidget.__init__(self, parent, QtCore.Qt.WindowFlags(fl))
        if name is not None:
            self.setObjectName(name)

        # Hardware objects ----------------------------------------------------
        self._beamline_setup_hwobj = None

        # Internal variables --------------------------------------------------

        # Properties ---------------------------------------------------------- 

        # Signals -------------------------------------------------------------

        # Slots ---------------------------------------------------------------

        # Graphic elements ----------------------------------------------------
        if acq_params is None:
            self._acquisition_parameters = queue_model_objects.AcquisitionParameters()
        else:
            self._acquisition_parameters = acq_params
        if path_template is None:
            self._path_template = queue_model_objects.PathTemplate()
        else:
            self._path_template = path_template

        self._acquisition_mib = DataModelInputBinder(self._acquisition_parameters)
        self.acq_widget = uic.loadUi(os.path.join(os.path.dirname(__file__),
                                "ui_files/Qt4_acquisition_widget_vertical_simple_layout.ui"))

        # Layout --------------------------------------------------------------
        main_layout = QtGui.QVBoxLayout(self)
        main_layout.addWidget(self.acq_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        # SizePolicies --------------------------------------------------------

        # Qt signal/slot connections ------------------------------------------
        self.acq_widget.num_images_cbox.activated.connect(self.update_num_images)
        self.acq_widget.detector_mode_combo.activated.connect(self.detector_mode_changed)
        self.acq_widget.osc_start_cbox.toggled.connect(self.osc_start_cbox_click)

        # Other ---------------------------------------------------------------
        self.energy_validator = QtGui.QDoubleValidator(0, 25, 5, self)
        self.resolution_validator = QtGui.QDoubleValidator(0, 15, 3, self)
        self.transmission_validator = QtGui.QDoubleValidator(0, 100, 3, self)
        self.exp_time_validator = QtGui.QDoubleValidator(0, 10000, 5, self)
        self.acq_widget.osc_start_ledit.setEnabled(False)
        self.acq_widget.kappa_ledit.setEnabled(False)
        self.acq_widget.kappa_phi_ledit.setEnabled(False) 
        self.acq_widget.num_images_cbox.setCurrentIndex(1)


    def osc_start_cbox_click(self, state):
        """
        Descript. :
        """
        self.update_osc_start(self._beamline_setup_hwobj._get_omega_axis_position())
        self.acq_widget.osc_start_ledit.setEnabled(state)

    def update_osc_start(self, new_value):
        """
        Descript. :
        """
        if not self.acq_widget.osc_start_cbox.isChecked():
            osc_start_value = 0
            try:
                osc_start_value = round(float(new_value), 2)
            except TypeError:
                pass
            self.acq_widget.osc_start_ledit.setText("%.2f" % osc_start_value)
            self._acquisition_parameters.osc_start = osc_start_value

    def update_kappa(self, new_value):
        """
        Descript. :
        """
        self.acq_widget.kappa_ledit.setText("%.2f" % float(new_value))

    def update_kappa_phi(self, new_value):
        """
        Descript. :
        """
        self.acq_widget.kappa_phi_ledit.setText("%.2f" % float(new_value))

    def use_kappa(self, state):
        """
        Descript. :
        """
        self.acq_widget.kappa_ledit.setDisabled(state)

    def use_kappa_phi(self, state):
        """
        Descript. :
        """
        self.acq_widget.kappa_phi_ledit.setDisabled(state)
    
    def update_num_images(self, index = None, num_images = None):
        """
        Descript. :
        """
        if index is not None:
            if index is 0:
                self._acquisition_parameters.num_images = 1
                self._path_template.num_files = 1
            elif index is 1:
                self._acquisition_parameters.num_images = 2
                self._path_template.num_files = 2
            elif index is 2:
                self._acquisition_parameters.num_images = 4
                self._path_template.num_files = 4

        if num_images:
            if self.acq_widget.num_images_cbox.count() > 3:
                self.acq_widget.num_images_cbox.removeItem(4)
        
            if num_images is 1:
                self.acq_widget.num_images_cbox.setCurrentIndex(0)    
            elif num_images is 2:
                self.acq_widget.num_images_cbox.setCurrentIndex(1)
            elif num_images is 4:
                self.acq_widget.num_images_cbox.setCurrentIndex(2)
            else:
                self.acq_widget.num_images_cbox.addItem(str(num_images))
                self.acq_widget.num_images_cbox.setCurrenIndex(3)

            self._path_template.num_files = num_images

    def use_mad(self, state):
        """
        Descript. :
        """
        pass

    def get_mad_energy(self):
        """
        Descript. :
        """
        pass

    def set_energies(self, energy_scan_result):
        """
        Descript. :
        """
        pass

    def energy_selected(self, index):
        """
        Descript. :
        """
        pass

    def set_beamline_setup(self, beamline_setup):
        """
        Descript. :
        """
        self._beamline_setup_hwobj = beamline_setup
        limits_dict = self._beamline_setup_hwobj.get_acquisition_limit_values()
        if 'osc_range' in limits_dict:
            limits = tuple(map(float, limits_dict['osc_range'].split(',')))
            (lower, upper) = limits
            osc_start_validator = QtGui.QDoubleValidator(lower, upper, 4, self)
            osc_range_validator = QtGui.QDoubleValidator(lower, upper, 4, self)
        else:
            osc_start_validator = QtGui.QDoubleValidator(-10000, 10000, 4, self)
            osc_range_validator = QtGui.QDoubleValidator(-10000, 10000, 4, self)

        self._acquisition_mib.bind_value_update('osc_start', 
                                                self.acq_widget.osc_start_ledit,
                                                float, 
                                                osc_start_validator)

        self._acquisition_mib.bind_value_update('osc_range', 
                                                self.acq_widget.osc_range_ledit,
                                                float, 
                                                osc_range_validator)

        kappa_validator = QtGui.QDoubleValidator(0, 180, 2, self)
        self._acquisition_mib.bind_value_update('kappa', 
                                                self.acq_widget.kappa_ledit,
                                                float, 
                                                kappa_validator)

        kappa_phi_validator = QtGui.QDoubleValidator(0, 180, 2, self)
        self._acquisition_mib.bind_value_update('kappa_phi', 
                                                self.acq_widget.kappa_phi_ledit,
                                                float, 
                                                kappa_phi_validator)

        self._acquisition_mib.bind_value_update('exp_time',
                              self.acq_widget.exp_time_ledit,
                              float, 
                              self.exp_time_validator)

        self._acquisition_mib.\
             bind_value_update('energy',
                               self.acq_widget.energy_ledit,
                               float,
                               self.energy_validator)
        self.acq_widget.energy_ledit.setToolTip(\
             "Energy limits %0.3f : %0.3f" % \
             (self.energy_validator.bottom(), self.energy_validator.top()))

        self._acquisition_mib.\
             bind_value_update('transmission',
                            self.acq_widget.transmission_ledit,
                            float,
                            self.transmission_validator)

        self._acquisition_mib.\
             bind_value_update('resolution',
                               self.acq_widget.resolution_ledit,
                               float,
                               self.resolution_validator)
 
        self.init_detector_modes()
        self._acquisition_mib.\
             bind_value_update('detector_mode',
                               self.acq_widget.detector_mode_combo,
                               int,
                               None)

        #self.acq_widget.osc_start_cbox.toggled.connnect(self.osc_start_cbox_click)
        self.set_tunable_energy(beamline_setup.tunable_wavelength())

    def set_energy(self, energy, wav):
        """
        Descript. :
        """
        self._acquisition_parameters.energy = energy
        self.acq_widget.energy_ledit.setText("%.4f" % float(energy))

    def update_transmission(self, transmission):
        """
        Descript. :
        """
        self.acq_widget.transmission_ledit.setText("%.2f" % float(transmission))
        self._acquisition_parameters.transmission = float(transmission)

    def update_resolution(self, resolution):
        """
        Descript. :
        """
        self.acq_widget.resolution_ledit.setText("%.3f" % float(resolution))
        self._acquisition_parameters.resolution = float(resolution)

    def update_energy_limits(self, limits):
        """
        Descript. :
        """
        if limits:
            self.energy_validator.setBottom(limits[0])
            self.energy_validator.setTop(limits[1])
            self.acq_widget.energy_ledit.setToolTip(
               "Energy limits %0.3f : %0.3f" %(limits[0], limits[1]))
            self._acquisition_mib.validate_all()

    def update_transmission_limits(self, limits):
        """
        Descript. :
        """
        if limits:
            self.transmission_validator.setBottom(limits[0])
            self.transmission_validator.setTop(limits[1])
            self.acq_widget.transmission_ledit.setToolTip(
               "Transmission limits %0.3f : %0.3f" %(limits[0], limits[1]))
            self._acquisition_mib.validate_all()

    def update_resolution_limits(self, limits):
        """
        Descript. :
        """
        if limits:
            self.resolution_validator.setBottom(limits[0])
            self.resolution_validator.setTop(limits[1])
            self.acq_widget.resolution_ledit.setToolTp(
               "Resolution limits %0.3f : %0.3f" %(limits[0], limits[1]))
            self._acquisition_mib.validate_all()

    def update_detector_exp_time_limits(self, limits):
        """
        Descript. :
        """
        if limits:
            self.exp_time_validator.setBottom(limits[0])
            self.exp_time_validator.setTop(limits[1])
            self.acq_widget.exp_time_ledit.setToolTip(
               "Exposure time limits %0.3f : %0.3f" %(limits[0], limits[1]))
            self._acquisition_mib.validate_all()

    def init_detector_modes(self):
        """
        Descript. :
        """
        if self._beamline_setup_hwobj is not None:
            modes_list = self._beamline_setup_hwobj.detector_hwobj.get_detector_modes_list()
            self.acq_widget.detector_mode_combo.clear()
            self.acq_widget.detector_mode_combo.addItems(modes_list)

    def update_detector_mode(self, detector_mode):
        """
        Descript. :
        """
        self.acq_widget.detector_mode_combo.setCurrentItem(detector_mode)
        
    def detector_mode_changed(self, detector_mode):
        """
        Descript. :
        """
        if self._beamline_setup_hwobj is not None:
            self._beamline_setup_hwobj.detector_hwobj.set_detector_mode(detector_mode)
    
    def update_data_model(self, acquisition_parameters, path_template):
        """
        Descript. :
        """
        self._acquisition_parameters = acquisition_parameters
        self._acquisition_mib.set_model(acquisition_parameters)
        self._path_template = path_template
        self.update_num_images(None, acquisition_parameters.num_images)

    """def get_resolution_limits(self):
        if self._beamline_setup_hwobj is not None:
            limits = self._beamline_setup_hwobj.resolution_hwobj.getLimits()
            return limits

    def get_energy_limits(self):
        if self._beamline_setup_hwobj is not None:
            limits = self._beamline_setup_hwobj.energy_hwobj.getEnergyLimits()
            return limits

    def get_exposure_time_limits(self):
        if self._beamline_setup_hwobj is not None:
            exposure_time_limits = self._beamline_setup_hwobj.detector_hwobj.get_exposure_time_limits()
            return exposure_time_limits

    def get_transmission_limits(self):
        if self._beamline_setup_hwobj is not None:
            limits = self._beamline_setup_hwobj.transmission_hwobj.get_transmission_limits()
            return limits"""

    def set_tunable_energy(self, state):
        """
        Descript. :
        """
        self.acq_widget.energy_ledit.setEnabled(state)

    def use_osc_start(self, state):
        """
        Descript. :
        """
        self.acq_widget.osc_start_cbox.setChecked(state)
        self.acq_widget.osc_start_cbox.setDisabled(state)

    def check_parameter_conflict(self):
        """
        Descript. :
        """
        return len(self._acquisition_mib.validate_all()) > 0
