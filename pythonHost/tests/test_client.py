import unittest
from unittest.mock import MagicMock, patch
from pykidev.client import main, parse_command


class ClientTests(unittest.TestCase):
    def test_command_arguments(self):
        self.assertEqual(parse_command('a 2 -3 1.5'), ('a', [2, -3, 1.5]))
        with self.assertRaises(ValueError):
            parse_command('a текст')
        with self.assertRaises(ValueError):
            parse_command(' ')
        with self.assertRaises(ValueError):
            parse_command('a "')

    def test_response_and_cleanup(self):
        with patch('pykidev.client.zerorpc.Client') as factory, patch('builtins.print') as output:
            client = factory.return_value
            client.command.return_value = [1, 2.5, 'OK']
            self.assertEqual(main(['--command', 'a 2 3']), 0)
            client.command.assert_called_once_with('a', 2, 3)
            client.close.assert_called_once()
            self.assertIn("[1, 2.5, 'OK']", output.call_args.args)

    def test_error_and_cleanup(self):
        with patch('pykidev.client.zerorpc.Client') as factory, patch('builtins.print'):
            factory.return_value.command.side_effect = RuntimeError('offline')
            self.assertEqual(main(['--command', 'hello']), 1)
            factory.return_value.close.assert_called_once()
