import threading
import pandas as pd
from fastapi import FastAPI
import time

from network_simulation.main import run_simulation

app = FastAPI()

# Accumulate history across ticks so charts have enough points to draw
all_data = []
MAX_ROWS = 2000          # keep last ~130 ticks × 15 devices
sim_lock = threading.Lock()

# ── Background simulation thread ─────────────────────
def simulation_worker():
    global all_data
    for df in run_simulation():
        rows = df.to_dict(orient="records")
        with sim_lock:
            all_data.extend(rows)
            # trim to keep memory bounded
            if len(all_data) > MAX_ROWS:
                all_data = all_data[-MAX_ROWS:]

def start_sim():
    t = threading.Thread(target=simulation_worker, daemon=True)
    t.start()

# start on boot
start_sim()

# ── API endpoints ─────────────────────────────────────
@app.get("/data")
def get_data():
    with sim_lock:
        return list(all_data)

@app.post("/reset")
def reset_simulation():
    """Clear history and restart simulation — called by dashboard on fresh page load."""
    global all_data
    with sim_lock:
        all_data = []
    start_sim()
    return {"status": "reset", "message": "Simulation restarted"}
