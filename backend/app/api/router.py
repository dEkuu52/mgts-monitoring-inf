from fastapi import APIRouter

from app.api.routes import auth, defects, infrastructure_objects, statuses, users , uploads

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(statuses.router)
api_router.include_router(infrastructure_objects.router)
api_router.include_router(defects.router)
api_router.include_router(uploads.router)

__all__ = ["api_router"]
