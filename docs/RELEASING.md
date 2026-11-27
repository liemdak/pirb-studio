# Release procedure

1. Update app/version.py, paths/text in installer/setup.c and uninstall.c, both native .rc resources, README filenames and CHANGELOG together.
2. Install requirements-build.txt in Python 3.12. Run `python -m unittest discover -s tests -v`, then `python tools/build_windows.py`.
3. On Windows, check Setup, shortcuts, global input, audio, transparency, language persistence and Apps uninstall. Do not label a cross-compiled installer as tested on Windows unless it was executed there.
4. Commit source/assets/docs only. Generated executables, caches, dist and private configuration stay out of git; distribute binaries through Releases.
5. Push the source to main with a new VERSION. After Linux tests and Windows tests/build/audit/smoke pass, the workflow creates v<VERSION> at that exact commit, uploads all assets to a draft and publishes a pre-release. Existing published assets are preserved; bump VERSION for a new build. Matching manually pushed tags are also supported and checked against VERSION. The workflow does not test interactive installation/uninstallation.

Manual repository setup (choose your account/visibility first):

```powershell
git init -b main
git add .
git commit -m "Release Pirb Desk 0.10.3 with bilingual Pythenians settings"
gh auth login
gh repo create pirb-studio --private --source . --remote origin --push
git tag v0.10.3
git push origin v0.10.3
```

No public visibility or open-source license is assumed. Organization policies may require allowing Actions to write repository contents.


0.10.0 naming contract: `Pirb_Desk_<version>_Windows_x64_Setup.exe`, `Pirb_Desk_<version>_Windows_x64_Portable.zip`, legacy `PIRB_Studio_<version>_Windows_x64_Setup.exe`, plus `SHA256SUMS.txt`. The legacy Setup must be byte-identical to the new Setup so installed 0.9.x clients can update. Do not remove this alias without an explicit migration plan. Portable root/launcher: `PirbDesk/PirbDesk.exe`. Keep QSettings, app-data, instance-lock, install-parent and uninstall registry IDs stable.

Publish complete assets from a draft release before exposing a new version to update clients. Verify anonymous release selection and checksums, including the legacy 0.9.1 client contract. Never publish just the new filename while the old updater still requires the alias.
