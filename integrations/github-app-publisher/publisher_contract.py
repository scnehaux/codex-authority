from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
import stat
from typing import Any

MAX_CONFIG_BYTES = 16_384
MAX_PERMIT_BYTES = 32_768
PERMIT_CONTRACT_VERSION = 1
PERMIT_KIND = "codex-governance-publication-permit"
REPOSITORY = "scnehaux/codex"
CHECK_CONTEXT = "Codex Governance Authority"
APP_ID = 4864946
INSTALLATION_ID = 159870521
EXPECTED_RUNTIME_SOURCE_REVISION = "cbd64f78c8f72f28880d4673729a796b249d8eae"
EXPECTED_EVALUATOR_SOURCE_REVISION = "23b05a855419b86b61b0c9266805bb66b143c366"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLISHER_FILES = ("github_app_publisher.py", "publisher_contract.py", "publisher_transport.py")


class PublisherError(Exception):
    """Operator-safe failure that never renders upstream bodies or credentials."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _is_sha(value: object) -> bool:
    return isinstance(value, str) and SHA_RE.fullmatch(value) is not None

def _read_json_object(path: Path, max_bytes: int, code: str) -> dict[str, Any]:
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise OSError
        with path.open("rb") as handle:
            raw = handle.read(max_bytes + 1)
        if not raw or len(raw) > max_bytes:
            raise ValueError
        value = json.loads(raw)
    except (OSError, ValueError, UnicodeError):
        raise PublisherError(code, "Cannot read a valid bounded JSON object.") from None
    if not isinstance(value, dict):
        raise PublisherError(code, "Expected a JSON object.")
    return value

def _exact_keys(value: dict[str, Any], expected: set[str], code: str) -> None:
    if set(value) != expected:
        raise PublisherError(code, "JSON fields do not match the expected contract.")

@dataclass(frozen=True, slots=True)
class Config:
    app_id: int
    installation_id: int
    client_id: str
    repository: str
    check_context: str
    permit_kind: str
    expected_runtime_source_revision: str
    expected_evaluator_source_revision: str
    expected_authority_service_source_revision: str | None
    publisher_source_revision: str | None
    publisher_source_blobs: dict[str, str] | None
    write_mode: str
    proof_head_sha: str | None
    proof_permit_digest: str | None
    live_proven: bool

    @classmethod
    def load(cls, path: Path) -> Config:
        data = _read_json_object(path, MAX_CONFIG_BYTES, "config-invalid")
        _exact_keys(
            data,
            {
                "config_version",
                "app_id",
                "installation_id",
                "client_id",
                "repository",
                "check_context",
                "permit_kind",
                "expected_runtime_source_revision",
                "expected_evaluator_source_revision",
                "expected_authority_service_source_revision",
                "publisher_source_revision",
                "publisher_source_blobs",
                "write_mode",
                "proof_head_sha",
                "proof_permit_digest",
                "live_proven",
            },
            "config-invalid",
        )
        if type(data["config_version"]) is not int or data["config_version"] != 1:
            raise PublisherError("config-version", "Unsupported publisher config version.")
        if data["app_id"] != APP_ID or type(data["app_id"]) is not int:
            raise PublisherError("config-app", "Publisher App ID drifted.")
        if data["installation_id"] != INSTALLATION_ID or type(data["installation_id"]) is not int:
            raise PublisherError("config-installation", "Publisher Installation ID drifted.")
        client_id = data["client_id"]
        if not isinstance(client_id, str) or re.fullmatch(r"[A-Za-z0-9]{8,128}", client_id) is None:
            raise PublisherError("config-client", "Client ID must be the public alphanumeric identifier.")
        if data["repository"] != REPOSITORY:
            raise PublisherError("config-repository", "Publisher repository is fixed to scnehaux/codex.")
        if data["check_context"] != CHECK_CONTEXT:
            raise PublisherError("config-context", "Publisher check context drifted.")
        if data["permit_kind"] != PERMIT_KIND:
            raise PublisherError("config-permit", "Publication permit kind drifted.")
        if data["expected_runtime_source_revision"] != EXPECTED_RUNTIME_SOURCE_REVISION:
            raise PublisherError("config-runtime-source", "Promoted Codex runtime source drifted.")
        if data["expected_evaluator_source_revision"] != EXPECTED_EVALUATOR_SOURCE_REVISION:
            raise PublisherError("config-evaluator-source", "Promoted Codex evaluator source drifted.")
        if data["write_mode"] not in {"disabled", "proof"}:
            raise PublisherError("config-write-mode", "Standalone publisher supports only disabled or single-candidate proof mode.")
        if data["live_proven"] is not False:
            raise PublisherError("config-live-proof", "Standalone publisher cannot claim live promotion.")

        source_fields = (
            data["expected_authority_service_source_revision"],
            data["publisher_source_revision"],
            data["publisher_source_blobs"],
        )
        if data["write_mode"] == "disabled":
            if (
                source_fields != (None, None, None)
                or data["proof_head_sha"] is not None
                or data["proof_permit_digest"] is not None
                or data["live_proven"] is not False
            ):
                raise PublisherError(
                    "config-disabled",
                    "Disabled publisher must not carry promoted write identities or live-proof claims.",
                )
        else:
            authority_revision, publisher_revision, publisher_blobs = source_fields
            if not _is_sha(authority_revision) or not _is_sha(publisher_revision):
                raise PublisherError(
                    "config-source-unbound",
                    "Write mode requires pinned authority-service and publisher source identities.",
                )
            if (
                not isinstance(publisher_blobs, dict)
                or set(publisher_blobs) != set(PUBLISHER_FILES)
                or any(not _is_sha(value) for value in publisher_blobs.values())
            ):
                raise PublisherError(
                    "config-source-unbound",
                    "Write mode requires exact Git blobs for the complete publisher source set.",
                )
            if (
                not _is_sha(data["proof_head_sha"])
                or not isinstance(data["proof_permit_digest"], str)
                or SHA256_RE.fullmatch(data["proof_permit_digest"]) is None
                or data["live_proven"] is not False
            ):
                raise PublisherError(
                    "config-proof",
                    "Proof mode requires one exact candidate SHA and exact promoted permit digest.",
                )

        return cls(
            app_id=data["app_id"],
            installation_id=data["installation_id"],
            client_id=client_id,
            repository=data["repository"],
            check_context=data["check_context"],
            permit_kind=data["permit_kind"],
            expected_runtime_source_revision=data["expected_runtime_source_revision"],
            expected_evaluator_source_revision=data["expected_evaluator_source_revision"],
            expected_authority_service_source_revision=data[
                "expected_authority_service_source_revision"
            ],
            publisher_source_revision=data["publisher_source_revision"],
            publisher_source_blobs=data["publisher_source_blobs"],
            write_mode=data["write_mode"],
            proof_head_sha=data["proof_head_sha"],
            proof_permit_digest=data["proof_permit_digest"],
            live_proven=data["live_proven"],
        )


@dataclass(frozen=True, slots=True)
class Permit:
    repository: str
    pull_request: int
    base_sha: str
    head_sha: str
    runtime_source_revision: str
    evaluator_source_revision: str
    authority_service_source_revision: str
    digest: str


def load_permit(path: Path, config: Config) -> Permit:
    data = _read_json_object(path, MAX_PERMIT_BYTES, "permit-invalid")
    _exact_keys(
        data,
        {
            "contract_version",
            "kind",
            "candidate",
            "decision",
            "source",
            "evidence",
            "publication",
        },
        "permit-invalid",
    )
    if data["contract_version"] != PERMIT_CONTRACT_VERSION or data["kind"] != config.permit_kind:
        raise PublisherError("permit-contract", "Unsupported publication permit contract.")
    candidate = data["candidate"]
    source = data["source"]
    evidence = data["evidence"]
    publication = data["publication"]
    for value, expected, code in (
        (candidate, {"repository", "pull_request", "base_sha", "head_sha"}, "permit-candidate"),
        (
            source,
            {"runtime_source_revision", "evaluator_source_revision", "authority_service_source_revision"},
            "permit-source",
        ),
        (evidence, {"recorded"}, "permit-evidence"),
        (
            publication,
            {"provider", "check_context", "expected_integration_id", "conclusion"},
            "permit-publication",
        ),
    ):
        if not isinstance(value, dict):
            raise PublisherError(code, "Publication permit section must be a JSON object.")
        _exact_keys(value, expected, code)
    if data["decision"] != "pass" or evidence["recorded"] is not True:
        raise PublisherError("permit-decision", "Only an evidenced PASS may be published.")
    if candidate["repository"] != config.repository:
        raise PublisherError("permit-repository", "Publication permit repository drifted.")
    if type(candidate["pull_request"]) is not int or candidate["pull_request"] <= 0:
        raise PublisherError("permit-pull-request", "Publication permit PR number is invalid.")
    if not _is_sha(candidate["base_sha"]) or not _is_sha(candidate["head_sha"]) or candidate["base_sha"] == candidate["head_sha"]:
        raise PublisherError("permit-sha", "Publication permit candidate SHAs are invalid.")
    if source["runtime_source_revision"] != config.expected_runtime_source_revision:
        raise PublisherError("permit-runtime-source", "Publication permit runtime source is not promoted.")
    if source["evaluator_source_revision"] != config.expected_evaluator_source_revision:
        raise PublisherError("permit-evaluator-source", "Publication permit evaluator source is not promoted.")
    if not _is_sha(source["authority_service_source_revision"]):
        raise PublisherError("permit-authority-source", "Publication permit authority-service source is invalid.")
    if config.expected_authority_service_source_revision is not None and source["authority_service_source_revision"] != config.expected_authority_service_source_revision:
        raise PublisherError("permit-authority-source", "Publication permit authority-service source is not promoted.")
    if publication != {
        "provider": "github",
        "check_context": config.check_context,
        "expected_integration_id": config.app_id,
        "conclusion": "success",
    }:
        raise PublisherError("permit-publication", "Publication permit capability drifted.")
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = sha256(canonical).hexdigest()
    return Permit(
        repository=candidate["repository"],
        pull_request=candidate["pull_request"],
        base_sha=candidate["base_sha"],
        head_sha=candidate["head_sha"],
        runtime_source_revision=source["runtime_source_revision"],
        evaluator_source_revision=source["evaluator_source_revision"],
        authority_service_source_revision=source["authority_service_source_revision"],
        digest=digest,
    )


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
        raise PublisherError("publisher-source", "Publisher source is missing or not a regular file.") from None
    if len(raw) > 1_000_000:
        raise PublisherError("publisher-source", "Publisher source exceeds the supported size.")
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()




def verify_exported_publisher(config_path: Path, permit_path: Path, config: Config) -> None:
    package = Path(__file__).resolve().parent
    if _inside_git(package) or _inside_git(config_path) or _inside_git(permit_path):
        raise PublisherError(
            "publisher-checkout",
            "Authenticated publication requires exported publisher/config/permit copies outside every Git checkout.",
        )
    if not _is_sha(config.publisher_source_revision) or not isinstance(config.publisher_source_blobs, dict):
        raise PublisherError("publisher-source-unbound", "Publisher source revision is not promoted.")
    for name in PUBLISHER_FILES:
        expected = config.publisher_source_blobs.get(name)
        if expected is None or _git_blob_sha(package / name) != expected:
            raise PublisherError(
                "publisher-blob-mismatch",
                "Exported publisher package does not match the promoted Git blobs.",
            )
