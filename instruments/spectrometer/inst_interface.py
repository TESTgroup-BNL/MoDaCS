from time import sleep, strftime
from PyQt5 import QtCore
from GPIOEmulator.EmulatorGUI import GPIO
from os.path import isabs
from os import makedirs
import logging
import random

class Inst_obj(QtCore.QObject):
    
    index = 0
    n = 0
    status = QtCore.pyqtSignal(int, str)
    dPath = ""
        
    def __init__(self,params,globalPath,**kwds):     #Inst object init - this is the same for all instruments
        super().__init__(**kwds)
        
        self.inst_cfg = params
        
        if params["Data"]["Destination"] == None or params["Data"]["Destination"] == "":
            self.dPath = globalPath + "\\" + params["InstrumentInfo"]["Name"].replace(" ", "_") + "\\"  #Using global location and default instrument directory
        elif isabs(params["Data"]["Destination"]):
            self.dPath = params["Data"]["Destination"] + "\\"        #Using absolute path from instrument config
        else:
            self.dPath = globalPath + "\\" + params["Data"]["Destination"] + "\\"       #Using global location and relative directory from instrument config
            
        makedirs(self.dPath, exist_ok=True)
        
        self.instLog = logging.getLogger(params["InstrumentInfo"]["Name"].replace(" ", "_"))
        logPath = self.dPath + str(strftime("\\\\%Y-%m-%d_%H%M%S_" + params["InstrumentInfo"]["Name"].replace(" ", "_") + "_Log.txt"))
                
        formatter = logging.Formatter('[%(levelname)s], %(asctime)s, %(message)s')
        formatter.datefmt = '%Y/%m/%d %I:%M:%S'
        fileHandler = logging.FileHandler(logPath, mode='w')
        fileHandler.setFormatter(formatter)
    
        self.instLog.setLevel(logging.DEBUG)
        self.instLog.addHandler(fileHandler)
        self.instLog.propagate = False
        
        
    def init(self):
        self.sp = Spec(self.inst_cfg, self.dPath)       #Call instrument init
        
        self.instLog.info("Init complete")
        self.status.emit(self.index, "Ready")
        
        
    def acquire(self):
        data = self.sp.get_spec()
        
        aq_type = self.inst_cfg["Acquisition"]["Aq_Type"].replace(" ", "").split(",")
        
        if "Log" in aq_type:
            self.instLog.info("Acquisition %i" % self.n)
        if "Save" in aq_type:
            if not data == None:
                self.sp.writeData(self.dPath, data)
        
        self.n += 1
        self.status.emit(self.index, "n=" + str(self.n))
        
    def close(self):
        self.sp.shutdown()
        self.instLog("Spec shutdown")        
        

class Spec:
    
    WL = [None] * 2
    WL[0] = [None] * 256
    WL[1] = [None] * 256
    
    
    def __init__(self, inst_cfg, path):
        self.inst_cfg = inst_cfg
        self.specLog = logging.getLogger(inst_cfg["InstrumentInfo"]["Name"].replace(" ", "_"))
        
        for i in range(0,257):
            self.WL[0][i-1] = i*2
            self.WL[1][i-1] = i*3
            
    
    def open(self):
        comport = int(inst_cfg["Initialization"]["COM"])
        # Fake init stuff
        specLog.info("Opened " + comport)
        
        
    def get_spec(self):
        data = [None] * 2
        data[0] = [None] * 256
        data[1] = [None] * 256
        
        for i in range(0,257):
            data[0][i-1] = random.random()
            data[1][i-1] = random.random()
        
        return data
        
    def writeData(self, path, data):
        # open output file in appending mode
        current_datetime = strftime("%Y-%m-%d__%H_%M_%S")
        filename = 'Uni_' + current_datetime  + '.spu' #+ '_' + station
    
        
        print("Writing file: " + filename)    
        fh = open(path + r'\\' + filename, "a")
    
        # write file header
        #fh.write('"File:    "' + data + r'\\' + filename + '"\n') 
        fh.write('"Remarks:    Data recorded directly to PC using python script 3-13-15"\n') 
        fh.write('"Time:    ' + strftime("%Y-%m-%d  %H:%M:%S") +  '"\n') 
        fh.write('"Limits_Ch_A:     ' + str(self.WL[1][0]) + ' - ' + str(self.WL[1][255]) + '\tLimits_Ch_B:     ' + str(self.WL[0][0]) + ' - ' + str(self.WL[0][247]) + '"\n') 
        fh.write('"GPS:     LAT= Ukn     LON=Ukn     ALT=Ukn     Updated=Ukn"\n')
        fh.write('"Station#: ' + self.inst_cfg["InstrumentInfo"]["Station"] + '"\n')
        fh.write('"Ch_B_WL    Ch_B_Value    Ch_A_WL    Ch_A_Value"\n')
        
        
        print("CH B: " + str(len(data[0])) + " values\tCH A: " + str(len(data[1])) + " values\n")
    
        i = 0
        for i in range(0, 256):
            dat_out = str(self.WL[0][i]) + "\t" + str(data[0][i]) + "\t" + str(self.WL[1][i]) + "\t" + str(data[1][i]) + "\n"
            fh.write(dat_out)
            #print(dat_out)
            
        fh.flush()
        fh.close()
        print("File Closed.")  
        
    def shutdown(self):
        specLog.info("Closed " + comport)
        
        