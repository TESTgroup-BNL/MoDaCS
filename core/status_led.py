import time

try:
    import RPi.GPIO as GPIO
    import neopixel, board
    usingRasPi = True
    # LED strip configuration:
    LED_COUNT      = 7      # Number of LED pixels.
    LED_PIN        = board.D18      # GPIO pin connected to the pixels (18 uses PWM!).
    #LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
    LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA        = 10       # DMA channel to use for generating signal (try 5)
    LED_BRIGHTNESS = 1     # Set to 0 for darkest and 255 for brightest
    LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
    LED_STRIP      = neopixel.GRB   # Strip type and colour ordering
except:
    usingRasPi = False

from PyQt5 import QtCore
from PyQt5.QtCore import QThread, QObject, pyqtSlot, QTimer, pyqtSignal


class StatusLED(QObject):

    setLED = pyqtSignal(int,int,int)
    setBlink = pyqtSignal(int,int,int,int,int,int,int,int,int)

    def __init__(self):
        super().__init__()
        if usingRasPi == True:            
            self.thread = QtCore.QThread()
            self.moveToThread(self.thread)
            self.thread.started.connect(self.init)
            self.thread.start()
    
    def init(self):
        # Create NeoPixel object with appropriate configuration.
        self.strip = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False, pixel_order=LED_STRIP)
        # Initialize the library (must be called once before other functions).
        #self.strip.begin() (not anymore!)
        
        self.setLED.connect(self.setColor)
        self.setBlink.connect(self.blink)
        
        self.rainbow(self.strip)

    @pyqtSlot(int,int,int)
    def setColor(self, R, G, B):
        #for i in range(LED_COUNT):
        #    self.strip.setPixelColor(i, Color(G,R,B))
        self.strip.fill((R,G,B))
        self.strip.show()
        
    @pyqtSlot(int,int,int,int,int,int,int,int,int)            
    def blink(self,R1,G1,B1,t1, R2,G2,B2,t2, cycles):
        self.R1 = R1
        self.G1 = G1
        self.B1 = B1
        self.t1 = t1
        self.R2 = R2
        self.G2 = G2
        self.B2 = B2
        self.t2 = t2
        self.cycles = cycles
        self.cyclecount = 0
        self.blinkState = True
        self.doBlink()
            
    @pyqtSlot()
    def doBlink(self):
        if self.blinkState:
            self.blinkState = False
            self.setColor(self.R1,self.G1,self.B1)
            QTimer.singleShot(self.t1, self.doBlink)
        else:
            self.blinkState = True
            self.setColor(self.R2,self.G2,self.B2)      
            if self.cyclecount < self.cycles:
                self.cyclecount += 1
                QTimer.singleShot(self.t2, self.doBlink)
   
        
    def wheel(self, pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)

    def rainbow(self, strip, wait_ms=10, iterations=1):
        """Draw rainbow that fades across all pixels at once."""
        for j in range(256*iterations):
            #for i in range(LED_COUNT):
            #    strip[i] = self.wheel(((i*int(255/LED_COUNT))+j) & 255)
            strip.fill(self.wheel(j & 255))
            strip.show()
            time.sleep(wait_ms/1000.0)
    