#System Imports
from os import path, makedirs
import logging
from time import sleep, time, strftime

#MoDaCS Imports
from util import JSONFileField, SBlock

#Other Imports
from pylepton import Lepton
import numpy as np


class Inst_interface(QtCore.QObject):
    
    #inst_vars.inst_log = logger object
    #inst_vars.inst_cfg = config object
    #inst_wid = instrument widget
    #inst_n = acquisition count
    #instPath = instrument's root folder

        
    #### Event functions ####
        
    def init(self, inst_vars, jsonFF):
        
        self.inst_vars = inst_vars
        self.jsonFF = jsonFF
        
        sleep(1)

        #Init camera   
        self.datbuf = np.ndarray((60, 80, 1), dtype=np.uint16)
        
        try:
            self.lepton = Lepton("/dev/spidev32766.0")
            self.lepton.__enter__()
        except Exception as e:
            self.inst_vars.inst_log.error("Error starting thermal cam: %s" % e)
        
        #Create output file
        self.dataFile = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], self.inst_vars.inst_cfg["Data"]["outputFilePrefix"] + "_data.json")
        self.imgPath = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], "Thermal")
        makedirs(path.dirname(self.dataFile), exist_ok=True)
        makedirs(self.imgPath, exist_ok=True)
        
        self.jsonFF.addField("Header")
        self.jsonFF["Header"]["Height"] = self.inst_vars.inst_cfg["InstrumentInfo"]["Height"]
        self.jsonFF["Header"]["Width"] = self.inst_vars.inst_cfg["InstrumentInfo"]["Width"]

        
    def acquire(self):
        #Call instrument acquisition method
        #imageFile = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], str(strftime("%Y-%m-%d_%H%M%S") + "Image_" + str(self.inst_n) + ".x16"))

        try:
            t = time()

            self.lepton.capture(self.datbuf, debug_print=False)

            #for x in range(0,60):
            #    for y in range(0,80):
            #print(np.array2string(a, formatter={"%5i"}))
            #        print('{0:5d}'.format(a[x][y][0]), end='')
            #    print("\n")
            #sleep(1)
            
        except Exception as e:
            raise e
    
        #Save metadata
        imgFile = path.join(self.imgPath, "Lepton_" + strftime("%Y%m%d_%H%M%S") + ".dat")
        self.jsonFF["Data"].write(imgFile, recnum=self.inst_vars.globalTrigCount, timestamp=t, compact=True)
        
        #Save binary
        with open(imgFile, 'wb') as out_file:
            out_file.write(self.datbuf)
        
    def close(self):
        self.lepton.__exit__(None,None,None)