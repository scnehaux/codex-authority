from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "governance/authority.json"
PROMOTION = ROOT / "governance/promotion.json"
PROTECTION = ROOT / "governance/repository-protection.json"
FORBIDDEN_SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks"}


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return value


def main() -> int:
    authority = load_object(AUTHORITY)
    promotion = load_object(PROMOTION)
    protection = load_object(PROTECTION)

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
        "schema_version": 2,
        "state": "foundation",
        "source_identity": {
            "codex_evaluator_source_revision": None,
            "codex_runtime_source_revision": None,
            "authority_service_source_revision": None,
            "publisher_source_revision": None,
            "deployment_artifact_digest": None,
        },
        "publisher": {
            "enabled": False,
            "live_proven": False,
            "publication_permit_required": True,
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

    expected_protection = {
        "schema_version": 1,
        "default_branch": "main",
        "required": {
            "changes_via_pull_request": True,
            "required_checks": ["Authority Foundation"],
            "force_push_allowed": False,
            "deletion_allowed": False,
            "linear_history_required": True,
            "allowed_merge_methods": ["squash"],
        },
        "provider_state": {
            "enforced": False,
            "evidence": None,
        },
    }
    if protection != expected_protection:
        raise SystemExit("repository protection desired state drifted")

    secret_like = [
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and path.suffix.lower() in FORBIDDEN_SECRET_SUFFIXES
    ]
    if secret_like:
        raise SystemExit(
            "credential-like files are forbidden: " + ", ".join(secret_like)
        )

    legacy_adr = ROOT / "docs/decisions"
    if legacy_adr.exists():
        raise SystemExit(
            "implementation-local decision notes must not masquerade as Codex ADR artifacts"
        )

    print("[PASS] authority foundation hardening invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
