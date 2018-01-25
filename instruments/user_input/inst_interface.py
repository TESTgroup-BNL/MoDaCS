#Qt Imports
from PyQt5 import QtCore


class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    
    inputs = []
    outputs = ["fileName"]
    
    #UI Inputs and Outputs are forwarded to remote clients and can access the ui class
    #but otherwise are the same as "standard" inputs and outputs
    ui_inputs = ["updateName"]
    ui_outputs = []

    #### Required Functions ####
    def init(self, inst_vars, jsonFF):
        
        self.inst_vars = inst_vars

        #self.ui_signals["updateName"].connect(lambda val: self.signals["fileName"].emit(val)) 
        self.ui_signals["updateName"].connect(self.signals["fileName"].emit)                    
            
    def acquire(self):
        pass

    def close(self):
        pass

        

class Ui_interface(QtCore.QObject):
    
    updateName = QtCore.pyqtSignal(str)
    
    def init(self):
        self.ui.pb_setname.released.connect(self.setNewName)
        self.ui.tb_filename.returnPressed.connect(self.setNewName)
    
 
    def setNewName(self):
        self.updateName.emit(self.ui.tb_filename.text())
