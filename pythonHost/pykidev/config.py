"""Shared setup.ini format: port on line one, settings, then commands."""
from dataclasses import dataclass
from pathlib import Path
import os
import sys
import tempfile

SETUP_PATH = ((Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False)
               else Path(__file__).resolve().parent.parent) / 'setup.ini')


@dataclass
class Settings:
    port: str = ''
    host: str = '127.0.0.1'
    tcp_port: int = 2020
    baudrate: int = 115200
    commands: str = ''

    @property
    def endpoint(self):
        return f'tcp://{self.host}:{self.tcp_port}'

    @property
    def connect_endpoint(self):
        host = '127.0.0.1' if self.host in ('0.0.0.0', '*') else self.host
        return f'tcp://{host}:{self.tcp_port}'


def load_settings(path=SETUP_PATH):
    path = Path(path)
    settings = Settings()
    if not path.exists():
        return settings
    lines = path.read_text(encoding='utf-8-sig').splitlines(keepends=True)
    if not lines:
        return settings
    first = lines[0].strip()
    settings.port = first[5:].strip() if first.startswith('port=') else first
    section = None
    command_lines = []
    for number, line in enumerate(lines[1:], 2):
        text = line.strip()
        if text == '[commands]':
            section = 'commands'
            continue
        if section == 'commands':
            command_lines.append(line)
            continue
        if not text or text.startswith(('#', ';')):
            continue
        if text == '[server]':
            section = 'server'
            continue
        key, separator, value = text.partition('=')
        if section != 'server' or not separator or key.strip() not in ('host', 'tcp_port', 'baudrate'):
            raise ValueError(f'{path}:{number}: invalid setting')
        key, value = key.strip(), value.strip()
        setattr(settings, key, int(value) if key != 'host' else value)
    if (settings.baudrate <= 0 or not 1 <= settings.tcp_port <= 65535
            or not settings.host or ':' in settings.host or '/' in settings.host):
        raise ValueError(f'{path}: invalid server settings')
    settings.commands = ''.join(command_lines)
    return settings


def save_connection(port, baudrate, endpoint, path=SETUP_PATH):
    """Update connection settings without changing the initialization commands."""
    path = Path(path)
    settings = load_settings(path)
    host, tcp_port = endpoint[len('tcp://'):].rsplit(':', 1)
    content = (f'port={port}\n[server]\nhost={host}\ntcp_port={tcp_port}\n'
               f'baudrate={baudrate}\n\n[commands]\n{settings.commands}')
    # Replace atomically so interruption cannot leave a half-written configuration.
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         delete=False) as stream:
            name = stream.name
            stream.write(content)
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)
