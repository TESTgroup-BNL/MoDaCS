#System Imports
import logging, stat
from os import path, makedirs, utime
from time import sleep

#Qt Imports
from PyQt5 import QtNetwork, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.Qt import QMessageBox, QProgressBar

#Other Imports
try:
    import paramiko
except ImportError:
    logging.warning("Paramiko not found; SFTP will not be functional.")


class SFTP_Client(QObject):    
    
    def __init__(self, run_cfg):
        super().__init__()
        self.run_cfg = run_cfg
        self.sock = QtNetwork.QUdpSocket(self)
        self.connected = False
        self.receivePath = None
        
        try:
            self.downloadPath = self.run_cfg["Data"]["location"]
            self.ssh_user = self.run_cfg["Data"]["SSH_User"]
            self.ssh_pw = self.run_cfg["Data"]["SSH_Password"]
        except KeyError as e:
            logging.warning("Error in RunConfig: %s /nSFTP transfer aborted." % e)
            sleep(1)
            self.sftpDone()
            return None
            
        #self.sock.readyRead.connect(lambda: self.checksftpReady()) 
        self.sock.bind(QtNetwork.QHostAddress(self.run_cfg["Client"]["TCP_Client_IP"]), int(self.run_cfg["Client"]["TCP_Client_Port"])+1)
        
        logging.info("Waiting for client...")
        dl_connecting = QtWidgets.QProgressDialog("Waiting for client...", "Cancel", 0, 300, None, QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
        dl_connecting.setWindowTitle = "SFTP Transfer"
        dl_connecting.setMinimumDuration(500)
        dl_connecting_pb = QProgressBar()
        dl_connecting_pb.setTextVisible(False)
        dl_connecting_pb.setRange(0,300)
        dl_connecting.setBar(dl_connecting_pb)    
        
        i = 0  
        while(self.sock.hasPendingDatagrams() == False):
            i += 1
            dl_connecting.setValue(i)
            if i > 300 or dl_connecting.wasCanceled():
                logging.warning("SFTP connection timed out.")
                if dl_connecting.wasCanceled():
                    QtWidgets.QMessageBox.warning(None, "SFTP Transfer", "Connection timed out")
                dl_connecting.reset()
                return None
            QtWidgets.QApplication.processEvents()
            sleep(0.1)
        
        dl_connecting.reset()
        self.checksftpReady()
        
        #return self.receivePath
                   
    def checksftpReady(self):
        self.connected = True
        try:
            while self.sock.hasPendingDatagrams():
                datagram, host, port = self.sock.readDatagram(self.sock.pendingDatagramSize())
                #self.dataRecievedSig.emit(host.toString(), int(port), len(datagram))
                data = datagram.decode()
                print(data)
                #dat_str = "" + data
                if data.startswith("Start SFTP"):
                    #print("Starting SFTP Transfer...")
                    logging.info("Starting SFTP Transfer...")
                    self.sftpTransfer(data[12:])
        except Exception as e:
            logging.warning(e)
            self.sftpDone()
            return
        
    def sftpTransfer(self, remote_dir):
        print(remote_dir)
        transport = paramiko.Transport((self.run_cfg["Client"]["TCP_Server_IP"],22))
        transport.connect(username=self.ssh_user,password=self.ssh_pw)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        receivePath = path.join(self.downloadPath, path.basename(path.normpath(remote_dir)))
        
        self.download_dir(remote_dir, receivePath, sftp)
        sftp.close()
        transport.close()
        
        self.sftpDone()
        
        logging.info("Done with SFTP Transfer.")
        
        self.receivePath = receivePath
        return
    
    def sftpDone(self):
        self.sock.writeDatagram("SFTP Done".encode(), QtNetwork.QHostAddress(self.run_cfg["Client"]["TCP_Server_IP"]), int(self.run_cfg["Client"]["TCP_Server_Port"])+1)
        self.sock.close()
        QtWidgets.QMessageBox.information(None, "SFTP Transfer", "SFTP transfer finished!")
        return
    
    def download_dir(self, remote_dir, local_dir, sftp, dl_prog=None):
        remote_dir = "/" + remote_dir
        if dl_prog is None:
            dl_prog = QtWidgets.QProgressDialog("Connecting...", "Cancel", 0, 100, None, QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
            dl_prog.setWindowTitle = "SFTP Transfer"
        path.exists(local_dir) or makedirs(local_dir)
        dir_items = sftp.listdir_attr(remote_dir)
        dl_prog.setMaximum(len(dir_items))
        logging.info("Downloading %i items from %s" %(len(dir_items), remote_dir))
        
        for i, item in enumerate(dir_items):
            if dl_prog.wasCanceled():
                print("Transfer canceled.")
                return
            dl_prog.setLabelText(remote_dir + "\n" + item.filename)

            remote_path = remote_dir + '/' + item.filename         
            local_path = path.join(local_dir, item.filename)
            if stat.S_ISDIR(item.st_mode):
                self.download_dir(remote_path, local_path, sftp, dl_prog)
            else:
                sftp.get(remote_path, local_path)
                fstats = sftp.stat(remote_path)
                utime(local_path, (fstats.st_atime, fstats.st_mtime))
            
            dl_prog.setValue(i)
            QtWidgets.QApplication.processEvents()
        return
    
    
class SFTP_Server(QObject):
    
    sftp_finished = pyqtSignal()
    
    def __init__(self, run_cfg):
        super().__init__()
        self.run_cfg = run_cfg

        #self.sftp_finished.connect(onFinished)
        logging.info("Starting SFTP transfer...")
        self.sock = QtNetwork.QUdpSocket(self)
        #self.sock.readyRead.connect(lambda: self.checksftpDone()) 
        self.sock.bind(QtNetwork.QHostAddress(self.run_cfg["Server"]["TCP_Server_IP"]), int(self.run_cfg["Server"]["TCP_Server_Port"])+1)
        start_str = "Start SFTP:" + self.run_cfg["Data"]["dataPath"]
        self.sock.writeDatagram(start_str.encode(), QtNetwork.QHostAddress(self.run_cfg["Server"]["TCP_Client_IP"]), int(self.run_cfg["Server"]["TCP_Client_Port"])+1)
        
        while(self.sock.hasPendingDatagrams() == False):     #no timeout, could be problematic
            QtWidgets.QApplication.processEvents()
            sleep(1)
            
        self.checksftpDone()


    def checksftpDone(self):
        while self.sock.hasPendingDatagrams():
            datagram, host, port = self.sock.readDatagram(self.sock.pendingDatagramSize())
            #self.dataRecievedSig.emit(host.toString(), int(port), len(datagram))
            data = datagram.decode()
            print(data)
            if data == "SFTP Done":
                self.sftpEnabled = False
                self.sock.close
                #self.sftp_finished.emit()
