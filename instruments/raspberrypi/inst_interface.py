from time import sleep
from PyQt5 import QtCore
import threading
try:
    import RPi.GPIO as GPIO
except:
    from GPIOEmulator.EmulatorGUI import GPIO


class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    #inst_wid = instrument widget
    
    inputs = []
    outputs = ["digitalTrig"]
        
    #### Event functions ####
        
    def init(self):
        self.listen = True
        self.trigpin = int(self.inst_cfg["Initialization"]["triggerpin"])
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.trigpin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        except Exception as e:
            self.instLog.warning(e)
            
        #GPIO.add_event_detect(17, GPIO.RISING, callback=reset, bouncetime=300) 
        
        try:
            self.t_gpio = threading.Thread(target=self.gpio_monitor)
            self.t_gpio.start()   
        except Exception as e:
            self.instLog.warning(e)

        
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