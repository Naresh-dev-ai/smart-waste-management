from datetime import datetime, date
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Date, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

class User(Base, TimestampMixin):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    full_name: Mapped[str]=mapped_column(String(120))
    email: Mapped[str]=mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    role: Mapped[str]=mapped_column(String(40), default="customer", index=True)
    phone: Mapped[str|None]=mapped_column(String(30), nullable=True)
    is_active: Mapped[bool]=mapped_column(Boolean, default=True)

class Zone(Base, TimestampMixin):
    __tablename__="zones"
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(100), unique=True)
    code: Mapped[str]=mapped_column(String(30), unique=True); description: Mapped[str|None]=mapped_column(Text, nullable=True)
    status: Mapped[str]=mapped_column(String(20), default="active"); supervisor_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"), nullable=True)
    schedule: Mapped[str|None]=mapped_column(String(200), nullable=True)

class Area(Base, TimestampMixin):
    __tablename__="areas"
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(120)); locality: Mapped[str]=mapped_column(String(120))
    street: Mapped[str|None]=mapped_column(String(150), nullable=True); zone_id: Mapped[int]=mapped_column(ForeignKey("zones.id"), index=True)

class WasteCategory(Base, TimestampMixin):
    __tablename__="waste_categories"
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(80), unique=True)
    recyclable: Mapped[bool]=mapped_column(Boolean, default=False); segregation_rule: Mapped[str|None]=mapped_column(Text, nullable=True)
    disposal_instruction: Mapped[str|None]=mapped_column(Text, nullable=True)

class Customer(Base, TimestampMixin):
    __tablename__="customers"
    id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str]=mapped_column(String(120)); phone: Mapped[str]=mapped_column(String(30)); email: Mapped[str|None]=mapped_column(String(180), nullable=True)
    address: Mapped[str]=mapped_column(Text); area_id: Mapped[int|None]=mapped_column(ForeignKey("areas.id"), nullable=True)
    latitude: Mapped[float|None]=mapped_column(Float, nullable=True); longitude: Mapped[float|None]=mapped_column(Float, nullable=True)
    service_status: Mapped[str]=mapped_column(String(20), default="active")

class Vehicle(Base, TimestampMixin):
    __tablename__="vehicles"
    id: Mapped[int]=mapped_column(primary_key=True); registration_no: Mapped[str]=mapped_column(String(30), unique=True)
    vehicle_type: Mapped[str]=mapped_column(String(50)); capacity_kg: Mapped[float]=mapped_column(Float)
    fuel_type: Mapped[str]=mapped_column(String(30)); status: Mapped[str]=mapped_column(String(30), default="available", index=True)
    last_service_date: Mapped[date|None]=mapped_column(Date, nullable=True)

class Worker(Base, TimestampMixin):
    __tablename__="workers"
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(120)); role: Mapped[str]=mapped_column(String(30))
    phone: Mapped[str]=mapped_column(String(30)); license_no: Mapped[str|None]=mapped_column(String(80), unique=True, nullable=True)
    skills: Mapped[str|None]=mapped_column(Text, nullable=True); available: Mapped[bool]=mapped_column(Boolean, default=True)
    supervisor_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"), nullable=True)

class PickupRequest(Base, TimestampMixin):
    __tablename__="pickup_requests"
    id: Mapped[int]=mapped_column(primary_key=True); customer_id: Mapped[int]=mapped_column(ForeignKey("customers.id"), index=True)
    category_id: Mapped[int]=mapped_column(ForeignKey("waste_categories.id")); zone_id: Mapped[int|None]=mapped_column(ForeignKey("zones.id"), nullable=True)
    estimated_kg: Mapped[float]=mapped_column(Float); pickup_address: Mapped[str]=mapped_column(Text)
    preferred_date: Mapped[date]=mapped_column(Date); priority: Mapped[str]=mapped_column(String(20), default="normal")
    status: Mapped[str]=mapped_column(String(30), default="pending", index=True); notes: Mapped[str|None]=mapped_column(Text, nullable=True)

class Assignment(Base, TimestampMixin):
    __tablename__="assignments"
    id: Mapped[int]=mapped_column(primary_key=True); pickup_id: Mapped[int]=mapped_column(ForeignKey("pickup_requests.id"), index=True)
    vehicle_id: Mapped[int]=mapped_column(ForeignKey("vehicles.id")); driver_id: Mapped[int]=mapped_column(ForeignKey("workers.id"))
    worker_ids: Mapped[list]=mapped_column(JSON, default=list); scheduled_at: Mapped[datetime]=mapped_column(DateTime)
    status: Mapped[str]=mapped_column(String(30), default="assigned")

class Collection(Base, TimestampMixin):
    __tablename__="collections"
    id: Mapped[int]=mapped_column(primary_key=True); pickup_id: Mapped[int]=mapped_column(ForeignKey("pickup_requests.id"), index=True)
    assignment_id: Mapped[int]=mapped_column(ForeignKey("assignments.id")); collected_kg: Mapped[float]=mapped_column(Float)
    collected_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow); status: Mapped[str]=mapped_column(String(30), default="completed")
    remarks: Mapped[str|None]=mapped_column(Text, nullable=True); photo_urls: Mapped[list]=mapped_column(JSON, default=list)

class RecyclingCenter(Base, TimestampMixin):
    __tablename__="recycling_centers"
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(120)); address: Mapped[str]=mapped_column(Text)
    capacity_kg: Mapped[float]=mapped_column(Float); accepted_category_ids: Mapped[list]=mapped_column(JSON, default=list)
    manager_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"), nullable=True); status: Mapped[str]=mapped_column(String(20), default="active")

class Transfer(Base, TimestampMixin):
    __tablename__="transfers"
    id: Mapped[int]=mapped_column(primary_key=True); collection_id: Mapped[int]=mapped_column(ForeignKey("collections.id"))
    center_id: Mapped[int]=mapped_column(ForeignKey("recycling_centers.id")); vehicle_id: Mapped[int]=mapped_column(ForeignKey("vehicles.id"))
    category_id: Mapped[int]=mapped_column(ForeignKey("waste_categories.id")); quantity_kg: Mapped[float]=mapped_column(Float)
    source_location: Mapped[str]=mapped_column(Text); status: Mapped[str]=mapped_column(String(30), default="in_transit")

class Segregation(Base, TimestampMixin):
    __tablename__="segregations"
    id: Mapped[int]=mapped_column(primary_key=True); transfer_id: Mapped[int]=mapped_column(ForeignKey("transfers.id"))
    recyclable_kg: Mapped[float]=mapped_column(Float); non_recyclable_kg: Mapped[float]=mapped_column(Float); contaminated_kg: Mapped[float]=mapped_column(Float)

class ProcessingBatch(Base, TimestampMixin):
    __tablename__="processing_batches"
    id: Mapped[int]=mapped_column(primary_key=True); center_id: Mapped[int]=mapped_column(ForeignKey("recycling_centers.id"))
    category_id: Mapped[int]=mapped_column(ForeignKey("waste_categories.id")); input_kg: Mapped[float]=mapped_column(Float)
    output_kg: Mapped[float]=mapped_column(Float); loss_kg: Mapped[float]=mapped_column(Float)
    processing_date: Mapped[date]=mapped_column(Date, default=date.today); status: Mapped[str]=mapped_column(String(30), default="completed")
    @property
    def yield_percent(self): return round((self.output_kg/self.input_kg)*100,2) if self.input_kg else 0

class Disposal(Base, TimestampMixin):
    __tablename__="disposals"
    id: Mapped[int]=mapped_column(primary_key=True); category_id: Mapped[int]=mapped_column(ForeignKey("waste_categories.id"))
    quantity_kg: Mapped[float]=mapped_column(Float); method: Mapped[str]=mapped_column(String(80)); location: Mapped[str]=mapped_column(Text)
    responsible_user_id: Mapped[int]=mapped_column(ForeignKey("users.id")); approved_by_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"), nullable=True)
    approved: Mapped[bool]=mapped_column(Boolean, default=False); disposal_date: Mapped[date]=mapped_column(Date, default=date.today)

class Maintenance(Base, TimestampMixin):
    __tablename__="maintenance"
    id: Mapped[int]=mapped_column(primary_key=True); vehicle_id: Mapped[int]=mapped_column(ForeignKey("vehicles.id"))
    description: Mapped[str]=mapped_column(Text); cost: Mapped[float]=mapped_column(Float, default=0); technician: Mapped[str|None]=mapped_column(String(120), nullable=True)
    scheduled_date: Mapped[date|None]=mapped_column(Date, nullable=True); completed: Mapped[bool]=mapped_column(Boolean, default=False)

class Complaint(Base, TimestampMixin):
    __tablename__="complaints"
    id: Mapped[int]=mapped_column(primary_key=True); customer_id: Mapped[int]=mapped_column(ForeignKey("customers.id"))
    category: Mapped[str]=mapped_column(String(80)); description: Mapped[str]=mapped_column(Text); priority: Mapped[str]=mapped_column(String(20), default="normal")
    assigned_team: Mapped[str|None]=mapped_column(String(120), nullable=True); status: Mapped[str]=mapped_column(String(30), default="open")
    resolution_remarks: Mapped[str|None]=mapped_column(Text, nullable=True)

class Notification(Base, TimestampMixin):
    __tablename__="notifications"
    id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str]=mapped_column(String(160)); message: Mapped[str]=mapped_column(Text); read: Mapped[bool]=mapped_column(Boolean, default=False)

class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[int]=mapped_column(primary_key=True); actor_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str]=mapped_column(String(80), index=True); entity: Mapped[str]=mapped_column(String(80)); entity_id: Mapped[int|None]=mapped_column(Integer, nullable=True)
    details: Mapped[dict]=mapped_column(JSON, default=dict); timestamp: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow, index=True)
