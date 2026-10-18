"""Run with the project's Python environment on Linux or Windows."""
import sys


def main():
    # The packaged executable also runs the GUI's worker processes.
    if sys.argv[1:2] == ['--server']:
        from pykidev.server import main as server_main
        return server_main(sys.argv[2:])
    if sys.argv[1:2] == ['--client']:
        from pykidev.client import main as client_main
        return client_main(sys.argv[2:])
    from pykidev.gui import main as gui_main
    return gui_main()

if __name__ == "__main__":
    raise SystemExit(main())
