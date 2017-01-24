from time import sleep, strftime
from PyQt5 import QtCore, QtGui
try:
    import RPi.GPIO as GPIO
    usingRPi = True
except:
    from GPIOEmulator.EmulatorGUI import GPIO
    usingRPi = False
from os.path import isabs
from os import makedirs
import logging
import random
import pyqtgraph as pg

class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    
    inputs = []
    outputs = []
    
    ui_inputs = []
    ui_outputs = ["specData"]
        
    def init(self):
        self.sp = Spec(self.inst_cfg)       #Call instrument init
        self.sp.open()
        self.ui_signals["specData"].connect(lambda: print("TEST"))
        
        
    def acquire(self):
        data = self.sp.get_spec()
        
        aq_type = self.inst_cfg["Acquisition"]["Aq_Type"].replace(" ", "").split(",")
        
        #Update UI
        self.ui_signals["specData"].emit(data)
        
        if "Save" in aq_type:
            if not data == None:
                self.sp.writeData(data)
        
    def close(self):
        self.sp.shutdown()
        self.instLog.info("Spec shutdown")    
        
        
class Ui_interface(QtCore.QObject):
    
    specData = QtCore.pyqtSignal(object)
    
    def init(self):
        
        self.pw = pg.PlotWidget(name='Plot1')
        self.layout1 = QtGui.QVBoxLayout()
        self.layout1.setContentsMargins(0,0,0,0)
        self.layout1.addWidget(self.pw)
        self.ui.pltWidget.setLayout(self.layout1)
        
        self.specplot = self.pw.plot()
        self.ui.pltWidget.setContentsMargins(0,0,0,0)
        y_axis = self.pw.getAxis('left')
        y_axis.enableAutoSIPrefix(False)
        y_axis.showLabel(False)
        y_axis.setRange(0, 1)
        y_axis.setWidth(15)

        x_axis = self.pw.getAxis('bottom')
        x_axis.enableAutoSIPrefix(False)
        x_axis.showLabel(False)
        x_axis.setHeight(15)
        #self.pw.setLabel('bottom', 'Wavelength', units='nm')
        
        self.pw.getAxis('top').setHeight(5)
        
        self.specData.connect(self.updatePlot)
        
    
    def updatePlot(self, data):       
        wls = data[0]
        intens = data[1]
        self.pw.setXRange(min(wls), max(wls))
        self.specplot.setData(x=wls, y=intens)    
        

class Spec:
    
    WL = [None] * 2
    WL[0] = [None] * 256
    WL[1] = [None] * 256
    
    
    def __init__(self, inst_cfg):
        self.inst_cfg = inst_cfg
        self.specLog = logging.getLogger(inst_cfg["InstrumentInfo"]["Name"].replace(" ", "_"))
        
        for i in range(0,257):
            self.WL[0][i-1] = i*2
            self.WL[1][i-1] = i*3
            
    
    def open(self):
        comport = self.inst_cfg["Initialization"]["COM"]
        # Fake init stuff
        self.specLog.info("Opened " + comport)
        
        
    def get_spec(self):
        data = [None] * 2
        data[0] = [None] * 256
        data[1] = [None] * 256
        
        for i in range(0,257):
            data[0][i-1] = random.random()
            data[1][i-1] = random.random()
        
        return data
        
    def writeData(self, data):
        # open output file in appending mode
        path = self.inst_cfg["Data"]["absolutePath"]
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
        self.specLog.info("Closed " + comport)
        
        