'''
Created on Jul 13, 2016

@author: amcmahon
'''
import sys, threading, time
from PyQt5 import QtWidgets, QtCore
from UI.ui import Ui_MainWindow
from GPIOEmulator.EmulatorGUI import GPIO

class Signals(QtCore.QObject):
      
    sigA = QtCore.pyqtSignal()
    
    
class Main(QtWidgets.QMainWindow):
   
    def __init__(self, parent=None):
        
        self.UI_init()
        
        
    def UI_init(self):
        
        QtWidgets.QMainWindow.__init__(self)
        
        self.sig = Signals()
        self.sig.sigA.connect(self.reset)
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.btn_Start.released.connect(self.t_Start)
        self.ui.btn_Reset.released.connect(self.e_reset)
        self.t = QtCore.QTimer()
        self.t.timeout.connect(self.displaytest)
        self.ui.plainTextEdit.textChanged.connect(self.updatecount)
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(15, GPIO.IN)
        
        #GPIO.add_event_detect(17, GPIO.RISING, callback=reset, bouncetime=300) 
        t_gpio = threading.Thread(target=self.gpio_monitor)
        t_gpio.start()    
        
        
    def e_reset(self):
        self.sig.sigA.emit()
        
    def t_Start(self):
        self.t.start(500)
        self.ui.plainTextEdit.appendPlainText("Timer Started!")

    def displaytest(self):
        self.ui.progressBar.setValue(self.ui.progressBar.value() + 10)
        if self.ui.progressBar.value() > 90:
            self.t.stop()
            self.ui.plainTextEdit.appendPlainText("Timer Stopped!")
          
    def reset(self):
        self.t.stop()
        self.ui.progressBar.setValue(0)
        self.ui.plainTextEdit.appendPlainText("Reset!")       
        
    def updatecount(self):
        self.ui.lcdNumber.display(self.ui.lcdNumber.intValue() + 1)


    def gpio_monitor(self):
        triggered = False
        while(1):
            if GPIO.input(15) == True and triggered == False:
                self.sig.sigA.emit()
                time.sleep(1)
                triggered = True
            elif triggered == True:
                triggered = False
            time.sleep(.01)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())
    GPIO.cleanup()