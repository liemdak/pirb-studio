# References inspected for v0.4

- https://github.com/MMmmmoko/Bongo-Cat-Mver
  Commit: 4da0b9468ad3b6ffaa096eba3f080501d6ab0b5c
  Inspected standard/mouse.png, keyboard assets, standard-mode draw order and Bezier silhouette implementation. Repository license: MIT.
- https://github.com/kuroni/bongocat-osu
  Commit: 0714582791529af714bc9a6a6a6f77497c7c561d
  Inspected mouse artwork and source-mode organization. Repository license: MIT.
- https://github.com/vladelaina/BongoCat
  Commit: 29ccda67802e6b6727acae0bdf42f50277f9aade
  Inspected src/core/mouse_tracking.c and the model artwork license. Source uses AGPL-3.0-only; bundled model assets have their own MIT notice.

No third-party source, texture, mouse or keyboard artwork from those repositories is distributed here. The inspected assets were flat cartoon/Live2D resources; this version uses independently drawn extruded keyboard geometry and a shaded mouse dome to provide visible thickness while preserving individual feedback for all 104 keys.

The continuous torso/wing union, head-layer clipping, device projection and rendering cache are application implementation code. Temporal interpolation was already present in this project and uses the standard exponential smoothing formula.

The PIRB head comes from the previously generated illustration in this conversation, cropped/resized for integration. Its generation history is AI image generation, not hand drawing. The head remains at a fixed position in v0.4; only eye interiors animate.
