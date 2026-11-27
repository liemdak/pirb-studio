# Pirb Desk changelog

## 0.10.3 — Clean borders and pressed-key compositing

Sửa các mảnh viền trắng/tím: dựng khung tối trực tiếp ở kích thước hiển thị, giới hạn RGB/bóng và giữ một khoảng trống dưới bàn phím; thay điểm ảnh phím cũ trước khi vẽ trạng thái nhấn. Giữ nguyên hai cặp cạnh song song và tùy chỉnh đã lưu.

- Remove the duplicate fine texture outline and tiny front-edge ornament; keep the front strip plain.
- Rasterize the matte desk edge once at final device resolution; use a physical-pixel-aware inner frame, without a bright subpixel outline.
- Add 12 board units of front clearance and clip keyboard shadows/RGB to the inset surface.
- Replace projected dirty-region updates with world-space Source-composition patches, then project once. Match a fresh full render within one premultiplied channel bit.
- Invalidate screen/keyboard caches when the window device-pixel ratio changes.
- Add final boundary, held-key and fractional-DPI regressions. Review idle/pressed scenes on white and dark backgrounds before publishing.


## 0.10.2 — One parallelogram for the whole desk

Sửa đúng toàn bộ đường bao: bốn góc, cả hai cặp cạnh đối diện song song. Bỏ phần thân bàn sáu đỉnh; vẽ viền và dải cạnh bên trong cùng một hình bình hành, giới hạn cả RGB trong hình đó.

- Replace the extruded shell with exactly the tabletop quadrilateral; move the front fascia inside it.
- Clip material, border and RGB to the same silhouette. Keep keyboard projection, mouse, wing contact and user preferences unchanged.
- Test all four corners, both opposite-edge pairs and the actual rendered alpha boundary, including purple/rainbow RGB. Review before publishing.


## 0.10.1 — Consistent desk edges

Sửa cảm giác góc bàn bên phải dốc khác bên trái: dựng cạnh bàn thành một khối liền, giảm độ dày và thống nhất viền/màu, bỏ nét chồng ở góc trước phải. Giữ nguyên mặt phẳng bàn, bố cục và tùy chỉnh cũ.

- Replace separately outlined front/right fascia polygons with one continuous swept body.
- Reduce desk thickness from 10 to 6 scene units and use one shell material with rounded joins.
- Keep identical tabletop side vectors and all keyboard/wing contacts; add a shell/rotation regression and white-background visual capture.


## 0.10.0 — Pirb Desk

Đổi tên thành **Pirb Desk**. Sửa phối cảnh mặt bàn, thêm nền Pyth Classic và nhập WAV riêng cho từng nhóm phím/chuột. Giữ thiết lập cũ và khả năng cập nhật từ PIRB Studio 0.9.x. Vào Giao diện → Dùng nền Pyth Classic để chuyển từ nền cũ; âm tùy chỉnh ở tab Âm thanh. Không cần cài Python riêng.

- Rename PIRB Studio to Pirb Desk in app, tray, settings, launcher, installer, shortcuts and documentation; preserve data/settings/instance-lock IDs and repository URL.
- Share the tabletop/texture plane with the keyboard; fix opposing depth axes, add a thin front/right desk fascia and update rotated scene bounds.
- Add a procedural Pyth Classic purple community desk theme. New profiles default to it; existing choices remain intact, with a one-click theme button.
- Import/copy short mono/stereo PCM WAV sounds for regular keys, Space, Enter, Backspace, modifiers and mouse. Add previews, individual clear/reset, bounded validation and fallback routing. No direct MP3/OGG import.
- Refine vivid Qt contact effects with a secondary ring and warm motes. No Three.js or WebEngine dependency.
- Publish new Pirb_Desk assets and a byte-identical PIRB_Studio Setup alias for 0.9.x update clients; both filenames are integrity checked. Migrate app-owned old shortcuts after new shortcuts are saved.
- Add geometry, audio import/fallback/persistence/UI and updater name-transition regressions. Interactive Windows installation, real audio and full upgrade remain manual checks.


## 0.9.1 — 2026-11-14

- Fix Qt redirect policy conversion so public GitHub asset downloads follow HTTPS redirects to the release CDN.
- Require a successful final HTTP 200 response and test redirect response bodies.

## 0.9.0 — 2026-11-14

- Public GitHub repository and anonymous release checks; no GitHub login/token in the app.
- Checks after startup and every 6 hours, with a manual check button and an option to include pre-releases.
- Asks before downloading/installing; Later leaves the app unchanged. Shows release notes, download progress and Cancel.
- Verifies release asset URLs, file size, SHA256SUMS and GitHub digest before launching Setup, then quits PIRB to allow the upgrade.
- Added English/Vietnamese Updates settings and explicit bundled-Python installation guidance.
- Added release-selection, consent, tampering, cancellation and asynchronous HTTP tests.

## 0.8.1 — 2026-11-14

- Stack Settings labels above fields on narrow windows to accommodate Windows font metrics.
- Include the Linux QtMultimedia CI dependency and attach build assets safely to existing releases.

## 0.8.0 — 2026-11-14

- Integrated Pythenians Settings: purple, gold, ivory, Greek ornament and olive accents.
- Persistent Vietnamese/English selector; immediate translation of Settings, dynamic image entries, dialogs, accessibility names and context menu.
- Existing preferences survive language changes and upgrades.
- Complete offline Windows x64 Setup/portable, Windows Apps uninstall entry and per-user uninstaller.
- Bilingual usage/requirements, pinned build inputs, checksums, regression tests and GitHub release workflow.

## 0.7.0 — 2026-11-13

- Whole-scene rotation/resize, docking, quick layouts and wheel shortcuts.
- HD head, refined eyes/expressions, smooth interaction effects.
- Native launcher and bundled Windows installer.
- Pythenians Settings arrived as a separate patch; now integrated into 0.8.0.

## 0.6.0 — 2026-11-12

- PIRB pose controls, desk image orientation, expressions and portable runtime.

## 0.5.0 — 2026-11-12

- Custom desk images, backgrounds, RGB and sound packs.

## Earlier drafts

- Perspective, keyboard/mouse and continuous wing/body geometry iterated in 0.3–0.4.
