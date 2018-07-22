from time import sleep
from PyQt5 import QtCore
import threading, datetime, logging, subprocess



class Inst_interface(QtCore.QObject):
    
    #inst_vars.inst_log = logger object
    #inst_cfg = config object
    #inst_wid = instrument widget
    
    inputs = []
    outputs = ["digitalTrig"]
    
    ui_inputs = ["syncTimeSig"]
    ui_outputs = []
        
    #### Event functions ####
        
    def init(self, inst_vars, jsonFF=None):
        try:
            import RPi.GPIO as GPIO
            self.usingRPi = True
        except:
            try:
                global GPIO     #This is very ugly and technically not allowed but makes it easy to prevent the emulator from
                                #popping up without the instrument running (causing the emulator window to get stuck open).
                from GPIOEmulator.EmulatorGUI import GPIO
            except:
                pass
            self.usingRPi = False
        
        
        self.inst_vars = inst_vars
        
        self.listen = True
        self.trigpin = int(self.inst_vars.inst_cfg["Initialization"]["triggerpin"])
        self.ledpin = int(self.inst_vars.inst_cfg["Initialization"]["ledpin"])
        try:
            GPIO.setmode(GPIO.BCM)
            sleep(0.1)
        except:
            pass
        try:
            GPIO.setup(self.trigpin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
            GPIO.setup(self.ledpin, GPIO.OUT)
            GPIO.output(self.ledpin, True)
        except Exception as e:
            self.inst_vars.inst_log.warning(e)
            
        #GPIO.add_event_detect(17, GPIO.RISING, callback=reset, bouncetime=300) 
        
        try:
            self.t_gpio = threading.Thread(target=self.gpio_monitor)
            self.t_gpio.start()   
        except Exception as e:
            self.inst_vars.inst_log.warning(e)

        self.ui_signals["syncTimeSig"].connect(self.setTime)
        
    def acquire(self):
        return                          #Call instrument acquisition method
        
    def close(self):
        self.listen = False
        GPIO.cleanup()
        
    def gpio_monitor(self):
        triggered = False
        led = False
        self.inst_vars.inst_log.info("Listening thread started.")
        while(self.listen == True):
            for i in range(0,50):
                if GPIO.input(self.trigpin) == False and triggered == False:
                    self.signals["digitalTrig"].emit("RaspPi")
                    sleep(1)
                    triggered = True
                elif triggered == True:
                    triggered = False
                sleep(.01)
            if led:
                led = False
            else:
                led = True
            GPIO.output(self.ledpin, led)
        self.inst_vars.inst_log.info("Listening thread finished.")
        
    def setTime(self, new_dt):
        if self.usingRPi:
            subprocess.call('sudo date -s ' + new_dt.strftime('%Y-%m-%d'), shell=True)
            subprocess.call('sudo date -s ' + new_dt.strftime('%H:%M:%S'), shell=True)
        
        self.inst_vars.inst_log.info("Clock set: %s %s" % (new_dt.strftime('%Y-%m-%d'), new_dt.strftime('%H:%M:%S')))

            
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