#Qt Imports
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QThread   
#System Imports
import logging

class shutterspeed(QObject):
    output = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
    
    def init(self):
        self.inputs = {}
        self.inputs["speed"] = 1
    
    def input(self, data, name):
        self.output.emit(data/2)
        
        
class remote_trig(QObject):
    output = pyqtSignal(str)
    
    def init(self):
        self.data_old = {'6':0}
    
    def input(self, data, name):
        if not data['6'] == self.data_old['6']:
            self.data_old['6'] = data['6']
            if (data['6'] < 1500 and data['6'] > 0):
                self.output.emit("Remote")


class testthing(QObject):
    output = pyqtSignal(str)
    
    def init(self):
        logging.info("hello from testthing init: %s" % int(QThread.currentThreadId()))
    
    def input(self, data, name):
        logging.info("hello from testthing, %s: %s" % (name, int(QThread.currentThreadId())))
        
        
        
def pre_init:
    pass

def post_init:
    pass

def client_post(run_config, atFinished):
    print("Hi, I'm doing the post processing!")
    
    atFinsihed()
    pass