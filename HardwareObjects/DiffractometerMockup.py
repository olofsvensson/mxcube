"""
Descript. :
"""
import os
import copy
import time
import logging
import numpy
import math
import tempfile
import gevent
import random
import shutil
import subprocess
from gevent.event import AsyncResult
from Qub.Tools import QubImageSave
from HardwareRepository import HardwareRepository
from HardwareRepository.TaskUtils import *
from HardwareRepository.BaseHardwareObjects import Equipment
import sample_centring

class myimage:
    """
    Descript. :
    """
    def __init__(self, drawing):
        """
        Descript. :
        """
        self.drawing = drawing
        matrix = self.drawing.matrix()
        self.zoom = 1
        if matrix is not None:
            self.zoom = matrix.m11()
        self.img = self.drawing.getPPP()
        fd, name = tempfile.mkstemp()
        os.close(fd)
        QubImageSave.save(name, self.img, self.drawing.canvas(), self.zoom, "JPEG")
        f = open(name, "r")
        self.imgcopy = f.read()
        f.close()
        os.unlink(name)
    def __str__(self):
        """
        Descript. :
        """
        return self.imgcopy

last_centred_position = [200, 200]

def take_snapshots(number_of_snapshots, light, light_motor, phi, zoom, drawing):
    if number_of_snapshots <= 0:
        return

    centredImages = []
    
    for i, angle in enumerate([-90] * number_of_snapshots):
        logging.getLogger("HWR").info("MiniDiff: taking snapshot #%d", i + 1)
#     centredImages.append((phi.getPosition(),str(myimage(drawing))))
#     phi.syncMoveRelative(angle)

    centredImages.reverse()  # snapshot order must be according to positive rotation direction

    return centredImages

class DiffractometerMockup(Equipment):
    """
    Descript. :
    """
    MANUAL3CLICK_MODE = "Manual 3-click"
    C3D_MODE = "Computer automatic"
    MOVE_TO_BEAM_MODE = "Move to Beam"

    def __init__(self, *args):
        """
        Descript. :
        """
        Equipment.__init__(self, *args)

        self.phiMotor = None
        self.phizMotor = None
        self.phiyMotor = None
        self.lightMotor = None
        self.zoomMotor = None
        self.sampleXMotor = None
        self.sampleYMotor = None
        self.camera = None
        self.beam_info_hwobj = None

        self.beam_position = None
        self.x_calib = None
        self.y_calib = None
        self.pixels_per_mm_x = None
        self.pixels_per_mm_y = None
        self.image_width = None
        self.image_height = None
        self.current_sample_info = None
        self.cancel_centring_methods = None
        self.current_centring_procedure = None
        self.current_centring_method = None
        self.current_positions_dict = None
        self.centring_methods = None
        self.centring_status = None
        self.centring_time = None
        self.user_confirms_centring = None
        self.user_clicked_event = None

        self.connect(self, 'equipmentReady', self.equipmentReady)
        self.connect(self, 'equipmentNotReady', self.equipmentNotReady)

        #IK - this will be sorted out
        self.startCentringMethod = self.start_centring_method 
        self.imageClicked = self.image_clicked
        self.acceptCentring = self.accept_centring
        self.rejectCentring = self.reject_centring

    def init(self):
        """
        Descript. :
        """
        self.x_calib = 0.000444
        self.y_calib = 0.000446
         
        self.pixels_per_mm_x = 1.0 / self.x_calib
        self.pixels_per_mm_y = 1.0 / self.y_calib
        self.beam_position = [200, 200]
        
        self.centring_methods = {
             DiffractometerMockup.MANUAL3CLICK_MODE: self.start_3Click_centring,
             DiffractometerMockup.C3D_MODE: self.start_automatic_centring}
        self.cancel_centring_methods = {}
        self.centring_status = {"valid": False}
        self.centring_time = 0
        self.user_confirms_centring = True
        self.user_clicked_event = AsyncResult()

        try:
          phiz_ref = self["centringReferencePosition"].getProperty("phiz")
        except:
          phiz_ref = None

        self.phiMotor = self.getDeviceByRole('phi')
        self.phizMotor = self.getDeviceByRole('phiz')
        self.phiyMotor = self.getDeviceByRole("phiy")
        self.zoomMotor = self.getDeviceByRole('zoom')
        self.lightMotor = self.getDeviceByRole('light')
        self.focusMotor = self.getDeviceByRole('focus')
        self.sampleXMotor = self.getDeviceByRole("sampx")
        self.sampleYMotor = self.getDeviceByRole("sampy")
        self.camera = self.getDeviceByRole('camera')
        self.kappaMotor = self.getDeviceByRole('kappa')
        self.kappaPhiMotor = self.getDeviceByRole('kappa_phi')
        self.beam_info = self.getObjectByRole('beam_info')

        self.centringPhi=sample_centring.CentringMotor(self.phiMotor, direction=-1)
        self.centringPhiz=sample_centring.CentringMotor(self.phizMotor, reference_position=phiz_ref)
        self.centringPhiy=sample_centring.CentringMotor(self.phiyMotor)
        self.centringSamplex=sample_centring.CentringMotor(self.sampleXMotor)
        self.centringSampley=sample_centring.CentringMotor(self.sampleYMotor)

        self.image_width = 400
        self.image_height = 400

        self.equipmentReady()
        self.user_clicked_event = AsyncResult()

        self.beam_info_hwobj = HardwareRepository.HardwareRepository().\
                                getHardwareObject(self.getProperty("beam_info"))
        if self.beam_info_hwobj is not None:
            self.connect(self.beam_info_hwobj, 'beamPosChanged', self.beam_position_changed)
        else:
            logging.getLogger("HWR").debug('Minidiff: Beaminfo is not defined')

    def getStatus(self):
        """
        Descript. :
        """
        return "ready"

    def manual_centring(self):
        """
        Descript. :
        """
        self.user_clicked_event = AsyncResult()
        x, y = self.user_clicked_event.get()
        last_centred_position[0] = x
        last_centred_position[1] = y
        random_num = random.random()
        centred_pos_dir = {'phiy': random_num * 10, 'phiz': random_num, 
                         'sampx': 0.0, 'sampy': 9.3, 'zoom': 8.53,
                         'phi': 311.1, 'focus': -0.42, 'kappa': 0.0009, 
                         ' kappa_phi': 311.0}
        return centred_pos_dir 		

    def set_sample_info(self, sample_info):
        """
        Descript. :
        """
        self.current_sample_info = sample_info
	
    def emit_diffractometer_moved(self, *args):
        """
        Descript. :
        """
        self.emit("diffractometerMoved", ())
	
    def isReady(self):
        """
        Descript. :
        """ 
        return True

    def isValid(self):
        """
        Descript. :
        """
        return True

    def equipmentReady(self):
        """
        Descript. :
        """
        self.emit('minidiffReady', ())

    def equipmentNotReady(self):
        """
        Descript. :
        """
        self.emit('minidiffNotReady', ())

    def invalidate_centring(self):
        """
        Descript. :
        """
        if self.current_centring_procedure is None and self.centring_status["valid"]:
            self.centring_status = {"valid":False}
            self.emitProgressMessage("")
            self.emit('centringInvalid', ())

    def get_available_centring_methods(self):
        """
        Descript. :
        """
        return self.centring_methods.keys()

    def get_calibration_data(self, offset):
        """
        Descript. :
        """
        #return (1.0 / self.x_calib, 1.0 / self.y_calib)
        return (1.0 / self.x_calib, 1.0 / self.y_calib)

    def get_pixels_per_mm(self):
        """
        Descript. :
        """
        return (self.pixels_per_mm_x, self.pixels_per_mm_y)

    def refresh_omega_reference_position(self):
        """
        Descript. :
        """
        return

#    def get_omega_axis_position(self):	
#        """
#        Descript. :
#        """
#        return self.current_positions_dict.get("phi")     

   
    def get_current_positions_dict(self):
        """
        Descript. :
        """
        return self.current_positions_dict

    def beam_position_changed(self, value):
        """
        Descript. :
        """
        self.beam_position = value
  
    def start_centring_method(self, method, sample_info = None):
        """
        Descript. :
        """
        if self.current_centring_method is not None:
            logging.getLogger("HWR").error("already in centring method %s" %\
                    self.current_centring_method)
            return
        curr_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.centring_status = {"valid": False, "startTime": curr_time}
        self.emit_centring_started(method)
        try:
            fun = self.centring_methods[method]
        except KeyError, diag:
            logging.getLogger("HWR").error("unknown centring method (%s)" % \
                    str(diag))
            self.emit_centring_failed()
        else:
            try:
                fun(sample_info)
            except:
                logging.getLogger("HWR").exception("problem while centring")
                self.emit_centring_failed()

    def cancel_centring_method(self, reject = False):
        """
        Descript. :
        """
        if self.current_centring_procedure is not None:
            try:
                self.current_centring_procedure.kill()
            except:
                logging.getLogger("HWR").exception("problem aborting the centring method")
            try:
                fun = self.cancel_centring_methods[self.current_centring_method]
            except:
                self.emit_centring_failed()
            else:
                try:
                    fun()
                except:
                    self.emit_centring_failed()
        else:
            self.emit_centring_failed()
        self.emit_progress_message("")
        if reject:
            self.reject_centring()

    def get_current_centring_method(self):
        """
        Descript. :
        """ 
        return self.current_centring_method

    def start_3Click_centring(self, sample_info=None):
        """
        Descript. :
        """
        self.emit_progress_message("3 click centring...")
        self.current_centring_procedure = gevent.spawn(self.manual_centring)
        self.current_centring_procedure.link(self.manual_centring_done)	

    def start3ClickCentring(self, sample_info=None):
        self.currentCentringProcedure = sample_centring.start({"phi":self.centringPhi,
                                                               "phiy":self.centringPhiy,
                                                               "sampx": self.centringSamplex,
                                                               "sampy": self.centringSampley,
                                                               "phiz": self.centringPhiz }, 
                                                              self.pixelsPerMmY, self.pixelsPerMmZ, 
                                                              self.getBeamPosX(), self.getBeamPosY())
                                                                         
        self.currentCentringProcedure.link(self.manualCentringDone)

    def start_automatic_centring(self, sample_info = None, loop_only = False):
        """
        Descript. :
        """
        return

    def motor_positions_to_screen(self, centred_positions_dict):
        self.pixelsPerMmY, self.pixelsPerMmZ = self.getCalibrationData(self.zoomMotor.getPosition())
        phi_angle = math.radians(self.centringPhi.direction*self.centringPhi.getPosition()) 
        sampx = self.centringSamplex.direction * (centred_positions_dict["sampx"]-self.centringSamplex.getPosition())
        sampy = self.centringSampley.direction * (centred_positions_dict["sampy"]-self.centringSampley.getPosition())
        phiy = self.centringPhiy.direction * (centred_positions_dict["phiy"]-self.centringPhiy.getPosition())
        phiz = self.centringPhiz.direction * (centred_positions_dict["phiz"]-self.centringPhiz.getPosition())
        rotMatrix = numpy.matrix([math.cos(phi_angle), -math.sin(phi_angle), math.sin(phi_angle), math.cos(phi_angle)])
        rotMatrix.shape = (2, 2)
        invRotMatrix = numpy.array(rotMatrix.I)
        dx, dy = numpy.dot(numpy.array([sampx, sampy]), invRotMatrix)*self.pixelsPerMmY
        beam_pos_x = self.getBeamPosX()
        beam_pos_y = self.getBeamPosY()

        x = (phiy * self.pixelsPerMmY) + beam_pos_x
        y = dy + (phiz * self.pixelsPerMmZ) + beam_pos_y

        return x, y
 
    def manualCentringDone(self, manual_centring_procedure):
        try:
          motor_pos = manual_centring_procedure.get()
          if isinstance(motor_pos, gevent.GreenletExit):
            raise motor_pos
        except:
          logging.exception("Could not complete manual centring")
          self.emitCentringFailed()
        else:
          self.emitProgressMessage("Moving sample to centred position...")
          self.emitCentringMoving()
          try:
            sample_centring.end()
          except:
            logging.exception("Could not move to centred position")
            self.emitCentringFailed()
          
          #logging.info("EMITTING CENTRING SUCCESSFUL")
          self.centredTime = time.time()
          self.emitCentringSuccessful()
          self.emitProgressMessage("")

    def autoCentringDone(self, auto_centring_procedure): 
        self.emitProgressMessage("")
        self.emit("newAutomaticCentringPoint", (-1,-1))

        res = auto_centring_procedure.get()
        
        if isinstance(res, gevent.GreenletExit):
          logging.error("Could not complete automatic centring")
          self.emitCentringFailed()
        else: 
          positions = self.zoomMotor.getPredefinedPositionsList()
          i = len(positions) / 2
          self.zoomMotor.moveToPosition(positions[i-1])

          #be sure zoom stop moving
          while self.zoomMotor.motorIsMoving():
              time.sleep(0.1)

          self.pixelsPerMmY, self.pixelsPerMmZ = self.getCalibrationData(self.zoomMotor.getPosition())

          if self.user_confirms_centring:
            self.emitCentringSuccessful()
          else:
            self.emitCentringSuccessful()
            self.acceptCentring()
    @task
    def move_to_centred_position(self, centred_pos):
        """
        Descript. :
        """
        time.sleep(1)
   
    def moveToCentredPosition(self, centred_position, wait = False):
        """
        Descript. :
        """
        try:
            return self.move_to_centred_position(centred_position, wait = wait)
        except:
            logging.exception("Could not move to centred position")

    def image_clicked(self, x, y, xi, yi): 
        """
        Descript. :
        """
        self.user_clicked_event.set((x, y))
	
    def emit_cetring_started(self, method):
        """
        Descript. :
        """
        self.current_centring_method = method
        self.emit('centringStarted', (method, False))

    def accept_centring(self):
        """
        Descript. :
        """
        self.centring_status["valid"] = True
        self.centring_status["accepted"] = True
        self.emit('centringAccepted', (True, self.get_centring_status()))
	
    def reject_centring(self):
        """
        Descript. :
        """
        if self.current_centring_procedure:
            self.current_centring_procedure.kill()
        self.centring_status = {"valid" : False}
        self.emit_progress_message("")
        self.emit('centringAccepted', (False, self.get_centring_status()))

    def emit_centring_moving(self):
        """
        Descript. :
        """
        self.emit('centringMoving', ())

    def emit_centring_started(self, method):
        """
        Descript. :
        """
        self.current_centring_method = method
        self.emit('centringStarted', (method, False))

    def emit_centring_failed(self):
        """
        Descript. :
        """
        self.centring_status = {"valid" : False}
        method = self.current_centring_method
        self.current_centring_method = None
        self.current_centring_procedure = None
        self.emit('centringFailed', (method, self.get_centring_status()))

    def emit_centring_successful(self):
        """
        Descript. :
        """
        if self.current_centring_procedure is not None:
            curr_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.centring_status["endTime"] = curr_time
            random_num = random.random()
            motors = {'phiy': random_num * 10,  'phiz': random_num*20,
                      'sampx': 0.0, 'sampy': 9.3, 'zoom': 8.53, 'phi': 311.1, 
		      'focus': -0.42, 'kappa': 0.0009, ' kappa_phi': 311.0}

            motors["beam_x"] = 0.1
            motors["beam_y"] = 0.1

            self.centring_status["motors"] = motors
            self.centring_status["method"] = self.current_centring_method
            self.centring_status["valid"] = True

            method = self.current_centring_method
            self.emit('centringSuccessful', (method, self.get_centring_status()))
            self.current_centring_method = None
            self.current_centring_procedure = None
        else:
            logging.getLogger("HWR").debug("trying to emit centringSuccessful outside of a centring")

    def emitProgressMessage(self,msg=None):
        #logging.getLogger("HWR").debug("%s: %s", self.name(), msg)
        self.emit('progressMessage', (msg,))


    def getCentringStatus(self):
        return copy.deepcopy(self.centringStatus)


    def getPositions(self):
      return { "phi": self.phiMotor.getPosition(),
               "focus": self.focusMotor.getPosition(),
               "phiy": self.phiyMotor.getPosition(),
               "phiz": self.phizMotor.getPosition(),
               "sampx": self.sampleXMotor.getPosition(),
               "sampy": self.sampleYMotor.getPosition(),
               "kappa": self.kappaMotor.getPosition() if self.kappaMotor is not None else None,
               "kappa_phi": self.kappaPhiMotor.getPosition() if self.kappaPhiMotor is not None else None,    
               "zoom": self.zoomMotor.getPosition()}
    


    def start_set_phase(self, name):
        """
        Descript. :
        """
        return

    def refresh_video(self):
        """
        Descript. :
        """
        if self.beam_info_hwobj: 
            self.beam_info_hwobj.beam_pos_hor_changed(300) 
            self.beam_info_hwobj.beam_pos_ver_changed(200)

    def start_auto_focus(self): 
        """
        Descript. :
        """
        return 
  
    def move_to_coord(self, x, y):
        """
        Descript. :
        """
        return
     
    def start_2D_centring(self):
        """
        Descript. :
        """
        self.centring_time = time.time()
        curr_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.centring_status = {"valid": True,
                                "startTime": curr_time,
                                "endTime": curr_time} 
        motors = self.getPositions()
        motors["beam_x"] = 0.1
        motors["beam_y"] = 0.1
        self.centring_status["motors"] = motors
        self.centring_status["valid"] = True
        self.centring_status["angleLimit"] = False
        self.emit_progress_message("")
        self.accept_centring()
        self.current_centring_method = None
        self.current_centring_procedure = None  

    def take_snapshots_procedure(self, image_count, drawing):
        """
        Descript. :
        """
        centred_images = []
        for index in range(image_count):
            logging.getLogger("HWR").info("MiniDiff: taking snapshot #%d", index + 1)
            centred_images.append((0, str(myimage(drawing))))
            centred_images.reverse() 
        return centred_images

    def take_snapshots(self, image_count, wait = False):
        """
        Descript. :
        """
        if image_count > 0:
            snapshots_procedure = gevent.spawn(self.take_snapshots_procedure,
                                               image_count, self._drawing)
            self.emit('centringSnapshots', (None,))
            self.emit_progress_message("Taking snapshots")
            self.centring_status["images"] = []
            snapshots_procedure.link(self.snapshots_done)
            if wait:
                self.centring_status["images"] = snapshots_procedure.get()

    def snapshots_done(self, snapshots_procedure):
        """
        Descript. :
        """
        try:
            self.centring_status["images"] = snapshots_procedure.get()
        except:
            logging.getLogger("HWR").exception("EMBLMiniDiff: could not take crystal snapshots")
            self.emit('centringSnapshots', (False,))
            self.emit_progress_message("")
        else:
            self.emit('centringSnapshots', (True,))
            self.emit_progress_message("")
        self.emit_progress_message("Sample is centred!")

    def moveMotors(self, roles_positions_dict):
        motor = { "phi": self.phiMotor,
                  "focus": self.focusMotor,
                  "phiy": self.phiyMotor,
                  "phiz": self.phizMotor,
                  "sampx": self.sampleXMotor,
                  "sampy": self.sampleYMotor,
                  "kappa": self.kappaMotor,
                  "kappa_phi": self.kappaPhiMotor,
                  "zoom": self.zoomMotor }
   
        for role, pos in roles_positions_dict.iteritems():
            m = motor.get(role)
            if m is not None:
                m.move(pos)
 
        # TODO: remove this sleep, the motors states should
        # be MOVING since the beginning (or READY if move is
        # already finished) 
        time.sleep(1)
 
        while not all([m.getState() == m.READY for m in motor.itervalues() if m is not None]):
            time.sleep(0.1)

    
    def takeSnapshots(self, image_count, wait=False):
        self.camera.forceUpdate = True
        
        snapshotsProcedure = gevent.spawn(take_snapshots, image_count, self.lightWago, self.lightMotor ,self.phiMotor,self.zoomMotor,self._drawing)
        self.emit('centringSnapshots', (None,))
        self.emitProgressMessage("Taking snapshots")
        self.centringStatus["images"]=[]
        snapshotsProcedure.link(self.snapshotsDone)

        if wait:
          self.centringStatus["images"] = snapshotsProcedure.get()

 
    def snapshotsDone(self, snapshotsProcedure):
        self.camera.forceUpdate = False
        
        try:
           self.centringStatus["images"] = snapshotsProcedure.get()
        except:
           logging.getLogger("HWR").exception("MiniDiff: could not take crystal snapshots")
           self.emit('centringSnapshots', (False,))
           self.emitProgressMessage("")
        else:
           self.emit('centringSnapshots', (True,))
           self.emitProgressMessage("")
        self.emitProgressMessage("Sample is centred!")
        #self.emit('centringAccepted', (True,self.getCentringStatus()))



    def simulateAutoCentring(self,sample_info=None):
        pass
            
    def save_snapshot(self, filename):
        snapshotReferenceDir = "/scisoft/pxsoft/data/WORKFLOW_TEST_DATA/id30a1/20150123/PROCESSED_DATA/RibBio/RibBio-S9/MXPressE_01"
        phi = self.phiMotor.getPosition()
        phiy = self.phiyMotor.getPosition()
        if phiy > 0.5:
            snapShotFileName = "snapshot_background.png"
        else:
            snapShotFileName = "snapshot_{0:03d}.png".format(int(phi/30)*30)
        snapShotFilePath = os.path.join(snapshotReferenceDir, snapShotFileName)
        fileDirectory = os.path.dirname(filename)
        if fileDirectory.startswith("/data/pyarch"):
            if not os.path.exists(fileDirectory):
                sts = subprocess.Popen("ssh mxedna 'mkdir -p {0}'".format(fileDirectory) , shell=True).wait()
            sts = subprocess.Popen("ssh mxedna 'cp {0} {1}'".format(snapShotFilePath, filename) , shell=True).wait()
        else:
            if not os.path.exists(fileDirectory):
                os.makedirs(fileDirectory)
            shutil.copyfile(snapShotFilePath, filename)
