'''
Created on Jul 13, 2016

@author: amcmahon
'''
#System Imports
import sys, traceback, getopt, logging, configparser, copy, importlib, subprocess
from time import time, strftime, sleep
from os import makedirs, path, execv

#Qt Imports
from PyQt5 import QtWidgets, QtCore

#RasPi Imports
try:
    import RPi.GPIO as GPIO
except:
    from GPIOEmulator.EmulatorGUI import GPIO

#MoSaCS Imports
sys.path.append("..")
sys.path.append(".")

from inst_common import inst_init, QSignalHandler
import instruments
from events_common import events_init
import ui.ui_interface
import util
        


class Main(QtWidgets.QMainWindow):
    
    #status = QtCore.pyqtSignal(str)
    inst_addedSig = QtCore.pyqtSignal(object, str)
    event_addedSig = QtCore.pyqtSignal(object, str)
    event_reloadSig = QtCore.pyqtSignal(object, str)
    event_reloadRemoteSig = QtCore.pyqtSignal(object, str)
    globalTrig = QtCore.pyqtSignal(str)
    logupdateSig = QtCore.pyqtSignal(str)
    finishedSig = QtCore.pyqtSignal()
    
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
        
        self.finishedSig.connect(self.finished)
        self.readyToClose = False
        self.shutdown_mode = ""
        
        self.runningThreads = util.RunningThreads()
              
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
        
        logging.getLogger().addHandler(logging.StreamHandler())
        
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

        logging.getLogger().addHandler(QSignalHandler(self.logupdateSig))
        self.logupdateSig.connect(self.ui_int.ui.plainTextEdit.appendPlainText)
        
        #Connect remote signals if server is enabled
        if self.ui_int.server.enabled:
            self.globalTrig.connect(lambda val="": self.ui_int.server.sendSig.emit("main_app.globalTrig", val))
            self.logupdateSig.connect(lambda val="": self.ui_int.server.sendSig.emit("main_app.logupdateSig", "[Remote] " + val))
       
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
            
        if self.ui_int.server.enabled or (not self.ui_int.client.enabled):
            #Start instrument threads
            for key, i in self.active_insts.items():
                i.inst_thread.start()
                
        if self.ui_int.server.allowControl:
            self.ui_int.server.controlClient.thread.start()
            
    def closeEvent(self, event):
        if self.readyToClose:
            if self.shutdown_mode == "Restart MoDaCS":
                execv(sys.executable, ['python3'] + sys.argv)
            elif self.shutdown_mode == "Shutdown RaspPi":
                subprocess.call('sudo shutdown now', shell=True)
            elif self.shutdown_mode == "Restart RaspPi":
                subprocess.call('sudo shutdown -r now', shell=True)
            event.accept()
        else:
            if (self.ui_large):
                quit_msg = "Are you sure you want to quit?"
                reply = QtWidgets.QMessageBox.question(self, 'Quit?', quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
                if reply == QtWidgets.QMessageBox.Yes:   
                    self.finishedSig.emit()
                    event.ignore()
                else:
                    event.ignore()
            else:
                msgbox = QtWidgets.QMessageBox()
                msgbox.setIcon(QtWidgets.QMessageBox.Question)
                msgbox.setWindowTitle("Shutdown?")
                msgbox.setText("Which would you like to do?")
                msgbox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                msgbox.setFixedSize(200,200)
                msgbox.addButton(QtWidgets.QPushButton("Exit to\nConsole"), QtWidgets.QMessageBox.YesRole)
                msgbox.addButton(QtWidgets.QPushButton("Restart\nMoDaCS"), QtWidgets.QMessageBox.YesRole)
                msgbox.addButton(QtWidgets.QPushButton("Shutdown\nRaspPi"), QtWidgets.QMessageBox.YesRole)
                msgbox.addButton(QtWidgets.QPushButton("Restart\nRaspPi"), QtWidgets.QMessageBox.YesRole)
                msgbox.addButton(QtWidgets.QPushButton("Cancel"), QtWidgets.QMessageBox.RejectRole)
                #msgbox.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect())
                msgbox.exec_()

                if msgbox.clickedButton().text() == "Cancel":
                    event.ignore()
                elif msgbox.clickedButton().text() == "Exit to Console":
                    if not self.ui_int.server.enabled:
                        event.accept()
                    else:
                        self.finishedSig.emit()
                        event.ignore()
                else:
                    self.shutdown_mode = msgbox.clickedButton().text()
                    self.finishedSig.emit()
                    event.ignore()
        
    def finished(self):
        logging.info("Shutting down...")
        logging.debug("Stopping %i thread(s)" % len(self.runningThreads))
        sys.stdout.flush()
        self._i = 0
        self.runningThreads.allDone.connect(self.quit)
        self.runningThreads.countChange.connect(lambda n: logging.debug("Waiting for %i thread(s)" % n))

        shut_timer = QtCore.QTimer(self)
        shut_timer.timeout.connect(self.check_shutdown)
        shut_timer.start(1000)
    
    def check_shutdown(self):
        self._i += 1
        if self._i == 10:   #10 second timeout for stopping all threads
            self._i += 1
            bad_threads = []
            for i in self.runningThreads.active_threads:
                bad_threads.append(i.name)
            logging.warning("%s thread(s) unresponsive.  Force terminating." % bad_threads)
            
            for i in self.runningThreads.active_threads:
                i.terminate()
        elif self._i > 10:
            logging.warning("Thread(s) blocked, attempting to force quit application.")
            self.quit()

            
    def quit(self):
        self.readyToClose = True
        logging.info("Done.")
        self.close()     


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
    sys.exit(app.exec_())




