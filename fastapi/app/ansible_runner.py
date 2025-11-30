# fastapi/app/ansible_runner.py

import subprocess
import shlex
from pathlib import Path
from datetime import datetime

# ROOT directory of the whole project
ROOT = Path(__file__).resolve().parents[2]

# Paths relative to project structure
ANSIBLE_DIR = ROOT / "ansible"
PLAYBOOKS = ANSIBLE_DIR / "playbooks"
INVENTORY = ANSIBLE_DIR / "inventories" / "devices.yml"

# Playbooks
PING_PLAYBOOK = PLAYBOOKS / "ping_test.yml"
JUNIPER_BACKUP = PLAYBOOKS / "backup_juniper.yml"
CISCO_BACKUP = PLAYBOOKS / "backup_cisco.yml"
PALO_BACKUP = PLAYBOOKS / "backup_paloalto.yml"


VENDOR_CONFIG = {
    "Juniper": {
        "ansible_connection": "netconf",
        "ansible_network_os": "junos",
        "ansible_user": "root",
        "ansible_password": "Survey@1244"
    },
    "Cisco": {
        "ansible_connection": "network_cli",
        "ansible_network_os": "ios",
        "ansible_user": "admin",
        "ansible_password": "cisco123"
    },
    "Sophos": {
        "ansible_connection": "ssh",   # example
        "ansible_network_os": "sophos",
        "ansible_user": "admin",
        "ansible_password": "sophosPass"
    }
}

def run_playbook(playbook_path, limit_name, vendor):
    """
    Generic runner for any playbook.
    """

    # Determine log folder
    if playbook_path == PING_PLAYBOOK:
        log_type = "ping_history"
    else:
        log_type = "backup"
    LOGS_DIR = ROOT / "logs" / log_type

    vendor_vars = VENDOR_CONFIG.get(vendor, {})

    # Build -e "key=value ..." string
    extra_vars = " ".join([f"{k}={v}" for k, v in vendor_vars.items()])
    
    cmd = f"ansible-playbook -i {INVENTORY} {playbook_path} --limit {limit_name} -e \"{extra_vars}\""
    print("Running:", cmd)

    process = subprocess.Popen(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate()
    success = (process.returncode == 0)
    output = stdout.decode() + "\n" + stderr.decode()

    # ------------------------
    # Save log
    # ------------------------
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    device_log_dir = LOGS_DIR / vendor / limit_name
    device_log_dir.mkdir(parents=True, exist_ok=True)

    log_file = device_log_dir / f"{timestamp}.log"
    with open(log_file, "w") as f:
        f.write(output)

    return success, output, str(log_file)
