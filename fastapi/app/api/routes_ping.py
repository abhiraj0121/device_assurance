import re
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.devices_loader import load_devices
from app.ansible_runner import run_playbook, PING_PLAYBOOK

router = APIRouter()
PING_STDOUT_REGEX = re.compile(r'"ping_output\.stdout":\s*"([^"]+)"')
templates = Jinja2Templates(directory="app/templates")

def extract_ping_stdout(ansible_output: str) -> str:
    """
    Try to extract only the ping_output.stdout part
    from the Ansible text output.
    If not found, return the original output.
    """
    m = PING_STDOUT_REGEX.search(ansible_output)
    if not m:
        return ansible_output.strip()

    raw = m.group(1)  # the quoted string with \n inside
    # Unescape \n etc.
    return bytes(raw, "utf-8").decode("unicode_escape").strip()

@router.post("/{device_id}/", name="ping_device")
async def ping(device_id: str):

    branches, cores = load_devices()

    # Find device
    device = next((d for d in branches if d["id"] == device_id), None)
    if not device:
        device = next((d for d in cores if d["id"] == device_id), None)

    if not device:
        return {"status": "notfound", "logfile": None}

    hostname = device["id"]
    vendor = device["vendor"]

    # Run playbook
    success, output, logfile = run_playbook(PING_PLAYBOOK, hostname, vendor)
    clean_output = extract_ping_stdout(output)

    return {
        "status": "success" if success else "fail",
        "logfile": logfile,
        "output": clean_output,
        "vendor": vendor,
        "device_id": hostname,
    }
