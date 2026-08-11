# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project = Path(SPEC).resolve().parents[1]

a = Analysis(
    [str(project / "main.py")],
    pathex=[str(project)],
    binaries=[(str(project / "build" / "VoiceInputSettings.appbin"), "native_settings")],
    datas=[
        (str(project / "env.example"), "."),
        (str(project / "packaging" / "StatusBarIcon.png"), "."),
    ],
    hiddenimports=[
        "ApplicationServices",
        "AVFoundation",
        "CoreText",
        "Quartz",
        "PyObjCTools",
        "_sounddevice_data",
    ],
    excludes=[
        "PyQt5",
        "openai",
        "pydantic",
        "httpx",
        "torch",
        "transformers",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VoxType",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=str(project / "packaging" / "voice_input.entitlements"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="VoxType",
)
app = BUNDLE(
    coll,
    name="VoxType.app",
    icon=str(project / "packaging" / "AppIcon.icns"),
    bundle_identifier="com.voxtype.dev",
    version="0.1.0",
    info_plist={
        "CFBundleDisplayName": "VoxType",
        "CFBundleName": "VoxType",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "100",
        "LSMinimumSystemVersion": "13.0",
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
        "NSMicrophoneUsageDescription": "VoxType 需要麦克风权限，才能把你的语音实时转成文字。",
        "NSAppleEventsUsageDescription": "VoxType 需要辅助功能权限，才能在当前光标处实时写入转写文字。",
        "NSHumanReadableCopyright": "VoxType contributors",
    },
)
