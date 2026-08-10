# SMILE Arduino Firmware

This repository contains the Arduino firmware used in the SMILE (Scalable Modular Instrumentation for Laboratory Experiments) project.

The firmware implements a lightweight command-based interface that allows external control from a Python host (via serial or ZeroRPC). It is designed for rapid prototyping of laboratory instruments using low-cost microcontrollers.

---

## Overview

The firmware provides:

- A simple command interpreter (based on CmdArduino)
- Access to device parameters via serial communication
- Real-time parameter updates
- Easy integration with Python drivers (pykidev)

---

## Build system

The project is built using [PlatformIO.](https://platformio.org/)

---

## Installation
### Install PlatformIO

[IDE installation how to](https://platformio.org/platformio-ide)

[CLI installation how to](https://docs.platformio.org/en/latest/core/installation/index.html) 

[PlatformIO drivers](https://docs.platformio.org/en/latest/core/installation/udev-rules.html)



### Build

cd firmware 

pio run

### Upload

pio run --target upload

---

## Hardware tested

The firmware has been tested on:

- Arduino Mega 2560 (ATmega2560)
- NUCLEO-L010RB (STM32L010RB)

Both platforms operate reliably at baud rates from 9600 to 115200 under Linux. Under Windows, however, the Arduino Mega 2560 board used in this project was observed to work reliably only at 9600 and approximately 57600 baud, while higher baud rates resulted in corrupted or unstable serial communication for reasons that are not yet fully understood.

---

## License 
MIT Copyright (c) 2026 Institute of Solid State Physics, Bulgarian Academy of Sciences

