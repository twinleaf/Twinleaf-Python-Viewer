# Twinleaf-Python-Viewer

Provides a Python GUI to view sensor data.  Currently works for our VMR magnetometers and SYNC units.  This program is newly created, and we are working to find and fix bugs.

Known Bugs:
- If used with a single VMR without a SYNC unit, there are momentary pauses in the graph animation

## Setting Up the GUI

To use this viewer, type:

    % pip3 install tl-pyview
    
Then, run the program with the command

    % vectorgui [usb-path]
    
where `[usb-path]` is replaced by the port path specific to your setup.  For MacOS, the path will be in the form `/dev/cu.usbXXXXX`.  For Linux, it will be in the form `/dev/ttyUSB0` or `/dev/ttyACM`.  For Windows, it will look like `COMX`.  Visit our [Getting Started](https://twinleaf.com/start/) page for more details.
