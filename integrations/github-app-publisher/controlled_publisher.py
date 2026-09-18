#!/usr/bin/env python3
"""Explicit, receipt-bound publication for bootstrap-v1 and attested-v2.

The checked-in configuration is disabled. No evaluation or candidate code runs
here. Enabling one candidate requires a separate reviewed Authority activation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from http.client import HTTPException
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from codex_authority.adapters.attested_runtime import blob_id, outside_git, read_regular
from codex_authority.attested_contract import (
    DEPENDENCY_BLOBS, EVALUATOR_REVISION, HandoverError, REPOSITORY, canonical,
    decode_object, digest, object_fields, require, sha,
)
from codex_authority.attested_handover import _write_bound
from codex_authority.controlled_evidence import BOOTSTRAP_PACKAGE, verify_bundle
from publisher_contract import APP_ID, INSTALLATION_ID, CHECK_CONTEXT, Config, Permit, PERMIT_KIND
from publisher_transport import (
    API_ROOT, API_VERSION, NoRedirect, TOKEN_PERMISSIONS, check_payload, default_key_path,
    make_jwt, preflight_app, request_json, verify_candidate_pr, verify_check,
)

CONFIG_PATH = ROOT / "governance" / "controlled-publication.json"
CLIENT_ID = "Iv23li8znPY4yr7chvFD"
SOURCE_FILES = (
    "src/codex_authority/__init__.py", "src/codex_authority/model.py",
    "src/codex_authority/ports.py", "src/codex_authority/policy.py",
    "src/codex_authority/service.py", "src/codex_authority/publication.py",
    "src/codex_authority/evidence.py", "src/codex_authority/privileged.py",
    "src/codex_authority/attested_contract.py", "src/codex_authority/attested_handover.py",
    "src/codex_authority/controlled_evidence.py", "src/codex_authority/adapters/__init__.py",
    "src/codex_authority/adapters/promoted_runtime.py", "src/codex_authority/adapters/attested_runtime.py",
    "integrations/github-app-publisher/controlled_publisher.py",
    "integrations/github-app-publisher/publisher_contract.py",
    "integrations/github-app-publisher/publisher_transport.py",
    "integrations/github-app-publisher/requirements.txt",
)
ACTIVATION_FIELDS = {
    "mode", "candidate", "runtime_package", "authority_service_source_revision",
    "publisher_source_revision", "publisher_source_blobs", "permit_digest",
    "evidence_sha256", "receipt_sha256", "not_before", "expires_at",
}
QUALIFICATION_PATH = re.compile(
    r"/repos/scnehaux/codex/commits/([0-9a-f]{40})/check-runs"
    r"\?check_name=Governance%20Qualification&filter=latest&per_page=100"
)


def _time(value):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is not None,
            "activation-time")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise HandoverError("activation-time") from None


def load_configuration(path):
    data = object_fields(decode_object(read_regular(Path(path), 32_768), 32_768), {
        "schema_version", "kind", "state", "activation", "claims",
    }, "publication-config")
    require(type(data["schema_version"]) is int and data["schema_version"] == 1
            and data["kind"] == "codex-controlled-publication", "publication-config-version")
    require(canonical(data["claims"]) == canonical({"live_publication_proven": False,
            "effective_enforcement_proven": False}), "publication-config-claims")
    if data["state"] == "disabled":
        require(data["activation"] is None, "publication-disabled-binding")
        return None
    require(data["state"] == "candidate-proof", "publication-config-state")
    a = object_fields(data["activation"], ACTIVATION_FIELDS, "publication-activation")
    require(a["mode"] in {"bootstrap-v1", "attested-v2"}, "publication-mode")
    c = object_fields(a["candidate"], {"repository", "pull_request", "base_sha", "head_sha"}, "publication-candidate")
    require(c["repository"] == REPOSITORY and type(c["pull_request"]) is int
            and c["pull_request"] > 0 and sha(c["base_sha"]) != sha(c["head_sha"]), "publication-candidate")
    package = object_fields(a["runtime_package"], {"repository", "source_revision", "entrypoint", "blobs"}, "publication-package")
    require(package["repository"] == REPOSITORY and sha(package["source_revision"]) != c["head_sha"], "publication-runtime")
    if a["mode"] == "bootstrap-v1":
        require(canonical(package) == canonical(BOOTSTRAP_PACKAGE), "publication-bootstrap-package")
    else:
        require(package["entrypoint"] == "attested_runtime.py", "publication-entrypoint")
        require(package["blobs"] == {"attested_runtime.py": sha(package.get("blobs", {}).get("attested_runtime.py")),
                **dict(DEPENDENCY_BLOBS)}, "publication-package-blobs")
    for field in ("authority_service_source_revision", "publisher_source_revision"):
        require(sha(a[field]) != c["head_sha"], "publication-candidate-as-source")
    object_fields(a["publisher_source_blobs"], set(SOURCE_FILES), "publication-source-set")
    for value in a["publisher_source_blobs"].values():
        sha(value)
    for field in ("permit_digest", "evidence_sha256", "receipt_sha256"):
        sha(a[field], 64)
    seconds = (_time(a["expires_at"]) - _time(a["not_before"])).total_seconds()
    require(0 < seconds <= 900, "activation-window")
    return a


def _fresh(a):
    now = datetime.now(timezone.utc)
    require(_time(a["not_before"]) <= now < _time(a["expires_at"]), "activation-expired-or-early")


def verify_export(root: Path, a):
    require(root.is_dir() and not root.is_symlink() and outside_git(root), "publisher-export")
    for relative in SOURCE_FILES:
        path = root / relative
        # Reject symlink ancestors as well as symlink final files.
        current = root
        for part in Path(relative).parts:
            current = current / part
            require(not current.is_symlink(), "publisher-source-symlink")
        require(blob_id(read_regular(path, 1_000_000)) == a["publisher_source_blobs"][relative], "publisher-source-blob")


def _request(path, token, *, method="GET", body=None):
    """Reuse historical authenticated transport; add one credential-free freshness read."""
    match = QUALIFICATION_PATH.fullmatch(path) if isinstance(path, str) else None
    if match is None:
        return request_json(path, token, method=method, body=body)
    require(method == "GET" and body is None, "qualification-method")
    sha(match.group(1))
    request = Request(API_ROOT + path, method="GET", headers={
        "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "scnehaux-controlled-publication/0.1",
    })
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=20) as response:
            require(response.status == 200, "qualification-status")
            raw = response.read(1_000_001)
    except HTTPError as exc:
        exc.close()
        raise HandoverError("qualification-http") from None
    except (URLError, OSError, TimeoutError, HTTPException):
        raise HandoverError("qualification-network") from None
    return decode_object(raw, 1_000_000)


def _qualification(bundle, request, token):
    p = bundle.permit
    path = (f"/repos/{REPOSITORY}/commits/{p.candidate.head_sha}/check-runs"
            "?check_name=Governance%20Qualification&filter=latest&per_page=100")
    data = request(path, token)
    require(type(data.get("total_count")) is int and data["total_count"] == 1
            and isinstance(data.get("check_runs"), list) and len(data["check_runs"]) == 1,
            "publication-qualification-count")
    q = data["check_runs"][0]
    require(isinstance(q, dict), "publication-qualification")
    app = q.get("app", {})
    require(type(q.get("id")) is int and q["id"] == bundle.qualification_id
            and q.get("head_sha") == p.candidate.head_sha and q.get("name") == "Governance Qualification"
            and q.get("status") == "completed" and q.get("conclusion") == "success"
            and isinstance(app, dict) and type(app.get("id")) is int and app["id"] == 15368
            and app.get("slug") == "github-actions" and app.get("owner", {}).get("login") == "github",
            "publication-qualification-drift")


def _legacy_types(a, bundle):
    """Explicit new contract adapter. Never rewrite the runtime as the historical revision."""
    p = bundle.permit
    config = Config(APP_ID, INSTALLATION_ID, CLIENT_ID, REPOSITORY, CHECK_CONTEXT, PERMIT_KIND,
                    p.runtime_source_revision, EVALUATOR_REVISION, p.authority_service_source_revision,
                    a["publisher_source_revision"], None, "proof", p.candidate.head_sha, p.digest, False)
    permit = Permit(REPOSITORY, p.candidate.pull_request, p.base_sha, p.candidate.head_sha,
                    p.runtime_source_revision, EVALUATOR_REVISION, p.authority_service_source_revision, p.digest)
    return config, permit


def _publish(a, bundle, root: Path, key_path: Path, request=_request):
    """All calls are testable with a synthetic transport. Real default is fixed-host."""
    _fresh(a)
    verify_export(root, a)
    directory = root / "publication-state"
    require(directory.is_dir() and not directory.is_symlink(), "publication-state-directory")
    key = digest({"repository": REPOSITORY, "pull_request": bundle.permit.candidate.pull_request,
                  "head_sha": bundle.permit.candidate.head_sha})
    attempt_path = directory / (key + ".attempt.json")
    outcome_path = directory / (key + ".outcome.json")
    require(not outcome_path.exists() and not outcome_path.is_symlink(), "publication-existing-outcome")
    # Exclusive durable reservation BEFORE credential access. Never auto-remove or retry.
    attempt = {"schema_version": 1, "kind": "codex-publication-attempt", "candidate": a["candidate"],
               "activation_digest": digest(a), "permit_digest": bundle.permit.digest,
               "evidence_sha256": bundle.evidence_digest, "receipt_sha256": bundle.receipt_digest}
    _write_bound(attempt_path, attempt)
    config, permit = _legacy_types(a, bundle)
    token = None
    attempted = False
    check_id = None
    revoked = False
    failure = None
    try:
        jwt = make_jwt(key_path, config.client_id)
        preflight_app(config, jwt, request)
        issued = request(f"/app/installations/{INSTALLATION_ID}/access_tokens", jwt, method="POST",
                         body={"repositories": ["codex"], "permissions": TOKEN_PERMISSIONS})
        token = issued.get("token")
        require(isinstance(token, str) and len(token) >= 8, "publication-token")
        require(issued.get("permissions") == TOKEN_PERMISSIONS, "publication-token-permissions")
        _qualification(bundle, request, token)
        pr = request(f"/repos/{REPOSITORY}/pulls/{permit.pull_request}", token)
        require(type(pr.get("number")) is int and pr.get("draft") is False, "publication-pr-ready")
        verify_candidate_pr(pr, permit)
        _fresh(a)
        attempted = True
        response = request(f"/repos/{REPOSITORY}/check-runs", token, method="POST", body=check_payload(permit))
        require(type(response.get("app", {}).get("id")) is int, "publication-check-source")
        check_id = verify_check(response, config, permit)
    except BaseException as exc:
        failure = exc
    finally:
        if isinstance(token, str) and len(token) >= 8:
            try:
                request("/installation/token", token, method="DELETE")
                revoked = True
            except BaseException as exc:
                if failure is None:
                    failure = exc
    status = ("published" if check_id is not None and revoked and failure is None else
              "published_cleanup_failed" if check_id is not None else
              "publication_uncertain" if attempted else "blocked_before_check_post")
    outcome = {"schema_version": 1, "kind": "codex-publication-outcome", "status": status,
               "candidate": a["candidate"], "activation_digest": digest(a),
               "permit_digest": permit.digest, "check_post_attempted": attempted,
               "check_run_id": check_id, "token_revoked": revoked,
               "effective_enforcement_proven": False}
    # If this write fails, the attempt persists and prevents a blind replay.
    _write_bound(outcome_path, outcome)
    if failure is not None:
        if isinstance(failure, (KeyboardInterrupt, SystemExit)):
            raise failure
        raise HandoverError("publication-stopped-reconcile-journal") from None
    require(status == "published", "publication-not-proven")
    return outcome


def execute(permit_path, evidence_path, receipt_path, *, write=False, confirm_repository=None,
            confirm_sha=None, key_path=None):
    """Fixed exported config; no CLI-supplied runtime, endpoint, context or conclusion."""
    a = load_configuration(CONFIG_PATH)
    if a is None:
        if write:
            raise HandoverError("controlled-publication-disabled")
        return {"status": "controlled_publication_disabled", "remote_mutations": 0}
    if write:
        require(confirm_repository == REPOSITORY and confirm_sha == a["candidate"]["head_sha"],
                "publication-operator-confirmation")
        _fresh(a)
    paths = [Path(p) for p in (permit_path, evidence_path, receipt_path)]
    require(all(outside_git(p) for p in paths), "publication-input-checkout")
    permit_raw, evidence_raw, receipt_raw = [read_regular(p, limit) for p, limit in
                                            zip(paths, (32_768, 1_000_000, 32_768), strict=True)]
    bundle = verify_bundle(permit_raw, evidence_raw, receipt_raw,
                           runtime_package=a["runtime_package"],
                           authority_revision=a["authority_service_source_revision"], mode=a["mode"])
    require(canonical(bundle.permit.to_mapping()["candidate"]) == canonical(a["candidate"])
            and bundle.permit.digest == a["permit_digest"]
            and bundle.evidence_digest == a["evidence_sha256"]
            and bundle.receipt_digest == a["receipt_sha256"], "publication-activation-binding")
    if not write:
        return {"status": "controlled_publication_preview", "permit_digest": bundle.permit.digest,
                "mode": a["mode"], "remote_mutations": 0, "effective_enforcement_proven": False}
    return _publish(a, bundle, ROOT, Path(key_path) if key_path is not None else default_key_path())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permit", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--confirm-repository")
    parser.add_argument("--confirm-sha")
    parser.add_argument("--private-key", type=Path)
    args = parser.parse_args(argv)
    try:
        report = execute(args.permit, args.evidence, args.receipt, write=args.write,
                         confirm_repository=args.confirm_repository, confirm_sha=args.confirm_sha,
                         key_path=args.private_key)
    except Exception:
        print(json.dumps({"status": "blocked", "message": "Controlled publication stopped; inspect the local journal before any retry."}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
