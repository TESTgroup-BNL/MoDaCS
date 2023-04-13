from time import sleep, strftime
from PyQt5 import QtCore, QtGui, QtWidgets
try:
    layout_test = QtGui.QVBoxLayout()
except Exception:
    QtGui = QtWidgets   #Compatibility hack

try:
    import RPi.GPIO as GPIO
    usingRPi = True
except:
    from GPIOEmulator.EmulatorGUI import GPIO
    usingRPi = False
    
import logging
import instruments.lidarlite.lidarlitev2
import pyqtgraph as pg

class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    
    inputs = []
    outputs = []
    
    ui_inputs = []
    ui_outputs = ["distance","signalstrength"]
        
    def init(self, inst_vars):
        
        #self.inst_cfg = inst_vars.inst_cfg
        #self.instLog = inst_vars.inst_log
        #self.inst_wid = inst_vars.inst_wid
        #self.inst_n = inst_vars.inst_n
        #self.inst_path = inst_vars.inst_path
        
        self.ll = lidarlitev2.LidarLite(self.inst_vars.inst_cfg['i2c_address'])
        self.ll.begin(0)
        
    def acquire(self):
        dist = self.ll.distance(False, False)
        sigstrength = self.ll.signalStrength()
        
        #Update UI
        self.ui_signals["distance"].emit(dist)
        self.ui_signals["signalstrength"].emit(sigstrength)
              
    def close(self):
        pass
        
        
class Ui_interface(QtCore.QObject):
    
    distData = QtCore.pyqtSignal(int)
    
    def init(self):
        
        self.pw = pg.PlotWidget(name='Plot1')
        self.layout1 = QtGui.QVBoxLayout()
        self.layout1.setContentsMargins(0,0,0,0)
        self.layout1.addWidget(self.pw)
        self.ui.pltWidget.setLayout(self.layout1)
        
        self.distplot = self.pw.plot()
        self.ui.pltWidget.setContentsMargins(0,0,0,0)
        y_axis = self.pw.getAxis('left')
        y_axis.enableAutoSIPrefix(False)
        y_axis.showLabel(False)
        y_axis.setRange(0, 1)
        y_axis.setWidth(15)

        x_axis = self.pw.getAxis('bottom')
        x_axis.enableAutoSIPrefix(False)
        x_axis.showLabel(True)
        x_axis.setHeight(15)
        self.pw.setLabel('bottom', 'Distance', units='m')
        
        self.pw.getAxis('top').setHeight(5)
        
        self.distData.connect(self.updatePlot)
        
    
    def updatePlot(self, data):       
        self.distplot.setData(y=data)
        