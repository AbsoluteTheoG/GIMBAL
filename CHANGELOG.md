# Changelog

All notable changes to Gimbal are listed here. Versions follow [Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-10-31

### Added
- **Simultaneous outputs**: one HOTAS press can send several gamepad buttons and/or keys at once (e.g. RT + LT for jumping in No Man's Sky, or Ctrl + C). Modifier keys are pressed first and released last.
- **HOTAS combos**: a binding can require several controls held together, even across two devices. A triggered combo masks simpler bindings it contains (B1 + B2 wins over B1 alone), so you can build Shift-style layers. On axis bindings, combo controls act as a lock.
- **Binding names**, shown in a new *Name* column, on HOTAS view labels and in the label menu.

## [1.1.0] - 2026-10-29

### Added
- **Virtual gamepad panel** on the main screen: a live Xbox controller shows exactly what Gimbal sends to the game (buttons, sticks, triggers), plus the keyboard and mouse keys currently sent. Controller art from [Gamepad Viewer](https://github.com/e7d/gamepad-viewer) (MIT).
- `tools/make_gamepad_assets.py` to regenerate the controller images.

### Changed
- The main window opens a bit wider to make room for the gamepad panel.

## [1.0.0] - 2026-10-29

First public release.

- Map any HOTAS, joystick, throttle or pedals to keyboard keys, mouse buttons, mouse wheel, mouse movement or a virtual Xbox 360 controller.
- One-click control detection, per-binding options (invert, deadzone, throttle axes, axis-as-button threshold, toggle, mouse speed).
- HOTAS view: picture of your HOTAS with draggable, resizable labels that light up when you use a control.
- Profiles saved automatically as JSON, with an example profile for VKB Gladiator EVO.
- Light / dark / system theme, English and French interface.
- Standalone Windows build (`Gimbal.exe`), no Python required.

[1.2.0]: https://github.com/AbsoluteTheoG/GIMBAL/releases/tag/v1.2.0
[1.1.0]: https://github.com/AbsoluteTheoG/GIMBAL/releases/tag/v1.1.0
[1.0.0]: https://github.com/AbsoluteTheoG/GIMBAL/releases/tag/v1.0.0
