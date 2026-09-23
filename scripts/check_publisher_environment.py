from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path, PurePath
import sys

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER_ROOT = ROOT / "integrations/github-app-publisher"


def _load_resolver():
    # Reuse current development source pins; historical proof stays revision-bound.
    spec = importlib.util.spec_from_file_location(
        "_publisher_preflight_proof", ROOT / "scripts/verify_publisher_proof.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("proof-verifier-unavailable")
    proof = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proof)
    for name, expected in proof.CURRENT_PUBLISHER_FILES.items():
        if proof.git_blob_sha(PUBLISHER_ROOT / name) != expected:
            raise RuntimeError("publisher-source-mismatch")
    sys.path.insert(0, str(PUBLISHER_ROOT))
    try:
        import publisher_transport
    finally:
        sys.path.pop(0)
    return publisher_transport.default_key_path


def inspect_environment() -> dict:
    """Read-only diagnosis, never an approval, permit, activation, or launcher.

    Resolve the existing publisher's default location lexically. Do not open,
    stat, inspect permissions on, or print that location; no key is accessed.
    The inspected environment is THIS process, not a future child environment.
    """
    checks = []

    def add(name: str, code: str | None = None) -> None:
        checks.append(
            {"check": name, "status": "blocked" if code else "pass", "code": code}
        )

    add(
        "python-runtime",
        None if sys.version_info >= (3, 13) else "python-3.13-required",
    )
    try:
        resolve = _load_resolver()
    except (Exception, SystemExit):
        add("publisher-source-integrity", "publisher-source-unverified")
    else:
        add("publisher-source-integrity")
        try:
            location = resolve()
            if not isinstance(location, PurePath):
                add("default-location-resolution", "invalid-location-type")
            elif (
                not location.is_absolute()
                or ".." in location.parts
                or any(ord(char) < 32 or ord(char) == 127 for char in str(location))
            ):
                add("default-location-resolution", "noncanonical-default-location")
            else:
                add("default-location-resolution")
        except RuntimeError:
            add("default-location-resolution", "home-directory-unresolvable")
        except Exception:
            add("default-location-resolution", "default-location-resolution-failed")
    return {
        "schema_version": 1,
        "kind": "codex-publisher-environment-preflight",
        "scope": "current-process-environment-only",
        "status": "pass"
        if all(item["status"] == "pass" for item in checks)
        else "blocked",
        "checks": checks,
        "boundaries": {
            "credential_accessed": False,
            "credential_existence_or_permissions_checked": False,
            "network_requests": 0,
            "publisher_invoked": False,
            "activation_modified": False,
            "publication_authorized": False,
        },
        "unassessed": [
            "execution-tool-authorization",
            "future-launcher-environment",
            "credential-existence-permissions-and-validity",
            "publisher-dependencies",
            "candidate-qualification-and-freshness",
            "governed-activation-and-publication",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline environment diagnosis only; no credential or publication access."
    )
    parser.parse_args(argv)
    report = inspect_environment()
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
