#Qt Imports
from PyQt5 import QtCore, QtGui, QtWidgets

#System Imports
from time import sleep, time
from os import path, makedirs
from datetime import datetime
import importlib, json

#MoDaCS Imports
from inst_common import Inst_jsonFF
from util import SBlock

#Other Imports
import pyqtgraph as pg
from numpy import interp, asarray

class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    
    inputs = []
    outputs = []
    
    #UI Inputs and Outputs are forwarded to remote clients and can access to the ui class
    #but otherwise are the same as "standard" inputs and outputs
    ui_inputs = ["ui.cb_correctNonlin.stateChanged", "ui.pb_DarkCurrent.released", "ui.sb_intTime.valueChanged", "ui.pb_aqRef.released", "ui.pb_remlast.released", "ui.pb_remlast.released"]
    ui_outputs = ["updatePlot", "setWavelengths", "updateIntTime", "updateNonlin"]

    #### Required Functions ####
    def init(self, inst_vars, jsonFF):
        
        self.inst_vars = inst_vars
        self.jsonFF = jsonFF
        
        import seabreeze.spectrometers as sb
    
        #Read config
        self.int_time = int(self.inst_vars.inst_cfg["Initialization"]["IntegrationTime"])
        self.correctDark = False #bool(self.inst_vars.inst_cfg["Initialization"]["CorrectDarkCounts"])
        self.correct_nonlin = bool(self.inst_vars.inst_cfg["Initialization"]["CorrectNonlinearity"])    
        
        #Set up spec
        devices = sb.list_devices()
        self.inst_vars.inst_log.info("Devices found: %s" % devices)
        if len(devices) == 0:
            raise Exception("No devices found.")
            return

        devs = {}
        try:
            for d in devices:
                if self.inst_vars.inst_cfg["Initialization"]["UpwardDevice"] in str(d):
                    devs["Upward"] = d
                if self.inst_vars.inst_cfg["Initialization"]["DownwardDevice"] in str(d):
                    devs["Downward"] = d
        except:
            raise Exception("Upward and downward devices not defined, check inst_cfg.ini")
        
        try:
            self.inst_vars.inst_log.info("Upward device:  %s" % devs["Upward"])
        except:
            raise Exception("Upward device not found!")
        
        try:
            self.inst_vars.inst_log.info("Downward device:  %s" % devs["Downward"])
        except:
            raise Exception("Downward device not found!")
        
        self.specs = {}
        try:
            self.specs["Upward"] = sb.Spectrometer(devs["Upward"])
            self.specs["Downward"] = sb.Spectrometer(devs["Downward"])
        except:
            raise Exception("Error setting up Seabreeze interface")
        

        #Create header
        self.wavelengths = {}
        header = self.jsonFF.addField("Header")
        for key, spec in self.specs.items():
            h = header.addField(key)
            h["Device"] = str(devs[key])
            h["PixelCount"] = spec.pixels
            h["Model"] = spec.model
            self.wavelengths[key] = list(spec.wavelengths())
        try:
            self.samplesPerPoint = int(self.inst_vars.inst_cfg["Initialization"]["SamplesPerPoint"])
        except KeyError:
            self.samplesPerPoint = 1
        self.inst_vars.inst_log.info("Samples per point: %i" % self.samplesPerPoint)
        header.addElement("SamplesPerPoint", self.samplesPerPoint)
        self.jsonFF.addElement("Wavelengths", self.wavelengths, compact=True) 
        self.jsonFF.addField("References", fieldType=list)
        self.jsonFF.addField("DarkCurrent", fieldType=list) 
         
        #Define reference variables
        self.refs = {}
        self.refs_avg = {}
        
        #Define dark current variable and attempt to load
        self.darkCurrent = {}
        dc_filePath = path.join(self.inst_vars.inst_path, 'DarkCurrent.json')
        try:
            self.inst_vars.inst_log.info("Reading saved dark current values...")
            dc_file = open(dc_filePath, 'r')
            dc_data = json.load(dc_file)
            dc_file.close()

            for dc_int_time_str, dc_itm in dc_data.items():
                dc_int_time = int(dc_int_time_str)
                dc_dt = datetime.fromtimestamp(dc_itm["Timestamp"])
                self.darkCurrent[dc_int_time] = dc_itm["intensities"]
                options = dc_itm["Options"]
                self.inst_vars.inst_log.info("%i uS from %s %s" % (dc_int_time, dc_dt.strftime('%Y-%m-%d'), dc_dt.strftime('%H:%M:%S')))
                self.jsonFF["DarkCurrent"].write({"Downward":self.darkCurrent[dc_int_time]["Downward"], "Upward":self.darkCurrent[dc_int_time]["Upward"], "Options":options}, recnum=dc_int_time, timestamp=dc_itm["Timestamp"], compact=True)
        except IOError:
            self.inst_vars.inst_log.warning("No dark current data available.  Measure to correct in real-time.")
        
        #Set up UI  
        self.ui_signals["ui.sb_intTime.valueChanged"].connect(self.intTimeChanged)
        self.ui_signals["ui.pb_DarkCurrent.released"].connect(self.setDarkCurrent)
        self.ui_signals["ui.cb_correctNonlin.stateChanged"].connect(self.correctNonlinChanged)
        self.ui_signals["ui.pb_aqRef.released"].connect(lambda: self.acquire(getRef=True))
        self.ui_signals["ui.pb_remlast.released"].connect(self.remLastRef)
        self.ui_signals["setWavelengths"].emit(self.wavelengths)                
         
         #Setup remote update connections        
        self.ui_signals["ui.sb_intTime.valueChanged"].connect(self.ui_signals["updateIntTime"].emit)
        self.ui_signals["ui.cb_correctNonlin.stateChanged"].connect(self.ui_signals["updateNonlin"].emit)
        
        self.intTimeChanged(self.int_time)
        #Create process pool for simultaneous sampling
        #self.pool = Pool(2)
        
            
    def acquire(self, getRef=False, setDark=False):
        
        #Read intensities
        intensitySamps = [] #{"Upward": [], "Downward": []}
#         st = time()
#         intensities = pool.map(self.getIntensitiesList, self.specs)
#          
#         print(time()-st)
        t = time()
        if setDark:
            samps = 20
        else:
            samps = self.samplesPerPoint

        for i in range(0, samps):
            intensitySamp = {}
            for key, spec in self.specs.items():
                intensitySamp[key] = self.getIntensitiesList(spec)
                
            intensitySamps.append(intensitySamp)
            
        intensities = self.avgSamples(intensitySamps)

        options = {"IntegrationTime":self.int_time, "CorrectNonlinearity":self.correct_nonlin}

        #Save data
        if getRef:
            self.jsonFF["References"].write(intensities, recnum=self.int_time, timestamp=t, compact=True)
            self.inst_vars.inst_log.info("Set white reference!")
            
            #Update UI
            #for key, intens in intensities.items():
            if self.correctDark:
                ref_temp = self.doCorrectDark(intensities, self.darkCurrent, self.int_time)   
            else:
                ref_temp = intensities
            try:
                self.refs[self.int_time].append(ref_temp)
            except KeyError:
                self.refs[self.int_time] = []
                self.refs[self.int_time].append(ref_temp)
                
            self.refs_avg[self.int_time] = self.avgSamples(self.refs[self.int_time])
            self.upward_ref_interp = interp(self.wavelengths["Downward"], self.wavelengths["Upward"], self.refs_avg[self.int_time]["Upward"])
            self.ui_signals["updatePlot"].emit([self.refs_avg[self.int_time], True, len(self.refs[self.int_time]), self.wavelengths])  #Note: using the 'Downward' list is purely arbitrary since both lists will be the same length, we just need the length of either one

        elif setDark:
            self.darkCurrent[self.int_time] = intensities
            self.inst_vars.inst_log.info("Set dark current integration time %i uS" % self.int_time)
            self.jsonFF["DarkCurrent"].write({"Downward":intensities["Downward"], "Upward":intensities["Upward"], "Options":options}, recnum=self.int_time, timestamp=t, compact=True)
            
            #Create output file & header
            dc_filePath = path.join(self.inst_vars.inst_path, 'DarkCurrent.json')
            try:
                dc_file = open(dc_filePath, 'r')
                dc_data = json.load(dc_file)
                dc_file.close()
            except IOError:
                dc_data = {}
            dc_file = open(dc_filePath, 'w')
            dc_data[self.int_time] = {"Timestamp": t, "Options":options, "intensities": intensities}
            json.dump(dc_data, dc_file)
            dc_file.close()
            self.inst_vars.inst_log.info("Dark current data saved in %s for integration time %i uS." % (dc_filePath, self.int_time))
            
        else:
            #Raw spec data is always saved without any dark current correction.  Reflectance is calculated with dark current correction if available.
            #Spec plots are always displayed with dark current correction if available BUT SAVED AS RAW, UNCORRECTED
        
            output = {}
            if hasattr(self, 'refs_avg'):
                #Calculate reflectance
                if self.correctDark:
                    corrected_intensities = self.doCorrectDark(intensities, self.darkCurrent, self.int_time)
                    #print(corrected_intensities)
                    reflec = self.calcReflectance(self.wavelengths, self.refs_avg[self.int_time], corrected_intensities, self.upward_ref_interp)
                    #Update UI
                    self.ui_signals["updatePlot"].emit([corrected_intensities, False, reflec, self.wavelengths])
                else:
                    reflec = self.calcReflectance(self.wavelengths, self.refs_avg[self.int_time], intensities, self.upward_ref_interp)
                    #Update UI
                    self.ui_signals["updatePlot"].emit([intensities, False, reflec, self.wavelengths])
                    
                #Save data
                ### python >=3.5 only ### self.jsonFF["Data"].write({**intensities, **{"Reflectance":list(reflec)}}, timestamp=t, compact=True)
                output = {"Downward":intensities["Downward"], "Upward":intensities["Upward"], "Reflectance":list(reflec), "Options":options}
                self.jsonFF["Data"].write(output, recnum=self.inst_vars.globalTrigCount, timestamp=t, compact=True)

            else:
                self.inst_vars.inst_log.warning("No reference values recorded yet; reflectance not calculated in real-time.")
                reflec = []
                #Save data without reflectance
                self.jsonFF["Data"].write({"Downward":intensities["Downward"], "Upward":intensities["Upward"], "Options":options}, recnum=self.inst_vars.globalTrigCount, timestamp=t, compact=True)
                
                if self.correctDark:
                    corrected_intensities = self.doCorrectDark(intensities, self.darkCurrent, self.int_time)
                    #Update UI
                    self.ui_signals["updatePlot"].emit([corrected_intensities, False, reflec, self.wavelengths])
                else:
                    #Update UI
                    self.ui_signals["updatePlot"].emit([intensities, False, reflec, self.wavelengths])

    def close(self):
        #self.jsonwriter.close()
        for spec in self.specs.values():
            try:
                spec.close()
            except:
                raise
        try:
            self.jsonFF.close()
        except Exception as e:
            self.inst_vars.inst_log.Info(str(e))
        del self.specs
        
        
    ### Optional, for displaying recorded data ###

    def displayRec(self, recNum):

        try:
            cachedData = self.jsonFF.read_jsonFFcached(self.jsonFF["Data"], recNum, self.inst_vars.inst_n, self.inst_vars.globalTrigCount)
        except KeyError as e:
            return
        
        try:
            
             #Set Wavelengths
            if not hasattr(self, 'wavelengths'):
                self.wavelengths = self.jsonFF.readField(self.jsonFF["Wavelengths"])
                self.ui_signals["setWavelengths"].emit(self.wavelengths)
                
            #Set Dark Current
            if not hasattr(self, 'darkCurrent'):
                try:
                    self.darkCurrent = {}
                    for dark_intens in self.jsonFF.readField(self.jsonFF["DarkCurrent"]):    #Upward and Downward
                        self.darkCurrent[dark_intens[0]] = {"Upward":dark_intens[2]["Upward"], "Downward":dark_intens[2]["Downward"]}
                    self.correctDark = True
                except KeyError:
                    self.correctDark = False
                    
            #Set Int Time and Nonlin Correction
            self.options = cachedData[str(recNum)][1]["Options"]
            self.int_time = self.options["IntegrationTime"]
            self.ui_signals["updateIntTime"].emit(self.int_time)
            self.ui_signals["updateNonlin"].emit(bool(self.options["CorrectNonlinearity"]))
                       
            #Set References
            if not hasattr(self, 'refs_avg'):
                #Define reference variables
                self.refs = {"Upward": [], "Downward": []}
                self.refs_avg = {}
                refs_temp = self.jsonFF.readField(self.jsonFF["References"])
                #Update UI    
                for ref in refs_temp:
                    if ref[0] == self.int_time:
                        if self.correctDark:
                            ref = self.doCorrectDark(ref[2], self.darkCurrent, ref[0])   
                        else:
                            ref = ref[2]
                            
                        #for key, intens in ref.items():    #Upward and Downward
                        self.refs[self.int_time].append(ref)                    
                            
                self.refs_avg[self.int_time] = self.avgSamples(self.refs[self.int_time])
                self.upward_ref_interp = interp(self.wavelengths["Downward"], self.wavelengths["Upward"], self.refs_avg[self.int_time]["Upward"])
                
                self.ui_signals["updatePlot"].emit([self.refs_avg[self.int_time], True, len(self.refs[self.int_time]), self.wavelengths])  #Note: using the 'Downward' list is purely arbitrary since both lists will be the same length, we just need the length of either one
            
            #Set Intensities
            intensities = {"Upward":cachedData[str(recNum)][1]["Upward"], "Downward":cachedData[str(recNum)][1]["Downward"]}
            if self.correctDark:
                intensities = self.doCorrectDark(intensities, self.darkCurrent, self.int_time)

            #Set reflectance
            try:
                reflec = cachedData[str(recNum)][1]["Reflectance"]
            except KeyError:
                reflec = None
                
            #Update UI
            self.ui_signals["updatePlot"].emit([intensities, False, reflec, self.wavelengths])
        except Exception as e:
            self.inst_vars.inst_log.info("Error displaying record " + str(recNum) + ": " + str(e)) 


    ### Other Instrument Functions/Classes ###
    
    def calcReflectance(self, wavelengths, refs_avg, intensities, upward_ref_interp):   
        #print(intensities)
        #for key, intens in intensities.items():
        #    print("%s: %i intensities, %i wavelengths" % (key, len(intensities[key]), len(wavelengths[key])))
        upward_interp = interp(wavelengths["Downward"], wavelengths["Upward"], intensities["Upward"])
        #upward_ref_interp = interp(wavelengths["Downward"], wavelengths["Upward"], refs_avg["Upward"])
        
        reflec = (upward_ref_interp/asarray(refs_avg["Downward"]))*(asarray(intensities["Downward"])/upward_interp)
        return reflec
    
    def getIntensitiesList(self, spec):
        return list(spec.intensities(correct_dark_counts=self.correctDark, correct_nonlinearity=self.correct_nonlin))

    def intTimeChanged(self, newTime):
        for spec in self.specs.values():
            spec.integration_time_micros(newTime)
            self.int_time = newTime
            try:
                self.ui_signals["updatePlot"].emit([self.refs_avg[self.int_time], True, len(self.refs[self.int_time]), self.wavelengths])  #Note: using the 'Downward' list is purely arbitrary since both lists will be the same length, we just need the length of either one
            except KeyError:
                self.ui_signals["updatePlot"].emit([{"Upward": [], "Downward": []}, True, 0, self.wavelengths])  #Note: using the 'Downward' list is purely arbitrary since both lists will be the same length, we just need the length of either one

        self.inst_vars.inst_log.info("Integration time changed to: %i uS" % newTime)
        
    def doCorrectDark(self, intensities, darkCurrent, int_time):
        new_intensities = {"Upward": [], "Downward": []}
        try:
            for key, intens in new_intensities.items():
                #print("%s: %i intensities %i dark current" % (key, len(asarray(intensities[key])), len(asarray(darkCurrent[int_time][key]))))         
                new_intensities[key] = list(asarray(intensities[key]) - asarray(darkCurrent[int_time][key]))
        except KeyError:
            self.inst_vars.inst_log.warning("Dark current data missing for %s; correction not applied." % key)
            return intensities
        return new_intensities
        
    def setDarkCurrent(self):
        self.correctDark = True
        self.inst_vars.inst_log.info("Setting dark current values now!")
        self.acquire(setDark=True)
       
    def correctNonlinChanged(self, value):
        if value == 0:
            self.correct_nonlin = False
        else:
            self.correct_nonlin = True
        self.inst_vars.inst_log.info("Use nonlinearity correction: %i" % self.correct_nonlin)
        
    def remLastRef(self):
        try:
            #for key, ref in self.refs[self.int_time].items():
            #    ref.pop()
            self.refs[self.int_time].pop()
        except:
            pass
        if len(self.refs[self.int_time]) > 0: 
            intensities = self.avgSamples(self.refs[self.int_time])
        else:
            intensities = {"Upward": [], "Downward": []}
        #Update UI
        self.ui_signals["updatePlot"].emit([intensities, True, len(self.refs[self.int_time]),self.wavelengths])

    
    def avgSamples(self, samples):
        temp_list = {}
        for samp in samples:
            for key, samp_dict_item in samp.items():
                try: 
                    temp_list[key]
                except Exception:
                    temp_list[key] = []
                temp_list[key].append(samp_dict_item)

        samplesAvg = {}
        #Calc new average
        for key in temp_list.keys():
            samplesAvg[key] = [sum(col)/len(col) for col in zip(*temp_list[key])]
        return samplesAvg
        

class Ui_interface(QtCore.QObject):
    
    def init(self):
        try: 
            
            self.wls = {}
            self.cumulativeplots = []
            
            self.pw_down = pg.PlotWidget(name='PlotDown',background='w')
            self.pw_up = pg.PlotWidget(name='PlotUp',background='w')
            self.pw_reflec = pg.PlotWidget(name='PlotReflec',background='w')
            self.pw_cumulative = pg.PlotWidget(name='PlotCumulative',background='w')
            
            if self.ui_large:
                
                try:
                    self.clearLayout(self.ui.layout1)      #Clear layout if it exists so that instrument resets work properly
                except:          
                    self.ui.layout1 = QtGui.QHBoxLayout()
                    self.ui.layout1.setContentsMargins(0,0,0,0)
                
                
                self.ui.pltWidget.setLayout(self.ui.layout1)
                self.ui.pltWidget.setContentsMargins(0,0,0,0)
                
                self.ui.tabWidget = QtWidgets.QTabWidget()  
                self.ui.layout1.addWidget(self.ui.tabWidget)
                
                
                self.ui.tabWidget.addTab(self.pw_cumulative,"Cumulative")
                self.ui.tabWidget.addTab(self.pw_reflec,"Reflectance")
                self.ui.tabWidget.addTab(self.pw_down,"Downward")
                self.ui.tabWidget.addTab(self.pw_up,"Upward")
                
            else:
    
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
            self.pw_down.setYRange(0, 65535, padding=None, update=False)
            
            self.setupSpecPlot(self.pw_up, (1/65535))
            self.pw_up.setYRange(0, 65535, padding=None, update=False)
            
            self.setupSpecPlot(self.pw_reflec, 1)
            self.pw_reflec.setYRange(0, 1, padding=None, update=False)
            
            self.setupSpecPlot(self.pw_cumulative, 1)
            self.pw_cumulative.setYRange(0, 1, padding=None, update=False)
            
            self.refplot = {}
            self.refplot["Upward"] = self.pw_up.plot(pen=pg.mkPen('b', width=1))            
            self.refplot["Downward"] = self.pw_down.plot(pen=pg.mkPen('b', width=1))     
                   
            self.specplot = {}
            self.specplot["Upward"] = self.pw_up.plot(pen=pg.mkPen('r', width=2))
            self.specplot["Downward"] = self.pw_down.plot(pen=pg.mkPen('r', width=2))
            
            self.reflecplot = self.pw_reflec.plot(pen=pg.mkPen('b', width=2))
        
        except Exception as e:
            print(e)
    
    
    def setupSpecPlot(self, plot, scale):
        try:
            x_axis = plot.getAxis('bottom')
            y_axis = plot.getAxis('left')
            
            if self.ui_large:
                y_axis.showLabel(True)
                x_axis.setHeight(25)
                x_axis.setLabel('Wavelength', units='nm')
                plot.getAxis('top').setHeight(5)
            else:
                y_axis.showLabel(False)
                x_axis.setHeight(0) 
                y_axis.setWidth(0)
                plot.getAxis('top').setHeight(3)
                x_axis.showLabel(False) 
                 
            x_axis.enableAutoSIPrefix(False) 
            y_axis.enableAutoSIPrefix(False)
            y_axis.setScale(scale)
            
        except Exception as e:
            print(e)
        
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
        reflec = data[2]
        wls = data[3]
        
        #Update limits if they haven't been set
        try:
            self.wls
        except:
            self.setWavelengths(wls)
                
        for key, inten in intens.items():            
            if isRef:
                l = data[2]
                self.ui.lbl_refcount.setNum(l)
                if l > 0:
                    self.refplot[key].setData(x=wls[key], y=inten) 
                else:
                    self.refplot[key].setData(x=[], y=[])
            else:
                self.specplot[key].setData(x=wls[key], y=inten)
                
        if not isRef:
            try:
                self.reflecplot.setData(x=wls["Downward"], y=reflec)
                plotcount = len(self.cumulativeplots)
                self.cumulativeplots.append(self.pw_cumulative.plot(pen=pg.mkPen(plotcount, width=1)))
                self.cumulativeplots[plotcount].setData(x=wls["Downward"], y=reflec)
            except:
                pass
                
    def setWavelengths(self, wls):
        self.wls = wls
        x_range = (min([min(wls["Upward"]), min(wls["Downward"])]), max([max(wls["Upward"]), max(wls["Downward"])]))
        self.pw_down.setXRange(*x_range)
        self.pw_up.setXRange(*x_range)
        self.pw_reflec.setXRange(*x_range)
        self.pw_cumulative.setXRange(*x_range)


    #Check remote changes
    def updateIntTime(self, value):
        with SBlock(self.ui.sb_intTime) as b:
            b.setValue(value)
         
    def updateNonlin(self, value):
        with SBlock(self.ui.cb_correctNonlin) as b:
            b.setCheckState(value)
                   