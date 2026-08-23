import threading
import asyncio
from bleak import BleakClient
import tkinter as tk
from tkinter import messagebox


ADDRESS = "36C15B6F-97F1-9721-8199-23C3E062CEE4"
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

client = None
loop = asyncio.new_event_loop()

# Keeps track of whether autonomous mode has been paused
autonomous_paused = False

# Button colours
DEFAULT_BUTTON_COLOUR = "#D3D3D3"
PRESSED_BUTTON_COLOUR = "green"


# ============================================================
# BLE CORE
# ============================================================

# Called automatically if the HM-10 disconnects
def disconnected_callback(_client):
    print("Bluetooth disconnected")

    # GUI changes must be made by Tkinter's main thread
    root.after(0, handle_disconnect)


# Connect to HM-10
async def connect():
    global client

    try:
        client = BleakClient(
            ADDRESS,
            disconnected_callback=disconnected_callback
        )

        await client.connect()

        if client.is_connected:
            print("Connected")

            # Tell Tkinter thread to update GUI
            root.after(0, connection_success)

        else:
            root.after(0, connection_failed)

    except Exception as e:
        print(f"Bluetooth connection failed: {e}")

        root.after(
            0,
            lambda error=str(e): connection_error(error)
        )


# Called when the user presses CONNECT
def start_connection():

    # Show that a connection attempt is in progress
    status_label.config(
        text="CONNECTING...",
        bg="orange",
        fg="black"
    )

    # Prevent user pressing CONNECT repeatedly
    connect_btn.config(
        state="disabled",
        text="CONNECTING..."
    )

    # Start BLE connection on background thread
    asyncio.run_coroutine_threadsafe(
        connect(),
        loop
    )


# Send a command to the robot
async def send(cmd):
    global client

    if client and client.is_connected:
        try:
            print(f"Sending: {cmd}")

            await client.write_gatt_char(
                CHAR_UUID,
                cmd.encode(),
                response=True
            )

        except Exception as e:
            print(f"BLE write failed: {e}")

            # Safely update GUI
            root.after(0, handle_disconnect)

    else:
        print(f"Cannot send '{cmd}' - Bluetooth not connected")


# Run Bluetooth asyncio in its own background thread
def ble_thread():
    asyncio.set_event_loop(loop)
    loop.run_forever()


# Allows Tkinter buttons to send BLE commands
def send_cmd(cmd):
    asyncio.run_coroutine_threadsafe(
        send(cmd),
        loop
    )


# ============================================================
# UI
# ============================================================

root = tk.Tk()
root.title("Robot Controller")

# Larger desktop-sized window
root.geometry("600x700")
root.configure(bg="white")

# Makes the three control columns use the available space evenly
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)

# Stores movement buttons so they can be enabled/disabled
buttons = []


# ============================================================
# CONNECTION GUI FUNCTIONS
# ============================================================

def connection_success():
    global autonomous_paused

    # Hide Connect button now connection has succeeded
    connect_btn.grid_remove()

    # Reset button for next time it is needed
    connect_btn.config(
        state="normal",
        text="CONNECT"
    )

    status_label.config(
        text="CONNECTED",
        bg="green",
        fg="white"
    )

    # Reset pause state when connecting
    autonomous_paused = False
    stop_btn.config(text="STOP")

    # Make sure Arduino and app agree on the current mode
    if mode_var.get() == "AUTONOMOUS":
        send_cmd("A")

    elif mode_var.get() == "ASSISTED":
        send_cmd("P")

    elif mode_var.get() == "MANUAL":
        send_cmd("M")

    messagebox.showinfo(
        "Bluetooth",
        "✅ Successfully Connected"
    )


def connection_failed():

    status_label.config(
        text="FAILED TO CONNECT",
        bg="red",
        fg="white"
    )

    # Allow user to try connecting again
    connect_btn.config(
        state="normal",
        text="CONNECT"
    )


def connection_error(error_message):

    status_label.config(
        text="NOT CONNECTED",
        bg="red",
        fg="white"
    )

    # Allow user to try connecting again
    connect_btn.config(
        state="normal",
        text="CONNECT"
    )

    messagebox.showerror(
        "Bluetooth",
        f"❌ Error: {error_message}"
    )


def handle_disconnect():
    global client
    global autonomous_paused

    client = None

    # Reset autonomous pause state
    autonomous_paused = False
    stop_btn.config(text="STOP")

    # Update connection status
    status_label.config(
        text="NOT CONNECTED",
        bg="red",
        fg="white"
    )

    # Reset movement button colours
    for b in buttons:
        b.config(bg=DEFAULT_BUTTON_COLOUR)

    # Reset and show Connect button again
    connect_btn.config(
        state="normal",
        text="CONNECT"
    )

    connect_btn.grid()


# ============================================================
# CONTROL BUTTON FUNCTIONS
# ============================================================

# Called when a movement button is pressed
def movement_pressed(btn, cmd):

    # Change button colour so the user can see it is active
    btn.config(
        bg=PRESSED_BUTTON_COLOUR,
        fg="white"
    )

    # Send movement command
    send_cmd(cmd)


# Called when a movement button is released
def movement_released(btn, stop_cmd):

    # Return button to its normal colour
    btn.config(
        bg=DEFAULT_BUTTON_COLOUR,
        fg="black"
    )

    # Stop the motors
    send_cmd(stop_cmd)


# Creates movement buttons that move while held down
def make_hold_btn(text, cmd, stop_cmd, row, col):

    btn = tk.Button(
        root,
        text=text,
        width=9,
        height=3,
        font=("Arial", 24, "bold"),
        bg=DEFAULT_BUTTON_COLOUR,
        fg="black",
        relief="flat",
        borderwidth=0
    )

    btn.grid(
        row=row,
        column=col,
        padx=18,
        pady=20
    )

    # When pressed:
    # - change colour
    # - send movement command
    btn.bind(
        "<ButtonPress-1>",
        lambda e: movement_pressed(btn, cmd)
    )

    # When released:
    # - return to normal colour
    # - send stop command
    btn.bind(
        "<ButtonRelease-1>",
        lambda e: movement_released(btn, stop_cmd)
    )

    buttons.append(btn)


# Controls STOP / RESUME button
def stop_resume():
    global autonomous_paused

    # Autonomous mode
    if mode_var.get() == "AUTONOMOUS":

        # Robot is currently running autonomously
        if not autonomous_paused:

            # Stop the robot
            send_cmd("S")

            autonomous_paused = True

            # Change button to RESUME
            stop_btn.config(
                text="RESUME"
            )

        # Robot is currently paused
        else:

            # Send A to restart autonomous mode
            send_cmd("A")

            autonomous_paused = False

            # Change button back to STOP
            stop_btn.config(
                text="STOP"
            )

    # Manual or Assisted mode
    else:

        # STOP simply stops the motors
        send_cmd("S")


# ============================================================
# TOP STATUS ROW
# ============================================================

top_frame = tk.Frame(
    root,
    bg="white"
)

top_frame.grid(
    row=0,
    column=0,
    columnspan=3,
    pady=30
)


status_label = tk.Label(
    top_frame,
    text="NOT CONNECTED",
    width=17,
    font=("Arial", 14, "bold"),
    bg="grey",
    fg="white"
)

status_label.grid(
    row=0,
    column=0,
    padx=15,
    pady=8
)


connect_btn = tk.Button(
    top_frame,
    text="CONNECT",
    command=start_connection,
    width=15,
    height=2,
    font=("Arial", 14, "bold"),
    bg=DEFAULT_BUTTON_COLOUR,
    fg="black",
    relief="flat"
)

connect_btn.grid(
    row=0,
    column=1,
    padx=15,
    pady=8
)


# ============================================================
# MODE ROW
# ============================================================

mode_label = tk.Label(
    top_frame,
    text="MODE:",
    width=17,
    font=("Arial", 15, "bold"),
    fg="black",
    bg="white"
)

mode_label.grid(
    row=1,
    column=0,
    padx=10,
    pady=15
)


# App starts in MANUAL mode
mode_var = tk.StringVar(
    value="MANUAL"
)


# Enable/disable movement buttons depending on mode
def set_control_mode(mode):

    if mode == "AUTONOMOUS":

        # Disable direction buttons
        for b in buttons:
            b.config(
                state="disabled",
                bg=DEFAULT_BUTTON_COLOUR,
                fg="black"
            )

        # STOP / RESUME remains available
        stop_btn.config(state="normal")

    elif mode == "MANUAL" or mode == "ASSISTED":

        # Manual and Assisted both use the direction controls
        for b in buttons:
            b.config(
                state="normal",
                bg=DEFAULT_BUTTON_COLOUR,
                fg="black"
            )

        stop_btn.config(state="normal")


# Called when mode dropdown changes
def set_mode(value):
    global autonomous_paused

    mode_var.set(value)

    # Reset STOP / RESUME whenever mode changes
    autonomous_paused = False
    stop_btn.config(text="STOP")

    if value == "AUTONOMOUS":

        send_cmd("A")
        set_control_mode("AUTONOMOUS")

    elif value == "ASSISTED":

        send_cmd("P")
        set_control_mode("ASSISTED")

    elif value == "MANUAL":

        send_cmd("M")
        set_control_mode("MANUAL")


mode_menu = tk.OptionMenu(
    top_frame,
    mode_var,
    "MANUAL",
    "ASSISTED",
    "AUTONOMOUS",
    command=set_mode
)

mode_menu.config(
    width=17,
    font=("Arial", 14, "bold")
)

mode_menu.grid(
    row=1,
    column=1,
    padx=10,
    pady=15
)


# ============================================================
# MOVEMENT CONTROLS
# ============================================================

# Forward
make_hold_btn(
    "⬆",
    "F",
    "S",
    2,
    1
)

# Left
make_hold_btn(
    "⬅",
    "L",
    "S",
    3,
    0
)


# STOP / RESUME
stop_btn = tk.Button(
    root,
    text="STOP",
    width=9,
    height=3,
    font=("Arial", 24, "bold"),
    bg=DEFAULT_BUTTON_COLOUR,
    fg="black",
    relief="flat",
    borderwidth=0,
    command=stop_resume
)

stop_btn.grid(
    row=3,
    column=1,
    padx=18,
    pady=20
)


# Right
make_hold_btn(
    "➡",
    "R",
    "S",
    3,
    2
)

# Backwards
make_hold_btn(
    "⬇",
    "B",
    "S",
    4,
    1
)


# App starts in manual mode
set_control_mode("MANUAL")


# ============================================================
# START PROGRAM
# ============================================================

threading.Thread(
    target=ble_thread,
    daemon=True
).start()

root.mainloop()