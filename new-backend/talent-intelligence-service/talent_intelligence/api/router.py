
from fastapi import APIRouter

from talent_intelligence.api.routes.ats import general, with_jd, with_role, roles

api_router = APIRouter()
api_router.include_router(general.router, tags=["analysis"])
api_router.include_router(with_role.router, tags=["analysis"])
api_router.include_router(with_jd.router, tags=["analysis"])
api_router.include_router(roles.router, tags=["roles"])
