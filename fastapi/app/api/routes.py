from fastapi import APIRouter

from .routes_auth import router as auth_router
from .routes_devices import router as devices_router
from .routes_ping import router as ping_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(devices_router, prefix="/devices", tags=["Devices"])
api_router.include_router(ping_router, prefix="/ping", tags=["Ping"])


