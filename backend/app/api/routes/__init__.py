from app.api.routes.auth import router as auth_router
from app.api.routes.reports import router as reports_router
from app.api.routes.users import router as users_router
from app.api.routes.analytics import router as analytics_router

__all__ = ["auth_router", "reports_router", "users_router", "analytics_router"]
