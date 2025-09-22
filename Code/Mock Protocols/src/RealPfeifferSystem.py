# Real Pfeiffer System

# This program reads the pressure from a "mock" gauge, the RPM and Drive Current from a "mock" Vacuum Pump, the temperature from a Eurotherm controller, and displays them through a Tkinter GUI
import csv
import os
import serial
import datetime
import numpy as np
import tkinter as tk
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # FigureCanvasTkAgg is a class that allows a Matplotlib plot to be embedded in a Tkinker GUI window
import pymodbus
from pymodbus.client import ModbusTcpClient

#Import the Pfeiffer gauge protocol
import PfiefferVacuumProtocol as pvp

#Import the mock Pfeiffer TC110 (vacuum pump) protocol
import RealPfeifferTC110 as rpt

# Import functions for Interlock System
import InterlockSystemLibrary as isl


# Open the serial port with a 1 second timeout (timeout time is the amount of time it will wait before moving onto the next line of code)
# If "COM1" doesn’t work, you need to find which COM port is assigned to your USB-to-RS485 adapter.
serial_port = serial.Serial("/dev/tty.usbserial-BG000M9B", baudrate=9600, timeout=1)

# Eurotherm controller configuration
eurotherm_IP = "192.168.111.222"   # IP address of the controller
modbus_temperature_parameter_address = 2
eurotherm_device_id = 1
client = ModbusTcpClient(eurotherm_IP)
if not client.connect():
    raise RuntimeError("Could not connect to Modbus TCP server")


        
# Address for querying the two gauges
GAUGE_ADDRESS1 = 122  # Use the number for the correct gauge
# GAUGE_ADDRESS2 = 132  # Use the number for the correct gauge

# Read gauge type
gauge_type1 = pvp.read_gauge_type(serial_port, GAUGE_ADDRESS1)
# gauge_type2 = pvp.read_gauge_type(s, GAUGE_ADDRESS2)
# print(f"Gauge Type: {gauge_type}")


# Create the pump
# pump = rpt.TC110()

# Set up deques
# This is X units long and stores pressure data for the two pressure sources with its corresponding timestamps
pressure_data = deque(maxlen=10)
pressure_read_counter = 0 #Counts how many times the pressure has been read (will be used to autosave pressure data after X amount of reads)

# Set up a deque for the pump (will store rpm and drive current along with their corresponding times)
# pump_data = deque(maxlen=10)
# pump_read_counter = 0

# This is X units long and stores temperature data with its corresponding timestamps
temperature_data = deque(maxlen=10)
temperature_read_counter = 0 #Counts how many times the temperature has been read (will be used to autosave temperature data after X amount of reads)



# Initialize the plot canvas and window
plot_canvas = None
graph_window = None
rpm_plot_canvas = None
rpm_graph_window = None
drvcurrent_plot_canvas = None
drvcurrent_graph_window = None
temperature_plot_canvas = None
temperature_graph_window = None

# File management system (to prevent an infinite number of files from being created)
# Define two destination folders for each quantity (one for the autosaved data and one for the manually saved data)
csv_manual_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/DataLogs/DataSnapshots/Manual"
csv_auto_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/DataLogs/DataSnapshots/Auto"
pressure_auto_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/DataLogs/PressureLogs/AutoPressureLogs"
pressure_manual_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/DataLogs/PressureLogs/ManualPressureLogs"
rpm_auto_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/DataLogs/RpmLogs/AutoRpmLogs"
rpm_manual_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/DataLogs/RpmLogs/ManualRpmLogs"
drvcurrent_auto_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/DataLogs/DrvCurrentLogs/AutoDrvCurrentLogs"
drvcurrent_manual_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/DataLogs/DrvCurrentLogs/ManualDrvCurrentLogs"

# Define age limit for a file to survive (any file older than this age will be deleted)
time_limit = datetime.timedelta(seconds=20)
    

# Tkinter GUI setup
# Create the main/"root" window of the Tkinter GUI application (all the other windows stem from this)
root = tk.Tk()
root.title("Live Pressure Reader")

# Create a frame to organize the labels and buttons in a grid-like fashion
main_frame = tk.Frame(root) # Creates a frame in the root window
main_frame.grid(row=0, column=0, padx=10, pady=10) # Creates a grid in the frame, which will help organize the labels/buttons/widgets

# Setting up the live plot
fig, ax = plt.subplots(figsize=(6, 4)) # Creates the figure and axes
rpm_fig, rpm_ax = plt.subplots(figsize=(6, 4)) # Creates the figure and axes
drvcurrent_fig, drvcurrent_ax = plt.subplots(figsize=(6, 4)) # Creates the figure and axes

# Create a box-like widget that will be used to display the live pressure reading #1
pressure_label1 = tk.Label(
    main_frame, 
    text="Pressure 1: 0.000 millibar", 
    font=("Helvetica", 20), 
    relief="solid",
    borderwidth=10,
    padx=20, # width of the pressure box widget
    pady=40 # height of the pressure box widget
)
pressure_label1.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
# Create a box-like widget that will be used to display the live pressure reading #2
pressure_label2 = tk.Label(
    main_frame, 
    text="Pressure 2: 0.000 millibar", 
    font=("Helvetica", 20), 
    relief="solid",
    borderwidth=10,
    padx=20,
    pady=40
)
pressure_label2.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

# Create a box-like widget that will be used to display the live pump rpm reading
rpm_label = tk.Label(
    main_frame, 
    text="Pump Speed: 0.000 rpm", 
    font=("Helvetica", 20), 
    relief="solid",
    borderwidth=10,
    padx=20, # width of the pressure box widget
    pady=40 # height of the pressure box widget
)
rpm_label.grid(row=0, column=2, padx=20, pady=20, sticky="nsew")
# Create a box-like widget that will be used to display the live pump drive current reading
drv_current_label = tk.Label(
    main_frame, 
    text="Pump Drive Current: 0.000 A", 
    font=("Helvetica", 20), 
    relief="solid",
    borderwidth=10,
    padx=20,
    pady=40
)
drv_current_label.grid(row=0, column=3, padx=20, pady=20, sticky="nsew")

# Create a box-like widget that will be used to display the live temperature reading
temperature_label = tk.Label(
    main_frame, 
    text="Temperature: 0.000 C", 
    font=("Helvetica", 20), 
    relief="solid",
    borderwidth=10,
    padx=20,
    pady=40
)
temperature_label.grid(row=0, column=3, padx=20, pady=20, sticky="nsew")

# Create button widget that directs user to pressure graph of last X seconds
graph_button = tk.Button(
    main_frame,
    text="Show Pressure Graph",
    font=("Helvetica", 16),
    command=lambda: isl.show_graph(root) #calls the show_graph function when clicked
)
graph_button.grid(row=2, column=0, columnspan=2, padx=20, pady=20, sticky="nsew")

# Create button widget that directs user to vacuum rpm graph of last X seconds
rpm_graph_button = tk.Button(
    main_frame,
    text="Show Vacuum RPM Graph",
    font=("Helvetica", 16),
    command=lambda: isl.show_rpm(root) #calls the show_rpm function when clicked
)
rpm_graph_button.grid(row=2, column=2, padx=20, pady=20, sticky="nsew")

# Create button widget that directs user to vacuum drive current graph of last X seconds
drvcurrent_graph_button = tk.Button(
    main_frame,
    text="Show Vacuum Drive Current Graph",
    font=("Helvetica", 16),
    command=lambda: isl.show_drvcurrent(root) #calls the show_graph function when clicked
)
drvcurrent_graph_button.grid(row=2, column=3, padx=20, pady=20, sticky="nsew")

# Create button widget that directs user to temperature graph of last X seconds
temperature_graph_button = tk.Button(
    main_frame,
    text="Show Temperature Graph",
    font=("Helvetica", 16),
    command=lambda: isl.show_temperature(root) #calls the show_graph function when clicked
)
temperature_graph_button.grid(row=2, column=3, padx=20, pady=20, sticky="nsew")

# Open the root window after X ms when the program starts running 
root.after(100, isl.get_pressure_data(serial_port, root, pressure_data, pressure_label1, ax, fig, plot_canvas, pressure_read_counter, csv_manual_destination_folder,
csv_auto_destination_folder,
pressure_auto_destination_folder,
pressure_manual_destination_folder,
rpm_auto_destination_folder,
rpm_manual_destination_folder,
drvcurrent_auto_destination_folder,
drvcurrent_manual_destination_folder
))
# root.after(100, get_pump_data)
root.after(100, isl.get_temperature_data(client, root, modbus_temperature_parameter_address, eurotherm_device_id))
root.mainloop() # keeps the GUI running continuously




