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
            conn.execute(sql_text("DROP INDEX IF EXISTS ix_devices_name"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sql_text("DROP INDEX IF EXISTS uq_device_name_location"))
            conn.commit()
        except Exception:
            pass
    with Session(engine) as session:
        existing = session.query(models.Location).count()
        if existing == 0:
            rows = session.execute(
                sql_text("SELECT DISTINCT location FROM devices WHERE location IS NOT NULL")
            ).all()
            for (location,) in rows:
                floor_row = session.execute(
                    sql_text("SELECT floor FROM devices WHERE location = :loc AND floor IS NOT NULL LIMIT 1"),
                    {"loc": location}
                ).first()
                floor = floor_row[0] if floor_row else None
                session.add(models.Location(name=location, floor=floor))
            session.commit()
            loc_map = {}
            for loc in session.query(models.Location).all():
                loc_map[loc.name] = loc
            for device in session.query(models.Device).filter(models.Device.location.isnot(None)):
                loc = loc_map.get(device.location)
                if loc:
                    device.location_id = loc.id
            session.commit()
        if session.query(models.DeviceType).count() == 0:
            defaults = [
                models.DeviceType(type="router", label="Routeur", color="#3b82f6"),
                models.DeviceType(type="modem", label="Modem", color="#8b5cf6"),
                models.DeviceType(type="ap", label="Point d'accès", color="#06b6d4"),
                models.DeviceType(type="switch", label="Switch", color="#f59e0b"),
                models.DeviceType(type="computer", label="Ordinateur", color="#10b981"),
                models.DeviceType(type="server", label="Serveur", color="#ef4444"),
                models.DeviceType(type="iot", label="IoT", color="#ec4899"),
                models.DeviceType(type="other", label="Autre", color="#6b7280"),
            ]
            for dt in defaults:
                session.add(dt)
            session.commit()
    yield


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
        d.location_floor = d.location_ref.floor if d.location_ref else None
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
    device.location_floor = device.location_ref.floor if device.location_ref else None
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
    db_device.location_floor = db_device.location_ref.floor if db_device.location_ref else None
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
    updated.location_floor = updated.location_ref.floor if updated.location_ref else None
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


@app.get("/api/locations", response_model=list[schemas.LocationResponse])
def list_locations(db: Session = Depends(get_db)):
    return crud.get_locations(db)


@app.post("/api/locations", response_model=schemas.LocationResponse)
def create_location(loc: schemas.LocationCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Location).filter(
        models.Location.name == loc.name,
        models.Location.floor == loc.floor,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Location already exists")
    return crud.create_location(db, loc)


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


@app.post("/api/scan")
def scan(db: Session = Depends(get_db)):
    from .scanner import scan_network
    found = scan_network(db=db)
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
    from .scanner import _is_valid_host, _parse_arp_table
    raw = _parse_arp_table(data.raw)
    found = [d for d in raw if _is_valid_host(d.get("ip"))]
    created = 0
    updated = 0
    enriched = 0
    for d in found:
        ip, mac, hostname = d["ip"], d.get("mac"), d.get("hostname")
        existing = None
        if mac:
            existing = db.query(models.Device).filter(
                models.Device.mac == mac
            ).first()
        if not existing and ip:
            existing = db.query(models.Device).filter(
                models.Device.ips.any(models.DeviceIP.ipv4 == ip)
            ).first()
        if existing:
            existing.last_seen = datetime.utcnow()
            existing.discovered = True
            if mac and not existing.mac:
                existing.mac = mac
            if hostname and not existing.hostname:
                existing.hostname = hostname
            if hostname and existing.name.startswith("device-"):
                short = hostname.split(".")[0] if "." in hostname else hostname
                existing.name = short
            if ip and not any(dev_ip.ipv4 == ip for dev_ip in existing.ips):
                dev_ip = models.DeviceIP(device_id=existing.id, ipv4=ip)
                crud.auto_assign_network(db, dev_ip)
                db.add(dev_ip)
            updated += 1
        elif mac:
            suffix = mac.replace(":", "").lower()
            name = hostname.split(".")[0] if hostname else f"device-{suffix}"
            new_device = crud.create_device(db, schemas.DeviceCreate(
                name=name,
                device_type="other",
                mac=mac,
                hostname=hostname,
                discovered=True,
                ips=[schemas.DeviceIPCreate(ipv4=ip)],
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
    from .enricher import enrich_device as do_enrich
    device = crud.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    updated = do_enrich(db, device)
    db.refresh(device)
    device.location_name = device.location_ref.name if device.location_ref else None
    device.location_floor = device.location_ref.floor if device.location_ref else None
    for p in device.ports:
        if p.connected_device:
            p.connected_device_name = p.connected_device.name
    return {"updated": updated, "device": device}


@app.get("/api/graph", response_model=schemas.GraphData)
def get_graph(db: Session = Depends(get_db)):
    return crud.get_graph_data(db)
