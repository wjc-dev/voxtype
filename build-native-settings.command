#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${0:A:h}"
cd "$PROJECT_DIR"
mkdir -p build/swift-module-cache build/clang-module-cache

if ! xcrun --find swiftc >/dev/null 2>&1; then
  print -u2 "缺少 Swift 编译器，请先运行：xcode-select --install"
  exit 1
fi

CLANG_MODULE_CACHE_PATH="$PROJECT_DIR/build/clang-module-cache" \
SWIFT_MODULECACHE_PATH="$PROJECT_DIR/build/swift-module-cache" \
xcrun swiftc -parse-as-library \
  -framework SwiftUI -framework AppKit \
  -Xlinker -sectcreate -Xlinker __TEXT -Xlinker __info_plist \
  -Xlinker "$PROJECT_DIR/native_settings/VoiceInputSettings-Info.plist" \
  native_settings/VoiceInputSettings.swift \
  -o build/VoiceInputSettings

print "已生成：$PROJECT_DIR/build/VoiceInputSettings"
