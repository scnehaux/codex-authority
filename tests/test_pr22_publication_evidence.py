from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "governance" / "evidence" / "pr22-bootstrap-publication-001.json"


class Pr22BootstrapPublicationEvidenceTests(unittest.TestCase):
    def test_exact_provider_and_candidate_binding_remain_conservative(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["kind"], "codex-pr22-bootstrap-publication-evidence")
        self.assertEqual(data["candidate"]["pull_request"], 22)
        self.assertEqual(data["candidate"]["head_sha"], "eaa5b41cd84fcc77fd1ff464120d4be83c57d1cd")
        self.assertEqual(data["candidate"]["merge_commit_sha"], "d835991afe6ada47a66d012a3ddc2c4350cd9ff8")
        self.assertEqual(data["publication"]["check_run_id"], 105581555853)
        self.assertEqual(data["publication"]["check_context"], "Codex Governance Authority")
        self.assertEqual(data["publication"]["app"], {
            "id": 4864946, "slug": "scnehaux-codex-authority", "owner": "scnehaux"
        })
        self.assertEqual(data["publication"]["status"], "completed")
        self.assertEqual(data["publication"]["conclusion"], "success")
        self.assertTrue(data["publication"]["token_revoked"])
        self.assertTrue(data["provider_enforcement"]["merge_completed"])
        self.assertEqual(data["provider_enforcement"]["ruleset_id"], 23193929)
        self.assertEqual(data["provider_enforcement"]["required_check_integration_id"], 4864946)
        self.assertFalse(data["claims"]["privileged_governance_maintenance_path_proven"])
        self.assertFalse(data["claims"]["effective_enforcement_proven"])


if __name__ == "__main__":
    unittest.main()
