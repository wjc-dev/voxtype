#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${0:A:h}"
VERSION="0.1.0"
OUTPUT_DIR="${1:-$PROJECT_DIR/dist-internal}"
RUN_ID="$(date +%Y%m%d-%H%M%S)-$$"
WORK_DIR="$PROJECT_DIR/.package-build/$RUN_ID"
PYINSTALLER_WORK="$WORK_DIR/pyinstaller"
PYINSTALLER_DIST="$WORK_DIR/dist"
ICONSET="$WORK_DIR/AppIcon.iconset"
STAGING="$WORK_DIR/dmg"
CLANG_CACHE="$WORK_DIR/clang-module-cache"
APP_PATH="$PYINSTALLER_DIST/VoxType.app"
DMG_PATH="$OUTPUT_DIR/VoxType-v${VERSION}-macOS-arm64-internal.dmg"
ZIP_PATH="$OUTPUT_DIR/VoxType-v${VERSION}-macOS-arm64-internal.zip"
PKG_PATH="$OUTPUT_DIR/VoxType-v${VERSION}-macOS-arm64-internal.pkg"

cleanup() {
  # Generated .app bundles must not remain under the source tree. LaunchServices
  # indexes nested app bundles and can later grant Accessibility to an obsolete
  # build that has the same display name as the installed app.
  if [[ "${VOICE_INPUT_KEEP_PACKAGE_BUILD:-false}" != "true" ]]; then
    rm -rf "$WORK_DIR"
  fi
}
trap cleanup EXIT

mkdir -p "$WORK_DIR" "$PYINSTALLER_WORK" "$PYINSTALLER_DIST" "$ICONSET" "$STAGING" "$OUTPUT_DIR" "$CLANG_CACHE" "$PROJECT_DIR/build"
export CLANG_MODULE_CACHE_PATH="$CLANG_CACHE"
export SWIFT_MODULECACHE_PATH="$CLANG_CACHE"

"$PROJECT_DIR/.venv/bin/python" -m pip show pyinstaller >/dev/null 2>&1 || \
  "$PROJECT_DIR/.venv/bin/python" -m pip install 'pyinstaller>=6.10,<7'

xcrun swiftc -parse-as-library -O -target arm64-apple-macos13.0 \
  -framework SwiftUI -framework AppKit \
  -Xlinker -sectcreate -Xlinker __TEXT -Xlinker __info_plist \
  -Xlinker "$PROJECT_DIR/native_settings/VoiceInputSettings-Info.plist" \
  "$PROJECT_DIR/native_settings/VoiceInputSettings.swift" \
  -o "$PROJECT_DIR/build/VoiceInputSettings.appbin"

if [[ ! -f "$PROJECT_DIR/packaging/AppIcon.icns" || \
      "$PROJECT_DIR/packaging/generate_app_icon.swift" -nt "$PROJECT_DIR/packaging/AppIcon.icns" ]]; then
  xcrun swift "$PROJECT_DIR/packaging/generate_app_icon.swift" "$WORK_DIR/AppIcon-1024.png"
  for SIZE in 16 32 128 256 512; do
    sips -z "$SIZE" "$SIZE" "$WORK_DIR/AppIcon-1024.png" \
      --out "$ICONSET/icon_${SIZE}x${SIZE}.png" >/dev/null
    DOUBLE=$((SIZE * 2))
    sips -z "$DOUBLE" "$DOUBLE" "$WORK_DIR/AppIcon-1024.png" \
      --out "$ICONSET/icon_${SIZE}x${SIZE}@2x.png" >/dev/null
  done
  iconutil -c icns "$ICONSET" -o "$PROJECT_DIR/packaging/AppIcon.icns"
fi

"$PROJECT_DIR/.venv/bin/pyinstaller" \
  --noconfirm \
  --distpath "$PYINSTALLER_DIST" \
  --workpath "$PYINSTALLER_WORK" \
  "$PROJECT_DIR/packaging/VoiceInput.spec"

while IFS= read -r -d '' FILE; do
  if [[ -x "$FILE" || "$FILE" == *.dylib || "$FILE" == *.so ]]; then
    /usr/bin/codesign --force --sign - --timestamp=none "$FILE"
  fi
done < <(find "$APP_PATH/Contents" -type f -print0)

/usr/bin/codesign --force --sign - --timestamp=none \
  --entitlements "$PROJECT_DIR/packaging/voice_input.entitlements" \
  "$APP_PATH/Contents/MacOS/VoxType"
/usr/bin/codesign --force --sign - --timestamp=none \
  --entitlements "$PROJECT_DIR/packaging/voice_input.entitlements" \
  "$APP_PATH"
/usr/bin/codesign --verify --deep --strict --verbose=2 "$APP_PATH"

/usr/bin/pkgbuild \
  --component "$APP_PATH" \
  --install-location "/Applications" \
  --identifier "com.voxtype.dev" \
  --version "$VERSION" \
  "$PKG_PATH"
shasum -a 256 "$PKG_PATH" > "$PKG_PATH.sha256"
print "完成：$PKG_PATH"

# Always provide the .app as a Finder-safe ZIP. This is the simplest artifact
# to hand to a small trusted test group and preserves bundle metadata.
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"
shasum -a 256 "$ZIP_PATH" > "$ZIP_PATH.sha256"
print "完成：$ZIP_PATH"

ditto "$APP_PATH" "$STAGING/VoxType.app"
cp "$PROJECT_DIR/packaging/内测版使用说明.txt" "$STAGING/使用说明.txt"
cp "$PROJECT_DIR/版本说明-v0.1.0.md" "$STAGING/版本说明-v0.1.0.md"
ln -s /Applications "$STAGING/Applications"

if hdiutil create -volname "VoxType" -srcfolder "$STAGING" \
  -ov -format UDZO "$DMG_PATH" >/dev/null; then
  shasum -a 256 "$DMG_PATH" > "$DMG_PATH.sha256"
  print "完成：$DMG_PATH"
  print "校验：$(cat "$DMG_PATH.sha256")"
else
  print -u2 "当前环境无法创建磁盘镜像；仍可使用已生成的 App ZIP 或 PKG。"
fi
