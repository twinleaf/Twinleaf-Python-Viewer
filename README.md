# Twinleaf Python Viewer

Provides a Python graphical user interface to view sensor data. Currently works for our VMR magnetometers and SYNC units and can be used to view data from a single sensor, or multiple synchronized sensors. 

*This program is under early-stage active development and we hope you will report issues, bugs, and feature requests.*

## Prerequisites

Python > 3.6 *with Tk*. To install:

    % brew install python3-tk # macOS
    % apt install python-tk # Linux

on windows it should be installed by default.

## Installation

Using pip (coming soon):

    % pip3 install tioview

Clone this repository and install using either:

    % pip3 install .

or

    % python3 setup.py

Then, run the program as follows, depending on your platform:

    % tioview # default connection to proxy at tcp://localhost
    % tioview /dev/cu.usbmodem123495 # macOS, USB CDC
    % tioview /dev/cu.usbserial123456 # macOS, USB FTDI
    % tioview /dev/ttyACM0 # Linux, USB CDC
    % tioview /dev/ttyUSB0 # Linux, USB FTDI
    % tioview /dev/ttyS3 # WSL
    % tioview COM3 # Windows
    % tioview udp://tio-sync8.local # macOS, linux
    % tioview tcp://10.0.0.x # macOS, Linux, connection to proxy

This installation also includes a Python graphical user interface specifically designed for a single VMR sensor.  Run this program with 

    % vm_monitor
  
Visit our [Getting Started](https://twinleaf.com/start/) page for more details on getting started with Twinleaf sensors.
