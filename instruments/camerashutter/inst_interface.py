from time import sleep, strftime
from PyQt5 import QtCore
from GPIOEmulator.EmulatorGUI import GPIO
from os.path import isabs
from os import makedirs
import logging

class Inst_obj(QtCore.QObject):
    
    status = QtCore.pyqtSignal(int, str)
    finished = QtCore.pyqtSignal()
        
    def __init__(self,params,globalPath):     #Inst object init - this is the same for all instruments
        super().__init__()
        
        self.index = 0
        self.n = 0
        
        self.inst_cfg = params
        
        if params["Data"]["Destination"] == None or params["Data"]["Destination"] == "":
            dPath = globalPath + "\\" + params["InstrumentInfo"]["Name"].replace(" ", "_") + "\\"  #Using global location and default instrument directory
        elif isabs(params["Data"]["Destination"]):
            dPath = params["Data"]["Destination"] + "\\"        #Using absolute path from instrument config
        else:
            dPath = globalPath + "\\" + params["Data"]["Destination"] + "\\"       #Using global location and relative directory from instrument config
            
        makedirs(dPath, exist_ok=True)
        
        self.inst_cfg["Data"]["dPath"] = dPath
        
        self.instLog = logging.getLogger(params["InstrumentInfo"]["Name"].replace(" ", "_"))
        logPath = dPath + str(strftime("\\\\%Y-%m-%d_%H%M%S_" + params["InstrumentInfo"]["Name"].replace(" ", "_") + "_Log.txt"))
                
        formatter = logging.Formatter('[%(levelname)s] (%(threadName)-10s), %(asctime)s, %(message)s')
        formatter.datefmt = '%Y/%m/%d %I:%M:%S'
        fileHandler = logging.FileHandler(logPath, mode='w')
        fileHandler.setFormatter(formatter)
    
        self.instLog.setLevel(logging.DEBUG)
        self.instLog.addHandler(fileHandler)
        self.instLog.propagate = False
        
        
    def init(self):
        self.cs = CameraShutter(self.inst_cfg)       #Call instrument init
        
        self.instLog.info("Init complete")
        self.status.emit(self.index, "Ready")
        
        
    def acquire(self):
        self.cs.snapshot()                          #Call instrument acquisition method
        self.instLog.info("Snapshot %i" % self.n)
        
        self.n += 1
        self.status.emit(self.index, "n=" + str(self.n))
        
    def close(self):
        self.cs.shutdown()
        self.instLog("Camera shutdown")        
        

class CameraShutter:
    
    def __init__(self, inst_cfg):
        self.shutter = int(inst_cfg["Initialization"]["shutterpin"])
        GPIO.setmode(GPIO.BCM)       
        GPIO.setup(self.shutter, GPIO.OUT)
        GPIO.output(self.shutter, False)
        
    def snapshot(self):
        GPIO.output(self.shutter, True)
        sleep(.1)
        GPIO.output(self.shutter, False)
        
    def shutdown(self):
        GPIO.output(self.shutter, False)
        
        