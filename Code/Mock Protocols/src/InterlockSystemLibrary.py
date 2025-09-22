# Interlock system library

#Import the Pfeiffer gauge protocol
import PfiefferVacuumProtocol as pvp

# other imports
import datetime

# The mock-gauge always returns a reading of 1 bar, so we add some noise to make the value appear realistic
def generate_noise():
    return np.random.random() * 0.1 - 0.05

# Read the pressure every X seconds
def get_pressure_data(s, root, pressure_data, pressure_label1, ax, fig, plot_canvas, pressure_read_counter, csv_manual_destination_folder,
csv_auto_destination_folder,
pressure_auto_destination_folder,
pressure_manual_destination_folder,
rpm_auto_destination_folder,
rpm_manual_destination_folder,
drvcurrent_auto_destination_folder,
drvcurrent_manual_destination_folder
):

    try:
       
        
        """
        :param s: The open serial device attached to the gauge.
        :param 1: The address of the gauge.
        """
        # Read the pressure from address 122 if the gauge is plugged into option 1 (or 132 if plugged into option 2) and print it
        p1 = pvp.read_pressure(s, 122) * 1000
        p2 = pvp.read_pressure(s, 122) * 1000
        print("Pressure: {:.3f} millibar".format(p1))
        
        # Save the current time to a variable
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        # Each entry in pressure_data gets the timestamp and its corresponding two pressures
        pressure_data.append((timestamp, p1, p2))
        # pressure_data.append((timestamp, p1))

        # Configure the two pressure labels to display the pressure
        pressure_label1.config(text=f"Pressure 1: {p1:.3f} millibar")
        # pressure_label2.config(text=f"Pressure 2: {p2:.3f} millibar")
        
        # Update the figure every second
        update_figure(ax, pressure_data, fig, csv_manual_destination_folder,
csv_auto_destination_folder,
pressure_auto_destination_folder,
pressure_manual_destination_folder,
rpm_auto_destination_folder,
rpm_manual_destination_folder,
drvcurrent_auto_destination_folder,
drvcurrent_manual_destination_folder
)
        
        # Canvas in Tkinter is a a rectangular area where you can place widgets, plots, etc.
        if plot_canvas is not None:
            plot_canvas.draw() # Create the plot canvas if it is not there already
        
        # Feature to autosave every X seconds
        pressure_read_counter += 1 # Keep track of how many times the program has called for the pressure
        # if pressure_read_counter % 5 == 0: # Autosave the png and csv data every X seconds
        #     save_graph_data()
            
        # Feature to delete files older than X seconds (applies to both the pressure and pump data)
        delete_old_files()

    except Exception as e: # error message if unable to read the pressure
        print(f"Error reading pressure: {e}")
    
    # Schedule this function to run again after X milliseconds
    root.after(1000, get_pressure_data(s, root, pressure_data, pressure_label1, ax, fig, plot_canvas, pressure_read_counter, csv_manual_destination_folder,
csv_auto_destination_folder,
pressure_auto_destination_folder,
pressure_manual_destination_folder,
rpm_auto_destination_folder,
rpm_manual_destination_folder,
drvcurrent_auto_destination_folder,
drvcurrent_manual_destination_folder
))
    
# Read the vacuum pump rpm and drive current every X seconds
def get_pump_data():
    global pump_read_counter # Make the read_counter variable callable across the whole program

    try:
        # read the pump data
        rpm = pump.get_rpm_speed()
        if rpm is None:
            print("Unable to get speed")
        else:
            print("Pump connected: RPM:", rpm)
        # After creating the pump object

        drv_current = pump.get_current()
        if drv_current is None:
            print("Unable to get drive current")
        else:
            print("Pump connected: Drive Current:", drv_current)
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

# Read the temperature every X seconds
def get_temperature_data(client, root, modbus_temperature_parameter_address, device_id):
    global temperature_read_counter # Make the read_counter variable callable across the whole program
    try:
       
        
        """
        :param s: The open serial device attached to the gauge.
        :param 1: The address of the gauge.
        """
        # Read the temp
        result = client.read_holding_registers(2, device_id) # The first input of this function is the MODBUS address of the parameters you're trying to read
        temperature = result.registers[0]
        
        # Save the current time to a variable
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        # Each entry in temperature_data gets the timestamp and its corresponding two temperatures
        temperature_data.append((timestamp, temperature))
        # temperature_data.append((timestamp, p1))

        # Configure the temperature label to display the temperature
        temperature_label1.config(text=f"temperature 1: {p1:.3f} millibar")
        
        # Update the figure every second
        update_figure()
        
        # Canvas in Tkinter is a a rectangular area where you can place widgets, plots, etc.
        if plot_canvas is not None:
            plot_canvas.draw() # Create the plot canvas if it is not there already
        
        # Feature to autosave every X seconds
        temperature_read_counter += 1 # Keep track of how many times the program has called for the temperature
        # if temperature_read_counter % 5 == 0: # Autosave the png and csv data every X seconds
        #     save_graph_data()
            
        # Feature to delete files older than X seconds (applies to both the temperature and pump data)
        delete_old_files()

    except Exception as e: # error message if unable to read the temperature
        print(f"Error reading temperature: {e}")
    
    # Schedule this function to run again after X milliseconds
    root.after(1000, get_temperature_data(client, root, modbus_temperature_parameter_address, device_id))

# Function to update the plot with new data in real-time
def update_figure(ax, pressure_data, fig, csv_manual_destination_folder,
csv_auto_destination_folder,
pressure_auto_destination_folder,
pressure_manual_destination_folder,
rpm_auto_destination_folder,
rpm_manual_destination_folder,
drvcurrent_auto_destination_folder,
drvcurrent_manual_destination_folder
):
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
    ax.set_ylabel("Pressure (millibar)")
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

    
# Function to update the temperature plot with new data in real-time
def temperature_update_figure():
    temperature_ax.clear() # Completely wipe the plot axes, since the plot needs to reset every second to accommodate new data

    # Extract data from pump_data tuple in order to plot
    timestamps = [item[0] for item in pump_data] # Timestamp is always the first element of the tuple, so this makes a list with all the timestamps
    temperature_vals = [item[1] for item in pump_data]

    # Plot the vacuum temperature vs time
    temperature_ax.plot(timestamps, temperature_vals, label="Temperature", color='blue')
    
    # Label the plot 
    temperature_ax.set_xlabel("Time (s)")
    temperature_ax.set_ylabel("Temperature")
    temperature_ax.set_title("Temperature vs Time (Last 60 seconds)")
    temperature_ax.set_ylim(100.8, 101.2)
    temperature_ax.legend()
    
    # Limit the number of tick marks on x-axis to reduce overcrowding
    if len(timestamps) > 1:
        step = max(1, len(timestamps) // 6)
        temperature_ax.set_xticks(timestamps[::step])
        temperature_ax.set_xticklabels(timestamps[::step], rotation=45, ha="right")
    
    # Ensure the whole figure fits into the window
    temperature_fig.tight_layout()

# Function to save live graph data as png (image) and csv (data values)
def save_graph_data(manual = False):
    
    # Check if data exists
    if not pressure_data:
        print("No data available to save.")
        return
    # if not pump_data:
    #     print("No data available to save.")
    #     return
    
    
    # Choose the destination folder (ManualPressureLogs if function was called through save button being clicked, AutoPressureLogs if function was called through autosave feature)
    csv_destination_folder = csv_manual_destination_folder if manual else csv_auto_destination_folder
    pressure_png_destination_folder = pressure_manual_destination_folder if manual else pressure_auto_destination_folder
    rpm_png_destination_folder = rpm_manual_destination_folder if manual else rpm_auto_destination_folder
    drvcurrent_png_destination_folder = drvcurrent_manual_destination_folder if manual else drvcurrent_auto_destination_folder
    
    # Ensure the destination folder exists (could add for the other folders for better debugging)
    os.makedirs(pressure_png_destination_folder, exist_ok=True)
    
    # Create file names for saving and send them to the destination folder
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") #generates the current time
    data_filename = os.path.join(csv_destination_folder, f"data_snapshot_{timestamp}.csv")
    pressure_plot_filename = os.path.join(pressure_png_destination_folder, f"pressure_data_snapshot_{timestamp}.png")
    rpm_plot_filename = os.path.join(rpm_png_destination_folder, f"rpm_data_snapshot_{timestamp}.png")
    drvcurrent_plot_filename = os.path.join(drvcurrent_png_destination_folder, f"drvcurrent_data_snapshot_{timestamp}.png")
    
    # Save a CSV file with time and pressure data in a table format
    with open(data_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "Pressure 1 (millibar)", "Pressure 2 (millibar)", "Vacuum Speed (rpm)", "Drive Current (A)"])
        for (t, p1, p2), (_, rpm_val, drvcurrent) in zip(pressure_data, pump_data): # zip combines two iterables into an iterable tuple
            writer.writerow([t, p1, p2, rpm_val, drvcurrent])

        
    print(f"Graph data saved as {data_filename}")
    
    # Save a png of the plot (dpi controls quality)
    fig.savefig(pressure_plot_filename, dpi=300)
    rpm_fig.savefig(rpm_plot_filename, dpi=300)
    drvcurrent_fig.savefig(drvcurrent_plot_filename, dpi=300)
    
    

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

# Function to display drive current plot when graph button on root window is clicked
def show_temperature(parent):
    # Makes these variables outside of the function's scope, so the function is not creating new ones but rather using the ones that have already been created
    global temperature_graph_window, temperature_plot_canvas

    # Ensures that a new plot is created when reopening the window
    if temperature_graph_window is not None and not temperature_graph_window.winfo_exists():
        temperature_plot_canvas = None

    # Prevents creation of a duplicate window if the window is already open
    if temperature_graph_window is not None and temperature_graph_window.winfo_exists():
        temperature_graph_window.lift() # brings the window the the front if it is hidden by other windows
        return

    # Initialize the graph window 
    temperature_graph_window = tk.Toplevel(parent) # graph_window is a child window of the root window, since it derives from it
    temperature_graph_window.title("Temperature vs Time (Last 60 seconds)")
    
    # Create a button to save data snapshot
    button_frame = tk.Frame(temperature_graph_window)
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
    temperature_plot_canvas = FigureCanvasTkAgg(temperature_fig, master=temperature_graph_window)
    temperature_plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

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
        (drvcurrent_auto_destination_folder, "Drive Current Autosave")]
    # Iterate through the folders we want to delete from
    for folder_path, label in auto_folders:
        delete_old_files_in_folder(folder_path, label)
