# This program reads the pressure from a "mock" gauge, the RPM and Drive Current from a "mock" Vacuum Pump, and displays them through a Tkinter GUI
import csv
import os
import datetime
import numpy as np
import tkinter as tk
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # FigureCanvasTkAgg is a class that allows a Matplotlib plot to be embedded in a Tkinker GUI window

#Import the Pfeiffer gauge protocol
from MockPfiefferProtocol import Serial, PPT100
import PfiefferVacuumProtocol as pvp

#Import the mock Pfeiffer TC110 (vacuum pump) protocol
import MockPfeifferTC110 as mpt

#Import the mock Eurotherm driver
import MockEurothermDriver as Eurotherm


#Create the mock gauge (unnecessary for non-mock program)
mock_gauge = PPT100()
s = Serial(connected_device=mock_gauge, port="COM1", timeout=1)

# Create the mock pump (same object can be used for real pump, just have to tweak the functions in the protocol to be non-mock)
pump = mpt.TC110()

# Create the mock Eurotherm controller
#temp_controller = Eurotherm.Eurotherm('COM1', 1)  # port name, slave address

# This is X units long and stores pressure data for the two pressure sources with its corresponding timestamps
pressure_data = deque(maxlen=10)
pressure_read_counter = 0 #Counts how many times the pressure has been read (will be used to autosave pressure data after X amount of reads)

# Set up a deque for the pump (will store rpm and drive current along with their corresponding times)
pump_data = deque(maxlen=10)
pump_read_counter = 0

# Set up a deque for the controller temp (will store controller temp along with its corresponding times)
temp_data = deque(maxlen=10)
temp_read_counter = 0


# Initialize the plot canvas and window
plot_canvas = None
graph_window = None
rpm_plot_canvas = None
rpm_graph_window = None
drvcurrent_plot_canvas = None
drvcurrent_graph_window = None
temp_plot_canvas = None
temp_graph_window = None
'''
## Read temperature (PV) ##
temperature = temp_controller.get_pv_loop1()

## Change temperature setpoint (SP) ##
#NEW_TEMPERATURE = 95.0
#heatercontroller.set_sp_loop1(NEW_TEMPERATURE)
'''
# The mock-gauge always returns a reading of 1 bar, so we add some noise to make the value appear realistic
def generate_noise():
    return np.random.random() * 0.1 - 0.05
# Read the pressure every X seconds
def get_pressure_data():
    global pressure_read_counter # Make the read_counter variable callable across the whole program

    try:
        # read the pressure from the mock gauge address
        p = pvp.read_pressure(s, 1)
        
        
        """
        :param s: The open serial device attached to the gauge.
        :param 1: The address of the gauge.
        """
        # Add noise to the pressure readings
        random_pressure1 = p + generate_noise()
        random_pressure2 = p + generate_noise()
        
        # Save the current time to a variable
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        # Each entry in pressure_data gets the timestamp and its corresponding two pressures
        pressure_data.append((timestamp, random_pressure1, random_pressure2))

        # Configure the two pressure labels to display the pressure
        pressure_label1.config(text=f"Pressure 1: {random_pressure1:.3f} bar")
        pressure_label2.config(text=f"Pressure 2: {random_pressure2:.3f} bar")
        
        # Update the figure every second
        update_figure()
        
        # Canvas in Tkinter is a a rectangular area where you can place widgets, plots, etc.
        if plot_canvas is not None:
            plot_canvas.draw() # Create the plot canvas if it is not there already
        
        # Feature to autosave every X seconds
        pressure_read_counter += 1 # Keep track of how many times the program has called for the pressure
        if pressure_read_counter % 5 == 0: # Autosave the png and csv data every X seconds
            save_graph_data()
            
        # Feature to delete files older than X seconds (applies to both the pressure and pump data)
        delete_old_files()

    except Exception as e: # error message if unable to read the pressure
        print(f"Error reading pressure: {e}")
    
    # Schedule this function to run again after X milliseconds
    root.after(1000, get_pressure_data)
    
# Read the vacuum pump rpm and drive current every X seconds
def get_pump_data():
    global pump_read_counter # Make the read_counter variable callable across the whole program

    try:
        # read the pump data
        rpm = pump.get_speed()
        drv_current = pump.get_current()
        
        # Add noise to the pump readings
        random_rpm = rpm + generate_noise()
        random_drv_current = drv_current + generate_noise()
        print(random_rpm)
        print(random_drv_current)
        
        # Save the current time to a variable
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        # Each entry in pressure_data gets the timestamp and its corresponding two pressures
        pump_data.append((timestamp, random_rpm, random_drv_current))
        
        # Configure the two pressure labels to display the pressure
        rpm_label.config(text=f"Pump Speed: {random_rpm:.3f} rpm")
        drv_current_label.config(text=f"Pump Drive Current: {random_drv_current:.3f} A")
        
        # Update the figure every second
        rpm_update_figure()
        drvcurrent_update_figure()
        
        # Canvas in Tkinter is a a rectangular area where you can place widgets, plots, etc.
        if rpm_plot_canvas is not None:
            rpm_plot_canvas.draw() # Create the plot canvas if it is not there already
        # Canvas in Tkinter is a a rectangular area where you can place widgets, plots, etc.
        if drvcurrent_plot_canvas is not None:
            drvcurrent_plot_canvas.draw() # Create the plot canvas if it is not there already
        
        # Feature to autosave every X seconds is built into get_pressure thru the save_graph_data function
        
        # Feature to delete files is in the get_pressure function
        
    except Exception as e: # error message if unable to read the pressure
        print(f"Error reading pressure: {e}")
    
    # Schedule this function to run again after X milliseconds
    root.after(1000, get_pump_data)

# Read the controller temp every X seconds
def get_temp_data():
    global temp_read_counter # Make the read_counter variable callable across the whole program

    try:
        # read the temp from the mock eurotherm controller
        #temp = temp_controller.get_pv_loop1()
        temp = 500
        
        # Add noise to the pressure readings
        random_temp = temp + 10*generate_noise()
        # Save the current time to a variable
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        # Each entry in temp_data gets the timestamp and its corresponding temp
        temp_data.append((timestamp, random_temp))

        # Configure the two pressure labels to display the pressure
        temp_label.config(text=f"Temp: {random_temp:.3f} Celsius")
        
        # Update the figure every second
        temp_update_figure()
        
        # Canvas in Tkinter is a a rectangular area where you can place widgets, plots, etc.
        if temp_plot_canvas is not None:
            temp_plot_canvas.draw() # Create the plot canvas if it is not there already
        
        # Feature to autosave every X seconds
        
            
        # Feature to delete files older than X seconds (applies to both the pressure and pump data)
        
    except Exception as e: # error message if unable to read the pressure
        print(f"Error reading pressure: {e}")
    
    # Schedule this function to run again after X milliseconds
    root.after(1000, get_temp_data)

# Function to update the plot with new data in real-time
def update_figure():
    ax.clear() # Completely wipe the plot axes, since the plot needs to reset every second to accommodate new data

    # Extract data from pressure_data tuple in order to plot
    timestamps = [item[0] for item in pressure_data] # Timestamp is always the first element of the tuple, so this makes a list with all the timestamps
    pres1_vals = [item[1] for item in pressure_data]
    pres2_vals = [item[2] for item in pressure_data]

    # Plot the two pressures vs time
    ax.plot(timestamps, pres1_vals, label="Pressure 1", color='blue')
    ax.plot(timestamps, pres2_vals, label="Pressure 2", color='red')
    
    # Label the plot 
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Pressure (bar)")
    ax.set_title("Pressure vs Time (Last 60 seconds)")
    ax.set_ylim(0.750, 1.250)
    ax.legend()
    
    # Limit the number of tick marks on x-axis to reduce overcrowding
    if len(timestamps) > 1:
        step = max(1, len(timestamps) // 6)
        ax.set_xticks(timestamps[::step])
        ax.set_xticklabels(timestamps[::step], rotation=45, ha="right")
    
    # Ensure the whole figure fits into the window
    fig.tight_layout()
    
# Function to update the rpm plot with new data in real-time
def rpm_update_figure():
    rpm_ax.clear() # Completely wipe the plot axes, since the plot needs to reset every second to accommodate new data

    # Extract data from pump_data tuple in order to plot
    timestamps = [item[0] for item in pump_data] # Timestamp is always the first element of the tuple, so this makes a list with all the timestamps
    rpm_vals = [item[1] for item in pump_data]

    # Plot the vacuum rpm vs time
    rpm_ax.plot(timestamps, rpm_vals, label="Vacuum speed", color='blue')
    
    # Label the plot 
    rpm_ax.set_xlabel("Time (s)")
    rpm_ax.set_ylabel("Vacuum speed (rpm)")
    rpm_ax.set_title("Vacuum speed vs Time (Last 60 seconds)")
    rpm_ax.set_ylim(100.8, 101.2)
    rpm_ax.legend()
    
    # Limit the number of tick marks on x-axis to reduce overcrowding
    if len(timestamps) > 1:
        step = max(1, len(timestamps) // 6)
        rpm_ax.set_xticks(timestamps[::step])
        rpm_ax.set_xticklabels(timestamps[::step], rotation=45, ha="right")
    
    # Ensure the whole figure fits into the window
    rpm_fig.tight_layout()
    
# Function to update the drive current plot with new data in real-time
def drvcurrent_update_figure():
    drvcurrent_ax.clear() # Completely wipe the plot axes, since the plot needs to reset every second to accommodate new data

    # Extract data from pump_data tuple in order to plot
    timestamps = [item[0] for item in pump_data] # Timestamp is always the first element of the tuple, so this makes a list with all the timestamps
    drvcurrent_vals = [item[2] for item in pump_data]

    # Plot the vacuum rpm vs time
    drvcurrent_ax.plot(timestamps, drvcurrent_vals, label="Vacuum Drive Current", color='blue')
    
    # Label the plot 
    drvcurrent_ax.set_xlabel("Time (s)")
    drvcurrent_ax.set_ylabel("Vacuum Drive Current (A)")
    drvcurrent_ax.set_title("Vacuum Drive Current vs Time (Last 60 seconds)")
    drvcurrent_ax.set_ylim(4.9, 5.1)
    drvcurrent_ax.legend()
    
    # Limit the number of tick marks on x-axis to reduce overcrowding
    if len(timestamps) > 1:
        step = max(1, len(timestamps) // 6)
        drvcurrent_ax.set_xticks(timestamps[::step])
        drvcurrent_ax.set_xticklabels(timestamps[::step], rotation=45, ha="right")
    
    # Ensure the whole figure fits into the window
    drvcurrent_fig.tight_layout()
    
def temp_update_figure():
    temp_ax.clear() # Completely wipe the plot axes, since the plot needs to reset every second to accommodate new data

    # Extract data from pump_data tuple in order to plot
    timestamps = [item[0] for item in temp_data] # Timestamp is always the first element of the tuple, so this makes a list with all the timestamps
    temp_vals = [item[1] for item in temp_data]

    # Plot the vacuum rpm vs time
    temp_ax.plot(timestamps, temp_vals, label="Temperature", color='blue')
    
    # Label the plot 
    temp_ax.set_xlabel("Time (s)")
    temp_ax.set_ylabel("Temperature (°C)")
    temp_ax.set_title("Temperature vs Time (Last 60 seconds)")
    temp_ax.set_ylim(499,501)
    temp_ax.legend()
    
    # Limit the number of tick marks on x-axis to reduce overcrowding
    if len(timestamps) > 1:
        step = max(1, len(timestamps) // 6)
        temp_ax.set_xticks(timestamps[::step])
        temp_ax.set_xticklabels(timestamps[::step], rotation=45, ha="right")
    
    # Ensure the whole figure fits into the window
    temp_fig.tight_layout()

# Function to save live graph data as png (image) and csv (data values)
def save_graph_data(manual = False):
    
    # Check if data exists
    if not pressure_data:
        print("No data available to save.")
        return
    if not pump_data:
        print("No data available to save.")
        return
    if not temp_data:
        print("No data available to save.")
        return
    
    
    # Choose the destination folder (ManualPressureLogs if function was called through save button being clicked, AutoPressureLogs if function was called through autosave feature)
    csv_destination_folder = csv_manual_destination_folder if manual else csv_auto_destination_folder
    pressure_png_destination_folder = pressure_manual_destination_folder if manual else pressure_auto_destination_folder
    rpm_png_destination_folder = rpm_manual_destination_folder if manual else rpm_auto_destination_folder
    drvcurrent_png_destination_folder = drvcurrent_manual_destination_folder if manual else drvcurrent_auto_destination_folder
    temp_png_destination_folder = temp_manual_destination_folder if manual else temp_auto_destination_folder
    
    # Ensure the destination folder exists (could add for the other folders for better debugging)
    os.makedirs(pressure_png_destination_folder, exist_ok=True)
    
    # Create file names for saving and send them to the destination folder
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") #generates the current time
    data_filename = os.path.join(csv_destination_folder, f"data_snapshot_{timestamp}.csv")
    pressure_plot_filename = os.path.join(pressure_png_destination_folder, f"pressure_data_snapshot_{timestamp}.png")
    rpm_plot_filename = os.path.join(rpm_png_destination_folder, f"rpm_data_snapshot_{timestamp}.png")
    drvcurrent_plot_filename = os.path.join(drvcurrent_png_destination_folder, f"drvcurrent_data_snapshot_{timestamp}.png")
    temp_plot_filename = os.path.join(temp_png_destination_folder, f"temp_data_snapshot_{timestamp}.png")
    
    # Save a CSV file with time and pressure data in a table format
    with open(data_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "Pressure 1 (bar)", "Pressure 2 (bar)", "Vacuum Speed (rpm)", "Drive Current (A)", "Temperature (C)"])
        for (t, p1, p2), (_, rpm_val, drvcurrent), (_, temp) in zip(pressure_data, pump_data, temp_data):
            writer.writerow([t, p1, p2, rpm_val, drvcurrent, temp])

    

        
    print(f"Graph data saved as {data_filename}")
    
    # Save a png of the plot (dpi controls quality)
    fig.savefig(pressure_plot_filename, dpi=300)
    rpm_fig.savefig(rpm_plot_filename, dpi=300)
    drvcurrent_fig.savefig(drvcurrent_plot_filename, dpi=300)
    temp_fig.savefig(temp_plot_filename, dpi=300)
    
    

# Function to display plot when graph button on root window is clicked
def show_graph(parent):
    # Makes these variables outside of the function's scope, so the function is not creating new ones but rather using the ones that have already been created
    global graph_window, plot_canvas

    # Ensures that a new plot is created when reopening the window
    if graph_window is not None and not graph_window.winfo_exists():
        plot_canvas = None

    # Prevents creation of a duplicate window if the window is already open
    if graph_window is not None and graph_window.winfo_exists():
        graph_window.lift() # brings the window the the front if it is hidden by other windows
        return

    # Initialize the graph window 
    graph_window = tk.Toplevel(parent) # graph_window is a child window of the root window, since it derives from it
    graph_window.title("Pressure vs Time (Last 60 seconds)")
    
    # Create a button to save data snapshot
    button_frame = tk.Frame(graph_window)
    button_frame.pack(side=tk.TOP, pady=10)
    save_data_button = tk.Button(
        button_frame,
        text="Save Data Snapshot",
        font=("Helvetica", 12),
        command=lambda: save_graph_data(manual=True) # Flags the manual variable as true to ensure the saved file gets sent to the manual folder rather than the autosave folder
    )
    save_data_button.pack()

    # Create label to remind user that graph is auto-saving every X seconds
    auto_save_label = tk.Label(
        button_frame,
        text="Auto-saving data every 5 seconds",
        font=("Helvetica", 10),
        fg="green"
    )
    auto_save_label.pack(pady=5)
    
    # Embeds the live figure into the canvas, making it visible
    plot_canvas = FigureCanvasTkAgg(fig, master=graph_window)
    plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
# Function to display rpm plot when graph button on root window is clicked
def show_rpm(parent):
    # Makes these variables outside of the function's scope, so the function is not creating new ones but rather using the ones that have already been created
    global rpm_graph_window, rpm_plot_canvas

    # Ensures that a new plot is created when reopening the window
    if rpm_graph_window is not None and not rpm_graph_window.winfo_exists():
        rpm_plot_canvas = None

    # Prevents creation of a duplicate window if the window is already open
    if rpm_graph_window is not None and rpm_graph_window.winfo_exists():
        rpm_graph_window.lift() # brings the window the the front if it is hidden by other windows
        return

    # Initialize the graph window 
    rpm_graph_window = tk.Toplevel(parent) # graph_window is a child window of the root window, since it derives from it
    rpm_graph_window.title("Vacuum rpm vs Time (Last 60 seconds)")
    
    # Create a button to save data snapshot
    button_frame = tk.Frame(rpm_graph_window)
    button_frame.pack(side=tk.TOP, pady=10)
    save_data_button = tk.Button(
        button_frame,
        text="Save Data Snapshot",
        font=("Helvetica", 12),
        command=lambda: save_graph_data(manual=True) # Flags the manual variable as true to ensure the saved file gets sent to the manual folder rather than the autosave folder
    )
    save_data_button.pack()

    # Create label to remind user that graph is auto-saving every X seconds
    auto_save_label = tk.Label(
        button_frame,
        text="Auto-saving data every 5 seconds",
        font=("Helvetica", 10),
        fg="green"
    )
    auto_save_label.pack(pady=5)
    
    # Embeds the live figure into the canvas, making it visible
    rpm_plot_canvas = FigureCanvasTkAgg(rpm_fig, master=rpm_graph_window)
    rpm_plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Function to display drive current plot when graph button on root window is clicked
def show_drvcurrent(parent):
    # Makes these variables outside of the function's scope, so the function is not creating new ones but rather using the ones that have already been created
    global drvcurrent_graph_window, drvcurrent_plot_canvas

    # Ensures that a new plot is created when reopening the window
    if drvcurrent_graph_window is not None and not drvcurrent_graph_window.winfo_exists():
        drvcurrent_plot_canvas = None

    # Prevents creation of a duplicate window if the window is already open
    if drvcurrent_graph_window is not None and drvcurrent_graph_window.winfo_exists():
        drvcurrent_graph_window.lift() # brings the window the the front if it is hidden by other windows
        return

    # Initialize the graph window 
    drvcurrent_graph_window = tk.Toplevel(parent) # graph_window is a child window of the root window, since it derives from it
    drvcurrent_graph_window.title("Vacuum rpm vs Time (Last 60 seconds)")
    
    # Create a button to save data snapshot
    button_frame = tk.Frame(drvcurrent_graph_window)
    button_frame.pack(side=tk.TOP, pady=10)
    save_data_button = tk.Button(
        button_frame,
        text="Save Data Snapshot",
        font=("Helvetica", 12),
        command=lambda: save_graph_data(manual=True) # Flags the manual variable as true to ensure the saved file gets sent to the manual folder rather than the autosave folder
    )
    save_data_button.pack()

    # Create label to remind user that graph is auto-saving every X seconds
    auto_save_label = tk.Label(
        button_frame,
        text="Auto-saving data every 5 seconds",
        font=("Helvetica", 10),
        fg="green"
    )
    auto_save_label.pack(pady=5)
    
    # Embeds the live figure into the canvas, making it visible
    drvcurrent_plot_canvas = FigureCanvasTkAgg(drvcurrent_fig, master=drvcurrent_graph_window)
    drvcurrent_plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Function to display temp plot when graph button on root window is clicked
def show_temp(parent):
    # Makes these variables outside of the function's scope, so the function is not creating new ones but rather using the ones that have already been created
    global temp_graph_window, temp_plot_canvas

    # Ensures that a new plot is created when reopening the window
    if temp_graph_window is not None and not temp_graph_window.winfo_exists():
        temp_plot_canvas = None

    # Prevents creation of a duplicate window if the window is already open
    if temp_graph_window is not None and temp_graph_window.winfo_exists():
        temp_graph_window.lift() # brings the window the the front if it is hidden by other windows
        return

    # Initialize the graph window 
    temp_graph_window = tk.Toplevel(parent) # graph_window is a child window of the root window, since it derives from it
    temp_graph_window.title("Temperature vs Time (Last 60 seconds)")
    
    # Create a button to save data snapshot
    button_frame = tk.Frame(temp_graph_window)
    button_frame.pack(side=tk.TOP, pady=10)
    save_data_button = tk.Button(
        button_frame,
        text="Save Data Snapshot",
        font=("Helvetica", 12),
        command=lambda: save_graph_data(manual=True) # Flags the manual variable as true to ensure the saved file gets sent to the manual folder rather than the autosave folder
    )
    save_data_button.pack()

    # Create label to remind user that graph is auto-saving every X seconds
    auto_save_label = tk.Label(
        button_frame,
        text="Auto-saving data every 5 seconds",
        font=("Helvetica", 10),
        fg="green"
    )
    auto_save_label.pack(pady=5)
    
    # Embeds the live figure into the canvas, making it visible
    temp_plot_canvas = FigureCanvasTkAgg(temp_fig, master=temp_graph_window)
    temp_plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Function to ensure old auto-saved files get deleted
def delete_old_files():
    # Function that takes in a folder, iterates through the files, and deletes those that are older than X amount of time
    def delete_old_files_in_folder(folder_path, label):
        # Check if folder exists first
        if not os.path.exists(folder_path):
            print(f"Folder not found: {folder_path}")
            return
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path): # Ensure it is indeed a file
                file_age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(file_path)) # Calculate how old the file is
                if file_age > time_limit:
                    print(f"Deleting from {label}: {file_path} (Age: {file_age})")
                    os.remove(file_path)
    # List of folders to be managed by the autodelete system (only the autosave files, in order to avoid too much data)
    auto_folders = [(csv_auto_destination_folder, "CSV Autosave"),
        (pressure_auto_destination_folder, "Pressure Autosave"),
        (rpm_auto_destination_folder, "RPM Autosave"),
        (drvcurrent_auto_destination_folder, "Drive Current Autosave"), (temp_auto_destination_folder, "Temp Autosave")]
    # Iterate through the folders we want to delete from
    for folder_path, label in auto_folders:
        delete_old_files_in_folder(folder_path, label)

# File management system (to prevent an infinite number of files from being created)
# Define two destination folders for each quantity (one for the autosaved data and one for the manually saved data)
csv_manual_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/Interlock Project/Data/DataLogs/DataSnapshots/Manual"
csv_auto_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/Interlock Project/Data/DataLogs/DataSnapshots/Auto"
pressure_auto_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/Interlock Project/Data/DataLogs/PressureLogs/AutoPressureLogs"
pressure_manual_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/Interlock Project/Data/DataLogs/PressureLogs/ManualPressureLogs"
rpm_auto_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/Interlock Project/Data/DataLogs/RpmLogs/AutoRpmLogs"
rpm_manual_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/Interlock Project/Data/DataLogs/RpmLogs/ManualRpmLogs"
drvcurrent_auto_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/Interlock Project/Data/DataLogs/DrvCurrentLogs/AutoDrvCurrentLogs"
drvcurrent_manual_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/Interlock Project/Data/DataLogs/DrvCurrentLogs/ManualDrvCurrentLogss"
temp_auto_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/Interlock Project/Data/DataLogs/TempLogs/AutoTempLogs"
temp_manual_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/Interlock Project/Data/DataLogs/TempLogs/ManualTempLogs"

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
temp_fig, temp_ax = plt.subplots(figsize=(6, 4)) # Creates the figure and axes

# Create a box-like widget that will be used to display the live pressure reading #1
pressure_label1 = tk.Label(
    main_frame, 
    text="Pressure 1: 0.000 bar", 
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
    text="Pressure 2: 0.000 bar", 
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

# Create a box-like widget that will be used to display the live temp reading
temp_label = tk.Label(
    main_frame, 
    text="Controller Temp: 0.000 C", 
    font=("Helvetica", 20), 
    relief="solid",
    borderwidth=10,
    padx=20,
    pady=40
)
temp_label.grid(row=3, column=0, padx=20, pady=20, sticky="nsew")

# Create button widget that directs user to pressure graph of last X seconds
graph_button = tk.Button(
    main_frame,
    text="Show Pressure Graph",
    font=("Helvetica", 16),
    command=lambda: show_graph(root) #calls the show_graph function when clicked
)
graph_button.grid(row=2, column=0, columnspan=2, padx=20, pady=20, sticky="nsew")

# Create button widget that directs user to vacuum rpm graph of last X seconds
rpm_graph_button = tk.Button(
    main_frame,
    text="Show Vacuum RPM Graph",
    font=("Helvetica", 16),
    command=lambda: show_rpm(root) #calls the show_rpm function when clicked
)
rpm_graph_button.grid(row=2, column=2, padx=20, pady=20, sticky="nsew")

# Create button widget that directs user to vacuum drive current graph of last X seconds
drvcurrent_graph_button = tk.Button(
    main_frame,
    text="Show Vacuum Drive Current Graph",
    font=("Helvetica", 16),
    command=lambda: show_drvcurrent(root) #calls the show_graph function when clicked
)
drvcurrent_graph_button.grid(row=2, column=3, padx=20, pady=20, sticky="nsew")

# Create button widget that directs user to temp graph of last X seconds
temp_graph_button = tk.Button(
    main_frame,
    text="Show Temperature Graph",
    font=("Helvetica", 16),
    command=lambda: show_temp(root) #calls the show_graph function when clicked
)
temp_graph_button.grid(row=4, column=0, padx=20, pady=20, sticky="nsew")

# Open the root window after X ms when the program starts running 
root.after(100, get_pressure_data)
root.after(100, get_pump_data)
root.after(100, get_temp_data)
root.mainloop() # keeps the GUI running continuously




