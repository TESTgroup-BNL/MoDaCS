# MoDaCS
Modular Data Collection System


This package is currently under development.

The goal is to develop a framework that uses a central module/UI to coordinate data acquisition, synchronization with a UAS control system and data storage through a common interface and interchangeable, hardware specific software modules.  Utilizing this structure, the system can be easily reconfigured on the fly to meet the needs of a specific platform or operation, eliminating the need to redevelop complete acquisition systems for specific instrument/platform configurations.  As an instrument module library develops, adding new hardware to a platform will become as simple as enabling the corresponding software module.

Currently being developed with:
- Python 3.5
- Qt 5.7 (not using any features past 5.3 for compatibility with default Raspbian Jessie Qt package)


*Security note:* The remote monitoring/control interface is NOT secure in any way and should not be used on a public a network.  There is currently no authentication process and the protocol allows almost any Qt signal/slot in the application to be targeted.


##MoDaCS Installation

Requirements:

- python (32-bit) >= 3.4 ([https://www.python.org/downloads/](https://www.python.org/downloads/))
- pyqt5 (available via pip)


##Instrument Dependencies

**Ocean Optics USB2000+**

- *python-seabreeze*

    Follow the instructions to install python-seabreeze from [https://github.com/ap--/python-seabreeze](https://github.com/ap--/python-seabreeze).
    
- *pyqtgraph*
    
    A standard pip install ("sudo pip install pyqtgraph") should work.

- *numpy*

    A standard pip install ("sudo pip install numpy") should work.

<br>

**ICI Thermal Camera**

- *pyqtgraph*

    A standard pip install ("sudo pip install pyqtgraph") should work.

- *numpy*

    A standard pip install ("sudo pip install numpy") should work.

- *ICI Library, Firmware and Calibrations Files*

    All of these should be obtained from ICI.  The library should be something like "libici9000.a" (compiled for appropriate target), the firmware “ici9000.hex” and the calibration file(s) “Cal6001194F.bin”.

- *C++/Python Wrapper*

    Compiled on Raspberry Pi and linked to ICI Library.  Sets up C wrapper around C++ calls which in turn can be called by ctypes in Python.

<br>

**Pixhawk**

- *dronekit*
    A standard pip install ("sudo pip install dronekit") should work.  ([http://python.dronekit.io/](http://python.dronekit.io/))

<br>

**Camera Shutter, Raspberry Pi**

- *RPi.GPIO*

    Part of the standard Raspberry Pi library; should be installed by default in Raspbian.  
  
OR

- *GPIOEmulator*

    An emulator for the Raspberry Pi’s GPIO ports.  Works with both inputs and outputs, interrupts are not supported, however. ([https://sourceforge.net/projects/pi-gpio-emulator/](https://sourceforge.net/projects/pi-gpio-emulator/))

<br>

**Other**

- On Windows with Intel x86 or x64 processors, some packages use numpy-mkl, available precomplied here: [http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy](http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy)

##Running MoDaCS

1. **Setup Run Configuration**

	The default run configuration is stored in the file "MoDaCS/core/run_cfg.ini".  Alternates can be specified at runtime (see step 3).

2. **Setup Instrument Configurations**

	Instrument configurations are stored in the file(s) "/*instrument*/inst_cfg.ini".

3. **Start Remote Client & Server**

    For both the client and server, from the MoDaCS directory run "python ./core/main.py".  Ensure that the default python installation is >= python 3.4, or specify python3 if necessary.  Optionally, use the “-c <config file>” option to use an alternative configuration file.  This is useful for keeping both server and client configurations on the same machine.  For example: “python ./core/main.py -c ./core/run_cfg_client.ini”.

	On the Raspberry Pi, the default configuration (server) will auto-start from boot.  To restart from a terminal, in addition to the command above, run "startx".

	Note:  It is recommended to start the client first so that all UI elements are initialized properly.  Starting the client after the server will still work without issue, but indicators will be invalid until explicitly updated by the server.  The client computer should have the same active instrument modules and instrument configurations as the server.

##Run Configuration
###([core/run_cfg.ini](core/run_cfg.ini))

Sections:
- **Active Instruments [Active_Insts]**
	
    This section should have a list of the instrument modules available in the current setup and whether or not to load each.  For example:

  >[Active_Insts]  
  camerashutter = True  
  spectrometer = False  
  pixhawk = True  
  raspberrypi = True  
  usb2000-pair = True  
  ICI_thermal = True  

- **Data Storage [Data]**

	  This section requires a single key "Location", which should be the absolute path to the directory where MoDaCS should store data.  For example:  

    > [Data]  
    > Location = C:\\temp\\MoDaCS Data

- **Event Handlers [Events]**

	  This section should contain a list of the event handlers included in "event_handlers.py" and inputs and outputs they use, as well as “direct connetions”.  For example:  

    > \#Event: Inputs (comma separated); Outputs (comma separated)  
    > \#Direct Connection: Input -> Output  
    
    > [Events]  
    shutterspeed: pixhawk.shutter; camerashutter.shutterspeed  
    auto_trig: pixhawk.trigger->GlobalTrigger  
    dig_trig: raspberrypi.digitalTrig->GlobalTrigger

- **UI Options \[UI\] (optional)**

	  This section has a single key "Size", which determines which UI version to load.  Options are “large” or “small”.  For example:

    > [UI]  
    Size = large

- **Server Options  [Server]**

	- Enabled: Sets whether or not this instance should run as a server

	- TCP_Server_IP: The server IP to use (the IP of this computer).  This options exists to differentiate between different networks when multiple network adaptors are active.

	- TCP_Server_Port: The server port to use

	- AllowControl: Sets whether or to allow remote clients to control this instance  
For example:
    
		> [Server]  
    Enabled = True  
    TCP_Server_IP = 192.168.1.101  
    TCP_Server_Port = 9400  
    AllowControl = True

- **Remote Client Options  [Client]**

	- Enabled: Sets whether or not this instance should run as a remote client

	- TCP_Server_IP: The remote server IP to connect to

	- TCP_Server_Port:The remote server port to connect to

	- ProvideControl: Sets whether or to send remote control commands to server  
For example:

		> [Client]  
    Enabled = False  
    TCP_Server_IP = 192.168.1.101  
    TCP_Server_Port = 9400  
    ProvideControl = True

- **Run Instrument in Main Thread \[MainThread\] (optional, for debugging only)**

    This section should be a list of instrument modules that (if set to True) will NOT be run in their own thread (and will instead stay in the main UI thread).  This can help to catch breakpoints when debugging in certain circumstances.  For example:

    > [MainThread]  
    usb2000-pair = True

#Instrument Configuration 
###(instruments/\<instrument\>/inst_cfg.ini)

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
