#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${0:A:h}"
cd "$PROJECT_DIR"

if [[ -x build/VoxTypeSettings.app/Contents/MacOS/VoxTypeSettings ]]; then
  SETTINGS_BINARY="$PROJECT_DIR/build/VoxTypeSettings.app/Contents/MacOS/VoxTypeSettings"
  EXISTING_PID="$(pgrep -f -x "$SETTINGS_BINARY" | head -n 1 || true)"
  if [[ -n "$EXISTING_PID" ]]; then
    kill -USR1 "$EXISTING_PID"
    exit 0
  fi
  SERVICE_PID="$(launchctl print "gui/$(id -u)/com.whisper-input-next" 2>/dev/null | awk '/pid =/{print $3; exit}' || true)"
  VOICE_INPUT_ROOT="$PROJECT_DIR" \
  VOICE_INPUT_DATA_ROOT="$PROJECT_DIR" \
  VOICE_INPUT_PARENT_PID="$SERVICE_PID" \
  exec "$SETTINGS_BINARY"
elif [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python settings_ui.py
else
  print -u2 "尚未安装，请先双击 install.command。"
  read -k 1 "?按任意键退出…"
fi
