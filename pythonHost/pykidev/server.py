"""Serial device setup and a shared ZeroRPC service."""
import argparse
from pathlib import Path
import shlex
import sys

import gevent
from gevent.lock import Semaphore
import signal
import zerorpc

from . import PykiDev, serial_ports_list
from .config import SETUP_PATH, load_settings, save_connection


def read_setup(path, text=None):
    """Read one command per line; ignore blank lines and # comments."""
    commands = []
    if text is None:
        text = Path(path).read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), 1):
        try:
            words = shlex.split(line, comments=True)
        except ValueError as error:
            raise ValueError(f"{path}:{number}: {error}") from error
        if not words:
            continue
        args = []
        for word in words[1:]:
            try:
                value = int(word)
            except ValueError:
                try:
                    value = float(word)
                except ValueError:
                    value = word
            args.append(value)
        commands.append((number, words[0], args))
    return commands


class DeviceService:
    """Serialize client calls so serial requests and responses cannot interleave."""

    def __init__(self, device):
        self._device = device
        self._lock = Semaphore()
        self._pool = gevent.get_hub().threadpool
        self._server = None
        for name in device.commands_list():
            if (isinstance(name, str) and name.isidentifier()
                    and not name.startswith('_') and not hasattr(self, name)):
                setattr(self, name, self._bind(name))

    def _bind(self, name):
        def call(*args):
            return self.command(name, *args)
        return call

    def command(self, name, *args, timeout=2.5):
        with self._lock:
            return self._pool.apply(
                self._device.command, (name, *args), {"timeout": timeout})

    def commands_list(self):
        return self._device.commands_list()

    def shutdown(self):
        # Give ZeroRPC time to send the acknowledgement before stopping.
        gevent.spawn_later(0.2, self._server.stop)
        return "Server stopping"

    def _close(self):
        with self._lock:
            self._pool.apply(self._device.close)


def serve(port, baudrate, setup, endpoint, config_path=None):
    if config_path is not None:
        commands = read_setup(config_path, load_settings(config_path).commands)
        setup = config_path
    else:
        commands = read_setup(setup) if setup else []
    device = None
    server = None
    service = None
    handlers = []
    try:
        print(f"Opening {port} at {baudrate} baud", flush=True)
        device = PykiDev(port=port, baudrate=baudrate)
        reply = device.command("hello")
        if not isinstance(reply, str) or reply.strip().casefold() not in ('protecta', 'protekta'):
            raise RuntimeError(f"Unexpected hello response: {reply!r}; expected Protecta/Protekta")
        print(f"hello: {reply}", flush=True)
        if config_path is not None:
            save_connection(port, baudrate, endpoint, config_path)
        for number, name, args in commands:
            if name not in device.commands_list():
                raise ValueError(f"{setup}:{number}: unknown device command {name!r}")
        for number, name, args in commands:
            reply = device.command(name, *args)
            if reply is None:
                raise RuntimeError(f"{setup}:{number}: no response to {name}")
            print(f"setup {name} {args}: {reply}", flush=True)
        service = DeviceService(device)
        server = zerorpc.Server(service)
        service._server = server
        server.bind(endpoint)
        def stop_on_signal(signum, frame):
            gevent.spawn(server.stop)

        for sig in (signal.SIGINT, signal.SIGTERM):
            handlers.append((sig, signal.signal(sig, stop_on_signal)))
        print(f"Serving at {endpoint}. Stop with Ctrl+C or 'smile stop'.", flush=True)
        server.run()
    finally:
        for sig, previous in handlers:
            signal.signal(sig, previous)
        if server is not None:
            server.close()
        if service is not None:
            service._close()
        elif device is not None:
            device.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list", help="List serial ports")
    start = sub.add_parser("start", help="Set up a device and serve it until stopped")
    start.add_argument("--port", help="Serial path; if omitted, select interactively")
    start.add_argument("--baudrate", type=int)
    start.add_argument("--setup", help="UTF-8 file with one device command per line")
    start.add_argument("--bind")
    stop = sub.add_parser("stop", help="Stop a running server and close its serial port")
    stop.add_argument("--connect")
    args = parser.parse_args(argv)
    try:
        settings = load_settings()
        if args.action == "list":
            serial_ports_list()
        elif args.action == "stop":
            client = zerorpc.Client(timeout=5)
            try:
                client.connect(args.connect or settings.connect_endpoint)
                print(client.shutdown())
            finally:
                client.close()
        else:
            port = args.port
            if port is None:
                ports = serial_ports_list()
                if not ports:
                    raise RuntimeError("No serial ports found")
                saved = next((i for i, p in enumerate(ports) if p.device == settings.port), None)
                answer = input(f"Select port number{f' [{saved}]' if saved is not None else ''}: ").strip()
                selection = saved if not answer and saved is not None else int(answer)
                if not 0 <= selection < len(ports):
                    raise ValueError("Invalid port number")
                port = ports[selection].device
            serve(port, args.baudrate or settings.baudrate, args.setup,
                  args.bind or settings.endpoint,
                  config_path=None if args.setup else SETUP_PATH)
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
