from fastapi import APIRouter
from typing import List, Dict

from talent_intelligence.config.roles import ROLES

router = APIRouter()


@router.get("/roles", summary="List available roles", response_model=List[Dict])
def list_roles():
    """Return the catalog of roles for UI consumption.

    Each role contains `id`, `title`, and `skills`.
    """
    rows = sorted(ROLES.values(), key=lambda r: (int(r["id"]), r["title"]))
    return [{"id": r["id"], "title": r["title"], "skills": r.get("skills", [])} for r in rows]
