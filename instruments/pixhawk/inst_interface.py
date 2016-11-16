from PyQt5 import QtCore, QtGui
from PyQt5.Qt import pyqtSignal
import logging

class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    
    inputs = ["test"]
    outputs = ["trigger", "shutter"]
    
    ui_inputs = ["btn_test.released"]
    ui_outputs = ["pb1.setValue", "pb2.setValue", "pb3.setValue", "pb4.setValue", "pb5.setValue", "pb6.setValue", "pb7.setValue", "pb8.setValue", "pb_Battery.setValue", "pb_Vcc.setValue"]

    #### Common event functions ####
        
    def init(self):
        
        from dronekit import connect, VehicleMode
                
        connection_string = self.inst_cfg["Initialization"]["Connection"]
        self.instLog.info("Connecting to vehicle on: %s" % (connection_string,))
    
        try:
            self.vehicle = connect(connection_string, wait_ready=False, baud=57600, heartbeat_timeout=5)
        except Exception as e:
            raise Exception("Error connecting: %s" % e)

        try:
            self.vehicle   
        except Exception:
            raise Exception("Init failed")
        
        try:
            self.ui_signals["btn_test.released"].connect(lambda: print("Button pressed!"))
        except Exception as e:
            raise e
        
        try:
            self.vehicle.cb_interface = Callback_interface(self.ui_signals)
            self.vehicle.cb_interface.trigger.connect(lambda val: self.signals["trigger"].emit(val))
            self.vehicle.cb_interface.shutter.connect(lambda val: self.signals["shutter"].emit(val))
#            print("\nPrint all parameters (iterate `vehicle.parameters`):")
            
#            for key, value in self.vehicle.items():
#                print(" Key:%s Value:%s" % (key,value))
#                raise Exception("test")
            @self.vehicle.on_message('POWER_STATUS')
            def callback(self, attr_name, value):
                self.cb_interface.updatePower(value)

            @self.vehicle.on_attribute('battery')
            def callback(self, attr_name, value):
                self.cb_interface.updateBatt(value)
        
            @self.vehicle.on_attribute('channels')
            def callback(self, attr_name, value):
                self.cb_interface.doUpdate(value)
                
            #@self.vehicle.on_attribute('servo_output_raw')
            #def callback(self, attr_name, value):
            #    self.cb_interface.servoUpdate(attr_name, value)
                
#            @self.vehicle.on_message('*')
#            def callback(self, attr_name, value):
#                print("%s: %s" % attr_name, data)   
        
        except Exception as e:
            raise Exception("Failed to setup callback: %s" % e)
        
    def acquire(self):
        
            self.instLog.info(" GPS: %s" % self.vehicle.gps_0)
            self.instLog.info(" Battery: %s" % self.vehicle.battery)
            self.instLog.info(" Last Heartbeat: %s" % self.vehicle.last_heartbeat)
            self.instLog.info(" Is Armable?: %s" % self.vehicle.is_armable)
            self.instLog.info(" System status: %s" % self.vehicle.system_status.state)
            self.instLog.info(" Mode: %s" % self.vehicle.mode.name)
        
    def close(self):
        self.vehicle.close()
    
    #Method to process input signals
    def input(self, data, name):
        print("input from %s, %s" % name, data)


class Callback_interface(QtCore.QObject):
    trigger = pyqtSignal(str)
    shutter = pyqtSignal(int)
    battSig = pyqtSignal(str)
    
    def __init__(self, ui_signals):
        super().__init__()
        self.ui_signals = ui_signals
        self.old_data = {}
        self._power_currentcolor = 0
        self._old_shutter = 0
        self._old_trig = 0
        
    def doUpdate(self, value):
        
        #Code to process new data; any signals to the outside world (i.e. triggers) should be emitted here
        #self.data.emit(value)
        self.doUIUpdate(value)
        if not self._old_shutter == int(value['6']):
            self.shutter.emit(int(value['6']))
            self._old_shutter = int(value['6'])
            
        if not self._old_trig == int(value['7']):
            if int(value['7']) > 1700:
                self.trigger.emit("Remote")
            self._old_trig = int(value['7'])
        
    def servoUpdate(self, name, value):
        if not (value.servo8_raw == self.old_data):
            self.old_data = value.servo8_raw
            #print(value)
            if value.servo8_raw > 1500:
                self.trigger.emit("Auto")

    def updateBatt(self, value):
        if value.level is None:
            self.ui_signals["pb_Battery.setValue"].emit(0)
        else:
            self.ui_signals["pb_Battery.setValue"].emit(int(value.level))
    
    def updatePower(self, value):
        self.ui_signals["pb_Vcc.setValue"].emit(int(value.Vcc))
    
    
    def doUIUpdate(self, value):
        self.ui_signals["pb1.setValue"].emit(int(value['3']))
        self.ui_signals["pb2.setValue"].emit(int(value['4']))
        self.ui_signals["pb3.setValue"].emit(int(value['2']))
        self.ui_signals["pb4.setValue"].emit(int(value['1']))
        
        self.ui_signals["pb5.setValue"].emit(int(value['5']))
        self.ui_signals["pb6.setValue"].emit(int(value['6']))
        self.ui_signals["pb7.setValue"].emit(int(value['7']))
        self.ui_signals["pb8.setValue"].emit(int(value['8']))
        


###NOTE: Runs in Main UI Thread. DO NOT BLOCK!
class Ui():
    
    def init(self):
        self._power_currentcolor = 0
        self.inst_ui.pb_Vcc.valueChanged.connect(self.update_pb_color)
        
    
    def update_pb_color(self):
        w = self.inst_ui.pb_Vcc
        v = w.value()
        if self._power_currentcolor != 2 and (v < 4300 or v > 5500):
            self.set_style_background(w, 255, 0, 0)
            self._power_currentcolor = 2
        elif self._power_currentcolor != 1 and (v < 4700 or v > 5100):
            self.set_style_background(w, 255, 255, 0)
            self._power_currentcolor = 1
        elif self._power_currentcolor != 0 and (v >= 4700 and v <= 5100):
            self.set_style_background(w, 0, 255, 0)
            self._power_currentcolor = 0
            
    def set_style_background(self, w, r, g, b):
        s = w.styleSheet()
        start = s.find("background-color:")
        w.setStyleSheet(s.replace(s[start + 17 : w.styleSheet().find(";",start)], "rgb(" + str(r) + ", " + str(g) + ", " + str(b) + ")"))