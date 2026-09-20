"""Read-only tests for selected historical data. Never invokes Git or provider APIs.

These tests validate integrity and consistency, not independent provenance,
provider behavior today, or overall Phase 10 acceptance.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "governance" / "evidence"
MANIFEST = "provider-evidence-package-001.json"
QUALIFICATION = "provider-qualification-negative-001.json"
RUNTIME = "provider-qualification-negative-001.runtime.json"
TRANSPORT = "provider-git-transport-001.json"
ARTIFACTS = {QUALIFICATION, RUNTIME, TRANSPORT}
MAX_BYTES = 1_048_576
SOURCE = "107f0dc53e873ef6d24a9f12cd28da7348f79331"
AUTHORITY = "11d13b4ec7b9dd0051116d73e33d785f3d2651fa"
HEAD = "e1b58e898fe2428faebbc8f5aba2941fc7ef9b1e"
WIRE_DIGEST = "11fc9baebef84a6f56fe4aca4e7ef2b02a90c635ece797f40dec6fbe1e48f811"
FIXTURE = "scnehaux/codex-provider-proof-20260920t144552z-7ef80d36"
FIXTURE_ID = 1378442804
BASELINE = "7710e75a5e45e16bfbbefc15104d4c143519a23a"
CHILD = "3aaa08ce7bec866520177057897c1cb98bdded82"


def strict_json(raw: bytes) -> object:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("invalid evidence byte length")

    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate evidence key")
            value[key] = item
        return value

    def reject_constant(value):
        raise ValueError("non-finite evidence number")

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("non-finite evidence number")
        return number

    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant,
                      parse_float=finite_float)


def canonical(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii") + b"\n"


def manifest_paths(manifest: dict) -> list[str]:
    entries = manifest["artifacts"]
    names = [entry["path"] for entry in entries]
    if len(names) != len(ARTIFACTS) or set(names) != ARTIFACTS:
        raise ValueError("unexpected, duplicated or unsafe artifact path")
    return names


def instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("unqualified timestamp")
    return parsed


class ProviderEvidencePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = strict_json((EVIDENCE / MANIFEST).read_bytes())
        cls.q = strict_json((EVIDENCE / QUALIFICATION).read_bytes())
        cls.runtime = strict_json((EVIDENCE / RUNTIME).read_bytes())
        cls.g = strict_json((EVIDENCE / TRANSPORT).read_bytes())
        cls.wire = strict_json(cls.runtime["runtime_result_json"].encode("utf-8"))
        cls.results = {r["outcome"]["label"]: r for r in cls.g["results"]}

    def test_duplicate_keys_are_rejected_at_any_depth(self):
        for raw in (b'{"x":1,"x":2}', b'{"parent":{"x":1,"x":2}}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                strict_json(raw)

    def test_invalid_nonfinite_and_oversized_json_is_rejected(self):
        for raw in (b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}',
                    b'{"x":1e999}', b'{bad', b'', b' ' * (MAX_BYTES + 1)):
            with self.subTest(raw=raw[:40]), self.assertRaises(ValueError):
                strict_json(raw)

    def test_manifest_exact_target_and_not_integrated_status(self):
        m = self.manifest
        self.assertEqual(m["schema_version"], 1)
        self.assertEqual(m["target_repository"], "scnehaux/codex-authority")
        self.assertEqual(m["target_baseline"], AUTHORITY)
        self.assertEqual(m["integration_state"], "not_applied_to_repository")
        self.assertEqual(set(manifest_paths(m)), ARTIFACTS)

    def test_manifest_rejects_unknown_duplicate_and_traversal_paths(self):
        for path in ("../README.md", "/tmp/data.json", "C:\\data.json", QUALIFICATION):
            m = deepcopy(self.manifest)
            m["artifacts"][1]["path"] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                manifest_paths(m)

    def test_every_selected_artifact_matches_canonical_manifest_digest(self):
        for entry in self.manifest["artifacts"]:
            data = strict_json((EVIDENCE / entry["path"]).read_bytes())
            self.assertEqual(sha256(canonical(data)).hexdigest(), entry["canonical_data_sha256"])

    def test_outer_json_line_endings_do_not_change_data_digest(self):
        for entry in self.manifest["artifacts"]:
            raw = (EVIDENCE / entry["path"]).read_bytes()
            crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            self.assertEqual(sha256(canonical(strict_json(crlf))).hexdigest(), entry["canonical_data_sha256"])

    def test_modified_observation_changes_digest(self):
        changed = deepcopy(self.q)
        changed["merge_attempt"]["http_status"] = 200
        expected = next(e["canonical_data_sha256"] for e in self.manifest["artifacts"] if e["path"] == QUALIFICATION)
        self.assertNotEqual(sha256(canonical(changed)).hexdigest(), expected)

    def test_serialization_profile_is_explicit(self):
        self.assertEqual(self.manifest["serialization"], {
            "profile": "sorted-compact-ascii-json-plus-lf-v1", "sort_keys": True,
            "separators": [",", ":"], "ensure_ascii": True, "allow_nan": False, "trailing_lf": True,
        })

    def test_embedded_wire_matches_original_captured_sha256(self):
        wire = self.runtime["runtime_result_json"].encode("utf-8")
        self.assertEqual(sha256(wire).hexdigest(), WIRE_DIGEST)
        self.assertEqual(self.runtime["runtime_result_sha256"], WIRE_DIGEST)
        self.assertEqual(self.q["issuer"]["runtime_result_sha256"], WIRE_DIGEST)
        self.assertEqual(self.manifest["runtime_wire"]["captured_sha256"], WIRE_DIGEST)

    def test_runtime_wire_line_endings_are_not_silently_normalized(self):
        wire = self.runtime["runtime_result_json"].encode("utf-8")
        self.assertIn(b"\r\n", wire)
        self.assertNotEqual(sha256(wire.replace(b"\r\n", b"\n")).hexdigest(), WIRE_DIGEST)

    def test_runtime_failure_is_bound_to_same_candidate_and_sources(self):
        r = self.runtime["decision_record"]
        self.assertEqual(self.runtime["authority_service_source_revision"], AUTHORITY)
        self.assertEqual(r["decision"], "fail")
        self.assertEqual(r["reasons"], ["candidate-qualification-failed"])
        self.assertEqual(r["request"], {"repository": "scnehaux/codex", "pull_request": 25, "head_sha": HEAD})
        self.assertEqual(r["snapshot"]["base_sha"], SOURCE)
        self.assertEqual(r["snapshot"]["changed_files"], ["provider-qualification-negative.md"])
        self.assertEqual(r["source"]["runtime_source_revision"], self.runtime["runtime_package"]["source_revision"])
        self.assertEqual(self.wire["candidate_sha"], HEAD)
        self.assertEqual(self.wire["base_sha"], SOURCE)

    def test_runtime_retains_original_failure_without_privilege_override(self):
        w = self.wire
        self.assertEqual(w["governance_decision"], "fail")
        self.assertEqual(w["original_evaluation"]["governance_decision"], "fail")
        self.assertEqual(w["evaluator_result"], w["original_evaluation"]["evaluator_result"])
        self.assertEqual(w["failure_reasons"], ["candidate-qualification-failed"])
        self.assertEqual(w["privileged_validation_evidence"], {"status": "not_required"})

    def test_runtime_source_dependencies_match_recorded_package(self):
        blobs = self.runtime["runtime_package"]["blobs"]
        self.assertEqual(len(blobs), 5)
        self.assertEqual(self.wire["source_dependencies"]["blobs"],
                         {k: v for k, v in blobs.items() if k != "attested_runtime.py"})
        self.assertEqual(self.runtime["runtime_package"]["entrypoint"], "attested_runtime.py")
        self.assertEqual(self.wire["source_dependencies"]["evaluator_revision"],
                         self.runtime["decision_record"]["source"]["evaluator_source_revision"])

    def test_runtime_neither_executes_candidate_nor_claims_publication(self):
        for key in ("candidate_code_executed", "credentials_used", "publish_enabled",
                    "authority_binding_advanced", "effective_enforcement_proven"):
            self.assertIs(self.wire[key], False)
        self.assertIs(self.wire["facts_collected_independently"], True)

    def test_real_github_actions_check_matches_qualification_capture(self):
        c = self.wire["qualification_evidence"]
        self.assertEqual(c["check_run_id"], 106095659722)
        self.assertEqual(c["app_id"], 15368)
        self.assertEqual(c["app_slug"], "github-actions")
        self.assertEqual(c["head_sha"], HEAD)
        self.assertEqual(c["conclusion"], "failure")
        self.assertIs(c["source_verified"], True)
        self.assertEqual(c["check_run_id"], self.q["workflow"]["job_id"])

    def test_failure_step_is_not_misreported_as_full_framework_test(self):
        workflow = self.q["workflow"]
        by_name = {s["name"]: s["conclusion"] for s in workflow["steps_through_qualification"]}
        self.assertEqual(workflow["conclusion"], "failure")
        self.assertEqual(by_name["Validate document formatting"], "failure")
        self.assertEqual(by_name["Install deterministic Python toolchain"], "success")
        self.assertEqual(by_name["Validate GitHub reference-provider projection"], "success")
        self.assertEqual(by_name["Qualify governance control plane"], "skipped")
        self.assertIs(self.q["claims"]["full_framework_suite_ran_on_candidate"], False)

    def test_merge_denial_is_exact_head_normal_method_and_two_unmet_checks(self):
        a = self.q["merge_attempt"]
        self.assertEqual(a["body"], {"merge_method": "squash", "sha": HEAD})
        self.assertEqual(a["endpoint"], "repos/scnehaux/codex/pulls/25/merge")
        self.assertEqual(a["method"], "PUT")
        self.assertEqual(a["http_status"], 405)
        self.assertIn("1 expected and 1 failing", a["message"])
        self.assertIs(a["qualification_only_causal_isolation"], False)

    def test_main_unchanged_across_time_ordered_refusal(self):
        before = self.q["main_observation"]["before"]
        after = self.q["main_observation"]["after"]
        a = self.q["merge_attempt"]
        self.assertEqual(before["sha"], SOURCE)
        self.assertEqual(after["sha"], SOURCE)
        self.assertLess(instant(before["time"]), instant(a["intent_time"]))
        self.assertLess(instant(a["intent_time"]), instant(a["response_time"]))
        self.assertLess(instant(a["response_time"]), instant(after["time"]))
        for value in (before, after, a):
            self.assertTrue(value["request_id"])

    def test_failure_has_no_receipt_permit_or_authority_check(self):
        issuer = self.q["issuer"]
        self.assertEqual(issuer["decision"], "fail")
        self.assertIs(issuer["evidence_recorded"], True)
        for key in ("permit_issued", "receipt_issued", "authority_check_published"):
            self.assertIs(issuer[key], False)
        self.assertIs(self.q["cleanup"]["closed_without_merge"], True)

    def test_git_transcript_scope_is_only_id_bound_fixture(self):
        self.assertEqual(self.g["transport"], "git-receive-pack-over-https")
        for r in self.g["results"]:
            i = r["intent"]
            self.assertEqual(i["fixture"], FIXTURE)
            self.assertEqual(i["fixture_id"], FIXTURE_ID)
            self.assertIn("https://github.com/" + FIXTURE + ".git", i["arguments"])
            self.assertNotIn("https://github.com/scnehaux/codex.git", i["arguments"])
            self.assertLess(instant(i["time"]), instant(r["outcome"]["time"]))
        self.assertEqual(self.g["claims"]["production_ref_mutations"], 0)

    def test_direct_push_positive_and_negative_share_update(self):
        yes, no = (self.results[k] for k in ("01-control-update", "02-direct-default-denial"))
        self.assertEqual(yes["intent"]["target"], no["intent"]["target"])
        self.assertEqual(yes["intent"]["before"], no["intent"]["before"])
        self.assertEqual(yes["outcome"]["exit_code"], 0)
        self.assertEqual(no["outcome"]["exit_code"], 1)
        self.assertEqual(no["outcome"]["after"], BASELINE)
        self.assertIn("GH013", no["outcome"]["stderr"])
        self.assertIn("Changes must be made through a pull request", no["outcome"]["stderr"])
        self.assertIs(no["intent"]["force_with_explicit_lease"], False)

    def test_force_positive_and_negative_share_non_fast_forward_target(self):
        yes, no = (self.results[k] for k in ("09-force-positive", "10-force-negative"))
        for r in (yes, no):
            self.assertEqual(r["intent"]["before"], CHILD)
            self.assertEqual(r["intent"]["target"], BASELINE)
            self.assertIs(r["intent"]["force_with_explicit_lease"], True)
            lease = "--force-with-lease=" + r["intent"]["ref"] + ":" + CHILD
            self.assertIn(lease, r["intent"]["arguments"])
        self.assertEqual(yes["outcome"]["exit_code"], 0)
        self.assertIn("(forced update)", yes["outcome"]["stdout"])
        self.assertEqual(yes["outcome"]["after"], BASELINE)
        self.assertEqual(no["outcome"]["exit_code"], 1)
        self.assertEqual(no["outcome"]["after"], CHILD)
        self.assertIn("Cannot force-push to this branch", no["outcome"]["stderr"])

    def test_force_control_creation_is_separate_from_forced_update(self):
        r = self.results["08-new-force-control"]
        self.assertIsNone(r["intent"]["before"])
        self.assertEqual(r["outcome"]["after"], CHILD)
        self.assertIn("[new branch]", r["outcome"]["stdout"])
        self.assertNotEqual(r["outcome"]["label"], "09-force-positive")

    def test_hang_and_inconsistent_deletion_have_no_proof_credit(self):
        excluded = self.g["excluded_attempts"]
        self.assertEqual(excluded["03-control-force"]["state"], "UNKNOWN_LOCAL_PROCESS_HANG")
        self.assertIs(excluded["03-control-force"]["original_client_exit_known"], False)
        self.assertEqual(excluded["11-delete-positive"]["exit_code"], 1)
        self.assertIsNone(excluded["11-delete-positive"]["after"])
        for label, value in excluded.items():
            self.assertIs(value["proof_credit"], False)
            self.assertNotIn(label, self.results)

    def test_unknown_api_responses_are_not_successful_denials(self):
        unknowns = self.g["api_unknowns"]
        self.assertEqual(len(unknowns), 4)
        for value in unknowns:
            self.assertIs(value["proof_credit"], False)
            self.assertTrue(value.get("http_status") is None)
        self.assertEqual(unknowns[2]["state"], "UNKNOWN_TIMEOUT")

    def test_tool_blocked_sequence_is_not_provider_evidence(self):
        record = self.g["final_native_deletion_sequence"]
        self.assertEqual(record["state"], "BLOCKED_BY_TOOL_SAFETY_NOT_SENT")
        self.assertIs(record["proof_credit"], False)
        self.assertIs(record["provider_denial_observed"], False)
        self.assertIs(self.g["claims"]["native_default_deletion_proven"], False)

    def test_archive_and_zero_open_prs_have_recorded_identity_and_request_ids(self):
        c = self.g["cleanup"]
        self.assertEqual(c["archive"]["repository_id"], FIXTURE_ID)
        self.assertEqual(c["archive"]["full_name"], FIXTURE)
        self.assertIs(c["archive"]["archived"], True)
        self.assertEqual(c["open_prs"]["body"], [])
        self.assertIs(c["repository_deleted"], False)
        for value in (c["archive"], c["open_prs"]):
            self.assertEqual(value["http_status"], 200)
            self.assertTrue(value["request_id"])

    def test_selected_projections_are_not_claimed_as_full_raw_captures(self):
        self.assertIs(self.q["source"]["complete_original_capture_included"], False)
        self.assertEqual(self.q["source"]["original_request_outcome_pairs_retained_locally"], 10)
        self.assertIs(self.g["source"]["complete_original_capture_included"], False)
        self.assertEqual(self.g["source"]["original_api_pairs_retained_locally"], 80)

    def test_acceptance_and_repository_ci_remain_unclaimed(self):
        self.assertEqual(self.manifest["acceptance_proposal"]["state"], "Proposed")
        self.assertIs(self.manifest["acceptance_proposal"]["acceptance_not_implied_by_packaging"], True)
        for value in self.manifest["claims"].values():
            self.assertIs(value, False)
        for data in (self.q, self.g):
            self.assertIs(data["claims"]["effective_enforcement_proven"], False)

    def test_test_module_has_no_network_or_process_import(self):
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        self.assertLessEqual(imported, {"__future__", "ast", "copy", "datetime", "hashlib", "json", "math", "pathlib", "unittest"})


if __name__ == "__main__":
    unittest.main()
