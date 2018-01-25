#Qt Imports
from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
#System Imports
from time import sleep, time
from os import path, makedirs
#MoDaCS Imports
from util import JSONFileField
#Other Imports
import pyqtgraph as pg

class Inst_interface(QtCore.QObject):
    
    #instLog = logger object
    #inst_cfg = config object
    
    inputs = []
    outputs = []
    
#    ui_inputs = ["ui.pb_tare_alt.released"]
#    ui_outputs = ["updatePlot"]
        
    #### Required Functions ####
    def init(self, inst_vars, jsonFF):
        
        self.inst_vars = inst_vars
        self.jsonFF = jsonFF
        
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
                self.out_file.write(data)
        except Exception as e:
            print(e)
            


#===============================================================================
class Ui_interface():
     
    def init(self):
        pass
     
#     specData = QtCore.pyqtSignal(object)
#     
#     def init(self):
#         self.refs = []
#         
#         self.pw = pg.PlotWidget(name='Plot1')
#         try:
#             self.clearLayout(self.ui.layout1)      #Clear layout if it exists so that instrument resets work properly
#         except:
#             self.ui.layout1 = QtGui.QVBoxLayout()
#             self.ui.layout1.setContentsMargins(0,0,0,0)
#             self.ui.pltWidget.setLayout(self.ui.layout1)
#             
#         self.ui.layout1.addWidget(self.pw)
#         
#         self.refplot = self.pw.plot(pen=(0,2))
#         self.specplot = self.pw.plot(pen=(1,2))
#         
#         self.ui.pltWidget.setContentsMargins(0,0,0,0)
#         y_axis = self.pw.getAxis('left')
#         y_axis.enableAutoSIPrefix(False)
#         y_axis.showLabel(False)
#         y_axis.setRange(0, 1)
#         #y_axis.setStyle(tickTextOffset=-30)
#         #y_axis.setTicks([(0,"0"),(65535,"65535")])
#         y_axis.setScale(1/65535)
#         y_axis.setWidth(25)
# 
#         x_axis = self.pw.getAxis('bottom')
#         x_axis.enableAutoSIPrefix(False)
#         x_axis.showLabel(False)
#         x_axis.setHeight(15)
#         #self.pw.setLabel('bottom', 'Wavelength', units='nm')
#         
#         self.pw.getAxis('top').setHeight(5)
#         
#         self.ui.pb_remlast.released.connect(self.remLastRef, QtCore.Qt.UniqueConnection)
#         #self.specData.connect(self.updatePlot)
#         
#     def clearLayout(self, layout):
#         if layout is not None:
#             while layout.count():
#                 item = layout.takeAt(0)
#                 widget = item.widget()
#                 if widget is not None:
#                     widget.deleteLater()
#                 else:
#                     self.clearLayout(item.layout())
#                     
#     def remLastRef(self):
#         try:
#             self.refs.pop()
#             self.updateRef()
#         except:
#             pass
#         
#     def updateRef(self):
#         l = len(self.refs)
#         self.ui.lbl_refcount.setNum(l)
#         if l > 0:
#             self.refAvg = [sum(col)/len(col) for col in zip(*self.refs)]
#             self.refplot.setData(x=self.refwls, y=self.refAvg) 
#         else:
#             self.refplot.setData(x=[], y=[])
#         
#     def updatePlot(self, data):    
#         wls = data[0]
#         intens = data[1]
#         isRef = data[2]
#         
#         self.pw.setXRange(min(wls), max(wls)) 
#         
#         if isRef:
#             self.refs.append(intens)
#             self.refwls = wls
#             self.updateRef()
#         else:
#             self.specplot.setData(x=wls, y=intens)
#===============================================================================
             