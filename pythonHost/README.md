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

ard = PykiDev('/dev/ttyACM0', baudrate=115200)
print(ard.hello())
```

---

### Distributed mode (ZeroRPC server)

### Desktop GUI (Linux and Windows)

Run `python launch_gui.py` from the project folder, or
`python -m pykidev.gui`. Use the Python environment containing the dependencies.
On this Linux machine:

```bash
/home/kamen/anaconda3/envs/myenv/bin/python launch_gui.py
```

On Windows, activate your Python/Conda environment and run:

```powershell
python -m pip install -e .
python launch_gui.py
```

Tkinter must be available in that environment (included in standard Windows
Python installations; Conda provides the `tk` package). After installation,
`smile-gui` also opens the window.

Choose a serial port (`/dev/ttyACM0` on Linux, e.g. `COM3` on Windows), baud
rate, bind address/port. Click **Стартирай** to connect,
check `hello`, run commands from `setup.ini`, and serve. **Спри** requests a graceful shutdown via
ZeroRPC on both platforms. Closing the window also stops its server; during
startup it waits for initialization to finish first. The log displays errors
and device responses. The window stays responsive while the server runs in a
separate process.

The **Команди** tab sends commands through ZeroRPC and displays their responses
and errors in a history pane. Enter `hello`, `sp1 150`, or `a 2 3.5`, then
press Enter or **Изпрати**. The client calls `client.command(name, *arguments)`;
arguments must be numbers and are converted to integers/floats. Sending clears
the input field. Use Up/Down to recall sent commands; Down past the newest
command restores the draft you were typing. History lasts for the current window.
The server address is filled in when you start the local server and can also be
set manually to use another server. Waiting for a response does not block the GUI.

### Terminal

The application automatically reads `setup.ini` beside `launch_gui.py`,
independently of the terminal's current directory. If missing, it uses defaults
and creates the file after a verified `hello` response (`Protecta` or `Protekta`,
case insensitive). The first line stores the last verified serial port.

```ini
port=/dev/ttyACM0
[server]
host=127.0.0.1
tcp_port=2020
baudrate=115200

[commands]
# One device command per line; uncomment as needed.
# pidm 0
# sp1 150
# pidm 1
```

On Windows the first line can be `port=COM3`. GUI preselects the saved port
only if present; otherwise select one. You can change the port, baud rate,
and server address before starting. If opening or verification fails, the GUI
asks you to select a port again and retains the last verified configuration.
Connection settings are saved only after a valid `hello`; initialization commands
are preserved. Changes to commands are read on every server start.

List ports and start from a terminal:

```bash
python -m pykidev.server list
python -m pykidev.server start
```

The terminal offers the saved port as the default in its selection prompt.
`--port`, `--baudrate`, and `--bind` override saved values. The legacy `--setup`
option accepts a separate command file without updating `setup.ini`.
Commands in `[commands]` are sent in order. Unknown commands or missing responses
abort startup and close the port. Firmware error messages are printed as responses.
The serial protocol transmits float arguments with three decimal places.

The server runs in the foreground and owns the open serial connection. Multiple
clients share it; requests are serialized to keep responses matched to commands.
Stop with Ctrl+C, SIGTERM, or from another terminal:

```bash
python -m pykidev.server stop
```

The default endpoint is `tcp://127.0.0.1:2020`. For a trusted local network, start
with `--bind tcp://0.0.0.0:2020` and stop with
`--connect tcp://SERVER_IP:2020`. ZeroRPC has no authentication here; clients
with access to the endpoint can control the device and stop the server.

```python
import zerorpc

client = zerorpc.Client(timeout=10)
client.connect("tcp://127.0.0.1:2020")
print(client.hello())
print(client.commands_list())
client.close()
```

After installing the package, `smile` is an alias for `python -m pykidev.server`.

---

## Architecture

- **Pykiba** → low-level serial transport and parsing  
- **PykiDev** → dynamic command interface (auto-generated from Arduino)  
- **pykidev/server.py** → deployment layer (CLI + ZeroRPC server)

This design allows seamless transition from local scripts to distributed laboratory systems.

---

## Requirements

- Python ≥ 3.8  
- Arduino device running a compatible command interpreter (e.g. CmdArduino)


---
## Hardware tested

The firmware has been tested on:

- NUCLEO-L010RB (STM32L010RB)

Both platforms operate reliably at baud rates from 9600 to

---
## Notes

This project is designed for small-scale experimental setups where simplicity, flexibility, and rapid development are more important than heavy infrastructure.
