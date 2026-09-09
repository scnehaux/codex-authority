from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codex_authority.policy import load_authority_policy  # noqa: E402


class AuthorityPolicyTests(unittest.TestCase):
    def load_mutation(self, mutate):
        data = json.loads(
            (ROOT / "governance/authority.json").read_text(encoding="utf-8")
        )
        mutate(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "authority.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return load_authority_policy(path)

    def test_repository_policy_loads_exact_foundation_binding(self):
        policy = load_authority_policy(ROOT / "governance/authority.json")
        self.assertEqual(policy.candidate_repository, "scnehaux/codex")
        self.assertEqual(policy.authority_check_context, "Codex Governance Authority")
        self.assertEqual(policy.github_app_id, 4864946)
        self.assertEqual(policy.execution_location, "external")
        self.assertFalse(policy.candidate_code_execution)
        self.assertFalse(policy.candidate_may_select_effective_revision)
        self.assertFalse(policy.candidate_may_auto_deploy_authority)
        self.assertFalse(policy.credentials_may_be_stored_in_repository)

    def test_invalid_app_identity_fails_closed(self):
        with self.assertRaises(ValueError):
            self.load_mutation(lambda data: data.__setitem__("github_app_id", 0))

    def test_candidate_execution_fails_closed(self):
        with self.assertRaises(ValueError):
            self.load_mutation(
                lambda data: data["execution"].__setitem__(
                    "candidate_code_execution", True
                )
            )

    def test_non_external_execution_fails_closed(self):
        with self.assertRaises(ValueError):
            self.load_mutation(
                lambda data: data["execution"].__setitem__("location", "candidate")
            )

    def test_candidate_selected_revision_fails_closed(self):
        with self.assertRaises(ValueError):
            self.load_mutation(
                lambda data: data["trust"].__setitem__(
                    "candidate_may_select_effective_revision", True
                )
            )

    def test_authority_context_drift_fails_closed(self):
        with self.assertRaises(ValueError):
            self.load_mutation(
                lambda data: data.__setitem__(
                    "authority_check_context", "Connectivity Probe"
                )
            )

    def test_unknown_policy_field_fails_closed(self):
        with self.assertRaises(ValueError):
            self.load_mutation(lambda data: data.__setitem__("extra", "unexpected"))


if __name__ == "__main__":
    unittest.main()
