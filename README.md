# MoDaCS
Modular Data Collection System


This package is currently under development.

The goal is to develop a framework that uses a central module/UI to coordinate data acquisition, synchronization with a UAS control system and data storage through a common interface and interchangeable, hardware specific software modules.  Utilizing this structure, the system can be easily reconfigured on the fly to meet the needs of a specific platform or operation, eliminating the need to redevelop complete acquisition systems for specific instrument/platform configurations.  As an instrument module library develops, adding new hardware to a platform will become as simple as enabling the corresponding software module.

Currently being developed with:
- Python 3.5
- Qt 5.7 (not using any features past 5.3 for compatibility with default Raspbian Jessie Qt package)


*Security note:* The remote monitoring/control interface is NOT secure in any way and should not be used on a public a network.  There is currently no authentication process and the protocol allows almost any Qt signal/slot in the application to be targeted.

## Tl;dr, show me some data! (Viewer Mode Quickstart)
1.  Install ([Python 3](https://www.python.org/downloads/))
2.  Install PyQt 5 and pyqtgraph (run "pip install pyqt5")
3.  From the MoDaCS directory, run "python .\core\main.py -f .\ExampleData\RunData.json"

## MoDaCS Installation

Requirements:

- *python* (32-bit) >= 3.4 ([https://www.python.org/downloads/](https://www.python.org/downloads/))
- *pyqt5* (available via pip on Windows or under the package name "python3-pyqt5" on Raspbian Jessie)

Optional:

- *paramiko* (for SFTP)

    Available via pip but depends on cryptography which has some binary dependencies.
    
    For Raspbian Jessie:  
    1. Run sudo apt-get update
    2. Run sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
    3. Run sudo pip (or pip3) install --upgrade setuptools
    4. Run sudo pip (or pip3) install paramiko
       Note: this step can take ~20 mins on some Rasp Pi 2 systems while it builds some of the cryptography dependencies
            
- *neopixel* (for RGB feedback LED on Raspberry Pi)

    Available from Adafruit: https://learn.adafruit.com/neopixels-on-raspberry-pi/software

- *pyqtgraph* (allows Viewer Mode to work for most instruments with no other dependencies)

    Available via pip
    
## [Instrument Modules Information](README-Instruments.md)
    
## Running MoDaCS

1. **Setup Run Configuration**

    The default run configuration is stored in the file "MoDaCS/core/run_cfg.ini".  Alternates can be specified at runtime (see step 3).

2. **Setup Instrument Configurations**

    Instrument configurations are stored in the file(s) "/*instrument*/inst_cfg.ini".

3.
    a. **Start Remote Client & Server for Data Collection**

    For both the client and server, from the MoDaCS directory run "python ./core/main.py".  Ensure that the default python installation is >= python 3.4, or specify python3 if necessary.  Optionally, use the “-c <config file>” option to use an alternative configuration file.  This is useful for keeping both server and client configurations on the same machine.  For example: “python ./core/main.py -c ./core/run_cfg_client.ini”.

    On the Raspberry Pi, the default configuration (server) will auto-start from boot.  To restart from a terminal, in addition to the command above, run "startx".

    Note:  It is recommended to start the client first so that all UI elements are initialized properly.  Starting the client after the server will still work without issue, but indicators will be invalid until explicitly updated by the server.  The client computer should have the same active instrument modules and instrument configurations as the server.

    **OR**
    
    b. **Start Viewer Mode**
    To start MoDaCS in viewer mode (to view previously saved data data), from the MoDaCS directory run "python ./core/main.py -o".  Ensure that the default python installation is >= python 3.4, or specify python3 if necessary.
    Alternatively, if running in data collection mode, the File->Load Records menu item will restart MoDaCS in viewer mode.  An open file dialog will appear.  The "RunData.json" file from the session being opened should be selected.


## Run Configuration
### ([core/run_cfg.ini](core/run_cfg.ini))

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

    This section requires a single key "Location", which should be the absolute path to the directory where MoDaCS should store data.  Optionally, "AutoTransfer" will enable SFTP transfers of a sessions data from a server to client instance.
    The transfer is initiated when the server instance is ready to close.  In a typical setup, a client would issue a remote shutdown command causing a server to stop, transfer data from that session and then shutdown.
    "SSH_User" and "SSH_Password" must be included to authenticate the SFTP connection.
    
    For example:  

  > [Data]  
  Location = C:\\temp\\MoDaCS Data  
  AutoTransfer = True  
  SSH_User = pi  
  SSH_Password = <your password here>

- **Event Handlers [Events]**

    This section should contain a list of the event handlers included in "event_handlers.py" and inputs and outputs they use, as well as “direct connetions”.  For example:  

  > \#Event: Inputs (comma separated); Outputs (comma separated)  
  > \#Direct Connection: Input -> Output  
  
  > [Events]  
  shutterspeed: pixhawk.shutter; camerashutter.shutterspeed  
  auto_trig: pixhawk.trigger->GlobalTrigger  
  dig_trig: raspberrypi.digitalTrig->GlobalTrigger  
  fileName: user_input.fileName->ici_thermal.fileName  

- **UI Options \[UI\] (optional)**
    
    |Key|Options|Description|
    |---|-------|-----------|
    |Size|-large <br> -small|Determines the UI size mode.  "Small" is designed as a limited interface for a 320x240 fixed display while "large" operates like a typical resizable desktop application.|
    |WaitForNTP|True/False|When running on an ARM based device, tries to contact an NTP server to sync time before starting to record data.  (Times out after 1 minute.)|

    For example:  

  > [UI]  
  Size = large  
  WaitForNTP = True  

- **Server Options  [Server]**

    |Key|Options|Description|
    |---|-------|-----------|
    |Enabled|True/False|Sets whether or not this instance should run as a server|
    |TCP_Server_IP| IP Address |The server IP to use (the IP of this computer).  This options exists to differentiate between different networks when multiple network adapters are active.|
    |TCP_Server_Port| 0-65535 | The server (local) port to use|
    |TCP_Client_IP| IP Address |  The client IP to use (the IP of the remote computer).|
    |TCP_Client_Port| 0-65535 | The client port to use|
    |AllowControl| True/False | Sets whether or to allow remote clients to control this instance |
    
    For example:  
    
  > [Server]  
  Enabled = True  
  TCP_Server_IP = 192.168.1.101  
  TCP_Client_IP = 192.168.1.100  
  TCP_Server_Port = 9400  
  TCP_Client_Port = 9400  
  AllowControl = True  

- **Remote Client Options  [Client]**

    |Key|Options|Description|
    |---|-------|-----------|
    |Enabled|True/False|Sets whether or not this instance should run as a remote client|
    |TCP_Server_IP| IP Address |The remote server IP to use. |
    |TCP_Server_Port| 0-65535 | The remote server port to use |
    |TCP_Client_IP| IP Address | The client IP to use (the IP of this computer).  This options exists to differentiate between different networks when multiple network adapters are active.|
    |TCP_Client_Port| 0-65535 | The client (local) port to use |
    |ProvideControl| True/False | Sets whether or to send remote control commands to server |
 
    For example:  

  > [Client]  
  Enabled = True  
  TCP_Server_IP = 192.168.1.101  
  TCP_Client_IP = 192.168.1.100  
  TCP_Server_Port = 9400  
  TCP_Client_Port = 9400  
  ProvideControl = True  

    Note on Server/Client configuration: TCP_Server_IP and TCP_Server_Port are mostly redundant and should almost always be the same for both the Server and Client modules.  The same applies to TCP_Client_IP and TCP_Client_Port.


- **Run Instrument in Main Thread \[MainThread\] (optional, for debugging only)**

    This section should be a list of instrument modules that (if set to True) will NOT be run in their own thread (and will instead stay in the main UI thread).  This can help to catch breakpoints when debugging in certain circumstances.  For example:

  > [MainThread]  
  usb2000-pair = True  

  