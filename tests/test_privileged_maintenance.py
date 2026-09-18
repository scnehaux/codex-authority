from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codex_authority import privileged as target  # noqa: E402
from codex_authority.model import (  # noqa: E402
    AuthorityDecision,
    CandidateRef,
    CandidateSnapshot,
    RuntimeDecisionEnvelope,
)

BASE = "1" * 40
HEAD = "2" * 40


def mapping() -> dict:
    return {
        "contract_version": 1,
        "kind": target.ATTESTATION_KIND,
        "candidate": {
            "repository": target.CANDIDATE_REPOSITORY,
            "pull_request": 22,
            "base_sha": BASE,
            "head_sha": HEAD,
            "changed_files": ["governance/scm/enforcement-policy.yaml"],
        },
        "decision": "pass",
        "scope": target.ATTESTATION_SCOPE,
        "authority": {
            "repository": target.AUTHORITY_REPOSITORY,
            "default_branch": target.AUTHORITY_DEFAULT_BRANCH,
            "mode": target.ATTESTATION_MODE,
        },
        "claims": {
            "candidate_code_executed": False,
            "credentials_used": False,
            "exact_candidate_binding": True,
        },
    }


def load_attestation() -> target.PrivilegedValidationAttestation:
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / f"{HEAD}.json"
        path.write_text(json.dumps(mapping()), encoding="utf-8")
        return target.PrivilegedValidationAttestation.load(path)


def envelope(
    reasons: tuple[str, ...] = ("privileged-validation-missing",),
    changed: tuple[str, ...] | None = None,
) -> RuntimeDecisionEnvelope:
    files = (
        ("governance/scm/enforcement-policy.yaml",)
        if changed is None
        else changed
    )
    return RuntimeDecisionEnvelope(
        snapshot=CandidateSnapshot(
            repository=target.CANDIDATE_REPOSITORY,
            pull_request=22,
            base_sha=BASE,
            head_sha=HEAD,
            state="open",
            changed_files=files,
        ),
        decision=AuthorityDecision.FAIL,
        reasons=reasons,
        runtime_source_revision=target.runtime_adapter.RUNTIME_SOURCE_REVISION,
        evaluator_source_revision=target.runtime_adapter.EVALUATOR_SOURCE_REVISION,
        source_identity_verified=True,
        facts_collected_independently=True,
        candidate_code_executed=False,
        credentials_used=False,
    )


class PrivilegedMaintenanceTests(unittest.TestCase):
    def test_attestation_is_exact_and_digest_is_stable(self):
        attestation = load_attestation()
        self.assertEqual(attestation.candidate.pull_request, 22)
        self.assertEqual(attestation.candidate.head_sha, HEAD)
        self.assertEqual(
            attestation.changed_files,
            ("governance/scm/enforcement-policy.yaml",),
        )
        self.assertEqual(len(attestation.digest), 64)
        self.assertEqual(attestation.digest, attestation.digest)

    def test_privilege_only_failure_can_be_resolved(self):
        attestation = load_attestation()
        request = CandidateRef(target.CANDIDATE_REPOSITORY, 22, HEAD)
        result = attestation.authorize(request, envelope())
        self.assertEqual(result.decision, AuthorityDecision.PASS)
        self.assertEqual(result.reasons, ())
        self.assertTrue(result.source_identity_verified)
        self.assertTrue(result.facts_collected_independently)
        self.assertFalse(result.candidate_code_executed)
        self.assertFalse(result.credentials_used)

    def test_non_privilege_failure_cannot_be_overridden(self):
        attestation = load_attestation()
        request = CandidateRef(target.CANDIDATE_REPOSITORY, 22, HEAD)
        with self.assertRaises(target.PrivilegedMaintenanceError) as error:
            attestation.authorize(
                request,
                envelope(reasons=("candidate-qualification-failed",)),
            )
        self.assertEqual(error.exception.code, "attestation-scope")

    def test_changed_file_drift_is_rejected(self):
        attestation = load_attestation()
        request = CandidateRef(target.CANDIDATE_REPOSITORY, 22, HEAD)
        with self.assertRaises(target.PrivilegedMaintenanceError) as error:
            attestation.authorize(
                request,
                envelope(changed=("governance/github/authority-binding.yaml",)),
            )
        self.assertEqual(error.exception.code, "attestation-snapshot")

    def test_checked_in_policy_is_disarmed_with_permanent_runtime_promoted(self):
        policy = target.load_maintenance_policy(
            ROOT / "governance" / "privileged-maintenance.json"
        )
        self.assertEqual(policy["state"], "permanent-runtime")
        self.assertFalse(policy["bootstrap"]["enabled"])
        self.assertIsNone(policy["bootstrap"]["candidate"])
        self.assertEqual(
            policy["permanent_runtime"],
            {
                "owner_repository": "scnehaux/codex",
                "state": "promoted",
                "attestation_read": "public-read-only",
            },
        )
        self.assertFalse(
            policy["claims"]["privileged_governance_maintenance_path_proven"]
        )
        self.assertFalse(policy["claims"]["effective_enforcement_proven"])


if __name__ == "__main__":
    unittest.main()
