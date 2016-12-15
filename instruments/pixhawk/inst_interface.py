from PyQt5 import QtCore, QtGui
from PyQt5.Qt import pyqtSignal
import logging, json, time
from util import JSONWriter
from os import path

class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    
    inputs = ["test"]
    outputs = ["trigger", "shutter"]
    
    ui_inputs = ["ui.btn_test.released"]
    ui_outputs = ["ui.pb1.setValue", "ui.pb2.setValue", "ui.pb3.setValue", "ui.pb4.setValue", "ui.pb5.setValue", "ui.pb6.setValue", "ui.pb7.setValue", "ui.pb8.setValue", "ui.pb_Battery.setValue", "ui.pb_Vcc.setValue"]

    #### Common event functions ####
        
    def init(self):
        
        import dronekit
        #from dronekit import connect, VehicleMode
        
        self.instLog.info("Waiting for Pixhawk to initialize...")
        time.sleep(2)   #Wait for Pixhawk to finish booting
        connection_string = self.inst_cfg["Initialization"]["Connection"]
        self.instLog.info("Connecting to vehicle on: %s" % (connection_string,))
    
        try:
            self.vehicle = dronekit.connect(connection_string, wait_ready=False, baud=57600, heartbeat_timeout=5)
        except Exception as e:
            raise Exception("Error connecting: %s" % e)

        try:
            self.vehicle   
        except Exception as e:
            raise Exception("Init failed: %s" % e)
        
        d = {}
        try:
            mission_list = self.download_mission()
        except Exception as e:
            self.instLog.error("Error downloading flight plan")
        try:
            home = self.vehicle.home_location
            if home is None:
                self.instLog.warning("Home location not set")
                home = dronekit.LocationGlobal(0,0,0)
                
            if mission_list is not None:
                self.save_mission(path.join(self.inst_cfg["Data"]["absolutePath"], self.inst_cfg["Data"]["outputFilePrefix"] + "_mission.waypoints"), mission_list)
                d["Flight Plan"] = []
                d["Flight Plan"].append([0,1,0,16,0,0,0,0,home.lat,home.lon,home.alt,1])
                for cmd in mission_list:
                    #d["Flight Plan"].append(cmd)
                    d["Flight Plan"].append([cmd.seq,cmd.current,cmd.frame,cmd.command,cmd.param1,cmd.param2,cmd.param3,cmd.param4,cmd.x,cmd.y,cmd.z,cmd.autocontinue])
                print(d)
        #except TypeError:
        #    self.instLog.warning("No flight plan loaded")
        except Exception as e:
            self.instLog.error("Error saving flight plan: %s" % e)

        self.dataFile = path.join(self.inst_cfg["Data"]["absolutePath"], self.inst_cfg["Data"]["outputFilePrefix"] + "_data.json")
        self.jsonWriter = JSONWriter()
        self.jsonWriter.start(self.dataFile, d)
            
        try:
            self.ui_signals["ui.btn_test.released"].connect(lambda: self.instLog.info("Button pressed!"))
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
                
            #@vehicle.on_message('SYSTEM_TIME')
            #def listener(self, name, message):
            #    print(message.time_unix_usec)
                
            #@self.vehicle.on_attribute('servo_output_raw')
            #def callback(self, attr_name, value):
            #    self.cb_interface.servoUpdate(attr_name, value)
                
#            @self.vehicle.on_message('*')
#            def callback(self, attr_name, value):
#                print("%s: %s" % attr_name, data)   
        
        except Exception as e:
            raise Exception("Failed to setup callback: %s" % e)
        
    def acquire(self):
        
        d = {}
        d["Battery"] = self.vehicle.battery #{"Voltage": self.vehicle.battery.voltage, "Current": self.vehicle.battery.current, "Level": self.vehicle.battery.level}
        d["Mode"] = self.vehicle.mode.name
        d["Status"] = self.vehicle.system_status.state
        d["EKF OK"] = self.vehicle.ekf_ok
        d["Last Heartbeat"] = self.vehicle.last_heartbeat
        d["GPS"] = self.vehicle.gps_0
        d["Gimbal"] = {"pitch": self.vehicle.gimbal.pitch, "roll": self.vehicle.gimbal.roll, "yaw": self.vehicle.gimbal.yaw}
        d["Attitude"] = self.vehicle.attitude
        d["Channels"] = self.vehicle.channels.values()
        d["Air Speed"] = self.vehicle.airspeed
        d["Ground Speed"] = self.vehicle.groundspeed
        d["Heading"] = self.vehicle.heading
        d["Global Location"] = self.vehicle.location.global_frame
        
        self.jsonWriter.write(time.time(), d)

        
    def close(self):
        self.jsonWriter.close()
        self.vehicle.close()
    
    #Method to process input signals
    def input(self, data, name):
        print("input from %s, %s" % name, data)
        
    
    def download_mission(self):
        """
        Downloads the current mission and returns it in a list.p
        It is used in save_mission() to get the file information to save.
        """
        print("Download mission from vehicle")
        missionlist=[]
        cmds = self.vehicle.commands
        cmds.download()
        cmds.wait_ready()
        for cmd in cmds:
            missionlist.append(cmd)
        return missionlist

    def save_mission(self, aFileName, missionlist):
        """
        Save a mission in the Waypoint file format 
        (http://qgroundcontrol.org/mavlink/waypoint_protocol#waypoint_file_format).
        """
        print("Save mission from Vehicle to file: %s" % aFileName)
        #Download mission from vehicle
        #missionlist = download_mission()
        #Add file-format information
        output='QGC WPL 110\n'
        #Add home location as 0th waypoint
        try:
            home = self.vehicle.home_location
            output+="%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (0,1,0,16,0,0,0,0,home.lat,home.lon,home.alt,1)
        except AttributeError:
            pass
        #Add commands
        for cmd in missionlist:
            commandline="%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (cmd.seq,cmd.current,cmd.frame,cmd.command,cmd.param1,cmd.param2,cmd.param3,cmd.param4,cmd.x,cmd.y,cmd.z,cmd.autocontinue)
            output+=commandline
        with open(aFileName, 'w') as file_:
            print("Write mission to file")
            file_.write(output)
        return output

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
            self.ui_signals["ui.pb_Battery.setValue"].emit(0)
        else:
            self.ui_signals["ui.pb_Battery.setValue"].emit(int(value.level))
    
    def updatePower(self, value):
        self.ui_signals["ui.pb_Vcc.setValue"].emit(int(value.Vcc))
    
    
    def doUIUpdate(self, value):
        self.ui_signals["ui.pb1.setValue"].emit(int(value['3']))
        self.ui_signals["ui.pb2.setValue"].emit(int(value['4']))
        self.ui_signals["ui.pb3.setValue"].emit(int(value['2']))
        self.ui_signals["ui.pb4.setValue"].emit(int(value['1']))
        
        self.ui_signals["ui.pb5.setValue"].emit(int(value['5']))
        self.ui_signals["ui.pb6.setValue"].emit(int(value['6']))
        self.ui_signals["ui.pb7.setValue"].emit(int(value['7']))
        self.ui_signals["ui.pb8.setValue"].emit(int(value['8']))
        


###NOTE: Runs in Main UI Thread. DO NOT BLOCK!
class Ui_interface():
    
    def init(self):
        self._power_currentcolor = 0
        self.ui.pb_Vcc.valueChanged.connect(self.update_pb_color)
    
    def update_pb_color(self):
        w = self.ui.pb_Vcc
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