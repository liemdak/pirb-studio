"""Run the built portable snapshot on a real Windows CI runner."""
import os
import subprocess
import sys
from pathlib import Path

if sys.platform != 'win32':
    raise SystemExit('This smoke test requires Windows.')
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'app'))
from version import BUNDLE_FOLDER,EXECUTABLE
folder = root / '.build' / BUNDLE_FOLDER
preview = folder / '_internal/app/preview.png'
preview.unlink(missing_ok=True)
result = subprocess.run([str(folder / EXECUTABLE), '--snapshot'], cwd=folder, timeout=60)
if result.returncode or not preview.is_file() or preview.stat().st_size < 1000:
    log = Path(os.environ.get('LOCALAPPDATA', '')) / 'PIRBDesktop/startup-error.log'
    if log.is_file(): print(log.read_text(encoding='utf-8'))
    raise SystemExit('Windows portable startup failed.')
print('Windows portable startup and snapshot succeeded.')
