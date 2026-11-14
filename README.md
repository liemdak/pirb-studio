# PIRB Studio

[Tiếng Việt](README_VI.md) · **Version 0.8.1** · Windows x64

An animated pigeon desktop companion that reacts to typing and mouse clicks. Customize the scene, expressions, effects and sounds in a Pythenians-inspired purple, gold and ivory Settings window.

![Settings in English](docs/settings-en.png)

## Install

Download **PIRB_Studio_0.8.1_Windows_x64_Setup.exe** from the repository's **Releases**. GitHub's **Code → Download ZIP** downloads source code, not the ready-to-run app.

1. Exit old PIRB using its system-tray menu.
2. Run Setup and confirm the installation.
3. Open **PIRB Studio** from Desktop or Start Menu.

Python, Qt, artwork, sounds and both Settings languages are bundled. No Python, pip, WinRAR or administrator rights are needed. Setup and the app work offline after downloading. No separate Settings patch is needed.

Install location: `%LOCALAPPDATA%\Programs\PIRBStudio\0.8.1\PIRB`.

Portable alternative: extract the **entire** `PIRB_Studio_0.8.1_Windows_x64_Portable.zip`, then run `PIRB\PIRB.exe`. Keep `_internal` beside the executable. Do not run inside an archive viewer. Portable also stores preferences in your Windows user profile.

## Requirements

| Item | Requirement |
| --- | --- |
| OS | Windows 10 version 1809 or later, or Windows 11; Intel/AMD **64-bit x64** |
| Storage | Reserve **300 MB free** for the app and installation temporary files |
| Display | A normal desktop session; 1280 × 720 or larger recommended for Settings |
| Input | Keyboard and mouse; global input drives the animation |
| Audio | An enabled audio output, only if sounds are wanted |
| Other | Windows built-in `tar.exe` for Setup, present in standard supported Windows installations |
| Internet | Needed to download; not needed to use the app |

32-bit Windows and native Windows ARM64 are not supported. Linux/macOS can render a source demo only. 300 MB is an installation allowance, not a measured RAM requirement.

References: [Qt 6.8 Windows support](https://doc.qt.io/qt-6.8/windows.html), [Windows tar](https://learn.microsoft.com/en-us/windows/tar), [Python embedded runtime](https://docs.python.org/3.12/using/windows.html#the-embeddable-package).

## Use

Right-click PIRB or its tray icon → **Giao diện & âm thanh… / Appearance & sound…**.

- **Language:** choose **English** or **Tiếng Việt** at the top of Settings. Text and the context menu change immediately; the choice persists after restart. First launch defaults to Vietnamese.
- **Position & size:** rotate the whole scene −180° to +180°, set a base width of 180–1200 px, select a screen corner or a quick layout. **Level the desk** compensates for the artwork's diagonal desk angle.
- **Appearance:** choose/import a background (PNG/JPG/WEBP under 30 MB), adjust crop/brightness/orientation, pose PIRB, choose expressions, keyboard lights and effects.
- **Sound:** Thock/Clicky/Tactile; keyboard, mouse and idle coo switches; individual volumes and preview buttons.
- **Ctrl + wheel** over PIRB resizes; **Alt + wheel** rotates. Left-drag moves the whole scene.
- Context menu: pause, lock, click-through, show/hide or exit. If click-through is enabled, open Settings from the tray icon.

Changes save automatically. Only one instance runs at a time. Startup with Windows is not enabled automatically; optionally copy the Desktop shortcut into the folder opened by **Win + R → `shell:startup`**.

## Upgrade, uninstall and troubleshooting

Exit the old app before upgrading. Existing preferences are reused. Old version folders/downloads are preserved, not automatically deleted.

For an installed copy, exit PIRB and use **Windows Settings → Apps → PIRB Studio 0.8.1 → Uninstall**, or run its `Uninstall.exe`. Preferences/custom images remain. For portable, exit and delete its extracted folder; the included uninstaller targets the installed location only.

If startup fails, run `_internal\support\DIAGNOSTICS.bat`. Errors may be written to `%LOCALAPPDATA%\PIRBDesktop\startup-error.log`. For sound issues check Windows output/Volume Mixer and the Sound tab. If another app's keys do not animate, test with a normal non-elevated app. Report the exact message, PIRB version and Windows version. The community build is unsigned and Windows may warn about its publisher; the app does not require disabling protection.

Preferences use `QSettings('PIRBCompanion', 'Desktop')`, normally `HKEY_CURRENT_USER\Software\PIRBCompanion\Desktop`. Imported images are copied to Qt's per-user `AppDataLocation` for `PIRBCommunity/PIRBDesktop`. Key states exist transiently in memory for animation; typed text is not recorded, input/images are not sent online, and there is no telemetry.

## Develop and build

For development install **Python 3.12 x64**:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app\main.py
```

Linux/macOS visual demo: `python app/main.py --demo`.

Build complete Windows distributions:

```powershell
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python tools\build_windows.py
```

The same tool cross-compiles on Linux. It downloads checksum-pinned official Windows CPython 3.12.10 and PySide6/Qt 6.8.3, resolves native dependencies and builds launcher/installer/uninstaller with Zig 0.13.0. Outputs: Setup, portable ZIP and `SHA256SUMS.txt` in `dist/`. `--cache PATH` reuses verified inputs. Build downloads require network; the installed app does not. See [release procedure](docs/RELEASING.md).

GitHub Actions tests source on Linux, builds on Windows and smoke-tests portable startup. A version tag publishes matching release assets when workflow permissions permit. See [validation status](docs/VALIDATION.md); a committed workflow is not evidence that it has run.

## Version and credits

[CHANGELOG](CHANGELOG.md) · [LICENSE](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md) · [Asset credits](app/ASSET_CREDITS.md)

This is a community project, not an official Pyth product. No open-source license has been selected for the original app code; third-party components retain their own licenses. Bongo Cat inspired the camera angle; no Bongo Cat code or textures are included.
