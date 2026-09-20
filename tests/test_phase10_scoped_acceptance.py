"""Offline validation of scoped acceptance, not live execution or permission issuance."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "governance/evidence/phase10-acceptance-001.json"
P = ROOT / "governance/evidence/phase10-final-preflight-001.json"
CODEX = "107f0dc53e873ef6d24a9f12cd28da7348f79331"
BASE = "251451c98eda2332674384cd56f5f02a0c42e032"
DECISION = "https://github.com/scnehaux/codex-authority/issues/28#issuecomment-5752319468"


def parse(raw):
    if not 0 < len(raw) < 128000:
        raise ValueError("size")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate")
            result[key] = value
        return result
    def reject(value):
        raise ValueError("nonfinite")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode() + b"\n"


def validate(a, p):
    def need(condition):
        if not condition:
            raise ValueError("acceptance invariant")
    need(a["schema_version"] == 1 and type(a["schema_version"]) is int)
    need(a["kind"] == "codex-phase10-scoped-acceptance")
    need(a["state"] == "accepted-reference-provider-scope")
    need(a["codex_revision"] == p["codex_revision"] == CODEX)
    need(a["authority_revision"] == p["authority_revision"] == BASE)
    need(a["decision"]["record"] == DECISION and a["decision"]["owner_response"] == "oke gas")
    need(a["decision"]["recommendation"] == "REC-D-018" and a["decision"]["method_status"] == "Accepted")
    need(a["decision"]["independent_human_acceptance_claimed"] is False)
    need(a["scope"]["repository"] == "scnehaux/codex" and a["scope"]["authority_app_id"] == 4864946)
    need(a["scope"]["obligation_waiver"] is False and a["scope"]["future_states_automatically_accepted"] is False)
    need(a["preflight"]["path"] == "governance/evidence/phase10-final-preflight-001.json")
    need(a["preflight"]["canonical_data_sha256"] == sha256(canonical(p)).hexdigest())
    need(len(a["rows"]) == 10)
    need(all(type(r["id"]) is int and r["id"] == i for i, r in enumerate(a["rows"], 1)))
    need(all(r["assessment"] == "accepted-under-rec-d-018" and r["limit"] for r in a["rows"]))
    need(a["claims"]["effective_enforcement_proven"] is True)
    need(a["claims"]["all_ten_obligations_accepted_in_declared_scope"] is True)
    need(all(a["claims"][key] is False for key in ("phase10_status_finalized",
        "full_mirror_equivalence_proven", "independent_human_review_proven",
        "native_git_default_deletion_observed", "new_live_destructive_tests_performed",
        "publication_capability_granted")))
    reads = p["provider_reads"]
    body = lambda key: reads[key]["selected_body"]
    need(body("repository")["permissions"]["admin"] is True and body("repository")["id"] == 1283007458)
    need(body("main")["sha"] == CODEX)
    rule = body("ruleset")
    need(rule["id"] == 23193929 and rule["enforcement"] == "active" and rule["bypass_actors"] == [])
    need(rule["conditions"] == {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}})
    effective = [{"type": r["type"], **({"parameters": r["parameters"]} if r.get("parameters") is not None else {})}
                 for r in body("effective")]
    need(effective == rule["rules"] and all(r["ruleset_id"] == rule["id"] for r in body("effective")))
    need([r["id"] for r in body("inherited")] == [23193929])
    need(reads["legacy"]["http_status"] == 404 and body("legacy")["message"] == "Branch not protected")
    need(body("reviewer")["permission"] == "read")
    need(len(p["fixtures"]) == 3 and all(f["repository"]["archived"] is True and f["open_prs"] == [] for f in p["fixtures"]))
    observed = parse(p["observer"]["stdout"])
    need(p["observer"]["exit_code"] == 0 and observed["drift"] == [] and observed["drift_state"] == "aligned")
    need(observed["observed_revision"] == CODEX and observed["enforcement_state"] == "active")
    policies = p["authority_policies"]
    need(policies["governance/privileged-maintenance.json"]["data"]["bootstrap"]["enabled"] is False)
    need(policies["governance/controlled-publication.json"]["data"]["activation"] is None)
    need(p["assessment"]["complete_for_declared_scope"] is True)
    return a


class ScopedAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.a, self.p = parse(A.read_bytes()), parse(P.read_bytes())

    def test_source_bound_acceptance(self):
        validate(self.a, self.p)

    def test_owner_decision_required(self):
        self.a["decision"]["record"] = None
        with self.assertRaises(ValueError): validate(self.a, self.p)

    def test_method_is_not_a_waiver(self):
        self.a["scope"]["obligation_waiver"] = True
        with self.assertRaises(ValueError): validate(self.a, self.p)

    def test_missing_row_rejected(self):
        self.a["rows"].pop()
        with self.assertRaises(ValueError): validate(self.a, self.p)

    def test_boolean_row_id_rejected(self):
        self.a["rows"][0]["id"] = True
        with self.assertRaises(ValueError): validate(self.a, self.p)

    def test_mirror_and_independence_are_not_claimed(self):
        for key in ("full_mirror_equivalence_proven", "independent_human_review_proven", "publication_capability_granted"):
            a = deepcopy(self.a); a["claims"][key] = True
            with self.assertRaises(ValueError): validate(a, self.p)

    def test_numeric_true_rejected(self):
        self.a["claims"]["effective_enforcement_proven"] = 1
        with self.assertRaises(ValueError): validate(self.a, self.p)

    def test_preflight_digest_tampering_rejected(self):
        self.p["codex_revision"] = "0" * 40
        with self.assertRaises(ValueError): validate(self.a, self.p)

    def test_effective_drift_even_with_rehashed_record_rejected(self):
        self.p["provider_reads"]["effective"]["selected_body"].pop()
        self.a["preflight"]["canonical_data_sha256"] = sha256(canonical(self.p)).hexdigest()
        with self.assertRaises(ValueError): validate(self.a, self.p)

    def test_missing_admin_access_is_not_legacy_absence(self):
        self.p["provider_reads"]["legacy"]["http_status"] = 401
        self.a["preflight"]["canonical_data_sha256"] = sha256(canonical(self.p)).hexdigest()
        with self.assertRaises(ValueError): validate(self.a, self.p)

    def test_original_dossier_and_evidence_are_not_rewritten(self):
        old = parse((ROOT / self.a["dossier"]["path"]).read_bytes())
        self.assertIsNone(old["method"]["owner_decision"])
        self.assertFalse(old["claims"]["effective_enforcement_proven"])
        self.assertEqual(old["source_inventory"], self.a["dossier"]["source_inventory"])
        self.assertEqual([r["obligation"] for r in old["rows"]], [r["obligation"] for r in self.a["rows"]])
        for source in old["source_inventory"].values():
            data = parse((ROOT / source["path"]).read_bytes())
            self.assertFalse(data.get("claims", {}).get("effective_enforcement_proven", False))

    def test_component_claims_remain_local(self):
        for record in self.p["authority_policies"].values():
            self.assertIs(record["data"]["claims"]["effective_enforcement_proven"], False)
        self.assertEqual(len(self.a["invalidation_events"]), 5)

    def test_request_metadata_and_scope_limit_retained(self):
        for item in self.p["provider_reads"].values():
            self.assertEqual(item["method"], "GET")
            self.assertTrue(item["headers"].get("x-github-request-id"))
            self.assertTrue(item["started_at"] <= item["completed_at"])
        self.assertGreaterEqual(len(self.a["residual_limits"]), 5)

    def test_strict_json_and_checkout_representation(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.assertRaises(ValueError): parse(raw)
        self.assertEqual(parse(A.read_bytes().replace(b"\n", b"\r\n")), self.a)


if __name__ == "__main__":
    unittest.main()
