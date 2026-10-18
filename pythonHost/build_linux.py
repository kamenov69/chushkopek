"""Build with: python -m pip install pyinstaller; python build_linux.py."""
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    if not sys.platform.startswith('linux'):
        raise SystemExit('Run this build on Linux.')
    root = Path(__file__).resolve().parent
    subprocess.run([
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
        '--onefile', '--name', 'Chushkopek',
        '--distpath', str(root / 'dist'),
        '--workpath', str(root / 'build'),
        '--specpath', str(root / 'build'),
        str(root / 'launch_gui.py'),
    ], cwd=root, check=True)
    # Keep configuration editable and persistent outside the bundled runtime.
    config = root / 'dist' / 'setup.ini'
    if not config.exists():
        shutil.copy2(root / 'setup.ini', config)
    print(f'Ready: {root / "dist" / "Chushkopek"}')


if __name__ == '__main__':
    main()
