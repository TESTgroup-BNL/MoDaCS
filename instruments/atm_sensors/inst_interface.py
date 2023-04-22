#Qt Imports
from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
try:
    layout_test = QtGui.QVBoxLayout()
except Exception:
    QtGui = QtWidgets   #Compatibility hack
    
#System Imports
from time import sleep, time
from os import path, makedirs
#MoDaCS Imports
from core.JSONFileField.jsonfilefield import JSONFileField
#Other Imports
import pyqtgraph as pg

class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    
    inputs = []
    outputs = []
    
    ui_inputs = []
    ui_outputs = ["updatePlot"]
        
    #### Required Functions ####
    def init(self, inst_vars, jsonFF):
        
        self.inst_vars = inst_vars
        self.jsonFF = jsonFF
        self.current_meas = Atm_Readings()
        
        #Read config
        self.rem_ip = self.inst_vars.inst_cfg["Initialization"]["RemoteIP"]
        self.rem_port = int(self.inst_vars.inst_cfg["Initialization"]["RemotePort"])     
        
        #Create output file & header
        self.out_filePath = self.inst_vars.inst_cfg["Data"]["absolutePath"]
        makedirs(self.out_filePath, exist_ok=True)
        self.out_file = open(path.join(self.out_filePath, self.inst_vars.inst_cfg["Initialization"]["OutputFile"]), 'a')
        self.out_file.write(self.inst_vars.inst_cfg["Initialization"]["Header"] + '\n')
        
        #Set up UI
        #self.ui_signals["ui.pb_tare_alt.released"].connect(self.tareAlt)

        #Start listening
        self.sock = QtNetwork.QUdpSocket(self)
        self.sock.readyRead.connect(lambda: self.processIncoming())
        self.qAdd = QtNetwork.QHostAddress(self.rem_ip)
        self.sock.bind(self.qAdd, self.rem_port)
        self.inst_vars.inst_log.info("Listening on %s:%i" % (self.rem_ip, self.rem_port))

            
    def acquire(self, getRef=False):
        pass

        #Update UI
#        self.ui_signals["updatePlot"].emit([self.wavelengths, intensities, getRef])
        
    def close(self):
        self.out_file.close()
        
    ### Other Instrument Functions/Classes ###
    def tareAlt(self):
        self.altOffset = 0
        
    def processIncoming(self):
        try:
            while self.sock.hasPendingDatagrams():
                datagram, host, port = self.sock.readDatagram(self.sock.pendingDatagramSize())
                #self.dataRecievedSig.emit(host.toString(), int(port), len(datagram))
                data = datagram.decode()
                #print(host.toString(), port, data)
                self.out_file.write(data + "\n")
                self.current_meas.values = data.split(",")
                self.ui_signals["updatePlot"].emit(self.current_meas.values)
        except Exception as e:
            print(e)
            
            

class Atm_Readings():
    
    def __init__(self):
        self.__current_meas = {"Time":0, "Temperature":0, "RH":0, "Pressure":0, "Altitude":0, "Latitude":0, "Longitude":0}
        
    @property
    def values(self):
        return self.__current_meas

    @values.setter
    def values(self, vals):
        if type(vals) == type(""):
            data = vals.split(",").trim()
            self.__current_meas["Time"] = float(data[0])
            self.__current_meas["Temperature"] = float(data[1])
            self.__current_meas["RH"] = float(data[2])
            self.__current_meas["Pressure"] = float(data[3])
            self.__current_meas["Altitude"] = float(data[4])
            self.__current_meas["Longitude"] = float(data[5])
            self.__current_meas["Latitude"] = float(data[6])
        elif type(vals) == type([]):
            data = vals
            self.__current_meas["Time"] = float(data[0])
            self.__current_meas["Temperature"] = float(data[1])
            self.__current_meas["RH"] = float(data[2])
            self.__current_meas["Pressure"] = float(data[3])
            self.__current_meas["Altitude"] = float(data[4])
            self.__current_meas["Longitude"] = float(data[5])
            self.__current_meas["Latitude"] = float(data[6])
        elif type(vals) == type({}):
            self.__current_meas = vals
            


class Ui_interface():
     
     
    def init(self):
        
        self.plt_data = {"Time":[], "Temperature":[], "Pressure":[], "RH":[], "Altitude":[]}
        self.lbls = {"Time":None, "Temperature":self.ui.lbl_temp, "Pressure":self.ui.lbl_press, "RH":self.ui.lbl_RH, "Altitude":self.ui.lbl_alt, "Longitude":self.ui.lbl_long, "Latitude":self.ui.lbl_lat}
        
        
        try:
            self.clearLayout(self.ui.layout1)      #Clear layout if it exists so that instrument resets work properly
        except:
            l = pg.GraphicsLayoutWidget()
            self.layout1 = QtGui.QVBoxLayout()
            self.layout1.setContentsMargins(0,0,0,0)
            self.layout1.addWidget(l)
            self.ui.pltWidget.setLayout(self.layout1)
        
        self.pI = pg.PlotItem(name='Plot1')
            
        #axis
        temp_axis = self.pI.getAxis("left")
        press_axis = pg.AxisItem("right")
        rh_axis = pg.AxisItem("left")
        alt_axis = pg.AxisItem("right")
        
        self.pI_vb = self.pI.getViewBox()
        self.press_axis_vb = pg.ViewBox()
        self.rh_axis_vb = pg.ViewBox()
        self.alt_axis_vb = pg.ViewBox()
        
        # add axis to layout     
        l.addItem(rh_axis, row = 1, col = 1,  rowspan=1, colspan=1)
        l.addItem(self.pI, row = 1, col = 2,  rowspan=1, colspan=1)
        l.addItem(press_axis, row = 1, col = 3,  rowspan=1, colspan=1)
        l.addItem(alt_axis, row = 1, col = 4,  rowspan=1, colspan=1)

        # add viewboxes to layout 
        l.scene().addItem(self.rh_axis_vb)
        l.scene().addItem(self.pI_vb)
        l.scene().addItem(self.press_axis_vb)
        l.scene().addItem(self.alt_axis_vb)
        
        # link axis with viewboxes
        rh_axis.linkToView(self.rh_axis_vb)
        press_axis.linkToView(self.press_axis_vb)
        alt_axis.linkToView(self.alt_axis_vb)

        # link viewboxes
        self.rh_axis_vb.setXLink(self.pI_vb)
        self.alt_axis_vb.setXLink(self.rh_axis_vb)
        self.press_axis_vb.setXLink(self.alt_axis_vb)
        
        # axes labels
        temp_axis.setLabel('Temp (deg C)', color='#FFFFFF')
        press_axis.setLabel('Pressure (mB)', color='#2E2EFE')
        
        rh_axis.setLabel('RH (%)', color='#2EFEF7')
        alt_axis.setLabel('Altitude (m)', color='#2EFE2E')
        
        self.plts = {}
        self.plts["Temperature"] = self.pI.plot(pen='#FFFFFF', axis='left')
        
        self.plts["Pressure"] = pg.PlotCurveItem(x=[0], y=[0], pen='#2E2EFE')
        self.press_axis_vb.addItem(self.plts["Pressure"])
        
        self.plts["RH"] = pg.PlotCurveItem(x=[0], y=[0], pen='#2EFEF7')
        self.rh_axis_vb.addItem(self.plts["RH"])
        
        self.plts["Altitude"] = pg.PlotCurveItem(x=[0], y=[0], pen='#2EFE2E')
        self.alt_axis_vb.addItem(self.plts["Altitude"])

        
#         self.plts["RH"] = self.pI.plot(pen='#2EFEF7')
#         self.rh_axis_vb.addItem(self.plts["RH"])
#         self.plts["Altitude"] = self.pI.plot(pen='#2EFE2E')
#         self.alt_axis_vb.addItem(self.plts["Altitude"])

        def updateViews(): 
            self.rh_axis_vb.setGeometry(self.pI_vb.sceneBoundingRect())
            self.alt_axis_vb.setGeometry(self.pI_vb.sceneBoundingRect())      
            self.press_axis_vb.setGeometry(self.pI_vb.sceneBoundingRect())   
        # updates when resized
        self.pI_vb.sigResized.connect(updateViews)

        # autorange once to fit views at start
        self.press_axis_vb.enableAutoRange(axis= pg.ViewBox.XYAxes, enable=True)
        self.rh_axis_vb.enableAutoRange(axis= pg.ViewBox.XYAxes, enable=True)
        self.alt_axis_vb.enableAutoRange(axis= pg.ViewBox.XYAxes, enable=True)

#         try:
#             self.clearLayout(self.ui.layout1)      #Clear layout if it exists so that instrument resets work properly
#         except:
#             self.ui.layout1 = QtGui.QVBoxLayout()
#             self.ui.layout1.setContentsMargins(0,0,0,0)
#             self.ui.pltWidget.setLayout(self.ui.layout1)
#              
#         self.ui.layout1.addWidget(self.pw)
#          

        

         
    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

         
    def updatePlot(self, data):

        def updatePlotItem(key, item):
            try:
                if len(self.plt_data[key]) >= 60:
                    self.plt_data[key][:-1] = self.plt_data[key][1:]  # shift data in the array one sample left
                    self.plt_data[key][-1] = item
                else:
                    self.plt_data[key].append(item)
            except KeyError:
                self.plt_data[key] = [item]

        updatePlotItem("Time", data["Time"])
        self.pI.setXRange(self.plt_data["Time"][0], self.plt_data["Time"][-1])
        
        for key, item in data.items():
            if key is not "Time":
                self.lbls[key].setText(str(item))
                updatePlotItem(key, item)
                try:
                    self.plts[key].setData(x=self.plt_data["Time"], y=self.plt_data[key])
                except KeyError:
                    pass    #ignore the items not being plotted