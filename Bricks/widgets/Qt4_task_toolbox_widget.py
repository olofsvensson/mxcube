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

import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

import Qt4_queue_item
import queue_model_objects_v1 as queue_model_objects
from queue_model_enumerables_v1 import EXPERIMENT_TYPE

from BlissFramework import Qt4_Icons
from widgets.Qt4_create_discrete_widget import CreateDiscreteWidget
from widgets.Qt4_create_helical_widget import CreateHelicalWidget
from widgets.Qt4_create_char_widget import CreateCharWidget
from widgets.Qt4_create_energy_scan_widget import CreateEnergyScanWidget
from widgets.Qt4_create_xrf_scan_widget import CreateXRFScanWidget
from widgets.Qt4_create_advanced_scan_widget import CreateAdvancedScanWidget


class TaskToolBoxWidget(QtGui.QWidget):
    def __init__(self, parent = None, name = "task_toolbox"):
        QtGui.QWidget.__init__(self, parent)
        self.setObjectName = name

        # Hardware objects ----------------------------------------------------
        self.graphics_manager_hwobj = None

        # Internal variables --------------------------------------------------
        self.tree_brick = None
        self.previous_page_index = 0

        # Graphic elements ----------------------------------------------------
        self.method_group_box = QtGui.QGroupBox(" Collection method", self)
        font = self.method_group_box.font()
        font.setPointSize(10)
        self.method_group_box.setFont(font)
    
        self.tool_box = QtGui.QToolBox(self.method_group_box)
        self.tool_box.setObjectName("tool_box")
        self.tool_box.setFixedWidth(475)
        self.tool_box.setFont(font)
        
        self.discrete_page = CreateDiscreteWidget(self.tool_box, "Discrete",)
        self.char_page = CreateCharWidget(self.tool_box, "Characterise")
        self.helical_page = CreateHelicalWidget(self.tool_box, "helical_page")
        self.energy_scan_page = CreateEnergyScanWidget(self.tool_box, "energy_scan")
        self.xrf_scan_page = CreateXRFScanWidget(self.tool_box, "xrf_scan")  
        self.advanced_scan_page = CreateAdvancedScanWidget(self.tool_box, "advanced_scan")
        
        self.tool_box.addItem(self.discrete_page, "Standard Collection")
        self.tool_box.addItem(self.char_page, "Characterisation")
        self.tool_box.addItem(self.helical_page, "Helical Collection")
        self.tool_box.addItem(self.energy_scan_page, "Energy Scan")
        self.tool_box.addItem(self.xrf_scan_page, "XRF Scan")
        self.tool_box.addItem(self.advanced_scan_page, "Advanced")

        self.button_box = QtGui.QWidget(self)
        self.create_task_button = QtGui.QPushButton("  Add to queue", self.button_box)
        self.create_task_button.setIcon(QtGui.QIcon(Qt4_Icons.load("add_row.png")))
        msg = "Add the collection method to the selected sample"
        self.create_task_button.setToolTip(msg)
        
        # Layout --------------------------------------------------------------
        self.method_group_box_layout = QtGui.QVBoxLayout(self)
        self.method_group_box_layout.addWidget(self.tool_box)
        self.method_group_box_layout.setSpacing(0)
        self.method_group_box_layout.setContentsMargins(0, 0, 0, 0)
        self.method_group_box.setLayout(self.method_group_box_layout)

        self.button_box_layout = QtGui.QHBoxLayout(self)
        self.button_box_layout.addStretch(0)
        self.button_box_layout.addWidget(self.create_task_button)
        self.button_box_layout.setSpacing(0)
        self.button_box_layout.setContentsMargins(0, 0, 0, 0)
        self.button_box.setLayout(self.button_box_layout)

        self.main_layout = QtGui.QVBoxLayout(self)
        self.main_layout.addWidget(self.method_group_box)
        self.main_layout.addWidget(self.button_box)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout) 

        # SizePolicies --------------------------------------------------------
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Expanding)


        # Qt signal/slot connections ------------------------------------------
        self.connect(self.create_task_button, QtCore.SIGNAL("clicked()"),
                     self.create_task_button_click)

        self.connect(self.tool_box, QtCore.SIGNAL("currentChanged( int )"),
                     self.current_page_changed)

        # Other ---------------------------------------------------------------   

    def set_tree_brick(self, brick):
        """
        Sets the tree brick of each page in the toolbox.
        """
        self.tree_brick = brick

        for i in range(0, self.tool_box.count()):
            self.tool_box.widget(i).set_tree_brick(brick)

    def set_beamline_setup(self, beamline_setup_hwobj):
        self._beamline_setup_hwobj = beamline_setup_hwobj
        for i in range(0, self.tool_box.count()):
            self.tool_box.widget(i).set_beamline_setup(beamline_setup_hwobj)

        self.graphics_manager_hwobj = beamline_setup_hwobj.shape_history_hwobj
        self.energy_scan_page.set_energy_scan_hwobj(beamline_setup_hwobj.energyscan_hwobj)

        # Remove energy scan page from non tunable wavelentgh beamlines
        if not beamline_setup_hwobj.tunable_wavelength():
            self.tool_box.removeItem(self.energy_scan_page)
            self.energy_scan_page.hide()

    def update_data_path_model(self):
        for i in range(0, self.tool_box.count()):
            item = self.tool_box.item(i)
            item.init_data_path_model()
            item.update_selection()

            
    def ispyb_logged_in(self, logged_in):
        """
        Handels the signal logged_in from the brick the handles LIMS (ISPyB)
        login, ie ProposalBrick. The signal is emitted when a user was 
        succesfully logged in.
        """
        #import pdb;pdb.set_trace()
        for i in range(0, self.tool_box.count()):
            self.tool_box.widget(i).ispyb_logged_in(logged_in)
            
    def current_page_changed(self, page_index):
        tree_items =  self.tree_brick.get_selected_items()

        if len(tree_items) > 0:        
            tree_item = tree_items[0]

            # Get the directory form the previous page and update 
            # the new page with the direcotry and run_number from the old.
            # IFF sample or group selected.
            if isinstance(tree_item, Qt4_queue_item.DataCollectionGroupQueueItem) or\
                    isinstance(tree_item, Qt4_queue_item.SampleQueueItem):
                new_pt = self.tool_box.widget(page_index)._path_template
                previous_pt = self.tool_box.widget(self.previous_page_index)._path_template
                new_pt.directory = previous_pt.directory
                new_pt.run_number = self._beamline_setup_hwobj.queue_model_hwobj.\
                    get_next_run_number(new_pt)
            elif isinstance(tree_item, Qt4_queue_item.DataCollectionQueueItem):
                data_collection = tree_item.get_model()
                if data_collection.experiment_type == EXPERIMENT_TYPE.HELICAL:
                    if self.tool_box.currentWidget() == self.helical_page:
                        self.create_task_button.setEnabled(True)
                elif data_collection.experiment_type == EXPERIMENT_TYPE.MESH:
                    if self.tool_box.currentWidget() == self.advanced_scan_page:
                        self.create_task_button.setEnabled(True)
                elif self.tool_box.currentWidget() == self.discrete_page:
                    self.create_task_button.setEnabled(True)
            elif isinstance(tree_item, Qt4_queue_item.CharacterisationQueueItem):
                if self.tool_box.currentWidget() == self.char_page:
                    self.create_task_button.setEnabled(True)
            elif isinstance(tree_item, Qt4_queue_item.EnergyScanQueueItem):
                if self.tool_box.currentWidget() == self.energy_scan_page:
                    self.create_task_button.setEnabled(True)
            elif isinstance(tree_item, Qt4_queue_item.XRFScanQueueItem):
                if self.tool_box.currentWidget() == self.xrf_scan_page:
                    self.create_task_button.setEnabled(True)
            elif isinstance(tree_item, Qt4_queue_item.GenericWorkflowQueueItem):
                if self.tool_box.currentWidget() == self.workflow_page:
                    self.create_task_button.setEnabled(True)


            self.tool_box.widget(page_index).selection_changed(tree_items)
            self.previous_page_index = page_index

    def selection_changed(self, items):
        """
        Called by the parent widget when selection in the tree changes.
        """
        if len(items) == 1:
            
            if isinstance(items[0], Qt4_queue_item.DataCollectionGroupQueueItem):
                self.create_task_button.setEnabled(False)
            else:
                self.create_task_button.setEnabled(True)

            if isinstance(items[0], Qt4_queue_item.DataCollectionQueueItem):
                data_collection = items[0].get_model()

                if data_collection.experiment_type == EXPERIMENT_TYPE.HELICAL:
                    self.tool_box.setCurrentWidget(self.helical_page)
                else:
                    self.tool_box.setCurrentWidget(self.discrete_page)
            elif isinstance(items[0], Qt4_queue_item.CharacterisationQueueItem):
                self.tool_box.setCurrentWidget(self.char_page)
            elif isinstance(items[0], Qt4_queue_item.EnergyScanQueueItem):
                self.tool_box.setCurrentWidget(self.energy_scan_page)
            elif isinstance(items[0], Qt4_queue_item.EnergyScanQueueItem):
                self.tool_box.setCurrentWidget(self.xrf_scan_page)
            elif isinstance(items[0], Qt4_queue_item.GenericWorkflowQueueItem):
                self.tool_box.setCurrentWidget(self.workflow_page)

        current_page = self.tool_box.currentWidget()
        current_page.selection_changed(items)

    def create_task_button_click(self):
        if self.tool_box.currentWidget().approve_creation():
            items = self.tree_brick.get_selected_items()

            if not items:
                logging.getLogger("user_level_log").\
                    warning("Select the sample or group you "\
                            "would like to add to.")
            else:
                for item in items:
                    shapes = self.graphics_manager_hwobj.get_selected_shapes()
                    task_model = item.get_model()

                    # Create a new group if sample is selected
                    if isinstance(task_model, queue_model_objects.Sample):
                        group_task_node = queue_model_objects.TaskGroup()
                        current_item = self.tool_box.currentWidget()

                        """if current_item is self.workflow_page:
                            group_name = current_item._workflow_cbox.currentText()
                        else:
                            group_name = current_item._task_node_name"""
                        group_name = current_item._task_node_name

                        group_task_node.set_name(group_name)
                        num = task_model.get_next_number_for_name(group_name)
                        group_task_node.set_number(num)

                        self.tree_brick.queue_model_hwobj.\
                          add_child(task_model, group_task_node)

                        task_model = group_task_node
                    
                    if len(shapes):
                        for shape in shapes:
                            self.create_task(task_model, shape)
                    else:
                        self.create_task(task_model)

            self.tool_box.currentWidget().update_selection()

    def create_task(self, task_node, shape = None):
        # Selected item is a task group
        if isinstance(task_node, queue_model_objects.TaskGroup):
            sample = task_node.get_parent()
            task_list = self.tool_box.currentWidget().create_task(sample, shape)

            for child_task_node in task_list:
                self.tree_brick.queue_model_hwobj.add_child(task_node, child_task_node)

        # The selected item is a task, make a copy.
        else:
            new_node = self.tree_brick.queue_model_hwobj.copy_node(task_node)
            self.tree_brick.queue_model_hwobj.add_child(task_node.get_parent(), new_node)
