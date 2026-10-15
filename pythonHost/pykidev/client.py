"""Send a text command to a ZeroRPC device server."""
import argparse
from pprint import pformat
import shlex
import sys

import zerorpc


def parse_command(text):
    words = shlex.split(text)
    if not words:
        raise ValueError("Въведи команда, например hello или sp1 150.")
    arguments = []
    for word in words[1:]:
        try:
            value = int(word)
        except ValueError:
            try:
                value = float(word)
            except ValueError as error:
                raise ValueError(f"Параметърът {word!r} трябва да е число.") from error
        arguments.append(value)
    return words[0], arguments


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--connect', default='tcp://127.0.0.1:2020')
    parser.add_argument('--command', required=True)
    args = parser.parse_args(argv)
    client = None
    try:
        name, values = parse_command(args.command)
        client = zerorpc.Client(timeout=10)
        client.connect(args.connect)
        print(pformat(client.command(name, *values)), flush=True)
        return 0
    except Exception as error:
        print(f'Грешка: {error}', file=sys.stderr, flush=True)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == '__main__':
    raise SystemExit(main())
