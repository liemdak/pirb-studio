# Validation status — 0.10.3

Local builds use Linux and official Windows x64 runtime inputs. Tests cover language changes without preference resets, persistence, dynamic image entries, menus, layout bounds, transform/contact regression and preference migration. UI images are rendered offscreen.

Packaging checks cover pinned input hashes, x64 GUI PE headers/imports, embedded ZIP CRC, exact source hashes and required runtime/plugin files.

**Local limitations:** Setup, Windows Apps registration, shortcuts, global hooks, audio output, transparency and uninstaller have not been executed on a Windows machine in this environment. Structural/source checks are not native runtime validation. No overall 9/10 score or Windows FPS is claimed.

The GitHub workflow adds Windows portable startup/snapshot testing once it actually runs. A committed workflow is not a completed CI run. Follow RELEASING.md for manual Windows installation/uninstallation checks.

Update tests cover semantic version ordering, release channels/assets/URLs, no download before consent, checksum/tamper refusal, cancellation, offline/manual behavior and asynchronous HTTP success/error/size bounds with a loopback fixture. Network checks are disabled in --demo/--snapshot. Full interactive Windows upgrade remains a manual validation step.


0.10.0 adds 22 local regression tests in total: shared tabletop/keyboard and texture axes, surface bounds and old backgrounds, bounded WAV validation/copy/source-removal, per-category fallback, old preference retention, custom sound UI/VI-EN/reset and renamed/legacy release selection. Updated offscreen UI and scene captures are in this directory. These checks do not establish real Windows audio, interactive install/uninstall or full update success; report actual CI results separately.


0.10.1 adds a regression for a single connected desk shell, covered front/right depth regions and identical side vectors through 25 scene rotations. There are 23 tests in total. White-background visual captures check the asymmetric-edge perception that prompted this correction.


0.10.2 checks the entire four-corner silhouette, not only the middle sections of its side edges. The tests cover both opposite vector pairs after rotations/scales, the inset fascia and every rendered scanline boundary including RGB. Native Windows build/startup and local visual review are distinct checks.

Local 0.10.2 review passed all 24 tests and inspected full-app renders at widths 180/320/600 and rotations -9/0/30/90 degrees before publishing source. The new alpha-boundary test checks every painted scanline for the desk and both RGB modes.


0.10.3: 28 tests in total. New checks inspect all four actual pixel boundaries with off/purple/rainbow RGB, held keys, widths 180/600, rotations -9/30 and DPR 1/1.25/1.5/2. A canonical full keyboard redraw detects stale raised-cap pixels; only a one-bit premultiplied-channel rounding tolerance is allowed. A pure-white custom skin exercises the same boundary matrix; the matte frame reserves at least two physical pixels. New keyboard states are rebuilt from the bare case after Windows CI exposed dirty-region font/raster differences. A separate check changes DPR without changing preferences and verifies cache reconstruction. Local visual review covers idle/held scenes on white/black backgrounds. Native Windows CI results remain a separate validation layer.
