from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class AuthorityPolicy:
    candidate_repository: str
    authority_check_context: str
    github_app_id: int
    execution_location: str
    candidate_code_execution: bool
    candidate_may_select_effective_revision: bool
    candidate_may_auto_deploy_authority: bool
    credentials_may_be_stored_in_repository: bool


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def load_authority_policy(path: str | Path) -> AuthorityPolicy:
    data = _object(json.loads(Path(path).read_text(encoding="utf-8")), "authority")
    if data.get("schema_version") != 1:
        raise ValueError("unsupported authority policy schema_version")

    execution = _object(data.get("execution"), "execution")
    trust = _object(data.get("trust"), "trust")
    app_id = data.get("github_app_id")
    if type(app_id) is not int or app_id <= 0:
        raise ValueError("github_app_id must be a positive integer")

    policy = AuthorityPolicy(
        candidate_repository=data.get("candidate_repository"),
        authority_check_context=data.get("authority_check_context"),
        github_app_id=app_id,
        execution_location=execution.get("location"),
        candidate_code_execution=execution.get("candidate_code_execution"),
        candidate_may_select_effective_revision=trust.get(
            "candidate_may_select_effective_revision"
        ),
        candidate_may_auto_deploy_authority=trust.get(
            "candidate_may_auto_deploy_authority"
        ),
        credentials_may_be_stored_in_repository=trust.get(
            "credentials_may_be_stored_in_repository"
        ),
    )
    if not policy.candidate_repository or "/" not in policy.candidate_repository:
        raise ValueError("candidate_repository must be owner/name")
    if not policy.authority_check_context:
        raise ValueError("authority_check_context is required")
    return policy
