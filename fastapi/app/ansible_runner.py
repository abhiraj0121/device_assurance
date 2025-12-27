# fastapi/app/ansible_runner.py

import os
import signal
import subprocess
import shlex
import re
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
CISCO_RESTART = PLAYBOOKS / "restart_cisco.yml"
JUNIPER_RESTART = PLAYBOOKS / "restart_juniper.yml"
# Add more playbooks as needed

VENDOR_CONFIG = {
    "Juniper": {
        "ansible_connection": "ansible.netcommon.network_cli",
        "ansible_network_os": "junipernetworks.junos.junos",
        "ansible_user": "root",
        "ansible_password": "Survey@1255",
    },
    "Cisco": {
        "ansible_user": "abhiraj.wagle",
        "ansible_password": "Surevey@1266",
        "ansible_port": "23",
    },
    "Sophos": {
        "ansible_connection": "ssh",  # example
        "ansible_network_os": "sophos",
        "ansible_user": "admin",
        "ansible_password": "sophosPass",
    },
}


def _mask_sensitive(cmd: str) -> str:
    """
    Mask ansible_user and ansible_password values in the printed command.
    Handles:
      ansible_user=foo
      ansible_user='foo bar'
      ansible_user="foo bar"
      ansible_password=...
    """
    cmd = re.sub(
        r'(ansible_password=)(\".*?\"|\'.*?\'|\S+)',
        r'\1********',
        cmd
    )
    cmd = re.sub(
        r'(ansible_user=)(\".*?\"|\'.*?\'|\S+)',
        r'\1********',
        cmd
    )
    return cmd

def run_playbook(playbook_path, limit_name, vendor, timeout_sec: int = 90):
    """
    Generic runner for any playbook, with hard timeout + safe logging.
    """

    # Determine log folder
    log_type = "ping_history" if playbook_path == PING_PLAYBOOK else "backup"
    LOGS_DIR = ROOT / "logs" / log_type

    vendor_vars = VENDOR_CONFIG.get(vendor, {})

    # Build -e "key=value ..." string
    extra_vars = " ".join([f"{k}={v}" for k, v in vendor_vars.items()])

    cmd = f'ansible-playbook -i {INVENTORY} {playbook_path} --limit {limit_name} -e "{extra_vars}"'
    print("Running:", _mask_sensitive(cmd))

    process = subprocess.Popen(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,  # important so we can kill child processes too
    )

    try:
        stdout, stderr = process.communicate(timeout=timeout_sec)
        success = (process.returncode == 0)
        output = stdout.decode(errors="replace") + "\n" + stderr.decode(errors="replace")

    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        success = False
        output = f"❌ TIMEOUT: ansible-playbook exceeded {timeout_sec}s and was killed.\n"

    # ------------------------
    # Save log
    # ------------------------
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    device_log_dir = LOGS_DIR / vendor / limit_name
    device_log_dir.mkdir(parents=True, exist_ok=True)

    log_file = device_log_dir / f"{timestamp}.log"
    with open(log_file, "w") as f:
        f.write(output)

    # Print a useful failure summary to terminal
    if not success:
        print(f"❌ Playbook failed: vendor={vendor} host={limit_name}")
        print(f"📄 Log saved: {log_file}")
        tail = "\n".join(output.splitlines()[-80:])
        print("---- last log lines ----")
        print(tail)
        print("------------------------")

    return success, output, str(log_file)