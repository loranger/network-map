import os
from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

OFFLINE_TIMEOUT_MINUTES = int(os.environ.get("OFFLINE_TIMEOUT_MINUTES", "30"))


device_ap_networks = Table(
    "device_ap_networks",
    Base.metadata,
    Column("device_id", Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True),
    Column("network_id", Integer, ForeignKey("networks.id", ondelete="CASCADE"), primary_key=True),
)


class Floor(Base):
    __tablename__ = "floors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    locations = relationship("Location", back_populates="floor_ref")


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    floor_ref = relationship("Floor", back_populates="locations")
    devices = relationship("Device", back_populates="location_ref")


class DeviceIP(Base):
    __tablename__ = "device_ips"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    ipv4 = Column(String, nullable=True)
    mac = Column(String, nullable=True)
    network_id = Column(Integer, ForeignKey("networks.id", ondelete="SET NULL"), nullable=True)
    ip_type = Column(String, nullable=True)

    device = relationship("Device", back_populates="ips")
    network = relationship("Network")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)
    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True)
    hostname = Column(String, nullable=True)
    location = Column(String, nullable=True)
    floor = Column(String, nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    admin_url = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    discovered = Column(Boolean, default=False)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    location_ref = relationship("Location", back_populates="devices")
    ips = relationship("DeviceIP", back_populates="device",
                       cascade="all, delete-orphan")
    ports = relationship("SwitchPort", back_populates="switch",
                         foreign_keys="SwitchPort.switch_id",
                         cascade="all, delete-orphan")
    connections_a = relationship("Connection", back_populates="device_a",
                                 foreign_keys="Connection.device_a_id",
                                 cascade="all, delete-orphan")
    connections_b = relationship("Connection", back_populates="device_b",
                                 foreign_keys="Connection.device_b_id",
                                 cascade="all, delete-orphan")
    ap_networks = relationship("Network", secondary=device_ap_networks,
                               back_populates="ap_devices")

    @property
    def online(self) -> bool:
        if not self.discovered:
            return True
        if self.last_seen is None:
            return False
        cutoff = datetime.utcnow() - timedelta(minutes=OFFLINE_TIMEOUT_MINUTES)
        return self.last_seen >= cutoff

    @property
    def ap_network_ids(self) -> list[int]:
        return [n.id for n in self.ap_networks]


class SwitchPort(Base):
    __tablename__ = "switch_ports"

    id = Column(Integer, primary_key=True, index=True)
    switch_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    name = Column(String, nullable=False)
    connected_device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    vlan = Column(String, nullable=True)
    poe = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    switch = relationship("Device", back_populates="ports",
                          foreign_keys=[switch_id])
    connected_device = relationship("Device", foreign_keys=[connected_device_id])


class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    device_a_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    device_b_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    type = Column(String, nullable=False)
    technology = Column(String, nullable=True)
    speed = Column(String, nullable=True)
    color = Column(String, nullable=True)
    network_id = Column(Integer, ForeignKey("networks.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)

    device_a = relationship("Device", back_populates="connections_a",
                            foreign_keys=[device_a_id])
    device_b = relationship("Device", back_populates="connections_b",
                            foreign_keys=[device_b_id])
    network = relationship("Network")


class DeviceType(Base):
    __tablename__ = "device_types"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, unique=True, nullable=False)
    label = Column(String, nullable=False)
    color = Column(String, nullable=False)
    icon = Column(String, nullable=True)


class Network(Base):
    __tablename__ = "networks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ssid = Column(String, nullable=True)
    type = Column(String, nullable=False)
    subnet = Column(String, nullable=True)
    gateway = Column(String, nullable=True)
    dns = Column(String, nullable=True)
    color = Column(String, nullable=True)

    @property
    def ap_device_ids(self) -> list[int]:
        return [d.id for d in self.ap_devices] if hasattr(self, 'ap_devices') else []

    ap_devices = relationship("Device", secondary=device_ap_networks,
                              back_populates="ap_networks")
