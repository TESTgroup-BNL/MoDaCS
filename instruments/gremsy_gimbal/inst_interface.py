from time import sleep, time
from os import path, makedirs
import ctypes

from PyQt5 import QtCore
    
from util import JSONFileField


class Inst_interface():
    
    #inst_vars.inst_log = logger object
    #inst_vars.inst_cfg = config object
    #inst_wid = instrument widget
    #inst_vars.inst_n = acquisition count
    
    inputs = ["orientation"]
    outputs = []

    ui_inputs = ["ui.pb_off.released","ui.pb_mon.released","ui.pb_down.released","ui.pb_up.released"]
    ui_outputs = ["ui.pitch.setText","ui.roll.setText","ui.yaw.setText"]
        
    #### Event functions ####
        
    def init(self, inst_vars, jsonFF):
        
        self.inst_vars = inst_vars
        self.jsonFF = jsonFF
        
        try:
            libpath = path.join(self.inst_vars.inst_path, 'libgSDKlib.so')
            self.glib = ctypes.cdll.LoadLibrary(libpath) 

            GimbalInterface = ctypes.POINTER(ctypes.c_char)
            SerialInterface = ctypes.POINTER(ctypes.c_char)
            cfloats = ctypes.c_float*3
            self.att = cfloats()

            self.glib.createGimbalInterface.argtypes = [SerialInterface]
            self.glib.createGimbalInterface.restype = GimbalInterface

            self.glib.createSerialInterface.argtypes = [ctypes.c_char_p, ctypes.c_int]
            self.glib.createSerialInterface.restype = SerialInterface

            self.glib.destroyGimbalInterface.argtypes = [GimbalInterface]
            self.glib.destroyGimbalInterface.restype = ctypes.c_void_p

            self.glib.destroySerialInterface.argtypes = [SerialInterface]
            self.glib.destroySerialInterface.restype = ctypes.c_void_p

            self.glib.stop.argtypes = [GimbalInterface, SerialInterface]
            self.glib.stop.restype = ctypes.c_void_p

            self.glib.setPower.argtypes = [GimbalInterface, ctypes.c_bool]
            self.glib.setPower.restype = ctypes.c_void_p

            self.glib.setTilt.argtypes = [GimbalInterface, ctypes.c_bool]
            self.glib.setTilt.restype = ctypes.c_void_p

            self.glib.getAttitude.argtypes = [GimbalInterface, ctypes.POINTER(ctypes.c_float * 3)]
            self.glib.getAttitude.restype = ctypes.c_void_p
        except Exception as e:
            self.inst_vars.inst_log.error("Error importing library: %s" % e)
            
        try:
            self.inst_vars.inst_log.info("Starting gimbal interface...")
            self.port = self.glib.createSerialInterface(ctypes.c_char_p(self.inst_vars.inst_cfg["Initialization"]["port"].encode()), 115200)
            self.gimbal = self.glib.createGimbalInterface(self.port)
            sleep(15)
        except Exception as e:
            self.inst_vars.inst_log.error("Error starting gimbal: %s" % e)

        # Set up UI
        self.ui_signals["ui.pb_off.released"].connect(lambda: self.motor_power(False))
        self.ui_signals["ui.pb_mon.released"].connect(lambda: self.motor_power(True))
        
        self.ui_signals["ui.pb_down.released"].connect(lambda: self.set_tilt(False))
        self.ui_signals["ui.pb_up.released"].connect(lambda: self.set_tilt(True))

    def motor_power(self, enabled):
        if enabled:
            self.inst_vars.inst_log.info("Setting motors on")
        else:
            self.inst_vars.inst_log.info("Setting motors off")
        self.glib.setPower(self.gimbal, enabled)

    def set_tilt(self, tilt_up):
        if tilt_up:
            self.inst_vars.inst_log.info("Setting tilt up")
        else:
            self.inst_vars.inst_log.info("Setting tilt down")
        self.glib.setTilt(self.gimbal, tilt_up)

    def acquire(self):
        att = self.get_attitude()
        self.jsonFF["Data"].write(att, recnum=self.inst_vars.globalTrigCount, timestamp=time(), compact=True)
        self.ui_signals["ui.pitch.setText"].emit("{:.2f}".format(att["pitch"]))
        self.ui_signals["ui.roll.setText"].emit("{:.2f}".format(att["roll"]))
        self.ui_signals["ui.yaw.setText"].emit("{:.2f}".format(att["yaw"]))

    def close(self):
        self.glib.stop(self.gimbal, self.serial)
        sleep(5)
        self.glib.destroyGimbalInterface(self.gimbal)
        self.glib.destroySerialInterface(self.port)

    def get_attitude(self):
        self.glib.getAttitude(self.gimbal, ctypes.byref(self.att))
        att_dict = {"pitch": self.att[0], "roll": self.att[1], "yaw": self.att[2]}
        return att_dict


class Ui_interface(QtCore.QObject):
      
    def init(self):
        pass
    