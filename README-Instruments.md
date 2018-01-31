# Instrument Modules

|Instrument|Dependencies|Notes|
|----------|------------|-----|
|**Ocean Optics USB2000+**|
|
||- *python-seabreeze*                                                                                                                                |
||                                                                                                                                                    |
||    Follow the instructions to install python-seabreeze from [https://github.com/ap--/python-seabreeze](https://github.com/ap--/python-seabreeze).  |
||                                                                                                                                                    |
||- *pyqtgraph*                                                                                                                                       |
||                                                                                                                                                    |
||    A standard pip install ("sudo pip install pyqtgraph") should work.                                                                              |
||                                                                                                                                                    |
||- *numpy*                                                                                                                                           |
||                                                                                                                                                    |
||    A standard pip install ("sudo pip install numpy") should work.                                                                                  |
||                                                                                                                                                    |
||                                                                                                                                                    |
|**ICI Thermal Camera**|
||                                                                                                                                                                                                                  |
||- *pyqtgraph*                                                                                                                                                                                                     |
||                                                                                                                                                                                                                  |
||    A standard pip install ("sudo pip install pyqtgraph") should work.                                                                                                                                            |
||                                                                                                                                                                                                                  |
||- *numpy*                                                                                                                                                                                                         |
||                                                                                                                                                                                                                  |
||    A standard pip install ("sudo pip install numpy") should work.                                                                                                                                                |
||                                                                                                                                                                                                                  |
||- *ICI Library, Firmware and Calibrations Files*                                                                                                                                                                  |
||                                                                                                                                                                                                                  |
||    All of these should be obtained from ICI.  The library should be something like "libici9000.a" (compiled for appropriate target), the firmware “ici9000.hex” and the calibration file(s) “Cal6001194F.bin”.   |
||                                                                                                                                                                                                                  |
||- *C++/Python Wrapper*                                                                                                                                                                                            |
||                                                                                                                                                                                                                  |
||    Compiled on Raspberry Pi and linked to ICI Library.  Sets up C wrapper around C++ calls which in turn can be called by ctypes in Python.                                                                      |
|
|**Pixhawk**|
|
||- *dronekit*                                                                                                                         |
||    A standard pip install ("sudo pip install dronekit") should work.  ([http://python.dronekit.io/](http://python.dronekit.io/))    |
||                                                                                                                                     |
|
|**Camera Shutter, Raspberry Pi**|
|
||- *RPi.GPIO*                                                                                                                                                                                                                                |
||                                                                                                                                                                                                                                            |
||    Part of the standard Raspberry Pi library; should be installed by default in Raspbian.                                                                                                                                                  |
||                                                                                                                                                                                                                                            |
||OR                                                                                                                                                                                                                                          |
||                                                                                                                                                                                                                                            |
||- *GPIOEmulator*                                                                                                                                                                                                                            |
||                                                                                                                                                                                                                                            |
||    An emulator for the Raspberry Pi’s GPIO ports.  Works with both inputs and outputs, interrupts are not supported, however. ([https://sourceforge.net/projects/pi-gpio-emulator/](https://sourceforge.net/projects/pi-gpio-emulator/))   |
|
|
|**Other**
|
||- On Windows with Intel x86 or x64 processors, some packages use numpy-mkl, available precomplied here: [http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy](http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy) |


# Instrument Configuration 
### (instruments/\<instrument\>/inst_cfg.ini)

While the majority of keys in instrument configurations are specific to their individual modules, below are the required and common ones.

Sections:

- **Instrument Information \[InstrumentInfo\] (Required)**

    This section should have information to identify an instrument such as model/serial numbers, hardware specifcations, etc.  The required keys are "Name" and “Model”.  For example:  
    
    > [InstrumentInfo]  
    Name = USB2000+ Pair  
    Model = OceanOptics USB 2000+

- **Initialization \[Initialization\] (Optional)**

    This section should be used for configuration information needed by the device initialization.  For example:

    > [Initialization]  
    UpwardDevice = USB2+U06380  
    DownwardDevice = USB2+H16507

    > \#Integration time in microseconds  
    IntegrationTime = 10000  
    CorrectDarkCounts = True  
    CorrectNonlinearity = True

- **Data Storage \[Data\] (Optional)**

    This section should have at least the key "Destination" which determines where, relative to the main MoDaCS data directory, data for this instrument should be stored.  For example (would create a directory: “MoDaCS Data/SpecData”):

    > [Data]  
    Destination = SpecData

- **Trigger Settings \[Trigger\] (Recommended)**

    - Source: Comma separated list of what global triggers this instrument will respond to.  If not specified, any trigger will apply.  
    Special values are:  
        + "Timed" - Uses internal interval timer  (see interval option below)
        + "*" - Respond to all triggers
        + "Manual" - Respond to a user clicking the "Global Trigger" button
	 
    - Interval: Integer in milliseconds specifying the frequency of the "Timed" trigger for this instrument.  

    For example:  

    >[Trigger]  
    Source = Timed, Manual, RaspPi  
    Interval = 1000