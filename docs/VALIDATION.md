# Validation status — 0.9.0

Local builds use Linux and official Windows x64 runtime inputs. Tests cover language changes without preference resets, persistence, dynamic image entries, menus, layout bounds, transform/contact regression and preference migration. UI images are rendered offscreen.

Packaging checks cover pinned input hashes, x64 GUI PE headers/imports, embedded ZIP CRC, exact source hashes and required runtime/plugin files.

**Local limitations:** Setup, Windows Apps registration, shortcuts, global hooks, audio output, transparency and uninstaller have not been executed on a Windows machine in this environment. Structural/source checks are not native runtime validation. No overall 9/10 score or Windows FPS is claimed.

The GitHub workflow adds Windows portable startup/snapshot testing once it actually runs. A committed workflow is not a completed CI run. Follow RELEASING.md for manual Windows installation/uninstallation checks.

Update tests cover semantic version ordering, release channels/assets/URLs, no download before consent, checksum/tamper refusal, cancellation, offline/manual behavior and asynchronous HTTP success/error/size bounds with a loopback fixture. Network checks are disabled in --demo/--snapshot. Full interactive Windows upgrade remains a manual validation step.
