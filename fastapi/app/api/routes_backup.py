from fastapi import APIRouter
from app.core.devices_loader import load_devices
from app.ansible_runner import (
    run_playbook,
    JUNIPER_BACKUP,
    CISCO_BACKUP,
    PALO_BACKUP,
)

router = APIRouter()

BACKUP_PLAYBOOKS = {
    "Juniper": JUNIPER_BACKUP,
    "Cisco": CISCO_BACKUP,
    "PaloAlto": PALO_BACKUP,
}


@router.post("/run/{device_id}/", name="backup_device")
async def run_backup(device_id: str):

    branches, cores = load_devices()

    # Find the device
    device = next((d for d in branches if d["id"] == device_id), None)
    if not device:
        device = next((d for d in cores if d["id"] == device_id), None)

    if not device:
        return {"status": "notfound", "logfile": None}

    vendor = device["vendor"]

    # Get the correct playbook
    playbook = BACKUP_PLAYBOOKS.get(vendor)
    if not playbook:
        return {
            "status": "unsupported_vendor",
            "logfile": None,
            "message": f"No backup playbook for vendor '{vendor}'"
        }

    # Run the playbook
    success, output, logfile = run_playbook(playbook, device_id, vendor)

    return {
        "status": "success" if success else "fail",
        "logfile": logfile,
        "vendor": vendor,
        "device_id": device_id,
    }
