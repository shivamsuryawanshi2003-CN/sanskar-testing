
from fastapi import APIRouter

from talent_intelligence.api.routes import roles_catalog
from talent_intelligence.api.routes.ats import general, suggestion, with_jd, with_role

api_router = APIRouter()
api_router.include_router(roles_catalog.router, tags=["catalog"])
api_router.include_router(general.router, tags=["analysis"])
api_router.include_router(with_role.router, tags=["analysis"])
api_router.include_router(with_jd.router, tags=["analysis"])
api_router.include_router(suggestion.router, tags=["analysis"])
