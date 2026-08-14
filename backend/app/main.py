import asyncio
import contextlib
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session, joinedload

from . import crud, models, schemas
from .database import Base, engine, get_db


def _background_scan():
    try:
        from .scanner import scan_network
        with Session(engine) as db:
            found = scan_network(db=db)
            print(f"Periodic scan: {len(found)} device(s) found")
    except Exception as e:
        print(f"Periodic scan error: {e}")


async def periodic_scan_loop():
    minutes = int(os.environ.get("SCAN_INTERVAL_MINUTES", "15") or 0)
    if minutes <= 0:
        print("Periodic scan: disabled (SCAN_INTERVAL_MINUTES <= 0)")
        return
    loop = asyncio.get_running_loop()
    lock = asyncio.Lock()
    print(f"Periodic scan: started, interval {minutes} min")
    while True:
        await loop.run_in_executor(None, _background_scan)
        await asyncio.sleep(minutes * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        for col in ["hostname", "ip_type", "floor"]:
            try:
                conn.execute(sql_text(f"ALTER TABLE devices ADD COLUMN {col} VARCHAR"))
                conn.commit()
            except Exception:
                pass
        try:
            conn.execute(sql_text("ALTER TABLE connections ADD COLUMN color VARCHAR"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("ALTER TABLE devices ADD COLUMN admin_url VARCHAR"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("ALTER TABLE devices ADD COLUMN location_id INTEGER REFERENCES locations(id)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("ALTER TABLE connections ADD COLUMN network_id INTEGER REFERENCES networks(id)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("""
                DELETE FROM device_ips WHERE id NOT IN (
                    SELECT MIN(id) FROM device_ips GROUP BY ipv4
                )
            """))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("CREATE UNIQUE INDEX IF NOT EXISTS uq_device_ips_ipv4 ON device_ips(ipv4)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("ALTER TABLE networks ADD COLUMN color VARCHAR"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("""
                UPDATE connections SET network_id = (
                    SELECT id FROM networks WHERE type = 'wired' LIMIT 1
                ) WHERE type = 'wired' AND network_id IS NULL
            """))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("""
                UPDATE device_ips SET network_id = (
                    SELECT id FROM networks WHERE type = 'wired' LIMIT 1
                ) WHERE network_id IS NULL AND ipv4 IS NOT NULL
            """))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("""
                CREATE TABLE IF NOT EXISTS device_ap_networks (
                    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
                    network_id INTEGER REFERENCES networks(id) ON DELETE CASCADE,
                    PRIMARY KEY (device_id, network_id)
                )
            """))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("""
                INSERT OR IGNORE INTO device_ap_networks (device_id, network_id)
                SELECT id, ap_network_id FROM devices WHERE ap_network_id IS NOT NULL
            """))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("ALTER TABLE devices DROP COLUMN ap_network_id"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("DROP INDEX IF EXISTS ix_devices_name"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("DROP INDEX IF EXISTS uq_device_name_location"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("ALTER TABLE device_ips ADD COLUMN mac VARCHAR"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("""
                UPDATE device_ips SET mac = (
                    SELECT mac FROM devices WHERE devices.id = device_ips.device_id
                ) WHERE mac IS NULL AND device_id IN (
                    SELECT id FROM devices WHERE mac IS NOT NULL
                )
            """))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("""
                INSERT INTO device_ips (device_id, mac)
                SELECT id, mac FROM devices
                WHERE mac IS NOT NULL AND id NOT IN (
                    SELECT DISTINCT device_id FROM device_ips
                )
            """))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("ALTER TABLE devices DROP COLUMN mac"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("ALTER TABLE device_types ADD COLUMN icon VARCHAR"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("ALTER TABLE devices ADD COLUMN icon VARCHAR"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("ALTER TABLE devices ADD COLUMN hostname_manual BOOLEAN"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("UPDATE devices SET hostname_manual = 0 WHERE hostname_manual IS NULL"))
            conn.commit()
        except Exception:
            pass
    with Session(engine) as session:
        # --- Add floor_id column to locations if missing ---
        try:
            session.execute(sql_text("SELECT floor_id FROM locations LIMIT 1"))
        except Exception:
            try:
                session.execute(sql_text("ALTER TABLE locations ADD COLUMN floor_id INTEGER REFERENCES floors(id)"))
                session.commit()
            except Exception:
                pass

        # --- Floor migration (string → FK) ---
        has_floor_column = False
        try:
            session.execute(sql_text("SELECT floor FROM locations LIMIT 1"))
            has_floor_column = True
        except Exception:
            pass
        if has_floor_column:
            rows = session.execute(
                sql_text("SELECT DISTINCT floor FROM locations WHERE floor IS NOT NULL")
            ).all()
            floor_map = {}
            for (floor_name,) in rows:
                existing = session.query(models.Floor).filter(
                    models.Floor.name == floor_name
                ).first()
                if not existing:
                    existing = models.Floor(name=floor_name, is_default=False)
                    session.add(existing)
                    session.flush()
                floor_map[floor_name] = existing.id
            loc_rows = session.execute(
                sql_text("SELECT id, floor FROM locations WHERE floor IS NOT NULL")
            ).all()
            for loc_id, floor_name in loc_rows:
                fid = floor_map.get(floor_name)
                if fid is not None:
                    session.execute(
                        sql_text("UPDATE locations SET floor_id = :fid WHERE id = :id"),
                        {"fid": fid, "id": loc_id}
                    )
            session.commit()
            try:
                session.execute(sql_text("ALTER TABLE locations DROP COLUMN floor"))
                session.commit()
            except Exception:
                pass

        # --- Seed initial locations from legacy devices ---
        existing = session.query(models.Location).count()
        if existing == 0:
            rows = session.execute(
                sql_text("SELECT DISTINCT location FROM devices WHERE location IS NOT NULL")
            ).all()
            for (location,) in rows:
                session.add(models.Location(name=location))
            session.commit()
            loc_map = {}
            for loc in session.query(models.Location).all():
                loc_map[loc.name] = loc
            for device in session.query(models.Device).filter(models.Device.location.isnot(None)):
                loc = loc_map.get(device.location)
                if loc:
                    device.location_id = loc.id
            session.commit()

        # --- Seed default floor if none exists ---
        if session.query(models.Floor).count() == 0:
            session.add(models.Floor(name="R+1", is_default=True))
            session.commit()

        if session.query(models.DeviceType).count() == 0:
            defaults = [
                models.DeviceType(type="router", label="Routeur", color="#3b82f6", icon="router"),
                models.DeviceType(type="modem", label="Modem", color="#8b5cf6", icon="network"),
                models.DeviceType(type="ap", label="Point d'accès", color="#06b6d4", icon="radio"),
                models.DeviceType(type="switch", label="Switch", color="#f59e0b", icon="arrow-left-right"),
                models.DeviceType(type="computer", label="Ordinateur", color="#10b981", icon="monitor"),
                models.DeviceType(type="server", label="Serveur", color="#ef4444", icon="server"),
                models.DeviceType(type="iot", label="IoT", color="#ec4899", icon="lightbulb"),
                models.DeviceType(type="other", label="Autre", color="#6b7280", icon="box"),
            ]
            for dt in defaults:
                session.add(dt)
            session.commit()
        default_icons = {
            "router": "router", "modem": "network", "ap": "radio",
            "switch": "arrow-left-right", "computer": "monitor",
            "server": "server", "iot": "lightbulb", "other": "box",
        }
        for dt in session.query(models.DeviceType).filter(models.DeviceType.icon.is_(None)).all():
            dt.icon = default_icons.get(dt.type, "box")
        session.commit()
    scan_task = asyncio.create_task(periodic_scan_loop())
    yield
    scan_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await scan_task


app = FastAPI(title="Network Map API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/devices", response_model=list[schemas.DeviceResponse])
def list_devices(
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = Query(None),
    location_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.Device).options(
        joinedload(models.Device.location_ref),
        joinedload(models.Device.ips).joinedload(models.DeviceIP.network),
    )
    if type:
        query = query.filter(models.Device.device_type == type)
    if location_id:
        query = query.filter(models.Device.location_id == location_id)
    devices = query.offset(skip).limit(limit).all()
    for d in devices:
        d.location_name = d.location_ref.name if d.location_ref else None
        d.location_floor = d.location_ref.floor_ref.name if (d.location_ref and d.location_ref.floor_ref) else None
        for ip in d.ips:
            ip.network_name = ip.network.name if ip.network else None
        for p in d.ports:
            if p.connected_device:
                p.connected_device_name = p.connected_device.name
    return devices


@app.get("/api/devices/{device_id}", response_model=schemas.DeviceResponse)
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = crud.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.location_name = device.location_ref.name if device.location_ref else None
    device.location_floor = device.location_ref.floor_ref.name if (device.location_ref and device.location_ref.floor_ref) else None
    for ip in device.ips:
        ip.network_name = ip.network.name if ip.network else None
    for p in device.ports:
        if p.connected_device:
            p.connected_device_name = p.connected_device.name
    return device


@app.post("/api/devices", response_model=schemas.DeviceResponse)
def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    db_device = crud.create_device(db, device)
    db_device.location_name = db_device.location_ref.name if db_device.location_ref else None
    db_device.location_floor = db_device.location_ref.floor_ref.name if (db_device.location_ref and db_device.location_ref.floor_ref) else None
    for ip in db_device.ips:
        ip.network_name = ip.network.name if ip.network else None
    return db_device


@app.put("/api/devices/{device_id}", response_model=schemas.DeviceResponse)
def update_device(
    device_id: int, device: schemas.DeviceUpdate, db: Session = Depends(get_db)
):
    updated = crud.update_device(db, device_id, device)
    if not updated:
        raise HTTPException(status_code=404, detail="Device not found")
    updated.location_name = updated.location_ref.name if updated.location_ref else None
    updated.location_floor = updated.location_ref.floor_ref.name if (updated.location_ref and updated.location_ref.floor_ref) else None
    for ip in updated.ips:
        ip.network_name = ip.network.name if ip.network else None
    return updated


@app.delete("/api/devices/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_device(db, device_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"ok": True}


@app.get("/api/devices/{device_id}/ports", response_model=list[schemas.SwitchPortResponse])
def list_ports(device_id: int, db: Session = Depends(get_db)):
    device = crud.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    ports = crud.get_switch_ports(db, device_id)
    for p in ports:
        if p.connected_device:
            p.connected_device_name = p.connected_device.name
    return ports


@app.post("/api/devices/{device_id}/ports", response_model=schemas.SwitchPortResponse)
def create_port(
    device_id: int, port: schemas.SwitchPortCreate, db: Session = Depends(get_db)
):
    device = crud.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    new_port = crud.create_switch_port(db, device_id, port)
    if new_port.connected_device:
        new_port.connected_device_name = new_port.connected_device.name
    return new_port


@app.put("/api/ports/{port_id}", response_model=schemas.SwitchPortResponse)
def update_port(port_id: int, data: dict, db: Session = Depends(get_db)):
    port = crud.update_switch_port(db, port_id, data)
    if not port:
        raise HTTPException(status_code=404, detail="Port not found")
    if port.connected_device:
        port.connected_device_name = port.connected_device.name
    return port


@app.delete("/api/ports/{port_id}")
def delete_port(port_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_switch_port(db, port_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Port not found")
    return {"ok": True}


@app.get("/api/connections", response_model=list[schemas.ConnectionResponse])
def list_connections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    conns = db.query(models.Connection).options(
        joinedload(models.Connection.network),
    ).offset(skip).limit(limit).all()
    all_devices = {d.id: d.name for d in db.query(models.Device).all()}
    for c in conns:
        c.device_a_name = all_devices.get(c.device_a_id)
        c.device_b_name = all_devices.get(c.device_b_id)
        c.network_name = c.network.name if c.network else None
    return conns


@app.post("/api/connections", response_model=schemas.ConnectionResponse)
def create_connection(conn: schemas.ConnectionCreate, db: Session = Depends(get_db)):
    return crud.create_connection(db, conn)


@app.put("/api/connections/{conn_id}", response_model=schemas.ConnectionResponse)
def update_connection(conn_id: int, data: dict, db: Session = Depends(get_db)):
    db_conn = db.query(models.Connection).filter(models.Connection.id == conn_id).first()
    if not db_conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    for key, value in data.items():
        setattr(db_conn, key, value)
    db.commit()
    db.refresh(db_conn)
    return db_conn


@app.delete("/api/connections/{conn_id}")
def delete_connection(conn_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_connection(db, conn_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"ok": True}


# --- Floors ---

@app.get("/api/floors", response_model=list[schemas.FloorResponse])
def list_floors(db: Session = Depends(get_db)):
    return crud.get_floors(db)


@app.post("/api/floors", response_model=schemas.FloorResponse)
def create_floor(floor: schemas.FloorCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Floor).filter(models.Floor.name == floor.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Floor already exists")
    return crud.create_floor(db, floor)


@app.put("/api/floors/{floor_id}", response_model=schemas.FloorResponse)
def update_floor(floor_id: int, floor: schemas.FloorUpdate, db: Session = Depends(get_db)):
    updated = crud.update_floor(db, floor_id, floor)
    if not updated:
        raise HTTPException(status_code=404, detail="Floor not found")
    return updated


@app.delete("/api/floors/{floor_id}")
def delete_floor(floor_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_floor(db, floor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Floor not found")
    return {"ok": True}


# --- Locations ---

@app.get("/api/locations", response_model=list[schemas.LocationResponse])
def list_locations(db: Session = Depends(get_db)):
    locs = crud.get_locations(db)
    for loc in locs:
        loc.floor_name = loc.floor_ref.name if loc.floor_ref else None
    return locs


@app.post("/api/locations", response_model=schemas.LocationResponse)
def create_location(loc: schemas.LocationCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Location).filter(
        models.Location.name == loc.name,
        models.Location.floor_id == loc.floor_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Location already exists")
    db_loc = crud.create_location(db, loc)
    db_loc.floor_name = db_loc.floor_ref.name if db_loc.floor_ref else None
    return db_loc


@app.delete("/api/locations/{loc_id}")
def delete_location(loc_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_location(db, loc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"ok": True}


@app.put("/api/locations/{loc_id}", response_model=schemas.LocationResponse)
def update_location(loc_id: int, loc: schemas.LocationUpdate, db: Session = Depends(get_db)):
    updated = crud.update_location(db, loc_id, loc)
    if not updated:
        raise HTTPException(status_code=404, detail="Location not found")
    updated.floor_name = updated.floor_ref.name if (updated and updated.floor_ref) else None
    return updated


# --- Device Types ---

@app.get("/api/device-types", response_model=list[schemas.DeviceTypeResponse])
def list_device_types(db: Session = Depends(get_db)):
    return crud.get_device_types(db)


@app.post("/api/device-types", response_model=schemas.DeviceTypeResponse)
def create_device_type(dt: schemas.DeviceTypeCreate, db: Session = Depends(get_db)):
    existing = db.query(models.DeviceType).filter(
        models.DeviceType.type == dt.type
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device type already exists")
    return crud.create_device_type(db, dt)


@app.put("/api/device-types/{dt_id}", response_model=schemas.DeviceTypeResponse)
def update_device_type(dt_id: int, dt: schemas.DeviceTypeUpdate, db: Session = Depends(get_db)):
    updated = crud.update_device_type(db, dt_id, dt)
    if not updated:
        raise HTTPException(status_code=404, detail="Device type not found")
    return updated


@app.delete("/api/device-types/{dt_id}")
def delete_device_type(dt_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_device_type(db, dt_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Device type not found")
    return {"ok": True}


# --- Networks ---

@app.get("/api/networks", response_model=list[schemas.NetworkResponse])
def list_networks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_networks(db, skip, limit)


@app.post("/api/networks", response_model=schemas.NetworkResponse)
def create_network(network: schemas.NetworkCreate, db: Session = Depends(get_db)):
    return crud.create_network(db, network)


@app.delete("/api/networks/{network_id}")
def delete_network(network_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_network(db, network_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Network not found")
    return {"ok": True}


@app.put("/api/networks/{network_id}", response_model=schemas.NetworkResponse)
def update_network(network_id: int, net: schemas.NetworkUpdate, db: Session = Depends(get_db)):
    updated = crud.update_network(db, network_id, net)
    if not updated:
        raise HTTPException(status_code=404, detail="Network not found")
    return updated


class ScanInput(BaseModel):
    subnet: Optional[str] = None


@app.post("/api/scan")
def scan(data: Optional[ScanInput] = None, db: Session = Depends(get_db)):
    from .scanner import scan_network
    found = scan_network(subnet=data.subnet if data else None, db=db)
    return {
        "found": len(found),
        "devices": found,
        "hint": len(found) < 3 and "Lancez 'bash scan-host.sh' depuis l'hôte pour un scan ARP réel, ou ajoutez les périphériques manuellement." or None,
    }


class ArpImportInput(BaseModel):
    raw: str


@app.post("/api/scan/import")
def import_arp(data: ArpImportInput, db: Session = Depends(get_db)):
    from .enricher import enrich_device as do_enrich
    from .scanner import PERSIST_LOCK, _is_valid_host, _parse_arp_table
    raw = _parse_arp_table(data.raw)
    found = [d for d in raw if _is_valid_host(d.get("ip"))]
    unique = []
    seen_ips = set()
    for d in found:
        if d["ip"] in seen_ips:
            continue
        seen_ips.add(d["ip"])
        unique.append(d)
    found = unique
    created = 0
    updated = 0
    enriched = 0
    with PERSIST_LOCK:
        for d in found:
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
                    owner = db.query(models.DeviceIP).filter(
                        models.DeviceIP.ipv4 == ip
                    ).first()
                    if owner is None:
                        dev_ip = models.DeviceIP(device_id=existing.id, ipv4=ip, mac=mac)
                        crud.auto_assign_network(db, dev_ip)
                        db.add(dev_ip)
                updated += 1
            elif mac:
                suffix = mac.replace(":", "").lower()
                name = hostname.split(".")[0] if hostname else f"device-{suffix}"
                new_device = crud.create_device(db, schemas.DeviceCreate(
                    name=name,
                    device_type="other",
                    hostname=hostname,
                    discovered=True,
                    ips=[schemas.DeviceIPCreate(ipv4=ip, mac=mac)],
                ))
                created += 1
                result = do_enrich(db, new_device)
                if result:
                    enriched += 1
        db.commit()
    return {"created": created, "updated": updated, "enriched": enriched, "ignored": len(raw) - len(found)}


@app.post("/api/enrich")
def enrich(db: Session = Depends(get_db)):
    from .enricher import enrich_all
    return enrich_all(db)


@app.post("/api/enrich/{device_id}")
def enrich_device(device_id: int, db: Session = Depends(get_db)):
    from .enricher import enrich_device as do_enrich, mdns_hostname_map
    from .freebox import freebox_hostname_map
    device = crud.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    first_ip = device.ips[0].ipv4 if device.ips else None
    mdns = {first_ip: mdns_hostname_map(first_ip)} if first_ip else {}
    hostname_map = {}
    try:
        hostname_map = freebox_hostname_map(db)
    except Exception as e:
        print(f"freebox API error: {e}")
    updated = do_enrich(db, device, mdns, hostname_map)
    db.refresh(device)
    device.location_name = device.location_ref.name if device.location_ref else None
    device.location_floor = device.location_ref.floor_ref.name if (device.location_ref and device.location_ref.floor_ref) else None
    for ip in device.ips:
        ip.network_name = ip.network.name if ip.network else None
    for p in device.ports:
        if p.connected_device:
            p.connected_device_name = p.connected_device.name
    return {"updated": updated, "device": device}


@app.get("/api/graph", response_model=schemas.GraphData)
def get_graph(db: Session = Depends(get_db)):
    return crud.get_graph_data(db)


# --- Accès (tokens) ---

@app.get("/api/access")
def list_accesses(db: Session = Depends(get_db)):
    from .freebox import freebox_config
    cfg = freebox_config(db)
    return {"accesses": [{
        "service": "freebox",
        "name": "Freebox",
        "configured": cfg["configured"],
        "base_url": cfg["base_url"],
    }]}


class PairInput(BaseModel):
    base_url: Optional[str] = None


@app.post("/api/access/freebox/pair")
def freebox_pair(data: PairInput, db: Session = Depends(get_db)):
    from .freebox import freebox_request_pair
    base_url = (data.base_url or "").strip() or "http://192.168.1.254"
    try:
        track_id = freebox_request_pair(db, base_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Freebox: {e}")
    return {"track_id": track_id, "message": "Validez l'autorisation sur l'écran de la Freebox."}


@app.get("/api/access/freebox/pair")
def freebox_pair_status(db: Session = Depends(get_db)):
    from .freebox import freebox_pair_status as status_fn
    return status_fn(db)


class TokenInput(BaseModel):
    token: str


@app.post("/api/access/freebox/token")
def freebox_token(data: TokenInput, db: Session = Depends(get_db)):
    from .freebox import freebox_set_token
    freebox_set_token(db, data.token.strip())
    return {"ok": True}


@app.delete("/api/access/freebox")
def freebox_clear(db: Session = Depends(get_db)):
    from .freebox import freebox_clear as clear_fn
    clear_fn(db)
    return {"ok": True}
