"""Offline evidence/lifecycle checks; no network, publisher, or live mutations."""
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "governance/evidence/phase10-completion-001.json"
HEAD = "07a393a24c29d19de8da703c49e22a1ce30f6b51"
MERGE = "915d24e861ededec0c516e9b9a95b4ca83796651"
BASE = "107f0dc53e873ef6d24a9f12cd28da7348f79331"


def read(path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate key")
            value[key] = item
        return value
    def reject(value):
        raise ValueError("nonfinite value")
    raw = path.read_bytes()
    if not 0 < len(raw) <= 128000:
        raise ValueError("size")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode() + b"\n"


def require(value):
    if not value:
        raise ValueError("completion invariant")


def validate(d):
    require(type(d["schema_version"]) is int and d["schema_version"] == 1)
    require(d["kind"] == "codex-phase10-governed-completion")
    candidate = d["candidate"]
    require(candidate["repository"] == "scnehaux/codex" and candidate["pull_request"] == 26)
    require((candidate["base_sha"], candidate["head_sha"], candidate["merge_commit_sha"]) == (BASE, HEAD, MERGE))
    require(candidate["changed_files"] == ["PLAN.md", "ROADMAP.md"] and candidate["merge_method"] == "squash")
    require(d["acceptance"]["method"] == "REC-D-018")
    require(d["acceptance"]["decision_record"].endswith("/issues/28#issuecomment-5752319468"))
    publication = d["publication"]
    journal = publication["journal"]
    require(journal["status"] == "published" and journal["token_revoked"] is True)
    require(journal["candidate"]["head_sha"] == HEAD and journal["candidate"]["base_sha"] == BASE)
    require(journal["check_run_id"] == 106143120366)
    require(sha256(canonical(journal)).hexdigest() == publication["journal_canonical_sha256"])
    require(journal["permit_digest"] == d["bundle"]["permit_digest"])
    check = publication["provider_read"]["selected_body"]
    require(check["id"] == journal["check_run_id"] and check["head_sha"] == HEAD)
    require(check["name"] == "Codex Governance Authority" and check["status"] == "completed" and check["conclusion"] == "success")
    require(check["app"] == {"id": 4864946, "slug": "scnehaux-codex-authority", "owner": "scnehaux"})
    require(publication["duplicate_publication_attempted"] is False)
    require(publication["qualification_check_run_id"] == 106142550431)
    post = d["postmerge"]
    pr = post["reads"]["pull"]["selected_body"]
    require(pr["merged"] is True and pr["state"] == "closed" and pr["head_sha"] == HEAD and pr["merge_commit_sha"] == MERGE)
    require(datetime.fromisoformat(check["completed_at"].replace("Z", "+00:00")) <= datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00")))
    observe = post["observer"]["evidence"]
    require(observe["observed_revision"] == MERGE and observe["drift"] == [] and observe["drift_state"] == "aligned" and observe["enforcement_state"] == "active")
    rule = post["reads"]["ruleset"]["selected_body"]
    require(rule["id"] == 23193929 and rule["bypass_actors"] == [] and rule["enforcement"] == "active")
    effective = post["reads"]["effective"]["selected_body"]
    require(all(r["ruleset_id"] == 23193929 for r in effective))
    require([{"type": r["type"], **({"parameters": r["parameters"]} if r.get("parameters") is not None else {})} for r in effective] == rule["rules"])
    disarm = d["disarm"]
    config = disarm["configuration_in_this_change"]
    require(config["state"] == "disabled" and config["activation"] is None)
    require(disarm["privileged_bootstrap_enabled"] is False and disarm["review_bootstrap_active"] is True)
    require(sha256(canonical(config)).hexdigest() == disarm["canonical_data_sha256"])
    require(d["claims"]["effective_enforcement_proven"] is True and d["claims"]["phase10_status_finalized"] is True)
    require(all(d["claims"][k] is False for k in ("full_mirror_equivalence_proven", "independent_human_review_proven", "native_git_default_deletion_observed", "governance_1_0_ready", "standing_publication_capability")))
    return d


class Phase10CompletionTests(unittest.TestCase):
    def setUp(self):
        self.data = read(FILE)

    def test_governed_chain_and_source_identity(self):
        validate(self.data)

    def test_old_head_cannot_be_reused(self):
        self.data["candidate"]["head_sha"] = "5bcff612189cf36fb66d771259f6964c3667884b"
        with self.assertRaises(ValueError): validate(self.data)

    def test_wrong_app_or_conclusion_rejected(self):
        for field, value in (("app", {"id": 15368}), ("conclusion", "failure")):
            d = deepcopy(self.data); d["publication"]["provider_read"]["selected_body"][field] = value
            with self.assertRaises(ValueError): validate(d)

    def test_mutated_journal_or_token_not_revoked_rejected(self):
        for field, value in (("token_revoked", False), ("permit_digest", "0" * 64)):
            d = deepcopy(self.data); d["publication"]["journal"][field] = value
            with self.assertRaises(ValueError): validate(d)

    def test_merged_boolean_required(self):
        self.data["postmerge"]["reads"]["pull"]["selected_body"]["merged"] = False
        with self.assertRaises(ValueError): validate(self.data)

    def test_observer_revision_or_drift_cannot_be_ignored(self):
        for field, value in (("observed_revision", BASE), ("drift_state", "drifted")):
            d = deepcopy(self.data); d["postmerge"]["observer"]["evidence"][field] = value
            with self.assertRaises(ValueError): validate(d)

    def test_reactivation_and_numeric_true_rejected(self):
        d = deepcopy(self.data); d["disarm"]["configuration_in_this_change"]["state"] = "candidate-proof"
        with self.assertRaises(ValueError): validate(d)
        d = deepcopy(self.data); d["claims"]["effective_enforcement_proven"] = 1
        with self.assertRaises(ValueError): validate(d)

    def test_recorded_disarm_is_disabled_without_freezing_future_activations(self):
        config = self.data["disarm"]["configuration_in_this_change"]
        self.assertEqual(config["state"], "disabled")
        self.assertIsNone(config["activation"])
        self.assertEqual(self.data["disarm"]["path"], "governance/controlled-publication.json")
        self.assertFalse(self.data["disarm"]["privileged_bootstrap_enabled"])
        self.assertFalse(config["claims"]["effective_enforcement_proven"])

    def test_historical_acceptance_checkpoint_retained(self):
        prior = read(ROOT / self.data["acceptance"]["path"])
        self.assertTrue(prior["claims"]["effective_enforcement_proven"])
        self.assertFalse(prior["claims"]["phase10_status_finalized"])
        self.assertEqual(prior["codex_revision"], BASE)
        self.assertEqual(len(prior["rows"]), 10)

    def test_residual_limits_and_next_phase_are_explicit(self):
        self.assertGreaterEqual(len(self.data["limits"]), 5)
        self.assertEqual(self.data["next_planned_slice"], "11.1 Declarative Framework Contract")
        for key in ("full_mirror_equivalence_proven", "independent_human_review_proven", "governance_1_0_ready"):
            d = deepcopy(self.data); d["claims"][key] = True
            with self.assertRaises(ValueError): validate(d)


if __name__ == "__main__":
    unittest.main()
