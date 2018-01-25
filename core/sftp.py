#System Imports
import logging, stat
from os import path, makedirs, utime
from time import sleep

#Qt Imports
from PyQt5 import QtNetwork, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal, QObject

#Other Imports
import paramiko


class SFTP_Client(QObject):    
    
    def __init__(self, run_cfg):
        super().__init__()
        self.run_cfg = run_cfg
        self.sock = QtNetwork.QUdpSocket(self)
        
        try:
            self.downloadPath = self.run_cfg["Data"]["location"]
            self.ssh_user = self.run_cfg["Data"]["SSH_User"]
            self.ssh_pw = self.run_cfg["Data"]["SSH_Password"]
        except KeyError as e:
            logging.warning("Error in RunConfig: %s /nSFTP transfer aborted." % e)
            sleep(1)
            self.sock.writeDatagram("SFTP Done".encode(), QtNetwork.QHostAddress(self.run_cfg["Client"]["TCP_Server_IP"]), int(self.run_cfg["Client"]["TCP_Server_Port"])+1)
            self.sock.close()
            return
            
        self.sock.readyRead.connect(lambda: self.checksftpReady()) 
        self.sock.bind(QtNetwork.QHostAddress(self.run_cfg["Client"]["TCP_Client_IP"]), int(self.run_cfg["Client"]["TCP_Client_Port"])+1)
                   
    def checksftpReady(self):
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
                
    def sftpTransfer(self, remote_dir):
        print(remote_dir)
        transport = paramiko.Transport((self.run_cfg["Client"]["TCP_Server_IP"],22))
        transport.connect(username=self.ssh_user,password=self.ssh_pw)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        receivePath = path.join(self.downloadPath, path.basename(path.normpath(remote_dir)))
        
        self.download_dir(remote_dir, receivePath, sftp)
        sftp.close()
        transport.close()
        
        self.sock.writeDatagram("SFTP Done".encode(), QtNetwork.QHostAddress(self.run_cfg["Client"]["TCP_Server_IP"]), int(self.run_cfg["Client"]["TCP_Server_Port"])+1)
        self.sock.close()
        
        logging.info("Done with SFTP Transfer.")
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
                print("Transfer cancelled.")
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
    
    def __init__(self, run_cfg, onFinished):
        super().__init__()
        self.run_cfg = run_cfg
        self.sftp_finished.connect(onFinished)
        logging.info("Starting SFTP transfer...")
        self.sock = QtNetwork.QUdpSocket(self)
        self.sock.readyRead.connect(lambda: self.checksftpDone()) 
        self.sock.bind(QtNetwork.QHostAddress(self.run_cfg["Server"]["TCP_Server_IP"]), int(self.run_cfg["Server"]["TCP_Server_Port"])+1)
        start_str = "Start SFTP:" + self.run_cfg["Data"]["dataPath"]
        self.sock.writeDatagram(start_str, QtNetwork.QHostAddress(self.run_cfg["Server"]["TCP_Client_IP"]), int(self.run_cfg["Server"]["TCP_Client_Port"])+1)

    def checksftpDone(self):
        while self.sock.hasPendingDatagrams():
            datagram, host, port = self.sock.readDatagram(self.sock.pendingDatagramSize())
            #self.dataRecievedSig.emit(host.toString(), int(port), len(datagram))
            data = datagram.decode()
            print(data)
            if data == "SFTP Done":
                self.sftpEnabled = False
                self.sock.close
                self.sftp_finished.emit()
                
                
class DownloadProgress(QtWidgets.QProgressDialog):

    def __init__(self, parent=None, total=100):
        super(DownloadProgress, self).__init__(parent)
        layout = QtGui.QVBoxLayout(self)       
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setFixedSize(200,200)
        self.progressBar = QtGui.QProgressBar(self)
        self.progressBar.setRange(0,total)
        self.currentDir = QtGui.QLabel(self)
        self.currentFile = QtGui.QLabel(self)
        button = QtGui.QPushButton("Cancel", self)
        layout.addWidget(self.currentDir)
        layout.addWidget(self.currentFile)
        layout.addWidget(self.progressBar)
        layout.addWidget(button)

        self.cancelled = False
        button.clicked.connect(self.onCancel)
        self.show()

    def onCancel(self):
        self.cancelled = True

    def setProgress(self, file, i):
        self.progressBar.setValue(i)
        self.currentFile.setText(file)
    
    def setDirTotal(self, dir, total):
        self.currentDir.setText(dir)
        self.progressBar.setRange(0,total)  
