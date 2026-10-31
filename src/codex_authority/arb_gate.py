"""Fail-closed ARB approval gate for GDC promotions (Codex PLAN REC-13-003).

A Codex candidate whose head leaves any ``governance/GDC-*.md`` at status
``approved`` with a version different from its base needs the owner's ARB
approval record for that exact head before a publication permit is exported.
GDC contents are read from local Git objects; no network access is used.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess

from .model import CandidateSnapshot

ROOT = Path(__file__).resolve().parents[2]
RECORD_DIR = ROOT / "governance" / "arb-approvals"
DEFAULT_CODEX_REPO = ROOT.parent / "codex"
RECORD_KIND = "codex-arb-approval-record"
GDC_PATH = re.compile(r"governance/GDC-\d{3}-[^/]+\.md")
META_LINE = re.compile(r"^  (id|version|status):\s*(\S.*?)\s*$")
SCORE = re.compile(r"(9|10)/10")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


class ArbGateError(Exception):
    """The candidate lacks a valid ARB approval record; no permit may be exported."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class RequiredApproval:
    document: str
    version: str
    path: str


def front_matter(text: str) -> dict[str, str]:
    """Return the ``doc_meta`` id/version/status fields of a GDC document."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta: dict[str, str] = {}
    in_doc_meta = False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line.startswith(" "):
            in_doc_meta = line.strip() == "doc_meta:"
            continue
        match = META_LINE.match(line)
        if in_doc_meta and match:
            meta[match.group(1)] = match.group(2)
    return meta


def _git(codex_repo: Path, *args: str) -> subprocess.CompletedProcess:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    try:
        return subprocess.run(["git", "-C", str(codex_repo), *args], env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        raise ArbGateError("arb-gate-git-unavailable") from None


def _blob(codex_repo: Path, revision: str, path: str) -> str | None:
    if _git(codex_repo, "cat-file", "-e", f"{revision}^{{commit}}").returncode != 0:
        raise ArbGateError("arb-gate-codex-commit-missing")
    result = _git(codex_repo, "cat-file", "blob", f"{revision}:{path}")
    if result.returncode != 0:
        return None
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        raise ArbGateError("arb-gate-gdc-encoding") from None


def required_approvals(snapshot: CandidateSnapshot, codex_repo: Path) -> tuple[RequiredApproval, ...]:
    required = []
    for path in snapshot.changed_files:
        if not GDC_PATH.fullmatch(path):
            continue
        head_text = _blob(codex_repo, snapshot.head_sha, path)
        if head_text is None:
            raise ArbGateError("arb-gate-gdc-removed")
        head = front_matter(head_text)
        if head.get("status") != "approved":
            continue
        base_text = _blob(codex_repo, snapshot.base_sha, path)
        base = front_matter(base_text) if base_text is not None else {}
        if base.get("status") == "approved" and base.get("version") == head.get("version"):
            continue
        if not head.get("id") or not head.get("version"):
            raise ArbGateError("arb-gate-gdc-metadata")
        required.append(RequiredApproval(head["id"], head["version"], path))
    return tuple(required)


def validate_record(data: object, snapshot: CandidateSnapshot, approval: RequiredApproval) -> None:
    def require(condition: bool) -> None:
        if not condition:
            raise ArbGateError(f"arb-approval-record-invalid:{approval.document}-{approval.version}")

    require(isinstance(data, dict))
    assert isinstance(data, dict)
    subject, review = data.get("subject"), data.get("review")
    approver, exception = data.get("approver"), data.get("review_exception")
    require(all(isinstance(part, dict) for part in (subject, review, approver, exception)))
    require(data.get("schema_version") == 1 and data.get("kind") == RECORD_KIND and data.get("decision") == "approve")
    require(subject.get("repository") == snapshot.repository and subject.get("pull_request") == snapshot.pull_request
            and subject.get("head_sha") == snapshot.head_sha and subject.get("document") == approval.document
            and subject.get("version") == approval.version and subject.get("status") == "approved")
    require(review.get("rubric") == "GDC-002" and isinstance(review.get("score"), str)
            and SCORE.fullmatch(review["score"]) is not None
            and isinstance(review.get("date"), str) and DATE.fullmatch(review["date"]) is not None)
    require(isinstance(approver.get("name"), str) and approver["name"].strip() != "")
    require(isinstance(exception.get("status"), str) and exception["status"] != "")


def check(snapshot: CandidateSnapshot, codex_repo: Path | None = None,
          record_dir: Path = RECORD_DIR) -> tuple[Path, ...]:
    """Raise ArbGateError unless every GDC promotion in the candidate has a valid record."""
    repo = DEFAULT_CODEX_REPO if codex_repo is None else Path(codex_repo)
    used = []
    for approval in required_approvals(snapshot, repo):
        path = record_dir / f"{approval.document}-{approval.version}-{snapshot.head_sha}.json"
        if not path.is_file() or path.is_symlink():
            raise ArbGateError(f"arb-approval-record-missing:{approval.document}-{approval.version}")
        try:
            data = json.loads(path.read_bytes())
        except (OSError, ValueError):
            raise ArbGateError(f"arb-approval-record-invalid:{approval.document}-{approval.version}") from None
        validate_record(data, snapshot, approval)
        used.append(path)
    return tuple(used)
