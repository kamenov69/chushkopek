import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import gevent
import zerorpc
from pykidev.server import DeviceService, read_setup, serve

class Device:
    def __init__(self, *args, **kwargs):
        self.calls = []
        self.closed = False
        self.active = 0
    def commands_list(self):
        return ['hello', 'sp1', 'pid1m']
    def command(self, name, *args, **kwargs):
        self.active += 1
        assert self.active == 1, 'Serial calls overlap'
        time.sleep(.01)
        self.calls.append((name, args))
        self.active -= 1
        return 'Protecta'
    def close(self):
        self.closed = True

class Tests(unittest.TestCase):
    def test_setup_and_failure_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'setup.txt'
            path.write_text('# comment\npid1m 0\nsp1 150.5 # target\npid1m 1\n')
            self.assertEqual(read_setup(path)[1], (3, 'sp1', [150.5]))
            device = Device()
            with patch('pykidev.server.PykiDev', return_value=device), patch('pykidev.server.zerorpc.Server') as server:
                serve('fake', 115200, path, 'inproc://unused')
                server.return_value.run.assert_called_once()
            self.assertEqual([x[0] for x in device.calls], ['hello', 'pid1m', 'sp1', 'pid1m'])
            self.assertTrue(device.closed)
            device = Device()
            device.command = lambda *a, **k: None
            with patch('pykidev.server.PykiDev', return_value=device):
                with self.assertRaises(RuntimeError):
                    serve('fake', 115200, None, 'inproc://unused')
            self.assertTrue(device.closed)

    def test_rpc_multiple_clients_and_shutdown(self):
        device = Device()
        service = DeviceService(device)
        server = zerorpc.Server(service)
        service._server = server
        server.bind('inproc://chushkopek-test')
        worker = gevent.spawn(server.run)
        clients = [zerorpc.Client(timeout=3) for _ in range(2)]
        try:
            for client in clients:
                client.connect('inproc://chushkopek-test')
            jobs = [gevent.spawn(client.hello) for client in clients]
            gevent.joinall(jobs, timeout=5, raise_error=True)
            self.assertEqual([job.value for job in jobs], ['Protecta', 'Protecta'])
            self.assertEqual(clients[0].shutdown(), 'Server stopping')
            worker.join(timeout=3)
            self.assertTrue(worker.ready())
        finally:
            for client in clients:
                client.close()
            server.close()
            service._close()
        self.assertTrue(device.closed)

if __name__ == '__main__':
    unittest.main()
