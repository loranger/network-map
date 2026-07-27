from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    device_type = Column(String, nullable=False)
    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True)
    hostname = Column(String, nullable=True)
    ip_type = Column(String, nullable=True)
    mac = Column(String, nullable=True)
    ipv4 = Column(String, nullable=True)
    ipv6 = Column(String, nullable=True)
    floor = Column(String, nullable=True)
    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    discovered = Column(Boolean, default=False)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    ports = relationship("SwitchPort", back_populates="switch",
                         foreign_keys="SwitchPort.switch_id",
                         cascade="all, delete-orphan")
    connections_a = relationship("Connection", back_populates="device_a",
                                 foreign_keys="Connection.device_a_id",
                                 cascade="all, delete-orphan")
    connections_b = relationship("Connection", back_populates="device_b",
                                 foreign_keys="Connection.device_b_id",
                                 cascade="all, delete-orphan")


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
    notes = Column(Text, nullable=True)

    device_a = relationship("Device", back_populates="connections_a",
                            foreign_keys=[device_a_id])
    device_b = relationship("Device", back_populates="connections_b",
                            foreign_keys=[device_b_id])


class Network(Base):
    __tablename__ = "networks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ssid = Column(String, nullable=True)
    type = Column(String, nullable=False)
    subnet = Column(String, nullable=True)
    gateway = Column(String, nullable=True)
    dns = Column(String, nullable=True)
