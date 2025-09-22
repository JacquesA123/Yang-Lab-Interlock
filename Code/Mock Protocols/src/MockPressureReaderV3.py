# This program reads the pressure from a "mock" gauge and displays it through a GUI
import csv
import os
import datetime
import numpy as np
import tkinter as tk
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # FigureCanvasTkAgg is a class that allows a Matplotlib plot to be embedded in a Tkinker GUI window

#Import the Pfeiffer protocol
from MockPfiefferProtocol import Serial, PPT100
import PfiefferVacuumProtocol as pvp

#Create the mock gauge (unnecessary for non-mock program)
mock_gauge = PPT100()
s = Serial(connected_device=mock_gauge, port="COM1", timeout=1)

# This is X units long and stores pressure data for the two pressure sources with its corresponding timestamps
pressure_data = deque(maxlen=10)
read_counter = 0 #Counts how many times the pressure has been read (will be used to autosave pressure data after X amount of reads)

# Setting up the live plot
fig, ax = plt.subplots(figsize=(6, 4)) # Creates the figure and axes
# Initialize the plot canvas and window
plot_canvas = None
graph_window = None

# The mock-gauge always returns a reading of 1 bar, so we add some noise to make the value appear realistic
def generate_noise():
    return np.random.random() * 0.1 - 0.05
# Read the pressure every second
def get_pressure():
    global read_counter # Make the read_counter variable callable across the whole program

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
        read_counter += 1 # Keep track of how many times the program has called for the pressure
        if read_counter % 5 == 0: # Autosave the png and csv data every X seconds
            save_graph_data()
            
        # Feature to delete files older than X seconds
        delete_old_files()

    except Exception as e: # error message if unable to read the pressure
        print(f"Error reading pressure: {e}")
    
    # Schedule this function to run again after X milliseconds
    root.after(1000, get_pressure)

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
    
    # Add whitespace below the plot to prevent x-axis values from being cut off
    plt.subplots_adjust(bottom=0.30)

# Function to save live graph data as png (image) and csv (data values)
def save_graph_data(manual = False):
    if not pressure_data:
        print("No data available to save.")
        return
    
    # Choose the destination folder (ManualPressureLogs if function was called through save button being clicked, AutoPressureLogs if function was called through autosave feature)
    destination_folder = manual_destination_folder if manual else auto_destination_folder
    
    # Ensure the destination folder exists
    os.makedirs(destination_folder, exist_ok=True)
    
    # Create file names for saving and send them to the destination folder
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") #generates the current time
    data_filename = os.path.join(destination_folder, f"pressure_data_snapshot_{timestamp}.csv")
    plot_filename = os.path.join(destination_folder, f"pressure_data_snapshot_{timestamp}.png")
    
    # Save a CSV file with time and pressure data in a table format
    with open(data_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "Pressure 1 (bar)", "Pressure 2 (bar)"])
        for t, p1, p2 in pressure_data:
            writer.writerow([t, p1, p2])
    print(f"Graph data saved as {data_filename}")
    
    # Save a png of the plot (dpi controls quality)
    fig.savefig(plot_filename, dpi=300)
    print(f"Graph image saved as {plot_filename}")

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


# Function to delete data files in the Pressure Logs folder if they are older than X seconds
def delete_old_files():
    # Determine the current time
    current_time = datetime.datetime.now()
    
    # Make sure the folder exists
    if not os.path.exists(auto_destination_folder):
        print(f"Folder not found: {auto_destination_folder}")
        return
    
    # Loop through all the files in the Pressure Logs folder and delete ones that are too old
    for filename in os.listdir(auto_destination_folder):
        file_path = os.path.join(auto_destination_folder, filename)

        if os.path.isfile(file_path): # Only deletes files (skips folders)
            file_modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)) # Gets the last modified time for a file
            file_age = current_time - file_modified_time # Defines the file's age
            
            # Delete file if it is older than the time limit
            if file_age > time_limit:
                print(f"Deleting: {file_path} (Age: {file_age})")
                os.remove(file_path)


# File management system (to prevent an infinite number of files from being created)
# Define two destination folders (one for the autosaved data and one for the manually saved data)
auto_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/AutoPressureLogs"
manual_destination_folder = "/Users/jacques/Documents/UChicago/UChicago Research/Yang Research/ManualPressureLogs"

# Ensure the destination folders exists
os.makedirs(auto_destination_folder, exist_ok=True)
os.makedirs(manual_destination_folder, exist_ok=True)

# Define age limit for a file to survive (any file older than this age will be deleted)
time_limit = datetime.timedelta(seconds=20)
    

# Tkinter GUI setup
# Create the main/"root" window of the Tkinter GUI application (all the other windows stem from this)
root = tk.Tk()
root.title("Live Pressure Reader")

# Create a box-like widget that will be used to display the live pressure reading #1
pressure_label1 = tk.Label(
    root, 
    text="Pressure 1: 0.000 bar", 
    font=("Helvetica", 40), 
    relief="solid",
    borderwidth=10,
    padx=100, # width of the pressure box widget
    pady=50 # height of the pressure box widget
)
pressure_label1.pack(pady=30) # adds padding/space above and below the widget (can make the whole root window bigger)
pressure_label1.pack(padx=10) # adds padding/space to left and right of the widget (can make the whole root window bigger)
# Create a box-like widget that will be used to display the live pressure reading #2
pressure_label2 = tk.Label(
    root, 
    text="Pressure 2: 0.000 bar", 
    font=("Helvetica", 40), 
    relief="solid",
    borderwidth=10,
    padx=100,
    pady=50
)
pressure_label2.pack(pady=30) 
pressure_label1.pack(padx=10)

# Create button widget that directs user to graph of last X seconds
graph_button = tk.Button(
    root,
    text="Show Graph (Last 60 seconds)",
    font=("Helvetica", 16),
    command=lambda: show_graph(root) #calls the show_graph function when clicked
)
graph_button.pack(pady=20)

# Open the root window after X ms when the program starts running 
root.after(100, get_pressure)
root.mainloop() # keeps the GUI running continuously




