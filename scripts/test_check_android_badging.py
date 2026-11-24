"""Synthetic aapt package, SDK and permission acceptance fixtures."""

import unittest

from check_android_badging import check_badging

GRADLE = """
android {
 defaultConfig {
  applicationId 'com.veypanel.client'
  minSdk 26
  targetSdk 35
  versionCode 18
  versionName '0.1.0-alpha.18'
 }
}
"""
BADGING = """package: name='com.veypanel.client' versionCode='18' versionName='0.1.0-alpha.18' compileSdkVersion='35'
sdkVersion:'26'
targetSdkVersion:'35'
uses-permission: name='android.permission.INTERNET'
uses-permission: name='android.permission.CAMERA'
"""


class BadgingTests(unittest.TestCase):
    """Refuse package/version drift and permissions outside policy."""

    def test_valid(self):
        """A reviewed package configuration is accepted."""
        package, version, permissions = check_badging(BADGING, GRADLE)
        self.assertEqual(package, "com.veypanel.client")
        self.assertEqual(version, "0.1.0-alpha.18")
        self.assertIn("android.permission.CAMERA", permissions)

    def test_wrong_package(self):
        """An unrelated package ID cannot pass."""
        with self.assertRaisesRegex(ValueError, "identity"):
            check_badging(BADGING.replace("com.veypanel.client", "evil.app"), GRADLE)

    def test_wrong_version(self):
        """Unexpected version codes fail."""
        with self.assertRaisesRegex(ValueError, "identity"):
            check_badging(BADGING.replace("versionCode='18'", "versionCode='19'"), GRADLE)

    def test_wrong_sdk(self):
        """SDK values must match Gradle."""
        with self.assertRaisesRegex(ValueError, "SDK policy"):
            check_badging(BADGING.replace("targetSdkVersion:'35'", "targetSdkVersion:'28'"), GRADLE)

    def test_unexpected_permission(self):
        """Sensitive, unreviewed permissions fail closed."""
        text = BADGING + "uses-permission: name='android.permission.RECORD_AUDIO'\n"
        with self.assertRaisesRegex(ValueError, "Unexpected APK permissions"):
            check_badging(text, GRADLE)

    def test_unrequested_vibration(self):
        """The bundled QR scanner does not justify VIBRATE permission."""
        text = BADGING + "uses-permission: name='android.permission.VIBRATE'\n"
        with self.assertRaisesRegex(ValueError, "Unexpected APK permissions"):
            check_badging(text, GRADLE)

    def test_missing_internet(self):
        """The expected telemetry permission must be declared."""
        text = BADGING.replace("uses-permission: name='android.permission.INTERNET'\n", "")
        with self.assertRaisesRegex(ValueError, "INTERNET"):
            check_badging(text, GRADLE)

    def test_missing_camera(self):
        text = BADGING.replace("uses-permission: name='android.permission.CAMERA'\n", "")
        with self.assertRaisesRegex(ValueError, "CAMERA"):
            check_badging(text, GRADLE)

    def test_duplicate_permission(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            check_badging(BADGING + "uses-permission: name='android.permission.CAMERA'\n", GRADLE)

    def test_malformed_permission(self):
        with self.assertRaisesRegex(ValueError, "malformed"):
            check_badging(BADGING + "uses-permission: unknown='x'\n", GRADLE)

    def test_sdk_specific_permission(self):
        text = BADGING + "uses-permission-sdk-23: name='android.permission.CAMERA'\n"
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            check_badging(text, GRADLE)

    def test_conditional_permission(self):
        text = BADGING.replace("name='android.permission.CAMERA'", "name='android.permission.CAMERA' maxSdkVersion='28'")
        with self.assertRaisesRegex(ValueError, "malformed"):
            check_badging(text, GRADLE)


if __name__ == "__main__":
    unittest.main()
