from time import time, strftime
import logging #, objgraph
import configparser
import importlib
from os.path import isabs
from os import makedirs, path

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal

    
def inst_init(self, instlist, globalPath):
    
    logging.info("Loading Instruments...")
    
    index = 0        
    for inst in instlist:
        if str.lower(instlist[inst]) == "true":
            try:                    
                #Create inst objects
                self.active_insts[inst] = Inst_obj(globalPath, inst, self.ui_int.client.enabled)
                self.active_insts[inst].index = index
                self.inst_list.append(inst)
                
                cp_inst = self.active_insts[inst].cp_inst
                    
                self.inst_addedSig.emit(cp_inst)
                
                if cp_inst.has_option("Trigger","Source"):
                    self.globalTrig.connect(self.active_insts[inst].trigger)                    #Connect global trigger by default
                
            except Exception as e:
                logging.error("Error loading '%s': %s" % (inst, e))
                try:
                    del self.active_insts[inst]
                except Exception:
                    pass
            
            index += 1

    logging.info("%d/%d instruments active.\n" % (len(self.active_insts), len(instlist)))



class Inst_obj(QtCore.QObject):
    
    #Setup class signals and properties
    readySig = QtCore.pyqtSignal() 
    triggerSig = QtCore.pyqtSignal(str)
    resetSig = QtCore.pyqtSignal()
    interfaceReadySig = QtCore.pyqtSignal(object)
    finishedSig = QtCore.pyqtSignal()
    tCountSig = QtCore.pyqtSignal(object)
    logupdateSig = QtCore.pyqtSignal(str)
    
    def tCount(self):
        self.tCount_prop += 1
        self.tCountSig.emit([self.index, self.tCount_prop]) 
    
    statusSig = QtCore.pyqtSignal(object)
    @property
    def status(self):
        return self.status_prop
    @status.setter
    def status(self, s):
        self.status_prop = s
        self.instLog.debug(s)
        self.statusSig.emit([self.index, s])
        if (s == "Ready"):
            self.ready = True
            self.readySig.emit()
            self.error = ""
        else:
            self.ready = False  
        
    errorSig = QtCore.pyqtSignal(int, object)
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
            self.statusSig.emit([self.index, e_str])
            self.errorSig.emit(self.index, e)
        
    def __init__(self, globalPath, inst, client_enabled):     #Inst object init - this is the same for all instruments
        super().__init__()
       
        self.ready = False
        self.tCount_prop = 0
        self.status_prop = ""     
        self.error_prop = None
        self.inst = inst
        self.client_enabled = client_enabled
                                            
        #Create inst threads
        if not client_enabled:
            self.inst_thread = QtCore.QThread()
            self.moveToThread(self.inst_thread)                 #move the inst object to its thread
            self.finishedSig.connect(self.inst_thread.quit)     #make sure thread exits when inst is closed
            self.inst_thread.started.connect(self.init)         #make sure object init when thread starts
        

        #Read inst config
        cp_inst = configparser.ConfigParser()
        cp_inst.read(path.join('.', 'instruments', inst, 'inst_cfg.ini'))
        
        self.cp_inst = cp_inst
        
        #Setup data storage directory
        if not cp_inst.has_option("Data", "Destination"):
            dataPath = path.join(globalPath, cp_inst["InstrumentInfo"]["Name"].replace(" ", "_"))  #Using global location and default instrument directory
        elif isabs(cp_inst["Data"]["Destination"]):
            dataPath = cp_inst["Data"]["Destination"]                               #Using absolute path from instrument config
        else:
            dataPath = path.join(globalPath, cp_inst["Data"]["Destination"])        #Using global location and relative directory from instrument config
        
        makedirs(dataPath, exist_ok=True)
        if not cp_inst.has_section("Data"):
            cp_inst.add_section("Data")
        cp_inst["Data"]["absolutePath"] = dataPath
        
        #Setup inst log
        iLog = logging.getLogger(cp_inst["InstrumentInfo"]["Name"].replace(" ", "_"))
        logPath = path.join(dataPath, str(strftime("%Y-%m-%d_%H%M%S_" + cp_inst["InstrumentInfo"]["Name"].replace(" ", "_") + "_Log.txt")))
                
        formatter = logging.Formatter('[%(levelname)-10s] (%(threadName)-10s), %(asctime)s, %(message)s') # 
        formatter.datefmt = '%Y/%m/%d %I:%M:%S'
        fileHandler = logging.FileHandler(logPath, mode='w')
        fileHandler.setFormatter(formatter)
        iLog.setLevel(logging.DEBUG)
        iLog.addHandler(fileHandler)
        
        sh = logging.StreamHandler()
        formatter = logging.Formatter("        [" + inst + "]: %(message)s")
        sh.setFormatter(formatter)
        iLog.addHandler(sh)
        iLog.propagate = False
    
        #Setup internal objects and trigger params
        self.index = 0
        self.inst_cfg = cp_inst
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
        
        if not client_enabled:
            logging.info("Instrument Loaded: " + cp_inst["InstrumentInfo"]["Name"] + ", Model: " + cp_inst["InstrumentInfo"]["Model"] + ", Thread: " + str(self.inst_thread.currentThread()))
        else:
            logging.info("Instrument Loaded: " + cp_inst["InstrumentInfo"]["Name"] + ", Model: " + cp_inst["InstrumentInfo"]["Model"])
                    
    def create_inst_interface(self):
    #Create inst interface
        try:
            inst_mod = importlib.import_module("instruments." + self.inst + ".inst_interface")
        except Exception as e:
            self.error = "Interface init error: " + str(e)
            raise e
        self.interface = inst_mod.Inst_interface()
        self.interface.instLog = self.instLog
        self.interface.inst_cfg = self.inst_cfg
        
        #Setup inst signals and input sub
        self.interface.signals = {}
        for s in self.interface.outputs:
            self.interface.signals[s] = Sig(s)
            
        #Setup UI signals
        try:
            self.interface.ui_signals = {}
            for s in self.interface.ui_outputs:
                self.interface.ui_signals[s] = Sig(s)
        except:
            pass
            
        #Create UI user class instance
        try:
            self.ui = inst_mod.Ui()
        except:
            pass
        
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
        try:
            self.interface.init()        #Call instrument init
        except Exception as e:
            self.error = "Init error: " + str(e)
            return
        self.instLog.info("Init complete")
        self.status = "Ready"
        
        #Init timed triggers
        if "Timed" in self.trig_mode:
            self.t = QtCore.QTimer(self)
            self.t.setInterval(self.trig_int)
            self.t.timeout.connect(lambda: self.triggerSig.emit("Timed"))
        
    def close(self):
        try:
            self.interface.close()
        except Exception as e:
            self.error = "Close error: " + str(e)
            return            
        self.status = "Shutdown"
        
    def reset(self):
        self.instLog.info("Attempting reset")
        #objgraph.show_refs([self.interface.signals['shutter']], filename="C://temp//og_i_sig_resetstart.dot")
        self.close()
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
        self.init()

    def trigger(self,source):
        if source in self.trig_mode or "*" in self.trig_mode:
            if self.ready:
                self.status = "Acquiring"
                
                try:
                    self.instLog.info("Acq. %i, Trigger: %s" % (self.tCount_prop, source))
                    self.tCount()                                     #Increment acquisition counter
                    self.interface.acquire()                          #Call instrument acquisition method

                except Exception as e:
                    self.error = "Trigger error: " + str(e)
                    return
                
                self.status = "Ready"
            else:
                self.instLog.info("Trigger, Inst not ready")
            
    def t_Start(self):
        self.t.start()
        
    def t_Stop(self):
        self.t.stop()
        
    def uiAction(self,action):
        if action == "Start":
            try:
                self.t.start()
                self.instLog.info("Timed trigger started.")
            except:
                self.instLog.warning("No timer set up; not started.")

        elif action == "Stop":
            try:
                self.t.stop()
                self.instLog.info("Timed trigger stopped.")
            except:
                self.instLog.warning("No timer set up; not stopped.")
        else:
            self.trigger(action)
    
class Sig(QtCore.QObject):                      #Signal "wrapper" to allow programmatic definition of signals
    s = QtCore.pyqtSignal(object, object)
    
    def __init__(self, name):
        super().__init__()
        self.name = name
        
    def emit(self, object):
        self.s.emit(object, self.name)
        
    def connect(self, obj):
        self.s.connect(obj)

class QSignalHandler(logging.Handler):          #logging handler that emits all log entries through a specified signal
    
    def __init__(self, sig):
        super().__init__()
        self.sig = sig

    def emit(self, record):
        msg = self.format(record)
        self.sig.emit(msg)

    def write(self, m):
        pass


