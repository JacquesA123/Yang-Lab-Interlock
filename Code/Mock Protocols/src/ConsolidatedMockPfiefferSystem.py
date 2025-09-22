# Consolidated Mock Pfeiffer System (Refactored)
# -------------------------------------------------
# Every single line in this file is commented so that you can follow the
# control‑flow and logic step‑by‑step.
#
# PURPOSE
# -------
# The original script had **three** nearly‑identical real‑time acquisition
# functions (pressure, pump RPM, and pump drive current) plus three nearly‑
# identical plotting helpers.  Here we fold those redundancies into two
# generic helpers:
#   1. `fetch_and_store(metric_name)`   – polls the hardware, adds noise,
#      stores the result, and updates the GUI label for **any** metric.
#   2. `update_plot(metric_name)`       – redraws the Matplotlib axes that
#      belong to that metric.
#
# By feeding these helpers a small configuration dictionary we avoid copy‑
# pasting logic while still supporting extra metrics (temperature was added
# as an example).
# -------------------------------------------------

# --------------------------- STANDARD LIB IMPORTS ---------------------------
import datetime  # → timestamping acquired data
import os        # → file‑system helpers (unused but kept for parity)
import numpy as np  # → noise generation
import tkinter as tk  # → GUI framework
from collections import deque  # → fixed‑length in‑memory ring‑buffers

# --------------------------- THIRD‑PARTY IMPORTS ---------------------------
import matplotlib.pyplot as plt  # → plotting library
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # → embed plots in Tk

# --------------------------- HARDWARE MOCK IMPORTS -------------------------
# In a real setup, swap these mocks for the real protocol drivers.
from MockPfiefferProtocol import Serial, PPT100  # → mock pressure gauge
import PfiefferVacuumProtocol as pvp             # → gauge read helper
import MockPfeifferTC110 as mpt                  # → mock turbo‑pump
import MockEurothermDriver as Eurotherm          # → mock Eurotherm temp ctrl

# --------------------------- HARDWARE SETUP --------------------------------
mock_gauge = PPT100()  # → instantiate the mock pressure gauge
s = Serial(connected_device=mock_gauge, port="COM1", timeout=1)  # → open a fake COM port
pump = mpt.TC110()  # → instantiate the mock turbo‑pump controller
temp_controller = Eurotherm.Eurotherm("COM1", 1)  # → instantiate the mock Eurotherm

# --------------------------- GUI ROOT WINDOW -------------------------------
root = tk.Tk()  # → create the main Tkinter window
root.title("Live Pfeiffer System Monitor")  # → set the window title

# --------------------------- DATA BUFFERS ----------------------------------
# Each deque is a rolling buffer that keeps the last N points so the plots
# remain readable and memory stays bounded.
BUFFER_LEN = 60  # → how many points to keep (~1 minute at 1 Hz)
pressure_data = deque(maxlen=BUFFER_LEN)      # → ( time, p1, p2 )
pump_data = deque(maxlen=BUFFER_LEN)          # → ( time, rpm, drv )
temp_data = deque(maxlen=BUFFER_LEN)          # → ( time, temp )

# --------------------------- MATPLOTLIB FIGURES ----------------------------
fig_pressure, ax_pressure = plt.subplots(figsize=(6, 4))  # → pressure figure/axes
fig_rpm, ax_rpm = plt.subplots(figsize=(6, 4))            # → rpm figure/axes
fig_drv, ax_drv = plt.subplots(figsize=(6, 4))            # → drive‑current figure/axes
fig_temp, ax_temp = plt.subplots(figsize=(6, 4))          # → temperature figure/axes

# --------------------------- TKINTER LABELS (LIVE VALUES) ------------------
main_frame = tk.Frame(root)        # → container for all widgets
main_frame.grid(row=0, column=0)   # → use grid geometry manager

# Helper to create a nicely‑formatted label and return it.
def _make_value_label(text, col):
    """Return a large bordered label and place it at *column* col."""
    lbl = tk.Label(
        main_frame,
        text=text,
        font=("Helvetica", 18),  # → readable but not gigantic
        relief="solid",          # → border style
        borderwidth=8,            # → border thickness
        padx=20, pady=30)         # → internal padding
    lbl.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")  # → place in grid
    return lbl  # → return for later updating

# Create the individual metric labels.
pressure_label1 = _make_value_label("Pressure 1: 0.000 bar", 0)
pressure_label2 = _make_value_label("Pressure 2: 0.000 bar", 1)
rpm_label        = _make_value_label("Pump RPM: 0.000 rpm", 2)
current_label    = _make_value_label("Drive I: 0.000 A",   3)
temp_label       = _make_value_label("Temp: 0.000 °C",     4)

# --------------------------- GUI PLOT BUTTONS ------------------------------
# Generic helper to spawn a new plot window for *fig* with title *title*.

def _spawn_plot_window(fig, title):
    """Embed *fig* in a new Tk Toplevel window and show it."""
    win = tk.Toplevel(root)           # → child window of the root
    win.title(title)                  # → window caption
    canvas = FigureCanvasTkAgg(fig, master=win)  # → embed figure
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)  # → stretch to fit

# Create buttons to pop up each figure.
btn_pressure = tk.Button(main_frame, text="Show Pressure Graph",
                         command=lambda: _spawn_plot_window(fig_pressure,
                                                            "Pressure vs Time"))
btn_pressure.grid(row=2, column=0, columnspan=2, pady=10, sticky="nsew")

btn_rpm = tk.Button(main_frame, text="Show RPM Graph",
                    command=lambda: _spawn_plot_window(fig_rpm, "RPM vs Time"))
btn_rpm.grid(row=2, column=2, pady=10, sticky="nsew")

btn_drv = tk.Button(main_frame, text="Show Drive Current Graph",
                    command=lambda: _spawn_plot_window(fig_drv,
                                                       "Drive Current vs Time"))
btn_drv.grid(row=2, column=3, pady=10, sticky="nsew")

btn_temp = tk.Button(main_frame, text="Show Temp Graph",
                     command=lambda: _spawn_plot_window(fig_temp,
                                                        "Temperature vs Time"))
btn_temp.grid(row=2, column=4, pady=10, sticky="nsew")

# --------------------------- UTILITY: NOISE GENERATOR ----------------------

def generate_noise():
    """Return a small random number centred at 0 (~±0.05)."""
    return np.random.random() * 0.1 - 0.05  # → uniform noise in [‑0.05, 0.05]

# --------------------------- CONFIGURATION DICT ---------------------------
# All per‑metric specifics live here.  The rest of the code is fully generic.
METRICS = {
    # PRESSURE is a *two‑channel* metric (P1 & P2 share a common timestamp).
    "pressure": {
        "read": lambda: tuple(pvp.read_pressure(s, 1) + generate_noise()
                               for _ in range(2)),  # → return (p1, p2)
        "deque": pressure_data,  # → store both values in a single deque
        "labels": (pressure_label1, pressure_label2),  # → Tk labels to update
        "label_fmt": ("Pressure 1: {:.3f} bar", "Pressure 2: {:.3f} bar"),
        "fig": fig_pressure,  # → Matplotlib figure
        "ax": ax_pressure,   # → axes inside that figure
        "colors": ("blue", "red"),  # → line colours
        "series_labels": ("P1", "P2"),  # → legend entries
        "ylim": (0.75, 1.25),  # → fixed y‑axis limits
        "ylabel": "Pressure (bar)",
        "title": "Pressure vs Time (Last 60 s)",
    },

    # PUMP RPM is a scalar metric.
    "rpm": {
        "read": lambda: pump.get_speed() + generate_noise(),  # → float
        "deque": pump_data,  # → combined deque shared with drive current
        "index": 1,  # → store at column‑1 inside the tuple (time, rpm, drv)
        "label": rpm_label,  # → Tk label to update
        "label_fmt": "Pump RPM: {:.3f} rpm",  # → sprintf‑style format
        "fig": fig_rpm,
        "ax": ax_rpm,
        "color": "blue",
        "series_label": "RPM",
        "ylim": (100.8, 101.2),
        "ylabel": "Speed (rpm)",
        "title": "Pump Speed vs Time (Last 60 s)",
    },

    # DRIVE CURRENT is another scalar metric sharing *pump_data*.
    "drv": {
        "read": lambda: pump.get_current() + generate_noise(),  # → float
        "deque": pump_data,
        "index": 2,  # → store at column‑2 inside the tuple (time, rpm, drv)
        "label": current_label,
        "label_fmt": "Drive I: {:.3f} A",
        "fig": fig_drv,
        "ax": ax_drv,
        "color": "green",
        "series_label": "Drive Current",
        "ylim": (4.9, 5.1),
        "ylabel": "Current (A)",
        "title": "Drive Current vs Time (Last 60 s)",
    },

    # TEMPERATURE – single‑value metric stored in its own deque.
    "temp": {
        "read": lambda: temp_controller.get_pv_loop1() + generate_noise(),
        "deque": temp_data,
        "label": temp_label,
        "label_fmt": "Temp: {:.3f} °C",
        "fig": fig_temp,
        "ax": ax_temp,
        "color": "purple",
        "series_label": "Temp",
        "ylim": (19, 25),
        "ylabel": "Temperature (°C)",
        "title": "Controller Temperature vs Time (Last 60 s)",
    },
}

# --------------------------- GENERIC HELPERS ------------------------------

def fetch_and_store(metric_name):
    """Poll the hardware for *metric_name* and push the result into the buffer."""
    now = datetime.datetime.now().strftime("%H:%M:%S")  # → current HH:MM:SS

    cfg = METRICS[metric_name]  # → shorthand reference to this metric's dict

    if metric_name == "pressure":  # → special‑case two‑channel metric
        p1, p2 = cfg["read"]()   # → execute the read lambda
        cfg["deque"].append((now, p1, p2))  # → store both pressures
        # Update both Tk labels.
        cfg["labels"][0].config(text=cfg["label_fmt"][0].format(p1))
        cfg["labels"][1].config(text=cfg["label_fmt"][1].format(p2))
    elif metric_name in ("rpm", "drv"):  # → shared pump_data structure
        # Read the fresh scalar value.
        val = cfg["read"]()
        # Build a mutable list from the last tuple or create a fresh one.
        if cfg["deque"]:
            last_time, last_rpm, last_drv = cfg["deque"][-1]
            # Determine which column gets the new value (rpm=1, drv=2).
            new_tuple = list((now, last_rpm, last_drv))
        else:
            # Initialise missing fields with NaNs if buffer empty.
            new_tuple = [now, np.nan, np.nan]
        new_tuple[cfg["index"]] = val  # → fill rpm *or* drv slot
        cfg["deque"].append(tuple(new_tuple))  # → write back to buffer
        # Update the corresponding Tk label.
        cfg["label"].config(text=cfg["label_fmt"].format(val))
    else:  # → generic single‑scalar metric (e.g. temperature)
        val = cfg["read"]()  # → poll hardware
        cfg["deque"].append((now, val))  # → store timestamp & value
        cfg["label"].config(text=cfg["label_fmt"].format(val))  # → update GUI

    # After mutating the buffer we immediately refresh its plot.
    update_plot(metric_name)  # → redraw the associated Matplotlib axes


def update_plot(metric_name):
    """Redraw the Matplotlib subplot associated with *metric_name*."""
    cfg = METRICS[metric_name]  # → metric‑specific configuration
    ax = cfg["ax"]             # → Matplotlib Axes to draw on
    ax.clear()                  # → wipe previous content

    if metric_name == "pressure":  # → two‑channel special case
        t  = [row[0] for row in cfg["deque"]]  # → x‑axis (time)
        y1 = [row[1] for row in cfg["deque"]]  # → P1 series
        y2 = [row[2] for row in cfg["deque"]]  # → P2 series
        ax.plot(t, y1, label=cfg["series_labels"][0], color=cfg["colors"][0])
        ax.plot(t, y2, label=cfg["series_labels"][1], color=cfg["colors"][1])
    elif metric_name in ("rpm", "drv"):  # → shared pump_data buffer
        idx = cfg["index"]  # → column index (1 = rpm, 2 = drv)
        t   = [row[0] for row in cfg["deque"]]
        y   = [row[idx] for row in cfg["deque"]]
        ax.plot(t, y, label=cfg["series_label"], color=cfg["color"])
    else:  # → generic scalar (temperature)
        t = [row[0] for row in cfg["deque"]]
        y = [row[1] for row in cfg["deque"]]
        ax.plot(t, y, label=cfg["series_label"], color=cfg["color"])

    # Set common axes properties.
    ax.set_xlabel("Time (HH:MM:SS)")
    ax.set_ylabel(cfg["ylabel"])
    ax.set_title(cfg["title"])
    ax.set_ylim(*cfg["ylim"])
    ax.legend(loc="upper right")

    # Improve readability by showing at most ~6 x‑tick labels.
    if len(t) > 1:
        step = max(1, len(t) // 6)
        ax.set_xticks(t[::step])
        ax.set_xticklabels(t[::step], rotation=45, ha="right")

    cfg["fig"].tight_layout()  # → prevent label clipping

# --------------------------- PERIODIC UPDATE LOOP -------------------------

def _update_all():
    """Poll *every* metric once per second and reschedule itself."""
    for name in METRICS:        # → iterate over all metric keys
        fetch_and_store(name)   # → do a single acquisition cycle
    root.after(1000, _update_all)  # → run again in 1000 ms (1 Hz)

# --------------------------- START EVERYTHING -----------------------------
root.after(100, _update_all)  # → kick‑off the periodic updater after 100 ms
root.mainloop()               # → enter Tk main‑event loop (blocking)
