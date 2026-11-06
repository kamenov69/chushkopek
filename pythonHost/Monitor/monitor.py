"""Tkinter monitor for the Chushkopek ZeroRPC service.

Run with the Python environment that contains zerorpc:
    python monitor.py
"""

from __future__ import annotations

from collections import deque
from configparser import ConfigParser
import queue
from pathlib import Path
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk


DEFAULT_ENDPOINT = "tcp://127.0.0.1:2020"
APPLICATION_DIR = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
CONFIG_PATH = APPLICATION_DIR / "monitor.ini"
POLL_SECONDS = 1.0
DEFAULT_TEMPERATURE_HISTORY_POINTS = 128
DEFAULT_BUFFER_POINTS = 64


class RpcWorker(threading.Thread):
    """Own the ZeroRPC client and keep all network calls off the Tk thread."""

    def __init__(self, endpoint, events, commands, expected_hello=None):
        super().__init__(daemon=True)
        self.endpoint = endpoint
        self.events = events
        self.commands = commands
        self.expected_hello = expected_hello
        self.stop_requested = threading.Event()

    def run(self):
        try:
            import zerorpc

            client = zerorpc.Client(timeout=3)
            try:
                client.connect(self.endpoint)
                hello = str(client.command("hello")).strip()
                if self.expected_hello is not None and hello != self.expected_hello:
                    raise RuntimeError(
                        f"Wrong Chushkopek: hello returned {hello!r}, "
                        f"expected {self.expected_hello!r}"
                    )
                self.events.put(("connected", hello))
                next_poll = 0.0
                previous_mode = None

                while not self.stop_requested.is_set():
                    while True:
                        try:
                            name, value = self.commands.get_nowait()
                        except queue.Empty:
                            break
                        try:
                            result = client.command(name, value)
                            self.events.put(("command_ok", (name, result)))
                        except Exception as error:
                            self.events.put(("error", f"{name}: {error}"))

                    now = time.monotonic()
                    if now >= next_poll:
                        values = {
                            "t0": float(client.command("t0")),
                            "t1": float(client.command("t1")),
                            "sp0": float(client.command("sp0")),
                            "sp1": float(client.command("sp1")),
                            "pwm0": float(client.command("pwm0")),
                            "pwm1": float(client.command("pwm1")),
                            "mode": int(client.command("mode")),
                            "pidm": int(client.command("pidm")),
                        }
                        if previous_mode not in (None, 0) and values["mode"] == 0:
                            try:
                                measurement = {
                                    "buf0": list(client.command("buf0")),
                                    "buf1": list(client.command("buf1")),
                                    "sum0": float(client.command("sum0")),
                                    "sum1": float(client.command("sum1")),
                                }
                                self.events.put(("measurement", measurement))
                            except Exception as error:
                                self.events.put(("error", f"Measurement data: {error}"))
                        previous_mode = values["mode"]
                        self.events.put(("data", values))
                        next_poll = now + POLL_SECONDS
                    time.sleep(0.05)
            finally:
                client.close()
        except Exception as error:
            self.events.put(("connection_error", str(error)))
        finally:
            self.events.put(("disconnected", None))

    def stop(self):
        self.stop_requested.set()


class TemperatureMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Chushkopek - Temperature Monitor")
        self.root.geometry("1080x720")
        self.root.minsize(800, 560)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.events = queue.Queue()
        self.commands = queue.Queue()
        self.worker = None
        self.temperature_history_points, self.buffer_points = self.load_display_settings()
        self.history = deque(maxlen=self.temperature_history_points)
        self.started_at = time.monotonic()
        self.last_values = None

        self.host, self.port = self.load_connection_settings()
        self.expected_hello = self.load_expected_hello()
        self.host_var = tk.StringVar(value=self.host)
        self.port_var = tk.StringVar(value=str(self.port))
        self.status = tk.StringVar(value="Not connected")
        self.mode_text = tk.StringVar(value="MODE: —")
        self.pidm_text = tk.StringVar(value="PID MODE: —")
        self.mode_color = "#777777"
        self.current = [tk.StringVar(value="— °C"), tk.StringVar(value="— °C")]
        self.setpoint = [tk.StringVar(value="—"), tk.StringVar(value="—")]
        self.pwm = [tk.StringVar(value="—"), tk.StringVar(value="—")]
        self.pwm_legend = [tk.StringVar(value="PWM0: — → T0 / SP0"),
                           tk.StringVar(value="PWM1: — → T1 / SP1")]
        self.sum_text = tk.StringVar(value="No completed measurement")
        self.measurement = None

        self.build_ui()
        self.root.after(100, self.poll_events)
        self.root.after(300, self.connect)

    @staticmethod
    def load_connection_settings():
        config = ConfigParser()
        try:
            config.read(CONFIG_PATH, encoding="utf-8")
            host = config.get("connection", "host", fallback="127.0.0.1")
            port = config.getint("connection", "port", fallback=2020)
            if not host or not 1 <= port <= 65535:
                raise ValueError
            return host, port
        except (OSError, ValueError):
            return "127.0.0.1", 2020

    @staticmethod
    def load_expected_hello():
        config = ConfigParser()
        try:
            config.read(CONFIG_PATH, encoding="utf-8")
            hello = config.get("device", "hello", fallback="").strip()
            return hello or None
        except (OSError, ValueError):
            return None

    @staticmethod
    def load_display_settings():
        config = ConfigParser()
        try:
            config.read(CONFIG_PATH, encoding="utf-8")
            history = config.getint(
                "display", "temperature_history_points",
                fallback=DEFAULT_TEMPERATURE_HISTORY_POINTS
            )
            buffers = config.getint(
                "display", "buffer_points", fallback=DEFAULT_BUFFER_POINTS
            )
            if not 1 <= history <= 10000 or not 1 <= buffers <= 10000:
                raise ValueError
            return history, buffers
        except (OSError, ValueError):
            return DEFAULT_TEMPERATURE_HISTORY_POINTS, DEFAULT_BUFFER_POINTS

    def save_connection_settings(self):
        config = ConfigParser()
        config["connection"] = {"host": self.host, "port": str(self.port)}
        if self.expected_hello:
            config["device"] = {"hello": self.expected_hello}
        config["display"] = {
            "temperature_history_points": str(self.temperature_history_points),
            "buffer_points": str(self.buffer_points),
        }
        try:
            with CONFIG_PATH.open("w", encoding="utf-8") as stream:
                config.write(stream)
        except OSError as error:
            self.status.set(f"Settings were not saved: {error}")

    def build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=3)
        outer.rowconfigure(2, weight=2)

        connection = ttk.LabelFrame(outer, text="ZeroRPC Connection", padding=8)
        connection.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        connection.columnconfigure(1, weight=1)
        ttk.Label(connection, text="Address:").grid(row=0, column=0, sticky="w")
        ttk.Entry(connection, textvariable=self.host_var, width=18).grid(
            row=0, column=1, sticky="ew", padx=(8, 4)
        )
        ttk.Label(connection, text="Port:").grid(row=0, column=2, sticky="e")
        ttk.Entry(connection, textvariable=self.port_var, width=8).grid(
            row=0, column=3, sticky="w", padx=(4, 8)
        )
        self.connect_button = ttk.Button(connection, text="Connect", command=self.connect)
        self.connect_button.grid(row=0, column=4, padx=(0, 8))
        ttk.Label(connection, textvariable=self.status).grid(
            row=1, column=0, columnspan=5, sticky="w", pady=(6, 0)
        )
        self.mode_indicator = tk.Label(
            connection, textvariable=self.mode_text, bg=self.mode_color,
            fg="white", font=("TkDefaultFont", 14, "bold"), padx=20, pady=8
        )
        self.mode_indicator.grid(row=0, column=5, padx=(12, 0), sticky="e")
        self.pidm_indicator = tk.Label(
            connection, textvariable=self.pidm_text, bg="#53616f",
            fg="white", font=("TkDefaultFont", 12, "bold"), padx=14, pady=8
        )
        self.pidm_indicator.grid(row=0, column=6, padx=(8, 0), sticky="e")

        graphs = ttk.Frame(outer)
        graphs.grid(row=1, column=0, sticky="nsew")
        graphs.columnconfigure(0, weight=1)
        graphs.columnconfigure(1, weight=1)
        graphs.rowconfigure(0, weight=1)

        chart_frame = ttk.LabelFrame(
            graphs, text=f"Temperature History ({self.temperature_history_points} points)", padding=8
        )
        chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        chart_frame.rowconfigure(0, weight=1)
        chart_frame.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(chart_frame, background="#18212b", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _event: self.draw_chart())

        legend = ttk.Frame(chart_frame)
        legend.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(legend, text="● T0", foreground="#e67e22").pack(side="left", padx=8)
        ttk.Label(legend, text="● T1", foreground="#3498db").pack(side="left", padx=8)
        ttk.Label(legend, text="— SP0", foreground="#f5b041").pack(side="left", padx=8)
        ttk.Label(legend, text="— SP1", foreground="#85c1e9").pack(side="left", padx=8)
        ttk.Label(legend, textvariable=self.pwm_legend[0], foreground="#e67e22",
                  font=("TkDefaultFont", 10, "bold")).pack(side="left", padx=8)
        ttk.Label(legend, textvariable=self.pwm_legend[1], foreground="#3498db",
                  font=("TkDefaultFont", 10, "bold")).pack(side="left", padx=8)

        measurement_frame = ttk.LabelFrame(
            graphs, text=f"Measurement Buffers ({self.buffer_points} points)", padding=8
        )
        measurement_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        measurement_frame.rowconfigure(0, weight=1)
        measurement_frame.columnconfigure(0, weight=1)
        self.measurement_canvas = tk.Canvas(
            measurement_frame, background="#18212b", highlightthickness=0
        )
        self.measurement_canvas.grid(row=0, column=0, sticky="nsew")
        self.measurement_canvas.bind(
            "<Configure>", lambda _event: self.draw_measurement()
        )
        ttk.Label(
            measurement_frame, textvariable=self.sum_text,
            font=("TkDefaultFont", 11, "bold")
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

    def connect(self):
        if self.worker and self.worker.is_alive():
            return
        host = self.host_var.get().strip()
        try:
            port = int(self.port_var.get())
            if not host or ":" in host or "/" in host or not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("Address", "Enter a valid address and a port between 1 and 65535.")
            return
        self.host, self.port = host, port
        endpoint = f"tcp://{host}:{port}"
        self.status.set("Connecting...")
        self.connect_button.configure(state="disabled")
        self.worker = RpcWorker(endpoint, self.events, self.commands, self.expected_hello)
        self.worker.start()

    def poll_events(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "connected":
                    self.status.set(f"Connected: {value}")
                    if self.expected_hello is None:
                        self.expected_hello = value
                    self.save_connection_settings()
                elif kind == "data":
                    self.last_values = value
                    elapsed = time.monotonic() - self.started_at
                    self.history.append((elapsed, value))
                    self.current[0].set(f"{value['t0']:.1f} °C")
                    self.current[1].set(f"{value['t1']:.1f} °C")
                    self.setpoint[0].set(f"{value['sp0']:.1f}")
                    self.setpoint[1].set(f"{value['sp1']:.1f}")
                    self.pwm[0].set(f"{value['pwm0']:.1f}")
                    self.pwm[1].set(f"{value['pwm1']:.1f}")
                    self.pwm_legend[0].set(f"PWM0: {value['pwm0']:.1f} → T0 / SP0")
                    self.pwm_legend[1].set(f"PWM1: {value['pwm1']:.1f} → T1 / SP1")
                    self.set_mode(value["mode"])
                    self.set_pidm(value["pidm"])
                    self.draw_chart()
                elif kind == "measurement":
                    self.measurement = value
                    self.sum_text.set(
                        f"SUM0: {value['sum0']:.4f}        SUM1: {value['sum1']:.4f}"
                    )
                    self.draw_measurement()
                elif kind == "command_ok":
                    name, result = value
                    self.status.set(f"{name} = {result}")
                elif kind == "error":
                    self.status.set(f"Error: {value}")
                elif kind == "connection_error":
                    self.status.set(f"Connection failed: {value}")
                elif kind == "disconnected":
                    self.connect_button.configure(state="normal")
                    if self.status.get() == "Disconnecting...":
                        self.status.set("Not connected")
        except queue.Empty:
            pass
        self.root.after(100, self.poll_events)

    def set_mode(self, mode):
        if mode == 0:
            color = "#20bf6b"
        elif mode == 1:
            color = "#f7b731"
        else:
            color = "#eb3b5a"
        self.mode_color = color
        self.canvas_mode_color = color
        labels = {0: "Ready", 1: "Measuring"}
        self.mode_text.set(f"MODE: {mode} - {labels.get(mode, 'Unknown mode')}")
        self.mode_indicator.configure(bg=color)

    def set_pidm(self, pidm):
        labels = {0: "PID OFF", 1: "PID CONTROL", 2: "ON/OFF CONTROL"}
        text = labels.get(pidm, "UNKNOWN CONTROL")
        color = {0: "#777777", 1: "#3867d6", 2: "#8854d0"}.get(pidm, "#eb3b5a")
        self.pidm_text.set(f"PID MODE: {pidm} - {text}")
        self.pidm_indicator.configure(bg=color)

    def draw_chart(self):
        if not hasattr(self, "canvas"):
            return
        canvas = self.canvas
        canvas.delete("all")
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 80 or height < 80:
            return
        left, top, right, bottom = 58, 18, width - 18, height - 38
        canvas.create_rectangle(left, top, right, bottom, outline="#53616f")
        values = [v for _, item in self.history for v in (item["t0"], item["t1"], item["sp0"], item["sp1"]) if v < 1000]
        if not values:
            canvas.create_text(width / 2, height / 2, text="No data", fill="#c6d0da")
            return
        lo = min(0, min(values) - 5)
        hi = max(50, max(values) + 5)
        for i in range(5):
            y_value = lo + (hi - lo) * i / 4
            y = bottom - (y_value - lo) / (hi - lo) * (bottom - top)
            canvas.create_line(left, y, right, y, fill="#2d3b48")
            canvas.create_text(left - 8, y, text=f"{y_value:.0f}", fill="#c6d0da",
                               anchor="e", font=("TkDefaultFont", 11, "bold"))

        if len(self.history) == 1:
            return
        first_time, _ = self.history[0]
        last_time, _ = self.history[-1]
        span = max(1.0, last_time - first_time)

        # Draw setpoints first so the live temperature traces remain visible
        # when the measured temperature is close to its target value.
        colors = {"sp0": "#f5b041", "sp1": "#85c1e9", "t0": "#e67e22", "t1": "#3498db"}
        for name, color in colors.items():
            points = []
            for item_time, item in self.history:
                if item[name] >= 1000:
                    continue
                x = left + (item_time - first_time) / span * (right - left)
                y = bottom - (item[name] - lo) / (hi - lo) * (bottom - top)
                points.extend((x, y))
            if len(points) >= 4:
                if name.startswith("sp"):
                    canvas.create_line(*points, fill=color, width=2, dash=(8, 4), smooth=True)
                else:
                    canvas.create_line(*points, fill=color, width=3, smooth=True)

        canvas.create_text(left, height - 15, text=f"{span:.0f} s", fill="#c6d0da",
                           anchor="w", font=("TkDefaultFont", 11, "bold"))
        canvas.create_oval(width - 92, 8, width - 76, 24, fill=getattr(self, "canvas_mode_color", "#777"), outline="")
        canvas.create_text(width - 68, 16, textvariable=self.mode_text, fill="#e8edf2", anchor="w")

    def draw_measurement(self):
        canvas = self.measurement_canvas
        canvas.delete("all")
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 80 or height < 50:
            return
        if not self.measurement:
            canvas.create_text(width / 2, height / 2, text="No completed measurement", fill="#c6d0da")
            return
        left, top, right, bottom = 42, 10, width - 16, height - 20
        # buffer_points is a display limit, not a firmware limitation.  The
        # current firmware returns 64 samples, but a future server may return
        # a longer buffer for signals that last more than eight seconds.
        buf0 = self.measurement["buf0"][:self.buffer_points]
        buf1 = self.measurement["buf1"][:self.buffer_points]
        point_count = max(len(buf0), len(buf1), 1)
        all_values = [value for value in buf0 + buf1 if value == value]
        if not all_values:
            return
        lo = min(all_values)
        hi = max(all_values)
        if hi <= lo:
            hi = lo + 1
        canvas.create_rectangle(left, top, right, bottom, outline="#53616f")
        for name, values, color in (("buf0", buf0, "#e67e22"), ("buf1", buf1, "#3498db")):
            points = []
            for index, value in enumerate(values):
                x = left + index / max(1, point_count - 1) * (right - left)
                y = bottom - (value - lo) / (hi - lo) * (bottom - top)
                points.extend((x, y))
            if len(points) >= 4:
                canvas.create_line(*points, fill=color, width=2, smooth=True)
        axis_font = ("TkDefaultFont", 11, "bold")
        canvas.create_text(left, height - 8, text="0", fill="#c6d0da",
                           anchor="w", font=axis_font)
        canvas.create_text(right, height - 8, text=str(point_count - 1), fill="#c6d0da",
                           anchor="e", font=axis_font)
        canvas.create_text(right - 5, top + 8, text="BUF0", fill="#e67e22",
                           anchor="e", font=axis_font)
        canvas.create_text(right - 5, top + 24, text="BUF1", fill="#3498db",
                           anchor="e", font=axis_font)

    def close(self):
        if self.worker:
            self.worker.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    TemperatureMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
