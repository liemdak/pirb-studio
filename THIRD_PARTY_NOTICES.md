# Third-party notices

Original license/metadata files from official inputs remain under `_internal` and `_internal/Lib/site-packages` in the Windows distribution.

| Component | Input/source | Notices |
| --- | --- | --- |
| CPython | [3.12.10 embedded Windows x64](https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip) | PSF and incorporated licenses, `_internal/LICENSE.txt` |
| PySide6/Qt/shiboken6 | Official PyPI 6.8.3 Windows wheels | Original dist-info/package license files; [Qt source](https://download.qt.io/archive/qt/6.8/6.8.3/submodules/), [PySide source](https://code.qt.io/cgit/pyside/pyside-setup.git/?h=6.8.3) |
| FFmpeg / Microsoft runtime DLLs | As supplied by the official Qt wheels | Original package/wheel notices retained; [FFmpeg source](https://ffmpeg.org/releases/) |
| Backgrounds/audio | CC0 sources in [asset credits](app/ASSET_CREDITS.md) | Original sound pack manifests included |

`PIRB.exe` is compiled from `build/launcher.c`; it runs the unchanged official Python GUI interpreter `_internal/pirb-runtime.exe`. App source is under `_internal/app`; native/build sources under `_internal/support`. This version does not use the old sitecustomize bootstrap. Shared Qt libraries remain separate and replaceable with compatible binaries.

Exact input hashes are in `tools/runtime-lock.json` and the packaged BUILD_MANIFEST.json. No Bongo Cat code or textures are distributed; see [reference notes](app/REFERENCE_NOTES.md). Third-party rights are separate from the original application code.
