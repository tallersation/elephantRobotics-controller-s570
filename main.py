# -------------------------------------------------
#  IMPORTS
# -------------------------------------------------
from coppeliasim_zmqremoteapi_client import RemoteAPIClient   # the client
import zmq.error
import tkinter as tk
from tkinter import ttk
import threading
import time
import math

# -------------------------------------------------
#  CONFIGURATION
# -------------------------------------------------
NUM_JOINTS = 14
DEG2RAD   = math.pi / 180.0
SIM_STEP  = 0.03

# -------------------------------------------------
#  CONNECT TO CoppeliaSim
# -------------------------------------------------
try:
    client = RemoteAPIClient()
    sim    = client.require('sim')
except Exception as exc:
    raise RuntimeError(f"Cannot connect to CoppeliaSim: {exc}")

# -------------------------------------------------
#  GET JOINT HANDLES
# -------------------------------------------------
joint_handles = []
for i in range(1, NUM_JOINTS + 1):
    name = f"/base_respondable/joint{i}"
    try:
        h = sim.getObject(name)
    except zmq.error.ZMQError as e:
        raise RuntimeError(f"Joint '{name}' not found in the scene: {e}")
    joint_handles.append(h)

# -------------------------------------------------
#  CALLBACK – slider → joint
# -------------------------------------------------
def slider_to_joint(value, joint_handle, label):
    try:
        rad = float(value) * DEG2RAD
        sim.setJointPosition(joint_handle, rad)
        # update label text
        label.config(text=f"{float(value):.1f}°")
    except zmq.error.ZMQError:
        pass

# -------------------------------------------------
#  BUILD THE TKINTER GUI
# -------------------------------------------------
root = tk.Tk()
root.title("CoppeliaSim – Joint Controller")

sliders = []
for idx, joint in enumerate(joint_handles, start=1):
    frame = ttk.Frame(root)
    frame.pack(pady=4, fill="x")

    ttk.Label(frame, text=f"Joint {idx}", width=10).pack(side="left")

    s = ttk.Scale(frame,
                  from_=-180,
                  to=180,
                  length=400,
                  orient="horizontal")
    s.set(0)
    s.pack(side="left", padx=5)

    angle_label = ttk.Label(frame, text="0.0°", width=8)
    angle_label.pack(side="left")

    # Bind slider to joint + angle label
    s.configure(command=lambda val, j=joint, lbl=angle_label: slider_to_joint(val, j, lbl))

    sliders.append((s, angle_label))

# -------------------------------------------------
#  SIMULATION THREAD
# -------------------------------------------------
def simulation_thread():
    try:
        sim.startSimulation()
        while True:
            sim.step()
            time.sleep(SIM_STEP)
    except zmq.error.ZMQError:
        return

sim_thread = threading.Thread(target=simulation_thread, daemon=True)
sim_thread.start()

# -------------------------------------------------
#  CLEAN SHUTDOWN
# -------------------------------------------------
def on_close():
    try:
        sim.stopSimulation()
    except zmq.error.ZMQError:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# -------------------------------------------------
#  MAIN LOOP
# -------------------------------------------------
root.mainloop()
print("Program terminated cleanly.")
