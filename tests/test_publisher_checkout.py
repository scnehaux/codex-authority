from __future__ import annotations

from hashlib import sha1
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_publisher_proof_checkout", ROOT / "scripts/verify_publisher_proof.py"
)
assert SPEC is not None and SPEC.loader is not None
PROOF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROOF)


class PublisherCheckoutTests(unittest.TestCase):
    def test_clean_checkout_preserves_proof_bytes_with_autocrlf(self) -> None:
        # Exercise a real Git checkout, not Python-side newline normalization.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = {
                key: value
                for key, value in os.environ.items()
                if not key.upper().startswith("GIT_")
            }

            def git(*args: str) -> None:
                subprocess.run(
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
                    check=True,
                    env=env,
                    capture_output=True,
                )

            git("init", "--quiet")
            git("config", "core.autocrlf", "true")
            git("config", "core.safecrlf", "false")
            attributes = ROOT / ".gitattributes"
            if attributes.exists():
                (root / ".gitattributes").write_bytes(attributes.read_bytes())
            paths = []
            for name in PROOF.CURRENT_PUBLISHER_FILES:
                relative = Path("integrations/github-app-publisher") / name
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
                paths.append(path)
            git("add", "--all")
            git(
                "-c",
                "user.name=Checkout Test",
                "-c",
                "user.email=checkout-test@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "checkout fixture",
            )
            for path in paths:
                path.unlink()
            git("checkout-index", "--all", "--force")
            for path in paths:
                with self.subTest(source=path.name):
                    self.assertEqual(
                        PROOF.git_blob_sha(path),
                        PROOF.CURRENT_PUBLISHER_FILES[path.name],
                    )
                    self.assertNotIn(b"\r\n", path.read_bytes())
            git("diff", "--exit-code")

    def test_blob_hash_matches_exact_regular_file_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.py"
            raw = b"value = 1\n"
            path.write_bytes(raw)
            expected = sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
            self.assertEqual(PROOF.git_blob_sha(path), expected)

    def test_blob_hash_still_detects_crlf_and_source_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.py"
            path.write_bytes(b"value = 1\n")
            expected = PROOF.git_blob_sha(path)
            for changed in (b"value = 1\r\n", b"value = 2\n"):
                with self.subTest(content=changed):
                    path.write_bytes(changed)
                    self.assertNotEqual(PROOF.git_blob_sha(path), expected)

    def test_blob_hash_rejects_missing_or_nonregular_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in (root, root / "missing.py"):
                with self.subTest(path=path):
                    with self.assertRaisesRegex(SystemExit, "publisher source missing"):
                        PROOF.git_blob_sha(path)


if __name__ == "__main__":
    unittest.main()
