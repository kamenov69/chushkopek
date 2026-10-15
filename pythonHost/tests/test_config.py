from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pykidev.config import load_settings, save_connection
from pykidev.server import serve
from test_server import Device


class ConfigTests(unittest.TestCase):
    def test_missing_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'setup.ini'
            self.assertEqual(load_settings(path).port, '')
            path.write_text('port=COM3\n[server]\nhost=0.0.0.0\ntcp_port=2037\nbaudrate=9600\n[commands]\n# retain comment\nsp1 150\n')
            self.assertEqual(load_settings(path).connect_endpoint, 'tcp://127.0.0.1:2037')
            save_connection('/dev/ttyACM0', 115200, 'tcp://127.0.0.1:2020', path)
            settings = load_settings(path)
            self.assertEqual(settings.port, '/dev/ttyACM0')
            self.assertEqual(settings.commands, '# retain comment\nsp1 150\n')
            self.assertTrue(path.read_text().startswith('port=/dev/ttyACM0\n'))

    def test_verified_port_and_commands(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'setup.ini'
            path.write_text('port=COM3\n[server]\n[commands]\nsp1 150\n')
            device = Device()
            with patch('pykidev.server.PykiDev', return_value=device), patch('pykidev.server.zerorpc.Server'):
                serve('COM4', 115200, None, 'tcp://127.0.0.1:2020', config_path=path)
            self.assertEqual(load_settings(path).port, 'COM4')
            self.assertEqual(device.calls, [('hello', ()), ('sp1', (150,))])
            before = path.read_text()
            device = Device()
            device.command = lambda *a, **k: 'wrong board'
            with patch('pykidev.server.PykiDev', return_value=device):
                with self.assertRaises(RuntimeError):
                    serve('COM5', 115200, None, 'tcp://127.0.0.1:2020', config_path=path)
            self.assertEqual(path.read_text(), before)
            self.assertTrue(device.closed)
