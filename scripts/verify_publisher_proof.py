from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path
import stat
import sys


ROOT = Path(__file__).resolve().parents[1]
PROOF_GOVERNANCE = ROOT / "governance/publisher-proof.json"
GENERIC_GOVERNANCE = ROOT / "governance/publisher.json"
PROMOTION = ROOT / "governance/promotion.json"
PUBLISHER_EVIDENCE = ROOT / "governance/evidence/publisher-live-001.json"
PUBLISHER_ROOT = ROOT / "integrations/github-app-publisher"
DEFAULT_CONFIG = PUBLISHER_ROOT / "config.json"
PROOF_CONFIG = PUBLISHER_ROOT / "proof-config.json"
PUBLISHER_FILES = {
    "github_app_publisher.py": "4ee2e9937b17bb157b702bcc8f6d10a33ca71e6c",
    "publisher_contract.py": "4b2ab8d9a5da6bda794586b43255688d7dc961fe",
    "publisher_transport.py": "03d54b7ea54296e17688eaa40a5ff0de9bbb61ca",
}
AUTHORITY_REVISION = "6b89e95b63fa000482a1c5cac82f22864a81eeeb"
RUNTIME_REVISION = "cbd64f78c8f72f28880d4673729a796b249d8eae"
EVALUATOR_REVISION = "23b05a855419b86b61b0c9266805bb66b143c366"
BASE_SHA = "b79f8c07d088820722b3644a396c89bf42fcd370"
HEAD_SHA = "a6ed1def64503ca57c647ce45937f887873aac6f"
PERMIT_DIGEST = "fa79155ddb243f3d03227205b0e5c8e93e154590acffce499475c1d8019cb3d7"
CHECK_RUN_ID = 103547296485
EVIDENCE_PATH = "governance/evidence/publisher-live-001.json"


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return value


def git_blob_sha(path: Path) -> str:
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise OSError
        raw = path.read_bytes()
    except OSError:
        raise SystemExit(f"publisher source missing: {path}") from None
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def main() -> int:
    proof = load_object(PROOF_GOVERNANCE)
    generic = load_object(GENERIC_GOVERNANCE)
    promotion = load_object(PROMOTION)
    evidence = load_object(PUBLISHER_EVIDENCE)
    default_config = load_object(DEFAULT_CONFIG)

    if PROOF_CONFIG.exists():
        raise SystemExit("candidate-proof config must be removed after live proof capture")

    expected_blobs = dict(PUBLISHER_FILES)
    expected_proof = {
        "schema_version": 1,
        "kind": "github-publisher-candidate-proof-result",
        "provider": "github",
        "repository": "scnehaux/codex",
        "pull_request": 17,
        "candidate": {
            "base_sha": BASE_SHA,
            "head_sha": HEAD_SHA,
        },
        "publication_permit": {
            "digest": PERMIT_DIGEST,
            "authority_service_source_revision": AUTHORITY_REVISION,
            "runtime_source_revision": RUNTIME_REVISION,
            "evaluator_source_revision": EVALUATOR_REVISION,
            "evidence_recorded": True,
        },
        "publisher": {
            "source_revision": AUTHORITY_REVISION,
            "source_blobs": expected_blobs,
            "check_context": "Codex Governance Authority",
            "app_id": 4864946,
            "installation_id": 159870521,
            "execution_location": "external",
            "exported_copy_required": True,
        },
        "activation": {
            "mode": "candidate-proof-completed",
            "generic_publisher_enabled": False,
            "live_proven": True,
            "proof_disarmed": True,
            "candidate_closed_without_merge": True,
            "evidence": EVIDENCE_PATH,
            "effective_enforcement_claimed": False,
        },
    }
    if proof != expected_proof:
        raise SystemExit("completed candidate-proof governance record drifted")

    expected_evidence = {
        "contract_version": 1,
        "kind": "scm-external-authority-publisher-evidence",
        "provider": "github",
        "repository": "scnehaux/codex",
        "evidence_id": "publisher-live-001",
        "authority": {
            "integration_id": 4864946,
            "check_context": "Codex Governance Authority",
            "expected_source_binding": "integration_id",
            "app_slug": "scnehaux-codex-authority",
            "app_owner": "scnehaux",
        },
        "publisher": {
            "execution_location": "external",
            "check_run_published": True,
            "source_verified": True,
            "exact_candidate_binding": True,
            "credentials_isolated": True,
            "candidate_code_executed": False,
            "check_run_id": CHECK_RUN_ID,
            "candidate_sha": HEAD_SHA,
            "conclusion": "success",
            "permit_digest": PERMIT_DIGEST,
            "authority_service_source_revision": AUTHORITY_REVISION,
            "publisher_source_revision": AUTHORITY_REVISION,
            "publisher_source_blobs": expected_blobs,
            "token_revoked": True,
        },
        "provider_observation": {
            "pull_request": 17,
            "base_sha": BASE_SHA,
            "check_status": "completed",
            "check_started_at": "2026-09-12T11:35:35Z",
            "check_completed_at": "2026-09-12T11:35:35Z",
            "candidate_closed_at": "2026-09-12T11:38:20Z",
            "candidate_closed_without_merge": True,
        },
        "claims": {
            "effective_enforcement_proven": False,
        },
    }
    if evidence != expected_evidence:
        raise SystemExit("publisher live evidence drifted")

    if not (
        default_config.get("write_mode") == "disabled"
        and default_config.get("expected_authority_service_source_revision") is None
        and default_config.get("publisher_source_revision") is None
        and default_config.get("publisher_source_blobs") is None
        and default_config.get("proof_head_sha") is None
        and default_config.get("proof_permit_digest") is None
        and default_config.get("live_proven") is False
    ):
        raise SystemExit("generic/default publisher must remain disabled")

    if generic.get("activation") != {
        "write_mode": "disabled",
        "proof_head_sha": None,
        "live_proven": False,
        "evidence": None,
        "effective_enforcement_claimed": False,
        "proof_permit_digest": None,
    }:
        raise SystemExit("generic publisher governance must remain unadvanced by candidate proof")

    if promotion.get("publisher") != {
        "enabled": False,
        "live_proven": False,
        "publication_permit_required": True,
    }:
        raise SystemExit("generic publisher promotion must remain unadvanced after candidate proof")
    if promotion.get("source_identity", {}).get("publisher_source_revision") is not None:
        raise SystemExit("generic publisher source must remain unpromoted after candidate proof")

    for name, expected in PUBLISHER_FILES.items():
        if git_blob_sha(PUBLISHER_ROOT / name) != expected:
            raise SystemExit(f"publisher source blob drifted after live proof: {name}")

    print("[PASS] live publisher proof is evidenced, disarmed, and generic publication remains disabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
