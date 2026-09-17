"""Offline v2 handover compatibility only. No network, key, write flag, or publication.

The historical publisher's Config.load still rejects a new runtime revision.
This preview adapts only an in-memory, permanently disabled Config for its existing
permit parser. It is NOT an activation interface or a replacement write contract.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import re
import stat

from publisher_contract import Config, PublisherError, load_permit


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise PublisherError(code, "Offline attested preview rejected inconsistent evidence.")


def _sha(value: object) -> str:
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None
             and value != "0" * 40, "preview-source")
    return value


def _unique(pairs: list[tuple]) -> dict:
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("duplicate key")
        data[key] = value
    return data


def _nonfinite(value: str) -> None:
    raise ValueError("non-finite number")


def _read(path: Path, limit: int) -> tuple[bytes, dict]:
    try:
        _require(stat.S_ISREG(path.lstat().st_mode), "preview-file-type")
        with path.open("rb") as handle:
            raw = handle.read(limit + 1)
        _require(0 < len(raw) <= limit, "preview-size")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_nonfinite)
    except (OSError, ValueError, UnicodeError, RecursionError):
        raise PublisherError("preview-input", "Cannot read bounded preview inputs.") from None
    _require(isinstance(value, dict), "preview-object")
    return raw, value


def preview_attested_permit(permit_path: Path, evidence_path: Path, receipt_path: Path, *,
                            expected_runtime_revision: str, expected_authority_revision: str) -> dict:
    """Validate wire compatibility and local links, never authorize a remote operation."""
    _sha(expected_runtime_revision)
    _sha(expected_authority_revision)
    base = Config.load(Path(__file__).with_name("config.json"))
    _require(base.write_mode == "disabled", "preview-requires-disabled")
    # Legacy parser reuse, not legacy Config.load promotion or configuration export.
    config = replace(base, expected_runtime_source_revision=expected_runtime_revision,
                     expected_authority_service_source_revision=expected_authority_revision)
    _, permit_data = _read(permit_path, 32_768)
    publication = permit_data.get("publication")
    _require(isinstance(publication, dict), "preview-permit-publication")
    _require(type(permit_data.get("contract_version")) is int
             and type(publication.get("expected_integration_id")) is int,
             "preview-permit-types")
    permit = load_permit(permit_path, config)
    canonical_permit = json.dumps(permit_data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    _require(permit.digest == sha256(canonical_permit).hexdigest(), "preview-permit-reread")
    evidence_raw, evidence = _read(evidence_path, 1_000_000)
    _, receipt = _read(receipt_path, 32_768)
    _require(set(evidence) == {"schema_version", "kind", "authority_service_source_revision",
             "runtime_package", "decision_record", "runtime_result_json", "runtime_result_sha256"}, "preview-evidence-fields")
    _require(type(evidence["schema_version"]) is int and evidence["schema_version"] == 1
             and evidence["kind"] == "codex-authority-attested-decision-evidence", "preview-evidence-kind")
    _require(set(receipt) == {"schema_version", "kind", "candidate", "source", "evidence_sha256",
             "runtime_result_sha256", "permit_digest"}, "preview-receipt-fields")
    _require(type(receipt["schema_version"]) is int and receipt["schema_version"] == 1
             and receipt["kind"] == "codex-attested-permit-receipt", "preview-receipt-kind")
    _require(receipt["permit_digest"] == permit.digest
             and receipt["evidence_sha256"] == sha256(evidence_raw).hexdigest()
             and receipt["candidate"] == permit_data["candidate"]
             and receipt["source"] == permit_data["source"], "preview-receipt-binding")
    _require(evidence["authority_service_source_revision"] == expected_authority_revision, "preview-authority-source")
    package = evidence["runtime_package"]
    _require(isinstance(package, dict) and package.get("repository") == config.repository
             and package.get("source_revision") == expected_runtime_revision, "preview-runtime-source")
    runtime_json = evidence["runtime_result_json"]
    _require(isinstance(runtime_json, str) and len(runtime_json.encode("utf-8")) <= 512_000, "preview-runtime-data")
    _require(evidence["runtime_result_sha256"] == receipt["runtime_result_sha256"]
             == sha256(runtime_json.encode("utf-8")).hexdigest(), "preview-runtime-digest")
    decision = evidence["decision_record"]
    _require(isinstance(decision, dict) and decision.get("decision") == "pass"
             and decision.get("reasons") == [], "preview-decision")
    snapshot = decision.get("snapshot")
    _require(isinstance(snapshot, dict) and snapshot.get("state") == "open", "preview-snapshot")
    candidate = permit_data["candidate"]
    _require(all(snapshot.get(k) == v for k, v in candidate.items()), "preview-candidate")
    _require(decision.get("request") == {k: candidate[k] for k in ("repository", "pull_request", "head_sha")}
             and decision.get("source") == {k: permit_data["source"][k]
                 for k in ("runtime_source_revision", "evaluator_source_revision")}, "preview-decision-source")
    return {"status": "attested_permit_preview_only", "write_mode": config.write_mode,
            "repository": permit.repository, "pull_request": permit.pull_request,
            "candidate_sha": permit.head_sha, "permit_digest": permit.digest,
            "evidence_sha256": receipt["evidence_sha256"], "remote_mutations": 0,
            "publisher_live_proven": False, "effective_enforcement_proven": False}
