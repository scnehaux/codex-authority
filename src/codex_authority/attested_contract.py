"""Version-2 wire validation, not a second governance evaluator or source promotion."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any

from .model import AuthorityDecision, CandidateRef, CandidateSnapshot

REPOSITORY = "scnehaux/codex"
AUTHORITY_REPOSITORY = "scnehaux/codex-authority"
COLLECTOR_REVISION = "cbd64f78c8f72f28880d4673729a796b249d8eae"
EVALUATOR_REVISION = "23b05a855419b86b61b0c9266805bb66b143c366"
DEPENDENCY_BLOBS = (
    ("runtime.py", "c59911e9c0800c917fed21e6f33f3181c3a61e60"),
    ("evaluator.py", "ab2f152c21bd6d6f22df21172c4d027035ff8c11"),
    ("promotion.json", "f8f67280baf1c8725f67592d015ff37be2c4a4c3"),
    ("runtime-promotion.json", "83658bf5a44d22804d1628074dd8f27a7047d68e"),
)
PRIVILEGE_BLOCKERS = frozenset({
    "privileged-validation-missing",
    "runtime-critical-mutation-requires-privileged-validation",
})
MAX_RESULT_BYTES = 512_000
FALSE_CLAIMS = {
    "facts_provenance_verified", "runtime_source_promoted", "candidate_code_executed",
    "credentials_used", "publish_enabled", "authority_binding_advanced",
    "effective_enforcement_proven",
}
RESULT_FIELDS = {
    "schema_version", "kind", "status", "repository", "pull_request", "base_sha",
    "candidate_sha", "candidate_manifest", "candidate_evidence", "qualification_evidence",
    "source_dependencies", "original_evaluation", "privileged_validation_evidence",
    "evaluator_result", "runtime_only_protected_mutations", "runtime_failure_reasons",
    "failure_reasons", "governance_decision", "facts_collected_independently", "notice",
} | FALSE_CLAIMS
EVALUATOR_FIELDS = {
    "schema_version", "status", "decision_scope", "repository", "pull_request", "base_sha",
    "candidate_sha", "authority_source_revision", "check_context", "protected_mutations",
    "requires_privileged_validation", "candidate_qualification", "privileged_validation",
    "failure_reasons", "governance_decision", "notice", "facts_provenance_verified",
    "publish_enabled", "authority_promoted", "candidate_code_executed", "credentials_used",
    "effective_enforcement_proven",
}


class HandoverError(Exception):
    """Stable operator-safe error; never includes candidate text or remote bodies."""
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Attested handover failed closed ({code}).")


def require(ok: bool, code: str) -> None:
    if not ok:
        raise HandoverError(code)


def object_fields(value: object, fields: set[str], code: str) -> dict[str, Any]:
    require(isinstance(value, dict) and set(value) == fields, code)
    return value


def sha(value: object, length: int = 40) -> str:
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None
            and value != "0" * length, "source-sha")
    return value


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return sha256(canonical(value)).hexdigest()


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value


def _nonfinite(value: str) -> None:
    raise ValueError("non-finite constant")


def decode_object(raw: bytes, limit: int = MAX_RESULT_BYTES) -> dict[str, Any]:
    require(type(raw) is bytes and 0 < len(raw) <= limit, "json-size")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_nonfinite)
    except (ValueError, UnicodeError, RecursionError):
        raise HandoverError("json-invalid") from None
    require(isinstance(value, dict), "json-object")
    return value


def _positive(value: object, limit: int | None = None) -> int:
    require(type(value) is int and value > 0 and (limit is None or value <= limit), "positive-integer")
    return value


def _strings(value: object, *, paths: bool = False) -> list[str]:
    require(isinstance(value, list) and len(value) <= 2_000, "string-list")
    for item in value:
        require(isinstance(item, str) and 0 < len(item) <= 4096, "string-list")
        require(all(32 <= ord(c) != 127 and not 0xD800 <= ord(c) <= 0xDFFF for c in item), "string-list")
        if paths:
            require("\\" not in item and all(p not in {"", ".", ".."} for p in item.split("/")), "changed-path")
    require(len(value) == len(set(value)), "duplicate-values")
    if paths:
        require(value == sorted(value), "path-order")
    return value


def _notice(value: object) -> None:
    require(isinstance(value, str) and 0 < len(value) <= 4096, "notice")


def _evaluator(value: object, identity: dict, paths: list[str], qualification: str) -> dict:
    data = object_fields(value, EVALUATOR_FIELDS, "evaluator-fields")
    require(type(data["schema_version"]) is int and data["schema_version"] == 2, "evaluator-version")
    require(data["status"] == "evaluation_complete" and data["decision_scope"] == "staging-offline", "evaluator-status")
    for key, expected in identity.items():
        require(type(data[key]) is type(expected) and data[key] == expected, "evaluator-identity")
    require(data["authority_source_revision"] == EVALUATOR_REVISION
            and data["check_context"] == "Codex Governance Authority", "evaluator-source")
    protected = _strings(data["protected_mutations"], paths=True)
    require(set(protected).issubset(paths) and data["requires_privileged_validation"] is bool(protected), "protected-paths")
    require(data["candidate_qualification"] == qualification, "evaluator-qualification")
    require(data["privileged_validation"] in ("pass", "not_required"), "privilege-state")
    reasons = _strings(data["failure_reasons"])
    require(data["governance_decision"] == ("fail" if reasons else "pass"), "evaluator-verdict")
    if qualification != "pass":
        require("candidate-qualification-failed" in reasons, "qualification-failure-lost")
    for key in ("facts_provenance_verified", "publish_enabled", "authority_promoted",
                "candidate_code_executed", "credentials_used", "effective_enforcement_proven"):
        require(data[key] is False, "evaluator-claim")
    _notice(data["notice"])
    return data


def _approval(evidence: dict, candidate: dict) -> None:
    # Integrity fields are checked here; committed origin is observed by the source-verified reader.
    fields = {"status", "authority_repository", "authority_revision", "path", "tree_chain",
              "blob_sha", "raw_sha256", "attestation_digest", "record"}
    object_fields(evidence, fields, "attestation-evidence-fields")
    require(evidence["authority_repository"] == AUTHORITY_REPOSITORY, "attestation-origin")
    sha(evidence["authority_revision"])
    require(evidence["path"] == f"governance/privileged-validations/{candidate['head_sha']}.json", "attestation-path")
    chain = evidence["tree_chain"]
    require(isinstance(chain, list) and 1 <= len(chain) <= 3, "attestation-tree-chain")
    for item in chain:
        sha(item)
    if evidence["status"] == "missing":
        require(all(evidence[k] is None for k in ("blob_sha", "raw_sha256", "attestation_digest", "record")), "missing-attestation")
        return
    require(evidence["status"] == "verified" and len(chain) == 3, "attestation-status")
    sha(evidence["blob_sha"])
    sha(evidence["raw_sha256"], 64)
    record = object_fields(evidence["record"], {
        "contract_version", "kind", "candidate", "decision", "scope", "authority", "claims",
    }, "attestation-fields")
    require(type(record["contract_version"]) is int and record["contract_version"] == 1, "attestation-version")
    require(record["kind"] == "codex-privileged-validation-attestation" and record["decision"] == "pass"
            and record["scope"] == "protected-governance-maintenance", "attestation-scope")
    observed = object_fields(record["candidate"], set(candidate), "attestation-candidate")
    require(type(observed["pull_request"]) is int and observed == candidate, "attestation-candidate")
    require(record["authority"] == {"repository": AUTHORITY_REPOSITORY, "default_branch": "main", "mode": "privileged-explicit"}, "attestation-authority")
    claims = object_fields(record["claims"], {"candidate_code_executed", "credentials_used", "exact_candidate_binding"}, "attestation-claims")
    require(claims["candidate_code_executed"] is False and claims["credentials_used"] is False
            and claims["exact_candidate_binding"] is True, "attestation-claims")
    require(sha(evidence["attestation_digest"], 64) == digest(record), "attestation-digest")


@dataclass(frozen=True, slots=True)
class AttestedResult:
    """Immutable parsed wire data. Parsing alone does NOT verify source or promote code."""
    raw: bytes
    snapshot: CandidateSnapshot
    decision: AuthorityDecision
    reasons: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        return decode_object(self.raw)

    @property
    def raw_digest(self) -> str:
        return sha256(self.raw).hexdigest()

    @classmethod
    def parse(cls, raw: bytes, request: CandidateRef) -> AttestedResult:
        data = object_fields(decode_object(raw), RESULT_FIELDS, "result-fields")
        require(type(data["schema_version"]) is int and data["schema_version"] == 2, "result-version")
        require(data["kind"] == "codex-attested-runtime-result"
                and data["status"] == "attested_runtime_evaluation_complete", "result-kind")
        identity = {"repository": request.repository, "pull_request": request.pull_request,
                    "base_sha": sha(data["base_sha"]), "candidate_sha": request.head_sha}
        sha(request.head_sha)
        require(request.repository == REPOSITORY, "candidate-repository")
        for key, expected in identity.items():
            require(type(data[key]) is type(expected) and data[key] == expected, "result-identity")
        for key in FALSE_CLAIMS:
            require(data[key] is False, "result-claim")
        require(data["facts_collected_independently"] is True, "result-provenance")
        _notice(data["notice"])
        manifest = object_fields(data["candidate_manifest"], {
            "schema_version", "repository", "pull_request", "base_sha", "head_sha", "changed_files",
        }, "manifest-fields")
        require(type(manifest["schema_version"]) is int and manifest["schema_version"] == 1, "manifest-version")
        paths = _strings(manifest["changed_files"], paths=True)
        candidate = {"repository": request.repository, "pull_request": request.pull_request,
                     "base_sha": data["base_sha"], "head_sha": request.head_sha, "changed_files": paths}
        require(type(manifest["pull_request"]) is int and manifest == {"schema_version": 1, **candidate}, "manifest-identity")
        require(bool(paths) and data["base_sha"] != request.head_sha, "candidate-range")
        source = object_fields(data["source_dependencies"], {"collector_revision", "evaluator_revision", "blobs"}, "source-fields")
        require(source == {"collector_revision": COLLECTOR_REVISION, "evaluator_revision": EVALUATOR_REVISION,
                           "blobs": dict(DEPENDENCY_BLOBS)}, "dependency-identity")
        observed = object_fields(data["candidate_evidence"], {
            "source", "pull_state", "base_ref", "api_changed_file_records", "touched_paths",
            "files_pages_read", "identity_verified", "changed_files_verified",
        }, "candidate-evidence")
        require(observed["source"] == "github-pull-request-api" and observed["pull_state"] == "open"
                and observed["base_ref"] == "main" and observed["identity_verified"] is True
                and observed["changed_files_verified"] is True, "candidate-provenance")
        count = _positive(observed["api_changed_file_records"], 2_000)
        require(count <= _positive(observed["touched_paths"], 2_000) == len(paths) <= 2 * count, "candidate-counts")
        require(_positive(observed["files_pages_read"], 20) == (count + 99) // 100, "candidate-pages")
        q = object_fields(data["qualification_evidence"], {
            "source", "check_run_id", "name", "head_sha", "status", "conclusion", "app_id",
            "app_slug", "source_verified", "details_url",
        }, "qualification-fields")
        require(q["source"] == "github-checks-api" and q["name"] == "Governance Qualification"
                and q["head_sha"] == request.head_sha and q["status"] == "completed"
                and type(q["app_id"]) is int and q["app_id"] == 15368 and q["app_slug"] == "github-actions"
                and q["source_verified"] is True, "qualification-source")
        _positive(q["check_run_id"])
        require(isinstance(q["details_url"], str) and re.fullmatch(
            r"https://github\.com/scnehaux/codex/actions/runs/[1-9][0-9]*/job/[1-9][0-9]*", q["details_url"]
        ) is not None, "qualification-url")
        require(isinstance(q["conclusion"], str) and 0 < len(q["conclusion"]) <= 100, "qualification-conclusion")
        qualification = "pass" if q["conclusion"] == "success" else "fail"
        original = object_fields(data["original_evaluation"], {
            "evaluator_result", "runtime_failure_reasons", "governance_decision",
        }, "original-fields")
        initial = _evaluator(original["evaluator_result"], identity, paths, qualification)
        require(initial["privileged_validation"] == "not_required", "original-privilege")
        protected = initial["protected_mutations"]
        require(("privileged-validation-missing" in initial["failure_reasons"]) is bool(protected), "original-privilege-reason")
        runtime_only = _strings(data["runtime_only_protected_mutations"], paths=True)
        require(set(runtime_only).issubset(paths) and not set(runtime_only).intersection(protected), "runtime-protected-paths")
        old_runtime_reasons = ["runtime-critical-mutation-requires-privileged-validation"] if runtime_only else []
        require(original["runtime_failure_reasons"] == old_runtime_reasons, "original-runtime-reasons")
        old_reasons = initial["failure_reasons"] + old_runtime_reasons
        require(original["governance_decision"] == ("fail" if old_reasons else "pass"), "original-verdict")
        approval = data["privileged_validation_evidence"]
        require(isinstance(approval, dict), "approval-shape")
        eligible = qualification == "pass" and bool(old_reasons) and set(old_reasons).issubset(PRIVILEGE_BLOCKERS)
        if not eligible:
            expected_status = "not_required" if not (protected or runtime_only) else "not_attempted"
            require(approval == {"status": expected_status}, "approval-not-eligible")
        else:
            _approval(approval, candidate)
        final = _evaluator(data["evaluator_result"], identity, paths, qualification)
        expected_final = dict(initial)
        final_runtime_reasons = old_runtime_reasons
        if eligible and approval["status"] == "verified":
            expected_final.update(privileged_validation="pass" if protected else "not_required",
                                  failure_reasons=[], governance_decision="pass")
            final_runtime_reasons = []
        require(final == expected_final, "verdict-rewrite")
        require(data["runtime_failure_reasons"] == final_runtime_reasons, "runtime-reasons")
        reasons = final["failure_reasons"] + final_runtime_reasons
        require(data["failure_reasons"] == reasons and data["governance_decision"] == ("fail" if reasons else "pass"), "final-verdict")
        snapshot = CandidateSnapshot(request.repository, request.pull_request, data["base_sha"],
                                     request.head_sha, "open", tuple(paths))
        return cls(raw, snapshot, AuthorityDecision(data["governance_decision"]), tuple(reasons))
