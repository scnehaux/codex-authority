from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_publisher_environment.py"
SPEC = importlib.util.spec_from_file_location("_tested_publisher_environment", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
TARGET = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TARGET)


def inspected(resolver):
    with patch.object(TARGET, "_load_resolver", return_value=resolver):
        return TARGET.inspect_environment()


def codes(report):
    return [item["code"] for item in report["checks"] if item["code"]]


def synthetic_environment():
    allowed = {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR"}
    result = {
        name: value for name, value in os.environ.items() if name.upper() in allowed
    }
    if os.name == "nt":
        result.update(
            USERPROFILE="C:/offline-synthetic-user",
            LOCALAPPDATA="C:/offline-synthetic-user/AppData/Local",
        )
    else:
        result["HOME"] = "/offline-synthetic-user"
    return result


class PublisherEnvironmentTests(unittest.TestCase):
    def test_valid_lexical_paths_need_no_files(self):
        for location in (
            PurePosixPath("/nonexistent/synthetic/example"),
            PureWindowsPath("C:/nonexistent/synthetic/example"),
        ):
            with self.subTest(flavour=type(location).__name__):
                result = inspected(lambda: location)
                self.assertEqual(result["status"], "pass")
                self.assertEqual(result["scope"], "current-process-environment-only")
                self.assertFalse(result["boundaries"]["publication_authorized"])
                self.assertFalse(
                    result["boundaries"]["credential_existence_or_permissions_checked"]
                )
                self.assertNotIn(str(location), json.dumps(result))

    def test_relative_traversal_and_control_character_locations_fail_closed(self):
        for location in (
            PurePosixPath("relative"),
            PureWindowsPath("C:relative"),
            PureWindowsPath("/rooted-no-drive"),
            PurePosixPath("/a/../b"),
            PurePosixPath("/a/" + chr(10) + "b"),
            PurePosixPath("/a/" + chr(127) + "b"),
        ):
            with self.subTest(location=repr(location)):
                result = inspected(lambda: location)
                self.assertEqual(result["status"], "blocked")
                self.assertIn("noncanonical-default-location", codes(result))

    def test_wrong_location_types_fail_closed(self):
        for location in (None, "C:/looks-absolute", 123, True):
            with self.subTest(type=type(location).__name__):
                self.assertIn(
                    "invalid-location-type", codes(inspected(lambda: location))
                )

    def test_home_resolution_failure_is_redacted(self):
        def unavailable():
            raise RuntimeError("SENSITIVE-EXCEPTION-DETAIL")

        result = inspected(unavailable)
        self.assertIn("home-directory-unresolvable", codes(result))
        self.assertNotIn("SENSITIVE", json.dumps(result))

    def test_other_resolution_failures_are_redacted(self):
        for exception in (ValueError("SENSITIVE-VALUE"), OSError("SENSITIVE-PATH")):
            with self.subTest(type=type(exception).__name__):

                def failed():
                    raise exception

                result = inspected(failed)
                self.assertIn("default-location-resolution-failed", codes(result))
                self.assertNotIn("SENSITIVE", json.dumps(result))

    def test_source_load_errors_do_not_attempt_resolution(self):
        for exception in (
            RuntimeError("SENSITIVE"),
            ImportError("SENSITIVE"),
            SystemExit("SENSITIVE"),
        ):
            with (
                self.subTest(type=type(exception).__name__),
                patch.object(TARGET, "_load_resolver", side_effect=exception),
            ):
                result = TARGET.inspect_environment()
                self.assertIn("publisher-source-unverified", codes(result))
                self.assertFalse(
                    any(
                        item["check"] == "default-location-resolution"
                        for item in result["checks"]
                    )
                )
                self.assertNotIn("SENSITIVE", json.dumps(result))

    def test_python_version_is_checked(self):
        with patch.object(TARGET.sys, "version_info", (3, 12, 9)):
            result = inspected(lambda: PurePosixPath("/synthetic"))
        self.assertIn("python-3.13-required", codes(result))

    def test_missing_pinned_source_is_blocked_before_import(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(TARGET, "PUBLISHER_ROOT", Path(directory)),
        ):
            self.assertIn(
                "publisher-source-unverified", codes(TARGET.inspect_environment())
            )

    def test_mutated_pinned_source_is_blocked_before_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "github_app_publisher.py").write_text(
                "raise AssertionError('must not execute')", encoding="utf-8"
            )
            with patch.object(TARGET, "PUBLISHER_ROOT", root):
                self.assertIn(
                    "publisher-source-unverified", codes(TARGET.inspect_environment())
                )

    def test_missing_verifier_spec_is_blocked(self):
        for spec in (None, SimpleNamespace(loader=None)):
            with (
                self.subTest(spec=repr(spec)),
                patch.object(
                    TARGET.importlib.util, "spec_from_file_location", return_value=spec
                ),
            ):
                self.assertIn(
                    "publisher-source-unverified", codes(TARGET.inspect_environment())
                )

    def test_existing_windows_fallback_bug_is_reproduced_without_secrets(self):
        resolver = TARGET._load_resolver()
        transport = sys.modules[resolver.__module__]
        fake_os = SimpleNamespace(
            name="nt", environ={"LOCALAPPDATA": "C:/synthetic-local-data"}
        )
        with (
            patch.object(transport, "os", fake_os),
            patch.object(
                transport.Path,
                "home",
                side_effect=RuntimeError("synthetic missing home"),
            ) as home,
        ):
            result = inspected(resolver)
        home.assert_called_once_with()
        self.assertEqual(result["status"], "blocked")
        self.assertIn("home-directory-unresolvable", codes(result))
        self.assertFalse(result["boundaries"]["publisher_invoked"])

    def test_cli_json_and_exit_codes(self):
        for location, expected in (
            (PurePosixPath("/synthetic"), 0),
            (PurePosixPath("relative"), 2),
        ):
            output = io.StringIO()
            with (
                self.subTest(code=expected),
                patch.object(TARGET, "_load_resolver", return_value=lambda: location),
                contextlib.redirect_stdout(output),
            ):
                code = TARGET.main([])
            report = json.loads(output.getvalue())
            self.assertEqual(code, expected)
            self.assertEqual(report["kind"], "codex-publisher-environment-preflight")
            self.assertFalse(report["boundaries"]["publication_authorized"])

    def test_write_and_credential_arguments_are_not_supported(self):
        for arguments in (
            ["--write"],
            ["--private-key", "unused"],
            ["--confirm-sha", "0" * 40],
        ):
            with (
                self.subTest(arguments=arguments),
                contextlib.redirect_stderr(io.StringIO()),
                patch.object(TARGET, "inspect_environment") as inspect,
            ):
                with self.assertRaises(SystemExit) as error:
                    TARGET.main(arguments)
                self.assertEqual(error.exception.code, 2)
                inspect.assert_not_called()

    def test_environment_is_not_modified(self):
        original = dict(os.environ)
        inspected(lambda: PurePosixPath("/synthetic"))
        self.assertEqual(dict(os.environ), original)

    def test_real_subprocess_uses_synthetic_home_and_no_credentials(self):
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(SCRIPT)],
            cwd=ROOT,
            env=synthetic_environment(),
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "pass")
        self.assertNotIn("offline-synthetic-user", result.stdout + result.stderr)
        self.assertTrue(
            all(value is False or value == 0 for value in report["boundaries"].values())
        )
        self.assertIn("execution-tool-authorization", report["unassessed"])

    @unittest.skipUnless(os.name == "nt", "native Windows home-resolution behavior")
    def test_native_windows_missing_home_is_caught_before_activation(self):
        environment = synthetic_environment()
        del environment["USERPROFILE"]
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(SCRIPT)],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("home-directory-unresolvable", codes(report))
        self.assertNotIn("offline-synthetic-user", result.stdout + result.stderr)

    def test_real_diagnostic_cannot_open_keys_spawn_or_connect(self):
        program = "\n".join(
            (
                "import importlib.util,json,sys",
                "spec=importlib.util.spec_from_file_location('diagnostic',sys.argv[1])",
                "module=importlib.util.module_from_spec(spec)",
                "def guard(event,args):",
                "    blocked = event.startswith('socket.') or event in ('subprocess.Popen','os.system')",
                "    key = event == 'open' and str(args[0]).lower().endswith(('.pem','.key'))",
                "    if blocked or key: raise AssertionError('forbidden diagnostic side effect')",
                "sys.addaudithook(guard)",
                "spec.loader.exec_module(module)",
                "print(json.dumps(module.inspect_environment()))",
            )
        )
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", program, str(SCRIPT)],
            cwd=ROOT,
            env=synthetic_environment(),
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "pass")


if __name__ == "__main__":
    unittest.main()
