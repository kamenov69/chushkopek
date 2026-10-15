"""Cross-platform Tkinter launcher for the serial ZeroRPC server."""
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from serial.tools.list_ports import comports
from .client import parse_command
from .config import SETUP_PATH, Settings, load_settings


class ServerWindow:
    def __init__(self, root):
        self.root = root
        self.process = None
        self.events = queue.Queue()
        self.closing = False
        self.stopping = False
        self.ready = False
        self.endpoint = None
        try:
            self.settings = load_settings()
        except (OSError, ValueError) as error:
            messagebox.showerror("setup.ini", str(error))
            self.settings = Settings()
        root.title("Чушкопек — ZeroRPC сървър")
        root.geometry("820x540")
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)
        frame = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(frame, text="Сървър")
        frame.columnconfigure(1, weight=1)
        self.port = tk.StringVar()
        self.baud = tk.StringVar(value=str(self.settings.baudrate))
        self.host = tk.StringVar(value=self.settings.host)
        self.rpc_port = tk.StringVar(value=str(self.settings.tcp_port))
        self.status = tk.StringVar(value="Спрян")
        self.inputs = []
        ttk.Label(frame, text="Сериен порт").grid(row=0, column=0, sticky="w")
        self.ports = ttk.Combobox(frame, textvariable=self.port, state="readonly")
        self.ports.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        self.refresh_button = ttk.Button(frame, text="Обнови", command=self.refresh)
        self.refresh_button.grid(row=0, column=2)
        self.inputs.extend([self.ports, self.refresh_button])
        self.entry(frame, 1, "Скорост (baud)", self.baud)
        ttk.Label(frame, text="Начална конфигурация").grid(row=2, column=0, sticky="w")
        ttk.Label(frame, text=str(SETUP_PATH), wraplength=480).grid(row=2, column=1, columnspan=2, sticky="w", padx=8, pady=4)
        self.entry(frame, 3, "Адрес на сървъра", self.host)
        self.entry(frame, 4, "TCP порт", self.rpc_port)
        ttk.Label(frame, text="127.0.0.1: само този компютър; 0.0.0.0: достъп от мрежата").grid(
            row=5, column=0, columnspan=3, sticky="w", pady=6)
        buttons = ttk.Frame(frame)
        buttons.grid(row=6, column=0, columnspan=3, sticky="ew", pady=8)
        self.start_button = ttk.Button(buttons, text="Стартирай", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(buttons, text="Спри", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=8)
        ttk.Label(buttons, textvariable=self.status).pack(side="left", padx=12)
        self.log = ScrolledText(frame, state="disabled", height=16, wrap="word")
        self.log.grid(row=7, column=0, columnspan=3, sticky="nsew")
        frame.rowconfigure(7, weight=1)
        self.build_console()
        self.refresh()
        root.after(100, self.poll)

    def build_console(self):
        frame = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(frame, text="Команди")
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(4, weight=1)
        self.client_endpoint = tk.StringVar(value=self.settings.connect_endpoint)
        self.command_text = tk.StringVar()
        self.command_history = []
        self.history_index = 0
        self.command_draft = ""
        self.command_busy = False
        ttk.Label(frame, text="Адрес на сървъра").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.client_endpoint).grid(row=0, column=1, columnspan=2, sticky="ew", padx=8, pady=4)
        ttk.Label(frame, text='Примери: hello    t1    sp1 150    a 2 3.5    |    ↑/↓ история').grid(row=1, column=0, columnspan=3, sticky="w", pady=8)
        ttk.Label(frame, text="Команда").grid(row=2, column=0, sticky="w")
        self.command_entry = ttk.Entry(frame, textvariable=self.command_text)
        self.command_entry.grid(row=2, column=1, sticky="ew", padx=8)
        self.command_entry.bind("<Return>", lambda event: self.send_command())
        self.command_entry.bind("<Up>", lambda event: self.browse_history(-1))
        self.command_entry.bind("<Down>", lambda event: self.browse_history(1))
        self.send_button = ttk.Button(frame, text="Изпрати", command=self.send_command)
        self.send_button.grid(row=2, column=2)
        self.command_status = tk.StringVar(value="Готов за изпращане")
        ttk.Label(frame, textvariable=self.command_status).grid(row=3, column=0, columnspan=3, sticky="w", pady=8)
        self.command_log = ScrolledText(frame, state="disabled", wrap="word")
        self.command_log.grid(row=4, column=0, columnspan=3, sticky="nsew")

    def browse_history(self, direction):
        if not self.command_history:
            return "break"
        if self.history_index == len(self.command_history):
            self.command_draft = self.command_text.get()
        self.history_index = max(0, min(len(self.command_history), self.history_index + direction))
        text = (self.command_draft if self.history_index == len(self.command_history)
                else self.command_history[self.history_index])
        self.command_text.set(text)
        self.command_entry.icursor("end")
        return "break"

    def write_command(self, text):
        self.command_log.configure(state="normal")
        self.command_log.insert("end", text + "\n")
        self.command_log.see("end")
        self.command_log.configure(state="disabled")

    def send_command(self):
        if self.command_busy or self.closing:
            return
        text = self.command_text.get().strip()
        endpoint = self.client_endpoint.get().strip()
        try:
            name, values = parse_command(text)
            if not endpoint.startswith("tcp://"):
                raise ValueError("Адресът трябва да започва с tcp://")
        except ValueError as error:
            self.write_command(f"Грешка: {error}")
            return
        self.write_command(f"> {text}  [{endpoint}]")
        self.command_history.append(text)
        self.history_index = len(self.command_history)
        self.command_draft = ""
        self.command_text.set("")
        self.command_entry.focus_set()
        self.command_busy = True
        self.command_status.set("Изчакване на отговор…")
        self.send_button.configure(state="disabled")
        threading.Thread(target=self.request_command, args=(endpoint, text), daemon=True).start()

    def request_command(self, endpoint, text):
        try:
            process = self.launch(["--connect", endpoint, "--command", text], module="pykidev.client")
            try:
                output, _ = process.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise RuntimeError("Изтече времето за отговор.")
            self.events.put(("command_result", (process.returncode, output.strip())))
        except Exception as error:
            self.events.put(("command_result", (1, f"Грешка: {error}")))

    def entry(self, frame, row, label, variable):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
        widget = ttk.Entry(frame, textvariable=variable)
        widget.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        self.inputs.append(widget)

    def refresh(self):
        try:
            ports = list(comports())
            self.port_paths = {f"{p.device} — {p.description}": p.device for p in ports}
            self.ports["values"] = list(self.port_paths)
            if self.port.get() not in self.port_paths:
                saved = next((label for label, path in self.port_paths.items()
                              if path == self.settings.port), "")
                self.port.set(saved)
                if not saved:
                    self.status.set("Избери сериен порт" if ports else "Няма намерени серийни портове")
        except Exception as error:
            messagebox.showerror("Серийни портове", str(error))

    def write(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    @staticmethod
    def launch(arguments, module="pykidev.server"):
        # Use the same Python environment; module launch also works on Windows.
        env = dict(os.environ, PYTHONUNBUFFERED="1")
        package_root = str(Path(__file__).resolve().parent.parent)
        env["PYTHONPATH"] = package_root + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.Popen(
            [sys.executable, "-m", module, *arguments],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            env=dict(env, PYTHONIOENCODING="utf-8"),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

    def start(self):
        if self.process is not None:
            return
        try:
            port = self.port_paths.get(self.port.get())
            if not port:
                raise ValueError("Избери сериен порт.")
            baud = int(self.baud.get())
            tcp = int(self.rpc_port.get())
            host = self.host.get().strip()
            if baud <= 0 or not 1 <= tcp <= 65535 or not host or ':' in host or '/' in host:
                raise ValueError("Провери скоростта, адреса и TCP порта (IPv4 или име).")
            self.endpoint = f"tcp://{'127.0.0.1' if host in ('0.0.0.0', '*') else host}:{tcp}"
            args = ["start", "--port", port, "--baudrate", str(baud), "--bind", f"tcp://{host}:{tcp}"]
            self.process = self.launch(args)
        except Exception as error:
            messagebox.showerror("Стартиране", str(error))
            return
        self.ready = self.stopping = False
        self.client_endpoint.set(self.endpoint)
        self.status.set("Свързване и начален setup…")
        self.start_button.configure(state="disabled")
        for widget in self.inputs:
            widget.configure(state="disabled")
        threading.Thread(target=self.read_output, args=(self.process,), daemon=True).start()

    def read_output(self, process):
        with process.stdout:
            for line in process.stdout:
                self.events.put(("log", line.rstrip()))
        self.events.put(("exit", process.wait()))

    def stop(self):
        if self.process is None or not self.ready or self.stopping:
            return
        self.stopping = True
        self.stop_button.configure(state="disabled")
        self.status.set("Спиране…")
        threading.Thread(target=self.request_stop, daemon=True).start()

    def request_stop(self):
        try:
            process = self.launch(["stop", "--connect", self.endpoint])
            try:
                output, _ = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                output, _ = process.communicate()
                raise RuntimeError("Изтече времето за спиране. " + output)
            if process.returncode:
                raise RuntimeError(output.strip())
            self.events.put(("log", output.strip()))
        except Exception as error:
            self.events.put(("stop_error", str(error)))

    def poll(self):
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "command_result":
                code, output = value
                self.write_command(output)
                self.command_busy = False
                self.command_status.set("Грешка" if code else "Получен отговор")
                self.send_button.configure(state="normal")
            elif kind == "log":
                self.write(value)
                if value.startswith("Serving at "):
                    self.settings = load_settings()
                    self.ready = True
                    self.status.set("Работи")
                    self.stop_button.configure(state="normal")
                    if self.closing:
                        self.stop()
            elif kind == "stop_error":
                self.write("Грешка при спиране: " + value)
                self.stopping = False
                self.closing = False
                self.status.set("Спирането не успя — опитай отново")
                self.stop_button.configure(state="normal")
            elif kind == "exit":
                self.process = None
                self.ready = self.stopping = False
                self.status.set(f"Спрян (код {value})")
                self.write(f"Процесът приключи с код {value}.")
                for widget in self.inputs:
                    widget.configure(state="normal")
                self.ports.configure(state="readonly")
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                if value != 0 and not self.closing:
                    self.port.set("")
                    messagebox.showerror("Свързването не успя", "Провери съобщенията и избери порт преди следващия опит.")
                if self.closing:
                    self.root.destroy()
                    return
        self.root.after(100, self.poll)

    def close(self):
        if self.process is None:
            self.root.destroy()
        else:
            self.closing = True
            if self.ready:
                self.stop()
            else:
                self.status.set("Изчакване на стартирането, след което спиране…")


def main():
    root = tk.Tk()
    ServerWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
