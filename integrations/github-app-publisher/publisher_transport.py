from __future__ import annotations

from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import stat
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from publisher_contract import (
    APP_ID, CHECK_CONTEXT, Config, INSTALLATION_ID, Permit, PublisherError, REPOSITORY,
    _inside_git, _is_sha,
)

API_ROOT = "https://api.github.com"
API_VERSION = "2026-03-10"
USER_AGENT = "scnehaux-codex-authority-publisher/0.1"
MAX_RESPONSE_BYTES = 1_000_000
KEY_MAX_BYTES = 32_768
TOKEN_PERMISSIONS = {
    "checks": "write",
    "contents": "read",
    "metadata": "read",
    "pull_requests": "read",
}
REQUIRED_INSTALLATION_PERMISSIONS = dict(TOKEN_PERMISSIONS)

def default_key_path() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
        return root / "scnehaux-codex-authority/secrets/github-app.pem"
    return Path.home() / ".local/share/scnehaux-codex-authority/secrets/github-app.pem"


def make_jwt(key_path: Path, client_id: str) -> str:
    original = key_path.expanduser().absolute()
    try:
        info = original.lstat()
        key = original.resolve(strict=True)
    except OSError:
        raise PublisherError("key-missing", "GitHub App private key was not found outside the repository.") from None
    if not stat.S_ISREG(info.st_mode):
        raise PublisherError("key-type", "Private key must be a regular file, not a symlink or directory.")
    if _inside_git(key) or key.is_relative_to(Path(__file__).resolve().parent):
        raise PublisherError("key-location", "Private key must stay outside all Git repositories and the publisher kit.")
    if os.name != "nt" and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
        raise PublisherError("key-permissions", "Private key must belong to this user and have chmod 600 permissions.")
    try:
        with key.open("rb") as handle:
            pem = handle.read(KEY_MAX_BYTES + 1)
    except OSError:
        raise PublisherError("key-unreadable", "Private key is not readable by this user.") from None
    if not pem or len(pem) > KEY_MAX_BYTES:
        raise PublisherError("key-size", "Private key is empty or exceeds the supported size.")
    try:
        import jwt
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
    except ImportError:
        raise PublisherError("dependencies-missing", "Install the pinned publisher requirements first.") from None
    try:
        private_key = serialization.load_pem_private_key(pem, password=None)
        if not isinstance(private_key, rsa.RSAPrivateKey) or private_key.key_size < 2048:
            raise ValueError
        now = int(time.time())
        token = jwt.encode(
            {"iat": now - 60, "exp": now + 300, "iss": client_id},
            private_key,
            algorithm="RS256",
        )
        if not isinstance(token, str):
            raise ValueError
        return token
    except Exception:
        raise PublisherError(
            "key-invalid",
            "Use an unencrypted RSA GitHub App PEM private key of at least 2048 bits.",
        ) from None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _path_allowed(path: str, method: str) -> bool:
    escaped_repo = re.escape(REPOSITORY)
    patterns = {
        "GET": (
            r"/app",
            rf"/app/installations/{INSTALLATION_ID}",
            rf"/repos/{escaped_repo}/installation",
            rf"/repos/{escaped_repo}/pulls/[1-9][0-9]*",
        ),
        "POST": (
            rf"/app/installations/{INSTALLATION_ID}/access_tokens",
            rf"/repos/{escaped_repo}/check-runs",
        ),
        "DELETE": (r"/installation/token",),
    }
    return any(re.fullmatch(pattern, path) for pattern in patterns.get(method, ()))


def request_json(
    path: str,
    token: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(path, str) or not _path_allowed(path, method):
        raise PublisherError("api-path", "GitHub API request is outside the publisher allowlist.")
    if not isinstance(token, str) or not token:
        raise PublisherError("api-token", "Publisher authentication token is unavailable.")
    if method in {"GET", "DELETE"} and body is not None:
        raise PublisherError("api-body", "GET and DELETE requests cannot carry a body.")
    if method == "POST" and not isinstance(body, dict):
        raise PublisherError("api-body", "POST request requires a fixed JSON object.")
    if path.endswith("/access_tokens") and body != {
        "repositories": [REPOSITORY.split("/", 1)[1]],
        "permissions": TOKEN_PERMISSIONS,
    }:
        raise PublisherError("token-scope", "Installation token scope drifted.")
    if path.endswith("/check-runs"):
        if (
            set(body or {}) != {"name", "head_sha", "status", "conclusion", "output"}
            or body.get("name") != CHECK_CONTEXT
            or not _is_sha(body.get("head_sha"))
            or body.get("status") != "completed"
            or body.get("conclusion") != "success"
            or not isinstance(body.get("output"), dict)
        ):
            raise PublisherError("check-payload", "Only the fixed successful authority check payload is permitted.")
    request = Request(
        API_ROOT + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        method=method,
    )
    expected = {"GET": 200, "POST": 201, "DELETE": 204}[method]
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            if response.status != expected:
                raise PublisherError("api-status", "Unexpected GitHub API status; publication stopped.")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        status = exc.code
        exc.close()
        messages = {
            401: "GitHub rejected publisher authentication.",
            403: "GitHub denied the publisher request or rate limit is exhausted.",
            404: "GitHub could not find the bound App, repository, pull request, or commit.",
            422: "GitHub rejected the fixed publisher payload; do not retry automatically.",
        }
        raise PublisherError(
            f"github-http-{status}",
            messages.get(status, "GitHub request failed; no redirect or automatic retry was attempted."),
        ) from None
    except (URLError, TimeoutError, OSError, HTTPException):
        raise PublisherError(
            "network-error",
            "Secure connection to api.github.com failed; publication was not retried.",
        ) from None
    if len(raw) > MAX_RESPONSE_BYTES:
        raise PublisherError("api-response-size", "GitHub response exceeded the supported size.")
    if expected == 204:
        return {}
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError):
        raise PublisherError("api-json", "GitHub returned invalid JSON; publication stopped.") from None
    if not isinstance(data, dict):
        raise PublisherError("api-shape", "GitHub returned an unexpected response shape.")
    return data


def verify_permissions(value: object) -> None:
    if not isinstance(value, dict):
        raise PublisherError("permissions-missing", "Installation permissions are missing.")
    for name, level in REQUIRED_INSTALLATION_PERMISSIONS.items():
        if value.get(name) != level:
            raise PublisherError("permissions-mismatch", "Dedicated App permissions do not match the publisher contract.")
    if any(level != "none" for name, level in value.items() if name not in REQUIRED_INSTALLATION_PERMISSIONS):
        raise PublisherError("permissions-excess", "Remove App permissions outside the dedicated publisher contract.")


def verify_installation(data: dict[str, Any], config: Config) -> None:
    if type(data.get("id")) is not int or data["id"] != config.installation_id:
        raise PublisherError("installation-mismatch", "Installation ID does not match the publisher contract.")
    if type(data.get("app_id")) is not int or data["app_id"] != config.app_id:
        raise PublisherError("installation-app-mismatch", "Installation belongs to a different GitHub App.")
    account = data.get("account")
    if not isinstance(account, dict) or account.get("login", "").lower() != config.repository.split("/", 1)[0].lower():
        raise PublisherError("installation-owner", "Installation owner does not match the repository owner.")
    if data.get("suspended_at", "missing") is not None:
        raise PublisherError("installation-suspended", "Installation is suspended or suspension state is unavailable.")
    if data.get("repository_selection") != "selected":
        raise PublisherError("repository-selection", "Dedicated publisher App must be limited to selected repositories.")
    verify_permissions(data.get("permissions"))


def preflight_app(
    config: Config,
    app_jwt: str,
    request: Callable[..., dict[str, Any]] = request_json,
) -> None:
    app = request("/app", app_jwt)
    if type(app.get("id")) is not int or app["id"] != config.app_id:
        raise PublisherError("app-mismatch", "Private key authenticates as a different GitHub App.")
    installation = request(f"/app/installations/{config.installation_id}", app_jwt)
    verify_installation(installation, config)
    repository_installation = request(f"/repos/{config.repository}/installation", app_jwt)
    verify_installation(repository_installation, config)


def issue_token(
    config: Config,
    app_jwt: str,
    request: Callable[..., dict[str, Any]] = request_json,
) -> str:
    issued = request(
        f"/app/installations/{config.installation_id}/access_tokens",
        app_jwt,
        method="POST",
        body={
            "repositories": [config.repository.split("/", 1)[1]],
            "permissions": TOKEN_PERMISSIONS,
        },
    )
    token = issued.get("token")
    if not isinstance(token, str) or len(token) < 8:
        raise PublisherError("token-invalid", "GitHub returned no usable installation token.")
    if issued.get("permissions") != TOKEN_PERMISSIONS:
        raise PublisherError("token-permissions", "Issued installation token scope drifted.")
    return token


def verify_candidate_pr(data: dict[str, Any], permit: Permit) -> None:
    if data.get("number") != permit.pull_request or data.get("state") != "open":
        raise PublisherError("candidate-pr", "Publisher requires the exact open pull request from the permit.")
    base = data.get("base")
    head = data.get("head")
    if not isinstance(base, dict) or not isinstance(head, dict):
        raise PublisherError("candidate-shape", "GitHub pull request identity is incomplete.")
    base_repo = base.get("repo")
    head_repo = head.get("repo")
    if (
        not isinstance(base_repo, dict)
        or not isinstance(head_repo, dict)
        or base_repo.get("full_name") != permit.repository
        or head_repo.get("full_name") != permit.repository
        or base.get("ref") != "main"
        or base.get("sha") != permit.base_sha
        or head.get("sha") != permit.head_sha
    ):
        raise PublisherError("candidate-identity", "GitHub candidate no longer matches the exact publication permit.")


def check_payload(permit: Permit) -> dict[str, Any]:
    return {
        "name": CHECK_CONTEXT,
        "head_sha": permit.head_sha,
        "status": "completed",
        "conclusion": "success",
        "output": {
            "title": "Codex governance authority passed",
            "summary": (
                f"Independent authority approved PR #{permit.pull_request} at exact head "
                f"{permit.head_sha}. Permit {permit.digest}."
            ),
        },
    }


def verify_check(data: dict[str, Any], config: Config, permit: Permit) -> int:
    app = data.get("app")
    check_id = data.get("id")
    if (
        type(check_id) is not int
        or check_id <= 0
        or data.get("name") != config.check_context
        or data.get("head_sha") != permit.head_sha
        or data.get("status") != "completed"
        or data.get("conclusion") != "success"
        or not isinstance(app, dict)
        or app.get("id") != config.app_id
    ):
        raise PublisherError("check-response", "Returned check run is not bound to the expected App/context/head.")
    return check_id

