'''
Created on Jul 13, 2016

@author: amcmahon
'''
import sys
import threading
import time
import logging
import configparser
import copy
import importlib
from os import makedirs

sys.path.append("..")
sys.path.append(".")

#from Instruments import instruments 

from PyQt5 import QtWidgets, QtCore
from ui.ui import Ui_MainWindow
from GPIOEmulator.EmulatorGUI import GPIO


            
class Trigger(QtCore.QObject):
    
    aq_trig = QtCore.pyqtSignal() 
    status = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(int)
    update_int = QtCore.pyqtSignal(int)
        
    def __init__(self, trig_params):
        super().__init__()
        
        self.trig_mode = trig_params["Mode"].replace(" ", "").split(",")
        self.trig_int = int(trig_params["Interval"])
        self.trig_repeat = int(trig_params["Repeat"])
        
        self.repeat = 0
        self.scope = "Scope not defined"
        
        logging.info("Triggers: " + trig_params["Mode"])
        
        if "Timed" in self.trig_mode:
            self.t = QtCore.QTimer()
            self.t.timeout.connect(lambda: self.trigger("Timed"))
            
            logging.info("Interval: " + str(self.trig_int))
            logging.info("Repeat: " + str(self.trig_repeat))
            
        elif "Movement" in self.trig_mode:
            
            self.t = QtCore.QTimer()
            self.t.timeout.connect(lambda: self.trigger("Movement"))
            self.update_int.connect(lambda: self.t.start(new_int))
            
        
    def trigger(self,source):
        
        if source in self.trig_mode:
                
            self.aq_trig.emit()
            self.status.emit("Trigger at %s" % time.time())
            logging.info(source + " trigger (" + self.scope + ")")
    
            if source == "Timed" and self.trig_repeat > 0:
                self.repeat += 1
                self.progress.emit(self.repeat / self.trig_repeat * 100)
                
                if self.repeat >= self.trig_repeat:
                    self.t.stop()
                    self.status.emit("Done.")
            
    def t_Start(self, new_int=0):
        if new_int == 0:
            new_int = self.trig_int
        self.t.start(new_int)
        
    def t_Stop(self):
        self.t.stop()
        
    def uiAction(self,action):
        if action == "Start":
            self.t_Start()
        elif action == "Stop":
            self.t_Stop()
        elif action == "Manual":
            self.trigger("Manual")
     
class ITrigs(QtCore.QObject):
    
    sig = QtCore.pyqtSignal(str)  
      
        
class Instruments(QtCore.QObject):
    
    status = QtCore.pyqtSignal(str)
    update_table = QtCore.pyqtSignal(object)
    
    active_insts = []
    inst_threads = []
    iTrigs = []
    
    def init(self, instlist, globalPath):
        
        self.status.emit("Loading Instruments...")
        
        index = 0        
        for inst in instlist:
            if instlist[inst] == "True":
                
                cp_inst = configparser.ConfigParser()
                cp_inst.read('.\\instruments\\' + inst + '\\inst_cfg.ini')
                
                #Create inst objects
                inst_mod = importlib.import_module("instruments." + inst + ".inst_interface")
                self.active_insts.append(inst_mod.Inst_obj(cp_inst, globalPath))
                self.active_insts[index].index = index
                        
                #Creat inst threads
                self.inst_threads.append(QtCore.QThread())
                self.active_insts[index].moveToThread(self.inst_threads[index])             #move the inst object to it's thread
                self.active_insts[index].finished.connect(self.inst_threads[index].quit)    #make sure thread exits when inst is closed
                self.inst_threads[index].started.connect(self.active_insts[index].init)     #make sure object init when thread starts
                
                #Setup individual triggers
                self.iTrigs.append(ITrigs())
                if cp_inst.has_option("Trigger","Scope"):
                    if "Individual" in cp_inst["Trigger"]["Scope"].replace(" ", "").split(","):
                        self.active_insts[index].trig = Trigger(cp_inst["Trigger"])                                 #Create individual trigger
                        self.active_insts[index].trig.scope = "Individual, " + inst
                        self.active_insts[index].trig.aq_trig.connect(self.active_insts[index].acquire)             #Connect individual trigger
                        self.iTrigs[index].sig.connect(self.active_insts[index].trig.uiAction)                      #Connect UI trigger
                
                self.update_table.emit(cp_inst)
                
                logging.info("Instrument Loaded: " + cp_inst["InstrumentInfo"]["Name"] + ", Model: " + cp_inst["InstrumentInfo"]["Model"] + ", Thread: " + str(self.inst_threads[index].currentThread()))
                
                index += 1

        self.status.emit("\n%d/%d instruments active." % (len(self.active_insts), len(instlist)))
    
    


class Main(QtWidgets.QMainWindow):
    startTime = 0
    count = 0
   
    def __init__(self, parent=None):
        super().__init__()
        
        self.ui_init()
        
        cp = configparser.ConfigParser()
        cp.read('.\\core\\run_cfg.ini')
        
        dataPath = cp["Data"]["location"] + str(time.strftime("\\\\%Y-%m-%d_%H%M%S"))
        makedirs(dataPath, exist_ok=True)
        logFile = dataPath + str(time.strftime("\\\\%Y-%m-%d_%H%M%S_RunLog.txt"))
        
        logging.basicConfig(
        filename=logFile,
        level=logging.DEBUG,
        format='[%(levelname)s] (%(threadName)-10s), %(asctime)s, %(message)s',
        datefmt='%Y/%m/%d %I:%M:%S',)
    
        self.inst = Instruments()
        self.inst.update_table.connect(self.set_inst_table)
        self.inst.status.connect(self.update_run_status)
        self.inst.init(cp["Active_Insts"], dataPath)
        
        #Setup global trigger
        self.trig = Trigger(cp["Trigger"])
        self.trig.scope = "Global"
        self.trig.status.connect(self.update_run_status)
        self.trig.progress.connect(self.update_trig_prog)
        self.ui.btn_Start.released.connect(self.trig.t_Start)
        self.ui.btn_Stop.released.connect(self.trig.t_Stop)
        self.ui.btn_ManTrig.released.connect(lambda: self.trig.trigger("Manual"))
        
        #Connect individual trigger buttons
        self.ui.btn_Start_In.released.connect(lambda: self.ui_Trig_In("Start"))    
        self.ui.btn_Stop_In.released.connect(lambda: self.ui_Trig_In("Stop"))
        self.ui.btn_ManTrig_In.released.connect(lambda: self.ui_Trig_In("Manual"))
        
        #Connect insts to trigs
        for i in self.inst.active_insts:
            
            i.status.connect(self.update_inst_status)  
                      
            if i.inst_cfg.has_option("Trigger","Scope"):
                if "Global" in i.inst_cfg["Trigger"]["Scope"].replace(" ", "").split(","):
                    self.trig.aq_trig.connect(i.acquire)                #Connect global trigger
            else:
                self.trig.aq_trig.connect(i.acquire)                    #Connect global trigger by default
                
        for i in self.inst.inst_threads:
            i.start()                                                   #Start instrument threads

        
    def ui_Trig_In(self, act):
        if len(self.ui.tbl_Instruments.selectionModel().selectedRows()) > 0:
            r = self.ui.tbl_Instruments.selectionModel().selectedRows()[0].row()
            self.inst.iTrigs[r].sig.emit(act)
        
        
    def set_inst_table(self, cp_inst):      
        self.ui.plainTextEdit.appendPlainText("- " + cp_inst["InstrumentInfo"]["Name"])
        r = self.ui.tbl_Instruments.rowCount()
        self.ui.tbl_Instruments.insertRow(r)
        self.ui.tbl_Instruments.setItem(r, 0, QtWidgets.QTableWidgetItem(cp_inst["InstrumentInfo"]["Name"]))
        self.ui.tbl_Instruments.setItem(r, 1, QtWidgets.QTableWidgetItem(cp_inst["InstrumentInfo"]["Model"]))
        self.ui.tbl_Instruments.setItem(r, 2, QtWidgets.QTableWidgetItem("Standby"))
            
    def update_run_status(self, s):
        self.ui.plainTextEdit.appendPlainText(s)
        
    def update_inst_status(self, r, status):
        self.ui.tbl_Instruments.setItem(r, 2, QtWidgets.QTableWidgetItem(status))
        
    def update_trig_prog(self, prog):
        self.ui.progressBar.setValue(prog)
        if prog == 0 or prog >= 100:
            self.ui.progressBar.setVisible(False)
        else:
            self.ui.progressBar.setVisible(True)

    def ui_init(self):     
        QtWidgets.QMainWindow.__init__(self)
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        stylesheet = "::section{Background-color:rgb(210,210,210);}"
        self.ui.tbl_Instruments.horizontalHeader().setStyleSheet(stylesheet)
        self.ui.tbl_Instruments.setColumnWidth(0, 100)
        self.ui.tbl_Instruments.setColumnWidth(1, 50)
        self.ui.tbl_Instruments.horizontalHeader().setStretchLastSection(True)
        
        self.ui.progressBar.setVisible(False)
          
        self.ui.tbl_Instruments.itemSelectionChanged.connect(self.updateInstStat)
        
        self.clockTimer = QtCore.QTimer()
        self.clockTimer.timeout.connect(self.updateTime)
        self.clockTimer.start(10)        
        
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(15, GPIO.IN)
        #GPIO.add_event_detect(17, GPIO.RISING, callback=reset, bouncetime=300) 
        t_gpio = threading.Thread(target=self.gpio_monitor)
        t_gpio.start()    
        
    def updateInstStat(self):
        if len(self.ui.tbl_Instruments.selectionModel().selectedRows()) > 0:
            r = self.ui.tbl_Instruments.selectionModel().selectedRows()[0].row()
            self.ui.txt_InstStat.setPlainText("Name: " + self.inst.active_insts[r].inst_cfg["InstrumentInfo"]["Name"])
            self.ui.txt_InstStat.appendPlainText("Model: " + self.inst.active_insts[r].inst_cfg["InstrumentInfo"]["Model"])
            self.ui.txt_InstStat.appendPlainText("Acquisition Type: " + self.inst.active_insts[r].inst_cfg["Acquisition"]["Aq_Type"])
            self.ui.txt_InstStat.appendPlainText("Data Location: " + self.inst.active_insts[r].inst_cfg["Data"]["Destination"])
       
        else:
            self.ui.txt_InstStat.setPlainText("")
            
    def updateTime(self):
        self.ui.lcdTime.display(time.strftime("%H"+":"+"%M"+":"+"%S"))

         
    def reset(self):
        self.ui.progressBar.setValue(0)
        self.ui.plainTextEdit.appendPlainText("Reset!")       


    def gpio_monitor(self):
        triggered = False
        while(1):
            if GPIO.input(15) == True and triggered == False:
                self.trig[0].trigger("Manual")
                time.sleep(1)
                triggered = True
            elif triggered == True:
                triggered = False
            time.sleep(.01)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    window.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    window.show()
    GPIO.cleanup() 
    sys.exit(app.exec_())


