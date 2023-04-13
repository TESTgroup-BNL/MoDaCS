#Qt Imports
from PyQt5 import QtCore, QtGui, QtWidgets
try:
    layout_test = QtGui.QVBoxLayout()
except Exception:
    QtGui = QtWidgets   #Compatibility hack
    
#System Imports
from time import sleep, time
from os import path, makedirs
#MoDaCS Imports
from util import JSONFileField
#Other Imports
import seabreeze.spectrometers as sb
import pyqtgraph as pg

class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    
    inputs = []
    outputs = []
    
    ui_inputs = ["ui.sb_intTime.valueChanged", "ui.cb_correctDark.stateChanged", "ui.cb_correctNonlin.stateChanged", "ui.pb_aqRef.released", "ui.pb_remlast.released"]
    ui_outputs = ["updatePlot"]
        
    #### Required Functions ####
    def init(self, inst_vars):
        
        self.inst_cfg = inst_vars.inst_cfg
        self.instLog = inst_vars.inst_log
        self.inst_wid = inst_vars.inst_wid
        self.inst_n = inst_vars.inst_n
        self.inst_path = inst_vars.inst_path
        
        
        #Read config
        self.int_time = int(self.inst_cfg["Initialization"]["IntegrationTime"])
        self.correct_dark = bool(self.inst_cfg["Initialization"]["CorrectDarkCounts"])
        self.correct_nonlin = bool(self.inst_cfg["Initialization"]["CorrectNonlinearity"])        
        
        #Set up spec
        devices = sb.list_devices()
        self.instLog.info("Devices found: %s" % devices)
        if len(devices) == 0:
            self.error = "No devices found."
        self.instLog.info("Using %s" % devices[0])
        global spec
        spec = sb.Spectrometer(devices[0])
        
        #Create output file
        self.dataFile = path.join(self.inst_cfg["Data"]["absolutePath"], "Data", self.inst_cfg["Data"]["outputFilePrefix"] + "_data.json")
        makedirs(path.dirname(self.dataFile), exist_ok=True)
        self.jsonFF = JSONFileField(self.dataFile)
        self.jsonFF.addElement("Configuration", {s:dict(self.inst_cfg.items(s)) for s in self.inst_cfg.sections()})
        self.jsonFF.addField("References", fieldType=list)
        self.jsonFF.addField("Data", fieldType=list)
        
        #Create header
        header = self.jsonFF.addField("Header")
        header["Device"] = str(devices[0])
        header["PixelCount"] = spec.pixels
        header["Model"] = spec.model
        self.wavelengths = list(spec.wavelengths())
        header.addElement("Wavelengths", self.wavelengths, compact=True)
        
        #Set up UI
        self.ui_signals["ui.sb_intTime.valueChanged"].connect(self.intTimeChanged)
        self.ui_signals["ui.cb_correctDark.stateChanged"].connect(self.correctDarkChanged)
        self.ui_signals["ui.cb_correctNonlin.stateChanged"].connect(self.correctNonlinChanged)
        self.ui_signals["ui.pb_aqRef.released"].connect(lambda: self.acquire(getRef=True))
        
            
    def acquire(self, getRef=False):
        #Read intensities
        intensities = list(spec.intensities(correct_dark_counts=self.correct_dark, correct_nonlinearity=self.correct_nonlin))
        
        #Save data
        if getRef:
            self.jsonFF["References"].write(intensities, timestamp=time(), compact=True)
        else:
            self.jsonFF["Data"].write(intensities, recnum=self.globalTrigCount, timestamp=time(), compact=True)
        
        #Update UI
        self.ui_signals["updatePlot"].emit([self.wavelengths, intensities, getRef])
        
    def close(self):
        #self.jsonwriter.close()
        self.jsonFF.close()
        spec.close()
        
    ### Other Instrument Functions/Classes ###
    def intTimeChanged(self, newTime):
        spec.integration_time_micros(newTime)
        self.instLog.info("Integration time changed to: %i" % newTime)
        
    def correctDarkChanged(self, value):
        if value == 0:
            self.correct_dark = False
        else:
            self.correct_dark = True
        self.instLog.info("Use dark correction: %i" % self.correct_dark)
        
    def correctNonlinChanged(self, value):
        if value == 0:
            self.correct_nonlin = False
        else:
            self.correct_nonlin = True
        self.instLog.info("Use nonlinearity correction: %i" % self.correct_nonlin)
        

class Ui_interface():
    
    #specData = QtCore.pyqtSignal(object)
    
    def init(self):
        self.refs = []
        
        self.pw = pg.PlotWidget(name='Plot1')
        try:
            self.clearLayout(self.ui.layout1)      #Clear layout if it exists so that instrument resets work properly
        except:
            self.ui.layout1 = QtGui.QVBoxLayout()
            self.ui.layout1.setContentsMargins(0,0,0,0)
            self.ui.pltWidget.setLayout(self.ui.layout1)
            
        self.ui.layout1.addWidget(self.pw)
        
        self.refplot = self.pw.plot(pen=(0,2))
        self.specplot = self.pw.plot(pen=(1,2))
        
        self.ui.pltWidget.setContentsMargins(0,0,0,0)
        y_axis = self.pw.getAxis('left')
        y_axis.enableAutoSIPrefix(False)
        y_axis.showLabel(False)
        y_axis.setRange(0, 1)
        #y_axis.setStyle(tickTextOffset=-30)
        #y_axis.setTicks([(0,"0"),(65535,"65535")])
        y_axis.setScale(1/65535)
        y_axis.setWidth(25)

        x_axis = self.pw.getAxis('bottom')
        x_axis.enableAutoSIPrefix(False)
        x_axis.showLabel(False)
        x_axis.setHeight(15)
        #self.pw.setLabel('bottom', 'Wavelength', units='nm')
        
        self.pw.getAxis('top').setHeight(5)
        
        self.ui.pb_remlast.released.connect(self.remLastRef, QtCore.Qt.UniqueConnection)
        #self.specData.connect(self.updatePlot)
        
    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())
                    
    def remLastRef(self):
        try:
            self.refs.pop()
            self.updateRef()
        except:
            pass
        
    def updateRef(self):
        l = len(self.refs)
        self.ui.lbl_refcount.setNum(l)
        if l > 0:
            self.refAvg = [sum(col)/len(col) for col in zip(*self.refs)]
            self.refplot.setData(x=self.refwls, y=self.refAvg) 
        else:
            self.refplot.setData(x=[], y=[])
        
    def updatePlot(self, data):    
        wls = data[0]
        intens = data[1]
        isRef = data[2]
        
        self.pw.setXRange(min(wls), max(wls)) 
        
        if isRef:
            self.refs.append(intens)
            self.refwls = wls
            self.updateRef()
        else:
            self.specplot.setData(x=wls, y=intens)
             