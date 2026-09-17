"""Offline cross-repository contract test against the exact Codex PR #22 source.

Candidate code runs ONLY in credential-free test execution with synthetic APIs.
This is not the Authority operational entrypoint, promotion, or an attestation.
"""
from __future__ import annotations

import argparse
import base64
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from codex_authority.attested_contract import DEPENDENCY_BLOBS, canonical
from codex_authority.adapters.attested_runtime import blob_id, read_regular
from codex_authority.attested_handover import REVIEW_HEAD, REVIEW_BLOB
from test_attested_handover import fixture, exercise_pipeline


class FakeGitHub:
    """Synthetic Git objects and Checks API facts; no network implementation."""
    def __init__(self, mode: str):
        self.mode = mode
        self.example = fixture()
        self.candidate = {k: v for k, v in self.example["candidate_manifest"].items() if k != "schema_version"}
        if mode == "unprotected":
            self.candidate["changed_files"] = ["README.md"]
        if mode == "runtime-only":
            self.candidate["changed_files"] = ["scripts/example.py"]
        self.authority_calls = 0

    def get(self, path, query=None):
        c = self.candidate
        if path == f"/repos/scnehaux/codex/pulls/{c['pull_request']}":
            return {"number": c["pull_request"], "state": "open", "changed_files": len(c["changed_files"]),
                    "base": {"ref": "main", "sha": c["base_sha"], "repo": {"full_name": c["repository"]}},
                    "head": {"ref": "test", "sha": c["head_sha"], "repo": {"full_name": c["repository"]}}}
        if path.endswith(f"/pulls/{c['pull_request']}/files"):
            return [{"filename": p, "status": "modified"} for p in c["changed_files"]]
        if path == f"/repos/scnehaux/codex/commits/{c['head_sha']}/check-runs":
            q = self.example["qualification_evidence"]
            return {"total_count": 1, "check_runs": [{"id": q["check_run_id"], "name": q["name"],
                    "head_sha": c["head_sha"], "status": "completed",
                    "conclusion": "failure" if self.mode == "qualification-failed" else "success",
                    "details_url": q["details_url"], "app": {"id": 15368, "slug": "github-actions", "owner": {"login": "github"}}}]}
        raise AssertionError("unexpected synthetic candidate endpoint")

    def get_authority(self, path):
        self.authority_calls += 1
        prefix = "/repos/scnehaux/codex-authority/git"
        revision, root, governance, approvals = (c * 40 for c in "cdef")
        record = copy.deepcopy(self.example["privileged_validation_evidence"]["record"])
        record["candidate"] = copy.deepcopy(self.candidate)
        if self.mode == "wrong-base":
            record["candidate"]["base_sha"] = "7" * 40
        raw = canonical(record)
        blob = blob_id(raw)
        if path == prefix + "/ref/heads/main":
            return {"ref": "refs/heads/main", "object": {"type": "commit", "sha": revision}}
        if path == prefix + "/commits/" + revision:
            return {"sha": revision, "tree": {"sha": root}}
        entries = {
            root: [{"path": "governance", "type": "tree", "mode": "040000", "sha": governance}],
            governance: [{"path": "privileged-validations", "type": "tree", "mode": "040000", "sha": approvals}],
            approvals: [] if self.mode == "missing" else [{"path": self.candidate["head_sha"] + ".json",
                "type": "blob", "mode": "100644", "sha": blob, "size": len(raw)}],
        }
        if path.startswith(prefix + "/trees/"):
            sha = path.rsplit("/", 1)[1]
            return {"sha": sha, "truncated": False, "tree": entries[sha]}
        if path == prefix + "/blobs/" + blob:
            return {"sha": blob, "encoding": "base64", "size": len(raw), "content": base64.b64encode(raw).decode("ascii")}
        raise AssertionError("unexpected synthetic Authority endpoint")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-root", type=Path, required=True)
    args = parser.parse_args()
    source = args.codex_root.resolve()
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True, timeout=10).strip()
    if revision != REVIEW_HEAD:
        raise SystemExit("cross-repository test source does not match the reviewed candidate")
    package = source / "integrations/github-governance-evaluator"
    for name, expected in (("attested_runtime.py", REVIEW_BLOB), *DEPENDENCY_BLOBS):
        if blob_id(read_regular(package / name, 1_000_000)) != expected:
            raise SystemExit("cross-repository test package blob drifted")
    spec = importlib.util.spec_from_file_location("_tested_codex_attested_runtime", package / "attested_runtime.py")
    reader = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = reader
    spec.loader.exec_module(reader)
    completed = []
    for mode in ("verified", "runtime-only", "unprotected", "missing", "qualification-failed", "wrong-base"):
        fake = FakeGitHub(mode)
        try:
            result = reader.collect_and_evaluate(220, fake.get, fake.get_authority)
        except reader.AttestedRuntimeError:
            if mode != "wrong-base":
                raise
            completed.append(mode)
            continue
        if mode == "wrong-base":
            raise SystemExit("wrong-base approval was not rejected")
        with tempfile.TemporaryDirectory() as temp:
            prepared, preview = exercise_pipeline(result, Path(temp), runtime_revision=REVIEW_HEAD)
            success = mode in {"verified", "runtime-only", "unprotected"}
            if (prepared.permit is not None) != success:
                raise SystemExit("actual reader/Authority permit compatibility failed")
            if success and (preview["remote_mutations"] != 0 or preview["write_mode"] != "disabled"):
                raise SystemExit("test preview is not write-disabled")
        if mode in {"unprotected", "qualification-failed"} and fake.authority_calls != 0:
            raise SystemExit("ineligible candidate unexpectedly requested approval")
        completed.append(mode)
    print(json.dumps({"status": "offline_cross_repository_compatibility_pass", "codex_source": REVIEW_HEAD,
                      "cases": completed, "candidate_code_executed_in_tests_only": True,
                      "operational_promotion": False, "publication_performed": False,
                      "effective_enforcement_proven": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
