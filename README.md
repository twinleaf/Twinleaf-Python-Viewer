# Twinleaf Python Viewer

Provides a Python graphical user interface to view sensor data. Currently works for our VMR magnetometers and SYNC units and can be used to view data from a single sensor, or multiple synchronized sensors. 

*This program is under early-stage active development and we hope you will report issues, bugs, and feature requests.*

## Prerequisites

Python > 3.6 *with Tk*. To install:

    % brew install python-tk

## Setting Up the GUI

To use this viewer, type:

    % pip3 install tlview

Then, run the program as follows, depending on your platform:

    % tlview # default connection to proxy at tcp://localhost
    % tlview /dev/cu.usbmodem123495 # macOS, USB CDC
    % tlview /dev/cu.usbserial123456 # macOS, USB FTDI
    % tlview /dev/ttyACM0 # Linux, USB CDC
    % tlview /dev/ttyUSB0 # Linux, USB FTDI
    % tlview /dev/ttyS3 # WSL
    % tlview COM3 # Windows
    % tlview udp://tio-sync8.local # macOS, linux
    % tlview tcp://10.0.0.x # macOS, Linux, connection to proxy

Visit our [Getting Started](https://twinleaf.com/start/) page for more details on getting started with Twinleaf sensors.

## Known Issues

- There are momentary pauses in the graph animation in some configurations.
