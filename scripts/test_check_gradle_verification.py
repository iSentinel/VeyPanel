"""Offline fixtures for strict Gradle SHA-256 verification policy."""

import unittest
import xml.etree.ElementTree as ET

from check_gradle_verification import inventory, require_runtime


def document(extra="", digest="a" * 64):
    """Build minimal verification metadata."""
    return ET.fromstring(f"""
<verification-metadata xmlns="https://schema.gradle.org/dependency-verification">
  <configuration><verify-metadata>true</verify-metadata>{extra}</configuration>
  <components>
    <component group="org.example" name="lib" version="1">
      <artifact name="lib-1.jar"><sha256 value="{digest}"/></artifact>
    </component>
  </components>
</verification-metadata>""")


class VerificationTests(unittest.TestCase):
    """Check strict verification coverage and trust-exception refusal."""

    def test_valid(self):
        self.assertEqual(len(inventory(document())), 1)

    def test_invalid_digest(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            inventory(document(digest="invalid"))

    def test_exemption(self):
        with self.assertRaisesRegex(ValueError, "exemption"):
            inventory(document(extra='<trusted-artifacts><trust group="x"/></trusted-artifacts>'))

    def test_missing_runtime(self):
        with self.assertRaisesRegex(ValueError, "misses"):
            require_runtime(inventory(document()), {"components": [
                {"group": "org.other", "name": "lib", "version": "1"}]})

    def test_runtime_coverage(self):
        require_runtime(inventory(document()), {"components": [
            {"group": "org.example", "name": "lib", "version": "1"}]})


if __name__ == "__main__":
    unittest.main()
