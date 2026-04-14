import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import HTTPException

_ROLES_FILE = Path(__file__).resolve().parent / "roles.json"


@lru_cache(maxsize=1)
def _load_roles() -> dict[str, dict[str, Any]]:
    if not _ROLES_FILE.exists():
        raise RuntimeError(f"roles.json not found: {_ROLES_FILE}")
    raw = json.loads(_ROLES_FILE.read_text(encoding="utf-8"))
    rows = raw.get("roles", [])
    roles: dict[str, dict[str, Any]] = {}
    for row in rows:
        role_id = str(row.get("id", "")).strip()
        title = str(row.get("title", "")).strip()
        skills = [str(k).strip().lower() for k in row.get("skills", []) if str(k).strip()]
        jd = str(row.get("jd", "")).strip()
        if not role_id or not title or not skills or not jd:
            continue
        roles[role_id] = {"id": role_id, "title": title, "skills": skills, "jd": jd}
    if not roles:
        raise RuntimeError("roles.json has no valid roles.")
    return roles


ROLES = _load_roles()


def role_config(role: str) -> dict[str, Any]:
    key = role.strip()
    if key in ROLES:
        return ROLES[key]
    key_lower = key.lower()
    for cfg in ROLES.values():
        title = cfg["title"].lower()
        if key_lower == title or key_lower in title:
            return cfg
    valid = ", ".join([f"{cfg['id']}:{cfg['title']}" for cfg in ROLES.values()])
    raise HTTPException(status_code=400, detail=f"Unknown role: {role}. Use one of: {valid}")
