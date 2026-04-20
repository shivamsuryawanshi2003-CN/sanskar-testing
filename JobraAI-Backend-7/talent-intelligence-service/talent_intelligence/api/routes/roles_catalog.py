"""Public role catalog for UI dropdowns (no full JD exposure)."""

from fastapi import APIRouter
from pydantic import BaseModel

from talent_intelligence.config.roles import ROLES

router = APIRouter()


class RolePublic(BaseModel):
    id: str
    title: str
    skills: list[str]


class RolesListResponse(BaseModel):
    roles: list[RolePublic]


@router.get("/roles", response_model=RolesListResponse, tags=["catalog"])
def list_roles() -> RolesListResponse:
    items = [RolePublic(id=c["id"], title=c["title"], skills=list(c["skills"])) for c in ROLES.values()]
    items.sort(key=lambda r: r.title.lower())
    return RolesListResponse(roles=items)
