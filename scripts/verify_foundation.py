from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "governance/authority.json"
PROMOTION = ROOT / "governance/promotion.json"
PROTECTION = ROOT / "governance/repository-protection.json"
SECRET_SCANNING = ROOT / "governance/secret-scanning.json"
RULESET = ROOT / "governance/github-main-ruleset.json"
SECRET_WORKFLOW = ROOT / ".github/workflows/secret-scan.yml"
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
    secret_scanning = load_object(SECRET_SCANNING)
    ruleset = load_object(RULESET)

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
        "schema_version": 2,
        "default_branch": "main",
        "provider_projection": "governance/github-main-ruleset.json",
        "required": {
            "changes_via_pull_request": True,
            "required_checks": ["Authority Foundation", "Secret Scan"],
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

    expected_secret_scanning = {
        "schema_version": 1,
        "control": "trufflehog-oss",
        "required_check_context": "Secret Scan",
        "implementation": {
            "action_repository": "trufflesecurity/trufflehog",
            "action_revision": "363923b901c911a9164f50b6c423f47c15372b1c",
            "scanner_version": "3.97.4",
            "workflow": ".github/workflows/secret-scan.yml",
        },
        "coverage": {
            "pull_request": True,
            "push_default_branch": True,
            "scheduled_full_history_scan": True,
        },
        "failure_policy": {
            "findings_block": True,
            "scan_errors_block": True,
            "self_update_disabled": True,
            "credentials_required": False,
        },
        "publisher_prerequisite": {
            "required": True,
            "proven": False,
            "evidence": None,
        },
    }
    if secret_scanning != expected_secret_scanning:
        raise SystemExit("secret-scanning contract drifted")

    expected_ruleset = {
        "name": "authority-main-protection",
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {
            "ref_name": {
                "include": ["~DEFAULT_BRANCH"],
                "exclude": [],
            }
        },
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {"type": "required_linear_history"},
            {
                "type": "pull_request",
                "parameters": {
                    "allowed_merge_methods": ["squash"],
                    "dismiss_stale_reviews_on_push": True,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_approving_review_count": 0,
                    "required_review_thread_resolution": True,
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [
                        {"context": "Authority Foundation"},
                        {"context": "Secret Scan"},
                    ],
                    "strict_required_status_checks_policy": True,
                },
            },
        ],
    }
    if ruleset != expected_ruleset:
        raise SystemExit("GitHub main ruleset projection drifted")

    workflow = SECRET_WORKFLOW.read_text(encoding="utf-8")
    required_workflow_fragments = (
        "name: Secret Scan",
        "permissions:\n  contents: read",
        "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
        "persist-credentials: false",
        "trufflesecurity/trufflehog@363923b901c911a9164f50b6c423f47c15372b1c",
        'version: "3.97.4"',
        'extra_args: "--fail-on-scan-errors"',
    )
    if any(fragment not in workflow for fragment in required_workflow_fragments):
        raise SystemExit("secret-scanning workflow pin or fail-closed contract drifted")
    if "${{ secrets." in workflow:
        raise SystemExit("secret-scanning pull-request workflow must not consume repository secrets")

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

    print("[PASS] authority foundation and pre-publisher security invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
