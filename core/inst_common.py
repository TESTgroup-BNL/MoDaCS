#System Imports
from time import time, strftime
import logging, configparser, importlib, traceback, sys, json
from os import makedirs, path
from collections import namedtuple

#Qt Imports
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal
from util import QSignalHandler, Sig

#MoDaCS Imports
from util import JSONFileField

    
def inst_init(self, instlist, globalPath, mainthreadlist, displayOnly, instrumentPaths):
    
    logging.info("Loading Instruments...")
    
    index = 0
    for inst in instlist:
        if str.lower(instlist[inst]) == "true":
            try:                    
                client_only = ((self.ui_int.client.enabled and (not self.ui_int.server.enabled)) or (displayOnly == True))
                mainthread = None
                if inst in mainthreadlist:
                    if bool(mainthreadlist[inst]) == True:
                        mainthread = self.thread()

                #Create inst objects
                if displayOnly:
                    instPath = instrumentPaths[inst]
                else:
                    instPath = None
                self.active_insts[inst] = Inst_obj(globalPath, inst, client_only, self.getGlobalTrigCount, mainthread, displayOnly=displayOnly, instPath=instPath)
                self.active_insts[inst].index = index
                self.inst_list.append(inst)
                
                if not client_only:
                    self.runningThreads.watchThread(self.active_insts[inst].inst_thread)
                    self.active_insts[inst].inst_thread.started.connect(self.active_insts[inst].init)         #make sure object init when thread starts

                self.inst_addedSig.emit(self.active_insts[inst].cp_inst, inst)
                self.finishedSig.connect(self.active_insts[inst].finishedSig)
                
                if hasattr(self.active_insts[inst].interface, "displayRec"):       #Connect global record display handler if it exists
                    self.ui_int.displayRec.connect(self.active_insts[inst].displayRec)

                #if len(self.active_insts[inst].trig_mode) > 0:
                #logging.debug("global trig connected to %s" % inst)
                if not client_only:
                    self.globalTrig.connect(self.active_insts[inst].trigger)                    #Connect global trigger by default

            except Exception as e:
                logging.error("Error loading '%s': %s" % (inst, e))
                try:
                    del self.active_insts[inst]
                except Exception:
                    pass

            index += 1

    logging.info("%d/%d instruments active.\n" % (len(self.active_insts), len(instlist)))


class Inst_jsonFF(JSONFileField):

    def __init__(self, inst_cfg, readOnly=False):
        
        #self.tCount_prop = tCount_prop
        #self.globalTrigCount = globalTrigCount
        self.dataCache = {}
        self.readOnly = readOnly
        
        #Create/load output file
        self.dataFile = path.join(inst_cfg["Data"]["absolutePath"], inst_cfg["Data"]["outputFilePrefix"] + ".json")

        if not readOnly:
            makedirs(path.dirname(self.dataFile), exist_ok=True)
        
        super().__init__(self.dataFile, fileOnly=readOnly)

        if not readOnly:
            self.addElement("Configuration", {s:dict(inst_cfg.items(s)) for s in inst_cfg.sections()})
            self.addField("Data", fieldType=object)
        
    def read_jsonFFcached(self, field, recNum, tCount_prop, globalTrigCount): 
        if self.readOnly:
            return field
        
        #Only re-read the full field if there's new data/new data is needed
        try:
            if self.last_tCount_prop == tCount_prop and ((recNum <= self.last_globalTrig) or self.last_globalTrig == 0):
                return self.dataCache[field]
        except:
            pass
        
        self.dataCache[field] = field.readAll()       
        self.last_tCount_prop = tCount_prop
        self.last_globalTrig = globalTrigCount
        
        return self.dataCache[field]
    
class Inst_vars():

    def __init__(self, **kwargs):
        for arg in kwargs:
            self.arg = arg
        #self.inst_vars = namedtuple("inst_vars", ["inst_cfg", "inst_log", "inst_n", "inst_path", "inst_wid", "realtime", "globalTrigCount"]) #Inst_vars()



class Inst_obj(QtCore.QObject):
    
    #Setup class signals and properties
    readySig = QtCore.pyqtSignal() 
    triggerSig = QtCore.pyqtSignal(str)
    resetSig = QtCore.pyqtSignal()
    interfaceReadySig = QtCore.pyqtSignal(object)
    uiReadySig = QtCore.pyqtSignal()
    finishedSig = QtCore.pyqtSignal()
    tCountSig = QtCore.pyqtSignal(object)
    logupdateSig = QtCore.pyqtSignal(str)
    
    def tCount(self):
        self.tCount_prop += 1
        try:
            self.interface.inst_n += 1      #if interface is broken, don't worry about it (though tCount should never be updating in that case anyway)
        except:
            pass
        self.tCountSig.emit([self.inst, self.tCount_prop]) 
    
    statusSig = QtCore.pyqtSignal(object)
    @property
    def status(self):
        return self.status_prop
    @status.setter
    def status(self, s):
        self.status_prop = s
        self.instLog.debug(s)
        self.statusSig.emit([self.inst, s])
        if (s == "Ready"):
            self.ready = True
            self.readySig.emit()
            self.error = ""
        else:
            self.ready = False  
        
    errorSig = QtCore.pyqtSignal(str, object)
    @property
    def error(self):
        return self.error_prop
    @error.setter
    def error(self, e):
        self.error_prop = e
        if e is not None and e is not "":
            self.instLog.error(e)
            self.ready = False
            #if isinstance(e, Exception):
            #    e_str = e.getType()
            #else:
            e_str = str(e)
            self.status_prop = e_str
            self.statusSig.emit([self.inst, e_str])
            self.errorSig.emit(self.inst, e)
        
    def __init__(self, globalPath, inst, client_only, getGlobalTrigCount, mainthread=None, displayOnly=False, instPath=None):     #Inst object init - this is the same for all instruments
        super().__init__()
       
        self.ready = False
        self.tCount_prop = 0
        self.status_prop = ""     
        self.error_prop = None
        self.inst = inst
        self.client_only = client_only
        self.initDone = False
        self.globalPath = globalPath
        self.instPath = instPath
        self.getGlobalTrigCount = getGlobalTrigCount
        self.displayOnly = displayOnly 
        self.mainthread = False   
        
        #Create inst threads
        if not client_only:
            if mainthread is not None:
                self.mainthread = True
                self.inst_thread = mainthread
            else:
                self.inst_thread = QtCore.QThread()
                self.inst_thread.setObjectName(inst)
                self.moveToThread(self.inst_thread)                 #move the inst object to its thread
                
            self.finishedSig.connect(self.finished)             #make sure thread exits when inst is closed
            self.uiReadySig.connect(self.init)                  #Re-init after instrument restart
       
        #Get inst config and setup paths
        cp_inst = configparser.ConfigParser()
        
        if displayOnly:
            self.uiReadySig.connect(self.init)
            
            try:
                with open(instPath + ".json") as rdJSON:
                    runData = json.load(rdJSON)
                
                #Read inst config
                cp_inst.read_dict(runData["Configuration"])

                #Change path to saved data location            
                if cp_inst.has_option("Data", "Destination"):
                    cp_inst["Data"]["absolutePath"] = path.join(globalPath, cp_inst["Data"]["Destination"])        #Using global location and relative directory from instrument config
                else:
                    cp_inst["Data"]["absolutePath"] = globalPath
                    

            except Exception as e:
                print("Error loading instrument configuration data: ", str(e))
                raise
            
        else:
            #Read inst config
            cp_inst.read(path.join('.', 'instruments', inst, 'inst_cfg.ini'))

            #Setup data storage directory
            if not cp_inst.has_option("Data", "Destination"):
                dataPath = path.join(globalPath, cp_inst["InstrumentInfo"]["Name"].replace(" ", "_"))  #Using global location and default instrument directory
            elif path.isabs(cp_inst["Data"]["Destination"]):
                dataPath = cp_inst["Data"]["Destination"]                               #Using absolute path from instrument config
            else:
                dataPath = path.join(globalPath, cp_inst["Data"]["Destination"])        #Using global location and relative directory from instrument config
            
            makedirs(dataPath, exist_ok=True)
            if not cp_inst.has_section("Data"):
                cp_inst.add_section("Data")
            cp_inst["Data"]["absolutePath"] = dataPath
            cp_inst["Data"]["outputFilePrefix"] = str(strftime("%Y-%m-%d_%H%M%S_" + cp_inst["InstrumentInfo"]["Name"].replace(" ", "_")))
            
            cp_inst["Data"]["inst"] = inst
            
        self.cp_inst = cp_inst    
        
        
        #Setup inst log
        iLog = logging.getLogger(cp_inst["InstrumentInfo"]["Name"].replace(" ", "_"))
        
        if displayOnly:
            self.logPath = path.join(cp_inst["Data"]["absolutePath"], cp_inst["Data"]["outputFilePrefix"] + "_Log.txt")
        
        if not (client_only or displayOnly):        
            self.logPath = path.join(dataPath, cp_inst["Data"]["outputFilePrefix"] + "_Log.txt") 
            formatter = logging.Formatter('[%(levelname)-10s] (%(threadName)-10s), %(asctime)s, %(message)s') # 
            formatter.datefmt = '%Y/%m/%d %I:%M:%S'
            fileHandler = logging.FileHandler(self.logPath, mode='w')
            fileHandler.setFormatter(formatter)
            iLog.setLevel(logging.DEBUG)
            iLog.addHandler(fileHandler)
        
        sh = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)-10s] (%(threadName)-10s), %(asctime)s,        [" + inst + "]: %(message)s")
        sh.setFormatter(formatter)
        iLog.addHandler(sh)
        iLog.propagate = False
        
           
        #Setup internal objects and trigger params
        self.inst_vars = Inst_vars()
        self.inst_vars.inst_cfg = cp_inst
        self.inst_vars.inst_log = iLog
        self.inst_vars.inst_n = 0
        self.inst_vars.inst_path = path.join("instruments", self.inst)
        self.inst_vars.inst_wid = None
        self.inst_vars.realtime = True
        self.inst_vars.globalTrigCount = 0
               
        self.index = 0
        self.instLog = iLog
        
        try:
            trig_params = cp_inst["Trigger"]
            self.trig_mode = trig_params["Source"].replace(" ", "").split(",") 
            iLog.info("Triggers: " + trig_params["Source"])
        except:
            iLog.warning("Error reading trigger parameters, defaulting to use any sources ('*')")
            self.trig_mode = "*"

        if "Timed" in self.trig_mode:
            try:
                self.trig_int = int(trig_params["Interval"])    
            except:
                iLog.warning("Error reading trigger interval, defaulting to 1 sec")
                self.trig_int = 1000
            iLog.info("Interval: " + str(self.trig_int))  

        #Setup individual signals/triggers
        self.triggerSig.connect(self.uiAction)                       #Connect UI trigger
        self.resetSig.connect(self.reset)                            #Connect reset trigger
    
        self.create_inst_interface()
        
        if not client_only:
            logging.info("Instrument Loaded: " + cp_inst["InstrumentInfo"]["Name"] + ", Model: " + cp_inst["InstrumentInfo"]["Model"] + ", Thread: " + str(self.inst_thread.currentThread()))
        else:
            logging.info("Instrument Loaded: " + cp_inst["InstrumentInfo"]["Name"] + ", Model: " + cp_inst["InstrumentInfo"]["Model"])
                    
    def create_inst_interface(self):
    #Create inst interface
        self.instLog.debug("Creating instrument interface...")
        try:
            inst_mod = importlib.import_module("instruments." + self.inst + ".inst_interface")
        except Exception as e:
            self.error = "Interface init error: " + str(e)
            raise e    
        
        self.interface = inst_mod.Inst_interface()
        
        #self.interface.instLog = self.instLog
        #self.interface.inst_cfg = self.inst_cfg
        #self.interface.inst_n = 0
        #self.interface.instPath = path.join("instruments", self.inst)
        
        #self.interface.create_jsonFF = self.create_jsonFF
        #self.interface.read_jsonFFcached = self.read_jsonFFcached
        #self.interface.realtime = True
        
        #Setup inst signals and input sub
        self.interface.signals = {}
        for s in self.interface.outputs:
            self.interface.signals[s] = Sig(s)
            
        #Setup UI signals
        self.uiReady = False
        try:
            self.interface.ui_signals = {}
            for s in self.interface.ui_outputs:
                self.interface.ui_signals[s] = Sig(s)
        except:
            pass
            
        #Create UI user class instance
        try:
            self.ui_interface = inst_mod.Ui_interface()
        except:
            pass
        self.instLog.debug("Interface ready")
        
        self.interfaceReadySig.emit(self)
        

    def cp_to_str(self, cp):
        r_str = ""
        for s in cp.sections():
            r_str += "[%s]\n" % s
            for k, v in cp[s].items():
                r_str += "    %s: %s\n" % (k, v)
            r_str += "\n"
        return r_str
        
    def init(self):
        
        if self.displayOnly:
            self.interface.inst_vars = self.inst_vars
            self.jsonFF = Inst_jsonFF(self.inst_vars.inst_cfg, readOnly=True)
            self.interface.jsonFF = self.jsonFF
            
            #Read existing log
            with open(self.logPath , 'r') as logFile_in:
                self.logupdateSig.emit(logFile_in.read()) #logFile.read())
            
        else:    
            if self.uiReady and self.inst_thread.isRunning() and (not self.initDone):
                self.initDone = True
                try:
                    self.jsonFF = Inst_jsonFF(self.inst_vars.inst_cfg)      #Create JSON output
                    self.interface.init(self.inst_vars, self.jsonFF)        #Call instrument init
                except ImportError as e:
                    traceback.print_exc(file=sys.stdout)
                    self.instLog.warning("Import error: " + str(e))
                    pass
                except Exception as e:
                    traceback.print_exc(file=sys.stdout)
                    self.error = "Init error: " + str(e)
                    return
                
                #Init timed triggers
                self.runContinuous = False
                self.continuous = False
                if "Timed" in self.trig_mode:
                    if self.trig_int == 0:
                        self.continuous = True
                        self.runContinuous = True
                        self.instLog.info("Continuous trigger enabled")
                    else:
                        self.t = QtCore.QTimer(self)
                        self.t.setInterval(self.trig_int)
                        self.t.timeout.connect(lambda: self.triggerSig.emit("Timed"))
                        
                self.instLog.info("Init complete")
                self.status = "Ready"
        
    def close(self):
        self.initDone = False
        try:
            self.interface.close()
        except Exception as e:
            self.warning = "Close error: " + str(e) #Warning instead of error to prevent shutdown hangs
        self.jsonFF.close() 
        self.status = "Shutdown"
        
    def reset(self):
        self.instLog.info("Attempting reset")
        #objgraph.show_refs([self.interface.signals['shutter']], filename="C://temp//og_i_sig_resetstart.dot")
        self.close()
        self.instLog.debug("Clearing signals")
        try:
            for key, s in self.interface.signals.items():
                try:
                    s.disconnect()
                except:
                    pass
            for key, s in self.interface.ui_signals.items():
                try:
                    s.disconnect()   
                except:
                    pass
            self.interface = None
        except Exception as e:
            self.instLog.info(e)
            pass
        self.create_inst_interface()
        #self.init_UI_Sigs()
        #self.init()

    def trigger(self, source):
        if source in self.trig_mode or "*" in self.trig_mode or source == "Manual":
            if self.ready or source=="Individual":
                self.status = "Acquiring"
                
                try: 
                    self.inst_vars.globalTrigCount = self.getGlobalTrigCount()
                    #self.interface.globalTrigCount = globalTrigCount
                    self.instLog.info("Acq. %i, Trigger: %s, RecNum: %i" % (self.tCount_prop, source, self.inst_vars.globalTrigCount))
                    self.interface.acquire()                          #Call instrument acquisition method
                    self.tCount()                                     #Increment acquisition counter

                except Exception as e:
                    self.error = "Trigger error: " + str(e)
                    return
                
                self.status = "Ready"
                
                QtWidgets.QApplication.processEvents()
                if self.runContinuous:
                    self.triggerSig.emit("Timed")
            else:
                self.instLog.info("Trigger, Inst not ready")
                
    def displayRec(self, recNum):
        try:
            if recNum == -1:
                if self.tCount_prop > 1:
                    recNum = self.tCount_prop - 1
                else:
                    return  #No record to display
                self.inst_vars.realtime = True
            else:
                self.inst_vars.realtime = False
            self.interface.displayRec(recNum)
        except Exception as e:
            self.instLog.info("Error loading record " + str(recNum) + ": " + str(e))
        return
            
    def t_Start(self):
        self.t.start()
        
    def t_Stop(self):
        self.t.stop()
        
    def uiAction(self,action):
        if action == "Start":
            if self.continuous:
                self.runContinuous = True
                self.triggerSig.emit("Timed")
            else:
                try:
                    self.t.start()
                    self.instLog.info("Timed trigger started.")
                except:
                    self.instLog.warning("No timer set up; not started.")

        elif action == "Stop":
            if self.continuous:
                self.runContinuous = False
            else:
                try:
                    self.t.stop()
                    self.instLog.info("Timed trigger stopped.")
                except:
                    self.instLog.warning("No timer set up; not stopped.")
        else:
            self.trigger(action)
            
    def finished(self):
        self.instLog.info("Shutting down...")
        self.close()
        
        if not self.mainthread:
            try:
                self.inst_thread.quit()
                self.inst_thread.wait()
            except Exception as e:
                self.instLog.warning("Error quitting thread: %s" % e)
        else:
            self.instLog.info("Shutdown (pending Main Thread)")

