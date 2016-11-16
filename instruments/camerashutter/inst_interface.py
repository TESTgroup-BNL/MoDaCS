from time import sleep
try:
    import RPi.GPIO as GPIO
except:
    from GPIOEmulator.EmulatorGUI import GPIO


class Inst_interface():
    
    #instLog = logger object
    #inst_cfg = config object
    #inst_wid = instrument widget
    
    inputs = ["shutterspeed"]
    outputs = []
        
    #### Event functions ####
        
    def init(self):
        try:
            self.cs = CameraShutter(int(self.inst_cfg["Initialization"]["shutterpin"]))       #Call instrument init
        except Exception as e:
            self.instLog.warning(e)
        
    def acquire(self):
        self.cs.snapshot()                          #Call instrument acquisition method
        
    def close(self):
        self.cs.shutdown()


        
    def shutterspeed(self, val, ev):
        print("input from %s: %s" % (ev, val))



class CameraShutter():
    
    def __init__(self, shutterpin):
        self.shutter = shutterpin
        try:
            GPIO.setmode(GPIO.BCM)       
            GPIO.setup(self.shutter, GPIO.OUT)
            GPIO.output(self.shutter, False)
        except:
            pass
        
    def snapshot(self):
        GPIO.output(self.shutter, True)
        sleep(.5)
        GPIO.output(self.shutter, False)
        
    def shutdown(self):
        GPIO.output(self.shutter, False)
        
        