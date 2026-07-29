from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from . import models, schemas


# --- Devices ---

def get_devices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Device).options(
        joinedload(models.Device.location_ref),
        joinedload(models.Device.ips).joinedload(models.DeviceIP.network),
    ).offset(skip).limit(limit).all()


def get_device(db: Session, device_id: int):
    return db.query(models.Device).options(
        joinedload(models.Device.location_ref),
        joinedload(models.Device.ips).joinedload(models.DeviceIP.network),
    ).filter(models.Device.id == device_id).first()


def create_device(db: Session, device: schemas.DeviceCreate):
    data = device.model_dump()
    ips_data = data.pop("ips", [])
    db_device = models.Device(**data)
    db.add(db_device)
    db.flush()
    existing_ips = set()
    for row in db.query(models.DeviceIP.ipv4).filter(models.DeviceIP.ipv4.isnot(None)).all():
        existing_ips.add(row[0])
    for ip_entry in ips_data:
        if ip_entry.get("ipv4") and ip_entry["ipv4"] in existing_ips:
            continue
        db.add(models.DeviceIP(device_id=db_device.id, **ip_entry))
        if ip_entry.get("ipv4"):
            existing_ips.add(ip_entry["ipv4"])
    db.commit()
    db.refresh(db_device)
    return db_device


def update_device(db: Session, device_id: int, device: schemas.DeviceUpdate):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not db_device:
        return None
    data = device.model_dump(exclude_unset=True)
    ips_data = data.pop("ips", None)
    if ips_data is not None:
        existing_ips = set()
        for row in db.query(models.DeviceIP.ipv4).filter(
            models.DeviceIP.ipv4.isnot(None),
            models.DeviceIP.device_id != device_id,
        ).all():
            existing_ips.add(row[0])
        db.query(models.DeviceIP).filter(models.DeviceIP.device_id == device_id).delete()
        for ip_entry in ips_data:
            if ip_entry.get("ipv4") and ip_entry["ipv4"] in existing_ips:
                continue
            db.add(models.DeviceIP(device_id=device_id, **ip_entry))
            if ip_entry.get("ipv4"):
                existing_ips.add(ip_entry["ipv4"])
    for key, value in data.items():
        setattr(db_device, key, value)
    db.commit()
    db.refresh(db_device)
    return db_device


def delete_device(db: Session, device_id: int):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if db_device:
        db.delete(db_device)
        db.commit()
    return db_device


# --- SwitchPorts ---

def get_switch_ports(db: Session, switch_id: int):
    ports = db.query(models.SwitchPort).filter(
        models.SwitchPort.switch_id == switch_id
    ).options(
        joinedload(models.SwitchPort.connected_device)
    ).all()
    return ports


def update_switch_port(db: Session, port_id: int, data: dict):
    port = db.query(models.SwitchPort).filter(
        models.SwitchPort.id == port_id
    ).first()
    if not port:
        return None
    old_device_id = port.connected_device_id
    for key, value in data.items():
        setattr(port, key, value)
    new_device_id = port.connected_device_id

    if new_device_id and new_device_id != old_device_id:
        existing = db.query(models.Connection).filter(
            (
                (models.Connection.device_a_id == port.switch_id) &
                (models.Connection.device_b_id == new_device_id)
            ) | (
                (models.Connection.device_a_id == new_device_id) &
                (models.Connection.device_b_id == port.switch_id)
            )
        ).first()
        if not existing:
            db.add(models.Connection(
                device_a_id=port.switch_id,
                device_b_id=new_device_id,
                type="wired",
                technology="Ethernet",
            ))
        wired = db.query(models.Network).filter(
            models.Network.type == "wired"
        ).first()
        if wired:
            for ip in db.query(models.DeviceIP).filter(
                models.DeviceIP.device_id == new_device_id,
                models.DeviceIP.network_id.is_(None),
            ).all():
                ip.network_id = wired.id
    elif old_device_id and not new_device_id:
        db.query(models.Connection).filter(
            (
                (models.Connection.device_a_id == port.switch_id) &
                (models.Connection.device_b_id == old_device_id)
            ) | (
                (models.Connection.device_a_id == old_device_id) &
                (models.Connection.device_b_id == port.switch_id)
            )
        ).delete()

    db.commit()
    db.refresh(port)
    return port


def create_switch_port(db: Session, switch_id: int, port: schemas.SwitchPortCreate):
    db_port = models.SwitchPort(switch_id=switch_id, **port.model_dump())
    db.add(db_port)
    db.commit()
    db.refresh(db_port)
    return db_port


def delete_switch_port(db: Session, port_id: int):
    db_port = db.query(models.SwitchPort).filter(
        models.SwitchPort.id == port_id
    ).first()
    if db_port:
        db.delete(db_port)
        db.commit()
    return db_port


# --- Connections ---

def get_connections(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Connection).offset(skip).limit(limit).all()


def create_connection(db: Session, conn: schemas.ConnectionCreate):
    db_conn = models.Connection(**conn.model_dump())
    db.add(db_conn)
    db.commit()
    db.refresh(db_conn)
    return db_conn


def delete_connection(db: Session, conn_id: int):
    db_conn = db.query(models.Connection).filter(
        models.Connection.id == conn_id
    ).first()
    if db_conn:
        db.delete(db_conn)
        db.commit()
    return db_conn


# --- Networks ---

def get_networks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Network).offset(skip).limit(limit).all()


def create_network(db: Session, network: schemas.NetworkCreate):
    db_network = models.Network(**network.model_dump())
    db.add(db_network)
    db.commit()
    db.refresh(db_network)
    return db_network


def delete_network(db: Session, network_id: int):
    db_network = db.query(models.Network).filter(
        models.Network.id == network_id
    ).first()
    if db_network:
        db.delete(db_network)
        db.commit()
    return db_network


def update_network(db: Session, network_id: int, net: schemas.NetworkUpdate):
    db_net = db.query(models.Network).filter(models.Network.id == network_id).first()
    if db_net:
        for key, value in net.model_dump(exclude_unset=True).items():
            setattr(db_net, key, value)
        db.commit()
        db.refresh(db_net)
    return db_net


# --- Locations ---

def get_locations(db: Session):
    return db.query(models.Location).order_by(func.lower(models.Location.name)).all()


def create_location(db: Session, loc: schemas.LocationCreate):
    db_loc = models.Location(**loc.model_dump())
    db.add(db_loc)
    db.commit()
    db.refresh(db_loc)
    return db_loc


def delete_location(db: Session, loc_id: int):
    db_loc = db.query(models.Location).filter(models.Location.id == loc_id).first()
    if db_loc:
        db.delete(db_loc)
        db.commit()
    return db_loc


def update_location(db: Session, loc_id: int, loc: schemas.LocationUpdate):
    db_loc = db.query(models.Location).filter(models.Location.id == loc_id).first()
    if db_loc:
        for key, value in loc.model_dump(exclude_unset=True).items():
            setattr(db_loc, key, value)
        db.commit()
        db.refresh(db_loc)
    return db_loc


# --- Device Types ---

def get_device_types(db: Session):
    return db.query(models.DeviceType).order_by(func.lower(models.DeviceType.label)).all()


def create_device_type(db: Session, dt: schemas.DeviceTypeCreate):
    db_dt = models.DeviceType(**dt.model_dump())
    db.add(db_dt)
    db.commit()
    db.refresh(db_dt)
    return db_dt


def update_device_type(db: Session, dt_id: int, dt: schemas.DeviceTypeUpdate):
    db_dt = db.query(models.DeviceType).filter(models.DeviceType.id == dt_id).first()
    if db_dt:
        for key, value in dt.model_dump(exclude_unset=True).items():
            setattr(db_dt, key, value)
        db.commit()
        db.refresh(db_dt)
    return db_dt


def delete_device_type(db: Session, dt_id: int):
    db_dt = db.query(models.DeviceType).filter(models.DeviceType.id == dt_id).first()
    if db_dt:
        db.delete(db_dt)
        db.commit()
    return db_dt


# --- Graph ---

def get_graph_data(db: Session) -> schemas.GraphData:
    devices = db.query(models.Device).options(
        joinedload(models.Device.location_ref),
        joinedload(models.Device.ips).joinedload(models.DeviceIP.network),
    ).all()
    connections = db.query(models.Connection).options(
        joinedload(models.Connection.network),
    ).all()

    type_colors = {}
    for dt in db.query(models.DeviceType).all():
        type_colors[dt.type] = dt.color

    nodes = []
    for d in devices:
        loc_name = d.location_ref.name if d.location_ref else None
        loc_floor = d.location_ref.floor if d.location_ref else None
        first_ip = d.ips[0].ipv4 if d.ips else None
        nodes.append({
            "id": d.id,
            "label": d.name,
            "title": f"{d.device_type}<br>{first_ip or ''}<br>{loc_name or ''}",
            "color": type_colors.get(d.device_type, "#6b7280"),
            "shape": "box",
            "group": d.device_type,
            "location": loc_name,
            "floor": loc_floor,
            "location_id": d.location_id,
        })

    edges = []
    for c in connections:
        edge_color = c.color or (c.network.color if c.network else None) or "#94a3b8"
        edges.append({
            "from": c.device_a_id,
            "to": c.device_b_id,
            "label": c.technology or c.type,
            "dashes": c.type == "wireless",
            "color": {"color": edge_color},
            "network_id": c.network_id,
        })

    return schemas.GraphData(nodes=nodes, edges=edges)
