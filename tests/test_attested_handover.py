from __future__ import annotations

import copy
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "integrations" / "github-app-publisher"))

from codex_authority import attested_contract as contract
from codex_authority import attested_handover as target
from codex_authority.adapters import attested_runtime as adapter
from codex_authority.model import AuthorityDecision, CandidateRef, RuntimeDecisionEnvelope
from codex_authority.policy import AuthorityPolicy
from codex_authority.evidence import EvidenceWriteError
import attested_preview
import publisher_contract

FIXTURE = ROOT / "tests" / "fixtures" / "attested-runtime-v2.json"
REQUEST = CandidateRef("scnehaux/codex", 220, "b" * 40)
RUNTIME_REVISION = "8" * 40
SERVICE_REVISION = "9" * 40
POLICY = AuthorityPolicy("scnehaux/codex", "Codex Governance Authority", 4864946,
                         "external", False, False, False, False)


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def missing(data: dict) -> dict:
    evidence = data["privileged_validation_evidence"]
    evidence.update(status="missing", blob_sha=None, raw_sha256=None, attestation_digest=None, record=None)
    original = data["original_evaluation"]
    data["evaluator_result"] = copy.deepcopy(original["evaluator_result"])
    data["runtime_failure_reasons"] = list(original["runtime_failure_reasons"])
    data["failure_reasons"] = data["evaluator_result"]["failure_reasons"] + data["runtime_failure_reasons"]
    data["governance_decision"] = "fail"
    return data


class SyntheticRuntime:
    """Test-only port. No independently promoted execution or GitHub observation."""
    def __init__(self, data: dict, revision: str = RUNTIME_REVISION):
        self.data = data
        self.package = adapter.RuntimePackage(revision, target.REVIEW_BLOB)
        self.result = None

    def evaluate(self, request):
        self.result = contract.AttestedResult.parse(contract.canonical(self.data), request)
        return RuntimeDecisionEnvelope(
            self.result.snapshot, self.result.decision, self.result.reasons,
            self.package.source_revision, contract.EVALUATOR_REVISION, True, True, False, False,
        )


def exercise_pipeline(data: dict, directory: Path, *, runtime_revision: str = RUNTIME_REVISION):
    evidence = directory / "decision.json"
    receipt = directory / "receipt.json"
    prepared = target._evaluate_and_prepare(
        REQUEST, SyntheticRuntime(data, runtime_revision), POLICY, SERVICE_REVISION, evidence, receipt,
    )
    if prepared.permit is None:
        return prepared, None
    permit_path = directory / "permit.json"
    # Test-only export after both writes returned; public production handover is disabled.
    permit_path.write_text(prepared.permit.to_json(), encoding="utf-8")
    report = attested_preview.preview_attested_permit(
        permit_path, evidence, receipt, expected_runtime_revision=runtime_revision,
        expected_authority_revision=SERVICE_REVISION,
    )
    return prepared, report


class AttestedContractTests(unittest.TestCase):
    def parse(self, data):
        return contract.AttestedResult.parse(contract.canonical(data), REQUEST)

    def test_fixture_is_synthetic_and_retains_original_failure(self):
        data = fixture()
        result = self.parse(data)
        self.assertEqual(result.decision, AuthorityDecision.PASS)
        self.assertEqual(result.to_mapping()["original_evaluation"]["governance_decision"], "fail")
        self.assertIn("Synthetic", data["notice"])
        copy_ = result.to_mapping()
        copy_["governance_decision"] = "fail"
        self.assertEqual(result.to_mapping()["governance_decision"], "pass")

    def test_missing_attestation_preserves_failure(self):
        result = self.parse(missing(fixture()))
        self.assertEqual(result.decision, AuthorityDecision.FAIL)
        self.assertEqual(set(result.reasons), contract.PRIVILEGE_BLOCKERS)

    def test_unprotected_pass_has_no_approval(self):
        data = fixture()
        data["privileged_validation_evidence"] = {"status": "not_required"}
        data["runtime_only_protected_mutations"] = []
        data["original_evaluation"]["runtime_failure_reasons"] = []
        data["original_evaluation"]["governance_decision"] = "pass"
        for evaluation in (data["original_evaluation"]["evaluator_result"], data["evaluator_result"]):
            evaluation.update(protected_mutations=[], requires_privileged_validation=False,
                              privileged_validation="not_required", failure_reasons=[], governance_decision="pass")
        self.assertEqual(self.parse(data).decision, AuthorityDecision.PASS)

    def test_runtime_only_protected_pass_uses_not_required_evaluator_fact(self):
        data = fixture()
        for evaluation in (data["original_evaluation"]["evaluator_result"], data["evaluator_result"]):
            evaluation.update(protected_mutations=[], requires_privileged_validation=False,
                              privileged_validation="not_required", failure_reasons=[], governance_decision="pass")
        self.assertEqual(self.parse(data).decision, AuthorityDecision.PASS)

    def test_failed_qualification_remains_failed_without_lookup(self):
        data = missing(fixture())
        data["privileged_validation_evidence"] = {"status": "not_attempted"}
        data["qualification_evidence"]["conclusion"] = "failure"
        for evaluation in (data["original_evaluation"]["evaluator_result"], data["evaluator_result"]):
            evaluation["candidate_qualification"] = "fail"
            evaluation["failure_reasons"].insert(0, "candidate-qualification-failed")
        data["failure_reasons"].insert(0, "candidate-qualification-failed")
        self.assertEqual(self.parse(data).decision, AuthorityDecision.FAIL)
        data["privileged_validation_evidence"] = fixture()["privileged_validation_evidence"]
        with self.assertRaises(contract.HandoverError):
            self.parse(data)

    def test_unknown_failure_cannot_be_authorized(self):
        data = missing(fixture())
        data["privileged_validation_evidence"] = {"status": "not_attempted"}
        for evaluation in (data["original_evaluation"]["evaluator_result"], data["evaluator_result"]):
            evaluation["failure_reasons"].append("future-governance-failure")
        data["failure_reasons"] = data["evaluator_result"]["failure_reasons"] + data["runtime_failure_reasons"]
        self.assertEqual(self.parse(data).decision, AuthorityDecision.FAIL)
        data["privileged_validation_evidence"] = fixture()["privileged_validation_evidence"]
        with self.assertRaises(contract.HandoverError):
            self.parse(data)

    def test_top_level_identity_and_claim_drift(self):
        mutations = {"repository": "other/repo", "pull_request": 221, "base_sha": "0"*40,
                     "candidate_sha": "d"*40, "schema_version": True, "kind": "legacy",
                     "status": "runtime_evaluation_complete", "facts_collected_independently": 1,
                     "new_field": False}
        mutations.update({key: 0 for key in contract.FALSE_CLAIMS})
        for key, value in mutations.items():
            with self.subTest(key=key):
                data = fixture(); data[key] = value
                with self.assertRaises(contract.HandoverError): self.parse(data)

    def test_missing_or_extra_field_in_every_result_section(self):
        paths = [(), ("candidate_manifest",), ("candidate_evidence",), ("qualification_evidence",),
                 ("source_dependencies",), ("original_evaluation",), ("evaluator_result",),
                 ("privileged_validation_evidence",)]
        for path in paths:
            for extra in (True, False):
                with self.subTest(path=path, extra=extra):
                    data = fixture(); section = data
                    for key in path: section = section[key]
                    if extra: section["unknown"] = 1
                    else: section.pop(next(iter(section)))
                    with self.assertRaises(contract.HandoverError): self.parse(data)

    def test_invalid_and_ambiguous_json(self):
        for raw in (b"", b"[]", b"{", b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff',
                    b" " * (contract.MAX_RESULT_BYTES + 1)):
            with self.subTest(raw=raw[:20]):
                with self.assertRaises(contract.HandoverError):
                    contract.AttestedResult.parse(raw, REQUEST)

    def test_paths_and_dependency_drift(self):
        for paths in (["../x"], ["a\\b"], ["a//b"], ["/x"], ["a", "a"], ["z", "a"], ["\u0000"], ["\ud800"]):
            data = fixture(); data["candidate_manifest"]["changed_files"] = paths
            with self.subTest(paths=paths):
                with self.assertRaises(contract.HandoverError): self.parse(data)
        data = fixture(); data["source_dependencies"]["blobs"]["runtime.py"] = "1"*40
        with self.assertRaises(contract.HandoverError): self.parse(data)

    def test_qualification_provenance_and_counts(self):
        for key, value in {"app_id": 999, "source_verified": 1, "head_sha": "c"*40,
                           "status": "queued", "details_url": "https://evil.invalid/",
                           "check_run_id": True}.items():
            data = fixture(); data["qualification_evidence"][key] = value
            with self.subTest(key=key):
                with self.assertRaises(contract.HandoverError): self.parse(data)
        data = fixture(); data["candidate_evidence"]["files_pages_read"] = True
        with self.assertRaises(contract.HandoverError): self.parse(data)

    def test_attestation_binding_and_strict_types(self):
        for key, value in {"pull_request": 221, "repository": "other/repo", "head_sha": "c"*40,
                           "base_sha": "c"*40, "changed_files": ["scripts/example.py"]}.items():
            data = fixture(); data["privileged_validation_evidence"]["record"]["candidate"][key] = value
            with self.subTest(key=key):
                with self.assertRaises(contract.HandoverError): self.parse(data)
        for path in (("contract_version",), ("claims", "exact_candidate_binding"),
                     ("claims", "credentials_used")):
            data = fixture(); record = data["privileged_validation_evidence"]["record"]
            if len(path) == 1: record[path[0]] = True
            else: record[path[0]][path[1]] = 1
            with self.assertRaises(contract.HandoverError): self.parse(data)

    def test_approval_origin_digest_and_path(self):
        for key, value in {"authority_repository": "other/repo", "authority_revision": "0"*40,
                           "path": "approval.json", "tree_chain": [], "blob_sha": None,
                           "raw_sha256": "1"*40, "attestation_digest": "1"*64,
                           "status": "not_required"}.items():
            data = fixture(); data["privileged_validation_evidence"][key] = value
            with self.subTest(key=key):
                with self.assertRaises(contract.HandoverError): self.parse(data)

    def test_verdict_rewrites_and_original_erasure(self):
        mutations = [("original_evaluation", "governance_decision", "pass"),
                     ("evaluator_result", "failure_reasons", ["other"]),
                     ("evaluator_result", "notice", "rewritten"),
                     ("original_evaluation", "runtime_failure_reasons", [])]
        for section, key, value in mutations:
            data = fixture(); data[section][key] = value
            with self.subTest(section=section, key=key):
                with self.assertRaises(contract.HandoverError): self.parse(data)


class AttestedPipelineTests(unittest.TestCase):
    def test_real_service_evidence_permit_and_publisher_parser(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            prepared, report = exercise_pipeline(fixture(), directory)
            self.assertEqual(prepared.outcome.decision, AuthorityDecision.PASS)
            self.assertEqual(report["write_mode"], "disabled")
            self.assertEqual(report["remote_mutations"], 0)
            evidence = json.loads((directory / "decision.json").read_text())
            retained = json.loads(evidence["runtime_result_json"])
            self.assertEqual(retained["original_evaluation"]["governance_decision"], "fail")
            self.assertEqual(retained["privileged_validation_evidence"]["record"], fixture()["privileged_validation_evidence"]["record"])
            receipt = json.loads((directory / "receipt.json").read_text())
            self.assertEqual(receipt["permit_digest"], prepared.permit.digest)
            self.assertEqual(receipt["evidence_sha256"], sha256((directory/"decision.json").read_bytes()).hexdigest())
            self.assertEqual(receipt["runtime_result_sha256"], sha256(evidence["runtime_result_json"].encode()).hexdigest())

    def test_legacy_default_rejects_new_revision(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp); exercise_pipeline(fixture(), directory)
            config = publisher_contract.Config.load(ROOT / "integrations/github-app-publisher/config.json")
            with self.assertRaises(publisher_contract.PublisherError) as error:
                publisher_contract.load_permit(directory/"permit.json", config)
            self.assertEqual(error.exception.code, "permit-runtime-source")

    def test_fail_and_invalid_result_never_issue_permit(self):
        for data in (missing(fixture()), {"bad": "result"}):
            with tempfile.TemporaryDirectory() as temp:
                directory = Path(temp); prepared, report = exercise_pipeline(data, directory)
                self.assertIsNone(prepared.permit); self.assertIsNone(report)
                self.assertFalse((directory/"receipt.json").exists())
                self.assertFalse((directory/"permit.json").exists())

    def test_evidence_failure_blocks_before_permit(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(target, "_write_bound", side_effect=EvidenceWriteError("test")):
            prepared, _ = exercise_pipeline(fixture(), Path(temp))
            self.assertEqual(prepared.outcome.decision, AuthorityDecision.BLOCKED)
            self.assertFalse(prepared.outcome.evidence_recorded)
            self.assertIsNone(prepared.permit)

    def test_receipt_failure_or_interrupt_does_not_return_or_export_permit(self):
        original_write = target._write_bound
        for failure in (EvidenceWriteError("test"), KeyboardInterrupt()):
            def write(path, value):
                if path.name == "receipt.json": raise failure
                return original_write(path, value)
            with tempfile.TemporaryDirectory() as temp, patch.object(target, "_write_bound", side_effect=write):
                with self.assertRaises(type(failure)): exercise_pipeline(fixture(), Path(temp))
                self.assertTrue((Path(temp)/"decision.json").exists())
                self.assertFalse((Path(temp)/"permit.json").exists())

    def test_existing_paths_and_symlinks_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp); (directory/"decision.json").write_text("existing")
            prepared, _ = exercise_pipeline(fixture(), directory)
            self.assertIsNone(prepared.permit)
            self.assertEqual((directory/"decision.json").read_text(), "existing")
        if os.name == "posix":
            with tempfile.TemporaryDirectory() as temp:
                directory = Path(temp); (directory/"decision.json").symlink_to(directory/"absent")
                prepared, _ = exercise_pipeline(fixture(), directory)
                self.assertIsNone(prepared.permit); self.assertFalse((directory/"absent").exists())

    def test_git_checkout_and_missing_parent_cannot_hold_operational_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp); (directory/".git").mkdir()
            prepared, _ = exercise_pipeline(fixture(), directory)
            self.assertIsNone(prepared.permit)
            prepared, _ = exercise_pipeline(fixture(), directory/"missing")
            self.assertIsNone(prepared.permit)

    def test_fsync_failure_cannot_return_permit(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(target.os, "fsync", side_effect=OSError("test")):
            prepared, _ = exercise_pipeline(fixture(), Path(temp))
            self.assertIsNone(prepared.permit)

    def test_tampered_receipt_evidence_or_source_is_rejected_by_preview(self):
        for target_file in ("receipt.json", "decision.json"):
            with tempfile.TemporaryDirectory() as temp:
                directory = Path(temp); exercise_pipeline(fixture(), directory)
                path = directory/target_file; data = json.loads(path.read_text()); data["extra"] = True
                path.write_text(json.dumps(data))
                with self.assertRaises(publisher_contract.PublisherError):
                    attested_preview.preview_attested_permit(directory/"permit.json", directory/"decision.json", directory/"receipt.json",
                        expected_runtime_revision=RUNTIME_REVISION, expected_authority_revision=SERVICE_REVISION)
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp); exercise_pipeline(fixture(), directory)
            with self.assertRaises(publisher_contract.PublisherError):
                attested_preview.preview_attested_permit(directory/"permit.json", directory/"decision.json", directory/"receipt.json",
                    expected_runtime_revision="7"*40, expected_authority_revision=SERVICE_REVISION)


    def test_second_attempt_same_outputs_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            first, _ = exercise_pipeline(fixture(), directory)
            original = (directory / "decision.json").read_bytes()
            second, _ = exercise_pipeline(fixture(), directory)
            self.assertIsNotNone(first.permit)
            self.assertIsNone(second.permit)
            self.assertEqual((directory / "decision.json").read_bytes(), original)

    def test_preview_malformed_permit_section_is_safe_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            exercise_pipeline(fixture(), directory)
            data = json.loads((directory / "permit.json").read_text())
            data["publication"] = []
            (directory / "permit.json").write_text(json.dumps(data))
            with self.assertRaises(publisher_contract.PublisherError):
                attested_preview.preview_attested_permit(
                    directory / "permit.json", directory / "decision.json", directory / "receipt.json",
                    expected_runtime_revision=RUNTIME_REVISION, expected_authority_revision=SERVICE_REVISION)


class AttestedPolicyTests(unittest.TestCase):
    def test_checked_in_state_is_exact_merged_runtime_promotion(self):
        policy = target.HandoverPolicy.load(target.POLICY_PATH)
        self.assertIsNotNone(policy.package)
        self.assertEqual(
            policy.package.source_revision,
            "d835991afe6ada47a66d012a3ddc2c4350cd9ff8",
        )
        self.assertEqual(policy.package.entrypoint_blob, target.REVIEW_BLOB)
        self.assertEqual(policy.timeout_seconds, 120)

    def test_public_entrypoint_uses_promoted_package_and_fixed_authority_policy(self):
        sentinel = object()
        with patch.object(target, "_authority_revision", return_value=SERVICE_REVISION),              patch.object(target, "load_authority_policy", return_value=POLICY),              patch.object(target, "AttestedCodexRuntime") as runtime,              patch.object(target, "_evaluate_and_prepare", return_value=sentinel) as prepare:
            result = target.prepare_attested_permit(REQUEST, "runtime", "decision", "receipt")
        self.assertIs(result, sentinel)
        package = runtime.call_args.args[1]
        self.assertEqual(package.source_revision, "d835991afe6ada47a66d012a3ddc2c4350cd9ff8")
        self.assertEqual(package.entrypoint_blob, target.REVIEW_BLOB)
        prepare.assert_called_once()

    def test_policy_rejects_partial_binding_claim_and_enable_drift(self):
        baseline = json.loads(target.POLICY_PATH.read_text())
        mutations = [("schema_version", True), ("state", "staged-disabled"), ("runtime_package", {}),
                     ("execution", {**baseline["execution"], "enabled": False}),
                     ("publication", {"write_enabled": True, "mode": "offline-preview-only"}),
                     ("claims", {"privileged_governance_maintenance_path_proven": 0, "effective_enforcement_proven": False})]
        for key, value in mutations:
            with tempfile.TemporaryDirectory() as temp:
                data = copy.deepcopy(baseline); data[key] = value
                path = Path(temp)/"policy.json"; path.write_text(json.dumps(data))
                with self.subTest(key=key):
                    with self.assertRaises(contract.HandoverError): target.HandoverPolicy.load(path)

    def test_promoted_policy_rejects_unmerged_review_head(self):
        data=json.loads(target.POLICY_PATH.read_text())
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"policy.json"
            self.assertEqual(target.HandoverPolicy.load(target.POLICY_PATH).package.source_revision,
                             "d835991afe6ada47a66d012a3ddc2c4350cd9ff8")
            data["runtime_package"]["source_revision"]=target.REVIEW_HEAD
            path.write_text(json.dumps(data))
            with self.assertRaises(contract.HandoverError): target.HandoverPolicy.load(path)


class AttestedRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.source=contract.canonical(fixture())

    def package(self, script=None):
        if script is None:
            script="import sys\nsys.stdout.buffer.write("+repr(self.source)+")\n"
        (self.root/adapter.ENTRYPOINT).write_text(script)
        dependencies=[]
        for name,_ in contract.DEPENDENCY_BLOBS:
            raw=b"# synthetic fixture dependency\n" if name.endswith(".py") else b"{}\n"
            (self.root/name).write_bytes(raw); dependencies.append((name,adapter.blob_id(raw)))
        package=adapter.RuntimePackage(RUNTIME_REVISION,adapter.blob_id((self.root/adapter.ENTRYPOINT).read_bytes()))
        patcher=patch.object(adapter,"DEPENDENCY_BLOBS",tuple(dependencies));patcher.start();self.addCleanup(patcher.stop)
        return package

    def test_harmless_verified_process_parses_result_and_is_one_shot(self):
        runtime=adapter.AttestedCodexRuntime(self.root,self.package())
        self.assertEqual(runtime.evaluate(REQUEST).decision,AuthorityDecision.PASS)
        with self.assertRaises(contract.HandoverError): runtime.evaluate(REQUEST)

    def test_no_ambient_credentials_proxy_or_python_paths(self):
        script="import os,sys\nassert not any(k in os.environ for k in ['GH_TOKEN','HTTPS_PROXY','PYTHONPATH','SSL_CERT_FILE'])\nassert sys.flags.isolated\nsys.stdout.buffer.write("+repr(self.source)+")\n"
        package=self.package(script)
        with patch.dict(os.environ,{"GH_TOKEN":"synthetic-not-a-secret","HTTPS_PROXY":"http://invalid.test","PYTHONPATH":"invalid","SSL_CERT_FILE":"invalid"}):
            self.assertEqual(adapter.AttestedCodexRuntime(self.root,package).evaluate(REQUEST).decision,AuthorityDecision.PASS)

    def test_tampered_missing_extra_and_symlink_source(self):
        package=self.package(); (self.root/adapter.ENTRYPOINT).write_text("tampered")
        with patch.object(adapter,"_run") as run:
            with self.assertRaises(contract.HandoverError): adapter.AttestedCodexRuntime(self.root,package).evaluate(REQUEST)
            run.assert_not_called()
        (self.root/"extra.py").write_text("extra")
        with self.assertRaises(contract.HandoverError): adapter.AttestedCodexRuntime(self.root,package).evaluate(REQUEST)
        (self.root/"extra.py").unlink(); (self.root/adapter.ENTRYPOINT).unlink()
        with self.assertRaises(contract.HandoverError): adapter.AttestedCodexRuntime(self.root,package).evaluate(REQUEST)
        if os.name == "posix":
            (self.root/adapter.ENTRYPOINT).symlink_to(self.root/"runtime.py")
            with self.assertRaises(contract.HandoverError): adapter.AttestedCodexRuntime(self.root,package).evaluate(REQUEST)

    def test_candidate_revision_cannot_be_runtime(self):
        package=replace(self.package(),source_revision=REQUEST.head_sha)
        with self.assertRaises(contract.HandoverError) as error:
            adapter.AttestedCodexRuntime(self.root,package).evaluate(REQUEST)
        self.assertEqual(error.exception.code,"candidate-as-authority")

    def test_export_required_before_execution(self):
        package=self.package(); (self.root/".git").mkdir()
        with self.assertRaises(contract.HandoverError): adapter.AttestedCodexRuntime(self.root,package).evaluate(REQUEST)

    def test_output_overflow_both_pipes_and_stderr_fail_closed(self):
        for stream, size in (("stdout",contract.MAX_RESULT_BYTES+1),("stderr",contract.MAX_RESULT_BYTES+1),("stderr",1)):
            package=self.package(f"import sys\nsys.{stream}.buffer.write(b'x'*{size})\n")
            with self.subTest(stream=stream,size=size):
                with self.assertRaises(contract.HandoverError): adapter.AttestedCodexRuntime(self.root,package).evaluate(REQUEST)

    def test_timeout_and_exit_verdict_mismatch(self):
        package=self.package("import time\ntime.sleep(10)\n")
        with self.assertRaises(contract.HandoverError) as error:
            adapter.AttestedCodexRuntime(self.root,package,timeout_seconds=1).evaluate(REQUEST)
        self.assertEqual(error.exception.code,"runtime-timeout")
        package=self.package("import sys\nsys.stdout.buffer.write("+repr(self.source)+")\nsys.exit(2)\n")
        with self.assertRaises(contract.HandoverError): adapter.AttestedCodexRuntime(self.root,package).evaluate(REQUEST)

    def test_verified_byte_snapshot_survives_original_path_drift(self):
        package=self.package(); execute=adapter._run
        def run(command,working,timeout):
            (self.root/adapter.ENTRYPOINT).write_text("raise RuntimeError('not executed')\n")
            return execute(command,working,timeout)
        with patch.object(adapter,"_run",side_effect=run):
            self.assertEqual(adapter.AttestedCodexRuntime(self.root,package).evaluate(REQUEST).decision,AuthorityDecision.PASS)


if __name__ == "__main__":
    unittest.main()
