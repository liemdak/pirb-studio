# Assets included in v0.8.0

## Desk backgrounds

**Free Japanese Backgrounds**, The Outlander
https://the-outlander.itch.io/free-japanese-backgrounds
License: CC0 1.0. The author explicitly permits use in any project, including commercially, with no credit required. The page discloses AI-assisted graphics.

Included images from that page's full-resolution image gallery, resized only by the runtime viewer and recompressed as JPEG for packaging:
- fuji_sakura.jpg: image 10827202, original/LjDBCQ.png
- temple_garden.jpg: image 10827201, original/+80zXo.png
- valley_sunset.jpg: image 10827204, original/tjHVmO.png

## Mechanical keyboard and mouse sounds

**Thock project**, ArahKarya
https://github.com/ArahKarya/thock
Inspected commit: 08a99447279bbdd469dafda5b955aa708fe939e1
Source folders: src-tauri/sounds/thock, clicky, tactile.

Each included pack.json explicitly identifies the bundled audio as CC0-1.0 and identifies its author as the Thock project. Audio was procedurally synthesized by that project; it is not a field recording of named mechanical switches. The WAV files and pack manifests are included unchanged. Application source code from that repository is not included.

## Pigeon effect

**Pigeon Coo 03**, SFXMint
https://sfxmint.com/sounds/pigeon-coo
Original file: https://sfxmint.com/dl/pigeon-coo-03.mp3
License: CC0 1.0. The page explicitly allows modification and redistribution in apps and games, and discloses AI-generated sound effects.

Converted to mono PCM 16-bit, 44,100 Hz WAV as assets/sounds/pirb_coo.wav. This is a generic pigeon coo demonstration effect, not an official PIRB/Pyth voice or sound.

## Listening comparison

Nghe_thu_Thock_Clicky_Tactile_PIRB.wav concatenates short sequences from the above CC0 sources, with pauses and volume adjustment. Order: Thock, Clicky, Tactile, pigeon coo.

## Character and rendering

The head is based on the PIRB illustration generated earlier in this conversation, cropped/resized for integration. It is AI-generated artwork. Torso, wings, desk, keyboard, mouse and lighting are rendered by application code.

The earlier Bongo Cat references are documented in REFERENCE_NOTES.md. No Bongo Cat runtime, code or textures are distributed here.

CC0 text and summary: https://creativecommons.org/publicdomain/zero/1.0/

The beak animation, facial expression overlays and adjustable character pose are application-drawn geometry added in v0.6.

Version 0.7 uses a higher-resolution crop from the same original PIRB illustration. The refined eyes, beak, chest lighting, interaction particles and scene transforms are runtime drawing code.


## Pirb Desk 0.10.0

Pyth Classic is procedural application-drawn community decoration: a purple gradient, abstract curves, Greek-key border and small PYTH text. It does not embed a new third-party logo or downloaded image. The character artwork and previous backgrounds retain the credits above. Custom WAV imports belong to the user and stay in local app data; they are not uploaded or bundled into releases.
