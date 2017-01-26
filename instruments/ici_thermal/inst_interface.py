#Qt Imports
from PyQt5 import QtCore, QtGui, QtWidgets

#System Imports
from os import path, makedirs
import logging, ctypes
from time import sleep, time, strftime

#MoDaCS Imports
from util import JSONFileField, SBlock

#Other Imports
import pyqtgraph as pg
import numpy


class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    #inst_wid = instrument widget
    #inst_n = acquisition count
    #instPath = instrument's root folder
    
    inputs = []
    outputs = []
    
    ui_inputs = []
    ui_outputs = ["updateImage"]
        
    #### Event functions ####
        
    def init(self):
        sleep(1)

        #Init camera   
        try:
            libpath = path.join(self.instPath, 'ici9000Pythonlib_v2.so')
            self.tc = ctypes.cdll.LoadLibrary(libpath) 
            self.tc.loadCal.argtypes = [ctypes.c_char_p]
            self.tc.getSN.restype = ctypes.c_long
            self.tc.getImage.argtypes = [ctypes.POINTER(ctypes.c_float)]
        except Exception as e:
            self.instLog.error("Error importing library: %s" % e)
            
        try:
            self.tc.startCam()
        except Exception as e:
            self.instLog.error("Error starting thermal cam: %s" % e)
        
        try:
            
            self.size = self.tc.getSize()
            self.height = self.tc.getHeight()
            self.width = self.tc.getWidth()
            
            if self.size > (640*480) or self.height==0 or self.width==0:
                raise Exception("Problem with image dimensions")
            
            self.imgbuf = numpy.zeros((self.height, self.width), numpy.float)
            self.datbuf = (ctypes.c_float * self.size)()
            
             #Load calibration
            self.calPath = path.join(self.instPath, self.inst_cfg["Initialization"]["CalibrationFolder"])
            self.tc.loadCal(self.calPath.encode())
        except Exception as e:
            raise Exception("Error setting up thermal camera: %s" % e)
        
        #Create output file
        self.dataFile = path.join(self.inst_cfg["Data"]["absolutePath"], "Data", self.inst_cfg["Data"]["outputFilePrefix"] + "_data.json")
        self.imgPath = path.join(self.inst_cfg["Data"]["absolutePath"], "Thermal")
        makedirs(path.dirname(self.dataFile), exist_ok=True)
        makedirs(self.imgPath, exist_ok=True)
        
        self.jsonFF = JSONFileField(self.dataFile)
        self.jsonFF.addElement("Configuration", {s:dict(self.inst_cfg.items(s)) for s in self.inst_cfg.sections()})
        self.jsonFF.addField("Header")
        self.jsonFF["Header"]["Model"] = self.inst_cfg["InstrumentInfo"]["Model"]
        self.jsonFF["Header"]["Serial Number"] = self.tc.getSN()
        self.jsonFF["Header"]["Height"] = self.height
        self.jsonFF["Header"]["Width"] = self.width
        self.jsonFF.addField("Data", fieldType=list)

        
    def acquire(self):
        #Call instrument acquisition method
        #imageFile = path.join(self.inst_cfg["Data"]["absolutePath"], str(strftime("%Y-%m-%d_%H%M%S") + "Image_" + str(self.inst_n) + ".x16"))
        self.datbuf[0] = 0
        
        trys = 0
        while  trys < 3:
            t = time()
            self.tc.getImage(self.datbuf)
            if not self.datbuf[0] == 0:
                break
            else:
                trys += 1
                self.instLog.warning("Partial or no data received, retrying capture")

        #Save metadata
        imgFile = path.join(self.imgPath, "Thermal_" + strftime("%Y%m%d_%H%M%S") + ".dat")
        self.jsonFF["Data"].write(imgFile, recnum=self.globalTrigCount, timestamp=t, compact=True)
        
        #Save binary
        with open(imgFile, 'wb') as out_file:
            out_file.write(self.datbuf)
            
        #Update display
        self.imgbuf = numpy.reshape(self.datbuf, (self.height, self.width))
        self.ui_signals["updateImage"].emit(self.imgbuf)
        
    def close(self):
        self.jsonFF["Header"]["Images Captured"] = self.inst_n
        self.jsonFF.close()
        self.tc.stopCam()
        
        

class Ui_interface(QtCore.QObject):
      
    def init(self):
     
        try:
            self.clearLayout(self.ui.layout1)      #Clear layout if it exists so that instrument resets work properly
        except:
            self.ui.layout1 = QtGui.QVBoxLayout()
            self.ui.layout1.setContentsMargins(0,0,0,0)
            self.ui.pltWidget.setLayout(self.ui.layout1)
            
        self.imv = pg.ImageView()    
        self.ui.layout1.addWidget(self.imv)
        
        self.imv.setPredefinedGradient('thermal')
        if not self.ui_large:
            self.imv.ui.histogram.hide()
            self.imv.ui.roiBtn.hide()
            self.imv.ui.normBtn.hide()
        
        
    def updateImage(self, data):
        self.imv.setImage(data.T)
    
    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout()) 
        