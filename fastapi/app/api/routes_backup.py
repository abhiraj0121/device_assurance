from fastapi import APIRouter
from app.core.devices_loader import load_devices
from app.ansible_runner import (
    run_playbook,
    JUNIPER_BACKUP,
    CISCO_BACKUP,
    PALO_BACKUP,
)
from pathlib import Path
from datetime import datetime
import difflib

router = APIRouter()

BACKUP_PLAYBOOKS = {
    "Juniper": JUNIPER_BACKUP,
    "Cisco": CISCO_BACKUP,
    "PaloAlto": PALO_BACKUP,
}

# Project root: .../device_assurance
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_ROOT = PROJECT_ROOT / "ansible" / "configs"
DIFF_LOG_ROOT = PROJECT_ROOT / "logs" / "diff"

def _find_device(device_id: str):
    branches, cores = load_devices()
    return (
        next((d for d in branches if d["id"] == device_id), None)
        or next((d for d in cores if d["id"] == device_id), None)
    )

def _resolve_config_dir(vendor: str, device_id: str) -> Path | None:
    """
    Your backup folders are not 100% consistent across vendors yet.
    Try common patterns:
      - ansible/configs/<Vendor>/<device_id>        (Cisco style)
      - ansible/configs/<device_id>                (Juniper old style)
      - ansible/configs/<vendor_lower>/<device_id> (just in case)
    """
    candidates = [
        CONFIG_ROOT / vendor / device_id,
        CONFIG_ROOT / vendor.lower() / device_id,
        CONFIG_ROOT / device_id,
    ]
    for p in candidates:
        if p.exists() and p.is_dir():
            return p
    return None

def _latest_two_files(dirpath: Path):
    files = [p for p in dirpath.iterdir() if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:2]


@router.post("/run/{device_id}/", name="backup_device")
async def run_backup(device_id: str):
    device = _find_device(device_id)
    if not device:
        return {"status": "notfound", "logfile": None}

    vendor = device["vendor"]
    playbook = BACKUP_PLAYBOOKS.get(vendor)
    if not playbook:
        return {
            "status": "unsupported_vendor",
            "logfile": None,
            "message": f"No backup playbook for vendor '{vendor}'",
        }

    success, output, logfile = run_playbook(playbook, device_id, vendor)

    return {
        "status": "success" if success else "fail",
        "logfile": logfile,
        "vendor": vendor,
        "device_id": device_id,
    }

@router.post("/diff/{device_id}/", name="diff_latest_backup")
async def diff_latest_backup(device_id: str, max_lines: int = 400):
    """
    Compare latest 2 backups for this device and return unified diff.
    max_lines limits UI output (full diff is still saved to log file).
    """
    device = _find_device(device_id)
    if not device:
        return {"status": "notfound", "diff": "", "logfile": None}

    vendor = device["vendor"]

    cfg_dir = _resolve_config_dir(vendor, device_id)
    if not cfg_dir:
        return {
            "status": "no_backups",
            "diff": "",
            "logfile": None,
            "message": f"No backup folder found for {vendor}/{device_id}",
        }

    latest = _latest_two_files(cfg_dir)
    if len(latest) < 2:
        return {
            "status": "not_enough_backups",
            "diff": "",
            "logfile": None,
            "message": f"Need at least 2 backup files in {cfg_dir}",
        }

    new_file, old_file = latest[0], latest[1]

    old_text = old_file.read_text(errors="ignore").splitlines()
    new_text = new_file.read_text(errors="ignore").splitlines()

    diff_lines = list(
        difflib.unified_diff(
            old_text,
            new_text,
            fromfile=str(old_file.name),
            tofile=str(new_file.name),
            lineterm="",
        )
    )

    diff_text_full = "\n".join(diff_lines) if diff_lines else "NO_CHANGES"

    # Save full diff to log
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    diff_dir = DIFF_LOG_ROOT / vendor / device_id
    diff_dir.mkdir(parents=True, exist_ok=True)
    diff_file = diff_dir / f"{ts}.diff"
    diff_file.write_text(diff_text_full, errors="ignore")

    # Limit what UI shows
    if diff_lines:
        shown = diff_lines[:max_lines]
        if len(diff_lines) > max_lines:
            shown.append(f"... (truncated, total lines: {len(diff_lines)}; see log file)")
        diff_text_ui = "\n".join(shown)
    else:
        diff_text_ui = "NO_CHANGES"

    return {
        "status": "success",
        "vendor": vendor,
        "device_id": device_id,
        "from": old_file.name,
        "to": new_file.name,
        "diff": diff_text_ui,
        "logfile": str(diff_file),
    }

# @router.post("/run/{device_id}/", name="backup_device")
# async def run_backup(device_id: str):

#     branches, cores = load_devices()

#     # Find the device
#     device = next((d for d in branches if d["id"] == device_id), None)
#     if not device:
#         device = next((d for d in cores if d["id"] == device_id), None)

#     if not device:
#         return {"status": "notfound", "logfile": None}

#     vendor = device["vendor"]

#     # Get the correct playbook
#     playbook = BACKUP_PLAYBOOKS.get(vendor)
#     if not playbook:
#         return {
#             "status": "unsupported_vendor",
#             "logfile": None,
#             "message": f"No backup playbook for vendor '{vendor}'"
#         }

#     # Run the playbook
#     success, output, logfile = run_playbook(playbook, device_id, vendor)

#     return {
#         "status": "success" if success else "fail",
#         "logfile": logfile,
#         "vendor": vendor,
#         "device_id": device_id,
#     }
