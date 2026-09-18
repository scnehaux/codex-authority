from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping

from .adapters import promoted_runtime as runtime_adapter
from .model import AuthorityDecision, CandidateRef, CandidateSnapshot, RuntimeDecisionEnvelope


ATTESTATION_CONTRACT_VERSION = 1
ATTESTATION_KIND = "codex-privileged-validation-attestation"
CANDIDATE_REPOSITORY = "scnehaux/codex"
AUTHORITY_REPOSITORY = "scnehaux/codex-authority"
AUTHORITY_DEFAULT_BRANCH = "main"
ATTESTATION_SCOPE = "protected-governance-maintenance"
ATTESTATION_MODE = "privileged-explicit"
ALLOWED_PRIVILEGE_BLOCKERS = frozenset(
    {
        "privileged-validation-missing",
        "runtime-critical-mutation-requires-privileged-validation",
    }
)
MAX_ATTESTATION_BYTES = 128_000
MAX_POLICY_BYTES = 64_000
MAX_RUNTIME_OUTPUT_BYTES = runtime_adapter.MAX_RUNTIME_OUTPUT_BYTES
DEFAULT_TIMEOUT_SECONDS = runtime_adapter.DEFAULT_TIMEOUT_SECONDS
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class PrivilegedMaintenanceError(Exception):
    """Fail-closed privileged-maintenance boundary error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _read_object(path: Path, limit: int, code: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError:
        raise PrivilegedMaintenanceError(code, "Governed input is unreadable.") from None
    if not raw or len(raw) > limit:
        raise PrivilegedMaintenanceError(code, "Governed input is empty or exceeds the supported size.")
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise PrivilegedMaintenanceError(code, "Governed input must be valid UTF-8 JSON.") from None
    if not isinstance(value, dict):
        raise PrivilegedMaintenanceError(code, "Governed input must be a JSON object.")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], code: str) -> None:
    if set(value) != expected:
        raise PrivilegedMaintenanceError(code, "Governed input fields do not match the contract.")


def _require_sha(value: object, code: str) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None or value == "0" * 40:
        raise PrivilegedMaintenanceError(code, "Expected an exact nonzero lowercase 40-character Git SHA.")
    return value


@dataclass(frozen=True, slots=True)
class PrivilegedValidationAttestation:
    candidate: CandidateRef
    base_sha: str
    changed_files: tuple[str, ...]

    @classmethod
    def load(cls, path: str | Path) -> "PrivilegedValidationAttestation":
        data = _read_object(Path(path), MAX_ATTESTATION_BYTES, "attestation-invalid")
        _exact_keys(
            data,
            {"contract_version", "kind", "candidate", "decision", "scope", "authority", "claims"},
            "attestation-invalid",
        )
        if data["contract_version"] != ATTESTATION_CONTRACT_VERSION or data["kind"] != ATTESTATION_KIND:
            raise PrivilegedMaintenanceError("attestation-contract", "Unsupported privileged attestation contract.")
        if data["decision"] != "pass" or data["scope"] != ATTESTATION_SCOPE:
            raise PrivilegedMaintenanceError("attestation-decision", "Privileged attestation must be an exact PASS for the protected-maintenance scope.")

        candidate = data["candidate"]
        authority = data["authority"]
        claims = data["claims"]
        if not isinstance(candidate, dict) or not isinstance(authority, dict) or not isinstance(claims, dict):
            raise PrivilegedMaintenanceError("attestation-shape", "Privileged attestation sections must be JSON objects.")
        _exact_keys(candidate, {"repository", "pull_request", "base_sha", "head_sha", "changed_files"}, "attestation-candidate")
        _exact_keys(authority, {"repository", "default_branch", "mode"}, "attestation-authority")
        _exact_keys(claims, {"candidate_code_executed", "credentials_used", "exact_candidate_binding"}, "attestation-claims")
        if authority != {
            "repository": AUTHORITY_REPOSITORY,
            "default_branch": AUTHORITY_DEFAULT_BRANCH,
            "mode": ATTESTATION_MODE,
        }:
            raise PrivilegedMaintenanceError("attestation-authority", "Privileged attestation authority identity drifted.")
        if claims != {
            "candidate_code_executed": False,
            "credentials_used": False,
            "exact_candidate_binding": True,
        }:
            raise PrivilegedMaintenanceError("attestation-claims", "Privileged attestation claims drifted.")

        files = candidate["changed_files"]
        if (
            not isinstance(files, list)
            or not files
            or any(not isinstance(path, str) or not path for path in files)
            or files != sorted(files)
            or len(set(files)) != len(files)
        ):
            raise PrivilegedMaintenanceError("attestation-files", "Changed files must be a sorted unique non-empty list.")

        try:
            ref = CandidateRef(
                repository=candidate["repository"],
                pull_request=candidate["pull_request"],
                head_sha=candidate["head_sha"],
            )
            snapshot = CandidateSnapshot(
                repository=ref.repository,
                pull_request=ref.pull_request,
                base_sha=candidate["base_sha"],
                head_sha=ref.head_sha,
                state="open",
                changed_files=tuple(files),
            )
        except (TypeError, ValueError):
            raise PrivilegedMaintenanceError("attestation-candidate", "Privileged attestation candidate identity is invalid.") from None
        if ref.repository != CANDIDATE_REPOSITORY:
            raise PrivilegedMaintenanceError("attestation-repository", "Privileged attestation is fixed to scnehaux/codex.")
        return cls(ref, snapshot.base_sha, snapshot.changed_files)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "contract_version": ATTESTATION_CONTRACT_VERSION,
            "kind": ATTESTATION_KIND,
            "candidate": {
                "repository": self.candidate.repository,
                "pull_request": self.candidate.pull_request,
                "base_sha": self.base_sha,
                "head_sha": self.candidate.head_sha,
                "changed_files": list(self.changed_files),
            },
            "decision": "pass",
            "scope": ATTESTATION_SCOPE,
            "authority": {
                "repository": AUTHORITY_REPOSITORY,
                "default_branch": AUTHORITY_DEFAULT_BRANCH,
                "mode": ATTESTATION_MODE,
            },
            "claims": {
                "candidate_code_executed": False,
                "credentials_used": False,
                "exact_candidate_binding": True,
            },
        }

    @property
    def digest(self) -> str:
        raw = json.dumps(self.to_mapping(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return sha256(raw).hexdigest()

    def authorize(self, request: CandidateRef, envelope: RuntimeDecisionEnvelope) -> RuntimeDecisionEnvelope:
        if request != self.candidate:
            raise PrivilegedMaintenanceError("attestation-request", "Attestation is not bound to the exact requested candidate.")
        snapshot = envelope.snapshot
        if (
            snapshot.repository != self.candidate.repository
            or snapshot.pull_request != self.candidate.pull_request
            or snapshot.base_sha != self.base_sha
            or snapshot.head_sha != self.candidate.head_sha
            or snapshot.changed_files != self.changed_files
        ):
            raise PrivilegedMaintenanceError("attestation-snapshot", "Attestation does not match the independently observed candidate snapshot.")
        if envelope.decision is not AuthorityDecision.FAIL:
            raise PrivilegedMaintenanceError("attestation-not-required", "Privileged validation may only resolve an otherwise failing privilege gate.")
        reasons = frozenset(envelope.reasons)
        if not reasons or not reasons.issubset(ALLOWED_PRIVILEGE_BLOCKERS):
            raise PrivilegedMaintenanceError("attestation-scope", "Privileged validation cannot override non-privilege governance failures.")
        return RuntimeDecisionEnvelope(
            snapshot=envelope.snapshot,
            decision=AuthorityDecision.PASS,
            reasons=(),
            runtime_source_revision=envelope.runtime_source_revision,
            evaluator_source_revision=envelope.evaluator_source_revision,
            source_identity_verified=envelope.source_identity_verified,
            facts_collected_independently=envelope.facts_collected_independently,
            candidate_code_executed=envelope.candidate_code_executed,
            credentials_used=envelope.credentials_used,
        )


def load_maintenance_policy(path: str | Path) -> dict[str, Any]:
    data = _read_object(Path(path), MAX_POLICY_BYTES, "maintenance-policy")
    _exact_keys(
        data,
        {"schema_version", "state", "candidate_repository", "attestation", "bootstrap", "permanent_runtime", "claims"},
        "maintenance-policy",
    )
    if data["schema_version"] != 1 or data["candidate_repository"] != CANDIDATE_REPOSITORY:
        raise PrivilegedMaintenanceError("maintenance-policy", "Privileged-maintenance policy identity drifted.")

    expected_attestation = {
        "repository": AUTHORITY_REPOSITORY,
        "default_branch": AUTHORITY_DEFAULT_BRANCH,
        "path_prefix": "governance/privileged-validations/",
        "contract_version": ATTESTATION_CONTRACT_VERSION,
        "kind": ATTESTATION_KIND,
        "append_only": True,
        "exact_candidate_binding": True,
    }
    if data["attestation"] != expected_attestation:
        raise PrivilegedMaintenanceError("maintenance-policy", "Privileged-attestation policy drifted.")

    bootstrap = data["bootstrap"]
    if not isinstance(bootstrap, dict):
        raise PrivilegedMaintenanceError("maintenance-policy", "Bootstrap policy must be an object.")
    _exact_keys(
        bootstrap,
        {"enabled", "candidate", "allowed_runtime_blockers", "publication_mode", "candidate_code_execution", "evaluation_credentials_allowed"},
        "maintenance-policy",
    )
    if bootstrap["allowed_runtime_blockers"] != sorted(ALLOWED_PRIVILEGE_BLOCKERS):
        raise PrivilegedMaintenanceError("maintenance-policy", "Bootstrap blocker allowlist drifted.")
    if (
        bootstrap["publication_mode"] != "candidate-proof"
        or bootstrap["candidate_code_execution"] is not False
        or bootstrap["evaluation_credentials_allowed"] is not False
    ):
        raise PrivilegedMaintenanceError("maintenance-policy", "Bootstrap safety boundary drifted.")

    permanent_runtime = data["permanent_runtime"]
    if not isinstance(permanent_runtime, dict):
        raise PrivilegedMaintenanceError("maintenance-policy", "Permanent runtime policy must be an object.")
    _exact_keys(
        permanent_runtime,
        {"owner_repository", "state", "attestation_read"},
        "maintenance-policy",
    )
    if (
        permanent_runtime["owner_repository"] != CANDIDATE_REPOSITORY
        or permanent_runtime["attestation_read"] != "public-read-only"
        or permanent_runtime["state"] not in {"not-implemented", "promoted"}
    ):
        raise PrivilegedMaintenanceError("maintenance-policy", "Permanent runtime policy drifted.")

    if bootstrap["enabled"] is False:
        if bootstrap["candidate"] is not None:
            raise PrivilegedMaintenanceError("maintenance-policy", "Disabled bootstrap must not bind a candidate.")
        expected_state = (
            "permanent-runtime"
            if permanent_runtime["state"] == "promoted"
            else "staged-disabled"
        )
        if data["state"] != expected_state:
            raise PrivilegedMaintenanceError("maintenance-policy", "Maintenance state does not match permanent-runtime promotion.")
    elif bootstrap["enabled"] is True:
        candidate = bootstrap["candidate"]
        if (
            data["state"] != "bootstrap-proof"
            or permanent_runtime["state"] != "not-implemented"
            or not isinstance(candidate, dict)
        ):
            raise PrivilegedMaintenanceError("maintenance-policy", "Enabled bootstrap requires one exact candidate binding before permanent promotion.")
        _exact_keys(candidate, {"pull_request", "head_sha"}, "maintenance-policy")
        if type(candidate["pull_request"]) is not int or candidate["pull_request"] <= 0:
            raise PrivilegedMaintenanceError("maintenance-policy", "Bootstrap pull request must be positive.")
        _require_sha(candidate["head_sha"], "maintenance-policy")
    else:
        raise PrivilegedMaintenanceError("maintenance-policy", "Bootstrap enabled flag must be boolean.")
    if data["claims"] != {
        "privileged_governance_maintenance_path_proven": False,
        "effective_enforcement_proven": False,
    }:
        raise PrivilegedMaintenanceError("maintenance-policy", "Privileged-maintenance claims advanced before proof.")
    return data


class PrivilegedBootstrapRuntime:
    """One-candidate bootstrap wrapper around the promoted, credential-free Codex runtime."""

    def __init__(
        self,
        runtime_dir: str | Path,
        attestation: PrivilegedValidationAttestation,
        policy: Mapping[str, Any],
        *,
        python_executable: str | Path = sys.executable,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        bootstrap = policy.get("bootstrap")
        if not isinstance(bootstrap, Mapping) or bootstrap.get("enabled") is not True:
            raise PrivilegedMaintenanceError("bootstrap-disabled", "Privileged bootstrap is disabled by governed policy.")
        candidate = bootstrap.get("candidate")
        if not isinstance(candidate, Mapping):
            raise PrivilegedMaintenanceError("bootstrap-candidate", "Privileged bootstrap has no exact candidate binding.")
        if candidate.get("pull_request") != attestation.candidate.pull_request or candidate.get("head_sha") != attestation.candidate.head_sha:
            raise PrivilegedMaintenanceError("bootstrap-candidate", "Governed bootstrap candidate does not match the attestation.")
        self._runtime_dir = Path(runtime_dir)
        self._attestation = attestation
        self._python = str(Path(python_executable).resolve())
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 300:
            raise ValueError("timeout_seconds must be an integer from 1 to 300")
        self._timeout = timeout_seconds

    def evaluate(self, request: CandidateRef) -> RuntimeDecisionEnvelope:
        if request.repository != CANDIDATE_REPOSITORY:
            raise PrivilegedMaintenanceError("candidate-repository", "Privileged bootstrap is fixed to scnehaux/codex.")
        runtime_adapter.verify_exported_runtime(self._runtime_dir)
        command = [
            self._python,
            "-I",
            str(self._runtime_dir.resolve() / "runtime.py"),
            "--pull-request",
            str(request.pull_request),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=self._runtime_dir.resolve(),
                env=runtime_adapter._clean_environment(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                timeout=self._timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise PrivilegedMaintenanceError("runtime-process", "Promoted runtime process failed or timed out.") from None
        if completed.returncode not in {0, 2}:
            raise PrivilegedMaintenanceError("runtime-failed", "Promoted runtime failed closed outside the supported governance verdicts.")
        if len(completed.stdout) > MAX_RUNTIME_OUTPUT_BYTES or len(completed.stderr) > MAX_RUNTIME_OUTPUT_BYTES:
            raise PrivilegedMaintenanceError("runtime-output-size", "Promoted runtime output exceeded the supported bound.")
        try:
            value = json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeError, ValueError):
            raise PrivilegedMaintenanceError("runtime-json", "Promoted runtime did not return valid UTF-8 JSON.") from None
        try:
            envelope = runtime_adapter._parse_runtime_result(value, request)
        except runtime_adapter.RuntimeAdapterError as exc:
            raise PrivilegedMaintenanceError("runtime-envelope", "Promoted runtime result failed source-bound validation.") from exc

        if completed.returncode == 0:
            if envelope.decision is not AuthorityDecision.PASS:
                raise PrivilegedMaintenanceError("runtime-exit", "Promoted runtime exit code and verdict disagree.")
            raise PrivilegedMaintenanceError("attestation-not-required", "Candidate already passes without privileged bootstrap.")
        if envelope.decision is not AuthorityDecision.FAIL:
            raise PrivilegedMaintenanceError("runtime-exit", "Promoted runtime exit code and verdict disagree.")
        return self._attestation.authorize(request, envelope)
