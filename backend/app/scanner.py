import re
import subprocess
from datetime import datetime

from sqlalchemy.orm import Session

from . import models
from .crud import auto_assign_network

IP_RE = re.compile(r'\d+\.\d+\.\d+\.\d+')
MAC_RE = re.compile(
    r'(([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})'
)

ARP_LINE_RE = re.compile(
    r'^\s*(?P<hostname>\S+)\s+\((?P<ip>\d+\.\d+\.\d+\.\d+)\)\s+at\s+'
    r'(?P<mac>(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})'
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
                "hostname": None,
            })
            current_ip = None
    return devices


def _parse_arp_table(output: str):
    devices = []
    for line in output.strip().splitlines():
        m = ARP_LINE_RE.search(line)
        if m:
            hostname = m.group("hostname")
            devices.append({
                "ip": m.group("ip"),
                "mac": m.group("mac"),
                "hostname": None if hostname == "?" else hostname,
            })
    return devices


def _persist(devices: list[dict], db: Session):
    for d in devices:
        ip, mac, hostname = d["ip"], d.get("mac"), d.get("hostname")
        existing = None
        if mac:
            ip_entry = db.query(models.DeviceIP).filter(
                models.DeviceIP.mac == mac
            ).first()
            existing = ip_entry.device if ip_entry else None
        if not existing and ip:
            existing = db.query(models.Device).filter(
                models.Device.ips.any(models.DeviceIP.ipv4 == ip)
            ).first()
        if existing:
            existing.last_seen = datetime.utcnow()
            existing.discovered = True
            if hostname and not existing.hostname:
                existing.hostname = hostname
            if hostname and existing.name.startswith("device-"):
                short = hostname.split(".")[0] if "." in hostname else hostname
                existing.name = short
            ip_match = next((dev_ip for dev_ip in existing.ips if dev_ip.ipv4 == ip), None)
            if ip_match:
                if mac and not ip_match.mac:
                    ip_match.mac = mac
            elif ip:
                dev_ip = models.DeviceIP(device_id=existing.id, ipv4=ip, mac=mac)
                auto_assign_network(db, dev_ip)
                db.add(dev_ip)
        elif mac:
            suffix = mac.replace(":", "").lower()
            name = hostname.split(".")[0] if hostname else f"device-{suffix}"
            dev = models.Device(
                name=name,
                device_type="other",
                hostname=hostname,
                discovered=True,
            )
            db.add(dev)
            db.flush()
            dev_ip = models.DeviceIP(device_id=dev.id, ipv4=ip, mac=mac)
            auto_assign_network(db, dev_ip)
            db.add(dev_ip)
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
