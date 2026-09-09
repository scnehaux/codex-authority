from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "governance/authority.json"
PROMOTION = ROOT / "governance/promotion.json"
FORBIDDEN_SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks"}


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return value


def main() -> int:
    authority = load_object(AUTHORITY)
    promotion = load_object(PROMOTION)

    expected_authority = {
        "schema_version": 1,
        "candidate_repository": "scnehaux/codex",
        "authority_check_context": "Codex Governance Authority",
        "github_app_id": 4864946,
        "execution": {
            "location": "external",
            "candidate_code_execution": False,
        },
        "trust": {
            "candidate_may_select_effective_revision": False,
            "candidate_may_auto_deploy_authority": False,
            "credentials_may_be_stored_in_repository": False,
        },
    }
    if authority != expected_authority:
        raise SystemExit("authority foundation contract drifted")

    expected_promotion = {
        "schema_version": 1,
        "state": "foundation",
        "effective_authority_revision": None,
        "publisher": {
            "enabled": False,
            "live_proven": False,
        },
        "deployment": {
            "automatic_from_main": False,
            "automatic_from_candidate": False,
        },
        "enforcement": {
            "effective": False,
        },
    }
    if promotion != expected_promotion:
        raise SystemExit("promotion foundation contract advanced prematurely")

    secret_like = [
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and path.suffix.lower() in FORBIDDEN_SECRET_SUFFIXES
    ]
    if secret_like:
        raise SystemExit("credential-like files are forbidden: " + ", ".join(secret_like))

    print("[PASS] authority foundation invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
