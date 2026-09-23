from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import os
import importlib
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / "integrations/github-app-publisher"
sys.path.insert(0, str(PUBLISHER))
target = importlib.import_module("publisher_transport")


class PublisherPathResolutionTests(unittest.TestCase):
    def test_windows_localappdata_does_not_resolve_unused_home(self):
        with (
            patch.object(
                target,
                "os",
                SimpleNamespace(
                    name="nt", environ={"LOCALAPPDATA": "C:/synthetic-data"}
                ),
            ),
            patch.object(target, "Path") as paths,
        ):
            paths.side_effect = PureWindowsPath
            paths.home.side_effect = RuntimeError("synthetic unavailable home")
            actual = target.default_key_path()
            self.assertEqual(
                actual,
                PureWindowsPath(
                    "C:/synthetic-data/scnehaux-codex-authority/secrets/github-app.pem"
                ),
            )
            paths.home.assert_not_called()

    def test_windows_missing_localappdata_uses_home_once(self):
        with (
            patch.object(target, "os", SimpleNamespace(name="nt", environ={})),
            patch.object(target, "Path") as paths,
        ):
            paths.side_effect = PureWindowsPath
            paths.home.return_value = PureWindowsPath("C:/synthetic-home")
            actual = target.default_key_path()
            self.assertEqual(
                actual,
                PureWindowsPath(
                    "C:/synthetic-home/AppData/Local/scnehaux-codex-authority/secrets/github-app.pem"
                ),
            )
            paths.home.assert_called_once_with()

    def test_missing_both_locations_remains_an_error(self):
        with (
            patch.object(target, "os", SimpleNamespace(name="nt", environ={})),
            patch.object(target, "Path") as paths,
        ):
            paths.home.side_effect = RuntimeError("synthetic unavailable home")
            with self.assertRaises(RuntimeError):
                target.default_key_path()

    def test_invalid_explicit_windows_location_does_not_fall_back(self):
        for value in (
            "",
            "  ",
            "relative",
            "C:relative",
            "/rooted",
            "C:/a/../b",
            "C:/a/" + chr(10),
            "C:/a/" + chr(127),
        ):
            with (
                self.subTest(value=repr(value)),
                patch.object(
                    target,
                    "os",
                    SimpleNamespace(name="nt", environ={"LOCALAPPDATA": value}),
                ),
                patch.object(target, "Path") as paths,
            ):
                paths.side_effect = PureWindowsPath
                paths.home.side_effect = AssertionError(
                    "must not hide invalid explicit configuration"
                )
                with self.assertRaises(target.PublisherError):
                    target.default_key_path()
                paths.home.assert_not_called()

    def test_posix_ignores_localappdata(self):
        with (
            patch.object(
                target,
                "os",
                SimpleNamespace(name="posix", environ={"LOCALAPPDATA": "not-used"}),
            ),
            patch.object(target, "Path") as paths,
        ):
            paths.side_effect = PurePosixPath
            paths.home.return_value = PurePosixPath("/synthetic-home")
            actual = target.default_key_path()
            self.assertEqual(
                actual,
                PurePosixPath(
                    "/synthetic-home/.local/share/scnehaux-codex-authority/secrets/github-app.pem"
                ),
            )
            paths.home.assert_called_once_with()

    def test_invalid_home_paths_remain_fail_closed(self):
        for name, home in (
            ("nt", PureWindowsPath("C:relative")),
            ("posix", PurePosixPath("/a/../b")),
            ("posix", PurePosixPath("relative")),
        ):
            with (
                self.subTest(name=name),
                patch.object(target, "os", SimpleNamespace(name=name, environ={})),
                patch.object(target, "Path") as paths,
            ):
                paths.home.return_value = home
                with self.assertRaises(target.PublisherError):
                    target.default_key_path()

    def test_valid_spaces_and_unicode_are_not_rewritten(self):
        value = "C:/synthetic user/" + chr(233)
        with (
            patch.object(
                target,
                "os",
                SimpleNamespace(name="nt", environ={"LOCALAPPDATA": value}),
            ),
            patch.object(target, "Path") as paths,
        ):
            paths.side_effect = PureWindowsPath
            self.assertEqual(
                target.default_key_path().parents[2], PureWindowsPath(value)
            )
            paths.home.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "native Windows resolution")
    def test_minimal_windows_process_needs_no_home_variable(self):
        environment = {
            k: v
            for k, v in os.environ.items()
            if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
        }
        environment["LOCALAPPDATA"] = "C:/synthetic-nonexistent-data"
        program = "import sys; sys.path.insert(0,sys.argv[1]); import publisher_transport as p; assert p.default_key_path().is_absolute(); print('resolved-without-credential-access')"
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", program, str(PUBLISHER)],
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "resolved-without-credential-access")


if __name__ == "__main__":
    unittest.main()
