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
        
        from pylepton import Lepton
        
        self.inst_vars = inst_vars
        self.jsonFF = jsonFF
        
        sleep(1)


        self.height = self.inst_vars.inst_cfg["InstrumentInfo"]["Height"]
        self.width = self.inst_vars.inst_cfg["InstrumentInfo"]["Width"]

  
        #Init camera   
        self.imgbuf = np.ndarray((self.height, self.width, 1), dtype=np.uint16)
        
        try:
            self.lepton = Lepton("/dev/spidev32766.0")
            self.lepton.__enter__()
        except Exception as e:
            self.inst_vars.inst_log.error("Error starting thermal cam: %s" % str(e))

        
        #Create output file
        self.dataFile = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], "Data", self.inst_vars.inst_cfg["Data"]["outputFilePrefix"] + "_data.json")
        self.imgPath = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], "Thermal")
        makedirs(path.dirname(self.dataFile), exist_ok=True)
        makedirs(self.imgPath, exist_ok=True)
        
        self.jsonFF.addField("Header")
        self.jsonFF["Header"]["Height"] = self.inst_vars.inst_cfg["InstrumentInfo"]["Height"]
        self.jsonFF["Header"]["Width"] = self.inst_vars.inst_cfg["InstrumentInfo"]["Width"]

        
    def acquire(self):
 #Call instrument acquisition method
        #imageFile = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], str(strftime("%Y-%m-%d_%H%M%S") + "Image_" + str(self.inst_n) + ".x16"))

        try:
            t = time()

            self.lepton.capture(self.datbuf, debug_print=False)

            #for x in range(0,60):
            #    for y in range(0,80):
            #print(np.array2string(a, formatter={"%5i"}))
            #        print('{0:5d}'.format(a[x][y][0]), end='')
            #    print("\n")
            #sleep(1)
            
        except Exception as e:
            raise e
    
        #Save metadata
        imgFile = path.join(self.imgPath, "Lepton_" + strftime("%Y%m%d_%H%M%S") + ".dat")
        self.jsonFF["Data"].write(imgFile, recnum=self.inst_vars.globalTrigCount, timestamp=t, compact=True)
        
        #Save binary
        with open(imgFile, 'wb') as out_file:
            out_file.write(self.imgbuf.ctypes.data_as(ctypes.c_uint16))
            
        #Update display
        #self.imgbuf = numpy.reshape(self.datbuf, (self.height, self.width))
        self.ui_signals["updateImage"].emit(self.datbuf)
        
    def close(self):
        self.lepton.__exit__(None,None,None)

        
    
    def displayRec(self, recNum):
   
        print("Display thermal image ", recNum)
        try:
            cachedData = self.jsonFF.read_jsonFFcached(self.jsonFF["Data"], recNum, self.inst_vars.inst_n, self.inst_vars.globalTrigCount)
            cachedHeader = self.jsonFF.read_jsonFFcached(self.jsonFF["Header"], recNum, self.inst_vars.inst_n, self.inst_vars.globalTrigCount)
        except KeyError:
            return
        
        imgPath = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], "Thermal")
        
        imgFile = cachedData[str(recNum)][1]     #Get filename
        
        imgFile = path.join(imgPath, path.split(imgFile)[1])
        self.height = cachedHeader["Height"]
        self.width = cachedHeader["Width"]
        
        if (not hasattr(self, "databuf")) or (not hasattr(self, "imgbuf")):
            self.imgbuf = numpy.zeros((self.height, self.width), numpy.uint16)
            self.datbuf = (ctypes.c_uint16 * self.size)()
        
        #Load binary
        with open(imgFile, 'rb') as in_file:
            in_file.readinto(self.datbuf)
            
        #Update display
        self.imgbuf = numpy.reshape(self.datbuf, (self.height, self.width))
        self.ui_signals["updateImage"].emit(self.imgbuf)

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
        