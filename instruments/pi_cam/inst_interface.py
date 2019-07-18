from time import sleep
from PyQt5 import QtCore
import threading, datetime, logging, subprocess
from time import time
try:
    import serial, pynmea2
except:
    pass


class Inst_interface(QtCore.QObject):
    
    #inst_vars.inst_log = logger object
    #inst_cfg = config object
    #inst_wid = instrument widget
    
    inputs = []
    outputs = []
    
    ui_inputs = []
    ui_outputs = ["ui.ts.setText","ui.sats.setText","ui.lat.setText","ui.long_2.setText","ui.alt.setText"]
        
    #### Event functions ####
        
    def init(self, inst_vars, jsonFF=None):
        
        self.inst_vars = inst_vars
        self.jsonFF = jsonFF

        self.listen = True
            
        #GPIO.add_event_detect(17, GPIO.RISING, callback=reset, bouncetime=300) 
        
        try:
            self.t_gps = threading.Thread(target=self.gps_monitor)
            self.t_gps.start()   
        except Exception as e:
            self.inst_vars.inst_log.warning(e)
        
    def acquire(self):
        d = {}
        d["GPS"] = {}
        d["GPS"]["satellites_visible"] = self.msg.num_sats
        d["Global Location"] = {}
        d["Global Location"]["lat"] = str(self.msg.latitude)
        d["Global Location"]["long"] = str(self.msg.longitude)
        d["Global Location"]["alt"] = str(self.msg.altitude)
        
        self.jsonFF["Data"].write(d, recnum=self.inst_vars.globalTrigCount, timestamp=time(), compact=True)
        return                          #Call instrument acquisition method
        
    def close(self):
        self.listen = False
        
        
    def gps_monitor(self):
        triggered = False
        led = False
        self.inst_vars.inst_log.info("Listening thread started.")
        
        port = self.inst_vars.inst_cfg["Initialization"]["port"]
        serialPort = serial.Serial(port, baudrate = 9600, timeout = 5)
        
        while(self.listen == True):
            dat = serialPort.readline().decode('utf-8')
            self.parseGPS(dat)
        self.inst_vars.inst_log.info("Listening thread finished.")
        
        
    def parseGPS(self, dat):
        if dat.find('GGA') > 0:
            self.msg = pynmea2.parse(dat)
            self.ui_signals["ui.ts.setText"].emit(self.msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            self.ui_signals["ui.sats.setText"].emit(self.msg.num_sats)
            self.ui_signals["ui.lat.setText"].emit(str(round(self.msg.latitude,6)))
            self.ui_signals["ui.long_2.setText"].emit(str(round(self.msg.longitude,6)))
            self.ui_signals["ui.alt.setText"].emit(str(self.msg.altitude))
            
            
class Ui_interface(QtCore.QObject):
    
    def init(self):
        pass