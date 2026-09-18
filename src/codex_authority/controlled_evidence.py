"""Evidence-preserving bootstrap and strict publication-bundle verification.

No credential or provider write belongs here. Public preparation reads the fixed
Authority policy; synthetic backends are confined to internal test seams.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile

from .adapters import promoted_runtime as legacy
from .adapters.attested_runtime import blob_id, outside_git, read_regular, _run
from .attested_contract import (
    AttestedResult, COLLECTOR_REVISION, DEPENDENCY_BLOBS, EVALUATOR_REVISION,
    HandoverError, REPOSITORY, canonical, decode_object, digest, object_fields,
    require, sha, _strings,
)
from .attested_handover import (
    ROOT, PreparedAttestedOutcome, _authority_revision, _write_bound,
)
from .evidence import _record_mapping
from .model import AuthorityDecision, CandidateRef, EvidenceRecord
from .policy import load_authority_policy
from .privileged import PrivilegedValidationAttestation, load_maintenance_policy
from .publication import PublicationPermit, issue_publication_permit
from .service import AuthorityService

BOOTSTRAP_PACKAGE = {
    "repository": REPOSITORY, "source_revision": COLLECTOR_REVISION,
    "entrypoint": "runtime.py", "blobs": dict(DEPENDENCY_BLOBS),
}
ATTESTATION_PREFIX = "governance/privileged-validations/"
MAINTENANCE_PATH = "governance/privileged-maintenance.json"
EVIDENCE_FIELDS = {
    "schema_version", "kind", "authority_service_source_revision", "runtime_package",
    "decision_record", "runtime_result_json", "runtime_result_sha256",
}
RECEIPT_FIELDS = {
    "schema_version", "kind", "candidate", "source", "evidence_sha256",
    "runtime_result_sha256", "permit_digest",
}


def strict_attestation(raw: bytes, request: CandidateRef, snapshot):
    data = decode_object(raw, 128_000)
    _strings(list(snapshot.changed_files), paths=True)
    attestation = PrivilegedValidationAttestation(request, snapshot.base_sha, snapshot.changed_files)
    # Canonical equality distinguishes JSON true from 1, unlike Python dict equality.
    require(canonical(data) == canonical(attestation.to_mapping()), "bootstrap-attestation-shape")
    return attestation


def bootstrap_result(raw: bytes, request: CandidateRef, attestation_raw: bytes):
    data = decode_object(raw)
    original = legacy._parse_runtime_result(data, request)
    require(original.decision is AuthorityDecision.FAIL, "bootstrap-original-not-fail")
    qualification = data["qualification_evidence"]
    require(qualification.get("conclusion") == "success"
            and type(qualification.get("check_run_id")) is int
            and qualification["check_run_id"] > 0, "bootstrap-qualification")
    facts = {
        "schema_version": 1, "repository": request.repository,
        "pull_request": request.pull_request, "base_sha": original.snapshot.base_sha,
        "head_sha": request.head_sha, "authority_source_revision": EVALUATOR_REVISION,
        "candidate_qualification": "pass", "privileged_validation": "not_required",
    }
    require(canonical(data["collected_facts"]) == canonical(facts), "bootstrap-facts")
    attestation = strict_attestation(attestation_raw, request, original.snapshot)
    return original, attestation.authorize(request, original)


class EvidencedBootstrapRuntime:
    """Execute only the old promoted four-file package; retain its original output."""
    def __init__(self, directory: Path, request: CandidateRef, attestation_raw: bytes):
        self.directory = directory
        self.request = request
        self.attestation_raw = attestation_raw
        self.raw: bytes | None = None
        self.original = None
        self.authorized = None
        self.used = False

    def evaluate(self, request):
        require(not self.used and request == self.request, "bootstrap-request")
        self.used = True
        root = self.directory.expanduser()
        require(request.head_sha != COLLECTOR_REVISION, "candidate-as-runtime")
        require(not root.is_symlink() and outside_git(root) and root.is_dir(), "bootstrap-export")
        require({p.name for p in root.iterdir()} == set(dict(DEPENDENCY_BLOBS)), "bootstrap-package-files")
        sources = {name: read_regular(root / name, 1_000_000) for name, _ in DEPENDENCY_BLOBS}
        require(all(blob_id(sources[name]) == expected for name, expected in DEPENDENCY_BLOBS), "bootstrap-package-blobs")
        with tempfile.TemporaryDirectory(prefix="codex-bootstrap-") as temporary:
            private = Path(temporary)
            require(outside_git(private), "bootstrap-export")
            for name, raw in sources.items():
                (private / name).write_bytes(raw)
            legacy.verify_exported_runtime(private)
            code, raw = _run([str(Path(sys.executable).resolve()), "-I", "-B",
                              str(private / "runtime.py"), "--pull-request",
                              str(request.pull_request)], private, 60)
        require(code == 2, "bootstrap-exit")
        self.raw = raw
        self.original, self.authorized = bootstrap_result(raw, request, self.attestation_raw)
        return self.authorized


class BootstrapEvidenceSink:
    def __init__(self, path, runtime, service_revision, origin, maintenance_raw):
        self.path, self.runtime = Path(path), runtime
        self.service_revision = sha(service_revision)
        self.origin, self.maintenance_raw = origin, maintenance_raw
        self.record_digest = None
        self.used = False

    def append(self, record):
        require(not self.used, "bootstrap-evidence-used")
        self.used = True
        if record.decision is AuthorityDecision.PASS:
            envelope = self.runtime.authorized
            require(envelope is not None and record.snapshot == envelope.snapshot
                    and record.reasons == () and record.request == self.runtime.request,
                    "bootstrap-evidence-binding")
            require(record.runtime_source_revision == COLLECTOR_REVISION
                    and record.evaluator_source_revision == EVALUATOR_REVISION, "bootstrap-evidence-source")
        raw = self.runtime.raw
        value = {
            "schema_version": 1, "kind": "codex-authority-bootstrap-decision-evidence",
            "authority_service_source_revision": self.service_revision,
            "runtime_package": BOOTSTRAP_PACKAGE, "decision_record": _record_mapping(record),
            "runtime_result_json": raw.decode("utf-8") if raw is not None else None,
            "runtime_result_sha256": sha256(raw).hexdigest() if raw is not None else None,
            "attestation_origin": self.origin,
            "maintenance_policy_json": self.maintenance_raw.decode("utf-8"),
            "maintenance_policy_blob": blob_id(self.maintenance_raw),
        }
        self.record_digest = _write_bound(self.path, value)


def _prepare_bootstrap(request, runtime, policy, service_revision, origin, maintenance_raw,
                       evidence_path, receipt_path):
    """Internal wiring; tests supply synthetic runtime output, never live approvals."""
    require(sha(service_revision) != request.head_sha, "candidate-as-service")
    sink = BootstrapEvidenceSink(evidence_path, runtime, service_revision, origin, maintenance_raw)
    outcome = AuthorityService(policy, runtime, sink).evaluate(request)
    if outcome.decision is not AuthorityDecision.PASS:
        return PreparedAttestedOutcome(outcome, None, sink.record_digest, None)
    require(sink.record_digest is not None and runtime.raw is not None, "bootstrap-evidence-missing")
    permit = issue_publication_permit(outcome, authority_service_source_revision=service_revision)
    require(permit is not None, "bootstrap-permit")
    receipt = {
        "schema_version": 1, "kind": "codex-bootstrap-permit-receipt",
        "candidate": permit.to_mapping()["candidate"], "source": permit.to_mapping()["source"],
        "evidence_sha256": sink.record_digest, "runtime_result_sha256": sha256(runtime.raw).hexdigest(),
        "permit_digest": permit.digest,
    }
    receipt_digest = _write_bound(Path(receipt_path), receipt)
    return PreparedAttestedOutcome(outcome, permit, sink.record_digest, receipt_digest)


def _committed_file(revision: str, relative: str, limit: int) -> tuple[bytes, str]:
    def git(*args):
        try:
            return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10).stdout
        except (OSError, subprocess.SubprocessError):
            raise HandoverError("bootstrap-committed-file") from None
    entry = git("ls-tree", revision, "--", relative).decode("utf-8").strip()
    parts = entry.split("\t")
    require(len(parts) == 2 and parts[1] == relative, "bootstrap-committed-path")
    metadata = parts[0].split()
    require(len(metadata) == 3 and metadata[:2] == ["100644", "blob"], "bootstrap-committed-mode")
    expected = sha(metadata[2])
    # Read the exact committed object bytes, not checkout-filtered working-tree bytes.
    size_text = git("cat-file", "-s", expected).decode("ascii").strip()
    require(size_text.isdigit(), "bootstrap-committed-size")
    size = int(size_text)
    require(0 < size <= limit, "bootstrap-committed-size")
    raw = git("cat-file", "blob", expected)
    require(len(raw) == size and blob_id(raw) == expected, "bootstrap-committed-blob")
    return raw, expected


def prepare_bootstrap_permit(request, runtime_dir, evidence_path, receipt_path):
    """Fixed-policy entrypoint. Disabled policy stops before Git, execution or writes."""
    path = ROOT / MAINTENANCE_PATH
    maintenance_raw = read_regular(path, 64_000)
    data = decode_object(maintenance_raw, 64_000)
    require(data.get("bootstrap", {}).get("enabled") is True, "bootstrap-disabled")
    maintenance = load_maintenance_policy(path)
    require(canonical(maintenance) == canonical(data), "bootstrap-policy-reread")
    require(type(data.get("schema_version")) is int and data["schema_version"] == 1,
            "bootstrap-policy-version")
    require(data["bootstrap"]["candidate"] == {"pull_request": request.pull_request,
            "head_sha": request.head_sha} and type(data["bootstrap"]["candidate"]["pull_request"]) is int,
            "bootstrap-policy-candidate")
    revision = _authority_revision()
    committed_policy, _ = _committed_file(revision, MAINTENANCE_PATH, 64_000)
    committed_data = decode_object(committed_policy, 64_000)
    require(canonical(committed_data) == canonical(data), "bootstrap-policy-drift")
    maintenance_raw = committed_policy
    relative = ATTESTATION_PREFIX + sha(request.head_sha) + ".json"
    raw, blob = _committed_file(revision, relative, 128_000)
    origin = {
        "authority_revision": revision, "path": relative, "mode": "100644",
        "blob_sha": blob, "raw_sha256": sha256(raw).hexdigest(), "record_json": raw.decode("utf-8"),
    }
    policy = load_authority_policy(ROOT / "governance" / "authority.json")
    runtime = EvidencedBootstrapRuntime(Path(runtime_dir), request, raw)
    return _prepare_bootstrap(request, runtime, policy, revision, origin, maintenance_raw,
                              Path(evidence_path), Path(receipt_path))


@dataclass(frozen=True, slots=True)
class PublicationBundle:
    permit: PublicationPermit
    evidence_digest: str
    receipt_digest: str
    qualification_id: int
    changed_files: tuple[str, ...]
    mode: str


def verify_bundle(permit_raw: bytes, evidence_raw: bytes, receipt_raw: bytes, *,
                  runtime_package: dict, authority_revision: str, mode: str) -> PublicationBundle:
    """Validate one immutable byte snapshot. Digests bind integrity, not signer authority."""
    require(mode in {"bootstrap-v1", "attested-v2"}, "bundle-mode")
    p = decode_object(permit_raw, 32_768)
    require(type(p.get("contract_version")) is int and p["contract_version"] == 1, "permit-version")
    permit = PublicationPermit.from_mapping(p)
    sha(permit.candidate.head_sha)
    sha(permit.base_sha)
    require(permit.authority_service_source_revision == sha(authority_revision)
            and permit.runtime_source_revision == sha(runtime_package.get("source_revision"))
            and permit.evaluator_source_revision == EVALUATOR_REVISION
            and permit.candidate.head_sha not in {authority_revision, permit.runtime_source_revision},
            "bundle-source")
    extra = {"attestation_origin", "maintenance_policy_json", "maintenance_policy_blob"} if mode == "bootstrap-v1" else set()
    evidence = object_fields(decode_object(evidence_raw, 1_000_000), EVIDENCE_FIELDS | extra, "bundle-evidence-fields")
    prefix = "bootstrap" if mode == "bootstrap-v1" else "attested"
    require(type(evidence["schema_version"]) is int and evidence["schema_version"] == 1
            and evidence["kind"] == f"codex-authority-{prefix}-decision-evidence", "bundle-evidence-kind")
    require(evidence["authority_service_source_revision"] == authority_revision
            and canonical(evidence["runtime_package"]) == canonical(runtime_package), "bundle-evidence-source")
    receipt = object_fields(decode_object(receipt_raw, 32_768), RECEIPT_FIELDS, "bundle-receipt-fields")
    require(type(receipt["schema_version"]) is int and receipt["schema_version"] == 1
            and receipt["kind"] == f"codex-{prefix}-permit-receipt", "bundle-receipt-kind")
    require(receipt["permit_digest"] == permit.digest
            and receipt["evidence_sha256"] == sha256(evidence_raw).hexdigest()
            and canonical(receipt["candidate"]) == canonical(p["candidate"])
            and canonical(receipt["source"]) == canonical(p["source"]), "bundle-receipt-link")
    require(isinstance(evidence["runtime_result_json"], str), "bundle-runtime-json")
    raw = evidence["runtime_result_json"].encode("utf-8")
    require(evidence["runtime_result_sha256"] == receipt["runtime_result_sha256"]
            == sha256(raw).hexdigest(), "bundle-runtime-digest")
    if mode == "attested-v2":
        require(runtime_package == {"repository": REPOSITORY,
                "source_revision": permit.runtime_source_revision, "entrypoint": "attested_runtime.py",
                "blobs": {"attested_runtime.py": sha(runtime_package.get("blobs", {}).get("attested_runtime.py")),
                          **dict(DEPENDENCY_BLOBS)}}, "bundle-runtime-package")
        parsed = AttestedResult.parse(raw, permit.candidate)
        snapshot, decision, reasons = parsed.snapshot, parsed.decision, parsed.reasons
        data = parsed.to_mapping()
    else:
        require(canonical(runtime_package) == canonical(BOOTSTRAP_PACKAGE), "bundle-bootstrap-package")
        origin = object_fields(evidence["attestation_origin"], {
            "authority_revision", "path", "mode", "blob_sha", "raw_sha256", "record_json",
        }, "bundle-approval-origin")
        require(origin["authority_revision"] == authority_revision and origin["mode"] == "100644"
                and origin["path"] == ATTESTATION_PREFIX + permit.candidate.head_sha + ".json"
                and isinstance(origin["record_json"], str), "bundle-approval-origin")
        approval_raw = origin["record_json"].encode("utf-8")
        require(origin["blob_sha"] == blob_id(approval_raw)
                and origin["raw_sha256"] == sha256(approval_raw).hexdigest(), "bundle-approval-digest")
        _, authorized = bootstrap_result(raw, permit.candidate, approval_raw)
        snapshot, decision, reasons = authorized.snapshot, authorized.decision, authorized.reasons
        data = decode_object(raw)
        require(isinstance(evidence["maintenance_policy_json"], str), "bundle-bootstrap-policy")
        policy_raw = evidence["maintenance_policy_json"].encode("utf-8")
        policy = decode_object(policy_raw, 64_000)
        require(blob_id(policy_raw) == evidence["maintenance_policy_blob"]
                and policy.get("state") == "bootstrap-proof"
                and policy.get("candidate_repository") == REPOSITORY, "bundle-bootstrap-policy")
        b = policy.get("bootstrap", {})
        require(b.get("enabled") is True and canonical(b.get("candidate")) == canonical({
            "pull_request": permit.candidate.pull_request, "head_sha": permit.candidate.head_sha}),
            "bundle-bootstrap-activation")
    require(decision is AuthorityDecision.PASS and not reasons and snapshot.base_sha == permit.base_sha,
            "bundle-not-pass")
    expected = _record_mapping(EvidenceRecord(permit.candidate, decision, reasons, snapshot,
                              permit.runtime_source_revision, EVALUATOR_REVISION))
    require(canonical(evidence["decision_record"]) == canonical(expected), "bundle-decision-binding")
    q = data["qualification_evidence"]
    require(q["conclusion"] == "success" and type(q["check_run_id"]) is int and q["check_run_id"] > 0,
            "bundle-qualification")
    return PublicationBundle(permit, sha256(evidence_raw).hexdigest(), sha256(receipt_raw).hexdigest(),
                             q["check_run_id"], snapshot.changed_files, mode)
