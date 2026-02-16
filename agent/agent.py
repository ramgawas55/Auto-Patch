import argparse
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib import request, error


def read_env_file(path: Path) -> dict:
    data = {}
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def get_config(state_dir: Path) -> dict:
    env_path = Path("/etc/autopatch/agent.env")
    data = read_env_file(env_path)
    data.update({k: v for k, v in os.environ.items() if k.startswith("AUTO_PATCH_")})
    token_file = state_dir / "agent_token"
    if token_file.exists():
        data.setdefault("AGENT_TOKEN", token_file.read_text().strip())
    return data


def write_agent_token(state_dir: Path, token: str):
    state_dir.mkdir(parents=True, exist_ok=True)
    token_file = state_dir / "agent_token"
    token_file.write_text(token)


def http_json(method: str, url: str, headers: dict, payload: dict | None, timeout: int = 15):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        if not body:
            return {}
        return json.loads(body)


def http_json_retry(method: str, url: str, headers: dict, payload: dict | None, retries: int = 3):
    last_error = None
    for _ in range(retries):
        try:
            return http_json(method, url, headers, payload)
        except error.HTTPError as exc:
            last_error = exc
            time.sleep(2)
        except Exception as exc:
            last_error = exc
            time.sleep(2)
    raise last_error


def run_cmd(args: list[str], timeout: int = 900):
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def detect_package_manager() -> str:
    for name in ["apt-get", "dnf", "yum"]:
        if shutil_which(name):
            return "apt" if name == "apt-get" else name
    return "unknown"


def shutil_which(cmd: str) -> bool:
    return any(os.access(Path(path) / cmd, os.X_OK) for path in os.environ.get("PATH", "").split(os.pathsep))


def get_os_release() -> dict:
    data = {}
    path = Path("/etc/os-release")
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"')
    return data


def get_last_update_time(pm: str) -> str | None:
    candidates = []
    if pm == "apt":
        candidates = [
            Path("/var/lib/apt/periodic/update-success-stamp"),
            Path("/var/lib/apt/periodic/upgrade-stamp")
        ]
    if pm in {"dnf", "yum"}:
        candidates = [Path("/var/log/dnf.log"), Path("/var/log/yum.log")]
    for path in candidates:
        if path.exists():
            ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            return ts.isoformat()
    return None


def parse_apt_updates(output: str) -> list[dict]:
    updates = []
    for line in output.splitlines():
        if not line.startswith("Inst "):
            continue
        parts = line.split()
        name = parts[1]
        current = None
        candidate = None
        if "[" in line and "]" in line:
            current = line.split("[", 1)[1].split("]", 1)[0]
        if "(" in line:
            candidate = line.split("(", 1)[1].split(" ", 1)[0]
        updates.append({"name": name, "current_version": current, "candidate_version": candidate, "is_security": False})
    return updates


def parse_yum_updates(output: str) -> list[dict]:
    updates = []
    for line in output.splitlines():
        if not line or line.startswith("Last metadata expiration check"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        name = parts[0]
        candidate = parts[1]
        updates.append({"name": name, "current_version": None, "candidate_version": candidate, "is_security": False})
    return updates


def list_updates(pm: str) -> list[dict]:
    if pm == "apt":
        code, out, _ = run_cmd(["apt-get", "-s", "upgrade"])
        return parse_apt_updates(out) if code == 0 else []
    if pm in {"dnf", "yum"}:
        code, out, _ = run_cmd([pm, "-q", "check-update"])
        if code in {0, 100}:
            return parse_yum_updates(out)
    return []


def list_security_updates(pm: str) -> list[dict]:
    if pm == "apt":
        if shutil_which("unattended-upgrades"):
            code, out, _ = run_cmd(["unattended-upgrades", "--dry-run"])
            if code == 0:
                updates = []
                for line in out.splitlines():
                    if line.startswith("Inst "):
                        name = line.split()[1]
                        updates.append({"name": name, "current_version": None, "candidate_version": None, "is_security": True})
                return updates
        return []
    if pm in {"dnf", "yum"}:
        if shutil_which(pm):
            code, out, _ = run_cmd([pm, "updateinfo", "list", "security"])
            if code == 0:
                updates = []
                for line in out.splitlines():
                    parts = line.split()
                    if len(parts) >= 3:
                        updates.append({"name": parts[2], "current_version": None, "candidate_version": None, "is_security": True})
                return updates
    return []


def reboot_required(pm: str, updates: list[dict]) -> bool:
    if pm == "apt":
        return Path("/var/run/reboot-required").exists()
    if pm in {"dnf", "yum"}:
        if shutil_which("needs-restarting"):
            code, _, _ = run_cmd(["needs-restarting", "-r"])
            return code != 0
        for update in updates:
            if update["name"].startswith("kernel"):
                return True
    return False


def collect_inventory() -> dict:
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    os_release = get_os_release()
    os_name = os_release.get("NAME", "unknown")
    os_version = os_release.get("VERSION_ID", "unknown")
    kernel = os.uname().release
    pm = detect_package_manager()
    updates = list_updates(pm)
    security_updates = list_security_updates(pm)
    reboot = reboot_required(pm, updates)
    return {
        "hostname": hostname,
        "ip": ip,
        "os_name": os_name,
        "os_version": os_version,
        "kernel_version": kernel,
        "package_manager": pm,
        "last_update_time": get_last_update_time(pm),
        "reboot_required": reboot,
        "updates": updates,
        "security_updates": security_updates
    }


def apply_patches(pm: str, security_only: bool) -> tuple[int, str, str]:
    stdout = ""
    stderr = ""
    if pm == "apt":
        code, out, err = run_cmd(["apt-get", "update"])
        stdout += out
        stderr += err
        if code != 0:
            return code, stdout, stderr
        if security_only and shutil_which("unattended-upgrades"):
            code, out, err = run_cmd(["unattended-upgrades", "-d"])
        else:
            code, out, err = run_cmd(["apt-get", "-y", "upgrade"])
        stdout += out
        stderr += err
        return code, stdout, stderr
    if pm in {"dnf", "yum"}:
        cmd = [pm, "-y", "update"]
        if security_only:
            cmd.append("--security")
        code, out, err = run_cmd(cmd)
        stdout += out
        stderr += err
        return code, stdout, stderr
    return 1, "", "Unsupported package manager"


def execute_job(job_type: str) -> tuple[int, str, str]:
    pm = detect_package_manager()
    if job_type in {"SCAN_NOW", "REPORT_ONLY"}:
        return 0, "Scan complete", ""
    if job_type == "APPLY_PATCHES":
        return apply_patches(pm, False)
    if job_type == "APPLY_SECURITY_ONLY":
        return apply_patches(pm, True)
    if job_type == "REBOOT":
        code, out, err = run_cmd(["reboot"])
        return code, out, err
    return 1, "", "Unknown job type"


def should_send_heartbeat(state_dir: Path) -> bool:
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "last_heartbeat"
    if not path.exists():
        return True
    last = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return datetime.now(timezone.utc) - last > timedelta(minutes=5)


def update_heartbeat(state_dir: Path):
    path = state_dir / "last_heartbeat"
    path.write_text(datetime.now(timezone.utc).isoformat())


def register_agent(config: dict, state_dir: Path, backend_url: str) -> str:
    payload = collect_inventory()
    headers = {"X-BOOTSTRAP-TOKEN": config.get("BOOTSTRAP_TOKEN", "")}
    data = http_json_retry("POST", f"{backend_url}/api/agent/register", headers, payload)
    token = data.get("agent_token")
    if not token:
        raise RuntimeError("Registration failed")
    write_agent_token(state_dir, token)
    return token


def send_heartbeat(config: dict, token: str, backend_url: str):
    inventory = collect_inventory()
    payload = {"inventory": inventory}
    headers = {"X-AGENT-TOKEN": token}
    http_json_retry("POST", f"{backend_url}/api/agent/heartbeat", headers, payload)


def poll_job(config: dict, token: str, backend_url: str):
    headers = {"X-AGENT-TOKEN": token}
    data = http_json_retry("GET", f"{backend_url}/api/agent/jobs/poll", headers, None)
    job = data.get("job")
    if not job:
        return
    job_id = job["id"]
    job_type = job["job_type"]
    start = datetime.now(timezone.utc)
    exit_code, stdout, stderr = execute_job(job_type)
    finish = datetime.now(timezone.utc)
    inventory = collect_inventory()
    payload = {
        "job_id": job_id,
        "started_at": start.isoformat(),
        "finished_at": finish.isoformat(),
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "status": "COMPLETED" if exit_code == 0 else "FAILED",
        "inventory": inventory
    }
    http_json_retry("POST", f"{backend_url}/api/agent/jobs/{job_id}/result", headers, payload)


def run_once(state_dir: Path):
    config = get_config(state_dir)
    backend_url = config.get("BACKEND_URL") or config.get("AUTO_PATCH_BACKEND_URL")
    if not backend_url:
        raise RuntimeError("BACKEND_URL missing")
    token = config.get("AGENT_TOKEN") or config.get("AUTO_PATCH_AGENT_TOKEN")
    if not token:
        if not config.get("BOOTSTRAP_TOKEN"):
            raise RuntimeError("AGENT_TOKEN missing")
        token = register_agent(config, state_dir, backend_url)
    if should_send_heartbeat(state_dir):
        send_heartbeat(config, token, backend_url)
        update_heartbeat(state_dir)
    poll_job(config, token, backend_url)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--state-dir", default="/var/lib/autopatch")
    args = parser.parse_args()
    state_dir = Path(args.state_dir)
    if args.once:
        run_once(state_dir)
        return
    while True:
        run_once(state_dir)
        time.sleep(60)


if __name__ == "__main__":
    main()
