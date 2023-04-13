from time import sleep
from xmlrpc.client import Server
from PyQt5 import QtCore
import threading, datetime, logging, subprocess
from time import time
try:
    import serial, pynmea2
    from ublox_gps import UbloxGps
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
        
        
        if str.lower(self.inst_vars.inst_cfg["Initialization"]["UseHP"]) == "true":
            self.use_HP = True
        else:
            self.use_HP = False
        self.port = self.inst_vars.inst_cfg["Initialization"]["port"]

        try:
            self.t_gps = threading.Thread(target=self.gps_monitor)
            self.t_gps.start()   
        except Exception as e:
            self.inst_vars.inst_log.warning(e)
        
    def acquire(self):
        d = {}
        d["GPS"] = {}
        d["GPS"]["Raw Data"] = str(self.geo)
        d["Global Location"] = {}
        if self.use_HP:
            d["GPS"]["Raw HP Data"] = str(self.hp_geo)
            d["Global Location"]["lat"] = "{:.8f}".format(self.hp_geo.latHp)
            d["Global Location"]["lon"] = "{:.8f}".format(self.hp_geo.latHp)
            d["Global Location"]["alt"] = "{:.8f}".format(self.hp_geo.heightHp)
        else:
            d["Global Location"]["lat"] = "{:.6f}".format(self.geo.lat)
            d["Global Location"]["lon"] = "{:.6f}".format(self.geo.lon)
            d["Global Location"]["alt"] = "{:.6f}".format(self.geo.height/1000)         
        
        self.jsonFF["Data"].write(d, recnum=self.inst_vars.globalTrigCount, timestamp=time(), compact=True)
        
        return
        
    def close(self):
        self.listen = False
        
        
    def gps_monitor(self):
        triggered = False
        led = False
        self.inst_vars.inst_log.info("Listening thread started.")

        ser = serial.Serial(self.port, baudrate=38400, timeout=1)
        gps = UbloxGps(ser)

        try: 
            print("Listenting for UBX Messages.")
            while(self.listen == True):
                try: 
                    gps_time = gps.date_time()
                    self.ui_signals["ui.ts.setText"].emit("{:4d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(gps_time.year, gps_time.month,gps_time.day,gps_time.hour,gps_time.min,gps_time.sec))

                    #self.sats = gps.satellites()
                    self.geo = gps.geo_coords()
                    self.ui_signals["ui.sats.setText"].emit(str(self.geo.numSV))

                    if self.use_HP:
                        self.hp_geo = gps.hp_geo_coords()
                        self.ui_signals["ui.lat.setText"].emit("{:.8f}".format(self.hp_geo.latHp))
                        self.ui_signals["ui.long_2.setText"].emit("{:.8f}".format(self.hp_geo.latHp))   
                        self.ui_signals["ui.alt.setText"].emit("{:.8f}".format(self.hp_geo.heightHp))                     
                    else:
                        self.ui_signals["ui.lat.setText"].emit("{:.6f}".format(self.geo.lat))
                        self.ui_signals["ui.long_2.setText"].emit("{:.6f}".format(self.geo.lon))
                        self.ui_signals["ui.alt.setText"].emit("{:.2f}".format(self.geo.height/10000))

                except (ValueError, IOError) as err:
                    self.inst_vars.inst_log.warning(err)

                except Exception as err:
                    self.inst_vars.inst_log.error(err)
        finally:
            ser.close()
        self.inst_vars.inst_log.info("Listening thread finished.")
              
            
class Ui_interface(QtCore.QObject):
    
    def init(self):
        pass