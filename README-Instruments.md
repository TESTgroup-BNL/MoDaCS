# Instrument Modules


<table><tr><th>Instrument</th><th>Dependencies</th><th>Notes</th></tr>
<tr><td rowspan="3">

**Ocean Optics USB2000+ Pair**
</td><td>

*pyqtgraph*
</td><td>A standard pip install should work (on Raspbian, "sudo pip install pyqtgraph").</td></tr>
<tr><td>
 
*numpy*
</td><td> A standard pip install should work (on Raspbian, "sudo pip install numpy").</td></tr>
</td><td>

*python-seabreeze*
 </td><td>
 
 Follow the instructions to install python-seabreeze from [https://github.com/ap--/python-seabreeze](https://github.com/ap--/python-seabreeze).</td></tr>
<tr><td rowspan="4">

**ICI Thermal Camera**
</td><td>

*pyqtgraph* 
</td><td>A standard pip install should work (on Raspbian, "sudo pip install pyqtgraph").</td></tr>
<tr><td>
 
*numpy*
</td><td> A standard pip install should work (on Raspbian, "sudo pip install numpy").</td></tr>
<tr><td>
 
*ICI Library, Firmware and Calibrations Files*
</td><td>All of these should be obtained from ICI.  The library should be something like "libici9000.a" (compiled for appropriate target), the firmware “ici9000.hex” and the calibration file(s) “Cal6001194F.bin”.</td></tr>
<tr><td>
 
*C++/Python Wrapper*
</td><td>Compiled on Raspberry Pi and linked to ICI Library.  Sets up C wrapper around C++ calls which in turn can be called by ctypes in Python.</td></tr>
<tr><td>

**Pixhawk**
</td><td>

*dronekit*
</td><td>

A standard pip install ("sudo pip install dronekit") should work.  ([http://python.dronekit.io/](http://python.dronekit.io/))</td></tr>

<tr><td rowspan="2">

**Camera Shutter and Raspberry Pi**
</td><td>

*RPi.GPIO*
</td><td>Part of the standard Raspberry Pi library; should be installed by default in Raspbian.</td><tr>
</td><td>

OR<br>
*GPIOEmulator*
</td><td>

An emulator for the Raspberry Pi’s GPIO ports.  Works with both inputs and outputs, interrupts are not supported, however. ([https://sourceforge.net/projects/pi-gpio-emulator/](https://sourceforge.net/projects/pi-gpio-emulator/))
</td></tr>
<tr><td>

**Other**
</td><td>

*numpy-mkl*
</td><td>

On Windows with Intel x86 or x64 processors, some packages use numpy-mkl, available precomplied here: [http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy](http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy)
</td></tr>

</table>

Some other instrument/utility modules that are somewhat functional but under development:

|Instrument|Description|
|----------|-----------|
|atm_sensors|Listens for a serial stream over raw UDP of atmospheric state data (temperature, RH, pressure), saves it to a CSV and displays a realtime plot.  (Based on ip_datasream.)|
|flir_lepton|Interfaces with a FLIR Lepton module for thermal imaging.|
|ip_datastream|Listens for a serial stream over raw UDP and saves it to a CSV.|
|lidarlite|Interfaces with a [LIDAR-Lite v2](https://www.pulsedlight3d.com/products/lidar-lite-v2-blue-label.html) sensor for distance/altitude information.|
|spectrometer|Deprecated module, originally used for testing/debugging.  Generates random, fake data.|
|usb2000|Deprecated module, interfaced with a single Ocean Optics USB-2000.|
|user_input|Passes a user entered string as an event.  Can be used to set prefixes for the data files saved by the ici_thermal module.|

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