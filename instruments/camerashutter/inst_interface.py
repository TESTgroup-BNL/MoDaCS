from time import sleep, time
from os import path
try:
    import RPi.GPIO as GPIO
except:
    from GPIOEmulator.EmulatorGUI import GPIO
    
from util import JSONFileField


class Inst_interface():
    
    #instLog = logger object
    #inst_cfg = config object
    #inst_wid = instrument widget
    #inst_n = acquisition count
    
    inputs = ["shutterspeed"]
    outputs = []
        
    #### Event functions ####
        
    def init(self):
        try:
            self.cs = CameraShutter(int(self.inst_cfg["Initialization"]["shutterpin"]))       #Call instrument init
        except Exception as e:
            self.instLog.warning(e)
        
        datafile = self.dataFile = path.join(self.inst_cfg["Data"]["absolutePath"], self.inst_cfg["Data"]["outputFilePrefix"] + "_data.json")
        self.jsonFF = JSONFileField(datafile)
        self.jsonFF.addField("Header")
        self.jsonFF["Header"]["Model"] = self.inst_cfg["InstrumentInfo"]["Model"]
        self.jsonFF["Header"]["Lens"] = self.inst_cfg["InstrumentInfo"]["Lens"]
        self.jsonFF.addField("Data", fieldType=list)
        
    def acquire(self):
        t = time()
        self.cs.snapshot()                          #Call instrument acquisition method
        self.jsonFF["Data"].write("Image " + str(self.inst_n), recnum=self.globalTrigCount, timestamp=t, compact=True)

    def close(self):
        self.cs.shutdown()
        self.jsonFF["Header"]["Images Captured"] = self.inst_n
        self.jsonFF.close()

        
    def shutterspeed(self, val, ev):
        print("input from %s: %s" % (ev, val))



class CameraShutter():
    
    def __init__(self, shutterpin):
        self.shutter = shutterpin
        try:
            GPIO.setmode(GPIO.BCM)
            sleep(0.1)
        except:
            pass
        try:    
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
        
        