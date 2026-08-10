# Chushkopek Arduino Firmware

This repository contains the Arduino firmware used in the Chushkopek (for my friend Meto) project.

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

- NUCLEO-L010RB (STM32L010RB)

Baud rates  115200 under Linux. 
Under Windows- ?.



