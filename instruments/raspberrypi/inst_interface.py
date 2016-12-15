from time import sleep
from PyQt5 import QtCore
import threading, datetime, logging, subprocess
try:
    import RPi.GPIO as GPIO
    usingRPi = True
except:
    from GPIOEmulator.EmulatorGUI import GPIO
    usingRPi = False


class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    #inst_wid = instrument widget
    
    inputs = []
    outputs = ["digitalTrig"]
    
    ui_inputs = ["syncTimeSig"]
    ui_outputs = []
        
    #### Event functions ####
        
    def init(self):
        self.listen = True
        self.trigpin = int(self.inst_cfg["Initialization"]["triggerpin"])
        try:
            GPIO.setmode(GPIO.BCM)
            sleep(0.1)
        except:
            pass
        try:
            GPIO.setup(self.trigpin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        except Exception as e:
            self.instLog.warning(e)
            
        #GPIO.add_event_detect(17, GPIO.RISING, callback=reset, bouncetime=300) 
        
        try:
            self.t_gpio = threading.Thread(target=self.gpio_monitor)
            self.t_gpio.start()   
        except Exception as e:
            self.instLog.warning(e)

        self.ui_signals["syncTimeSig"].connect(self.setTime)
        
    def acquire(self):
        return                          #Call instrument acquisition method
        
    def close(self):
        self.listen = False
        
    def gpio_monitor(self):
        triggered = False
        self.instLog.info("Listening thread started.")
        while(self.listen == True):
            if GPIO.input(self.trigpin) == False and triggered == False:
                self.signals["digitalTrig"].emit("RaspPi")
                sleep(1)
                triggered = True
            elif triggered == True:
                triggered = False
            sleep(.01)
        self.instLog.info("Listening thread finished.")
        
    def setTime(self, new_dt):
        if usingRPi:
            subprocess.call('sudo date -s ' + new_dt.strftime('%Y-%m-%d'), shell=True)
            subprocess.call('sudo date -s ' + new_dt.strftime('%H:%M:%S'), shell=True)
        
        self.instLog.info("Clock set: %s %s" % (new_dt.strftime('%Y-%m-%d'), new_dt.strftime('%H:%M:%S')))

            
class Ui_interface(QtCore.QObject):
    
    #self.client_enabled = inst_interface.client_enabled
    syncTimeSig = QtCore.pyqtSignal(object)    #this has to go in the UI class so that it is executed by clients (the inst interface class is not)
    
    def init(self):
        #self.inst_ui.syncTimeSig = self.syncTimeSig
        self.syncTimeSig.connect(self.ui.dt_ClientClock.setDateTime)
        if self.provideControl:
            self.ui.pb_SetClock.released.connect(self.syncTime)
        else:
            self.ui.pb_SetClock.setVisible(False)
            
    def syncTime(self):
        self.syncTimeSig.emit(datetime.datetime.now())
        #self.ui.dt_ClientClock.setDateTime(QtCore.QDateTime.currentDateTime())