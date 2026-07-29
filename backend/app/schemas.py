import ipaddress
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


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


class LocationBase(BaseModel):
    name: str
    floor: Optional[str] = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    floor: Optional[str] = None


class LocationResponse(LocationBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceIPCreate(BaseModel):
    ipv4: Optional[str] = None
    mac: Optional[str] = None
    network_id: Optional[int] = None
    ip_type: Optional[str] = None


class DeviceIPResponse(BaseModel):
    id: int
    device_id: int
    ipv4: Optional[str] = None
    mac: Optional[str] = None
    network_id: Optional[int] = None
    ip_type: Optional[str] = None
    network_name: Optional[str] = None

    model_config = {"from_attributes": True}


class DeviceBase(BaseModel):
    name: str
    device_type: str
    hostname: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    location_id: Optional[int] = None
    ap_network_ids: list[int] = []
    notes: Optional[str] = None
    admin_url: Optional[str] = None


class DeviceCreate(DeviceBase):
    ips: list[DeviceIPCreate] = []


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    device_type: Optional[str] = None
    hostname: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    location_id: Optional[int] = None
    ap_network_ids: Optional[list[int]] = None
    notes: Optional[str] = None
    admin_url: Optional[str] = None
    ips: Optional[list[DeviceIPCreate]] = None


class DeviceResponse(DeviceBase):
    id: int
    discovered: bool
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    ports: list[SwitchPortResponse] = []
    ips: list[DeviceIPResponse] = []
    location_name: Optional[str] = None
    location_floor: Optional[str] = None

    model_config = {"from_attributes": True}


class ConnectionBase(BaseModel):
    device_a_id: int
    device_b_id: int
    type: str
    technology: Optional[str] = None
    speed: Optional[str] = None
    color: Optional[str] = None
    network_id: Optional[int] = None
    notes: Optional[str] = None


class ConnectionCreate(ConnectionBase):
    pass


class ConnectionResponse(ConnectionBase):
    id: int
    device_a_name: Optional[str] = None
    device_b_name: Optional[str] = None
    network_name: Optional[str] = None

    model_config = {"from_attributes": True}


class NetworkBase(BaseModel):
    name: str
    ssid: Optional[str] = None
    type: str
    subnet: Optional[str] = None
    gateway: Optional[str] = None
    dns: Optional[str] = None
    color: Optional[str] = None


class NetworkCreate(NetworkBase):
    @field_validator("subnet")
    @classmethod
    def validate_subnet(cls, v):
        if v:
            try:
                ipaddress.ip_network(v, strict=False)
            except ValueError as e:
                raise ValueError(f"Invalid subnet: {e}")
        return v


class NetworkUpdate(BaseModel):
    name: Optional[str] = None
    ssid: Optional[str] = None
    type: Optional[str] = None
    subnet: Optional[str] = None
    gateway: Optional[str] = None
    dns: Optional[str] = None
    color: Optional[str] = None
    ap_device_ids: Optional[list[int]] = None

    @field_validator("subnet")
    @classmethod
    def validate_subnet(cls, v):
        if v:
            try:
                ipaddress.ip_network(v, strict=False)
            except ValueError as e:
                raise ValueError(f"Invalid subnet: {e}")
        return v


class NetworkResponse(NetworkBase):
    id: int
    ap_device_ids: list[int] = []

    model_config = {"from_attributes": True}


class DeviceTypeBase(BaseModel):
    type: str
    label: str
    color: str


class DeviceTypeCreate(DeviceTypeBase):
    pass


class DeviceTypeUpdate(BaseModel):
    label: Optional[str] = None
    color: Optional[str] = None


class DeviceTypeResponse(DeviceTypeBase):
    id: int

    model_config = {"from_attributes": True}


class GraphData(BaseModel):
    nodes: list[dict]
    edges: list[dict]
