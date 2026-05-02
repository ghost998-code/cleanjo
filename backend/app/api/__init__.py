from fastapi import APIRouter
from app.api.routes import analytics_router, auth_router, config_router, reports_router, users_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(config_router)
api_router.include_router(reports_router)
api_router.include_router(users_router)
api_router.include_router(analytics_router)
