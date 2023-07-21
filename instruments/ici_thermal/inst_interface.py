#Qt Imports
from PyQt5 import QtCore, QtGui, QtWidgets
try:
    layout_test = QtGui.QVBoxLayout()
except Exception:
    QtGui = QtWidgets   #Compatibility hack

#System Imports
from os import path, makedirs
import logging, ctypes
from time import sleep, time
from datetime import datetime
from shutil import copy2

#MoDaCS Imports
from core.JSONFileField.jsonfilefield import JSONFileField
from core.util import SBlock

#Other Imports
import pyqtgraph as pg
import numpy


class Inst_interface(QtCore.QObject):
    
    #inst_vars.inst_log = logger object
    #inst_vars.inst_cfg = config object
    #inst_wid = instrument widget
    #inst_n = acquisition count
    #instPath = instrument's root folder
    
    inputs = []
    outputs = []
    
    ui_inputs = []
    ui_outputs = ["updateImage"]
        
    #### Event functions ####
        
    def init(self, inst_vars, jsonFF):
        
        self.inst_vars = inst_vars
        self.jsonFF = jsonFF
        self.filePrefix = "Thermal_"
        self.updateDisplay = bool(self.inst_vars.inst_cfg["Initialization"]["UpdateDisplay"])

        #Init camera   
        try:
            copy2(path.join(self.inst_vars.inst_path, 'ici9000.hex'), 'ici9000.hex')    #make sure firmware is in current working dir; should figure out a better way to do this
            ctypes.CDLL("/usr/local/lib/libusb-1.0.so", mode = ctypes.RTLD_GLOBAL)
            ctypes.CDLL("/usr/local/lib/libicisdk.so")
            libpath = path.join(self.inst_vars.inst_path, 'ici9000Pythonlib_v3.so')  
            self.tc = ctypes.cdll.LoadLibrary(libpath)
            self.tc.startCam.restype = ctypes.c_int
            self.tc.stopCam.restype = ctypes.c_void_p
            self.tc.getSize.restype = ctypes.c_int
            self.tc.getWidth.restype = ctypes.c_int
            self.tc.getHeight.restype = ctypes.c_int
            self.tc.loadCal.argtypes = [ctypes.c_char_p]
            self.tc.loadCal.restype = ctypes.c_int
            self.tc.doNUC.restype = ctypes.c_int
            self.tc.getSN.restype = ctypes.c_long
            self.tc.getImage.argtypes = [ctypes.POINTER(ctypes.c_float)]
            #int GetTemps(float* fpaTemp, float* lensTemp, unsigned short* fpaState)
            self.tc.getTemps.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_ushort)]
            self.tc.getTemps.restype = ctypes.c_int
        except Exception as e:
            self.inst_vars.inst_log.error("Error importing library: %s" % e)
            
        try:
            if self.tc.startCam() < 0:
                raise Exception("No cameras found")
        except Exception as e:
            raise Exception("Error starting thermal cam: %s" % e)
            
        
        try:
            self.size = self.tc.getSize()
            self.height = self.tc.getHeight()
            self.width = self.tc.getWidth()
            
            if self.size > (640*480) or self.height==0 or self.width==0:
                raise Exception("Problem with image dimensions")
            
            self.imgbuf = numpy.zeros((self.height, self.width), numpy.float32)
            self.datbuf = (ctypes.c_float * self.size)()
            self.lensTemp = ctypes.c_float()
            self.fpaTemp = ctypes.c_float()
            self.fpaState = ctypes.c_ushort()

             #Load calibration
            self.calPath = self.inst_vars.inst_cfg["Initialization"]["CalibrationFolder"]
            self.inst_vars.inst_log.info("Loading cals from: " + self.calPath)
            retval = self.tc.loadCal(self.calPath.encode())
            self.inst_vars.inst_log.info("Cal load returned: %i" % retval)

            retval = self.tc.doNUC()
            self.inst_vars.inst_log.info("NUC returned: %i" % retval)

        except Exception as e:
            raise Exception("Error setting up thermal camera: %s" % e)
        
        #Create output file
        self.dataFile = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], self.inst_vars.inst_cfg["Data"]["outputFilePrefix"] + "_data.json")
        self.imgPath = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], "Thermal")
        makedirs(path.dirname(self.dataFile), exist_ok=True)
        makedirs(self.imgPath, exist_ok=True)
        
        self.jsonFF.addField("Header")
        self.jsonFF["Header"]["Model"] = self.inst_vars.inst_cfg["InstrumentInfo"]["Model"]
        self.jsonFF["Header"]["Serial Number"] = self.tc.getSN()
        self.jsonFF["Header"]["Height"] = self.height
        self.jsonFF["Header"]["Width"] = self.width
        self.jsonFF["Header"]["Size"] = self.size

        
    def acquire(self):
        #Call instrument acquisition method
        #imageFile = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], str(strftime("%Y-%m-%d_%H%M%S") + "Image_" + str(self.inst_n) + ".x16"))
        self.datbuf[0] = 0
        
        trys = 0
        while  trys < 10:
            t = time()
            self.tc.getImage(self.datbuf)
            self.tc.getTemps(self.fpaTemp, self.lensTemp, self.fpaState)

            if not self.datbuf[0] == 0:

                #Save binary
                imgFile = path.join(self.imgPath, self.filePrefix + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".dat")
                with open(imgFile, 'wb') as out_file:
                    out_file.write(self.datbuf)

                #Save metadata
                meanT = numpy.mean(self.datbuf)
                medT = numpy.median(self.datbuf)
                minT = numpy.min(self.datbuf)
                maxT = numpy.max(self.datbuf)

                rec = {"file": imgFile, "lensTemp": self.lensTemp.value, "fpaTemp": self.fpaTemp.value, "fpaState": self.fpaState.value, "meanTemp": float(meanT), "medTemp": float(medT), "minTemp": float(minT), "maxTemp": float(maxT)}
                self.jsonFF["Data"].write(rec, recnum=self.inst_vars.globalTrigCount, timestamp=t, compact=True)
                
                self.inst_vars.inst_log.info("Lens T: %f\tFPA T: %f\tFPA State: %d,\nMean T: %f\tMedian T: %f\nMin T: %f\tMax T: %f" % (self.lensTemp.value, self.fpaTemp.value, self.fpaState.value, meanT, medT, minT, maxT))
                    
                #Update display #Disabled 7-19-18 Nome
                if self.inst_vars.trigger_source in ("Manual", "Individual") or self.updateDisplay == True:  
                    #numpy.savez_compressed(imgstr, a=self.datbuf)                
                    #self.imgbuf = numpy.frombuffer(self.datbuf, dtype=numpy.float)
                    #self.imgbuf = numpy.reshape(datbuf, (480, 640))
                    self.imgbuf = bytearray()
                    self.imgbuf += self.datbuf
                    self.ui_signals["updateImage"].emit(self.imgbuf)
                break
            else:
                trys += 1
                self.inst_vars.inst_log.warning("Partial or no data received, retrying capture")


        
    def close(self):
        self.jsonFF["Header"]["Images Captured"] = self.inst_vars.inst_n
        self.tc.stopCam()
        
    
    def displayRec(self, recNum):
   
        print("Display thermal image ", recNum)
        try:
            cachedData = self.jsonFF.read_jsonFFcached(self.jsonFF["Data"], recNum, self.inst_vars.inst_n, self.inst_vars.globalTrigCount)
            cachedHeader = self.jsonFF.read_jsonFFcached(self.jsonFF["Header"], recNum, self.inst_vars.inst_n, self.inst_vars.globalTrigCount)
        except KeyError:
            return
        
        imgPath = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], "Thermal")
        
        try:
            imgFile = cachedData[str(recNum)][1]["file"]     #Get filename
        except (TypeError, KeyError):
             imgFile = cachedData[str(recNum)][1]
        
        imgFile = path.join(imgPath, path.split(imgFile)[1])
        self.height = cachedHeader["Height"]
        self.width = cachedHeader["Width"]
        self.size = cachedHeader["Size"]
        
        if (not hasattr(self, "databuf")) or (not hasattr(self, "imgbuf")):
            self.imgbuf = numpy.zeros((self.height, self.width), numpy.float32)
            self.datbuf = (ctypes.c_float * self.size)()
        
        #Load binary
        with open(imgFile, 'rb') as in_file:
            in_file.readinto(self.datbuf)
            
        #Update display
        self.imgbuf = numpy.reshape(self.datbuf, (self.height, self.width))
        self.ui_signals["updateImage"].emit(self.imgbuf)
        
    def fileName(self, val):
        self.filePrefix = val

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
        if self.ui_large:
            data_buf = (ctypes.c_float * (640*480)).from_buffer_copy(data)
            imgbuf = numpy.reshape(data_buf, (480, 640))
            self.imv.setImage(imgbuf.T)
    
    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout()) 
        