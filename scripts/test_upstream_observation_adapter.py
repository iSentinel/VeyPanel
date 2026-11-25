"""Exercise the strict upstream API normalization boundary offline."""

import unittest

from upstream_observation_adapter import extract_row


class ObservationAdapterTests(unittest.TestCase):
    """Validate identity, release status and exact commit corroboration."""

    def setUp(self) -> None:
        """Build synthetic, independent API-shaped snapshots."""
        self.repo = "ClassicOldSong/Apollo"
        self.metadata = {"full_name": self.repo, "default_branch": "master",
                         "license": {"spdx_id": "GPL-3.0"}, "archived": False}
        self.branch = {"sha": "a" * 40}
        self.release = {"id": 42, "tag_name": "v1", "draft": False,
                        "prerelease": False}
        self.ref = {"ref": "refs/tags/v1", "object": {"type": "commit", "sha": "b" * 40}}
        self.resolved = {"sha": "b" * 40}

    def row(self) -> dict:
        """Normalize the current fixture."""
        return extract_row(self.repo, self.metadata, self.branch, self.release,
                           self.ref, self.resolved)

    def test_valid_direct_tag(self) -> None:
        """Return only the seven reviewed fields for a complete observation."""
        self.assertEqual(self.row(), {"branch": "master", "head": "a" * 40,
                                      "release_id": 42, "tag": "v1", "release_commit": "b" * 40,
                                      "license": "GPL-3.0", "archived": False})

    def test_repository_mismatch(self) -> None:
        """Never accept data belonging to another repository."""
        self.metadata["full_name"] = "fixture/other"
        with self.assertRaises(ValueError):
            self.row()

    def test_unknown_repository(self) -> None:
        """Reject unreviewed repository membership."""
        self.repo = "fixture/other"
        self.metadata["full_name"] = self.repo
        with self.assertRaises(ValueError):
            self.row()

    def test_nonstable_release(self) -> None:
        """Reject draft, prerelease and ambiguous release flags."""
        for field, value in (("draft", True), ("prerelease", True), ("draft", 0)):
            with self.subTest(field=field, value=value):
                original = self.release[field]
                self.release[field] = value
                with self.assertRaises(ValueError):
                    self.row()
                self.release[field] = original

    def test_ref_mismatch(self) -> None:
        """Do not attribute a different tag to the latest release."""
        self.ref["ref"] = "refs/tags/v2"
        with self.assertRaises(ValueError):
            self.row()

    def test_annotated_tag_refused(self) -> None:
        """Require a direct commit until annotated tag resolution is qualified."""
        self.ref["object"]["type"] = "tag"
        with self.assertRaises(ValueError):
            self.row()

    def test_commit_mismatch(self) -> None:
        """Refuse tag movement or a contradictory resolved commit."""
        self.resolved["sha"] = "c" * 40
        with self.assertRaises(ValueError):
            self.row()

    def test_invalid_metadata(self) -> None:
        """Reject missing license and nonboolean archived status."""
        self.metadata["license"] = None
        with self.assertRaises(ValueError):
            self.row()
        self.metadata["license"] = {"spdx_id": "GPL-3.0"}
        self.metadata["archived"] = 0
        with self.assertRaises(ValueError):
            self.row()
