import threading
import os
import json
import time
import pandas as pd
from fastapi import FastAPI

from network_simulation.main import run_simulation

app = FastAPI()

# ── Shared state ──────────────────────────────────────────────────────────────
all_data  = []
MAX_ROWS  = 2000          # ~133 ticks × 15 devices
sim_lock  = threading.Lock()

# ── Active thread reference — so we can join() it on reset ───────────────────
_sim_thread: threading.Thread = None
_stop_event = threading.Event()

# ── Sim status ────────────────────────────────────────────────────────────────
_sim_status = {
    "tick": 0,
    "last_anomaly": "none",
    "anomaly_count": 0,
    "device_count": 15,
    "alive": False,
}

# ── Background simulation thread ──────────────────────────────────────────────
def simulation_worker(stop: threading.Event):
    global all_data, _sim_status

    _sim_status["alive"] = True

    for df in run_simulation():
        if stop.is_set():
            break

        rows = df.to_dict(orient="records")

        with sim_lock:
            # Double-check: only append if we haven't been reset mid-tick
            if not stop.is_set():
                all_data.extend(rows)
                if len(all_data) > MAX_ROWS:
                    all_data = all_data[-MAX_ROWS:]

        _sync_status()

    _sim_status["alive"] = False


def _sync_status():
    global _sim_status
    STATUS_FILE = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "network_simulation", "data", "sim_status.json"
    )
    try:
        with open(STATUS_FILE) as f:
            _sim_status = json.load(f)
    except Exception:
        pass


def _start_sim():
    global _stop_event, _sim_thread, all_data

    # 1. Signal the running thread to stop
    _stop_event.set()

    # 2. Immediately wipe data — don't wait for thread to finish first
    #    This ensures /data returns [] right away after reset
    with sim_lock:
        all_data = []

    # 3. Wait for old thread to fully exit (sim loop sleeps 1.2s per tick, so 5s is safe)
    if _sim_thread is not None and _sim_thread.is_alive():
        _sim_thread.join(timeout=5)

    # 4. Fresh stop event + new thread
    _stop_event = threading.Event()
    _sim_thread = threading.Thread(
        target=simulation_worker,
        args=(_stop_event,),
        daemon=True,
        name="sim-worker"
    )
    _sim_thread.start()


# ── Start on boot ─────────────────────────────────────────────────────────────
_start_sim()


# ── API endpoints ─────────────────────────────────────────────────────────────

@app.get("/data")
def get_data():
    with sim_lock:
        return list(all_data)


@app.get("/status")
def get_status():
    return dict(_sim_status)


@app.post("/reset")
def reset_simulation():
    """Hard reset — stops old thread, wipes data, starts fresh sim."""
    _start_sim()
    return {"status": "reset", "message": "Simulation restarted cleanly"}


@app.get("/health")
def health():
    return {"alive": _sim_status.get("alive", False), "rows": len(all_data)}