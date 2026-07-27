from sqlalchemy.orm import Session, joinedload

from . import models, schemas


def get_devices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Device).offset(skip).limit(limit).all()


def get_device(db: Session, device_id: int):
    return db.query(models.Device).filter(models.Device.id == device_id).first()


def create_device(db: Session, device: schemas.DeviceCreate):
    db_device = models.Device(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def update_device(db: Session, device_id: int, device: schemas.DeviceUpdate):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if db_device:
        for key, value in device.model_dump(exclude_unset=True).items():
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


def get_graph_data(db: Session) -> schemas.GraphData:
    devices = db.query(models.Device).all()
    connections = db.query(models.Connection).all()

    type_colors = {
        "router": "#3b82f6",
        "modem": "#8b5cf6",
        "ap": "#06b6d4",
        "switch": "#f59e0b",
        "computer": "#10b981",
        "server": "#ef4444",
        "iot": "#ec4899",
        "other": "#6b7280",
    }

    nodes = []
    for d in devices:
        nodes.append({
            "id": d.id,
            "label": d.name,
            "title": f"{d.device_type}<br>{d.ipv4 or ''}<br>{d.location or ''}",
            "color": type_colors.get(d.device_type, "#6b7280"),
            "shape": "box",
            "group": d.device_type,
            "location": d.location,
            "floor": d.floor,
        })

    edges = []
    for c in connections:
        edge_color = c.color or "#94a3b8"
        edges.append({
            "from": c.device_a_id,
            "to": c.device_b_id,
            "label": c.technology or c.type,
            "dashes": c.type == "wireless",
            "color": {"color": edge_color},
        })

    return schemas.GraphData(nodes=nodes, edges=edges)
