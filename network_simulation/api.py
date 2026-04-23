import threading
import pandas as pd
from fastapi import FastAPI
import time

from network_simulation.main import run_simulation  # we’ll create this

app = FastAPI()

latest_data = []

# ── Background simulation thread ─────────────────────
def simulation_worker():
    global latest_data
    for df in run_simulation():
        latest_data = df.tail(50).to_dict(orient="records")

# start simulation in background
threading.Thread(target=simulation_worker, daemon=True).start()


# ── API endpoint ─────────────────────────────────────
@app.get("/data")
def get_data():
    return latest_data