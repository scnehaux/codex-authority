from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / "governance/publisher.json"
PROMOTION = ROOT / "governance/promotion.json"
CONFIG = ROOT / "integrations/github-app-publisher/config.json"
PUBLISHER = ROOT / "integrations/github-app-publisher/github_app_publisher.py"
CONTRACT = ROOT / "integrations/github-app-publisher/publisher_contract.py"
TRANSPORT = ROOT / "integrations/github-app-publisher/publisher_transport.py"
REQUIREMENTS = ROOT / "integrations/github-app-publisher/requirements.txt"
PUBLICATION = ROOT / "src/codex_authority/publication.py"
FORBIDDEN_SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks"}
RUNTIME_REVISION = "cbd64f78c8f72f28880d4673729a796b249d8eae"
EVALUATOR_REVISION = "23b05a855419b86b61b0c9266805bb66b143c366"


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return value


def main() -> int:
    governance = load_object(GOVERNANCE)
    promotion = load_object(PROMOTION)
    config = load_object(CONFIG)

    expected_governance = {
        "schema_version": 1,
        "provider": "github",
        "candidate_repository": "scnehaux/codex",
        "check_context": "Codex Governance Authority",
        "authority_app": {
            "app_id": 4864946,
            "installation_id": 159870521,
            "client_id": "Iv23li8znPY4yr7chvFD",
            "expected_source_binding": "integration_id",
        },
        "permit": {
            "contract_version": 1,
            "kind": "codex-governance-publication-permit",
            "required": True,
            "success_only": True,
            "durable_evidence_required": True,
        },
        "source": {
            "expected_codex_runtime_revision": RUNTIME_REVISION,
            "expected_codex_evaluator_revision": EVALUATOR_REVISION,
            "authority_service_source_revision": None,
            "publisher_source_revision": None,
            "publisher_source_blobs": None,
        },
        "execution": {
            "location": "external",
            "exported_copy_required": True,
            "candidate_code_execution": False,
            "evaluation_credentials_allowed": False,
            "credentials_from_external_secret_boundary": True,
            "api_root": "https://api.github.com",
            "redirects_allowed": False,
            "check_post_retries": 0,
        },
        "activation": {
            "write_mode": "disabled",
            "proof_head_sha": None,
            "proof_permit_digest": None,
            "live_proven": False,
            "evidence": None,
            "effective_enforcement_claimed": False,
        },
    }
    if governance != expected_governance:
        raise SystemExit("publisher governance contract drifted or advanced prematurely")

    expected_config = {
        "config_version": 1,
        "app_id": 4864946,
        "installation_id": 159870521,
        "client_id": "Iv23li8znPY4yr7chvFD",
        "repository": "scnehaux/codex",
        "check_context": "Codex Governance Authority",
        "permit_kind": "codex-governance-publication-permit",
        "expected_runtime_source_revision": RUNTIME_REVISION,
        "expected_evaluator_source_revision": EVALUATOR_REVISION,
        "expected_authority_service_source_revision": None,
        "publisher_source_revision": None,
        "publisher_source_blobs": None,
        "write_mode": "disabled",
        "proof_head_sha": None,
        "proof_permit_digest": None,
        "live_proven": False,
    }
    if config != expected_config:
        raise SystemExit("publisher implementation config drifted or enabled prematurely")

    if promotion.get("publisher") != {
        "enabled": False,
        "live_proven": False,
        "publication_permit_required": True,
    }:
        raise SystemExit("repository promotion contract enabled publisher prematurely")
    if promotion.get("source_identity", {}).get("publisher_source_revision") is not None:
        raise SystemExit("publisher source revision must remain unpromoted in the staging slice")

    requirements = REQUIREMENTS.read_text(encoding="utf-8").splitlines()
    if requirements != ["PyJWT==2.13.0", "cryptography==50.0.1"]:
        raise SystemExit("publisher credential dependencies must remain exactly pinned")

    publisher_source = "\n".join(
        path.read_text(encoding="utf-8") for path in (PUBLISHER, CONTRACT, TRANSPORT)
    )
    required_publisher_fragments = (
        'API_ROOT = "https://api.github.com"',
        'CHECK_CONTEXT = "Codex Governance Authority"',
        'APP_ID = 4864946',
        'INSTALLATION_ID = 159870521',
        'EXPECTED_RUNTIME_SOURCE_REVISION = "' + RUNTIME_REVISION + '"',
        'EXPECTED_EVALUATOR_SOURCE_REVISION = "' + EVALUATOR_REVISION + '"',
        'PUBLISHER_FILES = ("github_app_publisher.py", "publisher_contract.py", "publisher_transport.py")',
        '"publisher-disabled"',
        '"publisher-checkout"',
        '"publisher-blob-mismatch"',
        '"operator-confirmation"',
        '"proof-permit"',
        '"candidate-identity"',
        '"check-response"',
        '"token_revoked": True',
        '"effective_enforcement_proven": False',
    )
    if any(fragment not in publisher_source for fragment in required_publisher_fragments):
        raise SystemExit("publisher fail-closed/source-binding contract drifted")
    if (
        "secrets." in publisher_source
        or "GITHUB_TOKEN" in publisher_source
        or "Authorization: Bearer" in publisher_source
    ):
        raise SystemExit("publisher source must not contain repository-secret bindings or embedded credentials")

    publication = PUBLICATION.read_text(encoding="utf-8")
    required_permit_fragments = (
        'PERMIT_KIND = "codex-governance-publication-permit"',
        'CANDIDATE_REPOSITORY = "scnehaux/codex"',
        'CHECK_CONTEXT = "Codex Governance Authority"',
        'EXPECTED_INTEGRATION_ID = 4864946',
        'if outcome.decision is not AuthorityDecision.PASS',
        'snapshot.state != "open"',
        'evidence_recorded is not True',
    )
    if any(fragment not in publication for fragment in required_permit_fragments):
        raise SystemExit("publication-permit gate drifted")

    publisher_root = PUBLISHER.parent
    forbidden = [
        path.relative_to(ROOT).as_posix()
        for path in publisher_root.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SECRET_SUFFIXES
    ]
    if forbidden:
        raise SystemExit("credential-like publisher files are forbidden: " + ", ".join(forbidden))

    print("[PASS] staged publication permit and disabled publisher invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
