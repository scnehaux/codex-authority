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
PROTECTION_EVIDENCE = ROOT / "governance/evidence/provider-protection-001.json"
SECRET_SCAN_EVIDENCE = ROOT / "governance/evidence/secret-scan-001.json"
SECRET_WORKFLOW = ROOT / ".github/workflows/secret-scan.yml"
FORBIDDEN_SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks"}
GITHUB_ACTIONS_APP_ID = 15368
MAIN_EVIDENCE_SHA = "04aede7bda750a3b4507318985f638fc9a380ab7"


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
    protection_evidence = load_object(PROTECTION_EVIDENCE)
    secret_scan_evidence = load_object(SECRET_SCAN_EVIDENCE)

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

    expected_checks = [
        {"context": "Authority Foundation", "integration_id": GITHUB_ACTIONS_APP_ID},
        {"context": "Secret Scan", "integration_id": GITHUB_ACTIONS_APP_ID},
    ]
    expected_protection = {
        "schema_version": 3,
        "default_branch": "main",
        "provider_projection": "governance/github-main-ruleset.json",
        "required": {
            "changes_via_pull_request": True,
            "required_checks": expected_checks,
            "force_push_allowed": False,
            "deletion_allowed": False,
            "linear_history_required": True,
            "allowed_merge_methods": ["squash"],
            "required_approving_review_count": 0,
            "dismiss_stale_reviews_on_push": True,
            "require_last_push_approval": False,
            "require_review_thread_resolution": True,
            "require_extra_approval_for_unattributed_changes": False,
            "bypass_allowed": False,
        },
        "provider_state": {
            "enforced": True,
            "evidence": "governance/evidence/provider-protection-001.json",
        },
    }
    if protection != expected_protection:
        raise SystemExit("repository protection contract drifted")

    expected_secret_scanning = {
        "schema_version": 2,
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
            "proven": True,
            "evidence": "governance/evidence/secret-scan-001.json",
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
                    "require_extra_approval_for_unattributed_changes": False,
                    "required_approving_review_count": 0,
                    "required_review_thread_resolution": True,
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "do_not_enforce_on_create": False,
                    "required_status_checks": expected_checks,
                    "strict_required_status_checks_policy": True,
                },
            },
        ],
    }
    if ruleset != expected_ruleset:
        raise SystemExit("GitHub main ruleset projection drifted")

    provider_rules = protection_evidence.get("ruleset", {}).get("rules", {})
    if not (
        protection_evidence.get("schema_version") == 1
        and protection_evidence.get("kind") == "github-repository-ruleset-evidence"
        and protection_evidence.get("repository") == "scnehaux/codex-authority"
        and protection_evidence.get("observed_branch") == "main"
        and protection_evidence.get("observed_head_sha") == MAIN_EVIDENCE_SHA
        and protection_evidence.get("observed_branch_protected") is True
        and protection_evidence.get("ruleset", {}).get("id") == 22679415
        and protection_evidence.get("ruleset", {}).get("name") == "authority-main-protection"
        and protection_evidence.get("ruleset", {}).get("enforcement") == "active"
        and protection_evidence.get("ruleset", {}).get("default_branch_only") is True
        and protection_evidence.get("ruleset", {}).get("bypass_actors") == []
        and protection_evidence.get("ruleset", {}).get("current_user_can_bypass") == "never"
        and provider_rules.get("deletion_restricted") is True
        and provider_rules.get("non_fast_forward_restricted") is True
        and provider_rules.get("linear_history_required") is True
        and provider_rules.get("required_status_checks") == expected_checks
        and provider_rules.get("strict_required_status_checks_policy") is True
        and protection_evidence.get("claims", {}).get("provider_protection_proven") is True
        and protection_evidence.get("claims", {}).get("publisher_enabled") is False
        and protection_evidence.get("claims", {}).get("effective_governance_enforcement_claimed") is False
    ):
        raise SystemExit("provider-protection evidence is invalid")

    observed_checks = protection_evidence.get("required_check_observation")
    if not isinstance(observed_checks, list) or len(observed_checks) != 2:
        raise SystemExit("provider-protection evidence must observe both required checks")
    for observed, expected in zip(observed_checks, expected_checks, strict=True):
        if not (
            observed.get("context") == expected["context"]
            and observed.get("head_sha") == MAIN_EVIDENCE_SHA
            and observed.get("status") == "completed"
            and observed.get("conclusion") == "success"
            and observed.get("integration_id") == GITHUB_ACTIONS_APP_ID
            and observed.get("app_slug") == "github-actions"
            and observed.get("app_owner") == "github"
            and type(observed.get("check_run_id")) is int
            and observed["check_run_id"] > 0
        ):
            raise SystemExit("provider-protection required-check evidence is invalid")

    secret_workflow = secret_scan_evidence.get("workflow", {})
    secret_scanner = secret_scan_evidence.get("scanner", {})
    secret_claims = secret_scan_evidence.get("claims", {})
    if not (
        secret_scan_evidence.get("schema_version") == 1
        and secret_scan_evidence.get("kind") == "secret-scanning-live-evidence"
        and secret_scan_evidence.get("repository") == "scnehaux/codex-authority"
        and secret_scan_evidence.get("observed_head_sha") == MAIN_EVIDENCE_SHA
        and secret_workflow.get("name") == "Secret Scan"
        and secret_workflow.get("path") == ".github/workflows/secret-scan.yml"
        and secret_workflow.get("run_id") == 34391660155
        and secret_workflow.get("event") == "push"
        and secret_workflow.get("status") == "completed"
        and secret_workflow.get("conclusion") == "success"
        and secret_workflow.get("check_run_id") == 102601170463
        and secret_workflow.get("check_context") == "Secret Scan"
        and secret_workflow.get("source") == {
            "integration_id": GITHUB_ACTIONS_APP_ID,
            "app_slug": "github-actions",
            "app_owner": "github",
        }
        and secret_scanner.get("control") == "trufflehog-oss"
        and secret_scanner.get("action_repository") == "trufflesecurity/trufflehog"
        and secret_scanner.get("action_revision") == "363923b901c911a9164f50b6c423f47c15372b1c"
        and secret_scanner.get("scanner_version") == "3.97.4"
        and secret_scanner.get("credentials_required") is False
        and secret_scanner.get("fail_on_scan_errors") is True
        and secret_scanner.get("self_update_disabled") is True
        and secret_claims.get("live_control_proven") is True
        and secret_claims.get("publisher_prerequisite_satisfied") is True
        and secret_claims.get("full_history_schedule_configured") is True
        and secret_claims.get("full_history_schedule_execution_proven") is False
        and secret_claims.get("publisher_enabled") is False
    ):
        raise SystemExit("secret-scanning evidence is invalid")

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
        raise SystemExit("secret-scanning workflow must not consume repository secrets")

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

    print("[PASS] authority foundation and pre-publisher evidence invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
