# fastapi/app/api/routes_devices.py

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.core.devices_loader import load_devices

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", name="devices_home")
async def devices_page(request: Request):
    # Load branch + core devices from YAML
    branch_devices, core_devices = load_devices()

    # Sort all devices alphabetically
    branch_devices = sorted(branch_devices, key=lambda d: d["name"].lower())
    core_devices = sorted(core_devices, key=lambda d: d["name"].lower())

    # Group branch devices by vendor
    branch_by_vendor = {}
    for d in branch_devices:
        vendor = d.get("vendor", "Unknown")
        branch_by_vendor.setdefault(vendor, []).append(d)

    # Sort vendors alphabetically
    branch_by_vendor = dict(sorted(branch_by_vendor.items(), key=lambda x: x[0].lower()))

    return templates.TemplateResponse(
        "devices.html",
        {
            "request": request,
            "branch_devices": branch_devices,
            "branch_by_vendor": branch_by_vendor,
            "core_devices": core_devices,
        }
    )
