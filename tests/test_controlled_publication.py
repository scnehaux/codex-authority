from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "integrations/github-app-publisher"))
sys.path.insert(0, str(ROOT / "tests"))

from codex_authority import controlled_evidence as core
from codex_authority.attested_contract import canonical, digest, HandoverError
from codex_authority.adapters.attested_runtime import blob_id
from codex_authority.model import AuthorityDecision
from test_attested_handover import fixture, exercise_pipeline, REQUEST, POLICY, RUNTIME_REVISION, SERVICE_REVISION
import controlled_publisher as target


def raw_legacy(data):
    """Synthetic v1 wire equivalent; actual Codex execution is tested by cross-repo CI."""
    return {
        "schema_version": 1, "status": "runtime_evaluation_complete", "repository": REQUEST.repository,
        "pull_request": REQUEST.pull_request, "base_sha": data["base_sha"], "candidate_sha": REQUEST.head_sha,
        "authority_source_revision": core.EVALUATOR_REVISION, "runtime_source_promoted": False,
        "facts_collected_independently": True, "facts_provenance_verified": False,
        "candidate_manifest": copy.deepcopy(data["candidate_manifest"]),
        "collected_facts": {"schema_version": 1, "repository": REQUEST.repository,
            "pull_request": REQUEST.pull_request, "base_sha": data["base_sha"], "head_sha": REQUEST.head_sha,
            "authority_source_revision": core.EVALUATOR_REVISION, "candidate_qualification": "pass",
            "privileged_validation": "not_required"},
        "candidate_evidence": copy.deepcopy(data["candidate_evidence"]),
        "qualification_evidence": copy.deepcopy(data["qualification_evidence"]),
        "runtime_only_protected_mutations": list(data["runtime_only_protected_mutations"]),
        "runtime_failure_reasons": list(data["original_evaluation"]["runtime_failure_reasons"]),
        "evaluator_result": copy.deepcopy(data["original_evaluation"]["evaluator_result"]),
        "governance_decision": "fail", "candidate_code_executed": False, "credentials_used": False,
        "publish_enabled": False, "authority_binding_advanced": False, "effective_enforcement_proven": False,
        "notice": "Synthetic bootstrap test data, never operational authority.",
    }


class SyntheticBootstrap:
    def __init__(self, data, approval):
        self.data, self.approval, self.request = data, approval, REQUEST
        self.raw = self.original = self.authorized = None

    def evaluate(self, request):
        self.raw = canonical(self.data)
        self.original, self.authorized = core.bootstrap_result(self.raw, request, self.approval)
        return self.authorized


def bootstrap_pipeline(directory, data=None):
    example = fixture()
    wire = raw_legacy(example) if data is None else data
    approval = canonical(example["privileged_validation_evidence"]["record"])
    origin = {"authority_revision": SERVICE_REVISION,
              "path": core.ATTESTATION_PREFIX + REQUEST.head_sha + ".json", "mode": "100644",
              "blob_sha": blob_id(approval), "raw_sha256": sha256(approval).hexdigest(),
              "record_json": approval.decode("utf-8")}
    policy = json.loads((ROOT / "governance/privileged-maintenance.json").read_text())
    policy["state"] = "bootstrap-proof"
    policy["bootstrap"].update(enabled=True, candidate={"pull_request": REQUEST.pull_request, "head_sha": REQUEST.head_sha})
    result = core._prepare_bootstrap(REQUEST, SyntheticBootstrap(wire, approval), POLICY,
             SERVICE_REVISION, origin, canonical(policy), directory / "decision.json", directory / "receipt.json")
    if result.permit is not None:
        (directory / "permit.json").write_text(result.permit.to_json(), encoding="utf-8")
    return result


def bundle_at(directory, mode="attested-v2"):
    paths = [directory / p for p in ("permit.json", "decision.json", "receipt.json")]
    evidence = json.loads(paths[1].read_text())
    return core.verify_bundle(*(p.read_bytes() for p in paths), runtime_package=evidence["runtime_package"],
                               authority_revision=SERVICE_REVISION, mode=mode)


def activation(directory, mode="attested-v2"):
    bundle = bundle_at(directory, mode)
    now = datetime.now(timezone.utc)
    kit = directory / "kit"
    kit.mkdir(exist_ok=True)
    (kit / "publication-state").mkdir(exist_ok=True)
    blobs = {}
    for relative in target.SOURCE_FILES:
        path = kit / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = ("# synthetic export fixture: " + relative + "\n").encode()
        path.write_bytes(raw)
        blobs[relative] = blob_id(raw)
    a = {"mode": mode, "candidate": bundle.permit.to_mapping()["candidate"],
         "runtime_package": json.loads((directory / "decision.json").read_text())["runtime_package"],
         "authority_service_source_revision": SERVICE_REVISION, "publisher_source_revision": "7" * 40,
         "publisher_source_blobs": blobs, "permit_digest": bundle.permit.digest,
         "evidence_sha256": bundle.evidence_digest, "receipt_sha256": bundle.receipt_digest,
         "not_before": (now - timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "expires_at": (now + timedelta(seconds=600)).strftime("%Y-%m-%dT%H:%M:%SZ")}
    config = kit / "governance/controlled-publication.json"
    config.parent.mkdir(exist_ok=True)
    config.write_bytes(canonical({"schema_version": 1, "kind": "codex-controlled-publication",
        "state": "candidate-proof", "activation": a,
        "claims": {"live_publication_proven": False, "effective_enforcement_proven": False}}))
    return bundle, a, kit, config


class FakeTransport:
    def __init__(self, bundle, mode="success"):
        self.bundle, self.mode, self.calls = bundle, mode, []

    def __call__(self, path, token, *, method="GET", body=None):
        self.calls.append((method, path, copy.deepcopy(body)))
        p = self.bundle.permit
        if path == "/app":
            return {"id": target.APP_ID}
        if path.endswith("/installation") or path.startswith("/app/installations/") and method == "GET":
            return {"id": target.INSTALLATION_ID, "app_id": target.APP_ID, "account": {"login": "scnehaux"},
                    "suspended_at": None, "repository_selection": "selected", "permissions": dict(target.TOKEN_PERMISSIONS)}
        if path.endswith("/access_tokens"):
            permissions = {} if self.mode == "bad-token-permissions" else dict(target.TOKEN_PERMISSIONS)
            return {"token": "synthetic-token-only", "permissions": permissions}
        if "?check_name=" in path:
            return {"total_count": 1, "check_runs": [{"id": self.bundle.qualification_id + (self.mode == "rerun"),
                "name": "Governance Qualification", "head_sha": p.candidate.head_sha,
                "status": "completed", "conclusion": "failure" if self.mode == "failed-check" else "success",
                "app": {"id": 15368, "slug": "github-actions", "owner": {"login": "github"}}}]}
        if "/pulls/" in path:
            return {"number": p.candidate.pull_request, "state": "open", "draft": self.mode == "draft",
                "base": {"ref": "main", "sha": "6" * 40 if self.mode == "base-drift" else p.base_sha,
                         "repo": {"full_name": target.REPOSITORY}},
                "head": {"sha": p.candidate.head_sha, "repo": {"full_name": target.REPOSITORY}}}
        if path.endswith("/check-runs"):
            if self.mode == "lost-response":
                raise TimeoutError("synthetic remote write may have succeeded")
            return {"id": 1234, "name": target.CHECK_CONTEXT, "head_sha": p.candidate.head_sha,
                    "status": "completed", "conclusion": "success",
                    "app": {"id": 42 if self.mode == "wrong-app" else target.APP_ID}}
        if path == "/installation/token":
            if self.mode == "revocation-failed":
                raise OSError("synthetic cleanup failure")
            return {}
        raise AssertionError("unexpected mock publisher endpoint")


def publish_synthetic(directory, mode="attested-v2", failure="success"):
    bundle, a, kit, _ = activation(directory, mode)
    transport = FakeTransport(bundle, failure)
    with patch.object(target, "make_jwt", return_value="synthetic-jwt"):
        result = target._publish(a, bundle, kit, Path("nonexistent-test-key"), transport)
    return result, transport, kit


class ControlledPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        exercise_pipeline(fixture(), self.directory)

    def test_v2_bundle_and_controlled_post_success(self):
        result, transport, _ = publish_synthetic(self.directory)
        self.assertEqual(result["status"], "published")
        self.assertTrue(result["token_revoked"])
        self.assertEqual(len([c for c in transport.calls if c[0] == "POST" and c[1].endswith("/check-runs")]), 1)

    def test_checked_in_config_is_exact_pr23_permanent_path_proof(self):
        a = target.load_configuration(target.CONFIG_PATH)
        self.assertIsNotNone(a)
        self.assertEqual(a["mode"], "attested-v2")
        self.assertEqual(a["candidate"], {
            "repository": "scnehaux/codex",
            "pull_request": 23,
            "base_sha": "d835991afe6ada47a66d012a3ddc2c4350cd9ff8",
            "head_sha": "d681a8f311cbb3a0bc69b795639112918e57a85f",
        })
        self.assertEqual(a["permit_digest"], "bd6c7f8afb76554a4afb7a1920dcebb660a66f373bea313cea27371f02d7972d")
        self.assertEqual(a["evidence_sha256"], "995b9a9c3781647ca9286fc8c969629ecbfccb4e891bc3f83a02d643ed92f37d")
        self.assertEqual(a["receipt_sha256"], "5f23e6421ba1a2f3bfb3bb2de657adc8d6c303e065b13697330932ebc0901535")

    def test_disabled_configuration_still_short_circuits(self):
        config = self.directory / "disabled.json"
        config.write_bytes(canonical({"schema_version": 1, "kind": "codex-controlled-publication",
            "state": "disabled", "activation": None,
            "claims": {"live_publication_proven": False, "effective_enforcement_proven": False}}))
        with patch.object(target, "CONFIG_PATH", config), patch.object(target, "make_jwt") as key, patch.object(target, "_request") as request:
            result = target.execute("absent", "absent", "absent")
            self.assertEqual(result["status"], "controlled_publication_disabled")
            with self.assertRaises(HandoverError):
                target.execute("absent", "absent", "absent", write=True)
            key.assert_not_called()
            request.assert_not_called()

    def test_bootstrap_gate_disabled_before_git_or_execution(self):
        with patch.object(core, "_authority_revision") as git, patch.object(core, "EvidencedBootstrapRuntime") as runtime:
            with self.assertRaises(HandoverError):
                core.prepare_bootstrap_permit(REQUEST, "missing", "missing", "missing")
            git.assert_not_called()
            runtime.assert_not_called()

    def test_live_config_is_separate_from_historical_loader(self):
        _, a, _, path = activation(self.directory)
        self.assertEqual(target.load_configuration(path), a)
        import publisher_contract
        with self.assertRaises(publisher_contract.PublisherError):
            publisher_contract.Config.load(path)

    def test_config_rejects_unbound_and_boolean_fields(self):
        _, _, _, path = activation(self.directory)
        baseline = json.loads(path.read_text())
        for mutate in (
            lambda d: d.update(schema_version=True),
            lambda d: d["activation"]["candidate"].update(pull_request=True),
            lambda d: d["activation"].update(publisher_source_blobs={}),
            lambda d: d["activation"].update(permit_digest="0" * 64),
            lambda d: d["activation"]["runtime_package"].update(source_revision=REQUEST.head_sha),
            lambda d: d["claims"].update(live_publication_proven=0),
            lambda d: d["activation"].update(mode="anything"),
        ):
            data = copy.deepcopy(baseline)
            mutate(data)
            path.write_bytes(canonical(data))
            with self.assertRaises(HandoverError):
                target.load_configuration(path)

    def test_expired_and_overlong_activation_windows_rejected(self):
        bundle, a, kit, path = activation(self.directory)
        a.update(not_before="2000-01-01T00:00:00Z", expires_at="2000-01-01T00:10:00Z")
        with patch.object(target, "make_jwt") as key, self.assertRaises(HandoverError):
            target._publish(a, bundle, kit, Path("absent"))
        key.assert_not_called()
        data = json.loads(path.read_text())
        data["activation"].update(not_before="2000-01-01T00:00:00Z", expires_at="2000-01-01T02:00:00Z")
        path.write_bytes(canonical(data))
        with self.assertRaises(HandoverError):
            target.load_configuration(path)

    def test_source_tamper_and_symlinks_rejected(self):
        _, a, kit, _ = activation(self.directory)
        path = kit / target.SOURCE_FILES[0]
        path.write_text("tampered")
        with self.assertRaises(HandoverError):
            target.verify_export(kit, a)
        path.unlink()
        try:
            path.symlink_to(kit / target.SOURCE_FILES[1])
        except OSError:
            self.skipTest("host does not permit symlink creation")
        with self.assertRaises(HandoverError):
            target.verify_export(kit, a)

    def test_receipt_evidence_and_permit_mutation_rejected(self):
        for filename in ("permit.json", "decision.json", "receipt.json"):
            p = self.directory / filename
            original = p.read_bytes()
            p.write_bytes(original.replace(b'"pass"', b'"fail"', 1) if filename != "receipt.json" else original + b" invalid")
            with self.assertRaises((HandoverError, ValueError)):
                bundle_at(self.directory)
            p.write_bytes(original)

    def test_relinked_evidence_still_revalidates_full_runtime(self):
        ep, rp = self.directory / "decision.json", self.directory / "receipt.json"
        e, r = json.loads(ep.read_text()), json.loads(rp.read_text())
        runtime = json.loads(e["runtime_result_json"])
        runtime["qualification_evidence"]["conclusion"] = "failure"
        wire = canonical(runtime)
        e.update(runtime_result_json=wire.decode(), runtime_result_sha256=sha256(wire).hexdigest())
        ep.write_bytes(canonical(e))
        r.update(evidence_sha256=sha256(ep.read_bytes()).hexdigest(), runtime_result_sha256=e["runtime_result_sha256"])
        rp.write_bytes(canonical(r))
        with self.assertRaises(HandoverError):
            bundle_at(self.directory)

    def test_no_check_post_for_drift_draft_or_qualification_failure(self):
        for mode in ("base-drift", "draft", "rerun", "failed-check", "bad-token-permissions"):
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                exercise_pipeline(fixture(), directory)
                bundle, a, kit, _ = activation(directory)
                fake = FakeTransport(bundle, mode)
                with patch.object(target, "make_jwt", return_value="synthetic-jwt"), self.assertRaises(HandoverError):
                    target._publish(a, bundle, kit, Path("absent"), fake)
                self.assertFalse(any(m == "POST" and p.endswith("/check-runs") for m, p, _ in fake.calls))
                self.assertTrue(any(m == "DELETE" for m, _, _ in fake.calls))

    def test_lost_post_response_is_uncertain_and_same_candidate_cannot_replay(self):
        bundle, a, kit, _ = activation(self.directory)
        fake = FakeTransport(bundle, "lost-response")
        with patch.object(target, "make_jwt", return_value="synthetic-jwt"), self.assertRaises(HandoverError):
            target._publish(a, bundle, kit, Path("absent"), fake)
        report = json.loads(next((kit / "publication-state").glob("*.outcome.json")).read_text())
        self.assertEqual(report["status"], "publication_uncertain")
        self.assertTrue(report["token_revoked"])
        other = FakeTransport(bundle)
        with patch.object(target, "make_jwt") as key, self.assertRaises(Exception):
            target._publish(a, bundle, kit, Path("absent"), other)
        key.assert_not_called()
        self.assertEqual(other.calls, [])

    def test_wrong_app_response_fails_after_one_post(self):
        with self.assertRaises(HandoverError):
            publish_synthetic(self.directory, failure="wrong-app")
        report = json.loads(next((self.directory / "kit/publication-state").glob("*.outcome.json")).read_text())
        self.assertEqual(report["status"], "publication_uncertain")

    def test_cleanup_failure_keeps_known_check_identity(self):
        with self.assertRaises(HandoverError):
            publish_synthetic(self.directory, failure="revocation-failed")
        report = json.loads(next((self.directory / "kit/publication-state").glob("*.outcome.json")).read_text())
        self.assertEqual(report["status"], "published_cleanup_failed")
        self.assertEqual(report["check_run_id"], 1234)
        self.assertFalse(report["token_revoked"])

    def test_failed_attempt_reservation_never_loads_credentials(self):
        bundle, a, kit, _ = activation(self.directory)
        with patch.object(target, "_write_bound", side_effect=OSError("synthetic disk failure")), \
             patch.object(target, "make_jwt") as key, self.assertRaises(OSError):
            target._publish(a, bundle, kit, Path("absent"))
        key.assert_not_called()

    def test_outcome_write_failure_does_not_allow_retry(self):
        bundle, a, kit, _ = activation(self.directory)
        write = target._write_bound
        def fail_outcome(path, data):
            if str(path).endswith(".outcome.json"):
                raise OSError("synthetic final fsync failure")
            return write(path, data)
        with patch.object(target, "make_jwt", return_value="synthetic-jwt"), \
             patch.object(target, "_write_bound", side_effect=fail_outcome), self.assertRaises(OSError):
            target._publish(a, bundle, kit, Path("absent"), FakeTransport(bundle))
        self.assertEqual(len(list((kit / "publication-state").glob("*.attempt.json"))), 1)

    def test_operator_confirmation_precedes_credential_access(self):
        _, _, kit, config = activation(self.directory)
        with patch.object(target, "CONFIG_PATH", config), patch.object(target, "ROOT", kit), \
             patch.object(target, "make_jwt") as key, self.assertRaises(HandoverError):
            target.execute(*(self.directory / n for n in ("permit.json", "decision.json", "receipt.json")), write=True)
        key.assert_not_called()

    def test_public_preview_verifies_without_any_write(self):
        _, _, kit, config = activation(self.directory)
        with patch.object(target, "CONFIG_PATH", config), patch.object(target, "ROOT", kit), \
             patch.object(target, "make_jwt") as key:
            result = target.execute(*(self.directory / n for n in ("permit.json", "decision.json", "receipt.json")))
        self.assertEqual(result["remote_mutations"], 0)
        key.assert_not_called()
        self.assertFalse(list((kit / "publication-state").iterdir()))

    def test_freshness_transport_is_public_fixed_get_without_token(self):
        path = f"/repos/scnehaux/codex/commits/{REQUEST.head_sha}/check-runs?check_name=Governance%20Qualification&filter=latest&per_page=100"
        response = io.BytesIO(b'{"total_count":0,"check_runs":[]}')
        response.status = 200
        with patch.object(target, "build_opener") as opener:
            opener.return_value.open.return_value = response
            target._request(path, "must-not-leak")
            sent = opener.return_value.open.call_args.args[0]
            self.assertIsNone(sent.get_header("Authorization"))
            self.assertEqual(sent.get_method(), "GET")
        with self.assertRaises(HandoverError):
            target._request(path, "irrelevant", method="POST", body={})


class ControlledBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def test_bootstrap_original_fail_receipt_and_publisher_success(self):
        prepared = bootstrap_pipeline(self.directory)
        self.assertIsNotNone(prepared.permit)
        evidence = json.loads((self.directory / "decision.json").read_text())
        self.assertEqual(json.loads(evidence["runtime_result_json"])["governance_decision"], "fail")
        self.assertEqual(evidence["decision_record"]["decision"], "pass")
        bundle_at(self.directory, "bootstrap-v1")
        result, _, _ = publish_synthetic(self.directory, "bootstrap-v1")
        self.assertEqual(result["status"], "published")

    def test_non_privilege_failure_never_issues_permit(self):
        data = raw_legacy(fixture())
        data["evaluator_result"]["failure_reasons"].append("unknown-governance-failure")
        prepared = bootstrap_pipeline(self.directory, data)
        self.assertIsNone(prepared.permit)
        self.assertFalse((self.directory / "receipt.json").exists())

    def test_qualification_cannot_be_overridden_by_privilege_reasons(self):
        data = raw_legacy(fixture())
        data["qualification_evidence"]["conclusion"] = "failure"
        prepared = bootstrap_pipeline(self.directory, data)
        self.assertIsNone(prepared.permit)

    def test_strict_attestation_rejects_numeric_claims_and_candidate_drift(self):
        data = raw_legacy(fixture())
        record = fixture()["privileged_validation_evidence"]["record"]
        for mutate in (
            lambda d: d.update(contract_version=True),
            lambda d: d["claims"].update(candidate_code_executed=0),
            lambda d: d["candidate"].update(base_sha="6" * 40),
            lambda d: d["candidate"].update(changed_files=["README.md"]),
        ):
            copy_ = copy.deepcopy(record)
            mutate(copy_)
            with self.assertRaises(Exception):
                core.bootstrap_result(canonical(data), REQUEST, canonical(copy_))

    def test_receipt_write_failure_does_not_return_permit(self):
        original = core._write_bound
        def fail_receipt(path, value):
            if Path(path).name == "receipt.json":
                raise OSError("synthetic failure")
            return original(path, value)
        with patch.object(core, "_write_bound", side_effect=fail_receipt), self.assertRaises(OSError):
            bootstrap_pipeline(self.directory)
        self.assertTrue((self.directory / "decision.json").exists())
        self.assertFalse((self.directory / "permit.json").exists())

    def test_evidence_write_failure_blocks_permit(self):
        with patch.object(core, "_write_bound", side_effect=OSError("synthetic failure")):
            result = bootstrap_pipeline(self.directory)
        self.assertIsNone(result.permit)
        self.assertEqual(result.outcome.decision, AuthorityDecision.BLOCKED)

    def test_committed_file_reads_exact_git_object_not_checkout_bytes(self):
        path = core.ATTESTATION_PREFIX + REQUEST.head_sha + ".json"
        raw = b'{"contract_version":1}\n'
        oid = blob_id(raw)
        outputs = [
            (f"100644 blob {oid}\t{path}\n").encode(),
            (str(len(raw)) + "\n").encode(),
            raw,
        ]
        completed = [type("Completed", (), {"stdout": value})() for value in outputs]
        with patch.object(core.subprocess, "run", side_effect=completed), \
             patch.object(core, "read_regular", side_effect=AssertionError("working tree must not be read")):
            observed, observed_oid = core._committed_file(SERVICE_REVISION, path, 128_000)
        self.assertEqual(observed, raw)
        self.assertEqual(observed_oid, oid)

    def test_committed_attestation_modes_and_blobs_checked(self):
        path = core.ATTESTATION_PREFIX + REQUEST.head_sha + ".json"
        fake = type("Completed", (), {"stdout": ("120000 blob " + "a" * 40 + "\t" + path + "\n").encode()})()
        with patch.object(core.subprocess, "run", return_value=fake), self.assertRaises(HandoverError):
            core._committed_file(SERVICE_REVISION, path, 128_000)


if __name__ == "__main__":
    unittest.main()
