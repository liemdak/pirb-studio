"""Structural audit; does not claim the Windows executables were run."""
import hashlib
import io
import json
import struct
import sys
import zipfile
from pathlib import Path, PurePosixPath
import pefile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from version import VERSION


def verify():
    folder = ROOT / 'dist'
    setup = folder / f'PIRB_Studio_{VERSION}_Windows_x64_Setup.exe'
    portable = folder / f'PIRB_Studio_{VERSION}_Windows_x64_Portable.zip'
    data = setup.read_bytes()
    magic, length = struct.unpack('<8sQ', data[-16:])
    assert magic == b'PIRBZIP1' and 0 < length < len(data) - 16
    assert data[-16-length:-16] == portable.read_bytes()
    expected_imports = {'kernel32.dll', 'user32.dll', 'shell32.dll', 'ole32.dll', 'advapi32.dll'}
    with zipfile.ZipFile(portable) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            path = PurePosixPath(name)
            assert not path.is_absolute() and '..' not in path.parts
            assert '__pycache__' not in path.parts
        names = set(archive.namelist())
        for name in ('PIRB.exe', 'Uninstall.exe', 'START_HERE.txt',
                     '_internal/python312.dll', '_internal/python312.zip', '_internal/python312._pth',
                     '_internal/pirb-runtime.exe', '_internal/LICENSE.txt',
                     '_internal/Lib/site-packages/PySide6/QtNetwork.pyd',
                     '_internal/Lib/site-packages/PySide6/plugins/platforms/qwindows.dll',
                     '_internal/Lib/site-packages/PySide6/plugins/multimedia/ffmpegmediaplugin.dll',
                     '_internal/support/README.md', '_internal/support/README_VI.md',
                     '_internal/support/docs/settings-en.png', '_internal/support/docs/settings-vi.png',
                     '_internal/app/i18n.py', '_internal/app/version.py'):
            assert 'PIRB/' + name in names, name
        manifest = json.loads(archive.read('PIRB/_internal/BUILD_MANIFEST.json'))
        assert manifest['version'] == VERSION
        for path in (ROOT / 'app').rglob('*.py'):
            rel = str(path.relative_to(ROOT / 'app')).replace('\\', '/')
            packaged = archive.read('PIRB/_internal/app/' + rel)
            assert packaged == path.read_bytes(), rel
            assert manifest['source_hashes'][rel] == hashlib.sha256(packaged).hexdigest()
        for name, content in [('Setup', data), ('Launcher', archive.read('PIRB/PIRB.exe')),
                              ('Uninstaller', archive.read('PIRB/Uninstall.exe'))]:
            pe = pefile.PE(data=content)
            assert pe.FILE_HEADER.Machine == 0x8664 and pe.OPTIONAL_HEADER.Subsystem == 2
            assert {i.dll.decode().lower() for i in pe.DIRECTORY_ENTRY_IMPORT} <= expected_imports
            assert any(e.id == 3 for e in pe.DIRECTORY_ENTRY_RESOURCE.entries)
            assert pe.VS_FIXEDFILEINFO[0].FileVersionMS == 8
            assert pe.VS_FIXEDFILEINFO[0].FileVersionLS == int(VERSION.split('.')[2]) << 16
            pe.close()
    for row in (folder / 'SHA256SUMS.txt').read_text().splitlines():
        expected, name = row.split('  ', 1)
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected
    print('Package verified: version, x64 GUI, icons, imports, CRC, exact source, runtime, docs and checksums.')


if __name__ == '__main__':
    verify()
