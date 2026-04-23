<div align="center">

<br>

# 🛡️ INS System — Intelligent Network Surveillance

### _Real-Time Network Simulation + AI Anomaly Detection_

<br>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)]()
[![ML](https://img.shields.io/badge/ML-Anomaly_Detection-orange?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)]()

---

<h3>A real-time network monitoring system that simulates devices, injects anomalies, and detects threats using machine learning.</h3>

</div>

---

## Overview

The **INS System** is a real-time network simulation and anomaly detection platform designed to:

- Simulate IoT/network environments  
- Inject realistic cyber anomalies  
- Detect threats using ML models  
- Visualize network topology live  

---

## Key Features

### Intelligent Simulation
- Stateful device behavior (traffic + signal memory)
- Time-based patterns (day/night activity)
- Device-specific profiles (camera, sensor, phone)

### Anomaly Injection (7 Types)
- Traffic Spike (DDoS-like)
- MAC Spoofing
- Rogue Device Injection
- AP Failure
- Device Offline
- Link Flapping
- Multi-device DDoS Attack

### ML-Based Detection
- Isolation Forest model
- Z-score baseline learning
- Severity + confidence scoring
- Real-time anomaly classification

### Live Topology Visualization
- Interactive network graph
- Real-time packet animation
- Color-coded anomalies
- Device status tracking

---

## System Architecture

Simulation Engine → Telemetry → FastAPI (/data) → ML Detection → Streamlit Dashboard

---

## Project Structure

H2H-OopsOps-INS_System/
│
├── network_simulation/
│   ├── simulation/
│   │   ├── devices.py
│   │   ├── topology.py
│   │   ├── telemetry.py
│   │   ├── anomalies.py
│   │   └── discovery.py
│   │
│   ├── main.py
│   ├── api.py
│   └── data/
│       ├── network_data.csv
│       ├── topology.json
│       └── sim_status.json
│
├── ml_model/
│   └── model.py
│
├── dashboard/
│   └── app.py
│
├── requirements.txt
└── README.md

---

## How It Works

1. Simulation generates devices and traffic  
2. Anomalies are injected dynamically  
3. ML model detects abnormal behavior  
4. Dashboard displays results in real-time  

---

## Quick Start

### Install

git clone https://github.com/avi2004-cpu/H2H-OopsOps-INS_System.git  
cd H2H-OopsOps-INS_System  
pip install -r requirements.txt  

### Run Simulation

python -m network_simulation.main  

### Run Dashboard

streamlit run dashboard/app.py  

---

## Deployment

### Backend (Render)

uvicorn network_simulation.api:app --host 0.0.0.0 --port 10000  

### Dashboard (Streamlit Cloud)

App path: dashboard/app.py  

---

## Output

- Live traffic updates  
- Device failures  
- Rogue devices  
- Real-time anomaly alerts  

---

## Highlights

✔ Real-time simulation  
✔ Stateful behavior  
✔ Multiple anomaly types  
✔ ML-based detection  
✔ Interactive topology  

---

## Roadmap

- [x] Simulation engine  
- [x] Anomaly injection  
- [x] ML detection  
- [x] Dashboard  

Future:
- [ ] UI-based attack trigger  
- [ ] Alert system  
- [ ] Historical analytics  

---

## Contributing

Pull requests are welcome.

---

## License

MIT License  

---

<div align="center">

Built with Python, FastAPI, Streamlit & Machine Learning

</div>