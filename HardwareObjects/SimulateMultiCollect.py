import os
import logging
import errno
import abc
import shutil
import httplib
from HardwareRepository.TaskUtils import *
from HardwareRepository.BaseHardwareObjects import HardwareObject

from AbstractMultiCollect import AbstractMultiCollect




class SimulateMultiCollect(HardwareObject, AbstractMultiCollect):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        HardwareObject.__init__(self, name)
        AbstractMultiCollect.__init__(self)
        self._last_image_saved = None
        self._beam_centre_x = 211.82
        self._beam_centre_y = 216.24
        self._detector_distance = 240.0
        self._resolution = 2.0
        self._wavelength = 1.0
        self._detector_px = 2463
        self._detector_py = 2527
        self._max_number_of_frames = 740


    def init(self):
        self.setControlObjects(diffractometer = self.getObjectByRole("diffractometer"),
                               sample_changer = self.getObjectByRole("sample_changer"),
                               lims = self.getObjectByRole("dbserver"),
                               safety_shutter = self.getObjectByRole("safety_shutter"),
                               machine_current = self.getObjectByRole("machine_current"),
                               cryo_stream = self.getObjectByRole("cryo_stream"),
                               energy = self.getObjectByRole("energy"),
                               resolution = self.getObjectByRole("resolution"),
                               detector_distance = self.getObjectByRole("detector_distance"),
                               transmission = self.getObjectByRole("transmission"),
                               undulators = self.getObjectByRole("undulators"),
                               flux = self.getObjectByRole("flux"),
                               detector = self.getObjectByRole("detector"),
                               beam_info = self.getObjectByRole("beam_info"))

        self.setBeamlineConfiguration(directory_prefix = self.getProperty("directory_prefix"),
                                      default_exposure_time = self.getProperty("default_exposure_time"),
                                      minimum_exposure_time = self.getProperty("minimum_exposure_time"),
                                      detector_fileext = self.getProperty("detector_fileext"),
                                      detector_type = self.getProperty("detector_type"),
                                      detector_mode = 1,
                                      detector_manufacturer = self.getProperty("detector_manufacturer"),
                                      detector_model = self.getProperty("detector_model"),
                                      detector_px = self.getProperty("detector_px"),
                                      detector_py = self.getProperty("detector_py"),
                                      undulators = None,
                                      focusing_optic = self.getProperty('focusing_optic'),
                                      monochromator_type = self.getProperty('monochromator'),
                                      beam_divergence_vertical = self.getProperty('beam_divergence_vertical'),
                                      beam_divergence_horizontal = self.getProperty('beam_divergence_horizontal'),     
                                      polarisation = self.getProperty('polarisation'),
                                      input_files_server = self.getProperty("input_files_server"))
 
    


    @task
    def data_collection_hook(self, data_collect_parameters):
        self._data_collect_parameters = data_collect_parameters
        fileinfo =  data_collect_parameters["fileinfo"]
        template = fileinfo["template"]
        directory = fileinfo["directory"]
        run_number = int(fileinfo["run_number"])
        oscillation_parameters = self._data_collect_parameters["oscillation_sequence"][0]
        number_of_images = oscillation_parameters["number_of_images"]
        if number_of_images > self._max_number_of_frames:
            number_of_images = self._max_number_of_frames
            oscillation_parameters["number_of_images"] = self._max_number_of_frames
            self.emit("collectNumberOfFrames", number_of_images) 
        start_image_number = oscillation_parameters["start_image_number"]
        first_image_no = start_image_number
        reference_image = None
        if "BurnStrategy" in directory:
            if  template.startswith("ref-"):
                reference_image = "/data/id23eh1/inhouse/mxihr6/20150121/RAW_DATA/Guillaume/Cer/BurnStrategy_01/ref-x_1_%04d.cbf" % first_image_no
            elif  template.startswith("burn-"):
                wedgeNumber = int(template.split("_")[-3].split("w")[-1])
                reference_image = "/data/id23eh1/inhouse/mxihr6/20150121/RAW_DATA/Guillaume/Cer/BurnStrategy_01/burn-xw%d_1_%04d.cbf" % (wedgeNumber, first_image_no)                    
        elif template.startswith("line-"):
            reference_image = "/data/id30a1/inhouse/opid30a1/20141114/RAW_DATA/opid30a1/6-1-2/MXPressE_02/line-opid30a1_%d_%04d.cbf" % (run_number, first_image_no)
        elif  template.startswith("mesh-"):
#                    reference_image = "/scisoft/pxsoft/data/WORKFLOW_TEST_DATA/id30a1/20141003/RAW_DATA/MXPressE_01/mesh-MARK2-m1010713a_1_%04d.cbf" % image_no
            reference_image = "/data/id30a1/inhouse/opid30a1/20141114/RAW_DATA/opid30a1/6-1-2/MXPressE_02/mesh-opid30a1_1_%04d.cbf" % first_image_no
        elif  template.startswith("ref-"):
            reference_image = "/data/id30a1/inhouse/opid30a1/20141114/RAW_DATA/opid30a1/6-1-2/MXPressE_02/ref-opid30a1_4_%04d.cbf" % first_image_no
        if reference_image is None:
            reference_image = "/data/id30a1/inhouse/opid30a1/20141114/RAW_DATA/opid30a1/6-1-2/opid30a1_1_%04d.cbf" % first_image_no
        # Read the header
        dictHeader = self.readHeaderPilatus(reference_image)
        self.update_beamline_config(dictHeader)
        oscillation_parameters["range"] = float(dictHeader["Angle_increment"].split(" ")[0])
                
        # Update detector info
        try:
            self.bl_control.lims.store_data_collection(data_collect_parameters, self.bl_config)
        except:
            logging.getLogger("HWR").exception("Could not update data collection in LIMS")
            


    def update_beamline_config(self, dictHeader):
        # Beam centre
        listBeamXY = dictHeader["Beam_xy"].replace("(", "").replace(")",",").split(",")
        self._beam_centre_x = float(listBeamXY[1])*0.172
        self._beam_centre_y = float(listBeamXY[0])*0.172
        # Flux
        self._flux = float(dictHeader["Flux"].split(" ")[0])
        # Wavelength
        self._wavelength = float(dictHeader["Wavelength"].split(" ")[0])
        # Detector distance
        self._detector_distance = float(dictHeader["Detector_distance"].split(" ")[0])*1000.0
        # Detector
        detector_fileext = "cbf"
        detector_manufacturer = "DECTRIS"
        detector_type = "pilatus"
        if dictHeader["Detector:"] == "PILATUS 6M, S/N 60-0116-F, ESRF ID23":
            detector_model = "Pilatus_6M_F" 
            self._detector_px = 2463
            self._detector_py = 2527
        elif dictHeader["Detector:"] == "PILATUS 6M, S/N 60-0104, ESRF ID29":
            detector_model = "Pilatus_6M_F" 
            self._detector_px = 2463
            self._detector_py = 2527
        elif dictHeader["Detector:"] == "PILATUS3 6M, S/N 60-0128, ESRF ID29":
            detector_model = "Pilatus3_6M" 
            self._detector_px = 2463
            self._detector_py = 2527
        elif dictHeader["Detector:"] == "PILATUS3 2M, S/N 24-0118, ESRF ID30" or \
             dictHeader["Detector:"] == "PILATUS2 3M, S/N 24-0118, ESRF ID23":
            detector_model = "Pilatus3_2M" 
            self._detector_px = 1475
            self._detector_py = 1679
        else:
            # Unknown detector...
            return
            
            
        self.setBeamlineConfiguration(directory_prefix = self.getProperty("directory_prefix"),
                                      default_exposure_time = self.getProperty("default_exposure_time"),
                                      minimum_exposure_time = self.getProperty("minimum_exposure_time"),
                                      detector_fileext = detector_fileext,
                                      detector_type = detector_type,
                                      detector_mode = 1,
                                      detector_manufacturer = detector_manufacturer,
                                      detector_model = detector_model,
                                      detector_px = self._detector_px,
                                      detector_py = self._detector_py,
                                      undulators = None,
                                      focusing_optic = self.getProperty('focusing_optic'),
                                      monochromator_type = self.getProperty('monochromator'),
                                      beam_divergence_vertical = self.getProperty('beam_divergence_vertical'),
                                      beam_divergence_horizontal = self.getProperty('beam_divergence_horizontal'),     
                                      polarisation = self.getProperty('polarisation'),
                                      input_files_server = self.getProperty("input_files_server"))        



    def readHeaderPilatus(self, _strImageFileName):
        """
        Returns an dictionary with the contents of a Pilatus CBF image header.
        """
        dictPilatus = None
        imageFile = open(_strImageFileName, "r")
        imageFile.seek(0, 0)
        bContinue = True
        iMax = 60
        iIndex = 0
        while bContinue:
            strLine = imageFile.readline()
            iIndex += 1
            if (strLine.find("_array_data.header_contents") != -1):
                dictPilatus = {}
            if (strLine.find("_array_data.data") != -1) or iIndex > iMax:
                bContinue = False
            if (dictPilatus != None) and (strLine[0] == "#"):
                # Check for date
                strTmp = strLine[2:].replace("\r\n", "")
                if strLine[6] == "/" and strLine[10] == "/":
                    dictPilatus["DateTime"] = strTmp
                else:
                    strKey = strTmp.split(" ")[0]
                    strValue = strTmp.replace(strKey, "")[1:]
                    dictPilatus[strKey] = strValue
        imageFile.close()
        return dictPilatus


    @task
    def set_transmission(self, transmission_percent):
        self.bl_control.transmission.setTransmission(transmission_percent)


    @task
    def set_wavelength(self, wavelength):
        pass


    @task
    def set_resolution(self, new_resolution):
      pass


    @task
    def set_energy(self, energy):
      pass   


    @task
    def close_fast_shutter(self):
        pass


    @task
    def move_detector(self, distance):
        pass


    @task
    def move_motors(self, motor_position_dict):
        return


    @task
    def open_safety_shutter(self):
        pass

   
    def safety_shutter_opened(self):
        return False


    @task
    def close_safety_shutter(self):
        pass


    @task
    def prepare_intensity_monitors(self):
        pass


    @task
    def prepare_oscillation(self, start, osc_range, exptime, npass):
        """Should return osc_start and osc_end positions -
        gonio should be ready for data collection after this ;
        Remember to check for still image if range is too small !
        """
        return (start, start+osc_range)


    @task
    def do_oscillation(self, start, end, exptime, npass):
        pass


    @task
    def set_detector_filenames(self, frame_number, start, filename, jpeg_full_path, jpeg_thumbnail_full_path):
      pass

    @task
    def last_image_saved(self):
      return self._last_image_saved

    @task
    def prepare_acquisition(self, take_dark, start, osc_range, exptime, npass, number_of_images, comment):
        pass
      
    def prepare_wedges_to_collect(self, start, nframes, osc_range, subwedge_size=1, overlap=0):
        if nframes > self._max_number_of_frames:
            nframes = self._max_number_of_frames
        if overlap == 0:
            wedge_sizes_list = [nframes//subwedge_size]*subwedge_size
        else:
            wedge_sizes_list = [subwedge_size]*(nframes//subwedge_size)
        remaining_frames = nframes % subwedge_size
        if remaining_frames:
            wedge_sizes_list.append(remaining_frames)
        
        wedges_to_collect = []

        for wedge_size in wedge_sizes_list:
            orig_start = start
            
            wedges_to_collect.append((start, wedge_size))
            start += wedge_size*osc_range - overlap

        return wedges_to_collect
    
    @task
    def start_acquisition(self, exptime, npass, first_frame):
        fileinfo = self._data_collect_parameters["fileinfo"]
        template = fileinfo["template"]
        directory = fileinfo["directory"]
        run_number = int(fileinfo["run_number"])
        for oscillation_parameters in self._data_collect_parameters["oscillation_sequence"]:
            number_of_images = oscillation_parameters["number_of_images"]
            start_image_number = oscillation_parameters["start_image_number"]
            for index in range(number_of_images):
                image_no = index + start_image_number
                image_path = os.path.join(directory, template % image_no)
                logging.info("Simulating collection of image: %s", image_path)
                if "BurnStrategy" in image_path:
                    if  template.startswith("ref-"):
                        reference_image = "/data/id23eh1/inhouse/mxihr6/20150121/RAW_DATA/Guillaume/Cer/BurnStrategy_01/ref-x_1_%04d.cbf" % image_no
                    elif  template.startswith("burn-"):
                        wedgeNumber = int(template.split("_")[-3].split("w")[-1])
                        reference_image = "/data/id23eh1/inhouse/mxihr6/20150121/RAW_DATA/Guillaume/Cer/BurnStrategy_01/burn-xw%d_1_%04d.cbf" % (wedgeNumber, image_no)                    
                elif template.startswith("line-"):
                    reference_image = "/data/id30a1/inhouse/opid30a1/20141114/RAW_DATA/opid30a1/6-1-2/MXPressE_02/line-opid30a1_%d_%04d.cbf" % (run_number, image_no)
                elif  template.startswith("mesh-"):
#                    reference_image = "/scisoft/pxsoft/data/WORKFLOW_TEST_DATA/id30a1/20141003/RAW_DATA/MXPressE_01/mesh-MARK2-m1010713a_1_%04d.cbf" % image_no
                    reference_image = "/data/id30a1/inhouse/opid30a1/20141114/RAW_DATA/opid30a1/6-1-2/MXPressE_02/mesh-opid30a1_1_%04d.cbf" % image_no
                elif  template.startswith("ref-"):
                    reference_image = "/data/id30a1/inhouse/opid30a1/20141114/RAW_DATA/opid30a1/6-1-2/MXPressE_02/ref-opid30a1_4_%04d.cbf" % image_no
                else:
                    reference_image = "/data/id30a1/inhouse/opid30a1/20141114/RAW_DATA/opid30a1/6-1-2/opid30a1_1_%04d.cbf" % image_no
                shutil.copyfile(reference_image, image_path)
                self._last_image_saved = image_no



    @task
    def stop_acquisition(self):
      # detector's readout
      pass


    @task
    def write_image(self, last_frame):
        pass


    @task
    def reset_detector(self):
        pass


    @task
    def data_collection_cleanup(self):
        pass


    def get_wavelength(self):
        return self._wavelength


    def get_detector_distance(self):
        return self._detector_distance


    def get_resolution(self):
        return self._resolution


    def get_transmission(self):
        return self.bl_control.transmission.getAttFactor()


    def get_undulators_gaps(self):
      return []


    def get_resolution_at_corner(self):
      return 1.6


    def get_beam_size(self):
      return (0.1, 0.1)


    def get_slit_gaps(self):
      return (0.1, 0.1)


    def get_beam_shape(self):
      return "elliptical"

    def get_beam_centre(self):
        return (self._beam_centre_x, self._beam_centre_y)

    def get_measured_intensity(self):
      return 1e11


    def get_machine_current(self):
      return 200.0

    def get_machine_fill_mode(self):
      return ""

    
    def get_machine_message(self):
      pass


    def get_cryo_temperature(self):
      pass


    def get_flux(self):
      """Return flux in photons/second"""
      return self._flux


    def store_image_in_lims(self, frame, first_frame, last_frame):
        if first_frame or last_frame:
            return True
        else:
            return False     

    @task
    def take_crystal_snapshots(self, number_of_snapshots):
      pass

       
    def set_helical(self, helical_on):
      pass


    def set_helical_pos(self, helical_pos):
      pass

 
    def get_archive_directory(self, directory):
        res = None
       
        dir_path_list = directory.split(os.path.sep)
        try:
            suffix_path=os.path.join(*dir_path_list[4:])
        except TypeError:
            return None
        else:
            if 'inhouse' in directory:
                archive_dir = os.path.join('/data/pyarch/', dir_path_list[2], suffix_path)
            else:
                archive_dir = os.path.join('/data/pyarch/', dir_path_list[4], dir_path_list[3], *dir_path_list[5:])
        if archive_dir[-1] != os.path.sep:
            archive_dir += os.path.sep
            
        return archive_dir


    def prepare_input_files(self, files_directory, prefix, run_number, process_directory):
        """Return XDS input file directory"""
        i = 1

        while True:
          xds_input_file_dirname = "xds_%s_run%s_%d" % (prefix, run_number, i)
          xds_directory = os.path.join(process_directory, xds_input_file_dirname)

          if not os.path.exists(xds_directory):
            break

          i+=1

        mosflm_input_file_dirname = "mosflm_%s_run%s_%d" % (prefix, run_number, i)
        mosflm_directory = os.path.join(process_directory, mosflm_input_file_dirname)

        hkl2000_dirname = "hkl2000_%s_run%s_%d" % (prefix, run_number, i)
        hkl2000_directory = os.path.join(process_directory, hkl2000_dirname)

        self.raw_data_input_file_dir = os.path.join(files_directory, "process", xds_input_file_dirname)
        self.mosflm_raw_data_input_file_dir = os.path.join(files_directory, "process", mosflm_input_file_dirname)
        self.raw_hkl2000_dir = os.path.join(files_directory, "process", hkl2000_dirname)

        for dir in (self.raw_data_input_file_dir, xds_directory):
          self.create_directories(dir)
          logging.info("Creating XDS processing input file directory: %s", dir)
          os.chmod(dir, 0777)
        for dir in (self.mosflm_raw_data_input_file_dir, mosflm_directory):
          self.create_directories(dir)
          logging.info("Creating MOSFLM processing input file directory: %s", dir)
          os.chmod(dir, 0777)
        for dir in (self.raw_hkl2000_dir, hkl2000_directory):
          self.create_directories(dir)
          os.chmod(dir, 0777)
 
        try: 
          try: 
              os.symlink(files_directory, os.path.join(process_directory, "links"))
          except os.error, e:
              if e.errno != errno.EEXIST:
                  raise
        except:
            logging.exception("Could not create processing file directory")

        return xds_directory, mosflm_directory, hkl2000_directory


    @task
    def write_input_files(self, collection_id):
        # copy *geo_corr.cbf* files to process directory
        try:
            process_dir = os.path.join(self.xds_directory, "..")
            raw_process_dir = os.path.join(self.raw_data_input_file_dir, "..")
            for dir in (process_dir, raw_process_dir):
                for filename in ("x_geo_corr.cbf.bz2", "y_geo_corr.cbf.bz2"):
                    dest = os.path.join(dir,filename)
                    if os.path.exists(dest):
                        continue
                    shutil.copyfile(os.path.join("/data/id23eh1/inhouse/opid231", filename), dest)
        except:
            logging.exception("Exception happened while copying geo_corr files")

        # assumes self.xds_directory and self.mosflm_directory are valid
        conn = httplib.HTTPConnection(self.bl_config.input_files_server)

        # hkl input files 
        for input_file_dir, file_prefix in ((self.raw_hkl2000_dir, "../.."), (self.hkl2000_directory, "../links")): 
            hkl_file_path = os.path.join(input_file_dir, "def.site")
            conn.request("GET", "/def.site/%d?basedir=%s" % (collection_id, file_prefix))
            hkl_file = open(hkl_file_path, "w")
            r = conn.getresponse()

            if r.status != 200:
                logging.error("Could not create input file")
            else:
                hkl_file.write(r.read())
            hkl_file.close()
            os.chmod(hkl_file_path, 0666)

        for input_file_dir, file_prefix in ((self.raw_data_input_file_dir, "../.."), (self.xds_directory, "../links")): 
            xds_input_file = os.path.join(input_file_dir, "XDS.INP")
            conn.request("GET", "/xds.inp/%d?basedir=%s" % (collection_id, file_prefix))
            r = conn.getresponse()
            if r.status != 200:
                logging.error("Could not create input file")
            else:
                strXml = r.read()
#                logging.error("XDS.INP: {0}\n{1}".format(xds_input_file, strXml))
                xds_file = open(xds_input_file, "w")
                xds_file.write(strXml)
                xds_file.close()
                os.chmod(xds_input_file, 0666)

        for input_file_dir, file_prefix in ((self.mosflm_raw_data_input_file_dir, "../.."), (self.mosflm_directory, "../links")): 
            mosflm_input_file = os.path.join(input_file_dir, "mosflm.inp")
            conn.request("GET", "/mosflm.inp/%d?basedir=%s" % (collection_id, file_prefix))
            mosflm_file = open(mosflm_input_file, "w")
            mosflm_file.write(conn.getresponse().read()) 
            mosflm_file.close()
            os.chmod(mosflm_input_file, 0666)
        
        # also write input file for STAC
        for stac_om_input_file_name, stac_om_dir in (("mosflm.descr", self.mosflm_directory),
                                                     ("xds.descr", self.xds_directory),
                                                     ("mosflm.descr", self.mosflm_raw_data_input_file_dir),
                                                     ("xds.descr", self.raw_data_input_file_dir)):
            stac_om_input_file = os.path.join(stac_om_dir, stac_om_input_file_name)
            conn.request("GET", "/stac.descr/%d" % collection_id)
            stac_om_file = open(stac_om_input_file, "w")
            stac_template = conn.getresponse().read()
            if stac_om_input_file_name.startswith("xds"):
                om_type = "xds"
                if stac_om_dir == self.raw_data_input_file_dir:
                    om_filename = os.path.join(stac_om_dir, "CORRECT.LP")
                else:
                    om_filename = os.path.join(stac_om_dir, "xds_fastproc", "CORRECT.LP")
            else:
                om_type = "mosflm"
                om_filename = os.path.join(stac_om_dir, "bestfile.par")
       
            stac_om_file.write(stac_template.format(omfilename=om_filename, omtype=om_type,
                             phi=self.bl_control.diffractometer.getPositions()["phi"],
                             sampx=self.bl_control.diffractometer.getPositions()["sampx"],
                             sampy=self.bl_control.diffractometer.getPositions()["sampy"],
                             phiy=self.bl_control.diffractometer.getPositions()["sampx"]))
            stac_om_file.close()
            os.chmod(stac_om_input_file, 0666)

