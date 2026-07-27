from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SwitchPortBase(BaseModel):
    name: str
    connected_device_id: Optional[int] = None
    vlan: Optional[str] = None
    poe: bool = False
    notes: Optional[str] = None


class SwitchPortCreate(SwitchPortBase):
    pass


class SwitchPortResponse(SwitchPortBase):
    id: int
    switch_id: int
    connected_device_name: Optional[str] = None

    model_config = {"from_attributes": True}


class DeviceBase(BaseModel):
    name: str
    device_type: str
    hostname: Optional[str] = None
    ip_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    mac: Optional[str] = None
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    location: Optional[str] = None
    floor: Optional[str] = None
    notes: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    device_type: Optional[str] = None
    hostname: Optional[str] = None
    ip_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    mac: Optional[str] = None
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    floor: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class DeviceResponse(DeviceBase):
    id: int
    discovered: bool
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    ports: list[SwitchPortResponse] = []

    model_config = {"from_attributes": True}


class ConnectionBase(BaseModel):
    device_a_id: int
    device_b_id: int
    type: str
    technology: Optional[str] = None
    speed: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None


class ConnectionCreate(ConnectionBase):
    pass


class ConnectionResponse(ConnectionBase):
    id: int
    device_a_name: Optional[str] = None
    device_b_name: Optional[str] = None

    model_config = {"from_attributes": True}


class NetworkBase(BaseModel):
    name: str
    ssid: Optional[str] = None
    type: str
    subnet: Optional[str] = None
    gateway: Optional[str] = None
    dns: Optional[str] = None


class NetworkCreate(NetworkBase):
    pass


class NetworkResponse(NetworkBase):
    id: int

    model_config = {"from_attributes": True}


class GraphData(BaseModel):
    nodes: list[dict]
    edges: list[dict]
