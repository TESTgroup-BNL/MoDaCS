#System Imports
import json, ast, logging, os, traceback
from os import path
from glob import glob
#from objgraph import InstanceType
from array import array

#Qt Imports
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from asyncore import read
        

class QSignalHandler(logging.Handler):          #logging handler that emits all log entries through a specified signal
    
    def __init__(self, sig):
        super().__init__()
        self.sig = sig

    def emit(self, record):
        msg = self.format(record)
        self.sig.emit(msg)

    def write(self, m):
        pass

class Sig(QtCore.QObject):                      #Signal "wrapper" to allow programmatic definition of signals
    s = QtCore.pyqtSignal(object, object)
    
    def __init__(self, name):
        super().__init__()
        self.name = name
        
    def emit(self, object):
        self.s.emit(object, self.name)
        
    def connect(self, obj):
        self.s.connect(obj)

class RunningThreads(QtCore.QObject):
    allDone = QtCore.pyqtSignal()
    countChange = QtCore.pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.active_threads = []
        
    def __len__(self):
        return len(self.active_threads)
        
    def watchThread(self, thrd):
        if thrd.isRunning():
            self._addItem(thrd)
            #print("Thread added imm.: %s" % thrd)
        else:
            thrd.started.connect(lambda thrd=thrd: self._addItem(thrd))
        thrd.finished.connect(lambda thrd=thrd: self._removeItem(thrd))
        #print("Thread watched: %s" % thrd)
        
    def _addItem(self, thrd):
        #print("Thread added: %s" % thrd)
        if thrd not in self.active_threads:
            self.active_threads.append(thrd)
        self.countChange.emit(len(self.active_threads))
        #print(self.active_threads)
    
    def _removeItem(self, thrd):
        #print("Thread stopped: %s" % thrd)
        try:
            self.active_threads.remove(thrd)
        except Exception as e:
            raise Exception("Error tracking active threads: %s" % e)
        #print(self.active_threads)
        finally:          
            if len(self.active_threads) == 0:
                self.allDone.emit()
            else:
                self.countChange.emit(len(self.active_threads)) 
                        
class SBlock:
    def __init__(self, obj):
        self.target = obj
        
    def __enter__(self):
        self.target.blockSignals(True)
        return self.target
        
    def __exit__(self, *args):
        self.target.blockSignals(False) 
        
        
def my_excepthook(type, value, traceb):
    #print('Unhandled error:', type, value, traceb)
    for l in traceback.format_exception(type, value, traceb):
        print(l)
    #print(traceback.format_exception(type, value, traceb))  
