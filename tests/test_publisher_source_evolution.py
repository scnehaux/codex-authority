from __future__ import annotations

from hashlib import sha1
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "_tested_publisher_history", ROOT / "scripts/verify_publisher_proof.py"
)
assert SPEC is not None and SPEC.loader is not None
TARGET = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TARGET)


class PublisherSourceEvolutionTests(unittest.TestCase):
    def test_historical_transport_pin_is_not_rewritten_to_fixed_source(self):
        self.assertEqual(
            TARGET.PUBLISHER_FILES["publisher_transport.py"],
            "03d54b7ea54296e17688eaa40a5ff0de9bbb61ca",
        )
        self.assertEqual(
            TARGET.AUTHORITY_REVISION, "6b89e95b63fa000482a1c5cac82f22864a81eeeb"
        )
        old = TARGET.read_historical_publisher_source("publisher_transport.py")
        current = (TARGET.PUBLISHER_ROOT / "publisher_transport.py").read_bytes()
        self.assertIn(b'os.environ.get("LOCALAPPDATA", str(Path.home()', old)
        self.assertNotEqual(old, current)
        self.assertNotEqual(TARGET.PUBLISHER_FILES, TARGET.CURRENT_PUBLISHER_FILES)
        self.assertEqual(
            set(TARGET.PUBLISHER_FILES), set(TARGET.CURRENT_PUBLISHER_FILES)
        )

    def test_all_historical_sources_verify_without_worktree_reads(self):
        with patch.object(
            TARGET,
            "git_blob_sha",
            side_effect=AssertionError("history must use Git objects"),
        ):
            for name, expected in TARGET.PUBLISHER_FILES.items():
                with self.subTest(source=name):
                    raw = TARGET.read_historical_publisher_source(name)
                    self.assertEqual(
                        sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest(), expected
                    )

    def test_current_sources_still_fail_on_mutation_or_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in TARGET.CURRENT_PUBLISHER_FILES:
                (root / name).write_bytes((TARGET.PUBLISHER_ROOT / name).read_bytes())
            with patch.object(TARGET, "PUBLISHER_ROOT", root):
                TARGET.verify_current_publisher_sources()
                path = root / "publisher_transport.py"
                path.write_bytes(path.read_bytes() + b"# changed\n")
                with self.assertRaisesRegex(
                    SystemExit, "current publisher source blob drifted"
                ):
                    TARGET.verify_current_publisher_sources()
                path.unlink()
                with self.assertRaisesRegex(SystemExit, "publisher source missing"):
                    TARGET.verify_current_publisher_sources()

    def test_unknown_source_is_rejected_before_git(self):
        with patch.object(TARGET, "_historical_git") as run:
            for name in ("../source.py", "missing.py"):
                with self.subTest(source=name), self.assertRaises(SystemExit):
                    TARGET.read_historical_publisher_source(name)
            run.assert_not_called()

    def test_tree_binding_rejects_wrong_mode_hash_path_or_record_count(self):
        name = "publisher_transport.py"
        expected = TARGET.PUBLISHER_FILES[name]
        relative = "integrations/github-app-publisher/" + name
        good = f"100644 blob {expected}\t{relative}\0".encode()
        for entry in (
            b"",
            good.replace(b"100644", b"120000"),
            good.replace(b"blob", b"tree"),
            good.replace(expected.encode(), b"0" * 40),
            good.replace(name.encode(), b"other.py"),
            good + good,
        ):
            with (
                self.subTest(entry=entry[:30]),
                patch.object(TARGET, "_historical_git", return_value=entry),
                self.assertRaisesRegex(SystemExit, "binding drifted"),
            ):
                TARGET.read_historical_publisher_source(name)

    def test_sizes_and_content_are_checked_before_acceptance(self):
        name = "publisher_transport.py"
        expected = TARGET.PUBLISHER_FILES[name]
        relative = "integrations/github-app-publisher/" + name
        entry = f"100644 blob {expected}\t{relative}\0".encode()
        for size in (b"bad", b"0", b"-1", b"1000001"):
            with (
                self.subTest(size=size),
                patch.object(TARGET, "_historical_git", side_effect=[entry, size]),
                self.assertRaisesRegex(SystemExit, "size invalid"),
            ):
                TARGET.read_historical_publisher_source(name)
        for size in (b"2", b"3"):
            with (
                self.subTest(size=size),
                patch.object(
                    TARGET, "_historical_git", side_effect=[entry, size, b"bad"]
                ),
                self.assertRaisesRegex(SystemExit, "bytes drifted"),
            ):
                TARGET.read_historical_publisher_source(name)

    def test_git_errors_are_fail_closed_and_redacted(self):
        for error in (
            OSError("sensitive detail"),
            subprocess.TimeoutExpired("git", 10),
            subprocess.CalledProcessError(1, "git"),
        ):
            with (
                self.subTest(error=type(error).__name__),
                patch.object(TARGET.subprocess, "check_output", side_effect=error),
                self.assertRaisesRegex(
                    SystemExit, "historical publisher Git source unavailable"
                ) as caught,
            ):
                TARGET._historical_git("cat-file", "-s", "0" * 40)
            self.assertNotIn("sensitive", str(caught.exception))

    def test_git_arguments_disable_replacement_and_inherited_redirection(self):
        with (
            patch.dict(
                os.environ,
                {
                    "GIT_DIR": "synthetic",
                    "GIT_CONFIG_COUNT": "1",
                    "git_work_tree": "synthetic",
                },
            ),
            patch.object(TARGET.subprocess, "check_output", return_value=b"ok") as run,
        ):
            self.assertEqual(TARGET._historical_git("test"), b"ok")
            self.assertEqual(
                run.call_args.args[0][:3],
                ["git", "--no-replace-objects", "--literal-pathspecs"],
            )
            self.assertFalse(
                any(k.upper().startswith("GIT_") for k in run.call_args.kwargs["env"])
            )
            self.assertEqual(run.call_args.kwargs["timeout"], 10)

    def test_real_git_replacement_refs_cannot_rewrite_historical_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = {
                k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")
            }

            def git(*args):
                return (
                    subprocess.check_output(
                        [
                            "git",
                            "-c",
                            "commit.gpgsign=false",
                            "-c",
                            "core.hooksPath=" + str(root / "no-hooks"),
                            "-C",
                            str(root),
                            *args,
                        ],
                        env=environment,
                        stderr=subprocess.DEVNULL,
                    )
                    .decode()
                    .strip()
                )

            git("init", "--quiet")
            git("config", "core.autocrlf", "false")
            git("config", "user.name", "Historical Fixture")
            git("config", "user.email", "fixture@example.invalid")
            relative = "integrations/github-app-publisher/example.py"
            path = root / relative
            path.parent.mkdir(parents=True)
            original = b"original = True\n"
            path.write_bytes(original)
            git("add", "--all")
            git("commit", "--quiet", "-m", "historical fixture")
            revision = git("rev-parse", "HEAD")
            blob = git("rev-parse", "HEAD:" + relative)
            path.write_bytes(b"replacement = True\n")
            git("add", "--all")
            git("commit", "--quiet", "-m", "replacement fixture")
            new_revision = git("rev-parse", "HEAD")
            new_blob = git("rev-parse", "HEAD:" + relative)
            git("replace", revision, new_revision)
            git("replace", blob, new_blob)
            with (
                patch.object(TARGET, "ROOT", root),
                patch.object(TARGET, "AUTHORITY_REVISION", revision),
                patch.object(TARGET, "PUBLISHER_FILES", {"example.py": blob}),
                patch.dict(os.environ, {"GIT_DIR": str(root / "absent-git-dir")}),
            ):
                self.assertEqual(
                    TARGET.read_historical_publisher_source("example.py"), original
                )

    def test_missing_historical_revision_never_falls_back_to_head(self):
        with (
            patch.object(TARGET, "AUTHORITY_REVISION", "0" * 40),
            self.assertRaisesRegex(
                SystemExit, "historical publisher Git source unavailable"
            ),
        ):
            TARGET.read_historical_publisher_source("publisher_transport.py")


if __name__ == "__main__":
    unittest.main()
