	# Project specification: device control GUI with mock mode and variable editor

## 1. Goal

Create a desktop GUI that can:
- discover available serial ports
- list them to the user
- allow the user to select one port and a baud rate
- save the chosen configuration to a file
- open the selected connection successfully
- work in mock mode when no device is physically connected
- query the device for available commands via `hlp`
- generate command buttons dynamically for each command
- open a parameter dialog for commands that take one or more values
- show command results in a log/output area
- read the global variable table via `varlst`
- display each variable with name, current value, min, max, and updated flag
- allow a user to edit values and apply them back to the device
- persist edited values to config and reload them automatically when reconnecting

## 2. Scope

This is a general-purpose control interface useful for instrument control, with a strong emphasis on testing and development without hardware.

## 3. User stories

### 3.1 UART connection
- As a user, I want to see all serial ports on the machine.
- As a user, I want to choose one port and a baud rate.
- As a user, I want the app to remember my connection choices.
- As a user, I want to connect in mock mode when no hardware is attached.

### 3.2 Command panel
- As a user, I want the app to read the command list from the device.
- As a user, I want a button for each command returned by `hlp`.
- As a user, I want to provide parameters in a dialog and run the command.
- As a user, I want to see the response in a result panel.

### 3.3 Global variables
- As a user, I want to read the variable list from `varlst`.
- As a user, I want to see all fields: name, value, min, max, updated flag.
- As a user, I want to edit a variable and send the new value to the device.
- As a user, I want the result of the write operation to be visible.
- As a user, I want my edited values saved to config so they can be restored at the next connection.

## 4. Functional requirements

### 4.1 Port detection
- The application must detect available serial ports using the Python serial library.
- If none are found, the app should still remain usable in mock mode.

### 4.2 Connection configuration
- The app must support:
  - selected serial port
  - baud rate
  - mock mode checkbox
- On save, the app must store a config object.
- The config must support at least:
  - `port`
  - `baudrate`
  - `mock`
  - `globals`

### 4.3 Device abstraction
- The application must use a device abstraction layer that supports both:
  - real serial-backed device
  - mock device
- The interface must provide a unified `.command(name, *args)` API.

### 4.4 `hlp` behavior
- The GUI must call `hlp` on connection.
- It must parse results and generate command buttons.
- Commands such as `hlp` itself must be excluded from button generation if not desired.

### 4.5 Command execution flow
- For each command button, the user can press it and provide parameters.
- Parameter input must be accepted as space- or comma-separated values.
- Numbers must be parsed as int/float when appropriate.
- The command result is appended to a result log window.

### 4.6 Global variable table (`varlst`)
- The app must call `varlst` and parse the returned data.
- The expected response shape is a list of rows with:
  - name
  - value
  - min
  - max
  - updated flag
- The UI must show editable fields for each variable.
- The Apply action must send the new value to the device using the variable name as the command name.

### 4.7 Config persistence
- The application must store configuration in a JSON file located in the project directory.
- The config file should persist:
  - last used serial port
  - last baud rate
  - last mock mode state
  - last user-entered values for global variables
- On connection, the app should reload any saved global values and push them to the device.

### 4.8 Service/configuration bootstrap mode
- The application must support a bootstrap workflow that is dedicated to device configuration and calibration.
- In this mode, the user selects a serial port and baud rate, opens a `PykiDev` object, and uses the command layer to interrogate and configure the device.
- The bootstrap mode must be able to:
  - call `hlp` to enumerate commands
  - call `varlst` to inspect global variables, their values, min/max limits, and updated state
  - present these values in a service-like editor UI
  - allow the user to set and write values to the device
  - save the final configuration to a config file
  - validate the configuration before accepting it as the current runtime state
- The configuration file must be treated as the source of truth for the "standard operational configuration".
- After a valid configuration is loaded and accepted, the temporary service object used for writing and reading must be discarded.
- The final runtime object handed to the ZeroRPC server must be a ready-to-use `PykiDev` instance created from the validated configuration.

### 4.9 Runtime handoff to ZeroRPC
- After the configuration bootstrap completes successfully, the application must create a runtime `PykiDev` instance configured with the validated serial settings.
- That runtime object must be passed to the ZeroRPC server as the backend device interface.
- The GUI/editor used for live configuration must not remain the active data path for runtime execution once the service phase is complete.
- The ZeroRPC layer should expose the same command surface as the configured device and should not depend on the temporary editor object staying in memory.

## 5. Non-functional requirements

- The app should be usable without hardware through mock mode.
- It should not crash if no serial ports are available.
- It should provide visible feedback for connection, execution, and errors.
- It should be easy to extend with additional commands.

## 6. Acceptance criteria

1. The GUI starts successfully in a Python environment with the required dependencies installed.
2. The app lists available serial ports when they exist.
3. The app works in mock mode without hardware.
4. `hlp` results become command buttons.
5. A parameter dialog is opened for command execution.
6. `varlst` results are displayed in a table-like editor.
7. Editing a variable and pressing Apply updates the device/mock state.
8. The config file is created and updated on save.
9. Saved globals are loaded and applied when reconnecting.
10. The user can keep testing the interface for multiple days without changing the code path for hardware absence.

## 7. Recommended implementation notes

- Use Tkinter as the first GUI implementation because it is built into Python and easy to start quickly.
- Keep the device abstraction isolated from the UI so mock mode and hardware mode share the same interface.
- Keep `hlp`, `varlst`, and other dynamic command logic in a thin controller layer.
- Separate the workflow into two phases: configuration/bootstrap and runtime service.
- In the bootstrap phase, use a transient `PykiDev` instance for configuration and validation.
- In the runtime phase, hand off the final device object to ZeroRPC and discard the helper/editor instance.
- Store config in JSON for easier inspection and modification.
- Treat the config file as the persisted operational state for the device, not as a temporary scratchpad.

## 8. Open questions

- Should the config file live in the project root or in a dedicated config folder?
- Should the app include a real ZeroRPC server mode later, or remain serial-only for now?
- Should commands be executed directly in the GUI process or via a background thread when connected to live hardware?

## 9. Development plan

1. Define and finalize the specification.
2. Build serial discovery and config UI.
3. Add mock device and command parser.
4. Implement dynamic command buttons and parameter dialogs.
5. Implement `varlst` variable editor with persistence.
6. Build the configuration bootstrap workflow: validate settings, save config, load config, and hand off a final `PykiDev` to ZeroRPC.
7. Validate the workflow end-to-end with mock mode.
8. Extend to real hardware when available.

## 10. Success definition

The project is successful when the user can:
- run the GUI without hardware
- discover ports and choose a port/baud combination
- save the configuration
- call `hlp`
- open parameter dialogs for commands
- read and edit global variables from `varlst`
- persist values in config and reload them on reconnect
