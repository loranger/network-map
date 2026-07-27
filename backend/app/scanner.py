import re
import subprocess
from datetime import datetime

from sqlalchemy.orm import Session

from . import models

IP_RE = re.compile(r'\d+\.\d+\.\d+\.\d+')
MAC_RE = re.compile(
    r'(([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})'
)

BOGUS_RANGES = [
    re.compile(r'^224\.'),
    re.compile(r'^239\.'),
    re.compile(r'^127\.'),
    re.compile(r'^0\.'),
]


def _is_valid_host(ip: str) -> bool:
    if ip is None:
        return False
    octets = ip.split(".")
    if len(octets) != 4:
        return False
    try:
        last = int(octets[3])
    except ValueError:
        return False
    if last == 0 or last == 255:
        return False
    for r in BOGUS_RANGES:
        if r.match(ip):
            return False
    return True


def _parse_nmap_output(output: str):
    devices = []
    current_ip = None
    for line in output.splitlines():
        m = IP_RE.search(line)
        if m and 'Nmap scan report for' in line:
            current_ip = m.group()
        elif 'MAC Address:' in line and current_ip:
            mm = MAC_RE.search(line)
            devices.append({
                "ip": current_ip,
                "mac": mm.group(1) if mm else None,
            })
            current_ip = None
    return devices


def _parse_arp_table(output: str):
    devices = []
    for line in output.strip().splitlines():
        ip_m = IP_RE.search(line)
        mac_m = MAC_RE.search(line)
        if ip_m:
            devices.append({
                "ip": ip_m.group(),
                "mac": mac_m.group(1) if mac_m else None,
            })
    return devices


def _persist(devices: list[dict], db: Session):
    for d in devices:
        ip, mac = d["ip"], d.get("mac")
        existing = None
        if mac:
            existing = db.query(models.Device).filter(
                models.Device.mac == mac
            ).first()
        if not existing and ip:
            existing = db.query(models.Device).filter(
                models.Device.ipv4 == ip
            ).first()
        if existing:
            existing.last_seen = datetime.utcnow()
            existing.discovered = True
            if mac and not existing.mac:
                existing.mac = mac
        elif mac:
            suffix = mac.replace(":", "").lower()
            db.add(models.Device(
                name=f"device-{suffix}",
                device_type="other",
                mac=mac,
                ipv4=ip,
                discovered=True,
            ))
    db.commit()


def scan_network(subnet: str = "192.168.1.0/24", db: Session = None):
    seen = {}
    found = []

    try:
        result = subprocess.run(
            ["nmap", "-sn", "-PR", "-n", subnet],
            capture_output=True, text=True, timeout=120,
        )
        for d in _parse_nmap_output(result.stdout):
            key = d["ip"]
            seen[key] = d
    except Exception as e:
        print(f"nmap ARP scan error: {e}")

    try:
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True, text=True, timeout=10,
        )
        for d in _parse_arp_table(result.stdout):
            key = d["ip"]
            if key not in seen:
                seen[key] = d
            elif d.get("mac") and not seen[key].get("mac"):
                seen[key]["mac"] = d["mac"]
    except Exception as e:
        print(f"arp -a error: {e}")

    found = list(seen.values())
    valid = [d for d in found if _is_valid_host(d.get("ip"))]

    if db is not None and valid:
        _persist(valid, db)

    return valid
