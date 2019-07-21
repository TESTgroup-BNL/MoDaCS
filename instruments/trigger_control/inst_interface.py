#Qt Imports
from PyQt5 import QtCore


class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    
    inputs = []
    outputs = ["trigger_out"]

    #### Required Functions ####
    def init(self, inst_vars, jsonFF):
        self.inst_vars = inst_vars                  
            
    def acquire(self):
        self.signals["trigger_out"].emit("trigger_control")

    def close(self):
        pass
