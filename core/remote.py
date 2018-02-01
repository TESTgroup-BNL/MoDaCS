#Qt Imports
from PyQt5 import QtNetwork, QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal, QObject, QThread
#System Imports
import logging, pickle, ast

def init_remote():
    pass


class Server(QObject):

    sendSig = pyqtSignal(str, object)
    dataSentSig = pyqtSignal(str, int, int)
    
    def __init__(self, cp, main_app, active_insts):
        super().__init__()
        self.enabled = False
        self.allowControl = False
        try:
            if str.lower(cp["Enabled"]) == "true":
                self.target_IP = cp["Target_IP"]
                self.target_addr = QtNetwork.QHostAddress(self.target_IP)
                self.port = int(cp["Target_Port"])

                #Create server thread
                self.thread = QThread()
                self.thread.setObjectName("Server(" + self.target_IP + ":" + str(self.port) + ")")
                self.moveToThread(self.thread)                 #move to new thread
                main_app.runningThreads.watchThread(self.thread)
                main_app.finishedSig.connect(self.thread.quit) #make sure thread exits when inst is closed
                self.thread.started.connect(self.init)         #make sure object init when thread starts   
                self.thread.start()
                
                try:
                    if str.lower(cp["AllowControl"]) == "true": 
                        self.allowControl = True
                        cp_control = {}
                        cp_control["Enabled"] = "True"
                        cp_control["Local_IP"] = cp["Local_Control_IP"]              
                        cp_control["Local_Port"] = cp["Local_Control_Port"]   
                        self.controlClient = Client(cp_control, main_app, active_insts)
                except KeyError:
                    if "AllowControl" in cp:
                        logging.warning("Control configuration missing or invalid, control client not started.")
                    else:
                        pass
                except Exception as e:
                    logging.warning("Error setting up control client; not started.  (%s)" % e)
                
        except KeyError:
            logging.warning("Server configuration missing or invalid, server not started.")

        
    def init(self):
        self.enabled = True
        self.sendSig.connect(self.send)
        self.sock = QtNetwork.QUdpSocket(self)
        logging.info("Server started.  Broadcasting to %s on port %i." % (self.target_IP, self.port))
        
        
    def send(self, target_obj, val):
        try:
            if not type(val) in (type(0), type("")):
                val = pickle.dumps(val)
            data = str([target_obj, val]).encode()
            #print(data)
            self.sock.writeDatagram(data, self.target_addr, self.port)
            self.dataSentSig.emit(self.target_addr.toString(), int(self.port), len(data))
        except Exception as e:
            logging.warning("Error sending remote data: %s" % e)
    
    
class Client(QObject):

    dataRecievedSig = pyqtSignal(str, int, int)
 
    def __init__(self, cp, main_app, active_insts):
        super().__init__()
        self.enabled = False
        self.provideControl = False
        self.main_app = main_app
        self.active_insts = active_insts
        try:
            if str.lower(cp["Enabled"]) == "true":
                self.server_IP = cp["Local_IP"]
                self.server_addr = QtNetwork.QHostAddress(self.server_IP)
                self.port = int(cp["Local_Port"])
                
                #Create client thread
                self.thread = QThread()
                self.thread.setObjectName("Client(" + self.server_IP + ":" + str(self.port) + ")")
                self.moveToThread(self.thread)                 #move to new thread
                main_app.runningThreads.watchThread(self.thread)
                main_app.finishedSig.connect(self.thread.quit) #make sure thread exits when inst is closed
                self.thread.started.connect(self.init)         #make sure object init when thread starts
                self.enabled = True
                
                try:
                    if str.lower(cp["ProvideControl"]) == "true":
                        self.provideControl = True 
                        cp_control = {}
                        cp_control["Enabled"] = "True"
                        cp_control["Target_IP"] = cp["Target_Control_IP"]              
                        cp_control["Target_Port"] = cp["Target_Control_Port"]   
                        self.controlServer = Server(cp_control, main_app, active_insts)
                except KeyError:
                    if "ProvideControl" in cp:
                        logging.warning("Control configuration missing or invalid, control server not started.")
                    else:
                        pass
                except Exception as e:
                    logging.warning("Error setting up control server; not started.  (%s)" % e)
                
        except KeyError:
            logging.warning("Client configuration missing or invalid, client not started.")
            self.enabled = False


        
    def init(self):
        self.targets = {}
        self.bad_targets = set()
        
        self.sock = QtNetwork.QUdpSocket(self)
        self.sock.readyRead.connect(self.processIncoming)
        self.sock.bind(self.server_addr, self.port)
        logging.info("Client started.  Listening from %s on port %i." % (self.server_IP, self.port))
        try:
            self.controlServer.thread.start()
        except:
            pass
        
    def processIncoming(self):
        while self.sock.hasPendingDatagrams():
            datagram, host, port = self.sock.readDatagram(self.sock.pendingDatagramSize())
            self.dataRecievedSig.emit(host.toString(), int(port), len(datagram))
            print(host.toString(), port, datagram)
            try:
                data = ast.literal_eval(datagram.decode())
                if not type(data[1]) in (type(0), type("")):
                    data_in = pickle.loads(data[1])
                else:
                    try:
                        data_in = data[1]
                    except:
                        data_in = None
            except Exception as e:
                logging.warning("Error unpacking remote data: %s" % e)
            self.receive(data[0], data_in)
            
    def receive(self, target_sig, val=None):
        try:
            if target_sig in self.bad_targets:  #if the target has already been checked and is bad, ignore
                return
            if not target_sig in self.targets:
             #if the target isn't in the dict yet, look it up and add a direct reference
                if self.add_signal(target_sig) == 0:
                    self.emit_signal(target_sig, val)
            else:
                self.emit_signal(target_sig, val)

        except Exception as e:
            if "does not have signal with signature" in str(e):
                logging.warning("Signal %s signature changed, attempting to re-link" % target_sig)
                if self.add_signal(target_sig) == 0:
                    self.emit_signal(target_sig, val)
            else:
                logging.warning("Error connecting remote signal: %s" % e)
            
    def emit_signal(self, target_sig, val):
        try:
            if val is None:
                self.targets[target_sig].emit()
            else: 
                self.targets[target_sig].emit(val)
        except Exception as e:
            logging.warning("Error processing remote data: %s" % e)

    def add_signal(self, target_sig):
        try:
            t_elements = target_sig.split(".")
            t_root = t_elements.pop(0)  #get the "root" module/instance
            if t_root == "main_app":
                t_root = self.main_app
            else:
                t_root = self.active_insts[t_root]
            
            for target_element in t_elements:
                try:
                    target_list = target_element.split("[") #check for lists and dicts
                    t_root_list = getattr(t_root, target_list[0])
                    t_root = t_root_list[target_list[1][1:-2].replace("~",".")]
                except:
                    t_root = getattr(t_root, target_element.replace("~","."))
                
            self.targets[target_sig] = t_root
            return 0
        
        except Exception as e:
            logging.warning("Problem with remote signal key '%s': %s.  Signal will be ignored." % (target_sig, e))
            self.bad_targets.add(target_sig)
            return -1
        
        
class TCPConnection(QObject):

    sendSig = pyqtSignal(str, object)
    dataRecievedSig = pyqtSignal(str, int, int)
    dataSentSig = pyqtSignal(str, int, int)
    clientConnectSig = pyqtSignal()
    
    def __init__(self, cp, main_app, active_insts, mode="server"):
        super().__init__()
        self.main_app = main_app
        self.active_insts = active_insts
        self.enabled = False
        self.allowControl = False
        self.provideControl = False
        self.targets = {}
        self.bad_targets = set()
        self.sock = []
        self.mode = mode
        self.datagram = ""
        self.d_len = 0
        #self.uiReady = False
        
        try:
            if str.lower(cp["Enabled"]) == "true":
                self.server_IP = cp["TCP_Server_IP"]
                self.port = int(cp["TCP_Server_Port"])                
                self.server_addr = QtNetwork.QHostAddress(self.server_IP)
                
                #Create server thread
                self.thread = QThread()
                self.thread.setObjectName("TCP Connection(" + self.server_IP + ":" + str(self.port) + ")")
                self.moveToThread(self.thread)                 #move to new thread
                main_app.runningThreads.watchThread(self.thread)
                main_app.finishedSig.connect(self.close)       #make sure thread exits when inst is closed
                self.thread.started.connect(self.init)         #make sure object init when thread starts  
                #main_app.uiReadySig.connect(lambda: self.uiReady = True)
                
                if mode == "server":
                    try:
                        if str.lower(cp["AllowControl"]) == "true": 
                            self.allowControl = True                           
                    except KeyError:
                        if "AllowControl" in cp:
                            logging.warning("Control configuration missing or invalid, not started.")
                        else:
                            pass
                    if self.allowControl:
                        self.controlClient = self
                    
                    self.thread.start()      
                else:
                    try:
                        if str.lower(cp["ProvideControl"]) == "true": 
                            self.provideControl = True                           
                    except KeyError:
                        if "ProvideControl" in cp:
                            logging.warning("Control configuration missing or invalid, not started.")
                        else:
                            pass
                    if self.provideControl:
                        self.controlServer = self
                        
                    #Client thread is started from main
                
                self.enabled = True
                
                
        except KeyError:
            logging.warning("Connection configuration missing or invalid, not started.")
        
        except Exception as e:
            logging.error("Error starting connection: %s" % e)
            

    def init(self):
        if self.mode == "server" or self.allowControl:
            self.tcpserver = QtNetwork.QTcpServer(self)
            self.tcpserver.listen(self.server_addr, self.port)
            self.tcpserver.newConnection.connect(self.addConnection)
            
            self.sendSig.connect(self.send)        
            logging.info("Server started.  Listening on %s, port %i." % (self.server_IP, self.port))
            
        if self.mode == "client":
            self.tcpclient = QtNetwork.QTcpSocket(self)
            self.tcpclient.setSocketOption(QtNetwork.QAbstractSocket.LowDelayOption, 1)
            self.tcpclient.readyRead.connect(lambda: self.processIncoming(self.tcpclient))
            self.tcpclient.disconnected.connect(self.tryConnect)
            self.tcpclient.connected.connect(self.connectionMade)
            if self.provideControl:
                self.sock.append(self.tcpclient)
                self.sendSig.connect(self.send)
            self.try_timer = QtCore.QTimer(self)
            self.try_timer.timeout.connect(self.tryConnect)
            #self.try_timer.start(10000)
            self.firstTry = True
            self.tryConnect()
        
    def tryConnect(self):
            if not self.firstTry:
                logging.warning("Timeout connecting to remote server.  Trying again...")
                self.tcpclient.abort()
            else:
                self.try_timer.start(10000)
            self.tcpclient.connectToHost(self.server_addr, self.port)
                
    def connectionMade(self):
        self.try_timer.stop()
        self.firstTry = True
        logging.info("Client started.  Listening from %s on port %i." % (self.server_IP, self.port))
        self.clientConnectSig.emit()
        
    def addConnection(self):
        print("Connection pending...")
        while(self.tcpserver.hasPendingConnections()):
            s = self.tcpserver.nextPendingConnection()
            s.setSocketOption(QtNetwork.QAbstractSocket.LowDelayOption, 1)
            s.disconnected.connect(lambda: self.removeConnection(s))
            self.sock.append(s)
            logging.info("New client connected: %s %s:%s" % (s.peerName(), s.peerAddress().toString(), s.peerPort()))
            s.readyRead.connect(lambda s=s: self.processIncoming(s))
            
    def removeConnection(self, s):
        #print("Client disconnected")
        logging.info("Client disconnected: %s %s:%s" % (s.peerName(), s.peerAddress().toString(), s.peerPort()))
        try:
            s.close()
        except:
            pass
        self.sock.remove(s)
        s.deleteLater()
            

    def send(self, target_obj, val):
        try:
            if not type(val) in (type(0), type("")):
                val = pickle.dumps(val)
            packed_target = str([target_obj, val])
            data = str(len(packed_target)) + "\n" + packed_target
            #print(data)
            for s in self.sock:
                s.write(data.encode())
                s.flush()
                #s.writeDatagram(data, self.target_addr, self.port)
            self.dataSentSig.emit(str(len(self.sock)) + " clients", int(self.port), len(data))
        except Exception as e:
            logging.warning("Error sending remote data: %s" % e)
    
        
    def processIncoming(self, s):
        #if self.UIready:
        while(s.bytesAvailable()):
            #print("incoming!", s.bytesAvailable(), self.d_len, self.datagram)
            if self.datagram == "":
                self.datagram = s.readLine()
                self.d_len = int(self.datagram[:-1])   #get data length  
            
            if s.bytesAvailable() >= self.d_len:
                                        
                self.datagram = s.read(self.d_len)
                #print(str(self.d_len), self.datagram)
                #print(s.peerAddress().toString(), int(s.peerPort()), self.d_len)
                self.dataRecievedSig.emit(s.peerAddress().toString(), int(s.peerPort()), self.d_len)
                #print(host.toString(), port, datagram)
                try:
                    data = ast.literal_eval(self.datagram.decode())
                    if not type(data[1]) in (type(0), type("")):
                        data_in = pickle.loads(data[1])
                    else:
                        try:
                            data_in = data[1]
                        except:
                            data_in = None
                    self.receive(data[0], data_in)
                except Exception as e:
                    logging.warning("Error unpacking remote data: %s" % e)
                finally:
                    self.datagram = ""
            QtWidgets.QApplication.processEvents()
            
            
    def receive(self, target_sig, val=None):
        try:
            if target_sig in self.bad_targets:  #if the target has already been checked and is bad, ignore
                return
            if not target_sig in self.targets:
             #if the target isn't in the dict yet, look it up and add a direct reference
                if self.add_signal(target_sig) == 0:
                    self.emit_signal(target_sig, val)
            else:
                self.emit_signal(target_sig, val)

        except Exception as e:
            if "does not have signal with signature" in str(e):
                logging.warning("Signal %s signature changed, attempting to re-link" % target_sig)
                if self.add_signal(target_sig) == 0:
                    self.emit_signal(target_sig, val)
            else:
                logging.warning("Error connecting remote signal: %s" % e)
            
    def emit_signal(self, target_sig, val):
        try:
            if val is None:
                self.targets[target_sig].emit()
            else: 
                self.targets[target_sig].emit(val)
        except Exception as e:
            logging.warning("Error processing remote data: %s" % e)

    def add_signal(self, target_sig):
        try:
            t_elements = target_sig.split(".")
            t_root = t_elements.pop(0)  #get the "root" module/instance
            if t_root == "main_app":
                t_root = self.main_app
            else:
                t_root = self.active_insts[t_root]
            
            for target_element in t_elements:
                try:
                    target_list = target_element.split("[") #check for lists and dicts
                    t_root_list = getattr(t_root, target_list[0])
                    t_root = t_root_list[target_list[1][1:-2].replace("~",".")]
                except:
                    t_root = getattr(t_root, target_element.replace("~","."))
                
            self.targets[target_sig] = t_root
            return 0
        
        except Exception as e:
            logging.warning("Problem with remote signal key '%s': %s.  Signal will be ignored." % (target_sig, e))
            self.bad_targets.add(target_sig)
            return -1
        
    def close(self):
        #Interrupt any init that's still happening
        self.thread.requestInterruption()
        
        #Attempt to cleanly close all connections
        try:
            for c in self.sock:
                c.close()
        except:
            pass
        try:
            self.tcpserver.close()
        except:
            pass
        try:
            self.tcpclient.abort()
        except:
            pass
        
        #Stop thread
        self.thread.quit()