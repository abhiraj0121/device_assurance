from fastapi import APIRouter
from app.core.devices_loader import load_devices
from app.ansible_runner import run_playbook, CISCO_RESTART, JUNIPER_RESTART

router = APIRouter()

RESTART_PLAYBOOKS = {
    "Cisco": CISCO_RESTART,
    "Juniper": JUNIPER_RESTART,
    # "Sophos": SOPHOS_RESTART,
}

@router.post("/run/{device_id}/", name="restart_device")
async def run_restart(device_id: str):
    branches, cores = load_devices()

    device = next((d for d in branches if d["id"] == device_id), None)
    if not device:
        device = next((d for d in cores if d["id"] == device_id), None)

    if not device:
        return {"status": "notfound", "output": "", "logfile": None}

    vendor = device["vendor"]
    playbook = RESTART_PLAYBOOKS.get(vendor)
    if not playbook:
        return {
            "status": "unsupported_vendor",
            "output": f"No restart playbook for vendor '{vendor}'",
            "logfile": None,
            "vendor": vendor,
            "device_id": device_id,
        }

    success, output, logfile = run_playbook(playbook, device_id, vendor)

    return {
        "status": "success" if success else "fail",
        "output": output,
        "logfile": logfile,
        "vendor": vendor,
        "device_id": device_id,
    }
