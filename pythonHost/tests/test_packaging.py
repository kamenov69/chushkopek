import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from pykidev.gui import ServerWindow


class PackagingTests(unittest.TestCase):
    def test_frozen_workers_use_executable_dispatch(self):
        with patch.object(sys, 'frozen', True, create=True), \
                patch.object(sys, 'executable', '/tmp/Chushkopek'), \
                patch('pykidev.gui.subprocess.Popen') as popen:
            ServerWindow.launch(['list'])
            self.assertEqual(popen.call_args.args[0],
                             ['/tmp/Chushkopek', '--server', 'list'])
            ServerWindow.launch(['--command', 'hello'], module='pykidev.client')
            self.assertEqual(popen.call_args.args[0],
                             ['/tmp/Chushkopek', '--client', '--command', 'hello'])

    def test_frozen_config_is_beside_executable(self):
        config = Path(__file__).resolve().parents[1] / 'pykidev' / 'config.py'
        with patch.object(sys, 'frozen', True, create=True), \
                patch.object(sys, 'executable', '/tmp/Chushkopek'):
            namespace = runpy.run_path(str(config))
        self.assertEqual(namespace['SETUP_PATH'], Path('/tmp/setup.ini'))
