#Qt Imports
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QThread   

#System Imports
import logging
import time
from post_processing.post_common import PostProcessing

#App Event Imports
from status_led import StatusLED
import sftp


class AppEvents():
        
    def pre_init(self):            
        print("pre init!")            
        self.status_LED = StatusLED()
        for i in range(0,4):    #wait up to 1 sec to init
            if self.status_LED.ready:
                self.status_LED.setSpin.emit(255,0,0,0,0,0,100,0)
                break
            else:
                time.sleep(0.250)
   
    def pre_inst_init(self, run_config=None, isServer=True):
        #run_config and isServer loaded at this point
        print("pre insts!")        
        self.run_config = run_config
        if self.run_config.has_option("Data", "AutoTransfer"):
            if self.run_config["Data"]["AutoTransfer"] == "True":
                self.sftpEnabled = True     
        #self.status_LED.setLED.emit(255,200,0)
        self.status_LED.setSpin.emit(255,200,0,0,0,0,100,0)

    def post_init(self):
        print("post init!")
        self.status_LED.setBlink.emit(0,0,0,250,0,255,0,250,3)
    
    def globalTrig(self):
        print("gloabl trig!")        
        self.status_LED.setBlink.emit(0,0,255,100,0,255,0,100,2)
        
    def pre_shutdown(self):
        print("pre shutdown")        
        #self.status_LED.setLED.emit(255,0,255)
        self.status_LED.setSpin.emit(255,0,255,0,0,0,100,0)

    def server_post_shutdown(self, isRemoteShutdown):
        print("post shutdown")        
        if isRemoteShutdown and self.sftpEnabled:
            sftp_server = sftp.SFTP_Server(self.run_config)
        self.status_LED.setCenter.emit(10,0,0)

    def client_remote_shutdown(self):
        print("remote shutdown!")        
        if self.sftpEnabled:
            sftp_client = sftp.SFTP_Client(self.run_config)
            
            if sftp_client.receivePath is not None:
                self.post_processing(sftp_client.receivePath)
    
    def client_post_shutdown(self):
        print("client shutdown!")
        
    def post_processing(self, receivePath):
        post = PostProcessing(receivePath)
        post.read_data() #priority=["pi_gps_ublox","pixhawk_v2","px4_ulog","ici_thermal","gphoto2_cam","kml_builder"])



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
