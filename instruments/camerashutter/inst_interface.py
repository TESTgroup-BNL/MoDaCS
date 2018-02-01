from time import sleep, time
from os import path, makedirs
    
from util import JSONFileField


class Inst_interface():
    
    #inst_vars.inst_log = logger object
    #inst_vars.inst_cfg = config object
    #inst_wid = instrument widget
    #inst_vars.inst_n = acquisition count
    
    inputs = ["shutterspeed"]
    outputs = []
        
    #### Event functions ####
        
    def init(self, inst_vars, jsonFF):
        
        self.inst_vars = inst_vars
        self.jsonFF = jsonFF
        
        try:
            self.cs = CameraShutter(int(self.inst_vars.inst_cfg["Initialization"]["shutterpin"]),int(self.inst_vars.inst_cfg["Initialization"]["focuspin"]),float(self.inst_vars.inst_cfg["Initialization"]["shutterDelay"]),float(self.inst_vars.inst_cfg["Initialization"]["focusDelay"]))       
        #Call instrument init
        except Exception as e:
            self.inst_vars.inst_log.warning(e)
        
        self.jsonFF.addField("Header")
        self.jsonFF["Header"]["Model"] = self.inst_vars.inst_cfg["InstrumentInfo"]["Model"]
        self.jsonFF["Header"]["Lens"] = self.inst_vars.inst_cfg["InstrumentInfo"]["Lens"]
        
        datafile = self.dataFile = path.join(self.inst_cfg["Data"]["absolutePath"], "Data", self.inst_cfg["Data"]["outputFilePrefix"] + "_data.json")
        makedirs(path.dirname(self.dataFile), exist_ok=True)
        self.jsonFF = JSONFileField(datafile)
        self.jsonFF.addField("Header")
        self.jsonFF.addElement("Configuration", {s:dict(self.inst_cfg.items(s)) for s in self.inst_cfg.sections()})
        self.jsonFF["Header"]["Model"] = self.inst_cfg["InstrumentInfo"]["Model"]
        self.jsonFF["Header"]["Lens"] = self.inst_cfg["InstrumentInfo"]["Lens"]
        self.jsonFF.addField("Data", fieldType=list)
        
    def acquire(self):
        t = time()
        self.cs.snapshot()                          #Call instrument acquisition method
        self.jsonFF["Data"].write("Image " + str(self.inst_vars.inst_n), recnum=self.inst_vars.globalTrigCount, timestamp=t, compact=True)

    def close(self):
        self.cs.shutdown()
        self.jsonFF["Header"]["Images Captured"] = self.inst_vars.inst_n

        
    def shutterspeed(self, val, ev):
        print("input from %s: %s" % (ev, val))

    def fileName(self, val):
        print(val)


class CameraShutter():

    
    def __init__(self, shutterpin, focuspin, shutterDelay, focusDelay):
        
        global GPIO     #This is very ugly and technically not allowed but makes it easy to prevent the emulator from
                        # popping up without the instrument running (causing the emulator window to get stuck open).
        try:
            import RPi.GPIO as GPIO
        except:
            try:
                from GPIOEmulator.EmulatorGUI import GPIO
            except:
                raise
            
        self.shutter = shutterpin
        self.focus = focuspin
        self.shutterDelay = shutterDelay
        self.focusDelay = focusDelay
        try:
            GPIO.setmode(GPIO.BCM)
            sleep(0.1)
        except:
            pass
        try:    
            GPIO.setup(self.shutter, GPIO.OUT)
            GPIO.output(self.shutter, False)
            GPIO.setup(self.focus, GPIO.OUT)
            GPIO.output(self.focus, False)
        except:
            pass
        
    def snapshot(self):
        GPIO.output(self.focus, True)
        sleep(self.focusDelay)
        GPIO.output(self.shutter, True)
        sleep(self.shutterDelay)
        GPIO.output(self.focus, False)
        GPIO.output(self.shutter, False)
        
    def shutdown(self):
        GPIO.output(self.shutter, False)
        GPIO.cleanup()
        
        