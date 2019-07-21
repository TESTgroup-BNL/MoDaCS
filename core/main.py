'''
Created on Jul 13, 2016

@author: amcmahon
'''
#System Imports
import sys, getopt, logging, configparser, copy, importlib, subprocess, json
from time import time, strftime, localtime, sleep
from os import makedirs, path, execl, chdir
from os.path import dirname, abspath

#Qt Imports
from PyQt5 import QtWidgets, QtCore, QtNetwork, QtGui
from PyQt5.QtCore import QDir, QProcess

#RasPi Imports
from status_led import StatusLED

#MoDaCS Imports
chdir(dirname(dirname(abspath(__file__))))
sys.path.append(dirname(abspath(__file__)))
sys.path.append(dirname(dirname(abspath(__file__))))

from inst_common import inst_init
from events_common import events_init
import ui.ui_interface
from util import QSignalHandler, RunningThreads, my_excepthook, JSONFileField
import sftp
import event_handlers


class Main(QtWidgets.QMainWindow):
    
    #status = QtCore.pyqtSignal(str)
    inst_addedSig = QtCore.pyqtSignal(object, str)
    event_addedSig = QtCore.pyqtSignal(object, str)
    event_reloadSig = QtCore.pyqtSignal(object, str)
    event_reloadRemoteSig = QtCore.pyqtSignal(object, str)
    globalTrig = QtCore.pyqtSignal(str)
    logupdateSig = QtCore.pyqtSignal(str)
    finishedSig = QtCore.pyqtSignal(str)
    uiReadySig = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        QtWidgets.QMainWindow.__init__(self)
        
        event_handlers.pre_init()
        self.status_LED = StatusLED()
        self.status_LED.setLED.emit(255,0,0)
        
        self.active_insts = {}
        self.inst_list = []
            
        self.event_objs = {}
        self.reset_lambdas = []
        
        self.startTime = 0
        self.count = 0
        
        self.globalTrigCount = -1
        self.globalTrig.connect(self.incGlobalTrigCount)
        self.globalTrig.connect(lambda: self.status_LED.setBlink.emit(0,0,255,100,0,255,0,100,2))
        
        self.finishedSig.connect(self.finished)
        self.readyToClose = False
        self.shutdown_mode = ""
        self.sftpEnabled = False
        
        self.displayOnly = False
        self.instrumentPaths = None
        
        self.ui_large = False
        self.runningThreads = RunningThreads()
        
        try:
            from os import uname
            if uname()[4].startswith("arm"):
                self.usingRasPi = True
                print("Running on RaspPi (or other ARM device)")
            else:
                self.usingRasPi = False
        except (AttributeError, ImportError):
            self.usingRasPi = False
              
        #Initialize config parser and logger
        cp = configparser.ConfigParser()
        opts, args = getopt.getopt(sys.argv[1:],"hc:f:o", ["run_config="])
        run_config = path.join('.', 'core', 'run_cfg.ini')
        try:
            for opt, arg in opts:
                if opt in ("-h", "--help", "?", "help"):
                    print("MoDaCS Main Module\n\nUsage: main.py [-c <run config file>]\n\nOptions:\n     -c, --run_config : Specifies an alternate run configuration file.  (Default is 'core\\run_cfg.ini'.)\n\n-o, --open : Prompts user to select an existing 'RunData.json' file to load data from\n\n-f, --file : Open a spcified 'RunData.json' file to load data from")
                    sys.exit()
                if opt in ("-c", "--run_config"):
                    run_config = arg
                    print("RUN CONFIG:")
                    print(opt)
                    print(arg)
                    print(sys.argv)
                if opt in ("-f", "--file", "-o", "--open"):
                    self.displayOnly = True
                    try:
                        if opt in ("-o", "--open"):
                            fname, typ = QtWidgets.QFileDialog.getOpenFileName(None, 'Open Global Record File', ".", "JSON files (*.json)")
                        else:
                            fname = arg
                        with open(fname) as rdJSON:
                            runData = json.load(rdJSON)
                        self.globalRecs = runData["globalRecs"]
                        self.instrumentPaths = runData["InstrumentPaths"]
                        cp.read_dict(runData["Configuration"])
                        self.dataPath = path.dirname(fname)
                        logFile = None
                        cp["Server"]["enabled"] = "False"
                        cp["Client"]["enabled"] = "False"
                        cp["UI"]["Size"] = "large"
                        
                        origpath = cp["Data"]["Location"]
                        
                        for inst, instpath in self.instrumentPaths.items():
                            self.instrumentPaths[inst] = path.join(self.dataPath, path.split(instpath)[1])

                    except Exception as e:
                        print("Error loading run configuration data: ", str(e))
                        raise      
            
            if self.displayOnly == False:
                cp.read(run_config)
                if self.usingRasPi:
                    if cp["UI"]["WaitForNTP"] == "True":
                        self.waitForNTP()
                
                self.dataPath = path.join(cp["Data"]["location"], str(strftime("%Y-%m-%d_%H%M%S")))
                
                makedirs(self.dataPath, exist_ok=True)
                logFile = path.join(self.dataPath, str(strftime("%Y-%m-%d_%H%M%S_RunLog.txt")))
                
        except KeyError:
            print("Error: run_cfg file missing or missing required keys")
            raise
        
        logging.basicConfig(
        filename=logFile,
        level=logging.DEBUG,
        format='[%(levelname)-10s] (%(threadName)-10s), %(asctime)s, %(message)s') #datefmt='%Y/%m/%d %I:%M:%S'
        
        if not self.displayOnly:
            sh = logging.StreamHandler()
            formatter = logging.Formatter("[%(levelname)-10s] (%(threadName)-10s), %(asctime)s, %(message)s")
            sh.setFormatter(formatter)
            
            logging.getLogger().addHandler(sh)
        
        #Initialize Main UI
        if cp.has_option("UI", "Size"):
            if cp["UI"]["Size"] == "large":
                self.ui_large = True
        self.ui_int = ui.ui_interface.UI_interface(self, cp, self.active_insts, self.inst_list, self.displayOnly)
        self.run_cfg = cp
        self.run_cfg["Data"]["dataPath"] = self.dataPath
        
        if cp.has_option("Data", "AutoTransfer"):
            if cp["Data"]["AutoTransfer"] == "True":
                self.sftpEnabled = True
        
        #Connect event UI widgets
        self.globalTrig.connect(lambda source="" : self.ui_int.ui.treeWidget.topLevelItem(0).setText(1, source))
        self.inst_addedSig.connect(self.ui_int.ui_set_inst_table)
        if not self.displayOnly:
            self.inst_addedSig.connect(self.addInstPath)
        self.event_addedSig.connect(self.ui_int.ui_eventtree_add)
        self.event_reloadSig.connect(self.ui_int.ui_eventreload)

        logging.getLogger().addHandler(QSignalHandler(self.logupdateSig))
        self.logupdateSig.connect(self.ui_int.ui.plainTextEdit.appendPlainText)
        
        #Connect remote signals if server is enabled
        self.isServer = self.ui_int.server.enabled
        if self.ui_int.server.enabled:
            self.globalTrig.connect(lambda val="": self.ui_int.server.sendSig.emit("main_app.globalTrig", val))
            self.logupdateSig.connect(lambda val="": self.ui_int.server.sendSig.emit("main_app.logupdateSig", "[Remote] " + val))
       
        if not self.ui_int.client.enabled:
            self.ui_int.ui.btn_ManTrig.released.connect(lambda: self.globalTrig.emit("Manual"))
        else:
            self.ui_int.ui.btn_RemSD.released.connect(self.remoteShutdown)
            
        #Initialize Main Data File
        if self.displayOnly:
            sorted_recs = sorted(self.globalRecs.items(), key=lambda x: x[1])
            for key, rec in sorted_recs:
                self.ui_int.ui_addGlobalRec(key, rec[0], rec[1])
            
        else:
            self.jsonFF = JSONFileField(path.join(self.dataPath, "RunData.json"))
            self.jsonFF.addElement("Configuration", {s:dict(cp.items(s)) for s in cp.sections()})
            self.jsonFF.addField("globalRecs", fieldType=object)
            self.jsonFF.addField("InstrumentPaths", fieldType=object)
        
        self.status_LED.setLED.emit(255,200,0)
        
        #Initialize Instruments
        try:
            mainthreadlist = cp["MainThread"]
        except:
            mainthreadlist = []
        inst_init(self, cp["Active_Insts"], self.dataPath, mainthreadlist, self.displayOnly, self.instrumentPaths)
        
        #Initialize Events
        events_init(self, cp["Events"], self.displayOnly)

        #Initialize inst widgets
        self.ui_int.ui_init_widgets()
        
        if self.ui_int.client.enabled:
            #Start client thread
            self.ui_int.client.thread.start()
        
        if (self.ui_int.server.enabled or (not self.ui_int.client.enabled)) and (self.displayOnly == False):
            #Start instrument threads
            for key, i in self.active_insts.items():
                i.inst_thread.start()
                
        if self.ui_int.server.allowControl:
            self.ui_int.server.controlClient.thread.start()
    
        #self.status_LED.setColor(0,255,0)
        event_handlers.post_init()
        self.status_LED.setBlink.emit(0,0,0,250,0,255,0,250,3)

    
    def getGlobalTrigCount(self):
        return self.globalTrigCount
    
    def incGlobalTrigCount(self, source):
        self.globalTrigCount += 1
        try:
            logging.debug("Global trigger: %s, %i" % (source, self.globalTrigCount))
        except Exception as e:
            print(e)
        self.ui_int.ui_addGlobalRec(self.globalTrigCount, strftime("%H"+":"+"%M"+":"+"%S", localtime()), source)
        self.jsonFF["globalRecs"][str(self.globalTrigCount)] = [strftime("%H"+":"+"%M"+":"+"%S", localtime()), source]
            
    def loadRecs(self):
        self.newConfigFile = QtWidgets.QFileDialog.getOpenFileName(None, 'Open Global Record File', self.run_cfg["Data"]["location"], "JSON files (*.json)")
        if not self.newConfigFile == "":
            self.shutdown_mode = "New Config"
            self.close()
            
    def switchToAcq(self):
        self.shutdown_mode = "Restart\nMoDaCS"
        self.close()
            
    def addInstPath(self, inst_cfg):
        self.jsonFF["InstrumentPaths"][inst_cfg["Data"]["Inst"]] = path.join(inst_cfg["Data"]["absolutePath"], inst_cfg["Data"]["outputFilePrefix"])
    
    def remoteShutdown(self):
        msgbox = ShutdownPopup()
        if msgbox.clickedButton().text() == "Cancel":
            return
        
        if self.sftpEnabled:
            sftp_client = sftp.SFTP_Client(self.run_cfg)
        
        if msgbox.clickedButton().text() == "Exit to Console":
            logging.info("Exiting remote instance...")
            self.ui_int.client.sendSig.emit("main_app.finishedSig", "Close")
        else:
            remSD_mode = msgbox.clickedButton().text()
            logging.info("Remote shutdown: " + remSD_mode)      
            self.ui_int.client.sendSig.emit("main_app.finishedSig", remSD_mode)
        
            
    def closeEvent(self, event):
        if self.readyToClose:
            self.status_LED.setLED.emit(0,0,0)
            sleep(0.1)
            #print("Using Rasp Pi still? %s" % self.usingRasPi)
            if self.usingRasPi:
                if self.shutdown_mode == "Restart\nMoDaCS":
                    #subprocess.call(QDir.toNativeSeparators(sys.executable + ' "' + sys.argv[0] + '"'))
                    #subprocess.Popen('/home/pi/Desktop/startMoDaCS.sh', shell=True)
                    #subprocess.Popen('startx', shell=True)
                    execl(sys.executable,sys.executable, * sys.argv)
                    #execv(sys.executable, ['python3'] + sys.argv)
                    
                elif self.shutdown_mode == "Shutdown\nRaspPi":
                    subprocess.call('sudo shutdown now', shell=True)
                    
                elif self.shutdown_mode == "Restart\nRaspPi":
                    subprocess.call('sudo shutdown -r now', shell=True)
                    
                elif self.shutdown_mode == "New Config":
                    print(QDir.toNativeSeparators(sys.executable + ' "' + sys.argv[0] + '" -f "' + self.newConfigFile[0] + '"'))
                    subprocess.call(QDir.toNativeSeparators(sys.executable + ' "' + sys.argv[0] + '" -f "' + self.newConfigFile[0] + '"'))
                    #QProcess.startDetached(QDir.toNativeSeparators(sys.executable + ' "' + sys.argv[0] + '" -o "' + self.newConfigFile[0] + '"'))                
            else:
                if self.shutdown_mode == "Restart\nMoDaCS":
                    subprocess.Popen(QDir.toNativeSeparators(sys.executable + ' "' + sys.argv[0] + '"'))
                    #subprocess.Popen('/home/pi/Desktop/startMoDaCS.sh', shell=True)
                    #execv(sys.executable, ['python3'] + sys.argv)
                    
                elif self.shutdown_mode == "Shutdown\nRaspPi":
                    print("Shutdown PC")
                    
                elif self.shutdown_mode == "Restart\nRaspPi":
                    print("Restart PC")

                elif self.shutdown_mode == "New Config":
                    #print(QDir.toNativeSeparators(sys.executable + ' "' + sys.argv[0] + '" -o "' + self.newConfigFile[0] + '"'))
                    subprocess.Popen(QDir.toNativeSeparators(sys.executable + ' "' + sys.argv[0] + '" -f "' + self.newConfigFile[0] + '"'))
                    #QProcess.startDetached(QDir.toNativeSeparators(sys.executable + ' "' + sys.argv[0] + '" -o "' + self.newConfigFile[0] + '"'))   
            event.accept()
        else:
            if (self.ui_large):
                if self.shutdown_mode == "New Config":
                    quit_msg = "This will restart MoDaCS.  Continue?"
                else:
                    quit_msg = "Are you sure you want to quit?"
                reply = QtWidgets.QMessageBox.question(self, 'Quit?', quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
                if reply == QtWidgets.QMessageBox.Yes:   
                    self.finishedSig.emit("")
                    if self.readyToClose:
                        self.closeEvent(event)      #to catch when "finished" and "quit" execute before event is ignored
                    else:
                        event.ignore()
                else:
                    event.ignore()
            else:
                msgbox = ShutdownPopup()
                
                if msgbox.clickedButton().text() == "Cancel":
                    event.ignore()
                elif msgbox.clickedButton().text() == "Exit to Console":
                    if not self.ui_int.server.enabled:
                        event.accept()
                    else:
                        self.finishedSig.emit("")
                        event.ignore()
                else:
                    self.shutdown_mode = msgbox.clickedButton().text()
                    self.finishedSig.emit("")
                    event.ignore()
                    
    def finished(self, mode=""):
        
        if mode is not "":
            self.shutdown_mode = mode
            self.isRemoteShutdown = True
            logging.info("Remotely initiated shutdown...")
        else:
            self.isRemoteShutdown = False
            logging.info("Shutting down...")
        
        self.status_LED.setLED.emit(255,0,255)
            
        try:
            self.jsonFF.close()
        except:
            pass

        if len(self.runningThreads) == 0:
            self.quit()
        else:
            logging.debug("Stopping %i thread(s)" % len(self.runningThreads))
            sys.stdout.flush()
            self._i = 0
            
            self.runningThreads.allDone.connect(self.quit)
            self.runningThreads.countChange.connect(lambda n: logging.debug("Waiting for %i thread(s)" % n))
    
            self.shut_timer = QtCore.QTimer(self)
            self.shut_timer.timeout.connect(self.check_shutdown)
            self.shut_timer.start(1000)
    
    def check_shutdown(self):
        self._i += 1
        
        if self._i > 10 or self.runningThreads.active_threads == 0:
            logging.warning("Thread(s) blocked, attempting to force quit application.")
            self.quit()
            
        elif self._i == 10:   #5 second timeout for stopping all threads
            self._i += 1
            bad_threads = []
            for i in self.runningThreads.active_threads:
                bad_threads.append(i.objectName())
            logging.warning("%s thread(s) unresponsive.  Force terminating." % bad_threads)
            
            for i in self.runningThreads.active_threads:
                i.terminate()

            
    def quit(self):
        logging.info("Done.")
        try:
            self.shut_timer.stop()
        except AttributeError:
            pass
        if self.sftpEnabled and self.isServer and self.isRemoteShutdown:
            self.sftpEnabled = False
            sftp_server = sftp.SFTP_Server(self.run_cfg, event_handlers.client_post, self.quit)
        else:
            self.readyToClose = True
            self.close()
            


    def waitForNTP(self):
        subprocess.call("sudo service ntp stop", shell=True)
        for i in range(0, 60): #try for 1 minute
            print("Waiting for NTP...")
            self.status_LED.setBlink.emit(255,200,0,100,255,0,0,100,3)
            try:
                ret = subprocess.check_output("sudo ntpdate -t 0.5 192.168.1.100", shell=True)
                break
                return
            except:
                pass
        
class ShutdownPopup(QtWidgets.QMessageBox):
    def __init__(self):
        super().__init__()
        self.setIcon(QtWidgets.QMessageBox.Question)
        self.setWindowTitle("Shutdown?")
        self.setText("Which would you like to do?")
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setFixedSize(200,200)
        self.addButton(QtWidgets.QPushButton("Exit to\nConsole"), QtWidgets.QMessageBox.YesRole)
        self.addButton(QtWidgets.QPushButton("Restart\nMoDaCS"), QtWidgets.QMessageBox.YesRole)
        self.addButton(QtWidgets.QPushButton("Shutdown\nRaspPi"), QtWidgets.QMessageBox.YesRole)
        self.addButton(QtWidgets.QPushButton("Restart\nRaspPi"), QtWidgets.QMessageBox.YesRole)
        self.addButton(QtWidgets.QPushButton("Cancel"), QtWidgets.QMessageBox.RejectRole)
        #self.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect())
        self.exec_()      
        

if __name__ == '__main__':
    sys.excepthook = my_excepthook
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    if not window.ui_large:
        window.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    window.show()
    sys.exit(app.exec_())





