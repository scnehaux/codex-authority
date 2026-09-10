from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "integrations" / "github-app-publisher"
sys.path.insert(0, str(PACKAGE))
spec = importlib.util.spec_from_file_location(
    "github_app_publisher", PACKAGE / "github_app_publisher.py"
)
target = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = target
spec.loader.exec_module(target)
import publisher_transport as transport  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
from codex_authority.model import (  # noqa: E402
    AuthorityDecision,
    AuthorityOutcome,
    CandidateRef,
    CandidateSnapshot,
)
from codex_authority.publication import issue_publication_permit  # noqa: E402


BASE = "1" * 40
HEAD = "2" * 40
AUTHORITY = "5" * 40
PUBLISHER_REVISION = "6" * 40
PUBLISHER_BLOB = "7" * 40


def permit_json() -> str:
    outcome = AuthorityOutcome(
        request=CandidateRef("scnehaux/codex", 17, HEAD),
        decision=AuthorityDecision.PASS,
        reasons=(),
        snapshot=CandidateSnapshot(
            repository="scnehaux/codex",
            pull_request=17,
            base_sha=BASE,
            head_sha=HEAD,
            state="open",
            changed_files=("README.md",),
        ),
        runtime_source_revision=target.EXPECTED_RUNTIME_SOURCE_REVISION,
        evaluator_source_revision=target.EXPECTED_EVALUATOR_SOURCE_REVISION,
        evidence_recorded=True,
    )
    permit = issue_publication_permit(
        outcome, authority_service_source_revision=AUTHORITY
    )
    assert permit is not None
    return permit.to_json()


def proof_config() -> target.Config:
    return target.Config(
        app_id=target.APP_ID,
        installation_id=target.INSTALLATION_ID,
        client_id="Iv23li8znPY4yr7chvFD",
        repository=target.REPOSITORY,
        check_context=target.CHECK_CONTEXT,
        permit_kind=target.PERMIT_KIND,
        expected_runtime_source_revision=target.EXPECTED_RUNTIME_SOURCE_REVISION,
        expected_evaluator_source_revision=target.EXPECTED_EVALUATOR_SOURCE_REVISION,
        expected_authority_service_source_revision=AUTHORITY,
        publisher_source_revision=PUBLISHER_REVISION,
        publisher_source_blobs={"github_app_publisher.py": PUBLISHER_BLOB, "publisher_contract.py": "8" * 40, "publisher_transport.py": "9" * 40},
        write_mode="proof",
        proof_head_sha=HEAD,
        proof_permit_digest=__import__("hashlib").sha256(__import__("json").dumps(__import__("json").loads(permit_json()), sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        live_proven=False,
    )


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.permit_path = self.root / "permit.json"
        self.permit_path.write_text(permit_json(), encoding="utf-8")

    def fail_code(self, code, fn, *args, **kwargs):
        with self.assertRaises(target.PublisherError) as result:
            fn(*args, **kwargs)
        self.assertEqual(result.exception.code, code)

    def test_checked_in_config_is_strictly_disabled(self):
        config = target.Config.load(PACKAGE / "config.json")
        self.assertEqual(config.app_id, 4864946)
        self.assertEqual(config.installation_id, 159870521)
        self.assertEqual(config.repository, "scnehaux/codex")
        self.assertEqual(config.check_context, "Codex Governance Authority")
        self.assertEqual(config.write_mode, "disabled")
        self.assertIsNone(config.publisher_source_revision)
        self.assertIsNone(config.publisher_source_blobs)
        self.assertIsNone(config.proof_permit_digest)
        self.assertFalse(config.live_proven)

    def test_permit_parser_binds_promoted_sources_and_fixed_capability(self):
        config = target.Config.load(PACKAGE / "config.json")
        permit = target.load_permit(self.permit_path, config)
        self.assertEqual(permit.head_sha, HEAD)
        self.assertEqual(permit.base_sha, BASE)
        self.assertEqual(permit.authority_service_source_revision, AUTHORITY)
        self.assertEqual(len(permit.digest), 64)

        data = json.loads(self.permit_path.read_text())
        data["source"]["runtime_source_revision"] = "8" * 40
        self.permit_path.write_text(json.dumps(data))
        self.fail_code(
            "permit-runtime-source", target.load_permit, self.permit_path, config
        )

    def test_disabled_preview_is_side_effect_free(self):
        config = target.Config.load(PACKAGE / "config.json")
        permit = target.load_permit(self.permit_path, config)
        report = target.preview(config, permit)
        self.assertEqual(report["status"], "preview_only")
        self.assertEqual(report["remote_mutations"], 0)
        self.assertEqual(report["write_mode"], "disabled")
        self.assertFalse(report["effective_enforcement_proven"])
        self.fail_code(
            "publisher-disabled",
            target.publish,
            config,
            permit,
            self.root / "key.pem",
            config_path=PACKAGE / "config.json",
            permit_path=self.permit_path,
        )

    def test_cli_preview_never_reads_key_or_opens_network(self):
        output = io.StringIO()
        with (
            patch.object(target, "make_jwt", side_effect=AssertionError("key access forbidden")),
            patch.object(transport, "build_opener", side_effect=AssertionError("network forbidden")),
            redirect_stdout(output),
        ):
            code = target.main(
                [
                    "--config",
                    str(PACKAGE / "config.json"),
                    "--permit",
                    str(self.permit_path),
                    "--json",
                ]
            )
        self.assertEqual(code, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["remote_mutations"], 0)

    def test_proof_mode_is_bound_to_exact_head_and_authority_source(self):
        config = proof_config()
        permit = target.load_permit(self.permit_path, config)
        bad_head = target.Config(
            app_id=config.app_id,
            installation_id=config.installation_id,
            client_id=config.client_id,
            repository=config.repository,
            check_context=config.check_context,
            permit_kind=config.permit_kind,
            expected_runtime_source_revision=config.expected_runtime_source_revision,
            expected_evaluator_source_revision=config.expected_evaluator_source_revision,
            expected_authority_service_source_revision=config.expected_authority_service_source_revision,
            publisher_source_revision=config.publisher_source_revision,
            publisher_source_blobs=config.publisher_source_blobs,
            write_mode="proof",
            proof_head_sha="9" * 40,
            proof_permit_digest=config.proof_permit_digest,
            live_proven=False,
        )
        self.fail_code(
            "proof-candidate",
            target.publish,
            bad_head,
            permit,
            self.root / "key.pem",
            config_path=PACKAGE / "config.json",
            permit_path=self.permit_path,
        )

    def test_proof_mode_is_bound_to_exact_promoted_permit_digest(self):
        config = proof_config()
        permit = target.load_permit(self.permit_path, config)
        bad = target.Config(
            app_id=config.app_id, installation_id=config.installation_id, client_id=config.client_id,
            repository=config.repository, check_context=config.check_context, permit_kind=config.permit_kind,
            expected_runtime_source_revision=config.expected_runtime_source_revision,
            expected_evaluator_source_revision=config.expected_evaluator_source_revision,
            expected_authority_service_source_revision=config.expected_authority_service_source_revision,
            publisher_source_revision=config.publisher_source_revision, publisher_source_blobs=config.publisher_source_blobs,
            write_mode="proof", proof_head_sha=config.proof_head_sha, proof_permit_digest="a" * 64, live_proven=False,
        )
        self.fail_code(
            "proof-permit", target.publish, bad, permit, self.root / "key.pem",
            config_path=self.root / "config.json", permit_path=self.permit_path,
        )

    def test_source_verification_precedes_private_key_access(self):
        config = proof_config()
        permit = target.load_permit(self.permit_path, config)
        order = []

        def verify_source(config_path, permit_path, actual_config):
            order.append("source")

        def key(*args, **kwargs):
            order.append("key")
            raise target.PublisherError("key-missing", "synthetic")

        with (
            patch.object(target, "verify_exported_publisher", side_effect=verify_source),
            patch.object(target, "make_jwt", side_effect=key),
        ):
            self.fail_code(
                "key-missing",
                target.publish,
                config,
                permit,
                self.root / "key.pem",
                config_path=self.root / "config.json",
                permit_path=self.permit_path,
            )
        self.assertEqual(order, ["source", "key"])

    def test_publish_sequence_verifies_identity_and_revokes_token(self):
        config = proof_config()
        permit = target.load_permit(self.permit_path, config)
        installation = {
            "id": target.INSTALLATION_ID,
            "app_id": target.APP_ID,
            "account": {"login": "scnehaux"},
            "permissions": dict(target.REQUIRED_INSTALLATION_PERMISSIONS),
            "suspended_at": None,
            "repository_selection": "selected",
        }
        calls = []

        def request(path, token, *, method="GET", body=None):
            calls.append((method, path, body))
            if path == "/app":
                return {"id": target.APP_ID}
            if path in {
                f"/app/installations/{target.INSTALLATION_ID}",
                f"/repos/{target.REPOSITORY}/installation",
            }:
                return dict(installation)
            if path.endswith("/access_tokens"):
                return {
                    "token": "ghs_SYNTHETIC_TEST_TOKEN",
                    "permissions": dict(target.TOKEN_PERMISSIONS),
                }
            if path.endswith("/pulls/17"):
                return {
                    "number": 17,
                    "state": "open",
                    "base": {
                        "ref": "main",
                        "sha": BASE,
                        "repo": {"full_name": target.REPOSITORY},
                    },
                    "head": {
                        "sha": HEAD,
                        "repo": {"full_name": target.REPOSITORY},
                    },
                }
            if path.endswith("/check-runs"):
                return {
                    "id": 12345,
                    "name": target.CHECK_CONTEXT,
                    "head_sha": HEAD,
                    "status": "completed",
                    "conclusion": "success",
                    "app": {"id": target.APP_ID},
                }
            if path == "/installation/token":
                return {}
            raise AssertionError(path)

        with (
            patch.object(target, "verify_exported_publisher") as verify_source,
            patch.object(target, "make_jwt", return_value="APP-JWT") as make_jwt,
        ):
            report = target.publish(
                config,
                permit,
                self.root / "key.pem",
                config_path=self.root / "config.json",
                permit_path=self.permit_path,
                request=request,
            )
        verify_source.assert_called_once_with(
            self.root / "config.json", self.permit_path, config
        )
        make_jwt.assert_called_once_with(
            self.root / "key.pem", config.client_id
        )
        self.assertEqual(report["check_run_id"], 12345)
        self.assertEqual(report["integration_id"], target.APP_ID)
        self.assertTrue(report["source_verified"])
        self.assertTrue(report["exact_candidate_binding"])
        self.assertTrue(report["credentials_isolated"])
        self.assertTrue(report["token_revoked"])
        self.assertFalse(report["candidate_code_executed"])
        self.assertFalse(report["effective_enforcement_proven"])
        self.assertEqual(
            [(method, path) for method, path, _ in calls],
            [
                ("GET", "/app"),
                ("GET", f"/app/installations/{target.INSTALLATION_ID}"),
                ("GET", f"/repos/{target.REPOSITORY}/installation"),
                ("POST", f"/app/installations/{target.INSTALLATION_ID}/access_tokens"),
                ("GET", f"/repos/{target.REPOSITORY}/pulls/17"),
                ("POST", f"/repos/{target.REPOSITORY}/check-runs"),
                ("DELETE", "/installation/token"),
            ],
        )

    def test_check_failure_is_never_retried_and_token_revocation_is_attempted(self):
        config = proof_config()
        permit = target.load_permit(self.permit_path, config)
        installation = {
            "id": target.INSTALLATION_ID,
            "app_id": target.APP_ID,
            "account": {"login": "scnehaux"},
            "permissions": dict(target.REQUIRED_INSTALLATION_PERMISSIONS),
            "suspended_at": None,
            "repository_selection": "selected",
        }
        check_posts = 0
        revoked = 0

        def request(path, token, *, method="GET", body=None):
            nonlocal check_posts, revoked
            if path == "/app":
                return {"id": target.APP_ID}
            if path in {
                f"/app/installations/{target.INSTALLATION_ID}",
                f"/repos/{target.REPOSITORY}/installation",
            }:
                return dict(installation)
            if path.endswith("/access_tokens"):
                return {"token": "ghs_SYNTHETIC", "permissions": dict(target.TOKEN_PERMISSIONS)}
            if path.endswith("/pulls/17"):
                return {
                    "number": 17,
                    "state": "open",
                    "base": {"ref": "main", "sha": BASE, "repo": {"full_name": target.REPOSITORY}},
                    "head": {"sha": HEAD, "repo": {"full_name": target.REPOSITORY}},
                }
            if path.endswith("/check-runs"):
                check_posts += 1
                raise target.PublisherError("network-error", "synthetic")
            if path == "/installation/token":
                revoked += 1
                return {}
            raise AssertionError(path)

        with (
            patch.object(target, "verify_exported_publisher"),
            patch.object(target, "make_jwt", return_value="APP-JWT"),
        ):
            self.fail_code(
                "network-error",
                target.publish,
                config,
                permit,
                self.root / "key.pem",
                config_path=self.root / "config.json",
                permit_path=self.permit_path,
                request=request,
            )
        self.assertEqual(check_posts, 1)
        self.assertEqual(revoked, 1)

    def test_transport_rejects_arbitrary_paths_and_mutable_check_capability(self):
        self.fail_code("api-path", target.request_json, "https://evil.test/app", "token")
        self.fail_code("api-path", target.request_json, "/repos/scnehaux/other/check-runs", "token", method="POST", body={})
        body = target.check_payload(target.load_permit(self.permit_path, target.Config.load(PACKAGE / "config.json")))
        body["name"] = "Other Context"
        self.fail_code(
            "check-payload",
            target.request_json,
            f"/repos/{target.REPOSITORY}/check-runs",
            "token",
            method="POST",
            body=body,
        )


if __name__ == "__main__":
    unittest.main()
