import serial.tools.list_ports
import serial
import socket
import glob
import time
def serial_ports_list():
    """Lists and returns all available serial ports.

    Returns
    -------
    list
        A list of serial port objects, each containing:
        - device: device path (e.g., '/dev/ttyUSB0')
        - manufacturer: USB manufacturer name
    """
    ports = serial.tools.list_ports.comports()
    #print("\n")
    for i, p in enumerate(ports):
        print(f"{i}.   {p.manufacturer}   {p.device}")
    #print("")
    return ports


def search_by_manufacturer(ports, mnfact):
    """Finds the first serial port matching a specific manufacturer string.

    Parameters
    ----------
    ports : list
        List of serial port objects (from serial_ports_list())
    mnfact : str
        Manufacturer name prefix (case-sensitive)

    Returns
    -------
    str or None
        Device path (e.g., '/dev/ttyACM0') if found, otherwise None.
    """
    ret_val = None
    for p in ports:
        if str(p.manufacturer).startswith(mnfact):
            ret_val = p.device
            break
    return ret_val


def get_my_ip():
    """
    Returns the external (local network) IP address of the machine.

    How it works:
    - Creates a temporary UDP socket.
    - "Connects" it to a public DNS server (Google 8.8.8.8 on port 53).
      No real traffic is sent, this is just to let the OS decide the route.
    - Retrieves the IP address assigned to the chosen interface.
    - Closes the socket and returns the IP.
    """
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Connect to Google DNS (just to determine the route, no packets sent)
        sock.connect(("8.8.8.8", 53))

        # Get the IP address used by this socket
        my_ip = sock.getsockname()[0]

    except Exception as error:
        # In case of error, return the message
        my_ip = f"Unable to determine IP: {error}"

    finally:
        # Always close the socket
        sock.close()
    return my_ip


def print_my_ip():
    """
    Prints the external (local network) IP address of the machine.
    """
    ip = get_my_ip()
    print(ip, end="")
