from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codex_authority.evidence import EvidenceWriteError, SingleRecordEvidenceSink  # noqa: E402
from codex_authority.model import (  # noqa: E402
    AuthorityDecision,
    CandidateRef,
    CandidateSnapshot,
    EvidenceRecord,
)


BASE = "1" * 40
HEAD = "2" * 40
RUNTIME = "3" * 40
EVALUATOR = "4" * 40


def record():
    request = CandidateRef("scnehaux/codex", 17, HEAD)
    snapshot = CandidateSnapshot(
        repository=request.repository,
        pull_request=request.pull_request,
        base_sha=BASE,
        head_sha=HEAD,
        state="open",
        changed_files=(".gitignore",),
    )
    return EvidenceRecord(
        request=request,
        decision=AuthorityDecision.PASS,
        reasons=(),
        snapshot=snapshot,
        runtime_source_revision=RUNTIME,
        evaluator_source_revision=EVALUATOR,
    )


class DurableEvidenceTests(unittest.TestCase):
    def test_creates_one_durable_exact_record_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "evidence" / "decision.json"
            sink = SingleRecordEvidenceSink(path)
            sink.append(record())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "codex-authority-decision-evidence")
            self.assertEqual(data["decision"], "pass")
            self.assertEqual(data["request"]["head_sha"], HEAD)
            self.assertEqual(data["snapshot"]["changed_files"], [".gitignore"])
            with self.assertRaises(EvidenceWriteError):
                sink.append(record())

    def test_refuses_operational_evidence_inside_git_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            path = root / "proof" / "decision.json"
            with self.assertRaises(EvidenceWriteError):
                SingleRecordEvidenceSink(path).append(record())


if __name__ == "__main__":
    unittest.main()
