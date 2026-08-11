import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackagingIdentityTests(unittest.TestCase):
    def test_current_app_and_login_item_use_stable_qwen_identity(self):
        spec = (ROOT / "packaging" / "VoiceInput.spec").read_text(encoding="utf-8")
        settings = (ROOT / "native_settings" / "VoiceInputSettings.swift").read_text(
            encoding="utf-8"
        )
        build = (ROOT / "build-internal-dmg.command").read_text(encoding="utf-8")

        self.assertIn('bundle_identifier="com.voxtype.dev"', spec)
        self.assertIn('"Label": "com.voxtype.dev"', settings)
        self.assertIn('--identifier "com.voxtype.dev"', build)

    def test_old_identity_is_only_kept_for_login_item_migration(self):
        spec = (ROOT / "packaging" / "VoiceInput.spec").read_text(encoding="utf-8")
        build = (ROOT / "build-internal-dmg.command").read_text(encoding="utf-8")

        self.assertNotIn("com.voiceinputnext.app", spec)
        self.assertNotIn("com.voiceinputnext.app", build)
        self.assertNotIn("com.voiceinputnext.qwen", spec)
        self.assertNotIn("com.voiceinputnext.qwen", build)

    def test_packaging_cleans_nested_app_bundles_by_default(self):
        build = (ROOT / "build-internal-dmg.command").read_text(encoding="utf-8")

        self.assertIn("trap cleanup EXIT", build)
        self.assertIn('rm -rf "$WORK_DIR"', build)
        self.assertIn("VOICE_INPUT_KEEP_PACKAGE_BUILD", build)

    def test_permission_identity_survives_main_process_restart(self):
        settings = (ROOT / "native_settings" / "VoiceInputSettings.swift").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("permissionPID == Int(parentPID)", settings)
        self.assertIn("Darwin.kill(Int32(permissionPID), 0) == 0", settings)
        self.assertIn('appendingPathComponent("Contents/MacOS/VoxType")', settings)


if __name__ == "__main__":
    unittest.main()
