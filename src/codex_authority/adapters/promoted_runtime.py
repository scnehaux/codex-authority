from __future__ import annotations

from hashlib import sha1
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any

from ..model import (
    AuthorityDecision,
    CandidateRef,
    CandidateSnapshot,
    RuntimeDecisionEnvelope,
)


REPOSITORY = "scnehaux/codex"
RUNTIME_SOURCE_REVISION = "cbd64f78c8f72f28880d4673729a796b249d8eae"
RUNTIME_SOURCE_BLOB = "c59911e9c0800c917fed21e6f33f3181c3a61e60"
EVALUATOR_SOURCE_REVISION = "23b05a855419b86b61b0c9266805bb66b143c366"
EVALUATOR_SOURCE_BLOB = "ab2f152c21bd6d6f22df21172c4d027035ff8c11"
QUALIFICATION_CONTEXT = "Governance Qualification"
QUALIFICATION_APP_ID = 15368
MAX_RUNTIME_OUTPUT_BYTES = 1_000_000
DEFAULT_TIMEOUT_SECONDS = 60
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_ENV = {
    "COMSPEC",
    "HOME",
    "PATH",
    "PATHEXT",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "TMPDIR",
    "USERPROFILE",
    "WINDIR",
}


class RuntimeAdapterError(Exception):
    """Fail-closed boundary error with no candidate or environment secret material."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _inside_git(path: Path) -> bool:
    resolved = path.resolve()
    return any((parent / ".git").exists() for parent in (resolved, *resolved.parents))


def _git_blob_sha(path: Path) -> str:
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise OSError
        raw = path.read_bytes()
    except OSError:
        raise RuntimeAdapterError(
            "runtime-source",
            "Promoted runtime source is missing or is not a regular file.",
        ) from None
    if len(raw) > 1_000_000:
        raise RuntimeAdapterError(
            "runtime-source",
            "Promoted runtime source exceeds the supported size.",
        )
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def verify_exported_runtime(runtime_dir: Path) -> None:
    package = runtime_dir.expanduser().resolve()
    if _inside_git(package):
        raise RuntimeAdapterError(
            "runtime-checkout",
            "Promoted Codex runtime must be exported outside every Git checkout.",
        )
    runtime = package / "runtime.py"
    evaluator = package / "evaluator.py"
    promotion = package / "promotion.json"
    runtime_promotion = package / "runtime-promotion.json"
    for path in (runtime, evaluator, promotion, runtime_promotion):
        try:
            if not stat.S_ISREG(path.lstat().st_mode):
                raise OSError
        except OSError:
            raise RuntimeAdapterError(
                "runtime-source",
                "Exported runtime package is incomplete.",
            ) from None
    if _git_blob_sha(runtime) != RUNTIME_SOURCE_BLOB:
        raise RuntimeAdapterError(
            "runtime-blob-mismatch",
            "Exported runtime.py does not match the promoted Git blob.",
        )
    if _git_blob_sha(evaluator) != EVALUATOR_SOURCE_BLOB:
        raise RuntimeAdapterError(
            "evaluator-blob-mismatch",
            "Exported evaluator.py does not match the promoted Git blob.",
        )
    try:
        contract = json.loads(runtime_promotion.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise RuntimeAdapterError(
            "runtime-promotion",
            "Exported runtime promotion contract is unreadable or invalid.",
        ) from None
    expected_source = {
        "schema_version": 1,
        "repository": REPOSITORY,
        "runtime_source_revision": RUNTIME_SOURCE_REVISION,
        "runtime_source_path": "integrations/github-governance-evaluator/runtime.py",
        "runtime_source_blob": RUNTIME_SOURCE_BLOB,
        "evaluator_source_revision": EVALUATOR_SOURCE_REVISION,
        "evaluator_source_blob": EVALUATOR_SOURCE_BLOB,
        "promotion": {
            "mode": "privileged-explicit",
            "state": "runtime-source-pinned",
            "candidate_may_select_effective_revision": False,
            "auto_deploy_from_candidate": False,
        },
        "runtime": {
            "execution_location": "external",
            "exported_copy_required": True,
            "live_instance_proven": False,
            "facts_provenance_verified": False,
            "publish_enabled": False,
            "authority_binding_advanced": False,
            "effective_enforcement_proven": False,
        },
    }
    if contract != expected_source:
        raise RuntimeAdapterError(
            "runtime-promotion",
            "Exported runtime promotion contract drifted from the pinned Codex source.",
        )


def _clean_environment() -> dict[str, str]:
    return {
        name: value
        for name, value in os.environ.items()
        if name.upper() in _ALLOWED_ENV
    }


def _string_list(value: object, code: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise RuntimeAdapterError(code, "Promoted runtime returned malformed reasons.")
    return value


def _parse_runtime_result(
    value: object,
    request: CandidateRef,
) -> RuntimeDecisionEnvelope:
    if not isinstance(value, dict):
        raise RuntimeAdapterError(
            "runtime-output",
            "Promoted runtime output must be a JSON object.",
        )

    required = {
        "schema_version",
        "status",
        "repository",
        "pull_request",
        "base_sha",
        "candidate_sha",
        "authority_source_revision",
        "runtime_source_promoted",
        "facts_collected_independently",
        "facts_provenance_verified",
        "candidate_manifest",
        "collected_facts",
        "candidate_evidence",
        "qualification_evidence",
        "runtime_only_protected_mutations",
        "runtime_failure_reasons",
        "evaluator_result",
        "governance_decision",
        "candidate_code_executed",
        "credentials_used",
        "publish_enabled",
        "authority_binding_advanced",
        "effective_enforcement_proven",
        "notice",
    }
    if set(value) != required:
        raise RuntimeAdapterError(
            "runtime-output",
            "Promoted runtime output fields drifted.",
        )
    if (
        value["schema_version"] != 1
        or value["status"] != "runtime_evaluation_complete"
        or value["repository"] != REPOSITORY
        or value["pull_request"] != request.pull_request
        or value["candidate_sha"] != request.head_sha
        or value["authority_source_revision"] != EVALUATOR_SOURCE_REVISION
        or value["facts_collected_independently"] is not True
        or value["candidate_code_executed"] is not False
        or value["credentials_used"] is not False
    ):
        raise RuntimeAdapterError(
            "runtime-identity",
            "Promoted runtime output is not bound to the exact trusted candidate.",
        )
    if (
        value["runtime_source_promoted"] is not False
        or value["facts_provenance_verified"] is not False
        or value["publish_enabled"] is not False
        or value["authority_binding_advanced"] is not False
        or value["effective_enforcement_proven"] is not False
    ):
        raise RuntimeAdapterError(
            "runtime-self-report",
            "Promoted runtime conservative self-report drifted.",
        )

    manifest = value["candidate_manifest"]
    evidence = value["candidate_evidence"]
    qualification = value["qualification_evidence"]
    evaluator_result = value["evaluator_result"]
    if not all(
        isinstance(item, dict)
        for item in (manifest, evidence, qualification, evaluator_result)
    ):
        raise RuntimeAdapterError(
            "runtime-shape",
            "Promoted runtime returned malformed evidence.",
        )
    if set(manifest) != {
        "schema_version",
        "repository",
        "pull_request",
        "base_sha",
        "head_sha",
        "changed_files",
    }:
        raise RuntimeAdapterError(
            "runtime-manifest",
            "Promoted runtime candidate manifest fields drifted.",
        )
    changed_files = manifest["changed_files"]
    if (
        manifest["schema_version"] != 1
        or manifest["repository"] != request.repository
        or manifest["pull_request"] != request.pull_request
        or manifest["head_sha"] != request.head_sha
        or manifest["base_sha"] != value["base_sha"]
        or not isinstance(changed_files, list)
        or not changed_files
        or any(not isinstance(path, str) or not path for path in changed_files)
    ):
        raise RuntimeAdapterError(
            "runtime-manifest",
            "Promoted runtime candidate manifest is inconsistent.",
        )
    if (
        evidence.get("source") != "github-pull-request-api"
        or evidence.get("pull_state") != "open"
        or evidence.get("base_ref") != "main"
        or evidence.get("identity_verified") is not True
        or evidence.get("changed_files_verified") is not True
    ):
        raise RuntimeAdapterError(
            "runtime-evidence",
            "Promoted runtime candidate provenance is not verified.",
        )
    if (
        qualification.get("source") != "github-checks-api"
        or qualification.get("name") != QUALIFICATION_CONTEXT
        or qualification.get("head_sha") != request.head_sha
        or qualification.get("status") != "completed"
        or qualification.get("app_id") != QUALIFICATION_APP_ID
        or qualification.get("app_slug") != "github-actions"
        or qualification.get("source_verified") is not True
    ):
        raise RuntimeAdapterError(
            "qualification-evidence",
            "Candidate qualification provenance is not bound to GitHub Actions.",
        )

    runtime_reasons = _string_list(
        value["runtime_failure_reasons"],
        "runtime-reasons",
    )
    evaluator_reasons = _string_list(
        evaluator_result.get("failure_reasons"),
        "evaluator-reasons",
    )
    decision_value = value["governance_decision"]
    if decision_value not in {"pass", "fail"}:
        raise RuntimeAdapterError(
            "runtime-decision",
            "Promoted runtime returned an unsupported governance decision.",
        )
    if evaluator_result.get("governance_decision") not in {"pass", "fail"}:
        raise RuntimeAdapterError(
            "evaluator-decision",
            "Promoted evaluator returned an unsupported governance decision.",
        )

    reasons: list[str] = []
    for reason in (*evaluator_reasons, *runtime_reasons):
        if reason not in reasons:
            reasons.append(reason)
    if decision_value == "pass" and reasons:
        raise RuntimeAdapterError(
            "runtime-decision",
            "Passing runtime result must not contain failure reasons.",
        )
    if decision_value == "fail" and not reasons:
        raise RuntimeAdapterError(
            "runtime-decision",
            "Failing runtime result must contain at least one reason.",
        )

    try:
        snapshot = CandidateSnapshot(
            repository=request.repository,
            pull_request=request.pull_request,
            base_sha=value["base_sha"],
            head_sha=request.head_sha,
            state="open",
            changed_files=tuple(changed_files),
        )
        return RuntimeDecisionEnvelope(
            snapshot=snapshot,
            decision=AuthorityDecision(decision_value),
            reasons=tuple(reasons),
            runtime_source_revision=RUNTIME_SOURCE_REVISION,
            evaluator_source_revision=EVALUATOR_SOURCE_REVISION,
            source_identity_verified=True,
            facts_collected_independently=True,
            candidate_code_executed=False,
            credentials_used=False,
        )
    except (TypeError, ValueError) as exc:
        raise RuntimeAdapterError(
            "runtime-envelope",
            "Promoted runtime result could not satisfy the authority envelope.",
        ) from exc


class PromotedCodexRuntime:
    """Adapter that executes only the raw-blob-verified promoted Codex runtime."""

    def __init__(
        self,
        runtime_dir: str | Path,
        *,
        python_executable: str | Path = sys.executable,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._runtime_dir = Path(runtime_dir)
        self._python = str(Path(python_executable).resolve())
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 300:
            raise ValueError("timeout_seconds must be an integer from 1 to 300")
        self._timeout = timeout_seconds

    def evaluate(self, request: CandidateRef) -> RuntimeDecisionEnvelope:
        if request.repository != REPOSITORY:
            raise RuntimeAdapterError(
                "candidate-repository",
                "Promoted runtime adapter is fixed to scnehaux/codex.",
            )
        verify_exported_runtime(self._runtime_dir)
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
                env=_clean_environment(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                timeout=self._timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise RuntimeAdapterError(
                "runtime-process",
                "Promoted runtime process failed or timed out.",
            ) from None
        if completed.returncode != 0:
            raise RuntimeAdapterError(
                "runtime-failed",
                "Promoted runtime failed closed; no permit may be issued.",
            )
        if (
            len(completed.stdout) > MAX_RUNTIME_OUTPUT_BYTES
            or len(completed.stderr) > MAX_RUNTIME_OUTPUT_BYTES
        ):
            raise RuntimeAdapterError(
                "runtime-output-size",
                "Promoted runtime process output exceeded the supported bound.",
            )
        try:
            text = completed.stdout.decode("utf-8")
            value = json.loads(text)
        except (UnicodeError, ValueError):
            raise RuntimeAdapterError(
                "runtime-json",
                "Promoted runtime did not return valid UTF-8 JSON.",
            ) from None
        return _parse_runtime_result(value, request)
