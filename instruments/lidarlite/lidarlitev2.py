""" =============================================================================
  LIDARLite Arduino Library:
  The purpose of this library is two-fold:
  1.  Quick access all the basic functions of LIDAR-Lite via Arduino without
      worrying about specifics
  2.  By reading through this library, users of any platform will get an
      explanation of how to use the various functions of LIDAR-Lite and see an
      Arduino example along side.
  This libary was written by Austin Meyers (AK5A) with PulsedLight Inc. And was
  likely downloaded from:
  https://github.com/PulsedLight3D/LIDARLite_v2_Arduino_Library
  Visit http://pulsedlight3d.com for documentation and support requests
  
  "Translated" to Python by Andrew McMahon    11/2/15
============================================================================= """

import smbus
import time
import RPi.GPIO as GPIO

class LidarLite:

    I2C_Bus = smbus.SMBus(1)

    def __init__(self, address=0x62):
        self.LidarLiteI2cAddress = address

    def begin(self, configuration):
        GPIO.setmode(GPIO.BCM)
        try:
            self.I2C_Bus = smbus.SMBus(1)    #Setup I2C
            time.sleep(0.5)
            self.configure(configuration)
            return 0
        except:
            return -1
        
    def configure(self, configuration):
        if (configuration == 0): self.write(0x00,0x00,self.LidarLiteI2cAddress)
        elif (configuration == 1): self.write(0x04,0x00,self.LidarLiteI2cAddress)        #Set aquisition count to 1/3 default value, faster reads, slightly noisier values
        elif (configuration == 2): self.write(0x1c,0x20,self.LidarLiteI2cAddress)        #Low noise, low sensitivity: Pulls decision criteria higher above the noise, allows fewer false detections, reduces sensitivity
        elif (configuration == 3): self.write(0x1c,0x60,self.LidarLiteI2cAddress)        #High noise, high sensitivity: Pulls decision criteria into the noise, allows more false detections, increses sensitivity
        
    def beginContinuous(self, modePinLow, interval, numberOfReadings):
        #  Register 0x45 sets the time between measurements. 0xc8 corresponds to 10Hz
        #  while 0x13 corresponds to 100Hz. Minimum value is 0x02 for proper
        #  operation.
        self.write(0x45,interval,self.LidarLiteI2cAddress)
        
        #  Set register 0x04 to 0x20 to look at "NON-default" value of velocity scale
        #  If you set bit 0 of 0x04 to "1" then the mode pin will be low when done
        if (modePinLow == True):
            self.write(0x04,0x21,self.LidarLiteI2cAddress)
        else:
            self.write(0x04,0x20,self.LidarLiteI2cAddress)

        #  Set the number of readings, 0xfe = 254 readings, 0x01 = 1 reading and
        #  0xff = continuous readings
        self.write(0x11,numberOfReadings,self.LidarLiteI2cAddress)
        
        #  Initiate reading distance
        self.write(0x00,0x04,self.LidarLiteI2cAddress)

    def distance(self, stablizePreampFlag, takeReference):
        if (stablizePreampFlag == True):
            # Take acquisition & correlation processing with DC correction
            self.write(0x00,0x04,self.LidarLiteI2cAddress)
        else:
            # Take acquisition & correlation processing without DC correction
            self.write(0x00,0x03,self.LidarLiteI2cAddress)
            
        # Array to store high and low bytes of distance
        ##distanceArray = [None] * 2
        # Read two bytes from register 0x8f. (See autoincrement note above)
        distance = self.read(0x8f,2,True,self.LidarLiteI2cAddress)
        # Shift high byte and add to low byte
        ##distance = (distanceArray[0] << 8) + distanceArray[1]
        return distance
    
    def distanceContinuous(self):
        ##distanceArray = [None] * 2            # Array to store high and low bytes of distance
        distanceArray = self.read(0x8f,2,False,self.LidarLiteI2cAddress)     # Read two bytes from register 0x8f. (See autoincrement note above)
        distance = (distanceArray[0] << 8) + distanceArray[1]            # Shift high byte and add to low byte
        return(distance)

    def velocity(self):
        #  Write 0xa0 to 0x04 to switch on velocity mode
        self.write(0x04,0xa0,self.LidarLiteI2cAddress)
        #  Write 0x04 to register 0x00 to start getting distance readings
        self.write(0x00,0x04,self.LidarLiteI2cAddress)
        #  Array to store bytes from read function
        ##velocityArray = [None]
        #  Read 1 byte from register 0x09 to get velocity measurement
        return int(self.read(0x09,1,True,self.LidarLiteI2cAddress))
        #  Convert 1 byte to char and then to int to get signed int value for velo-
        #  city measurement
        ##return(int(char(velocityArray[0])))
        
    def signalStrength(self):
        #  Array to store read value
        ##signalStrengthArray = [None]
        #  Read one byte from 0x0e
        return self.read(0x0e, 1, False, self.LidarLiteI2cAddress)

    def correlationRecordToArray(self, numberOfReadings):
        arrayToSave = [None] * numberOfReadings
        # Array to store read values
        correlationArray = [None] * 2
        # Var to store value of correlation record
        correlationValue = 0
        #  Selects memory bank
        self.write(0x5d,0xc0,self.LidarLiteI2cAddress)
        # Sets test mode select
        self.write(0x40, 0x07,self.LidarLiteI2cAddress)
        for i in range(0, numberOfReadings):
            # Select single byte
            self.read(0xd2,2,correlationArray,False,self.LidarLiteI2cAddress)
            #  Low byte is the value of the correlation record
            correlationValue = int(correlationArray[0])
            # if upper byte lsb is set, the value is negative
            if (correlationArray[1] == 1):
                correlationValue |= 0xff00
            arrayToSave[i] = correlationValue

        # Send null command to control register
        self.write(0x40,0x00,self.LidarLiteI2cAddress)
        return arrayToSave

    def correlationRecordToConsole(self, separator, numberOfReadings):
        # Array to store read values
        correlationArray = [None] * 2
        # Var to store value of correlation record
        correlationValue = 0
        #  Selects memory bank
        self.write(0x5d,0xc0,self.LidarLiteI2cAddress)
        # Sets test mode select
        self.write(0x40, 0x07,self.LidarLiteI2cAddress)
        for i in range(0, numberOfReadings):
            # Select single byte
            self.read(0xd2,2,correlationArray,False,self.LidarLiteI2cAddress)
            #  Low byte is the value of the correlation record
            correlationValue = correlationArray[0]
            # if upper byte lsb is set, the value is negative
            if (int(correlationArray[1]) == 1):
                correlationValue |= 0xff00

            print(int(correlationValue))
            print(separator)

        # Send null command to control register
        self.write(0x40,0x00,self.LidarLiteI2cAddress)

    def changeAddress(self, newI2cAddress, disablePrimaryAddress, currentLidarLiteAddress):
        #  Array to save the serial number
        ##serialNumber = [None] * 2    #unsigned char 
        newI2cAddressArray = [None] #unsigned char 
        
        #  Read two bytes from 0x96 to get the serial number
        serialNumber = self.read(0x96,2,False,currentLidarLiteAddress)
        #  Write the low byte of the serial number to 0x18
        self.write(0x18,serialNumber[0],currentLidarLiteAddress)
        #  Write the high byte of the serial number of 0x19
        self.write(0x19,serialNumber[1],currentLidarLiteAddress)
        #  Write the new address to 0x1a
        self.write(0x1a,newI2cAddress,currentLidarLiteAddress)
        
        while(newI2cAddress != newI2cAddressArray[0]):
            newI2cAddressArray = self.read(0x1a,1,False,currentLidarLiteAddress)
        
        #  Choose whether or not to use the default address of 0x62
        if (disablePrimaryAddress):
            self.write(0x1e,0x08,currentLidarLiteAddress)
        else:
            self.write(0x1e,0x00,currentLidarLiteAddress)
        
        return newI2cAddress;
        
    def changeAddressMultiPwrEn(self, numOfSensors, pinArray, i2cAddressArray, usePartyLine):
        for i in range(0, numOfSensors):
            GPIO.setup(pinArray[i], GPIO.OUT)    # Pin to first LIDAR-Lite Power Enable line    
            time.sleep(.002)
            GPIO.output(pinArray[i], True)
            time.sleep(.02)
            self.configure(1)
            self.changeAddress(i2cAddressArray[i],True)    # We have to turn off the party line to actually get these to load

        if (usePartyLine == True):
            for i in range(0, numOfSensors):
                self.write(0x1e,0x00,i2cAddressArray[i])


    def write(self, myAddress, myValue, CurrentAddress):
        return self.I2C_Bus.write_byte_data(CurrentAddress, myAddress, myValue)
        

    def read(self, myAddress, numOfBytes, monitorBusyFlag, CurrentAddress):
        if (numOfBytes == 2):
                        return self.I2C_Bus.read_word_data(CurrentAddress, myAddress)
        else:
            return self.I2C_Bus.read_byte_data(CurrentAddress, myAddress)
            #return self.I2C_Bus.read_i2c_block_data(CurrentAddress, myAddress, numOfBytes) 
