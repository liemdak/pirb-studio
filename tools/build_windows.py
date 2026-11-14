"""Build a bundled x64 Windows app and installer from pinned official inputs.

Works on Linux (cross compilation) or Windows; never uses a previous release.
"""
import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

import pefile
import ziglang

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from version import VERSION


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs(cache):
    cache.mkdir(parents=True, exist_ok=True)
    result = []
    for item in json.loads((ROOT / 'tools/runtime-lock.json').read_text()):
        path = cache / item['filename']
        if not path.exists():
            url = item['source']
            if url.endswith('/json'):
                with urllib.request.urlopen(url, timeout=60) as response:
                    metadata = json.load(response)
                url = next(row['url'] for row in metadata['urls'] if row['filename'] == path.name)
            print('Downloading', path.name, flush=True)
            temp = path.with_suffix(path.suffix + '.part')
            with urllib.request.urlopen(url, timeout=90) as response, temp.open('wb') as output:
                shutil.copyfileobj(response, output)
            if digest(temp) != item['sha256']:
                temp.unlink()
                raise ValueError('Download hash mismatch: ' + path.name)
            temp.replace(path)
        if digest(path) != item['sha256']:
            raise ValueError('Cached input hash mismatch: ' + path.name)
        result.append(path)
    return result


def compile_native(folder, source, output, entry, resource=None, extra=()):
    headers = Path(ziglang.__file__).parent / 'lib/libc/include/any-windows-any'
    args = [sys.executable, '-m', 'ziglang', 'cc', '-target', 'x86_64-windows-gnu',
            '-ffreestanding', '-fno-stack-protector', '-nostdlib', '-isystem', str(headers),
            '-Os', source]
    if resource:
        subprocess.run([sys.executable, '-m', 'ziglang', 'rc', '/fo', resource,
                        resource.replace('.res', '.rc')], cwd=folder, check=True, timeout=120)
        args.append(resource)
    args += ['-Wl,--subsystem,windows', '-Wl,--entry,' + entry, '-o', str(output),
             '-luser32', '-lkernel32', *extra]
    subprocess.run(args, cwd=folder, check=True, timeout=180)
    pe = pefile.PE(str(output))
    assert pe.FILE_HEADER.Machine == 0x8664 and pe.OPTIONAL_HEADER.Subsystem == 2
    pe.close()


def assemble_runtime(downloads, stage, internal):
    wheels = stage / 'wheels'
    wheels.mkdir(parents=True)
    for path in downloads:
        with zipfile.ZipFile(path) as archive:
            archive.extractall(wheels if path.suffix == '.whl' else internal)
    site = internal / 'Lib/site-packages'
    site.mkdir(parents=True)
    for package in ('PySide6', 'shiboken6'):
        for path in (wheels / package).rglob('*'):
            if path.is_file() and (path.suffix.lower() in ('.py', '.pyi', '.json', '.txt', '.xml', '.conf') or 'license' in str(path).lower()):
                dest = site / path.relative_to(wheels)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest)
    for path in wheels.glob('*.dist-info'):
        shutil.copytree(path, site / path.name)
    seeds = [wheels / 'PySide6' / (m + '.pyd') for m in ('QtCore', 'QtGui', 'QtWidgets', 'QtMultimedia')]
    seeds += list((wheels / 'shiboken6').glob('*.pyd'))
    for category in ('platforms', 'imageformats', 'iconengines', 'styles', 'multimedia', 'networkinformation', 'tls'):
        seeds += [p for p in (wheels / 'PySide6/plugins' / category).glob('*.dll') if p.name.lower() != 'qpdf.dll']
    seeds += [p for p in (wheels / 'PySide6').glob('*.dll') if p.name.lower().startswith(('avcodec', 'avformat', 'avutil', 'swresample', 'swscale'))]
    index = {}
    for path in wheels.rglob('*'):
        if path.suffix.lower() in ('.dll', '.pyd'):
            index.setdefault(path.name.lower(), []).append(path)
    selected, unresolved = set(), set()
    while seeds:
        path = seeds.pop()
        if path in selected:
            continue
        selected.add(path)
        if path.suffix.lower() == '.pyd':
            for name in set(re.findall(rb'PySide6\.(Qt[A-Za-z]+)', path.read_bytes())):
                binding = wheels / 'PySide6' / (name.decode() + '.pyd')
                if binding.is_file():
                    seeds.append(binding)
        pe = pefile.PE(str(path), fast_load=True)
        pe.parse_data_directories(directories=[1, 13])
        assert pe.FILE_HEADER.Machine == 0x8664
        for attr in ('DIRECTORY_ENTRY_IMPORT', 'DIRECTORY_ENTRY_DELAY_IMPORT'):
            for entry in getattr(pe, attr, []):
                name = entry.dll.decode().lower()
                if name in index:
                    candidates = index[name]
                    seeds.append(next((p for p in candidates if p.parent == path.parent), candidates[0]))
                else:
                    unresolved.add(name)
        pe.close()
    for path in selected:
        dest = site / path.relative_to(wheels)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    for package in ('PySide6', 'shiboken6'):
        for pattern in ('msvcp*.dll', 'vcruntime*.dll'):
            for path in (wheels / package).glob(pattern):
                shutil.copy2(path, site / package / path.name)
    shutil.copy2(internal / 'pythonw.exe', internal / 'pirb-runtime.exe')
    (internal / 'python312._pth').write_text('python312.zip\n.\nLib/site-packages\napp\nimport site\n', encoding='utf-8')
    return {'native_files': sorted(str(p.relative_to(wheels)) for p in selected),
            'external_imports': sorted(unresolved)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, default=ROOT / '.cache/runtime')
    args = parser.parse_args()
    downloads = inputs(args.cache.resolve())
    stage = ROOT / '.build'
    if stage.exists():
        shutil.rmtree(stage)
    internal = stage / 'PIRB/_internal'
    internal.mkdir(parents=True)
    manifest = assemble_runtime(downloads, stage, internal)
    app = internal / 'app'
    shutil.copytree(ROOT / 'app', app, ignore=shutil.ignore_patterns('__pycache__', 'preview.png', '*.pyc'))
    support = internal / 'support'
    support.mkdir()
    for name in ('README.md', 'README_VI.md', 'CHANGELOG.md', 'THIRD_PARTY_NOTICES.md', 'LICENSE'):
        shutil.copy2(ROOT / name, support / name)
    shutil.copytree(ROOT / 'docs', support / 'docs')
    for name in ('build', 'installer', 'tools'):
        shutil.copytree(ROOT / name, support / name, ignore=shutil.ignore_patterns('*.exe', '*.res', '*.pyc', '__pycache__'))
    (support / 'DIAGNOSTICS.bat').write_text('@echo off\r\ncd /d "%~dp0.."\r\n"%~dp0..\\python.exe" "%~dp0..\\app\\launch.py"\r\npause\r\n', encoding='ascii')
    top = internal.parent
    (top / 'START_HERE.txt').write_text('PIRB Studio ' + VERSION + '\n\nOpen PIRB.exe. Keep _internal beside it.\nRight-click PIRB > Appearance & sound. Language: English / Tieng Viet.\n\nMo PIRB.exe. Giu nguyen thu muc _internal.\nHuong dan: _internal/support/README_VI.md\n', encoding='utf-8')
    compile_native(ROOT / 'build', 'launcher.c', top / 'PIRB.exe', 'pirb_start', 'launcher.res')
    extra = ('-lshell32', '-lole32', '-ladvapi32')
    compile_native(ROOT / 'installer', 'uninstall.c', top / 'Uninstall.exe', 'pirb_uninstall_start', 'uninstall.res', extra)
    compile_native(ROOT / 'installer', 'setup.c', stage / 'setup_stub.exe', 'pirb_setup_start', 'setup.res', extra)
    manifest.update(version=VERSION, python='3.12.10', qt='6.8.3',
                    inputs={p.name: digest(p) for p in downloads},
                    source_hashes={p.relative_to(app).as_posix(): digest(p) for p in app.rglob('*.py')})
    (internal / 'BUILD_MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    portable = dist / ('PIRB_Studio_' + VERSION + '_Windows_x64_Portable.zip')
    with zipfile.ZipFile(portable, 'w', zipfile.ZIP_DEFLATED, compresslevel=7) as archive:
        for path in sorted(top.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(stage))
    payload = portable.read_bytes()
    setup = dist / ('PIRB_Studio_' + VERSION + '_Windows_x64_Setup.exe')
    setup.write_bytes((stage / 'setup_stub.exe').read_bytes() + payload + struct.pack('<8sQ', b'PIRBZIP1', len(payload)))
    hashes = dist / 'SHA256SUMS.txt'
    hashes.write_text(''.join(digest(p) + '  ' + p.name + '\n' for p in (setup, portable)), encoding='ascii')
    print('Built', setup, '\nBuilt', portable)


if __name__ == '__main__':
    main()
