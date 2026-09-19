from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "prepare_provider_acceptance", ROOT / "scripts" / "prepare_provider_acceptance.py")
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)
REVISION = "1" * 40
RUN = "20260920t040000z-1234abcd"


def snapshot():
    return {
        "id": 23193929, "name": "main-governance", "target": "branch",
        "source_type": "Repository", "source": "scnehaux/codex", "enforcement": "active",
        "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [
            {"type": "deletion"}, {"type": "non_fast_forward"},
            {"type": "required_linear_history"},
            {"type": "pull_request", "parameters": {
                "required_approving_review_count": 0, "dismiss_stale_reviews_on_push": True,
                "require_code_owner_review": False, "require_last_push_approval": False,
                "required_review_thread_resolution": True, "allowed_merge_methods": ["squash"],
                "require_extra_approval_for_unattributed_changes": True,
            }},
            {"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": True, "do_not_enforce_on_create": False,
                "required_status_checks": [{"context": "Governance Qualification"},
                    {"context": "Codex Governance Authority", "integration_id": 4864946}],
            }},
        ],
    }


class ProviderAcceptancePlanTests(unittest.TestCase):
    def plan(self, data=None, run=RUN):
        return target.prepare(target.canonical(snapshot() if data is None else data), REVISION, run)

    def test_synthetic_fixture_is_not_live_evidence(self):
        plan = self.plan()
        self.assertEqual(plan["state"], "planned-not-executed")
        self.assertTrue(all(value is False for value in plan["claims"].values()))
        self.assertIsNone(plan["target"]["repository_id"])
        self.assertIn("independent-reviewer-for-stale-approval", plan["pending"])

    def test_full_mirror_preserves_all_rules_and_extra_provider_fields(self):
        data = snapshot()
        before = deepcopy(data)
        plan = self.plan(data)
        mirror = plan["exact_mirror"]["payload"]
        self.assertEqual(mirror["rules"], data["rules"])
        self.assertEqual(mirror["conditions"], data["conditions"])
        self.assertEqual(mirror["bypass_actors"], [])
        self.assertEqual(data, before)
        self.assertTrue(plan["exact_mirror"]["app_installation_must_not_be_widened"])

    def test_payload_deep_copy_cannot_mutate_source(self):
        source = snapshot()
        payload = target.make_payload(source, name="fixture", selector="~DEFAULT_BRANCH",
                                      types=target.RULE_TYPES)
        payload["rules"][3]["parameters"]["allowed_merge_methods"].append("merge")
        self.assertEqual(source["rules"][3]["parameters"]["allowed_merge_methods"], ["squash"])

    def test_isolation_is_explicitly_not_full_equivalence(self):
        plan = self.plan()
        for experiment in plan["isolation_experiments"]:
            self.assertEqual(experiment["scope"], "control-isolation-not-full-equivalence")
            self.assertEqual(len(experiment["payload"]["rules"]), 1)
            self.assertEqual(len(experiment["omitted_rule_types"]), 4)
            selector = experiment["payload"]["conditions"]["ref_name"]["include"]
            self.assertNotIn("~DEFAULT_BRANCH", selector)
            self.assertEqual(experiment["payload"]["bypass_actors"], [])

    def test_production_cannot_be_selected_as_output_repository(self):
        plan = self.plan()
        self.assertTrue(plan["target"]["repository"].startswith("scnehaux/codex-provider-proof-"))
        self.assertNotEqual(plan["target"]["repository"], "scnehaux/codex")
        self.assertFalse(plan["cleanup"]["production_mutations_allowed"])
        self.assertFalse(plan["target"]["reuse_existing"])

    def test_bad_run_ids_are_rejected(self):
        for value in ("main", "../codex", "20260920t040000z-1234abcd/x", "", RUN + "\n"):
            with self.subTest(value=value), self.assertRaises(target.PlanError):
                self.plan(run=value)

    def test_bad_revisions_are_rejected(self):
        for value in ("main", True, "x" * 40, "a" * 39, "a" * 40 + "\n"):
            with self.subTest(value=value), self.assertRaises(target.PlanError):
                target.prepare(target.canonical(snapshot()), value, RUN)

    def test_identity_bypass_and_selector_drift_are_rejected(self):
        mutations = [
            {"id": True}, {"id": 1}, {"source": "scnehaux/codex-authority"},
            {"source_type": "Organization"}, {"name": "other"}, {"target": "tag"},
            {"enforcement": "evaluate"}, {"bypass_actors": [{"actor_id": 1}]},
            {"conditions": {"ref_name": {"include": ["~ALL"], "exclude": []}}},
        ]
        for change in mutations:
            data = snapshot()
            data.update(change)
            with self.subTest(change=change), self.assertRaises(target.PlanError):
                self.plan(data)

    def test_missing_extra_duplicate_and_unknown_rule_are_rejected(self):
        for mode in ("missing", "extra", "duplicate", "unknown"):
            data = snapshot()
            if mode == "missing": data["rules"].pop()
            if mode == "extra": data["rules"].append({"type": "creation"})
            if mode == "duplicate": data["rules"][0] = data["rules"][1]
            if mode == "unknown": data["rules"][0] = {"type": "unknown"}
            with self.subTest(mode=mode), self.assertRaises(target.PlanError):
                self.plan(data)

    def test_review_policy_changes_require_a_new_plan_review(self):
        for field, value in (("required_approving_review_count", False),
                             ("required_approving_review_count", 1),
                             ("dismiss_stale_reviews_on_push", 1),
                             ("required_review_thread_resolution", False),
                             ("allowed_merge_methods", ["merge"])):
            data = snapshot()
            data["rules"][3]["parameters"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(target.PlanError):
                self.plan(data)

    def test_wrong_source_and_check_drift_are_rejected(self):
        mutations = [
            lambda p: p.update(strict_required_status_checks_policy=1),
            lambda p: p.update(do_not_enforce_on_create=True),
            lambda p: p["required_status_checks"][1].update(integration_id=True),
            lambda p: p["required_status_checks"][1].update(integration_id=15368),
            lambda p: p["required_status_checks"][1].update(context="other"),
            lambda p: p["required_status_checks"][1].update(context=[]),
        ]
        for mutate in mutations:
            data = snapshot()
            mutate(data["rules"][4]["parameters"])
            with self.assertRaises(target.PlanError): self.plan(data)

    def test_malformed_parameters_are_rejected(self):
        for index in (3, 4):
            data = snapshot()
            data["rules"][index]["parameters"] = []
            with self.assertRaises(target.PlanError): self.plan(data)

    def test_json_rejects_duplicate_nonfinite_nonobject_and_oversize(self):
        for raw in (b'{"id":1,"id":2}', b'{"value":NaN}', b'[]', b'', b' ' * (target.LIMIT + 1)):
            with self.assertRaises(target.PlanError): target.decode(raw)

    def test_plan_output_is_exclusive_and_deterministic(self):
        plan = self.plan()
        self.assertEqual(plan, self.plan())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            target.write_new(path, plan)
            with self.assertRaises(FileExistsError): target.write_new(path, plan)
            self.assertEqual(json.loads(path.read_bytes()), plan)


if __name__ == "__main__":
    unittest.main()
