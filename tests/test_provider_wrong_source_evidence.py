from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "governance/evidence/provider-wrong-source-001.json"


class ProviderWrongSourceEvidenceTests(unittest.TestCase):
    def test_wrong_source_success_remains_provider_blocked(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["schema_version"], 1)
        self.assertEqual(
            evidence["kind"],
            "codex-provider-wrong-source-authority-rejection-evidence",
        )
        self.assertEqual(evidence["repository"], "scnehaux/codex")
        self.assertEqual(evidence["evidence_id"], "provider-wrong-source-001")

        activation = evidence["activation"]
        self.assertEqual(activation["ruleset_id"], 23193929)
        self.assertEqual(activation["ruleset_name"], "main-governance")
        self.assertEqual(activation["enforcement"], "active")
        self.assertEqual(activation["bypass_actors"], [])
        self.assertEqual(activation["current_user_can_bypass"], "never")
        self.assertEqual(
            activation["required_external_context"],
            "Codex Governance Authority",
        )
        self.assertEqual(activation["required_external_integration_id"], 4864946)

        proof = evidence["negative_proof"]
        self.assertEqual(proof["pull_request"], 21)
        self.assertIs(proof["draft"], False)
        self.assertEqual(proof["state_at_observation"], "open")
        self.assertIs(proof["mergeable"], True)
        self.assertEqual(proof["mergeable_state"], "blocked")
        self.assertEqual(proof["changed_files"], [".gitignore"])
        self.assertTrue(proof["candidate_checks"])
        self.assertTrue(
            all(item["conclusion"] == "success" for item in proof["candidate_checks"])
        )

        status = proof["wrong_source_status"]
        self.assertEqual(status["status_id"], 54096778055)
        self.assertEqual(status["context"], "Codex Governance Authority")
        self.assertEqual(status["state"], "success")
        self.assertEqual(status["creator_login"], "anshacerbia2")
        self.assertEqual(status["source_type"], "user-commit-status")
        self.assertEqual(status["expected_authority_integration_id"], 4864946)
        self.assertIs(status["bound_authority_source_satisfied"], False)
        self.assertEqual(proof["reviews"], 0)
        self.assertEqual(proof["review_threads"], 0)
        self.assertIs(proof["closed_without_merge"], True)

        claims = evidence["claims"]
        self.assertIs(claims["provider_ruleset_live"], True)
        self.assertIs(
            claims["missing_external_authority_merge_denial_proven"],
            True,
        )
        self.assertIs(claims["external_authority_source_binding_configured"], True)
        self.assertIs(claims["wrong_source_authority_rejection_proven"], True)
        self.assertIs(claims["deletion_enforcement_proven"], False)
        self.assertIs(claims["non_fast_forward_enforcement_proven"], False)
        self.assertIs(
            claims["privileged_governance_maintenance_path_proven"],
            False,
        )
        self.assertIs(claims["effective_enforcement_proven"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
