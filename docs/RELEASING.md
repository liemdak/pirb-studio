# Release procedure

1. Update app/version.py, paths/text in installer/setup.c and uninstall.c, both native .rc resources, README filenames and CHANGELOG together.
2. Install requirements-build.txt in Python 3.12. Run `python -m unittest discover -s tests -v`, then `python tools/build_windows.py`.
3. On Windows, check Setup, shortcuts, global input, audio, transparency, language persistence and Apps uninstall. Do not label a cross-compiled installer as tested on Windows unless it was executed there.
4. Commit source/assets/docs only. Generated executables, caches, dist and private configuration stay out of git; distribute binaries through Releases.
5. Push the source, tag the matching commit v0.8.1 and push the tag. The workflow checks tag/version alignment, builds on Windows, smoke-tests portable startup and publishes Setup, portable ZIP and SHA256SUMS. It does not test interactive installation/uninstallation.

Manual repository setup (choose your account/visibility first):

```powershell
git init -b main
git add .
git commit -m "Release PIRB Studio 0.8.1 with bilingual Pythenians settings"
gh auth login
gh repo create pirb-studio --private --source . --remote origin --push
git tag v0.8.1
git push origin v0.8.1
```

No public visibility or open-source license is assumed. Organization policies may require allowing Actions to write repository contents.
