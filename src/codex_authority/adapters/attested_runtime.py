"""Source-bound v2 adapter; promotion is supplied only by the Authority boundary."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from threading import Event, Thread

from ..attested_contract import (
    AttestedResult, DEPENDENCY_BLOBS, EVALUATOR_REVISION, HandoverError,
    MAX_RESULT_BYTES, REPOSITORY, require, sha,
)
from ..model import CandidateRef, RuntimeDecisionEnvelope

ENTRYPOINT = "attested_runtime.py"
MAX_SOURCE_BYTES = 1_000_000
DEFAULT_TIMEOUT_SECONDS = 120


def blob_id(raw: bytes) -> str:
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def outside_git(path: Path) -> bool:
    resolved = path.resolve()
    return not any((p / ".git").exists() for p in (resolved, *resolved.parents))


def read_regular(path: Path, limit: int) -> bytes:
    try:
        require(stat.S_ISREG(path.lstat().st_mode), "source-file-type")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as handle:
            require(stat.S_ISREG(os.fstat(handle.fileno()).st_mode), "source-file-type")
            raw = handle.read(limit + 1)
    except OSError:
        raise HandoverError("source-unreadable") from None
    require(0 < len(raw) <= limit, "source-size")
    return raw


@dataclass(frozen=True, slots=True)
class RuntimePackage:
    """An explicitly supplied trusted package identity, NOT an automatic promotion."""
    source_revision: str
    entrypoint_blob: str

    def __post_init__(self) -> None:
        sha(self.source_revision)
        sha(self.entrypoint_blob)

    @property
    def blobs(self) -> tuple[tuple[str, str], ...]:
        return ((ENTRYPOINT, self.entrypoint_blob), *DEPENDENCY_BLOBS)

    def to_mapping(self) -> dict:
        return {"repository": REPOSITORY, "source_revision": self.source_revision,
                "entrypoint": ENTRYPOINT, "blobs": dict(self.blobs)}


def _environment() -> dict[str, str]:
    # Do not inherit tokens, proxies, Python paths, HOME, or user-supplied CA overrides.
    allowed = {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR"}
    result = {name: value for name, value in os.environ.items() if name.upper() in allowed}
    result["PATH"] = os.defpath
    return result


def _run(command: list[str], cwd: Path, timeout: int) -> tuple[int, bytes]:
    """Bound both pipes while draining them; do not accumulate unlimited communicate()."""
    buffers = [bytearray(), bytearray()]
    failed = Event()
    try:
        process = subprocess.Popen(command, cwd=cwd, env=_environment(), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    except OSError:
        raise HandoverError("runtime-process") from None

    def drain(stream, destination: bytearray) -> None:
        try:
            with stream:
                while chunk := stream.read(16_384):
                    if len(destination) + len(chunk) > MAX_RESULT_BYTES:
                        failed.set()
                        process.kill()
                        return
                    destination.extend(chunk)
        except (OSError, ValueError):
            failed.set()
            try:
                process.kill()
            except OSError:
                pass

    threads = [Thread(target=drain, args=(stream, buffer), daemon=True)
               for stream, buffer in zip((process.stdout, process.stderr), buffers, strict=True)]
    try:
        for thread in threads:
            thread.start()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            raise HandoverError("runtime-timeout") from None
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        for thread in threads:
            if thread.ident is not None:
                thread.join(timeout=1)
    require(not failed.is_set() and not any(t.is_alive() for t in threads), "runtime-output-bound")
    require(not buffers[1], "runtime-stderr")
    require(process.returncode in (0, 2), "runtime-exit")
    return process.returncode, bytes(buffers[0])


class AttestedCodexRuntime:
    """One-shot backend. The public handover entrypoint gates this before construction.

    Construction by tests with a synthetic RuntimePackage is not a promotion and
    must never be recorded as an independently authorized operational execution.
    """
    def __init__(self, runtime_dir: str | Path, package: RuntimePackage, *,
                 timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        require(isinstance(package, RuntimePackage), "runtime-package")
        require(type(timeout_seconds) is int and 1 <= timeout_seconds <= 300, "runtime-timeout-setting")
        self.package = package
        self.runtime_dir = Path(runtime_dir)
        self.timeout = timeout_seconds
        self.result: AttestedResult | None = None
        self._used = False

    def evaluate(self, request: CandidateRef) -> RuntimeDecisionEnvelope:
        require(not self._used, "runtime-already-used")
        self._used = True
        self.result = None
        require(request.repository == REPOSITORY, "candidate-repository")
        require(request.head_sha != self.package.source_revision, "candidate-as-authority")
        root = self.runtime_dir.expanduser()
        require(not root.is_symlink() and outside_git(root), "runtime-checkout")
        require(root.is_dir() and {p.name for p in root.iterdir()} == set(dict(self.package.blobs)), "runtime-package-files")
        sources = {}
        for name, expected in self.package.blobs:
            raw = read_regular(root / name, MAX_SOURCE_BYTES)
            require(blob_id(raw) == expected, "runtime-blob-mismatch")
            sources[name] = raw
        # Execute a private snapshot of verified bytes, not a mutable original path or .pyc.
        with tempfile.TemporaryDirectory(prefix="codex-attested-") as temp:
            working = Path(temp)
            require(outside_git(working), "runtime-checkout")
            for name, raw in sources.items():
                (working / name).write_bytes(raw)
            command = [str(Path(sys.executable).resolve()), "-I", "-B", str(working / ENTRYPOINT),
                       "--pull-request", str(request.pull_request)]
            returncode, raw = _run(command, working, self.timeout)
        result = AttestedResult.parse(raw, request)
        require(returncode == (0 if result.decision.value == "pass" else 2), "runtime-exit-verdict")
        self.result = result
        return RuntimeDecisionEnvelope(
            snapshot=result.snapshot, decision=result.decision, reasons=result.reasons,
            runtime_source_revision=self.package.source_revision,
            evaluator_source_revision=EVALUATOR_REVISION, source_identity_verified=True,
            facts_collected_independently=True, candidate_code_executed=False, credentials_used=False,
        )
