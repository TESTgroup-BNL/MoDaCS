#Qt Imports
from PyQt5 import QtCore, QtGui, QtWidgets

#System Imports
from time import sleep, time
from os import path, makedirs
import importlib

#MoDaCS Imports
from util import JSONFileField, SBlock

#Other Imports
import pyqtgraph as pg
from numpy import interp

class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    
    inputs = []
    outputs = []
    
    ui_inputs = ["ui.cb_correctNonlin.stateChanged", "ui.cb_correctDark.stateChanged", "ui.sb_intTime.valueChanged", "ui.pb_aqRef.released", "ui.pb_remlast.released", "ui.pb_remlast.released"]
    ui_outputs = ["updatePlot", "setWavelengths", "updateIntTime", "updateDarkCounts", "updateNonlin"]

    #### Required Functions ####
    def init(self):
        import seabreeze.spectrometers as sb
    
        #Read config
        self.int_time = int(self.inst_cfg["Initialization"]["IntegrationTime"])
        self.correct_dark = bool(self.inst_cfg["Initialization"]["CorrectDarkCounts"])
        self.correct_nonlin = bool(self.inst_cfg["Initialization"]["CorrectNonlinearity"])    
        
        #Set up spec
        devices = sb.list_devices()
        self.instLog.info("Devices found: %s" % devices)
        if len(devices) == 0:
            raise Exception("No devices found.")
            return

        devs = {}
        try:
            for d in devices:
                if self.inst_cfg["Initialization"]["UpwardDevice"] in str(d):
                    devs["Upward"] = d
                if self.inst_cfg["Initialization"]["DownwardDevice"] in str(d):
                    devs["Downward"] = d
        except:
            raise Exception("Upward and downward devices not defined, check inst_cfg.ini")
        
        try:
            self.instLog.info("Upward device:  %s" % devs["Upward"])
        except:
            raise Exception("Upward device not found!")
        
        try:
            self.instLog.info("Downward device:  %s" % devs["Downward"])
        except:
            raise Exception("Downward device not found!")
        
        self.specs = {}
        try:
            self.specs["Upward"] = sb.Spectrometer(devs["Upward"])
            self.specs["Downward"] = sb.Spectrometer(devs["Downward"])
        except:
            raise Exception("Error setting up Seabreeze interface")
        
        #Create output file
        self.dataFile = path.join(self.inst_cfg["Data"]["absolutePath"], "Data", self.inst_cfg["Data"]["outputFilePrefix"] + "_data.json")
        makedirs(path.dirname(self.dataFile), exist_ok=True)
        self.jsonFF = JSONFileField(self.dataFile)
        self.jsonFF.addElement("Configuration", {s:dict(self.inst_cfg.items(s)) for s in self.inst_cfg.sections()})
        self.jsonFF.addField("References", fieldType=list)
        self.jsonFF.addField("Data", fieldType=list)
        
        #Create header
        self.wavelengths = {}
        header = self.jsonFF.addField("Header")
        for key, spec in self.specs.items():
            h = header.addField(key)
            h["Device"] = str(devs[key])
            h["PixelCount"] = spec.pixels
            h["Model"] = spec.model
            self.wavelengths[key] = list(spec.wavelengths())
            h.addElement("Wavelengths", self.wavelengths[key], compact=True)
            
        #Define reference variables
        self.refs = {"Upward": [], "Downward": []}
        self.refAvg = {}
        
        #Set up UI  
        self.ui_signals["ui.sb_intTime.valueChanged"].connect(self.intTimeChanged)
        self.ui_signals["ui.cb_correctDark.stateChanged"].connect(self.correctDarkChanged)
        self.ui_signals["ui.cb_correctNonlin.stateChanged"].connect(self.correctNonlinChanged)
        self.ui_signals["ui.pb_aqRef.released"].connect(lambda: self.acquire(getRef=True))
        self.ui_signals["ui.pb_remlast.released"].connect(self.remLastRef)
        self.ui_signals["setWavelengths"].emit(self.wavelengths)                
         
         #Setup remote update connections        
        self.ui_signals["ui.sb_intTime.valueChanged"].connect(self.ui_signals["updateIntTime"].emit)
        self.ui_signals["ui.cb_correctDark.stateChanged"].connect(self.ui_signals["updateDarkCounts"].emit)
        self.ui_signals["ui.cb_correctNonlin.stateChanged"].connect(self.ui_signals["updateNonlin"].emit)
        
        #Create process pool for simultaneous sampling
        #self.pool = Pool(2)
        
            
    def acquire(self, getRef=False):
        
        #Read intensities
        intensities = {}
#         st = time()
#         intensities = pool.map(self.getIntensitiesList, self.specs)
#          
#         print(time()-st)
        t = time()
        for key, spec in self.specs.items():
            intensities[key] = self.getIntensitiesList(spec)

        options = {"IntegrationTime":self.int_time, "CorrectDarkCounts":self.correct_dark, "CorrectNonlinearity":self.correct_nonlin}

        #Save data
        if getRef:
            self.jsonFF["References"].write(intensities, timestamp=t, compact=True)
            
            #Update UI
            for key, intens in intensities.items():
                self.refs[key].append(intens)
                self.refs_avg = self.avgRefs(self.refs)
            self.ui_signals["updatePlot"].emit([self.refs_avg, True, len(self.refs["Downward"])])  #Note: using the 'Downward' list is purely arbitrary since both lists will be the same length, we just need the length of either one

        else:
            if hasattr(self, 'refs_avg'):
            #Calculate reflectance
                upward_interp = interp(self.wavelengths["Downward"], self.wavelengths["Upward"], intensities["Upward"])
                upward_ref_interp = interp(self.wavelengths["Downward"], self.wavelengths["Upward"], self.refs_avg["Upward"]) 
                reflec = (upward_ref_interp/self.refs_avg["Downward"])*(intensities["Downward"]/upward_interp)
                
                #Save data
                ### python >=3.5 only ### self.jsonFF["Data"].write({**intensities, **{"Reflectance":list(reflec)}}, timestamp=t, compact=True)
                self.jsonFF["Data"].write({"Downward":intensities["Downward"], "Upward":intensities["Upward"], "Reflectance":list(reflec), "Options":options}, recnum=self.globalTrigCount, timestamp=t, compact=True)
            else:
                self.instLog.warning("No reference values recorded yet; reflectance not calculated in real-time.")
                reflec = []
                #Save data without reflectance
                self.jsonFF["Data"].write({"Downward":intensities["Downward"], "Upward":intensities["Upward"], "Options":options}, recnum=self.globalTrigCount, timestamp=t, compact=True)
    
            #Update UI
            self.ui_signals["updatePlot"].emit([intensities, False, reflec])

        
    def close(self):
        #self.jsonwriter.close()
        for spec in self.specs.values():
            try:
                spec.close()
            except:
                raise
        self.jsonFF.close()
        del specs
                    
        
    ### Other Instrument Functions/Classes ###
    
    def getIntensitiesList(self, spec):
        return list(spec.intensities(correct_dark_counts=self.correct_dark, correct_nonlinearity=self.correct_nonlin))

    def intTimeChanged(self, newTime):
        for spec in self.specs.values():
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
        
    def remLastRef(self):
        try:
            for key, ref in self.refs.items():
                ref.pop()
        except:
            pass            
        intensities = self.avgRefs(self.refs)
        #Update UI
        self.ui_signals["updatePlot"].emit([intensities, True, len(self.refs["Downward"])])

    
    def avgRefs(self, refs):
        refAvg = {}
        #Calc new average
        for key in refs.keys():
            refAvg[key] = [sum(col)/len(col) for col in zip(*refs[key])]
        return refAvg
        

class Ui_interface(QtCore.QObject):
    
    def init(self):
         
        self.wls = {}
        
        self.pw_down = pg.PlotWidget(name='PlotDown')
        self.pw_up = pg.PlotWidget(name='PlotUp')
        self.pw_reflec = pg.PlotWidget(name='PlotReflec')
        self.ui.vWidget = QtWidgets.QWidget()
        
        try:
            self.clearLayout(self.ui.layout1)      #Clear layout if it exists so that instrument resets work properly
        except:          
            self.ui.layout1 = QtGui.QHBoxLayout()
            self.ui.layout1.setContentsMargins(0,3,0,3)
            
        self.ui.vWidget.setLayout(self.ui.layout1)
            
        try:
            self.clearLayout(self.ui.layout2)      #Clear layout if it exists so that instrument resets work properly
        except:
            self.ui.layout2 = QtGui.QVBoxLayout()
            self.ui.layout2.setContentsMargins(3,0,3,0)
            
        self.ui.pltWidget.setLayout(self.ui.layout2)
        self.ui.pltWidget.setContentsMargins(0,0,0,0)
        
        self.ui.layout1.addWidget(self.pw_down)
        self.ui.layout1.addWidget(self.pw_up)
        
        self.ui.layout2.addWidget(self.pw_reflec)
        self.ui.layout2.addWidget(self.ui.vWidget)
        
        self.setupSpecPlot(self.pw_down, (1/65535))
        self.setupSpecPlot(self.pw_up, (1/65535))
        self.setupSpecPlot(self.pw_reflec, 1)
        
        self.refplot = {}
        self.specplot = {}
        self.refplot["Upward"] = self.pw_up.plot(pen=(0,2))
        self.specplot["Upward"] = self.pw_up.plot(pen=(1,2))
        self.refplot["Downward"] = self.pw_down.plot(pen=(0,2))
        self.specplot["Downward"] = self.pw_down.plot(pen=(1,2))
        
        self.reflecplot = self.pw_reflec.plot(pen=(0,1))
    
    
    def setupSpecPlot(self, plot, scale):
        x_axis = plot.getAxis('bottom')
        y_axis = plot.getAxis('left')
        
        if self.ui_large:
            x_axis.setHeight(25)
            x_axis.setLabel('Wavelength', units='nm')
            plot.getAxis('top').setHeight(5)
        else:
            x_axis.setHeight(0) 
            y_axis.setWidth(0)
            plot.getAxis('top').setHeight(3)
            
        x_axis.enableAutoSIPrefix(False)
        x_axis.showLabel(False)    
            
        y_axis.enableAutoSIPrefix(False)
        y_axis.showLabel(False)
        y_axis.setRange(0, 1)
        y_axis.setScale(scale)
            #y_axis.setWidth(25)

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())        
        
    def updatePlot(self, data):    
        intens = data[0]
        isRef = data[1]
                
        for key, inten in intens.items():            
            if isRef:
                l = data[2]
                self.ui.lbl_refcount.setNum(l)
                if l > 0:
                    self.refplot[key].setData(x=self.wls[key], y=inten) 
                else:
                    self.refplot[key].setData(x=[], y=[])
            else:
                self.specplot[key].setData(x=self.wls[key], y=inten)
                
        if not isRef:
            try:
                self.reflecplot.setData(x=self.wls["Downward"], y=data[2])
            except:
                pass
                
    def setWavelengths(self, wls):
        self.wls = wls
        x_range = (min([min(wls["Upward"]), min(wls["Downward"])]), max([max(wls["Upward"]), max(wls["Downward"])]))
        self.pw_down.setXRange(*x_range)
        self.pw_up.setXRange(*x_range)
        self.pw_reflec.setXRange(*x_range)
        


    #Check remote changes
    def updateIntTime(self, value):
        with SBlock(self.ui.sb_intTime) as b:
            b.setValue(value)
             
    def updateDarkCounts(self, value):
        with SBlock(self.ui.cb_correctDark) as b:
            b.setCheckState(value)
         
    def updateNonlin(self, value):
        with SBlock(self.ui.cb_correctNonlin) as b:
            b.setCheckState(value)
                   