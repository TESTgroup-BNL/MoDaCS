'''
Created on Jul 13, 2016

@author: amcmahon
'''
import sys
import threading
import time
import datetime
import logging
import sched

sys.path.append("..")
sys.path.append(".")

from PyQt5.QtCore import QThread, QObject, pyqtSignal

class Signals(QObject):
      
    corr_tick = pyqtSignal()

class cTimer():   
       
    b_setInt = 10
    b_corrInt = 0
    avg_n = 0
    corrected_ms = 0 
    correction = 0
    correction_arr = []  
    starttime = 0 
    
    def __init__(self):
        self.sig = Signals()
        self.sig.corr_tick.connect(self.corr_tickadd)
        
        self.backSched = sched.scheduler()
        self.bsched_t = threading.Thread(target=self.bsched_worker)
        self.bsched_t.start()
        
    def corr_tickadd(self):
        self.corrected_ms += 10
        
    def bsched_worker(self):
        self.starttime = time.time()
        while 1:
            self.backSched.enter(self.b_corrInt, 1, self.b_tick)
            self.backSched.run()
        
    def b_tick(self):
        actual_dT = time.time() - self.starttime
        self.sig.corr_tick.emit()
        self.correction_arr.append(self.b_setInt - actual_dT*1000)
        if self.avg_n < 1000:
            self.avg_n += 1
        else:
            del self.correction_arr[0]
        self.correction = sum(self.correction_arr) / self.avg_n
        err = (self.correction / max(self.b_setInt, .000001)) * 100
        logging.debug('correction: %f  set dT: %d  actual dT: %f  %% Error: %f', self.correction, self.b_setInt, actual_dT, err)
        self.b_corrInt = max(self.b_setInt + self.correction, 0)
        self.starttime = time.time()
    