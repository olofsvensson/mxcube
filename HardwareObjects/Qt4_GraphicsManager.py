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
#   You should have received a copy of the GNU General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

"""
Qt4_GraphicsManager keeps track of the current shapes the user has created. The
shapes handled are any that inherits the Shape base class. There are currently
two shapes implemented Point and Line.

Point is the graphical representation of a centred position. A point can be
stored and managed by the ShapeHistory. the Line object represents a line
between two Point objects.

"""
import copy
import types
import logging
import traceback

from PyQt4 import QtGui
from PyQt4 import QtCore

import queue_model_objects_v1 as queue_model_objects

from HardwareRepository.BaseHardwareObjects import HardwareObject
from HardwareRepository.HardwareRepository import dispatcher

SELECTED_COLOR = QtCore.Qt.green
NORMAL_COLOR = QtCore.Qt.yellow


class Qt4_GraphicsManager(HardwareObject):
    """
    Keeps track of the current shapes the user has created. The
    shapes handled are any that inherits the Shape base class.
    """
    def __init__(self, name):
        HardwareObject.__init__(self, name)
     
        self.pixels_per_mm = [0, 0]
        self.beam_size = [0, 0]
        self.beam_position = [0, 0]
        self.beam_shape = None
        self.graphics_scene_width = None
        self.graphics_scene_height = None
        self.graphics_view = GraphicsView()
         
        self.graphics_camera_frame = GraphicsCameraFrame()
        self.graphics_beam_item = GraphicsItemBeam(self)
        self.graphics_scale_item = GraphicsItemScale(self)
        self.graphics_omega_reference_item = GraphicsItemOmegaReference(self)
        self.graphics_centring_lines_item = GraphicsItemCentringLines(self)
        self.graphics_centring_lines_item.hide()
        self.graphics_mesh_draw_item = GraphicsItemMesh(self)
        self.graphics_mesh_draw_item.hide()
         
        self.graphics_view.graphics_scene.addItem(self.graphics_camera_frame) 
        self.graphics_view.graphics_scene.addItem(self.graphics_beam_item)
        self.graphics_view.graphics_scene.addItem(self.graphics_omega_reference_item)
        self.graphics_view.graphics_scene.addItem(self.graphics_centring_lines_item) 
        #self.graphics_view.graphics_scene.addItem(self.graphics_mesh_draw_item)
        self.graphics_view.graphics_scene.addItem(self.graphics_scale_item)

        self.beam_info_dict = {}
        self.omega_axis_info_dict = {}
        self.centring_points = []
        self.centring_state = False
        self.mesh_drawing_state = False
        self.point_count = 0

        """QtCore.QObject.connect(self.graphics_view.scene(), 
                               QtCore.SIGNAL('graphicsViewMouseClicked'), 
                               self.graphics_view_mouse_clicked)
        QtCore.QObject.connect(self.graphics_view.scene(),
                               QtCore.SIGNAL('graphicsViewMouseReleased'),
                               self.graphics_view_mouse_released)
        QtCore.QObject.connect(self.graphics_view, 
                               QtCore.SIGNAL('graphicsViewMouseMoved'), 
                               self.graphics_view_mouse_moved)"""

        self.graphics_view.scene().mouseClickedSignal.connect(\
             self.graphics_view_mouse_clicked)
        self.graphics_view.scene().mouseReleasedSignal.connect(\
             self.graphics_view_mouse_released)
        self.graphics_view.mouseMovedSignal.connect(
             self.graphics_view_mouse_moved)
        self.graphics_view.keyPressedSignal.connect(
             self.graphics_view_key_pressed)
        
    def graphics_view_mouse_clicked(self, x, y): 
        self.emit("graphicsClicked", x, y)
        if self.centring_state:
            self.graphics_centring_lines_item.set_coordinates(x, y)
        elif self.mesh_drawing_state:
            self.graphics_mesh_draw_item.show()
            self.graphics_mesh_draw_item.set_draw_mode(True)
            self.graphics_mesh_draw_item.set_draw_start_position(x, y)
        else:
            for graphics_item in self.graphics_view.scene().items():
                graphics_item.setSelected(False)

    def graphics_view_mouse_released(self, x, y):
        self.graphics_mesh_draw_item.set_draw_mode(False)

    def graphics_view_mouse_moved(self, x, y):
        if self.centring_state:
            self.graphics_centring_lines_item.set_coordinates(x, y)
        if (self.mesh_drawing_state and 
            self.graphics_mesh_draw_item.is_draw_mode()):
            self.graphics_mesh_draw_item.set_draw_end_position(x, y)

    def graphics_view_key_pressed(self, key_event):
        if key_event == "Delete":
            for item in self.graphics_view.graphics_scene.items():
                if item.isSelected():
                    self.delete_shape(item)

    def get_graphics_view(self):
        return self.graphics_view

    def get_camera_frame(self):
        return self.graphics_camera_frame 

    def set_graphics_scene_size(self, size):
        self.graphics_scene_size = size
        self.graphics_scale_item.set_position(10, self.graphics_scene_size[1] - 10)

    def get_graphics_beam_item(self):
        return self.graphics_beam_item

    def get_scale_item(self):
        return self.graphics_scale_item

    def get_omega_reference_item(self):
        return self.graphics_omega_reference_item

    def set_centring_state(self, state):
        self.centring_state = state
        self.graphics_centring_lines_item.set_visible(state)

    def get_shapes(self):
        """
        :returns: All the shapes currently handled.
        """
        shapes_list = []
        for shape in self.graphics_view.graphics_scene.items():
            if type(shape) in (GraphicsItemPoint, GraphicsItemLine, GraphicsItemMesh):
                shapes_list.append(shape)                 
        return shapes_list

    def get_points(self):
        """
        :returns: All points currently handled
        """
        current_points = []

        for shape in self.get_shapes():
            if isinstance(shape, GraphicsItemPoint):
                current_points.append(shape)

        return current_points
        
    def add_shape(self, shape):
        """
        Adds the shape <shape> to the list of handled objects.

        :param shape: Shape to add.
        :type shape: Shape object.
        """
        self.de_select_all()
        shape.setSelected(True) 

        if isinstance(shape, GraphicsItemPoint):
            self.point_count += 1
            shape.set_index(self.point_count)
            
        self.graphics_view.graphics_scene.addItem(shape)

    def _delete_shape(self, shape):
        if isinstance(shape, GraphicsItemPoint):
            self.point_count -= 1  
        self.graphics_view.graphics_scene.removeItem(shape)

    def delete_shape(self, shape):
        """
        Removes the shape <shape> from the list of handled shapes.

        :param shape: The shape to remove
        :type shape: Shape object.
        """
        if isinstance(shape, GraphicsItemPoint):
            for s in self.get_shapes():
                if isinstance(s, GraphicsItemLine):
                    if shape in (s.cp_start, s.cp_start):
                        self._delete_shape(s)
                        break
        self._delete_shape(shape)

    def clear_all(self):
        """
        Clear the shape history, remove all contents.
        """
        print "clear all TODO"

    def de_select_all(self):
        self.graphics_view.graphics_scene.clearSelection()

    def select_shape_with_cpos(self, cpos):
        self.de_select_all()
        for shape in self.get_shapes():
            if isinstance(shape, GraphicsItemPoint):
                if shape.get_centred_positions()[0] == cpos:
                    shape.setSelected(True)

    def get_grid(self):
        """
        Returns the current grid object.
        """
        grid_dict = dict()
        dispatcher.send("grid", self, grid_dict)
        return grid_dict

    def set_grid_data(self, key, result_data):
        dispatcher.send("set_grid_data", self, key, result_data)

    def get_selected_shapes(self):
        selected_shapes = []
        for item in self.graphics_view.graphics_scene.items():
            if (type(item) in [GraphicsItemPoint, GraphicsItemMesh, GraphicsItemLine] and
                item.isSelected()):
                selected_shapes.append(item) 
        return selected_shapes

    def update_beam_position(self, beam_position):
        if beam_position is not None:
            self.graphics_beam_item.set_position(beam_position[0],
                                                 beam_position[1])

    def update_pixels_per_mm(self, pixels_per_mm):
        if pixels_per_mm is not None:
            self.pixels_per_mm = pixels_per_mm
            self.graphics_beam_item.set_size(self.beam_size[0] * self.pixels_per_mm[0],
                                             self.beam_size[1] * self.pixels_per_mm[1])

    def update_beam_info(self, beam_info):
        if beam_info is not None:
            self.beam_size[0] = beam_info.get("size_x")
            self.beam_size[1] = beam_info.get("size_y")
            self.graphics_beam_item.set_shape(beam_info.get("shape", "rectangular"))
            if self.pixels_per_mm is not None:
                self.graphics_beam_item.set_size(self.beam_size[0] * self.pixels_per_mm[0],
                                                 self.beam_size[1] * self.pixels_per_mm[1])

    def update_omega_reference(self, omega_reference):
        self.graphics_omega_reference_item.set_reference(omega_reference)  

    def add_new_centring_point(self, state, centring_status, beam_info):
        new_point = GraphicsItemPoint(self,200, 200)
        self.centring_points.append(new_point)
        self.graphics_view.graphics_scene.addItem(new_point)        

    def get_snapshot(self, shape):
        if shape:
            self.de_select_all()
            shape.setSelected(True)

        image = QtGui.QImage(self.graphics_view.graphics_scene.sceneRect().size().toSize(), 
                             QtGui.QImage.Format_ARGB32)
        image.fill(QtCore.Qt.transparent)
        image_painter = QtGui.QPainter(image)
        self.graphics_view.render(image_painter)
        image_painter.end()
        return image

    def set_mesh_draw_state(self, state):
        self.mesh_drawing_state = state

    def start_mesh_draw(self):
        self.graphics_mesh_draw_item.show()
        self.mesh_drawing_state = True

    def save_current_mesh(self):
        new_mesh_obj = GraphicsItemMesh(self)
        new_mesh_obj.set_properties(self.graphics_mesh_draw_item.get_properties())

        self.add_shape(self.graphics_mesh_draw_item)
        self.graphics_mesh_draw_item = GraphicsItemMesh(self)
        self.graphics_mesh_draw_item.hide()
  
class GraphicsItem(QtGui.QGraphicsItem):
    """
    Descript. : Base class for shapes.
    """
    def __init__(self, parent=None, position_x = 0, position_y = 0):
        QtGui.QGraphicsItem.__init__(self)
        rect = QtCore.QRectF(0, 0, 0, 0)
        self.rect = rect
        self.style = QtCore.Qt.SolidLine
        self.setMatrix = QtGui.QMatrix()
        self.setPos(position_x, position_y)

    def boundingRect(self):
        return self.rect.adjusted(-2, -2, 2, 2)

    def set_size(self, width, height):
        self.rect.setWidth(width)
        self.rect.setHeight(height)

    def set_position(self, position_x, position_y):
        if (position_x is not None and
            position_y is not None):
            self.setPos(position_x, position_y)

    def set_visible(self, is_visible):
        if is_visible: 
            self.show()
        else:
            self.hide()

class GraphicsItemBeam(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent, position_x = 0, position_y= 0):
        GraphicsItem.__init__(self, parent, position_x = 0, position_y= 0)
        self.shape_is_rectangle = True
        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable | \
                      QtGui.QGraphicsItem.ItemIsSelectable)

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.style)
        pen.setWidth(1)
        if option.state & QtGui.QStyle.State_Selected:
            pen.setColor(QtCore.Qt.red)
        else:
            pen.setColor(QtCore.Qt.blue)
        painter.setPen(pen)
        if self.shape_is_rectangle:
            painter.drawRect(self.rect)
        else:
            painter.drawEllipse(self.rect)
        pen.setColor(QtCore.Qt.red) 
        painter.setPen(pen)
        painter.drawLine(int(self.rect.width() / 2) - 15, int(self.rect.height() / 2),
                         int(self.rect.width() / 2) + 15, int(self.rect.height() / 2))
        painter.drawLine(int(self.rect.width() / 2), int(self.rect.height() / 2) - 15, 
                         int(self.rect.width() / 2), int(self.rect.height() / 2) + 15)  

    def set_shape(self, is_rectangle):
        self.shape_is_rectangle = is_rectangle      

class GraphicsItemMesh(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent, position_x = 0, position_y= 0):
        GraphicsItem.__init__(self, parent, position_x = 0, position_y= 0)
        self.__beam_size_hor = 70
        self.__beam_size_ver = 70
        self.__cell_height = 70
        self.__cell_width = 70
        self.__corner_points_motor_pos = []
        self.__corner_points_coord = [[0, 0], [0, 0], [0, 0], [0, 0]]
        self.__num_col = 0      
        self.__num_row = 0
        #self.__num_col = 5
        #self.__num_row = 3
        self.__draw_mode = True
        self.__draw_projection = False

    def set_draw_start_position(self, pos_x, pos_y):
        self.__corner_points_coord[0][0] = pos_x
        self.__corner_points_coord[0][1] = pos_y
        self.__corner_points_coord[1][1] = pos_y
        self.__corner_points_coord[2][0] = pos_x
        self.scene().update()

    def set_draw_end_position(self, pos_x, pos_y):
        self.__corner_points_coord[1][0] = pos_x
        self.__corner_points_coord[2][1] = pos_y
        self.__corner_points_coord[3][0] = pos_x
        self.__corner_points_coord[3][1] = pos_y
        self.scene().update()

    def set_draw_mode(self, draw_mode):
        self.__draw_mode = draw_mode 

    def is_draw_mode(self):
        return self.__draw_mode

    def get_properties(self):
        return {"beam_hor" : self.__beam_size_hor,
                "beam_ver" : self.__beam_size_ver,
                "cell_height" : self.__cell_height,
                "cell_width" : self.__cell_width,
                "corner_pos" : self.__corner_points_motor_pos,
                "corner_coord" : self.__corner_points_coord,
                "num_col" : self.__num_col,
                "num_row" : self.__num_row}

    def set_properties(self, properties_dict):
        self.__beam_size_hor = properties_dict.get("beam_hor")
        self.__beam_size_ver = properties_dict.get("beam_ver")
        self.__cell_width = properties_dict.get("cell_width")
        self.__cell_height = properties_dict.get("cell_height")
        self.__corner_points_motor_pos = properties_dict.get("corner_pos") 
        self.__corner_points_coord = properties_dict.get("corner_coord")
        self.__num_col = properties_dict.get("num_col")
        self.__num_row = properties_dict.get("num_row")

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.style)
        pen.setWidth(1)
        brush = QtGui.QBrush(self.style)
        brush.setColor(QtGui.QColor(70,70,165))
        if option.state & QtGui.QStyle.State_Selected:
            pen.setStyle(QtCore.Qt.DashLine)
            pen.setColor(QtCore.Qt.green)
        else:
            pen.setStyle(QtCore.Qt.SolidLine) 
            pen.setColor(QtCore.Qt.black)

        pen.setColor(QtCore.Qt.green)
        painter.setPen(pen)
        painter.setBrush(brush)
        
        if not self.__draw_projection:
            self.__num_col = int(abs(self.__corner_points_coord[0][0] - \
                                     self.__corner_points_coord[1][0]) / \
                                     self.__beam_size_hor)
            self.__num_row = int(abs(self.__corner_points_coord[0][1] - \
                                     self.__corner_points_coord[2][1]) / \
                                     self.__beam_size_ver) 
            for row in range(0, self.__num_row):
                row_offset = row * self.__cell_width
                for col in range(0, self.__num_col):
                    col_offset = col * self.__cell_height 
                    start_x = self.__corner_points_coord[0][0] + \
                              col_offset
                    start_y = self.__corner_points_coord[0][1] + \
                              row_offset
                    brush.setStyle(QtCore.Qt.Dense4Pattern)
                    painter.setBrush(brush)
                    painter.drawEllipse(start_x, start_y, self.__cell_height,
                                        self.__cell_width) 
                    brush.setStyle(QtCore.Qt.NoBrush)
                    painter.setBrush(brush)
                    painter.drawRect(start_x, start_y, self.__cell_height,
                                     self.__cell_width)
                     
        else:
            print "draw projection"
 
class GraphicsItemScale(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent, position_x = 0, position_y= 0):
        GraphicsItem.__init__(self, parent, position_x = 0, position_y= 0)

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.style)
        pen.setWidth(3)
        pen.setColor(QtCore.Qt.green)
        painter.setPen(pen)
        painter.drawLine(0, 0, 150, 0)
        painter.drawLine(0, 0, 0, -50)

class GraphicsItemOmegaReference(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent, position_x = 0, position_y= 0):
        GraphicsItem.__init__(self, parent, position_x = 0, position_y= 0)
        self.parent = parent
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.style)
        pen.setWidth(1)
        pen.setColor(QtCore.Qt.white)
        painter.setPen(pen)
        painter.drawLine(self.start_x, self.start_y, self.end_x, self.end_y)

    def set_reference(self, omega_reference):
        line_length = self.parent.graphics_scene_size
        if omega_reference[0] is not None:
            #Omega reference is a vertical axis
            self.start_x = omega_reference[0]
            self.end_x = omega_reference[0]
            self.start_y = 0
            self.end_y = line_length[1]
        else:
            self.start_x = 0
            self.end_x = line_length[0]
            self.start_y = omega_reference[1]
            self.end_y = omega_reference[1]

class GraphicsItemCentringLines(GraphicsItem):
    """
    Descrip. : 
    """
    def __init__(self, parent, position_x = 0, position_y= 0):
        GraphicsItem.__init__(self, parent, position_x = 0, position_y= 0)
        self.parent = parent

        self.coord_x = 200
        self.coord_y = 100

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.style)
        pen.setWidth(1)
        pen.setColor(QtCore.Qt.yellow)
        painter.setPen(pen)
        painter.drawLine(self.coord_x, 0, self.coord_x, self.scene().height())
        painter.drawLine(0, self.coord_y, self.scene().width(), self.coord_y)

    def set_coordinates(self, x, y):
        self.coord_x = x
        self.coord_y = y 
        self.scene().update()        

class GraphicsItemPoint(GraphicsItem):
    """
    Descrip. : Centred point class.
    Args.    : parent, centred position (motors position dict, 
               full_centring (True if 3click centring), initial position)
    """
    def __init__(self, centred_position = None, full_centring = True,
                 position_x = 0, position_y = 0):
        GraphicsItem.__init__(self, position_x, position_y)

        self.full_centring = full_centring
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable) 

        if centred_position is None:
            self.centred_position = queue_model_objects.CentredPosition()
            self.centred_position.centring_method = False
        else:
            self.centred_position = centred_position
        self.set_size(20, 20)
	self.set_position(position_x, position_y)
        self.index = None

    def get_centred_positions(self):
        return [self.centred_position]

    def set_index(self, index):
        self.index = index  

    def get_index(self):
        return self.index

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.style)
        pen.setWidth(1)

        if option.state & QtGui.QStyle.State_Selected:
            pen.setColor(QtCore.Qt.green)
        else:
            pen.setColor(QtCore.Qt.yellow)
        painter.setPen(pen)
        painter.drawEllipse(self.rect)
        painter.drawLine(self.rect.left(), self.rect.top(),
                         self.rect.right(), self.rect.bottom())
        painter.drawLine(self.rect.right(), self.rect.top(),
                         self.rect.left(), self.rect.bottom())
        if self.index: 
            painter.drawText(self.rect.right() + 2, self.rect.top(), str(self.index))
        else:
            painter.drawText(self.rect.right() + 2, self.rect.top(), "#")

    def get_position(self):
        return self.__position_x, self.__position_y

    def set_position(self, position_x, position_y):
        self.__position_x = position_x
        self.__position_y = position_y
        self.setPos(self.__position_x - 10, self.__position_y - 10)

class GraphicsItemLine(GraphicsItem):
    """
    Descrip. : Line class.
    """
    def __init__(self, cp_start, cp_end):
        GraphicsItem.__init__(self)

        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)
        self.index = None
        self.cp_start = cp_start
        self.cp_end = cp_end

    def get_centred_positions(self):
        return [self.cp_start.centred_position, self.cp_end.centred_position]

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.style)
        pen.setWidth(2)

        if option.state & QtGui.QStyle.State_Selected:
            pen.setColor(QtCore.Qt.green)
        else:
            pen.setColor(QtCore.Qt.yellow)
        painter.setPen(pen)
        (start_cp_x, start_cp_y) = self.cp_start.get_position()
        (end_cp_x, end_cp_y) = self.cp_end.get_position()
        painter.drawLine(start_cp_x, start_cp_y,
                         end_cp_x, end_cp_y)
        if self.index:
            painter.drawText(self.rect.right() + 2, self.rect.top(), str(self.index))
        else:
            painter.drawText(self.rect.right() + 2, self.rect.top(), "#")

    def setSelected(self, state):
        GraphicsItem.setSelected(self, state)
        self.cp_start.setSelected(state)
        self.cp_end.setSelected(state)

    def get_points_index(self):
        return (self.cp_start.get_index(), self.cp_end.get_index())

class GraphicsView(QtGui.QGraphicsView):
    mouseMovedSignal = QtCore.pyqtSignal(int, int)
    keyPressedSignal = QtCore.pyqtSignal(str)

    def __init__ (self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.graphics_scene = GraphicsScene(self)
        self.setScene(self.graphics_scene)  
        self.graphics_scene.clearSelection()
        self.setMouseTracking(True)
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)

    def mouseMoveEvent(self, event):
        position = QtCore.QPointF(event.pos())
        self.mouseMovedSignal.emit(position.x(), position.y())
        self.update()
 
    def keyPressEvent(self, event):
        key_type = None
        if event.key() in(QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):  
            key_type = "Delete"
        if key_type:
            self.keyPressedSignal.emit(key_type)


class GraphicsScene(QtGui.QGraphicsScene):
    mouseClickedSignal = QtCore.pyqtSignal(int, int)
    mouseReleasedSignal = QtCore.pyqtSignal(int, int)

    def __init__ (self, parent=None):
        super(GraphicsScene, self).__init__ (parent)


class GraphicsCameraFrame(QtGui.QGraphicsPixmapItem):
    def __init__ (self, parent=None):
        super(GraphicsCameraFrame, self).__init__(parent)

    def mousePressEvent(self, event):
        position = QtCore.QPointF(event.pos())
        self.scene().mouseClickedSignal.emit(position.x(), position.y())
        #self.scene().emit(QtCore.SIGNAL("graphicsViewMouseClicked"), position.x(), position.y())
        self.update()  

    def mouseReleaseEvent(self, event):
        position = QtCore.QPointF(event.pos())
        self.scene().mouseReleasedSignal.emit(position.x(), position.y())
        #self.scene().emit(QtCore.SIGNAL("graphicsViewMouseReleased"), position.x(), position.y())
        self.update()
