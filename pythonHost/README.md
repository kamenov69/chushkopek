# pykidev

**pykidev** is a lightweight Python driver and communication layer for Arduino-based laboratory instruments, developed as part of the **SMILE (Scalable Modular Instrumentation for Laboratory Experiments)** project.

It provides:
- A simple serial communication interface (`Pykiba`)
- Automatic discovery and binding of Arduino commands (`PykiDev`)
- Optional network access via ZeroRPC for distributed control

The goal is to bridge fast Arduino prototyping with flexible Python-based experiment control, without the overhead of large frameworks.

---

## Installation

There are two main ways to install and use the project.

---

### 1. Install full project (recommended)

Clone the repository and install it using pip:

```bash
pip install -e .
```

This installs the package in editable mode.

Optional (with Jupyter support):

```bash
pip install -e .[client]
```

---

### 2. Manual installation of dependencies

If you prefer to install dependencies manually:

```bash
pip install pyserial zerorpc fire msgpack pyzmq
```

Optional (for UI and plotting):

```bash
pip install jupyter matplotlib ipywidgets
```

---

## Quick usage

### Direct (centralized mode)

```python
from pykidev import PykiDev

ard = PykiDev('/dev/ttyACM0', baudrate=9600)
print(ard.hello())
```

---

### Distributed mode (ZeroRPC server)

Start server:

```bash
smile --n=0 --baudrate=9600 --bind_port=2020
```

Or:

```bash
python smile.py --n=0 --baudrate=9600 --bind_port=2020
```

---

## Architecture

- **Pykiba** → low-level serial transport and parsing  
- **PykiDev** → dynamic command interface (auto-generated from Arduino)  
- **smile.py** → deployment layer (CLI + ZeroRPC server)

This design allows seamless transition from local scripts to distributed laboratory systems.

---

## Requirements

- Python ≥ 3.8  
- Arduino device running a compatible command interpreter (e.g. CmdArduino)

---

## License 
MIT Copyright (c) 2026 Institute of Solid State Physics, Bulgarian Academy of Sciences

---
## Hardware tested

The firmware has been tested on:

- Arduino Mega 2560 (ATmega2560)
- NUCLEO-L010RB (STM32L010RB)

Both platforms operate reliably at baud rates from 9600 to 115200 under Linux. Under Windows, however, the Arduino Mega 2560 board used in this project was observed to work reliably only at 9600 and approximately 57600 baud, while higher baud rates resulted in corrupted or unstable serial communication for reasons that are not yet fully understood.

---

## Notes

This project is designed for small-scale experimental setups where simplicity, flexibility, and rapid development are more important than heavy infrastructure.
