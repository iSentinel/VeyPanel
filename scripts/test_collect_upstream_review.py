"""Offline transport and collection gates; never contact external services."""

import contextlib
import io
import subprocess
import time
import unittest
from unittest.mock import MagicMock, patch

import collect_upstream_review as collector


class CollectorTests(unittest.TestCase):
    """Verify fixed endpoint, resource and incomplete evidence behavior."""

    def setUp(self) -> None:
        """Use a reviewed repository and synthetic transport snapshots."""
        self.repo = "ClassicOldSong/Apollo"
        self.prefix = "/repos/" + self.repo
        self.snapshots = [{"full_name": self.repo, "default_branch": "a/b",
                           "license": {"spdx_id": "GPL-3.0"}, "archived": False},
                          {"sha": "a" * 40},
                          {"id": 42, "tag_name": "v1", "draft": False, "prerelease": False},
                          {"ref": "refs/tags/v1", "object": {"type": "commit", "sha": "b" * 40}},
                          {"sha": "b" * 40}]

    def test_endpoint_allowlist(self) -> None:
        """Reject arbitrary hosts, extra query and unreviewed repositories."""
        self.assertTrue(collector.allowed_path(self.prefix + "/commits/a%2Fb"))
        for path in ("https://evil.invalid/", self.prefix + "?x=1", "/repos/x/y",
                     self.prefix + "/commits/a/b", self.prefix + "/releases",
                     self.prefix + "/commits/%2E%2E", self.prefix + "/commits/a%2F..",
                     self.prefix + "/commits/%3F", self.prefix + "/commits/%FF"):
            self.assertFalse(collector.allowed_path(path))

    def test_reference_encoding(self) -> None:
        """Encode valid slash refs and reject ambiguous or invalid segments."""
        self.assertEqual(collector.segment("a/b"), "a%2Fb")
        for value in ("..", "?x", "", None, "a" * 129, "a/../b", "/a", "a//b"):
            with self.assertRaises(ValueError):
                collector.segment(value)

    def test_exact_request_sequence(self) -> None:
        """Bind dynamic branch/tag requests to the actual metadata snapshots."""
        get = MagicMock(side_effect=self.snapshots)
        row = collector.collect_row(self.repo, get)
        self.assertEqual(row["release_commit"], "b" * 40)
        self.assertEqual([call.args[0] for call in get.call_args_list],
                         [self.prefix, self.prefix + "/commits/a%2Fb",
                          self.prefix + "/releases/latest", self.prefix + "/git/ref/tags/v1",
                          self.prefix + "/commits/v1"])

    def test_wrong_identity_stops_requests(self) -> None:
        """Do not follow branch information from mismatched metadata."""
        get = MagicMock(return_value={"full_name": "other/repo"})
        with self.assertRaises(ValueError):
            collector.collect_row(self.repo, get)
        get.assert_called_once_with(self.prefix)

    def test_missing_rows(self) -> None:
        """Never replace failed observations with baseline or fabricated data."""
        get = MagicMock(side_effect=ValueError("private canary"))
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            document, complete = collector.collect(get)
        self.assertFalse(complete)
        self.assertEqual(document["repositories"], {})
        self.assertNotIn("private canary", errors.getvalue())
        self.assertEqual(get.call_count, 5)

    def test_https_success_and_cleanup(self) -> None:
        """Use only the fixed TLS origin and close the connection on success."""
        with patch.object(collector.http.client, "HTTPSConnection") as factory:
            conn = factory.return_value
            response = conn.getresponse.return_value.__enter__.return_value
            response.status = 200
            response.getheader.return_value = "identity"
            response.read.return_value = b"{}"
            self.assertEqual(collector.fetch_bytes(self.prefix), b"{}")
            factory.assert_called_once_with(collector.ORIGIN, timeout=collector.REQUEST_SECONDS)
            response.read.assert_called_once_with(collector.MAX_RESPONSE + 1)
            conn.close.assert_called_once()

    def test_http_failure_and_oversize(self) -> None:
        """Reject redirects, rate limit, compressed and oversized bodies."""
        for status, encoding, raw in ((302, "identity", b""), (403, "identity", b""),
                                      (429, "identity", b""), (200, "gzip", b""),
                                      (200, "identity", b"x" * (collector.MAX_RESPONSE + 1))):
            with patch.object(collector.http.client, "HTTPSConnection") as factory:
                conn = factory.return_value
                response = conn.getresponse.return_value.__enter__.return_value
                response.status = status
                response.getheader.return_value = encoding
                response.read.return_value = raw
                with self.assertRaises(ValueError):
                    collector.fetch_bytes(self.prefix)
                conn.close.assert_called_once()

    def test_worker_budget_and_strict_json(self) -> None:
        """Enforce remaining time, reject invalid JSON and worker failures."""
        with patch.object(collector.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                collector.request_json(self.prefix, time.monotonic() - 1)
            run.assert_not_called()
            for code, raw in ((1, b"{}"), (0, b'{"a":1,"a":2}')):
                run.return_value = subprocess.CompletedProcess([], code, raw, b"")
                with self.assertRaises(ValueError):
                    collector.request_json(self.prefix, time.monotonic() + 2)
            run.return_value = subprocess.CompletedProcess([], 0, b"{}", b"")
            self.assertEqual(collector.request_json(self.prefix, time.monotonic() + 2), {})
            self.assertLessEqual(run.call_args.kwargs["timeout"], 2)

    def test_rate_limit_stops_all(self) -> None:
        """Stop the entire run after a worker reports a rate limit."""
        with patch.object(collector.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 3, b"", b"")
            with self.assertRaises(collector.RateLimited):
                collector.request_json(self.prefix, time.monotonic() + 2)
        get = MagicMock(side_effect=collector.RateLimited("private canary"))
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            document, complete = collector.collect(get)
        self.assertFalse(complete)
        self.assertEqual(document["repositories"], {})
        self.assertEqual(get.call_count, 1)
        self.assertNotIn("private canary", stderr.getvalue())

    def test_rate_limit_http_classification(self) -> None:
        """Classify explicit quota and secondary throttling without reading bodies."""
        for status, headers in ((429, {}), (403, {"X-RateLimit-Remaining": "0"}),
                                (403, {"Retry-After": "30"})):
            with patch.object(collector.http.client, "HTTPSConnection") as factory:
                connection = factory.return_value
                response = connection.getresponse.return_value.__enter__.return_value
                response.status = status
                response.getheader.side_effect = lambda key, default=None: headers.get(key, default)
                with self.assertRaises(collector.RateLimited):
                    collector.fetch_bytes(self.prefix)
                response.read.assert_not_called()
                connection.close.assert_called_once()
