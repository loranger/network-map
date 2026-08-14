import hashlib
import hmac

import requests
from sqlalchemy.orm import Session

from . import crud

APP_ID = "fr.networkmap"
APP_NAME = "Network Map"
APP_VERSION = "1.0"
DEVICE_NAME = "network-map"

_API_VERSION = "v4"
_TIMEOUT = 5

_KEY_BASE_URL = "freebox.base_url"
_KEY_APP_TOKEN = "freebox.app_token"
_KEY_PENDING_TRACK = "freebox.pending_track_id"
_KEY_PENDING_TOKEN = "freebox.pending_app_token"


def freebox_config(db: Session) -> dict:
    return {
        "base_url": (crud.get_setting(db, _KEY_BASE_URL) or "http://192.168.1.254").rstrip("/"),
        "app_token": crud.get_setting(db, _KEY_APP_TOKEN) or "",
        "configured": bool(crud.get_setting(db, _KEY_APP_TOKEN)),
    }


def _api(base_url: str, path: str, method: str = "GET", body: dict | None = None, headers: dict | None = None):
    url = f"{base_url}/api/{_API_VERSION}/{path}"
    resp = requests.request(method, url, json=body, headers=headers, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Freebox {path}: {data.get('error_code') or data.get('msg') or 'unknown error'}")
    return data


def _session_token(base_url: str, app_token: str) -> str:
    challenge = _api(base_url, "login/")["result"]["challenge"]
    password = hmac.new(app_token.encode(), challenge.encode(), hashlib.sha1).hexdigest()
    session = _api(
        base_url,
        "login/session/",
        "POST",
        {"app_id": APP_ID, "password": password},
    )
    return session["result"]["session_token"]


def freebox_request_pair(db: Session, base_url: str) -> int:
    """Demande un jeton d'app. Retourne le track_id à valider sur l'écran Freebox."""
    crud.set_setting(db, _KEY_BASE_URL, base_url.rstrip("/"))
    res = _api(
        base_url,
        "login/authorize/",
        "POST",
        {
            "app_id": APP_ID,
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "device_name": DEVICE_NAME,
        },
    )
    if not res.get("success"):
        raise RuntimeError(res.get("msg", "unknown error"))
    result = res["result"]
    crud.set_setting(db, _KEY_PENDING_TRACK, str(result["track_id"]))
    crud.set_setting(db, _KEY_PENDING_TOKEN, result["app_token"])
    return result["track_id"]


def freebox_pair_status(db: Session) -> dict:
    """Interroge l'état d'un appairage en cours. Sauvegarde le token si accordé."""
    base_url = (crud.get_setting(db, _KEY_BASE_URL) or "http://192.168.1.254").rstrip("/")
    track_id = crud.get_setting(db, _KEY_PENDING_TRACK)
    if not track_id:
        return {"status": "none"}
    res = _api(base_url, f"login/authorize/{track_id}")
    status = res["result"]["status"]
    if status == "granted":
        token = crud.get_setting(db, _KEY_PENDING_TOKEN) or ""
        crud.set_setting(db, _KEY_APP_TOKEN, token)
        crud.set_setting(db, _KEY_PENDING_TRACK, None)
        crud.set_setting(db, _KEY_PENDING_TOKEN, None)
    return {"status": status}


def freebox_clear(db: Session):
    crud.set_setting(db, _KEY_APP_TOKEN, None)
    crud.set_setting(db, _KEY_PENDING_TRACK, None)
    crud.set_setting(db, _KEY_PENDING_TOKEN, None)


def freebox_set_token(db: Session, token: str):
    crud.set_setting(db, _KEY_APP_TOKEN, token)
    crud.set_setting(db, _KEY_PENDING_TRACK, None)
    crud.set_setting(db, _KEY_PENDING_TOKEN, None)


def freebox_hostname_map(db: Session) -> dict[str, str]:
    """Renvoie un mapping {IP: hostname} depuis la table LAN de la Freebox."""
    base_url, app_token, _ = freebox_config(db).values()
    if not app_token:
        return {}
    token = _session_token(base_url, app_token)
    headers = {"X-Fbx-App-Auth": token}
    API = f"{base_url}/api/{_API_VERSION}/"

    interfaces = _api(base_url, "lan/browser/interfaces/", headers=headers)["result"]

    result: dict[str, str] = {}
    for iface in interfaces:
        hosts = _api(base_url, f"lan/browser/{iface['name']}/", headers=headers)["result"]
        for host in hosts:
            names = host.get("names") or []
            name = host.get("primary_name") or (names[0].get("name") if names else None)
            if not name:
                continue
            for conn in host.get("l3connectivities") or []:
                if conn.get("af") == "ipv4":
                    result.setdefault(conn["addr"], name)
    return result
