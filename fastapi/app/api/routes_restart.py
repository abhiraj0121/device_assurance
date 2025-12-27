from fastapi import APIRouter
from app.core.devices_loader import load_devices
from app.ansible_runner import run_playbook, CISCO_RESTART, JUNIPER_RESTART, CISCO_UPTIME, JUNIPER_UPTIME
import re

router = APIRouter()

UPTIME_PLAYBOOKS = {
    "Juniper": JUNIPER_UPTIME,
    "Cisco": CISCO_UPTIME,
}

def extract_uptime(output: str) -> str | None:
    if not output:
        return None

    # Find "UPTIME: <one line>" anywhere in output
    m = re.search(r"UPTIME:\s*([^\r\n]+)", output)
    return m.group(1).strip() if m else None

RESTART_PLAYBOOKS = {
    "Cisco": CISCO_RESTART,
    "Juniper": JUNIPER_RESTART,
    # "Sophos": SOPHOS_RESTART,
}

@router.post("/uptime/{device_id}/", name="device_uptime")
async def device_uptime(device_id: str):
    branches, cores = load_devices()
    device = next((d for d in branches if d["id"] == device_id), None) or \
             next((d for d in cores if d["id"] == device_id), None)

    if not device:
        return {"status": "notfound", "uptime": None}

    vendor = device["vendor"]
    playbook = UPTIME_PLAYBOOKS.get(vendor)
    if not playbook:
        return {"status": "unsupported_vendor", "uptime": None, "vendor": vendor}

    success, output, logfile = run_playbook(playbook, device_id, vendor, timeout_sec=45)

    uptime = extract_uptime(output)
    return {
        "status": "success" if uptime else "fail",
        "uptime": uptime,
        "logfile": logfile,
        "vendor": vendor,
        "device_id": device_id,
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
