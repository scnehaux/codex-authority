from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codex_authority import arb_gate  # noqa: E402
from codex_authority.arb_gate import ArbGateError, RequiredApproval  # noqa: E402
from codex_authority.model import CandidateSnapshot  # noqa: E402

SCRIPT = ROOT / "scripts/issue_controlled_permit.py"
SPEC = importlib.util.spec_from_file_location("_tested_issue_controlled_permit", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
PERMIT_SCRIPT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PERMIT_SCRIPT)

GDC = "governance/GDC-000-governance-policy.md"


def gdc(status: str, version: str) -> str:
    return (f"---\ndoc_meta:\n  id: GDC-000\n  title: Policy\n  version: {version}\n  status: {status}\n"
            "  classification: public\n---\n\n# Policy\n")


def record(snapshot, **overrides):
    data = {
        "schema_version": 1, "kind": "codex-arb-approval-record", "decision": "approve",
        "approver": {"name": "Owner", "github": "owner", "role": "repository owner acting as ARB"},
        "subject": {"repository": snapshot.repository, "pull_request": snapshot.pull_request,
                    "head_sha": snapshot.head_sha, "base_sha": snapshot.base_sha,
                    "document": "GDC-000", "version": "1.0.0", "status": "approved"},
        "review": {"date": "2026-10-29", "rubric": "GDC-002", "score": "9/10", "notes": "n"},
        "review_exception": {"status": "active-zero-mandatory-approvals"},
    }
    for dotted, value in overrides.items():
        target = data
        *parents, leaf = dotted.split("__")
        for part in parents:
            target = target[part]
        target[leaf] = value
    return data


class ArbGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "codex"
        self.records = Path(self.temp.name) / "arb-approvals"
        self.records.mkdir()
        self.repo.mkdir()
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
        self.git("init", "-q")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], env=self.env, check=True,
                              stdout=subprocess.PIPE, text=True).stdout.strip()

    def commit(self, files: dict[str, str | None]) -> str:
        for name, content in files.items():
            path = self.repo / name
            if content is None:
                path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode())
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "c")
        return self.git("rev-parse", "HEAD")

    def snapshot(self, base, head, changed=(GDC,)):
        return CandidateSnapshot("scnehaux/codex", 48, base, head, "open", tuple(changed))

    def write_record(self, snapshot, data=None):
        path = self.records / f"GDC-000-1.0.0-{snapshot.head_sha}.json"
        path.write_text(json.dumps(record(snapshot) if data is None else data))
        return path

    def test_front_matter_reads_doc_meta_only(self):
        meta = arb_gate.front_matter(gdc("approved", "1.0.0").replace("\n", "\r\n"))
        self.assertEqual(meta, {"id": "GDC-000", "version": "1.0.0", "status": "approved"})
        self.assertEqual(arb_gate.front_matter("# no front matter\nstatus: approved\n"), {})

    def test_draft_to_approved_promotion_requires_record(self):
        base = self.commit({GDC: gdc("draft", "0.1.0")})
        head = self.commit({GDC: gdc("approved", "1.0.0")})
        required = arb_gate.required_approvals(self.snapshot(base, head), self.repo)
        self.assertEqual(required, (RequiredApproval("GDC-000", "1.0.0", GDC),))

    def test_new_approved_gdc_requires_record(self):
        base = self.commit({"README.md": "r"})
        head = self.commit({GDC: gdc("approved", "1.0.0")})
        self.assertEqual(len(arb_gate.required_approvals(self.snapshot(base, head), self.repo)), 1)

    def test_approved_version_change_requires_record(self):
        base = self.commit({GDC: gdc("approved", "1.0.0")})
        head = self.commit({GDC: gdc("approved", "1.1.0")})
        required = arb_gate.required_approvals(self.snapshot(base, head), self.repo)
        self.assertEqual([item.version for item in required], ["1.1.0"])

    def test_draft_edits_and_other_files_need_no_record(self):
        base = self.commit({GDC: gdc("draft", "0.1.0"), "PLAN.md": "a"})
        head = self.commit({GDC: gdc("draft", "0.2.0"), "PLAN.md": "b"})
        snapshot = self.snapshot(base, head, (GDC, "PLAN.md"))
        self.assertEqual(arb_gate.required_approvals(snapshot, self.repo), ())
        self.assertEqual(arb_gate.check(snapshot, self.repo, self.records), ())

    def test_unchanged_approved_metadata_needs_no_record(self):
        base = self.commit({GDC: gdc("approved", "1.0.0")})
        head = self.commit({GDC: gdc("approved", "1.0.0") + "typo fix\n"})
        self.assertEqual(arb_gate.required_approvals(self.snapshot(base, head), self.repo), ())

    def test_removed_gdc_fails_closed(self):
        base = self.commit({GDC: gdc("approved", "1.0.0")})
        head = self.commit({GDC: None, "README.md": "r"})
        with self.assertRaises(ArbGateError) as caught:
            arb_gate.required_approvals(self.snapshot(base, head), self.repo)
        self.assertEqual(caught.exception.reason, "arb-gate-gdc-removed")

    def test_missing_codex_objects_fail_closed(self):
        base = self.commit({GDC: gdc("draft", "0.1.0")})
        with self.assertRaises(ArbGateError) as caught:
            arb_gate.required_approvals(self.snapshot(base, "f" * 40), self.repo)
        self.assertEqual(caught.exception.reason, "arb-gate-codex-commit-missing")

    def test_promotion_without_record_is_blocked(self):
        base = self.commit({GDC: gdc("draft", "0.1.0")})
        head = self.commit({GDC: gdc("approved", "1.0.0")})
        with self.assertRaises(ArbGateError) as caught:
            arb_gate.check(self.snapshot(base, head), self.repo, self.records)
        self.assertEqual(caught.exception.reason, "arb-approval-record-missing:GDC-000-1.0.0")

    def test_valid_record_passes(self):
        base = self.commit({GDC: gdc("draft", "0.1.0")})
        head = self.commit({GDC: gdc("approved", "1.0.0")})
        snapshot = self.snapshot(base, head)
        path = self.write_record(snapshot)
        self.assertEqual(arb_gate.check(snapshot, self.repo, self.records), (path,))

    def test_mismatched_or_weak_records_are_blocked(self):
        base = self.commit({GDC: gdc("draft", "0.1.0")})
        head = self.commit({GDC: gdc("approved", "1.0.0")})
        snapshot = self.snapshot(base, head)
        for overrides in ({"subject__head_sha": "a" * 40}, {"subject__pull_request": 47},
                          {"subject__version": "1.0.1"}, {"decision": "reject"},
                          {"review__score": "8/10"}, {"review__date": "29 October"},
                          {"approver__name": " "}, {"review_exception": "none"}, {"kind": "other"}):
            with self.subTest(overrides=overrides):
                self.write_record(snapshot, record(snapshot, **overrides))
                with self.assertRaises(ArbGateError) as caught:
                    arb_gate.check(snapshot, self.repo, self.records)
                self.assertEqual(caught.exception.reason, "arb-approval-record-invalid:GDC-000-1.0.0")

    def test_checked_in_records_are_well_formed(self):
        for path in sorted(arb_gate.RECORD_DIR.glob("*.json")):
            with self.subTest(record=path.name):
                data = json.loads(path.read_bytes())
                subject = data["subject"]
                self.assertEqual(path.name, f"{subject['document']}-{subject['version']}-{subject['head_sha']}.json")
                snapshot = CandidateSnapshot(subject["repository"], subject["pull_request"], subject["base_sha"],
                                             subject["head_sha"], "open", (GDC,))
                arb_gate.validate_record(data, snapshot,
                                         RequiredApproval(subject["document"], subject["version"], ""))


class PermitScriptGateTests(unittest.TestCase):
    def run_script(self, check):
        snapshot = CandidateSnapshot("scnehaux/codex", 48, "b" * 40, "a" * 40, "open", (GDC,))
        permit = SimpleNamespace(to_mapping=lambda: {"p": 1}, digest="d" * 64)
        result = SimpleNamespace(permit=permit, outcome=SimpleNamespace(snapshot=snapshot, reasons=(), evidence_recorded=True),
                                 evidence_digest="e" * 64, receipt_digest="r" * 64)
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(PERMIT_SCRIPT, "prepare_attested_permit", return_value=result), \
                patch.object(PERMIT_SCRIPT, "check_arb_approvals", side_effect=check) as gate, \
                contextlib.redirect_stdout(out):
            permit_path = Path(directory) / "permit.json"
            code = PERMIT_SCRIPT.main(["--mode", "attested-v2", "--runtime-dir", directory, "--pull-request", "48",
                                       "--head-sha", "a" * 40, "--evidence-out", str(Path(directory) / "e.json"),
                                       "--receipt-out", str(Path(directory) / "r.json"),
                                       "--permit-out", str(permit_path)])
            return code, json.loads(out.getvalue()), permit_path.exists(), gate

    def test_gate_failure_withholds_permit(self):
        def refuse(*_):
            raise ArbGateError("arb-approval-record-missing:GDC-000-1.0.0")
        code, report, exported, gate = self.run_script(refuse)
        self.assertEqual(code, 2)
        self.assertEqual(report["reasons"], ["arb-approval-record-missing:GDC-000-1.0.0"])
        self.assertFalse(report["permit_exported"])
        self.assertFalse(exported)
        gate.assert_called_once()

    def test_gate_pass_exports_permit(self):
        code, report, exported, _ = self.run_script(lambda *_: ())
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "controlled_permit_prepared")
        self.assertTrue(exported)


if __name__ == "__main__":
    unittest.main()
