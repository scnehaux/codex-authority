from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ATTESTATION_PREFIX = "governance/privileged-validations/"


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        raise SystemExit("could not inspect privileged-attestation history") from None


def main() -> int:
    base = _git("merge-base", "origin/main", "HEAD")
    output = _git(
        "diff",
        "--name-status",
        base,
        "HEAD",
        "--",
        ATTESTATION_PREFIX,
    )
    for line in output.splitlines():
        fields = line.split("\t")
        if len(fields) < 2:
            raise SystemExit("malformed privileged-attestation history record")
        status, paths = fields[0], fields[1:]
        json_paths = [path for path in paths if path.endswith(".json")]
        if json_paths and status != "A":
            raise SystemExit("existing privileged attestation JSON records are immutable")

    print("[PASS] privileged attestation JSON changes are append-only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
