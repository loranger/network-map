import os
import socket
import threading
import time
from typing import Optional

import dns.reversename
import dns.resolver
from sqlalchemy.orm import Session
from zeroconf import IPVersion, ServiceBrowser, ServiceListener, Zeroconf

from . import models

DNS_SERVERS = [s.strip() for s in os.environ.get("DNS_SERVERS", "").split(",") if s.strip()]

_REVERSE_TIMEOUT = 2

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
    "FC253F": "HP",
    "00037B": "Synology",
    "001132": "Synology",
    "001C7B": "Ubiquiti",
    "0022BD": "Netgear",
    "00255B": "Acer",
    "0040F3": "Netgear",
    "0050C2": "Netgear",
    "0050F2": "Microchip",
    "005A39": "ASUS",
    "00802D": "Intelbras",
    "009073": "Motorola",
    "0090D0": "Fujitsu",
    "009E1E": "Zyxel",
    "00A0C9": "Intel",
    "00AA01": "Intel",
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
    "00F4B9": "SFR",
    "00FC58": "Technicolor",
    "020701": "Raspberry Pi",
    "08002B": "DEC",
    "08005A": "IBM",
    "0C37DC": "Huawei",
    "0C8C8D": "Apple",
    "0C9D92": "Samsung",
    "0CB5DE": "Xiaomi",
    "0CD746": "Intel",
    "0CF429": "Xiaomi",
    "0CF5A4": "TP-Link",
    "0CE5C3": "Intelbras",
    "0CEEE6": "Lenovo",
    "0C9E91": "Toshiba",
    "100D7F": "OnePlus",
    "1065A3": "ZTE",
    "10C37B": "Samsung",
    "10E7C6": "Sony",
    "10FEED": "Google",
    "14F65A": "Apple",
    "14FEE4": "SFR",
    "183451": "Avm",
    "18A6F7": "Xiaomi",
    "18C58A": "LG",
    "18D6C7": "TP-Link",
    "1C5C55": "Sony",
    "1C917D": "Technicolor",
    "1CB72C": "Apple",
    "1CBDD8": "Ubiquiti",
    "1CC1DE": "Apple",
    "1CFCBB": "Synology",
    "204E7F": "Apple",
    "20AA25": "Freebox",
    "20C6EB": "Xiaomi",
    "20D2A1": "Freebox",
    "20D906": "Ubiquiti",
    "2405F5": "Google",
    "24497B": "Sony",
    "244B81": "Ubiquiti",
    "24693E": "ASUS",
    "247018": "Microsoft",
    "2482B3": "Canon",
    "2499DE": "Panasonic",
    "24A43B": "Apple",
    "24B657": "Samsung",
    "24CDC1": "Samsung",
    "24F067": "LG",
    "280A21": "Samsung",
    "286847": "Intel",
    "28C0DA": "Samsung",
    "2C3361": "Xiaomi",
    "2C4138": "HP",
    "2C542D": "Dell",
    "2CF0A2": "Intel",
    "2CFD52": "TP-Link",
    "303926": "Aruba",
    "3090AB": "Google",
    "30A0F7": "Ubiquiti",
    "30B216": "Samsung",
    "30D1D3": "Huawei",
    "34B571": "HP",
    "34C959": "Apple",
    "34F39B": "ASUS",
    "380E4D": "Ruckus",
    "38F3AB": "MikroTik",
    "3C22FB": "Raspberry Pi",
    "3C5282": "Apple",
    "3C7C3F": "Dell",
    "3CB6B4": "Sony",
    "3CD16E": "Microsoft",
    "3CE5A6": "LG",
    "3CF0B4": "Liteon",
    "3CCE15": "Benq",
    "4001C5": "Huawei",
    "404A03": "Enedis",
    "40B395": "Xiaomi",
    "40D32D": "Apple",
    "40F02F": "TP-Link",
    "44D1FA": "Apple",
    "44D832": "Freebox",
    "44D9E7": "Ubiquiti",
    "4495FA": "TCL",
    "48A97A": "Panasonic",
    "48B8E1": "Shaw",
    "48D38D": "Samsung",
    "48DF1C": "Huawei",
    "48FD8B": "LG",
    "4C3C16": "Xiaomi",
    "4C5254": "Microsoft",
    "4C77A4": "D-Link",
    "4C7C5F": "TP-Link",
    "4C9E3F": "Freebox",
    "4CD9C8": "Freebox",
    "4CFC31": "Schneider",
    "5067AE": "Apple",
    "508569": "Zyxel",
    "50C58D": "Samsung",
    "50E085": "Arris",
    "546041": "HP",
    "54A050": "Ubiquiti",
    "54B620": "TP-Link",
    "54E03A": "Netgear",
    "548998": "Cisco",
    "58639A": "Nvidia",
    "60A44C": "Apple",
    "60F2E3": "Samsung",
    "6476BA": "Samsung",
    "649EF3": "Bose",
    "64A3CB": "ASUS",
    "64D954": "Sonos",
    "6C8814": "Apple",
    "6C9CED": "Apple",
    "6CDB31": "Panasonic",
    "6C96AB": "Lenovo",
    "70D57E": "Microsoft",
    "70F1A1": "MikroTik",
    "74DA38": "Freebox",
    "78A6BD": "Apple",
    "78CABA": "AVM",
    "78D752": "Samsung",
    "7C11BE": "LG",
    "7C6193": "HP",
    "7CA237": "ZTE",
    "7CE9D3": "Apple",
    "80BE05": "Huawei",
    "8863DF": "Apple",
    "8866A5": "Samsung",
    "8894F9": "Sonos",
    "8C705A": "Intel",
    "8C8590": "Intel",
    "8C8EF2": "Samsung",
    "90F1AA": "Sonos",
    "94B8C6": "Samsung",
    "94D1AC": "Proximus",
    "98DA34": "Samsung",
    "9C2E70": "TP-Link",
    "9C3BA6": "Zyxel",
    "A0A4C5": "Apple",
    "A0AD9F": "Apple",
    "A4134E": "Apple",
    "A438CC": "Apple",
    "A4049C": "Ubiquiti",
    "A82066": "Apple",
    "A8574E": "Samsung",
    "A8A159": "Apple",
    "AC8DB1": "Apple",
    "B082E2": "ASUS",
    "B827EB": "Raspberry Pi",
    "B87879": "TP-Link",
    "C005C2": "Synology",
    "C04A00": "Samsung",
    "C093D1": "Panasonic",
    "C0C1C0": "Verizon",
    "C40ACB": "Google",
    "C48466": "ASUS",
    "CC08E0": "Apple",
    "CC20E8": "Ubiquiti",
    "CC34D3": "TCL",
    "D067E5": "Dell",
    "D0B33D": "TP-Link",
    "D4D748": "Orange",
    "D85D4C": "Ubiquiti",
    "D89695": "Apple",
    "DC4427": "Salesforce",
    "DC9B1C": "Huawei",
    "E0ACCB": "Apple",
    "E0B9A5": "Samsung",
    "E0D748": "Arris",
    "E41C4B": "Samsung",
    "E42BD2": "Toshiba",
    "F0F6C1": "Apple",
    "F45C89": "Apple",
    "F4B72A": "HP",
    "F80CF9": "Samsung",
    "F81D78": "Arris",
    "F8889E": "Sonos",
    "F8E4E3": "TP-Link",
    "FC253F": "HP",
    "FC3F7C": "Canon",
    "FCCE46": "Samsung",
    "FCDF70": "Samsung",
    "107C61": "ASUS",
    "2066CF": "Freebox",
    "381A52": "Epson",
    "50EBF6": "ASUS",
    "542A1B": "Sonos",
    "6CA042": "Silicon Labs",
    "6CD552": "Bilian",
    "8C26AA": "Apple",
    "9009D0": "Synology",
    "949F3E": "Sonos",
    "98BD80": "Intel",
    "9C6B00": "ASRock",
    "B40AD8": "Sony Interactive",
    "C435D9": "Apple",
    "CC988B": "Sony",
    "CCA7C1": "Google",
}

# Normalize keys: remove colons so they match lookup_oui() output
OUI_DB = {k.replace(":", "").upper(): v for k, v in OUI_DB.items()}


def lookup_oui(mac: str) -> Optional[str]:
    if not mac:
        return None
    prefix = mac.replace(":", "").upper()[:6]
    return OUI_DB.get(prefix)


def _ptr_via_dns(ip: str, nameservers: list[str] | None = None) -> Optional[str]:
    resolver = dns.resolver.Resolver()
    if nameservers:
        resolver.nameservers = nameservers
    resolver.timeout = _REVERSE_TIMEOUT
    resolver.lifetime = _REVERSE_TIMEOUT
    try:
        answers = resolver.resolve(dns.reversename.from_address(ip), "PTR")
        return str(answers[0]).rstrip(".")
    except Exception:
        return None


def _gethostbyaddr_bounded(ip: str, timeout: float = _REVERSE_TIMEOUT) -> Optional[str]:
    box = {"hostname": None}

    def worker():
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            box["hostname"] = hostname
        except Exception:
            box["hostname"] = None

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout)
    return box["hostname"]


def reverse_dns(ip: str) -> Optional[str]:
    if not ip:
        return None
    if DNS_SERVERS:
        return _ptr_via_dns(ip, DNS_SERVERS)
    hostname = _gethostbyaddr_bounded(ip)
    if hostname:
        return hostname
    return _ptr_via_dns(ip)


class _MdnsListener(ServiceListener):
    def __init__(self, register):
        self._service_types = set()
        self._instances = {}
        self._register = register

    def add_service(self, zc, type_, name):
        self._handle(zc, type_, name)

    def update_service(self, zc, type_, name):
        self._handle(zc, type_, name)

    def remove_service(self, zc, type_, name):
        pass

    def _handle(self, zc, type_, name):
        if type_ == "_services._dns-sd._udp.local.":
            self._service_types.add(name)
        else:
            self._instances.setdefault(type_, set()).add(name)

    def collect(self, browsers):
        self._resolved = set()

        def resolve():
            for t, names in list(self._instances.items()):
                for name in list(names):
                    key = (t, name)
                    if key in self._resolved:
                        continue
                    self._resolved.add(key)
                    info = zc.get_service_info(t, name, timeout=500)
                    if info is None:
                        continue
                    host = (info.server or "").rstrip(".")
                    if not host:
                        continue
                    for addr in info.parsed_addresses():
                        ip = str(addr)
                        if ":" not in ip:
                            self._register.setdefault(ip, host)

        zc = browsers[0].zc if browsers else None
        if zc is None:
            return
        resolve()


def mdns_hostname_map(ip: str, timeout: int = 3) -> Optional[str]:
    """Retourne le hostname mDNS (.local) de l'IP donnée."""
    result: dict[str, str] = {}
    browsers: list = []
    zc = Zeroconf()
    try:
        listener = _MdnsListener(result)
        browsers.append(ServiceBrowser(zc, "_services._dns-sd._udp.local.", listener))
        deadline = time.time() + timeout
        seen_types = set()
        while time.time() < deadline:
            for t in list(listener._service_types):
                if t not in seen_types:
                    seen_types.add(t)
                    browsers.append(ServiceBrowser(zc, t, listener))
            listener.collect(browsers)
            if result.get(ip):
                return result[ip]
            time.sleep(0.5)
        return result.get(ip)
    finally:
        for b in browsers:
            try:
                b.cancel()
            except Exception:
                pass
        zc.close()


def mdns_hostname_map_all(timeout: int = 5) -> dict[str, str]:
    """Retourne un mapping {IP: hostname mDNS} de tout le LAN."""
    result: dict[str, str] = {}
    browsers: list = []
    zc = Zeroconf()
    try:
        listener = _MdnsListener(result)
        browsers.append(ServiceBrowser(zc, "_services._dns-sd._udp.local.", listener))
        deadline = time.time() + timeout
        seen_types = set()
        while time.time() < deadline:
            for t in list(listener._service_types):
                if t not in seen_types:
                    seen_types.add(t)
                    browsers.append(ServiceBrowser(zc, t, listener))
            listener.collect(browsers)
            time.sleep(0.5)
        return result
    finally:
        for b in browsers:
            try:
                b.cancel()
            except Exception:
                pass
        zc.close()


def enrich_device(db: Session, device: models.Device, mdns_map: dict | None = None) -> dict:
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
        hn = device.hostname
        if not hn:
            hn = reverse_dns(first_ip)
            if not hn and mdns_map:
                hn = mdns_map.get(first_ip)
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
    mdns_map = mdns_hostname_map_all()
    enriched = 0
    for device in devices:
        if enrich_device(db, device, mdns_map):
            enriched += 1
    return {"total": total, "enriched": enriched}
