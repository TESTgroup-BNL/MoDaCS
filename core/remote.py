from PyQt5 import QtCore, QtNetwork
import logging, pickle, ast
from PyQt5.QtCore import pyqtSignal, QObject


def init_remote():
    pass


class Server(QObject):
    
    finishedSig = pyqtSignal()
    sendSig = pyqtSignal(str, object)
    
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
                self.thread = QtCore.QThread()
                self.moveToThread(self.thread)                 #move to new thread
                self.finishedSig.connect(self.thread.quit)     #make sure thread exits when inst is closed
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
            self.sock.writeDatagram(str([target_obj, val]).encode(), self.target_addr, self.port)
        except Exception as e:
            logging.warning("Error sending remote data: %s" % e)
    
    
class Client(QObject):
    
    finishedSig = pyqtSignal()
 
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
                self.thread = QtCore.QThread()
                self.moveToThread(self.thread)                 #move to new thread
                self.finishedSig.connect(self.thread.quit)     #make sure thread exits when inst is closed
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
            #print(host.toString(), port, datagram)
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
                
                except Exception as e:
                    logging.warning("Problem with remote signal key '%s': %s.  Signal will be ignored." % (target_sig, e))
                    self.bad_targets.add(target_sig)
                    return
                
            if val is None:
                self.targets[target_sig].emit()
            else: 
                self.targets[target_sig].emit(val)

        except Exception as e:
            logging.warning("Error processing remote data: %s" % e)
