# fastapi/app/core/devices_loader.py

import yaml
from pathlib import Path

# Project root: /home/abhiraj/Projects/device_assurance
ROOT_DIR = Path(__file__).resolve().parents[3]

# ansible inventory path (relative to project root)
DEVICES_FILE = ROOT_DIR / "ansible" / "inventories" / "devices.yml"


def load_devices():
    """
    Load devices from Ansible inventory into two lists:
      - branch (list of dicts)
      - core   (list of dicts)

    Each device dict looks like:
    {
        "id": "taplejung",          # hostname in ansible
        "name": "Taplejung",        # device_name in YAML
        "vendor": "Sophos",
        "ip": "10.70.35.1",
        "group": "branch"           # or "core"
    }
    """
    with open(DEVICES_FILE, "r") as f:
        data = yaml.safe_load(f)

    branch = []
    core = []

    # Navigate: all -> children -> {branch, core} -> hosts
    groups = data.get("all", {}).get("children", {})

    # ---------------------------
    # Branch devices
    # ---------------------------
    branch_hosts = groups.get("branch", {}).get("hosts", {}) or {}
    for host_id, info in branch_hosts.items():
        branch.append({
            "id": host_id,
            "name": (
                info.get("device_name")
                or info.get("name")  # fallback if ever used
                or host_id
            ),
            "vendor": info.get("vendor", "Unknown"),
            "ip": info.get("ip") or info.get("ansible_host"),
            "group": "branch",
        })

    # ---------------------------
    # Core devices
    # ---------------------------
    core_hosts = groups.get("core", {}).get("hosts", {}) or {}
    for host_id, info in core_hosts.items():
        core.append({
            "id": host_id,
            "name": (
                info.get("device_name")
                or info.get("name")
                or host_id
            ),
            "vendor": info.get("vendor", "Unknown"),
            "ip": info.get("ip") or info.get("ansible_host"),
            "group": "core",
        })

    return branch, core
