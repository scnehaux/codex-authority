from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "governance/evidence/provider-enforcement-001.json"


class ProviderEnforcementEvidenceTests(unittest.TestCase):
    def test_negative_proof_is_exact_and_conservative(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["schema_version"], 1)
        self.assertEqual(
            evidence["kind"],
            "codex-provider-enforcement-negative-proof-evidence",
        )
        self.assertEqual(evidence["repository"], "scnehaux/codex")

        activation = evidence["activation"]
        self.assertEqual(activation["ruleset_id"], 23193929)
        self.assertEqual(activation["ruleset_name"], "main-governance")
        self.assertEqual(activation["enforcement"], "active")
        self.assertIs(activation["main_protected"], True)
        self.assertEqual(activation["bypass_actors"], [])
        self.assertEqual(activation["current_user_can_bypass"], "never")
        self.assertEqual(
            activation["required_status_checks"],
            [
                {"context": "Governance Qualification"},
                {
                    "context": "Codex Governance Authority",
                    "integration_id": 4864946,
                },
            ],
        )

        proof = evidence["negative_proof"]
        self.assertEqual(proof["pull_request"], 20)
        self.assertIs(proof["draft"], False)
        self.assertEqual(proof["state_at_observation"], "open")
        self.assertIs(proof["mergeable"], True)
        self.assertEqual(proof["mergeable_state"], "blocked")
        self.assertEqual(proof["changed_files"], [".gitignore"])
        self.assertEqual(
            proof["required_candidate_check"]["conclusion"],
            "success",
        )
        self.assertIs(proof["external_authority_check_present"], False)
        self.assertEqual(proof["reviews"], 0)
        self.assertEqual(proof["review_threads"], 0)
        self.assertIs(proof["closed_without_merge"], True)

        claims = evidence["claims"]
        self.assertIs(claims["provider_ruleset_live"], True)
        self.assertIs(
            claims["missing_external_authority_merge_denial_proven"],
            True,
        )
        self.assertIs(claims["wrong_source_authority_rejection_proven"], False)
        self.assertIs(claims["deletion_enforcement_proven"], False)
        self.assertIs(claims["non_fast_forward_enforcement_proven"], False)
        self.assertIs(
            claims["privileged_governance_maintenance_path_proven"],
            False,
        )
        self.assertIs(claims["effective_enforcement_proven"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
