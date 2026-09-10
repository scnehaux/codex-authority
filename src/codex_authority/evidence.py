from __future__ import annotations

import json
import os
from pathlib import Path
import stat
from typing import Any

from .model import EvidenceRecord


class EvidenceWriteError(Exception):
    """Durable evidence could not be created safely."""


def _inside_git(path: Path) -> bool:
    resolved = path.resolve()
    return any((parent / ".git").exists() for parent in (resolved, *resolved.parents))


def _record_mapping(record: EvidenceRecord) -> dict[str, Any]:
    snapshot = record.snapshot
    return {
        "schema_version": 1,
        "kind": "codex-authority-decision-evidence",
        "request": {
            "repository": record.request.repository,
            "pull_request": record.request.pull_request,
            "head_sha": record.request.head_sha,
        },
        "decision": record.decision.value,
        "reasons": list(record.reasons),
        "snapshot": (
            None
            if snapshot is None
            else {
                "repository": snapshot.repository,
                "pull_request": snapshot.pull_request,
                "base_sha": snapshot.base_sha,
                "head_sha": snapshot.head_sha,
                "state": snapshot.state,
                "changed_files": list(snapshot.changed_files),
            }
        ),
        "source": {
            "runtime_source_revision": record.runtime_source_revision,
            "evaluator_source_revision": record.evaluator_source_revision,
        },
    }


def write_new_json_file(path: str | Path, value: dict[str, Any]) -> None:
    target = Path(path).expanduser()
    parent = target.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
        parent = parent.resolve(strict=True)
    except OSError:
        raise EvidenceWriteError("evidence parent directory could not be prepared") from None
    if _inside_git(parent):
        raise EvidenceWriteError("operational evidence must be written outside every Git checkout")
    target = parent / target.name
    if not target.name or target.name in {".", ".."}:
        raise EvidenceWriteError("evidence filename is invalid")
    if target.exists() or target.is_symlink():
        raise EvidenceWriteError("evidence output already exists")
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(raw) > 1_000_000:
        raise EvidenceWriteError("evidence record exceeds the supported size")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(target, flags, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError:
        raise EvidenceWriteError("evidence record could not be durably created") from None
    try:
        info = target.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise OSError
    except OSError:
        raise EvidenceWriteError("evidence output is not a regular file") from None


class SingleRecordEvidenceSink:
    """One-shot durable sink for controlled proof executions."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def append(self, record: EvidenceRecord) -> None:
        if not isinstance(record, EvidenceRecord):
            raise EvidenceWriteError("authority evidence record type is invalid")
        write_new_json_file(self._path, _record_mapping(record))
