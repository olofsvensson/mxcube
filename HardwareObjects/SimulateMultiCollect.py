import os
import logging
import errno
import abc
import shutil
from HardwareRepository.TaskUtils import *
from HardwareRepository.BaseHardwareObjects import HardwareObject

from AbstractMultiCollect import AbstractMultiCollect




class SimulateMultiCollect(HardwareObject, AbstractMultiCollect):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        HardwareObject.__init__(self, name)
        AbstractMultiCollect.__init__(self)
        self.__last_image_saved = None


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
                                      detector_fileext = self.getProperty("file_suffix"),
                                      detector_type = self.getProperty("type"),
                                      detector_mode = 1,
                                      detector_manufacturer = self.getProperty("manufacturer"),
                                      detector_model = self.getProperty("model"),
                                      detector_px = self.getProperty("px"),
                                      detector_py = self.getProperty("py"),
                                      undulators = None,
                                      focusing_optic = self.getProperty('focusing_optic'),
                                      monochromator_type = self.getProperty('monochromator'),
                                      beam_divergence_vertical = self.getProperty('beam_divergence_vertical'),
                                      beam_divergence_horizontal = self.getProperty('beam_divergence_horizontal'),     
                                      polarisation = self.getProperty('polarisation'),
                                      input_files_server = self.getProperty("input_files_server"))
 
    


    @task
    def data_collection_hook(self, data_collect_parameters):
        fileinfo =  data_collect_parameters["fileinfo"]
        template = fileinfo["template"]
        directory = fileinfo["directory"]
        for oscillation_parameters in data_collect_parameters["oscillation_sequence"]:
            number_of_images = oscillation_parameters["number_of_images"]
            start_image_number = oscillation_parameters["start_image_number"]
            for index in range(number_of_images):
                image_no = index + start_image_number
                image_path = os.path.join(directory, template % image_no)
                logging.info("Simulating collection of image: %s", image_path)
                if template.startswith("line-"):
                    reference_image = "/scisoft/pxsoft/data/WORKFLOW_TEST_DATA/id30a1/20141003/RAW_DATA/MXPressE_01/line-MARK2-m1010713a_2_%04d.cbf" % image_no
                elif  template.startswith("mesh-"):
                    reference_image = "/scisoft/pxsoft/data/WORKFLOW_TEST_DATA/id30a1/20141003/RAW_DATA/MXPressE_01/mesh-MARK2-m1010713a_1_%04d.cbf" % image_no
                else:
                    reference_image = "/scisoft/pxsoft/data/AUTO_PROCESSING/id29_elspeth/tln_1_0001.cbf"
                shutil.copyfile(reference_image, image_path)
                self.__last_image_saved = image_no

    @task
    def set_transmission(self, transmission_percent):
        pass


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
      return self.__last_image_saved

    @task
    def prepare_acquisition(self, take_dark, start, osc_range, exptime, npass, number_of_images, comment):
        pass
      

    @task
    def start_acquisition(self, exptime, npass, first_frame):
        pass


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
      return 1.0


    def get_detector_distance(self):
      return 240.0


    def get_resolution(self):
      return 2.0


    def get_transmission(self):
      return 100.0


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
      return (211.82, 216.24)

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
      pass


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
        pass

