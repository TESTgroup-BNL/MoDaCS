# MoDaCS
Modular Data Collection System


This package is currently under development.

The goal is to develop a framework that uses a central module/UI to coordinate data acquisition, synchronization with a UAS control system and data storage through a common interface and interchangeable, hardware specific software modules.  Utilizing this structure, the system can be easily reconfigured on the fly to meet the needs of a specific platform or operation, eliminating the need to redevelop complete acquisition systems for specific instrument/platform configurations.  As an instrument module library develops, adding new hardware to a platform will become as simple as enabling the corresponding software module.

Currently being developed with:
- Python 3.5
- Qt 5.7 (not using any features past 5.3 for compatibility with default Raspbian Jessie Qt package)
