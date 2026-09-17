"""Actual Codex reader/collector through controlled publisher with synthetic transport.

No credentials are loaded; all provider calls are mocks. Source execution is test
execution, never privileged approval of the installing Codex candidate.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "scripts"))

from codex_authority.adapters.attested_runtime import blob_id, read_regular
from codex_authority.attested_contract import DEPENDENCY_BLOBS
from codex_authority.attested_handover import REVIEW_BLOB, REVIEW_HEAD
from test_attested_handover import exercise_pipeline
from test_controlled_publication import bootstrap_pipeline, publish_synthetic
from verify_attested_compatibility import FakeGitHub


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-root", type=Path, required=True)
    args = parser.parse_args()
    source = args.codex_root.resolve()
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True, timeout=10).strip()
    if revision != REVIEW_HEAD:
        raise SystemExit("unexpected Codex compatibility input")
    package = source / "integrations/github-governance-evaluator"
    for name, expected in (("attested_runtime.py", REVIEW_BLOB), *DEPENDENCY_BLOBS):
        if blob_id(read_regular(package / name, 1_000_000)) != expected:
            raise SystemExit("Codex compatibility source mismatch")
    spec = importlib.util.spec_from_file_location("_controlled_test_reader", package / "attested_runtime.py")
    reader = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = reader
    spec.loader.exec_module(reader)
    collector, _ = reader.load_dependencies()
    cases = []
    for mode in ("verified", "runtime-only", "unprotected", "missing", "qualification-failed", "wrong-base"):
        fake = FakeGitHub(mode)
        try:
            data = reader.collect_and_evaluate(220, fake.get, fake.get_authority)
        except reader.AttestedRuntimeError:
            if mode != "wrong-base":
                raise
            cases.append("attested-v2:wrong-base-denied")
            continue
        if mode == "wrong-base":
            raise SystemExit("wrong-base approval accepted")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            prepared, _ = exercise_pipeline(data, directory, runtime_revision=REVIEW_HEAD)
            expected = mode in {"verified", "runtime-only", "unprotected"}
            if (prepared.permit is not None) != expected:
                raise SystemExit("v2 permit outcome mismatch")
            if expected:
                result, _, _ = publish_synthetic(directory)
                if result["status"] != "published":
                    raise SystemExit("synthetic publication did not complete")
        cases.append("attested-v2:" + mode)
    for mode in ("verified", "unprotected", "qualification-failed"):
        fake = FakeGitHub(mode)
        data = collector.collect_and_evaluate(220, fake.get)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            prepared = bootstrap_pipeline(directory, data)
            if (prepared.permit is not None) != (mode == "verified"):
                raise SystemExit("bootstrap permit outcome mismatch")
            if prepared.permit is not None:
                result, _, _ = publish_synthetic(directory, "bootstrap-v1")
                if result["status"] != "published":
                    raise SystemExit("bootstrap synthetic publication failed")
        cases.append("bootstrap-v1:" + mode)
    print(json.dumps({"status": "controlled_cross_repository_compatibility_pass", "cases": cases,
                      "codex_source": REVIEW_HEAD, "real_credentials_used": False,
                      "provider_writes_performed": False, "operational_promotion": False,
                      "effective_enforcement_proven": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
