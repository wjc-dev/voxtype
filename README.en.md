# VoxType for macOS — Qwen / Doubao

English · [简体中文](./README.md)

A macOS voice input tool that **does not** replace your system input method. Sogou Pinyin (or any IME) stays as your active input source; hold a global hotkey to dictate, and the recognized text is pasted at the caret only after you release.

## What problem does this solve

Many users love Sogou Pinyin for typing but occasionally need voice input. Installing the Qwen or Doubao IME to get voice means switching away from Sogou. VoxType turns voice recognition into a **standalone dictation tool**:

- Does not register as a system input method; never touches your current IME
- Hold the hotkey to speak → release → recognized text is pasted at the caret
- Supports both Qwen Audio 3.0 ASR Streaming and Doubao Seed ASR 2.0
- Does not depend on the target app's Accessibility surface — works on WeChat 4.x, VS Code, and other AX-closed apps

## Capabilities

- Selectable engine: Qwen Audio 3.0 ASR Streaming (default) or Doubao Seed ASR 2.0
- Shared recognition vocabulary across both engines; Doubao can bind a console hot-word table ID
- Right Option, Fn/Globe, Right Command, or a custom combo; passive (non-swallowing) listeners available
- `⌃⌥Space` is registered as a system hotkey — does not read other keystrokes, no Input Monitoring permission needed
- Clicking the menu-bar icon only opens Settings — never starts or stops recording
- Floating preview anchors to bottom-center of the main screen by default; set `VOICE_INPUT_FLOATING_FOLLOW_CARET=1` to follow the caret instead
- Final text is committed exactly once; switching windows mid-recording never writes to the new foreground window
- **Blind Cmd+V path**: when no AX anchor can be captured (WeChat 4.x, VS Code), VoxType falls back to `⌘V` and still lands the text in the foreground window
- Compatibility-first clipboard paste: original clipboard content is fully restored and tagged transient/concealed so history tools (Maccy, Raycast, Alfred) skip it; never synthesizes Return or auto-submits
- Short-press, silence, and personalized-context-echo guards
- On failure, the last 5 recognized texts are kept in a local recovery list
- Native SwiftUI settings helper, menu-bar-resident, ships a self-contained App/PKG with no Python dependency

VoxType intentionally does **not** implement marked-text underlines. That requires registering as an InputMethodKit input source, which conflicts with the "keep Sogou as the active IME" goal. Streaming changes are confined to the standalone preview capsule; the target editor only receives the stable final result.

## Install (end users)

Grab `VoxType-v0.1.0-macOS-arm64-internal.dmg` or `.pkg`. Both bundle the runtime — no Python, Homebrew, or terminal needed. Without a Developer ID, the App itself is ad-hoc signed and the PKG installer container is unsigned; on first launch grant Microphone, Accessibility, and (for single-modifier hotkeys) Input Monitoring permission as prompted.

After first launch:

1. Pick Qwen or Doubao on the "Engine" pane and enter your credentials. Default is Qwen; try Doubao for technical terms or quiet voice.
2. Right Option works on most personal Macs; on tightly managed corporate Macs use `Control + Option + Space`.
3. Click "Save and restart".
4. Focus an input field, hold Right Option, speak, release. If corporate security software blocks Right Option, switch to `⌃⌥Space` in Settings.

## Run from source

Requires macOS 13+, Apple Silicon, Xcode Command Line Tools, Python 3.13.

```bash
git clone https://github.com/WangJincheng888/voxtype.git
cd voxtype
uv venv --python 3.13 .venv           # or: python3.13 -m venv .venv
uv pip install -r requirements.txt     # or: pip install -r requirements.txt
cp env.example .env                    # then fill in your Qwen or Doubao API credentials
.venv/bin/python main.py
```

## Build distributable .dmg / .pkg

```bash
zsh ./build-internal-dmg.command
# Output in dist-internal/VoxType-v0.1.0-macOS-arm64-internal.{dmg,pkg,zip}
```

The build downloads PyInstaller and compiles the SwiftUI settings helper via `xcrun swiftc`.

## Project layout

```
main.py               Entry point, recording session orchestration
settings_ui.py        PyQt fallback settings panel
src/
  audio/              Microphone capture, streaming chunking
  transcription/      Qwen + Doubao engine implementations
  keyboard/           Global hotkeys, text insertion, blind Cmd+V path
  ui/                 Status bar, floating preview
  clipboard_paste.py  Transient clipboard write + restore
  correction_learning.py Text insertion and AX target capture
native_settings/      SwiftUI native settings helper (separate subprocess)
packaging/            PyInstaller spec, icons, entitlements
test/                 Unit tests (pytest)
```

## Privacy posture

- **No recording uploads**: local archive is off by default; toggle in Settings
- **No recognized content in logs**: only coarse metrics (character count, write success) — never the text, context, or target app
- **Transient clipboard**: pasted text is tagged `org.nspasteboard.TransientType` / `ConcealedType` / `AutoGeneratedType` so clipboard-history tools skip it
- **API credentials**: stored at `~/Library/Application Support/VoxType/.env`, **never** baked into build artifacts
- Audio goes to the Qwen or Doubao cloud for recognition; if your content is sensitive, point VoxType at a self-hosted ASR endpoint

## Known limits

- macOS 26 Tahoe regressed Accessibility behavior for Electron apps (VS Code, Cursor, etc.). When VoxType can't capture an AX target it falls back to a blind `⌘V`, so text still reaches the foreground window — but precise caret positioning and dedup are lost
- WeChat 4.x disables AX exposure entirely and also relies on the blind Cmd+V path
- No marked-text underline, by design (see above)

## Contributing

Issues and PRs welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md). Every PR must pass `pytest test/`.

## Security

Report vulnerabilities per [SECURITY.md](./SECURITY.md). **Do not** paste API keys or recordings into public Issues.

## License

[MIT](./LICENSE). This project derives from [ErlichLiu/Whisper-Input](https://github.com/ErlichLiu) and [Mor-Li/Whisper-Input-Next](https://github.com/Mor-Li); their original copyright notices are preserved.
