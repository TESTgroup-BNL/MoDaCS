'''
Created on Jul 13, 2016

@author: amcmahon
'''
import sys, traceback, pickle, inspect, getopt
from time import time, strftime, sleep
import logging
import configparser
import copy
import importlib
from os.path import isabs
from os import makedirs, path
from test.test_threading_local import target

from PyQt5 import QtWidgets, QtCore
try:
    import RPi.GPIO as GPIO
except:
    from GPIOEmulator.EmulatorGUI import GPIO
from logging import StreamHandler

sys.path.append("..")
sys.path.append(".")

from inst_common import inst_init, QSignalHandler
import instruments
from events_common import events_init
import ui.ui_interface
        


class Main(QtWidgets.QMainWindow):
    
    #status = QtCore.pyqtSignal(str)
    inst_addedSig = QtCore.pyqtSignal(object)
    event_addedSig = QtCore.pyqtSignal(object, str)
    event_reloadSig = QtCore.pyqtSignal(object, str)
    event_reloadRemoteSig = QtCore.pyqtSignal(object, str)
    globalTrig = QtCore.pyqtSignal(str)
    logupdateSig = QtCore.pyqtSignal(str)
    
    active_insts = {}
    inst_list = []
        
    event_objs = {}
    reset_lambdas = []
    
    startTime = 0
    count = 0
    
    ui_large = False
   
    def __init__(self, parent=None):
        super().__init__()
        QtWidgets.QMainWindow.__init__(self)
              
        #Initialize config parser and logger
        cp = configparser.ConfigParser()
        opts, args = getopt.getopt(sys.argv[1:],"hc:", ["run_config="])
        run_config = path.join('.', 'core', 'run_cfg.ini')
        try:
            for opt, arg in opts:
                if opt in ("-h", "--help", "?", "help"):
                    print("MoDaCS Main Module\n\nUsage: main.py [-c <run config file>]\n\nOptions:\n     -c, --run_config : Specifies an alternate run configuration file.  (Default is 'core\\run_cfg.ini'.)")
                    sys.exit()
                if opt in ("-c", "--run_config"):
                    run_config = arg
            cp.read(run_config)
            dataPath = path.join(cp["Data"]["location"], str(strftime("%Y-%m-%d_%H%M%S")))
            makedirs(dataPath, exist_ok=True)
            logFile = path.join(dataPath, str(strftime("%Y-%m-%d_%H%M%S_RunLog.txt")))
        except KeyError:
            print("Error: run_cfg file missing or missing required keys")
            raise
        
        logging.basicConfig(
        filename=logFile,
        level=logging.DEBUG,
        format='[%(levelname)-10s] (%(threadName)-10s), %(asctime)s, %(message)s',
        datefmt='%Y/%m/%d %I:%M:%S',)
        
        logging.getLogger().addHandler(StreamHandler())
        
        #Initialize Main UI
        if cp.has_option("UI", "Size"):
            if cp["UI"]["Size"] == "large":
                self.ui_large = True
        self.ui_int = ui.ui_interface.UI_interface(self, cp, self.active_insts, self.inst_list)
        
        #Connect event UI widgets
        self.globalTrig.connect(lambda source="" : self.ui_int.ui.treeWidget.topLevelItem(0).setText(1, source))
        self.inst_addedSig.connect(self.ui_int.ui_set_inst_table)
        self.event_addedSig.connect(self.ui_int.ui_eventtree_add)
        self.event_reloadSig.connect(self.ui_int.ui_eventreload)
        #self.status.connect(self.ui_int.ui_update_run_status)

        logging.getLogger().addHandler(QSignalHandler(self.logupdateSig))
        self.logupdateSig.connect(self.ui_int.ui.plainTextEdit.appendPlainText)
        
        #Connect remote signals if server is enabled
        if self.ui_int.server.enabled:
            self.globalTrig.connect(lambda val="": self.ui_int.server.sendSig.emit("main_app.globalTrig", val))
            self.logupdateSig.connect(lambda val="": self.ui_int.server.sendSig.emit("main_app.logupdateSig", "[Remote] " + val))
            #self.inst_addedSig.connect(lambda val="": self.ui_int.server.sendSig.emit("main_app.inst_addedSig", val))
            #self.event_addedSig.connect(lambda val="": self.ui_int.server.sendSig.emit("main_app.event_addedSig", {"direct": val["direct"], "inputs": dict.fromkeys(list(val["inputs"].keys())), "outputs": dict.fromkeys(list(val["outputs"].keys())) } ))
        
        if not self.ui_int.client.enabled:
            self.ui_int.ui.btn_ManTrig.released.connect(lambda: self.globalTrig.emit("Manual"))
          
        #Initialize Instruments
        inst_init(self, cp["Active_Insts"], dataPath)
        
        #Initialize Events
        events_init(self, cp["Events"])

        #Initialize inst widgets
        self.ui_int.ui_init_widgets()
        
        if self.ui_int.client.enabled:
            #Start client thread
            self.ui_int.client.thread.start()
        else:
            #Start instrument threads
            for key, i in self.active_insts.items():
                i.inst_thread.start()
                
        if self.ui_int.server.allowControl:
            self.ui_int.server.controlClient.thread.start()
            
        #objgraph.show_refs([self], filename="C://temp//og_i_main.dot")
        
def my_excepthook(type, value, traceb):
    #print('Unhandled error:', type, value, traceb)
    for l in traceback.format_exception(type, value, traceb):
        print(l)
    #print(traceback.format_exception(type, value, traceb))                                   


if __name__ == '__main__':
    sys.excepthook = my_excepthook
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    if not window.ui_large:
        window.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    window.show()
    GPIO.cleanup() 
    sys.exit(app.exec_())



