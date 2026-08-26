# Veyqa Voice

English · [简体中文](./README.md)

Push-to-talk voice dictation for macOS. Hold a hotkey, speak, release — text lands at the caret.

It does not replace your system input method. Pinyin, Wubi, or Rime keep working; voice is one keystroke away when you need it.

## Why

- Love Sogou / Rime / Wubi but occasionally want voice — don't switch IMEs just to get dictation
- Bring your own credentials for Qwen Audio 3.0 ASR or Doubao Seed ASR 2.0
- Hold to talk, release to commit. No marked-text underline, no flow disruption
- Floating preview anchored at the bottom-center, never steals focus
- Menu-bar resident, native SwiftUI settings
- Recordings are not uploaded (local archive is off by default); logs do not capture recognized content
- MIT licensed, derived from ErlichLiu's Whisper-Input

## Install

Grab the latest Veyqa Voice installer, drag Veyqa Voice to Applications. On first launch grant Microphone and Accessibility permissions as prompted.

Requires macOS 13+ on Apple Silicon.

## Configure

1. Open Veyqa Voice, pick an engine (Qwen or Doubao), enter your API credentials.
2. The default hotkey is `⌃⌥Space`. macOS registers this exact combination, so it does not need Input Monitoring permission and can report a registration conflict. Settings can record other modifier-plus-key combinations.
3. Save and restart. Focus any input field, hold the hotkey, speak, release.

Left/right Option, Command, Control, or Fn can also be used alone. Modifier-only shortcuts require a read-only keyboard monitor and Input Monitoring permission, and are more likely to conflict with macOS, remote-desktop tools, Karabiner, or managed-device security software. Prefer a combination for general reliability.

## Background reliability and recovery

- Packaged builds register a small supervisor through the macOS 13+ Service Management API. It relaunches a missing Veyqa Voice process, but cools down for five minutes after three failures in 60 seconds to prevent a crash loop.
- A Quartz shortcut listener is health-checked and re-enabled when macOS disables it. Managed Macs that reject the read-only event tap fall back to an AppKit compatibility monitor.
- The menu item uses a retained square template icon and periodic health checks. macOS may still temporarily hide third-party items when menu-bar space is exhausted. Reopen Veyqa Voice from Applications or Spotlight to raise the existing settings window without starting a second service.
- The Recovery & Diagnostics page reports login-item status, permissions, shortcut backend, and the latest session. A running legacy Voice Input process is reported during migration so two shortcut listeners are not left active silently.

Public distribution still requires a stable Developer ID signature for the App/PKG and Apple notarization. The repository's `internal` artifacts are ad-hoc-signed test builds, not a universal public release.

## Run from source

```bash
git clone https://github.com/wjc-dev/voxtype.git
cd voxtype
uv venv --python 3.13 .venv
uv pip install -r requirements-dev.txt
cp env.example .env          # fill in your Qwen or Doubao credentials
.venv/bin/python main.py
```

Requires macOS 13+, Apple Silicon, Xcode Command Line Tools, Python 3.13.

## Build .dmg / .pkg

```bash
zsh ./build-internal-dmg.command
```

Output in `dist-internal/`.

Before handing off a candidate, run the isolated verifier below. It executes the full test suite, rebuilds, validates the bundle signature/version, and launches a temporary copy to smoke-test the menu bar and settings window. It neither installs the app nor registers a login item.

```bash
zsh ./tools/verify-release-candidate.command
```

## Project layout

```
main.py            Entry point
settings_ui.py     Settings panel
src/
  audio/           Microphone capture
  transcription/   Qwen + Doubao engines
  keyboard/        Global hotkeys, text insertion
  ui/              Status bar, floating preview
native_settings/   SwiftUI native settings helper
packaging/         PyInstaller spec, icons
test/              Unit tests
```

## Contributing

Issues and PRs welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md). PRs must pass `.venv/bin/python -m pytest test/`.

## Security

Report vulnerabilities per [SECURITY.md](./SECURITY.md).

## License

[MIT](./LICENSE). Derived from [ErlichLiu/Whisper-Input](https://github.com/ErlichLiu) and [Mor-Li/Whisper-Input-Next](https://github.com/Mor-Li); original copyright notices preserved.
