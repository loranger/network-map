import socket
from typing import Optional

from sqlalchemy.orm import Session

from . import models

OUI_DB = {
    "00037F": "Synology",
    "001132": "Synology",
    "0013A2": "Raspberry Pi",
    "001A2B": "Raspberry Pi",
    "002590": "Apple",
    "00AA01": "Intel",
    "00A0C9": "Intel",
    "00B00C": "Dell",
    "00B064": "HP",
    "00C0B7": "Netgear",
    "00D059": "Netgear",
    "00D0D3": "Belkin",
    "00E018": "Dell",
    "00E04C": "Dell",
    "00E08F": "Cisco",
    "00E0B0": "Cisco",
    "00E0BD": "Dell",
    "00E0F7": "Dell",
    "020701": "Raspberry Pi",
    "08002B": "DEC",
    "08005A": "IBM",
    "0C8C8D": "Apple",
    "0C9D92": "Samsung",
    "0CB5DE": "Xiaomi",
    "0CD746": "Intel",
    "0CF429": "Xiaomi",
    "0CF5A4": "TP-Link",
    "14F65A": "Apple",
    "1CC1DE": "Apple",
    "1C5C55": "Sony",
    "1CB72C": "Apple",
    "1CBDD8": "Ubiquiti",
    "1CFCBB": "Synology",
    "204E7F": "Apple",
    "20C6EB": "Xiaomi",
    "20AA25": "Freebox",
    "20D2A1": "Freebox",
    "20D906": "Ubiquiti",
    "24693E": "ASUS",
    "24497B": "Sony",
    "2482B3": "Canon",
    "2499DE": "Panasonic",
    "24B657": "Samsung",
    "244B81": "Ubiquiti",
    "24F067": "LG",
    "247018": "Microsoft",
    "24A43B": "Apple",
    "24CDC1": "Samsung",
    "286847": "Intel",
    "28C0DA": "Samsung",
    "2C3361": "Xiaomi",
    "2C4138": "HP",
    "2C542D": "Dell",
    "2CF0A2": "Intel",
    "2CFD52": "TP-Link",
    "3090AB": "Google",
    "30A0F7": "Ubiquiti",
    "30B216": "Samsung",
    "30D1D3": "Huawei",
    "34C959": "Apple",
    "3499D2": "Huawei",
    "34B571": "HP",
    "34F39B": "ASUS",
    "3C22FB": "Raspberry Pi",
    "3C5282": "Apple",
    "3C7C3F": "Dell",
    "3CB6B4": "Sony",
    "3CD16E": "Microsoft",
    "3CE5A6": "LG",
    "4001C5": "Huawei",
    "404A03": "Enedis",
    "40B395": "Xiaomi",
    "40D32D": "Apple",
    "40F02F": "TP-Link",
    "44D1FA": "Apple",
    "44D9E7": "Ubiquiti",
    "44D832": "Freebox",
    "48A97A": "Panasonic",
    "48DF1C": "Huawei",
    "48D38D": "Samsung",
    "48FD8B": "LG",
    "4C3C16": "Xiaomi",
    "4C5254": "Microsoft",
    "4C77A4": "D-Link",
    "4C7C5F": "TP-Link",
    "4C9E3F": "Freebox",
    "4CD9C8": "Freebox",
    "5067AE": "Apple",
    "54E03A": "Netgear",
    "546041": "HP",
    "548998": "Cisco",
    "54B620": "TP-Link",
    "54A050": "Ubiquiti",
    "60A44C": "Apple",
    "64A3CB": "ASUS",
    "6C8814": "Apple",
    "6C9CED": "Apple",
    "6CDB31": "Panasonic",
    "70D57E": "Microsoft",
    "70F1A1": "MikroTik",
    "74DA38": "Freebox",
    "78A6BD": "Apple",
    "7C6193": "HP",
    "80BE05": "Huawei",
    "8863DF": "Apple",
    "8C705A": "Intel",
    "8C8590": "Intel",
    "A0A4C5": "Apple",
    "A0AD9F": "Apple",
    "A4134E": "Apple",
    "A438CC": "Apple",
    "A8A159": "Apple",
    "AC8DB1": "Apple",
    "B082E2": "ASUS",
    "B827EB": "Raspberry Pi",
    "C005C2": "Synology",
    "CC08E0": "Apple",
    "CC20E8": "Ubiquiti",
    "F0F6C1": "Apple",
    "F45C89": "Apple",
    "FC253F": "HP",
}

# Normalize keys: remove colons so they match lookup_oui() output
OUI_DB = {k.replace(":", "").upper(): v for k, v in OUI_DB.items()}


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
    if not device.manufacturer:
        for ip in device.ips:
            if ip.mac:
                mfr = lookup_oui(ip.mac)
                if mfr:
                    device.manufacturer = mfr
                    updated["manufacturer"] = mfr
                    break
    first_ip = device.ips[0].ipv4 if device.ips else None
    if first_ip:
        hn = reverse_dns(first_ip) if not device.hostname else device.hostname
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
