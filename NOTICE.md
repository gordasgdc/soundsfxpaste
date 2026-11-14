# SoundSFXPaste — notices

SoundSFXPaste is free software under the MIT License (see LICENSE).
Copyright (c) 2026 GDC (Dumitru Cristinel Gordas).

## Author
Dumitru Cristinel Gordas (GDC).

## Third-party components
- **Electron / Chromium** run inside DaVinci Resolve's own Workflow Integration host. They are NOT redistributed by this project.
- **DaVinci Resolve scripting API** (`DaVinciResolveScript`) is read from the user's own Resolve installation. Nothing from Blackmagic Design is bundled. The `WorkflowIntegration.node` module is not used or shipped.
- **Python 3** is provided by the user's system (python.org, Homebrew or Xcode Command Line Tools). Not bundled.
- No third-party fonts, icons, images or npm/pip packages are bundled. The interface uses system fonts and original SVG icons.
- **demo-audio/** contains sounds synthesised by `scripts/make_demo_audio.py` (CC0 1.0). See docs/PROVENANCE.md.

DaVinci Resolve and Blackmagic Design are trademarks of Blackmagic Design Pty Ltd. Not affiliated or endorsed.
