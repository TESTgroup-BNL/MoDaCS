from time import sleep, time
from os import path, makedirs

#Qt Imports
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap

try:
    layout_test = QtGui.QVBoxLayout()
except Exception:
    QtGui = QtWidgets   #Compatibility hack

#Other Imports
import pyqtgraph as pg
import numpy
from core.JSONFileField.jsonfilefield import JSONFileField
try:
    import gphoto2 as gp
except:
    pass


class Inst_interface():
    
    #inst_vars.inst_log = logger object
    #inst_vars.inst_cfg = config object
    #inst_wid = instrument widget
    #inst_vars.inst_n = acquisition count
    
    inputs = []
    outputs = []

    ui_inputs = []
    ui_outputs = ["updateImage"]
        
    #### Event functions ####
        
    def init(self, inst_vars, jsonFF):
        
        self.inst_vars = inst_vars
        self.jsonFF = jsonFF
        self.cam_present = False
        self.preview = True

        try:
            self.preview = bool(self.inst_vars.inst_cfg["Initialization"]["preview"])
        except KeyError:
            pass

        self.imgPath = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], "Canon")
        makedirs(self.imgPath, exist_ok=True)

        try:
            #Call instrument init
            self.cam = gp.Camera()
            self.cam.init()
            cam_info = self.cam.get_summary().text
            self.cam_present = True
        except Exception as e:
            if "referenced before assignment" in str(e):
                Exception("No camera found.")
            else:
                self.inst_vars.inst_log.warning(e)
        
        self.inst_vars.inst_log.info(cam_info)
        header = self.jsonFF.addField("Header")
        header["Camera Info"] = cam_info

        
    def acquire(self):
        if self.cam_present:
            
            if self.preview:
                prev = self.cam.capture_preview()
            t = time()    
            img = self.cam.capture(gp.GP_CAPTURE_IMAGE)

            self.jsonFF["Data"].write(img.name, recnum=self.inst_vars.globalTrigCount, timestamp=t, compact=True)
            if self.preview:
                prev.save(path.join(self.imgPath, "prev_" + img.name))
                with open(path.join(self.imgPath, "prev_" + img.name), 'rb') as f:
                    self.ui_signals["updateImage"].emit(f.read())
            #Save prev and copy temp prev to inst data path
            #shutil.move(prev.name, path.join(self.imgPath, prev.name))

            #prevFile = path.join(self.imgPath, self.filePrefix + strftime("%Y%m%d_%H%M%S") + ".jpg")

    def displayRec(self, recNum):
   
        print("Display RGB image ", recNum)
        try:
            cachedData = self.jsonFF.read_jsonFFcached(self.jsonFF["Data"], recNum, self.inst_vars.inst_n, self.inst_vars.globalTrigCount)
            cachedHeader = self.jsonFF.read_jsonFFcached(self.jsonFF["Header"], recNum, self.inst_vars.inst_n, self.inst_vars.globalTrigCount)
        except KeyError:
            return
        
        imgPath = path.join(self.inst_vars.inst_cfg["Data"]["absolutePath"], "Canon")
        imgFile = cachedData[str(recNum)][1]     #Get filename
        imgFile = path.join(imgPath, "prev_" + path.split(imgFile)[1])
        self.ui_signals["updateImage"].emit(imgFile)

    def close(self):
        self.cam.exit()
        self.jsonFF["Header"]["Images Captured"] = self.inst_vars.inst_n


class Ui_interface(QtCore.QObject):
      
    def init(self):
        pass
        # try:
        #     self.clearLayout(self.ui.layout1)      #Clear layout if it exists so that instrument resets work properly
        # except:
        #     self.ui.layout1 = QtGui.QVBoxLayout()
        #     self.ui.layout1.setContentsMargins(0,0,0,0)
        #     self.ui.pltWidget.setLayout(self.ui.layout1)
        
        # self.label = QtGui.QLabel()
        # self.ui.layout1.addWidget(self.label)
        
    def updateImage(self, data):
        if self.ui_large:
            if type(data) is str:
                fname = data
            else:
                with open("prev.jpg", 'wb') as f:
                    f.write(data)
                    fname = "prev.jpg"
            pixmap = QPixmap(fname)
            self.ui.label.setPixmap(pixmap.scaled(self.ui.label.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio))
            #print("Pixmap: %d x %d" % (pixmap.width(), pixmap.height()))
            #self.ui.label.resize(pixmap.width(), pixmap.height())
            
    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout()) 
        