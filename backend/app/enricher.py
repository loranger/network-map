import socket
from typing import Optional

from sqlalchemy.orm import Session

from . import models

OUI_DB = {
    "00037F": "Synology",
    "001132": "Synology",
    "0013A2": "Raspberry Pi",
    "001A2B": "Raspberry Pi",
    "00AA01": "Intel",
    "08002B": "DEC",
    "08005A": "IBM",
    "08:00:20": "Sun Microsystems",
    "0C8C8D": "Apple",
    "14:10:9F": "ASUS",
    "14F65A": "Apple",
    "1C:69:7A": "Intel",
    "1C:B7:2C": "Apple",
    "1CC1DE": "Apple",
    "20:66:CF": "Freebox",
    "22:99:D3": "Intel",
    "24:4B:FE": "Ubiquiti",
    "286847": "Intel",
    "2C:B0:5D": "Google",
    "3090AB": "Google",
    "38:F7:3D": "Huawei",
    "3C:5A:B4": "Intel",
    "3C:6A:9D": "Ubiquiti",
    "40:16:7C": "Apple",
    "3C22FB": "Raspberry Pi",
    "4281B8": "Apple",
    "44:D1:FA": "Apple",
    "50:EB:F6": "Apple",
    "54:2A:1B": "Samsung",
    "54:E0:3A": "Netgear",
    "58:8B:F3": "Ubiquiti",
    "6C:A0:42": "Apple",
    "6C:D5:52": "Apple",
    "70:5A:0F": "Huawei",
    "74:C6:3B": "Apple",
    "78:8B:5C": "Apple",
    "80:BE:05": "Huawei",
    "84:29:99": "Huawei",
    "8C:26:AA": "Apple",
    "8C:85:90": "Intel",
    "94:9F:3E": "Apple",
    "A0:AD:9F": "Apple",
    "A4:38:CC": "Apple",
    "A8:A1:59": "Apple",
    "B0:82:E2": "ASUS",
    "B8:27:EB": "Raspberry Pi",
    "C0:05:C2": "Synology",
    "CC:98:8B": "Apple",
    "D0:52:A8": "Apple",
    "DC:A6:32": "Apple",
    "E0:2B:E9": "Apple",
    "E0:3F:49": "Samsung",
    "EC:0E:C4": "Huawei",
    "F0:F6:C1": "Apple",
    "F4:5C:89": "Apple",
    "FC:25:3F": "HP",
}


def lookup_oui(mac: str) -> Optional[str]:
    if not mac:
        return None
    prefix = mac.replace(":", "").upper()[:6]
    return OUI_DB.get(prefix)


def reverse_dns(ip: str) -> Optional[str]:
    if not ip:
        return None
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror, OSError):
        return None


def enrich_device(db: Session, device: models.Device) -> dict:
    updated = {}
    if device.mac and not device.manufacturer:
        mfr = lookup_oui(device.mac)
        if mfr:
            device.manufacturer = mfr
            updated["manufacturer"] = mfr
    if device.ipv4:
        hn = reverse_dns(device.ipv4) if not device.hostname else device.hostname
        if hn:
            if not device.hostname:
                device.hostname = hn
                updated["hostname"] = hn
            if device.name.startswith("device-"):
                short = hn.split(".")[0] if "." in hn else hn
                device.name = short
                updated["name"] = short
    if updated:
        db.commit()
    return updated


def enrich_all(db: Session) -> dict:
    devices = db.query(models.Device).all()
    total = len(devices)
    enriched = 0
    for device in devices:
        if enrich_device(db, device):
            enriched += 1
    return {"total": total, "enriched": enriched}
