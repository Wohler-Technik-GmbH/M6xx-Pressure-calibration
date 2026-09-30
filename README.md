![Logo](https://www.woehler.de/shop/static/version1724252505/frontend/Woehler/de/de_DE/images/logo.svg)

# Calibration of M603 with KAL100

Bridges an M603 calibration device to a KAL100 pressure calibrator over serial. It listens for M603 pressure commands and forwards them as setpoints or vent commands to the KAL100. Use a KAL100 with a maximum pressure of 100kPa.

## Setup

```powershell
# Create a virtual python environment
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Install the required Python packages
python -m pip install -r requirements.txt
```

## Usage

Find out the COM ports for your M603 and KAL100 devices in the Device Manager under "Ports (COM & LPT)".

```powershell
# Run the calibration script with the appropriate COM ports for your devices
python .\src\pressure_calibration.py <M603_PORT> <KAL100_PORT>
```

Example:

```powershell
python .\src\pressure_calibration.py COM4 COM7
```

Press `Ctrl+C` to stop.