from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, date
import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Float,
    ForeignKey,
    CheckConstraint,
    Index,
    and_,
    or_,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

database_url = os.getenv("DATABASE_PATH", "sqlite:///outputs/databases/leasetrack_commercial_property_lease_manager.db")
engine = create_engine("sqlite:////mnt/genming/training-local-cases-20261104/cases/b2b_saas_2_0/pre_state.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_users_email", User.email)

class Property(Base):
    __tablename__ = "properties"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address_line = Column(String, nullable=False)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    country = Column(String)
    property_type = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_properties_address", Property.address_line, Property.city, Property.state, Property.postal_code)
Index("idx_properties_name", Property.name)

class PropertyFeature(Base):
    __tablename__ = "property_features"
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    feature = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Index("idx_property_features_property_id", PropertyFeature.property_id)

class Unit(Base):
    __tablename__ = "units"
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    unit_name = Column(String, nullable=False)
    floor_number = Column(Integer)
    floor_area_sqm = Column(Float)
    fitout_type = Column(String)
    occupancy_status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_units_property_id", Unit.property_id)
Index("idx_units_property_unit", Unit.property_id, Unit.unit_name)

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    legal_name = Column(String, nullable=False)
    abn = Column(String)
    billing_address = Column(String)
    risk_rating = Column(String)
    primary_contact_name = Column(String)
    primary_contact_email = Column(String)
    primary_contact_phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_tenants_legal_name", Tenant.legal_name)
Index("idx_tenants_abn", Tenant.abn)

class Lease(Base):
    __tablename__ = "leases"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    lease_start_date = Column(Date, nullable=False)
    lease_end_date = Column(Date, nullable=False)
    rent_type = Column(String, nullable=False)
    security_deposit = Column(Float, nullable=False)
    break_options = Column(String)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_leases_tenant_id", Lease.tenant_id)
Index("idx_leases_unit_id", Lease.unit_id)
Index("idx_leases_dates", Lease.lease_start_date, Lease.lease_end_date)

class RentSchedule(Base):
    __tablename__ = "rent_schedules"
    id = Column(Integer, primary_key=True)
    lease_id = Column(Integer, ForeignKey("leases.id"), nullable=False)
    charge_type = Column(String, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="AUD")
    is_generated = Column(Integer, nullable=False, default=1)
    is_revised = Column(Integer, nullable=False, default=0)
    revision_note = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_rent_schedules_lease_id", RentSchedule.lease_id)
Index("idx_rent_schedules_lease_due", RentSchedule.lease_id, RentSchedule.due_date)
Index("idx_rent_schedules_charge_type", RentSchedule.charge_type)

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    lease_id = Column(Integer, ForeignKey("leases.id"), nullable=False)
    rent_schedule_id = Column(Integer, ForeignKey("rent_schedules.id"))
    invoice_number = Column(String)
    charge_type = Column(String, nullable=False)
    description = Column(String)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    amount_paid = Column(Float, nullable=False, default=0.0)
    allocation_status = Column(String, nullable=False, default="unallocated")
    status = Column(String, nullable=False, default="unpaid")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_invoices_tenant_id", Invoice.tenant_id)
Index("idx_invoices_lease_id", Invoice.lease_id)
Index("idx_invoices_due_date", Invoice.due_date)
Index("idx_invoices_status", Invoice.status)
Index("idx_invoices_allocation_status", Invoice.allocation_status)

class IndexationEvent(Base):
    __tablename__ = "indexation_events"
    id = Column(Integer, primary_key=True)
    lease_id = Column(Integer, ForeignKey("leases.id"), nullable=False)
    effective_date = Column(Date, nullable=False)
    index_rate = Column(Float, nullable=False)
    description = Column(String)
    applied = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_indexation_events_lease_date", IndexationEvent.lease_id, IndexationEvent.effective_date)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    received_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)
    reference = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_payments_tenant_id", Payment.tenant_id)
Index("idx_payments_received_date", Payment.received_date)

class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"
    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    allocated_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Index("idx_payment_allocations_payment_id", PaymentAllocation.payment_id)
Index("idx_payment_allocations_invoice_id", PaymentAllocation.invoice_id)

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_name = Column(String)
    contact_email = Column(String)
    contact_phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_vendors_name", Vendor.name)

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"))
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    priority_level = Column(String, nullable=False)
    issue_category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    photos_metadata = Column(String)
    preferred_access_times = Column(String)
    status = Column(String, nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    resolution_notes = Column(String)
    requested_date = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_maintenance_property_id", MaintenanceRequest.property_id)
Index("idx_maintenance_unit_id", MaintenanceRequest.unit_id)
Index("idx_maintenance_tenant_id", MaintenanceRequest.tenant_id)
Index("idx_maintenance_status", MaintenanceRequest.status)
Index("idx_maintenance_vendor_id", MaintenanceRequest.vendor_id)

class Inspection(Base):
    __tablename__ = "inspections"
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    inspection_type = Column(String, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    outcome = Column(String)
    follow_up_actions = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Index("idx_inspections_property_id", Inspection.property_id)
Index("idx_inspections_outcome", Inspection.outcome)
Index("idx_inspections_scheduled_date", Inspection.scheduled_date)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LeaseTrack Commercial Property Lease Manager API", version="1.0.0")

def now_utc() -> datetime:
    return datetime.utcnow()

class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique user identifier", example=1)
    username: str = Field(..., description="User login name", example="admin")
    email: str = Field(..., description="User email address", example="admin@example.com")
    full_name: Optional[str] = Field(None, description="Full display name", example="LeaseTrack Admin")
    created_at: datetime = Field(..., description="User creation timestamp", example="2024-01-01T12:00:00Z")
    updated_at: datetime = Field(..., description="User last update timestamp", example="2024-01-10T09:30:00Z")

class UserMeResponse(BaseModel):
    user: UserModel = Field(..., description="Current authenticated user", example={})

class PropertyCreateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Display name of the property", example="120 Market Street")
    address_line: str = Field(..., description="Street address line", example="120 Market Street")
    city: Optional[str] = Field(None, description="City or suburb", example="Sydney")
    state: Optional[str] = Field(None, description="State or region", example="NSW")
    postal_code: Optional[str] = Field(None, description="Postal or ZIP code", example="2000")
    country: Optional[str] = Field(None, description="Country name", example="Australia")
    property_type: str = Field(..., description="Property type; must be 'office' or 'industrial'", example="office")

class PropertyUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="New property name", example="120 Market Street Tower")
    address_line: Optional[str] = Field(None, description="Updated street address", example="120 Market St")
    city: Optional[str] = Field(None, description="Updated city", example="Sydney")
    state: Optional[str] = Field(None, description="Updated state", example="NSW")
    postal_code: Optional[str] = Field(None, description="Updated postal code", example="2000")
    country: Optional[str] = Field(None, description="Updated country", example="Australia")
    property_type: Optional[str] = Field(None, description="Updated property type", example="office")

class PropertyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Property identifier", example=1)
    name: Optional[str] = Field(None, description="Property name", example="120 Market Street")
    address_line: str = Field(..., description="Street address", example="120 Market Street")
    city: Optional[str] = Field(None, description="City or suburb", example="Sydney")
    state: Optional[str] = Field(None, description="State or region", example="NSW")
    postal_code: Optional[str] = Field(None, description="Postal code", example="2000")
    country: Optional[str] = Field(None, description="Country", example="Australia")
    property_type: str = Field(..., description="Property type", example="office")
    created_by: int = Field(..., description="User who created the property", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-01T10:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-01T10:00:00Z")

class PropertySingleResponse(BaseModel):
    property: PropertyModel = Field(..., description="Property object", example={})

class PropertyListResponse(BaseModel):
    properties: List[PropertyModel] = Field(..., description="List of properties", example=[])

class PropertyDeleteResult(BaseModel):
    success: bool = Field(..., description="True if property was deleted", example=True)
    deleted_property_id: int = Field(..., description="ID of deleted property", example=1)

class PropertyDeleteResponse(BaseModel):
    result: PropertyDeleteResult = Field(..., description="Delete result", example={})

class PropertyFeatureCreateRequest(BaseModel):
    feature: str = Field(..., description="Description of the feature", example="A-grade office tower")

class PropertyFeatureModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Property feature identifier", example=10)
    property_id: int = Field(..., description="Related property identifier", example=1)
    feature: str = Field(..., description="Feature description", example="A-grade office tower")
    created_at: datetime = Field(..., description="Feature creation timestamp", example="2025-01-01T10:05:00Z")

class PropertyFeatureSingleResponse(BaseModel):
    feature: PropertyFeatureModel = Field(..., description="Property feature", example={})

class PropertyFeatureListResponse(BaseModel):
    features: List[PropertyFeatureModel] = Field(..., description="List of property features", example=[])

class PropertyFeatureDeleteResult(BaseModel):
    success: bool = Field(..., description="True if feature was deleted", example=True)
    deleted_feature_id: int = Field(..., description="ID of deleted feature", example=10)

class PropertyFeatureDeleteResponse(BaseModel):
    result: PropertyFeatureDeleteResult = Field(..., description="Delete result", example={})

class UnitCreateRequest(BaseModel):
    unit_name: str = Field(..., description="Unit label or number", example="Unit 501")
    floor_number: Optional[int] = Field(None, description="Floor number where the unit is located", example=5)
    floor_area_sqm: Optional[float] = Field(None, description="Floor area in square meters", example=750.0)
    fitout_type: Optional[str] = Field(None, description="Fitout description", example="open plan")
    occupancy_status: str = Field(..., description="Current occupancy_status; 'vacant' or 'occupied'", example="vacant")

class UnitUpdateRequest(BaseModel):
    unit_name: Optional[str] = Field(None, description="Updated unit name or label", example="Suite 501")
    floor_number: Optional[int] = Field(None, description="Updated floor number", example=5)
    floor_area_sqm: Optional[float] = Field(None, description="Updated floor area in sqm", example=760.0)
    fitout_type: Optional[str] = Field(None, description="Updated fitout type", example="spec fitout")
    occupancy_status: Optional[str] = Field(None, description="Updated occupancy status", example="occupied")

class UnitModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unit identifier", example=100)
    property_id: int = Field(..., description="Parent property identifier", example=1)
    unit_name: str = Field(..., description="Unit label or number", example="Unit 501")
    floor_number: Optional[int] = Field(None, description="Floor number", example=5)
    floor_area_sqm: Optional[float] = Field(None, description="Floor area in square meters", example=750.0)
    fitout_type: Optional[str] = Field(None, description="Fitout description", example="open plan")
    occupancy_status: str = Field(..., description="Occupancy status", example="vacant")
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-01T10:10:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-01T10:10:00Z")

class UnitSingleResponse(BaseModel):
    unit: UnitModel = Field(..., description="Unit object", example={})

class UnitListResponse(BaseModel):
    units: List[UnitModel] = Field(..., description="List of units", example=[])

class UnitDeleteResult(BaseModel):
    success: bool = Field(..., description="True if unit was deleted", example=True)
    deleted_unit_id: int = Field(..., description="ID of deleted unit", example=100)

class UnitDeleteResponse(BaseModel):
    result: UnitDeleteResult = Field(..., description="Delete result", example={})

class TenantCreateRequest(BaseModel):
    legal_name: str = Field(..., description="Legal name of the tenant", example="Bluewave Legal Pty Ltd")
    abn: Optional[str] = Field(None, description="Australian Business Number or similar identifier", example="22 345 678 901")
    billing_address: Optional[str] = Field(None, description="Billing address for invoices", example="Level 10, 33 George St, Sydney NSW 2000")
    risk_rating: Optional[str] = Field(None, description="Risk rating: 'low', 'medium', or 'high'", example="medium")
    primary_contact_name: Optional[str] = Field(None, description="Primary contact name", example="Sarah Collins")
    primary_contact_email: Optional[str] = Field(None, description="Primary contact email", example="sarah.collins@bluewavelegal.com")
    primary_contact_phone: Optional[str] = Field(None, description="Primary contact phone number", example="+61 2 9000 1111")

class TenantUpdateRequest(BaseModel):
    legal_name: Optional[str] = Field(None, description="Updated legal name", example="Bluewave Legal Pty Ltd")
    abn: Optional[str] = Field(None, description="Updated ABN", example="22 345 678 901")
    billing_address: Optional[str] = Field(None, description="Updated billing address", example="Level 11, 33 George St, Sydney NSW 2000")
    risk_rating: Optional[str] = Field(None, description="Updated risk rating", example="low")
    primary_contact_name: Optional[str] = Field(None, description="Updated contact name", example="Sarah Collins")
    primary_contact_email: Optional[str] = Field(None, description="Updated contact email", example="legal.ap@bluewavelegal.com")
    primary_contact_phone: Optional[str] = Field(None, description="Updated contact phone", example="+61 2 9000 2222")

class TenantModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Tenant identifier", example=200)
    legal_name: str = Field(..., description="Legal name", example="Bluewave Legal Pty Ltd")
    abn: Optional[str] = Field(None, description="Business number", example="22 345 678 901")
    billing_address: Optional[str] = Field(None, description="Billing address", example="Level 10, 33 George St, Sydney NSW 2000")
    risk_rating: Optional[str] = Field(None, description="Risk rating", example="medium")
    primary_contact_name: Optional[str] = Field(None, description="Contact name", example="Sarah Collins")
    primary_contact_email: Optional[str] = Field(None, description="Contact email", example="sarah.collins@bluewavelegal.com")
    primary_contact_phone: Optional[str] = Field(None, description="Contact phone number", example="+61 2 9000 1111")
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-01T11:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-01T11:00:00Z")

class TenantSingleResponse(BaseModel):
    tenant: TenantModel = Field(..., description="Tenant object", example={})

class TenantListResponse(BaseModel):
    tenants: List[TenantModel] = Field(..., description="List of tenants", example=[])

class TenantDeleteResult(BaseModel):
    success: bool = Field(..., description="True if tenant was deleted", example=True)
    deleted_tenant_id: int = Field(..., description="ID of deleted tenant", example=200)

class TenantDeleteResponse(BaseModel):
    result: TenantDeleteResult = Field(..., description="Delete result", example={})

class LeaseCreateRequest(BaseModel):
    tenant_id: int = Field(..., description="Tenant identifier for this lease", example=200)
    unit_id: int = Field(..., description="Unit identifier for this lease", example=100)
    lease_start_date: str = Field(..., description="Lease start date (YYYY-MM-DD)", example="2025-01-01")
    lease_end_date: str = Field(..., description="Lease end date (YYYY-MM-DD)", example="2030-12-31")
    rent_type: str = Field(..., description="Rent type: 'indexed' or 'turnover'", example="indexed")
    security_deposit: float = Field(..., description="Security deposit amount", example=75000.0)
    break_options: Optional[str] = Field(None, description="Break clause options text", example="Tenant break at year 5 with 6 months notice")
    status: Optional[str] = Field(None, description="Lease status; defaults to 'active'", example="active")

class LeaseUpdateRequest(BaseModel):
    lease_start_date: Optional[str] = Field(None, description="Updated lease start date (YYYY-MM-DD)", example="2025-01-01")
    lease_end_date: Optional[str] = Field(None, description="Updated lease end date (YYYY-MM-DD)", example="2031-12-31")
    rent_type: Optional[str] = Field(None, description="Updated rent type", example="turnover")
    security_deposit: Optional[float] = Field(None, description="Updated security deposit", example=80000.0)
    break_options: Optional[str] = Field(None, description="Updated break options text", example="Tenant break at year 3 with 6 months notice")
    status: Optional[str] = Field(None, description="Updated status ('active','terminated','expired','draft')", example="active")

class LeaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Lease identifier", example=300)
    tenant_id: int = Field(..., description="Tenant identifier", example=200)
    unit_id: int = Field(..., description="Unit identifier", example=100)
    lease_start_date: date = Field(..., description="Start date", example="2025-01-01")
    lease_end_date: date = Field(..., description="End date", example="2030-12-31")
    rent_type: str = Field(..., description="Rent type", example="indexed")
    security_deposit: float = Field(..., description="Security deposit amount", example=75000.0)
    break_options: Optional[str] = Field(None, description="Break options text", example="Tenant break at year 5 with 6 months notice")
    status: str = Field(..., description="Lease status", example="active")
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-01T11:30:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-01T11:30:00Z")

class LeaseSingleResponse(BaseModel):
    lease: LeaseModel = Field(..., description="Lease object", example={})

class LeaseListResponse(BaseModel):
    leases: List[LeaseModel] = Field(..., description="List of leases", example=[])

class LeaseDeleteResult(BaseModel):
    success: bool = Field(..., description="True if lease was deleted", example=True)
    deleted_lease_id: int = Field(..., description="ID of deleted lease", example=300)

class LeaseDeleteResponse(BaseModel):
    result: LeaseDeleteResult = Field(..., description="Delete result", example={})

class RentScheduleCreateRequest(BaseModel):
    lease_id: int = Field(..., description="Lease identifier this charge relates to", example=300)
    charge_type: str = Field(..., description="Charge type", example="base_rent")
    period_start: str = Field(..., description="Start of rental period (YYYY-MM-DD)", example="2025-01-01")
    period_end: str = Field(..., description="End of rental period (YYYY-MM-DD)", example="2025-01-31")
    due_date: str = Field(..., description="Due date for payment (YYYY-MM-DD)", example="2025-01-01")
    amount: float = Field(..., description="Charge amount", example=25000.0)
    currency: Optional[str] = Field(None, description="Currency code; defaults to 'AUD'", example="AUD")
    is_generated: Optional[int] = Field(None, description="1 if generated by system, 0 if manual", example=1)
    is_revised: Optional[int] = Field(None, description="Flag indicating revised schedule", example=0)
    revision_note: Optional[str] = Field(None, description="Explanation for revision if applicable", example="Initial schedule load")

class RentScheduleUpdateRequest(BaseModel):
    charge_type: Optional[str] = Field(None, description="Updated charge type", example="base_rent")
    period_start: Optional[str] = Field(None, description="Updated period_start (YYYY-MM-DD)", example="2025-01-01")
    period_end: Optional[str] = Field(None, description="Updated period_end (YYYY-MM-DD)", example="2025-01-31")
    due_date: Optional[str] = Field(None, description="Updated due_date (YYYY-MM-DD)", example="2025-01-01")
    amount: Optional[float] = Field(None, description="Updated amount", example=25875.0)
    currency: Optional[str] = Field(None, description="Updated currency", example="AUD")
    is_generated: Optional[int] = Field(None, description="Updated generated flag", example=1)
    is_revised: Optional[int] = Field(None, description="Updated revised flag", example=1)
    revision_note: Optional[str] = Field(None, description="Updated revision note", example="Indexation applied 2026-01-01")

class RentScheduleModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Rent schedule identifier", example=400)
    lease_id: int = Field(..., description="Lease identifier", example=300)
    charge_type: str = Field(..., description="Charge type", example="base_rent")
    period_start: date = Field(..., description="Period start date", example="2025-01-01")
    period_end: date = Field(..., description="Period end date", example="2025-01-31")
    due_date: date = Field(..., description="Due date", example="2025-01-01")
    amount: float = Field(..., description="Charge amount", example=25000.0)
    currency: str = Field(..., description="Currency code", example="AUD")
    is_generated: int = Field(..., description="Generated flag", example=1)
    is_revised: int = Field(..., description="Revised flag", example=0)
    revision_note: Optional[str] = Field(None, description="Revision note if any", example="Initial schedule load")
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-01T12:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-01T12:00:00Z")

class RentScheduleSingleResponse(BaseModel):
    rent_schedule: RentScheduleModel = Field(..., description="Rent schedule", example={})

class RentScheduleListResponse(BaseModel):
    rent_schedules: List[RentScheduleModel] = Field(..., description="List of rent schedules", example=[])

class RentScheduleBulkCreateItem(BaseModel):
    lease_id: int = Field(..., description="Lease identifier", example=300)
    charge_type: str = Field(..., description="Charge type", example="base_rent")
    period_start: str = Field(..., description="Period start", example="2025-01-01")
    period_end: str = Field(..., description="Period end", example="2025-01-31")
    due_date: str = Field(..., description="Due date", example="2025-01-01")
    amount: float = Field(..., description="Amount", example=25000.0)
    currency: Optional[str] = Field(None, description="Currency code", example="AUD")
    is_generated: Optional[int] = Field(None, description="Generated flag", example=1)
    is_revised: Optional[int] = Field(None, description="Revised flag", example=0)
    revision_note: Optional[str] = Field(None, description="Revision note", example="Initial 2025 rent")

class RentScheduleBulkCreateRequest(BaseModel):
    items: List[RentScheduleBulkCreateItem] = Field(..., description="Array of rent schedule entries to create", example=[])

class RentScheduleBulkCreateResponse(BaseModel):
    rent_schedules: List[RentScheduleModel] = Field(..., description="Created rent schedules", example=[])

class RentScheduleDeleteResult(BaseModel):
    success: bool = Field(..., description="True if schedule was deleted", example=True)
    deleted_rent_schedule_id: int = Field(..., description="Deleted schedule id", example=400)

class RentScheduleDeleteResponse(BaseModel):
    result: RentScheduleDeleteResult = Field(..., description="Delete result", example={})

class InvoiceCreateRequest(BaseModel):
    tenant_id: int = Field(..., description="Tenant identifier", example=200)
    lease_id: int = Field(..., description="Lease identifier", example=300)
    rent_schedule_id: Optional[int] = Field(None, description="Linked rent schedule id if applicable", example=400)
    invoice_number: Optional[str] = Field(None, description="External invoice number, if any", example="INV-2025-0001")
    charge_type: str = Field(..., description="Charge type for this invoice", example="base_rent")
    description: Optional[str] = Field(None, description="Description line for the invoice", example="February 2025 base rent")
    issue_date: str = Field(..., description="Invoice issue date (YYYY-MM-DD)", example="2025-02-01")
    due_date: str = Field(..., description="Invoice due date (YYYY-MM-DD)", example="2025-02-01")
    amount: float = Field(..., description="Invoice amount", example=25000.0)
    amount_paid: Optional[float] = Field(None, description="Initial amount already paid, usually 0", example=0.0)
    allocation_status: Optional[str] = Field(None, description="Allocation status; defaults to 'unallocated'", example="unallocated")
    status: Optional[str] = Field(None, description="Payment status; defaults to 'unpaid'", example="unpaid")

class InvoiceUpdateRequest(BaseModel):
    invoice_number: Optional[str] = Field(None, description="Updated invoice number", example="INV-2025-0001-REV1")
    description: Optional[str] = Field(None, description="Updated description", example="February 2025 base rent (revised)")
    issue_date: Optional[str] = Field(None, description="Updated issue date", example="2025-02-02")
    due_date: Optional[str] = Field(None, description="Updated due date", example="2025-02-05")
    amount: Optional[float] = Field(None, description="Updated amount", example=25500.0)
    amount_paid: Optional[float] = Field(None, description="Updated amount paid", example=20000.0)
    allocation_status: Optional[str] = Field(None, description="Updated allocation status", example="partially_allocated")
    status: Optional[str] = Field(None, description="Updated payment status", example="unpaid")

class InvoiceModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Invoice identifier", example=500)
    tenant_id: int = Field(..., description="Tenant identifier", example=200)
    lease_id: int = Field(..., description="Lease identifier", example=300)
    rent_schedule_id: Optional[int] = Field(None, description="Linked rent schedule identifier", example=400)
    invoice_number: Optional[str] = Field(None, description="Invoice number", example="INV-2025-0001")
    charge_type: str = Field(..., description="Charge type", example="base_rent")
    description: Optional[str] = Field(None, description="Description", example="February 2025 base rent")
    issue_date: date = Field(..., description="Issue date", example="2025-02-01")
    due_date: date = Field(..., description="Due date", example="2025-02-01")
    amount: float = Field(..., description="Invoice amount", example=25000.0)
    amount_paid: float = Field(..., description="Amount paid so far", example=0.0)
    allocation_status: str = Field(..., description="Allocation status", example="unallocated")
    status: str = Field(..., description="Invoice status", example="unpaid")
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-02-01T09:00:00Z")
    updated_at: datetime = Field(..., description="Update timestamp", example="2025-02-01T09:00:00Z")

class InvoiceSingleResponse(BaseModel):
    invoice: InvoiceModel = Field(..., description="Invoice object", example={})

class InvoiceListResponse(BaseModel):
    invoices: List[InvoiceModel] = Field(..., description="List of invoices", example=[])

class InvoiceBulkCreateItem(BaseModel):
    tenant_id: int = Field(..., description="Tenant identifier", example=200)
    lease_id: int = Field(..., description="Lease identifier", example=300)
    rent_schedule_id: Optional[int] = Field(None, description="Linked rent schedule id", example=400)
    invoice_number: Optional[str] = Field(None, description="Invoice number", example="INV-2025-0002")
    charge_type: str = Field(..., description="Charge type", example="service_charge")
    description: Optional[str] = Field(None, description="Description", example="February 2025 service charge")
    issue_date: str = Field(..., description="Issue date", example="2025-02-01")
    due_date: str = Field(..., description="Due date", example="2025-02-01")
    amount: float = Field(..., description="Amount", example=4500.0)
    amount_paid: Optional[float] = Field(None, description="Amount paid", example=0.0)
    allocation_status: Optional[str] = Field(None, description="Allocation status", example="unallocated")
    status: Optional[str] = Field(None, description="Invoice status", example="unpaid")

class InvoiceBulkCreateRequest(BaseModel):
    items: List[InvoiceBulkCreateItem] = Field(..., description="Array of invoices to create", example=[])

class InvoiceBulkCreateResponse(BaseModel):
    invoices: List[InvoiceModel] = Field(..., description="Created invoices", example=[])

class InvoiceDeleteResult(BaseModel):
    success: bool = Field(..., description="True if invoice was deleted", example=True)
    deleted_invoice_id: int = Field(..., description="Deleted invoice id", example=500)

class InvoiceDeleteResponse(BaseModel):
    result: InvoiceDeleteResult = Field(..., description="Delete result", example={})

class IndexationEventCreateRequest(BaseModel):
    lease_id: int = Field(..., description="Lease identifier this indexation applies to", example=300)
    effective_date: str = Field(..., description="Indexation effective date (YYYY-MM-DD)", example="2026-01-01")
    index_rate: float = Field(..., description="Indexation rate as percentage", example=3.5)
    description: Optional[str] = Field(None, description="Optional description or reference", example="Annual CPI indexation 2026")
    applied: Optional[int] = Field(None, description="0 if not applied yet, 1 if already applied", example=0)

class IndexationEventUpdateRequest(BaseModel):
    effective_date: Optional[str] = Field(None, description="Updated effective date (YYYY-MM-DD)", example="2026-01-01")
    index_rate: Optional[float] = Field(None, description="Updated indexation rate", example=3.5)
    description: Optional[str] = Field(None, description="Updated description", example="Updated indexation per CPI release")
    applied: Optional[int] = Field(None, description="Updated applied flag (0 or 1)", example=1)

class IndexationEventModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Indexation event identifier", example=600)
    lease_id: int = Field(..., description="Lease identifier", example=300)
    effective_date: date = Field(..., description="Effective date", example="2026-01-01")
    index_rate: float = Field(..., description="Indexation rate (%)", example=3.5)
    description: Optional[str] = Field(None, description="Description", example="Annual CPI indexation 2026")
    applied: int = Field(..., description="Applied flag", example=0)
    created_at: datetime = Field(..., description="Created timestamp", example="2025-12-01T09:00:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-12-01T09:00:00Z")

class IndexationEventSingleResponse(BaseModel):
    indexation_event: IndexationEventModel = Field(..., description="Indexation event", example={})

class IndexationEventListResponse(BaseModel):
    indexation_events: List[IndexationEventModel] = Field(..., description="List of indexation events", example=[])

class IndexationEventDeleteResult(BaseModel):
    success: bool = Field(..., description="True if event was deleted", example=True)
    deleted_indexation_event_id: int = Field(..., description="Deleted event id", example=600)

class IndexationEventDeleteResponse(BaseModel):
    result: IndexationEventDeleteResult = Field(..., description="Delete result", example={})

class ApplyIndexationRequest(BaseModel):
    indexation_event_id: int = Field(..., description="Indexation event id to apply", example=600)
    apply_from_due_date: Optional[str] = Field(None, description="Override date from which future base_rent schedule entries should be indexed", example="2026-01-01")

class ApplyIndexationAllocationResult(BaseModel):
    indexation_event_id: int = Field(..., description="Applied indexation event id", example=600)
    lease_id: int = Field(..., description="Lease id to which indexation was applied", example=300)
    updated_rent_schedule_ids: List[int] = Field(..., description="List of rent schedule ids whose amounts were updated", example=[410, 411, 412])
    applied_index_rate: float = Field(..., description="Indexation rate (%) used", example=3.5)

class ApplyIndexationResponse(BaseModel):
    result: ApplyIndexationAllocationResult = Field(..., description="Indexation apply result", example={})

class PaymentCreateRequest(BaseModel):
    tenant_id: int = Field(..., description="Tenant who made the payment", example=200)
    received_date: str = Field(..., description="Date payment was received (YYYY-MM-DD)", example="2025-02-05")
    amount: float = Field(..., description="Payment amount", example=32000.0)
    payment_method: str = Field(..., description="Payment method description", example="bank_transfer")
    reference: Optional[str] = Field(None, description="Reference text", example="Ref 123456 Feb Rent")

class PaymentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Payment identifier", example=700)
    tenant_id: int = Field(..., description="Tenant identifier", example=200)
    received_date: date = Field(..., description="Received date", example="2025-02-05")
    amount: float = Field(..., description="Payment amount", example=32000.0)
    payment_method: str = Field(..., description="Payment method", example="bank_transfer")
    reference: Optional[str] = Field(None, description="Payment reference", example="Ref 123456 Feb Rent")
    created_at: datetime = Field(..., description="Created timestamp", example="2025-02-05T10:00:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-02-05T10:00:00Z")

class PaymentSingleResponse(BaseModel):
    payment: PaymentModel = Field(..., description="Payment object", example={})

class PaymentListResponse(BaseModel):
    payments: List[PaymentModel] = Field(..., description="List of payments", example=[])

class PaymentDeleteResult(BaseModel):
    success: bool = Field(..., description="True if payment was deleted", example=True)
    deleted_payment_id: int = Field(..., description="Deleted payment id", example=700)

class PaymentDeleteResponse(BaseModel):
    result: PaymentDeleteResult = Field(..., description="Delete result", example={})

class PaymentAllocationCreateRequest(BaseModel):
    payment_id: int = Field(..., description="Payment identifier to allocate from", example=700)
    invoice_id: int = Field(..., description="Invoice identifier to allocate to", example=500)
    allocated_amount: float = Field(..., description="Amount of payment allocated to this invoice", example=25000.0)

class PaymentAllocationModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Payment allocation identifier", example=800)
    payment_id: int = Field(..., description="Payment identifier", example=700)
    invoice_id: int = Field(..., description="Invoice identifier", example=500)
    allocated_amount: float = Field(..., description="Allocated amount", example=25000.0)
    created_at: datetime = Field(..., description="Created timestamp", example="2025-02-05T10:10:00Z")

class PaymentAllocationSingleResponse(BaseModel):
    payment_allocation: PaymentAllocationModel = Field(..., description="Payment allocation", example={})

class PaymentAllocationListResponse(BaseModel):
    payment_allocations: List[PaymentAllocationModel] = Field(..., description="List of payment allocations", example=[])

class PaymentAllocationDeleteResult(BaseModel):
    success: bool = Field(..., description="True if allocation was deleted", example=True)
    deleted_allocation_id: int = Field(..., description="Deleted allocation id", example=800)

class PaymentAllocationDeleteResponse(BaseModel):
    result: PaymentAllocationDeleteResult = Field(..., description="Delete result", example={})

class AutoAllocateRequest(BaseModel):
    allocation_order: Optional[List[str]] = Field(None, description="Preferred charge_type allocation order", example=["base_rent", "service_charge", "parking"])
    up_to_due_date: Optional[str] = Field(None, description="Only allocate to invoices with due_date <= this date", example="2025-02-28")

class AutoAllocateInvoiceAllocation(BaseModel):
    invoice_id: int = Field(..., description="Invoice id that received allocation", example=500)
    allocated_amount: float = Field(..., description="Allocated amount to this invoice", example=25000.0)
    allocation_id: int = Field(..., description="Created allocation id", example=800)
    allocation_status: str = Field(..., description="Resulting invoice allocation_status", example="fully_allocated")
    invoice_status: str = Field(..., description="Resulting invoice status", example="paid")

class AutoAllocateResult(BaseModel):
    payment_id: int = Field(..., description="Allocated payment id", example=700)
    total_allocated: float = Field(..., description="Total amount allocated", example=32000.0)
    allocations: List[AutoAllocateInvoiceAllocation] = Field(..., description="Created allocations mapping payment to invoices", example=[])

class AutoAllocateResponse(BaseModel):
    result: AutoAllocateResult = Field(..., description="Auto allocation result", example={})

class VendorCreateRequest(BaseModel):
    name: str = Field(..., description="Vendor business name", example="ChillTech HVAC Services")
    contact_name: Optional[str] = Field(None, description="Primary contact name", example="John Doe")
    contact_email: Optional[str] = Field(None, description="Primary contact email", example="service@chilltech.com")
    contact_phone: Optional[str] = Field(None, description="Primary contact phone", example="+61 2 9555 1111")

class VendorUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Updated vendor name", example="ChillTech HVAC & Mechanical")
    contact_name: Optional[str] = Field(None, description="Updated contact name", example="Jane Smith")
    contact_email: Optional[str] = Field(None, description="Updated contact email", example="support@chilltech.com")
    contact_phone: Optional[str] = Field(None, description="Updated contact phone", example="+61 2 9555 2222")

class VendorModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Vendor identifier", example=900)
    name: str = Field(..., description="Vendor name", example="ChillTech HVAC Services")
    contact_name: Optional[str] = Field(None, description="Contact name", example="John Doe")
    contact_email: Optional[str] = Field(None, description="Contact email", example="service@chilltech.com")
    contact_phone: Optional[str] = Field(None, description="Contact phone", example="+61 2 9555 1111")
    created_at: datetime = Field(..., description="Created timestamp", example="2025-01-01T09:00:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-01-01T09:00:00Z")

class VendorSingleResponse(BaseModel):
    vendor: VendorModel = Field(..., description="Vendor object", example={})

class VendorListResponse(BaseModel):
    vendors: List[VendorModel] = Field(..., description="List of vendors", example=[])

class VendorDeleteResult(BaseModel):
    success: bool = Field(..., description="True if vendor was deleted", example=True)
    deleted_vendor_id: int = Field(..., description="Deleted vendor id", example=900)

class VendorDeleteResponse(BaseModel):
    result: VendorDeleteResult = Field(..., description="Delete result", example={})

class MaintenanceRequestCreateRequest(BaseModel):
    property_id: int = Field(..., description="Property where issue occurs", example=1)
    unit_id: Optional[int] = Field(None, description="Specific unit related to the issue, if any", example=100)
    tenant_id: Optional[int] = Field(None, description="Tenant reporting the issue, if applicable", example=200)
    priority_level: str = Field(..., description="Priority: 'low','medium','high','urgent'", example="high")
    issue_category: str = Field(..., description="Issue category", example="air_conditioning")
    description: str = Field(..., description="Detailed description of issue", example="No cooling on the east side of the floor since yesterday")
    photos_metadata: Optional[str] = Field(None, description="JSON-encoded metadata about related photos", example='["ac_vent_1.jpg","thermostat_error_code.png"]')
    preferred_access_times: Optional[str] = Field(None, description="Preferred times for access", example="Weekdays 7-9am")
    status: str = Field(..., description="Status: 'open','in_progress','completed','cancelled'", example="open")
    vendor_id: Optional[int] = Field(None, description="Assigned vendor id if already known", example=900)
    resolution_notes: Optional[str] = Field(None, description="Notes about resolution or actions taken", example="Technician visit scheduled for 2025-01-15")
    requested_date: Optional[str] = Field(None, description="Requested date; defaults to current date if omitted", example="2025-01-10")

class MaintenanceRequestUpdateRequest(BaseModel):
    priority_level: Optional[str] = Field(None, description="Updated priority level", example="urgent")
    issue_category: Optional[str] = Field(None, description="Updated category", example="air_conditioning")
    description: Optional[str] = Field(None, description="Updated description", example="No cooling in east wing; west wing OK")
    photos_metadata: Optional[str] = Field(None, description="Updated JSON photos metadata", example='["ac_vent_1.jpg","ac_vent_2.jpg"]')
    preferred_access_times: Optional[str] = Field(None, description="Updated access times", example="Weekdays 6-9am")
    status: Optional[str] = Field(None, description="Updated status", example="in_progress")
    vendor_id: Optional[int] = Field(None, description="Updated assigned vendor id", example=900)
    resolution_notes: Optional[str] = Field(None, description="Updated resolution notes", example="Technician visit scheduled for 2025-01-15")

class MaintenanceRequestModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Maintenance request identifier", example=1000)
    property_id: int = Field(..., description="Property identifier", example=1)
    unit_id: Optional[int] = Field(None, description="Unit identifier", example=100)
    tenant_id: Optional[int] = Field(None, description="Tenant identifier", example=200)
    priority_level: str = Field(..., description="Priority level", example="high")
    issue_category: str = Field(..., description="Issue category", example="air_conditioning")
    description: str = Field(..., description="Issue description", example="No cooling on the east side of the floor since yesterday")
    photos_metadata: Optional[str] = Field(None, description="JSON encoded photos metadata", example='["ac_vent_1.jpg","thermostat_error_code.png"]')
    preferred_access_times: Optional[str] = Field(None, description="Preferred access times", example="Weekdays 7-9am")
    status: str = Field(..., description="Request status", example="open")
    vendor_id: Optional[int] = Field(None, description="Assigned vendor identifier", example=900)
    resolution_notes: Optional[str] = Field(None, description="Resolution notes", example="Technician visit scheduled for 2025-01-15")
    requested_date: date = Field(..., description="Date the request was made", example="2025-01-10")
    created_at: datetime = Field(..., description="Created timestamp", example="2025-01-10T09:00:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-01-10T09:00:00Z")

class MaintenanceRequestSingleResponse(BaseModel):
    maintenance_request: MaintenanceRequestModel = Field(..., description="Maintenance request", example={})

class MaintenanceRequestListResponse(BaseModel):
    maintenance_requests: List[MaintenanceRequestModel] = Field(..., description="List of maintenance requests", example=[])

class MaintenanceRequestDeleteResult(BaseModel):
    success: bool = Field(..., description="True if request was deleted", example=True)
    deleted_request_id: int = Field(..., description="Deleted request id", example=1000)

class MaintenanceRequestDeleteResponse(BaseModel):
    result: MaintenanceRequestDeleteResult = Field(..., description="Delete result", example={})

class InspectionCreateRequest(BaseModel):
    property_id: int = Field(..., description="Property identifier for the inspection", example=1)
    inspection_type: str = Field(..., description="Description of inspection type", example="Fire safety inspection")
    scheduled_date: str = Field(..., description="Scheduled date for inspection (YYYY-MM-DD)", example="2025-02-10")
    outcome: Optional[str] = Field(None, description="Inspection outcome: 'pass','fail','pending'", example="pass")
    follow_up_actions: Optional[str] = Field(None, description="Follow up actions required", example="Next annual check due Feb 2026")

class InspectionUpdateRequest(BaseModel):
    inspection_type: Optional[str] = Field(None, description="Updated inspection type", example="Lift compliance inspection")
    scheduled_date: Optional[str] = Field(None, description="Updated scheduled date (YYYY-MM-DD)", example="2025-02-15")
    outcome: Optional[str] = Field(None, description="Updated outcome", example="fail")
    follow_up_actions: Optional[str] = Field(None, description="Updated follow up actions", example="Replace safety sensor on Lift 3 by 2025-03-01")

class InspectionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Inspection identifier", example=1100)
    property_id: int = Field(..., description="Property identifier", example=1)
    inspection_type: str = Field(..., description="Type of inspection", example="Fire safety inspection")
    scheduled_date: date = Field(..., description="Scheduled date", example="2025-02-10")
    outcome: Optional[str] = Field(None, description="Inspection outcome", example="pass")
    follow_up_actions: Optional[str] = Field(None, description="Follow up actions", example="Next annual check due Feb 2026")
    created_at: datetime = Field(..., description="Created timestamp", example="2025-01-15T09:00:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-01-15T09:00:00Z")

class InspectionSingleResponse(BaseModel):
    inspection: InspectionModel = Field(..., description="Inspection object", example={})

class InspectionListResponse(BaseModel):
    inspections: List[InspectionModel] = Field(..., description="List of inspections", example=[])

class InspectionDeleteResult(BaseModel):
    success: bool = Field(..., description="True if inspection was deleted", example=True)
    deleted_inspection_id: int = Field(..., description="Deleted inspection id", example=1101)

class InspectionDeleteResponse(BaseModel):
    result: InspectionDeleteResult = Field(..., description="Delete result", example={})

class FailedInspectionReportItem(BaseModel):
    inspection_id: int = Field(..., description="Inspection identifier", example=1101)
    property_id: int = Field(..., description="Property identifier", example=1)
    property_name: Optional[str] = Field(None, description="Name of property if available", example="120 Market Street")
    inspection_type: str = Field(..., description="Inspection type", example="Lift compliance inspection")
    scheduled_date: date = Field(..., description="Scheduled date", example="2025-02-15")
    outcome: str = Field(..., description="Outcome, always 'fail'", example="fail")
    follow_up_actions: Optional[str] = Field(None, description="Required follow up actions", example="Replace safety sensor on Lift 3 by 2025-03-01")

class FailedInspectionReportResponse(BaseModel):
    failed_inspections: List[FailedInspectionReportItem] = Field(..., description="List of failed inspections with follow-ups", example=[])

class ArrearsTenantItem(BaseModel):
    tenant_id: int = Field(..., description="Tenant identifier", example=200)
    tenant_legal_name: str = Field(..., description="Tenant legal name", example="Bluewave Legal Pty Ltd")
    total_overdue_amount: float = Field(..., description="Total overdue amount for this tenant as of as_of_date", example=12500.0)
    number_of_unpaid_invoices: int = Field(..., description="Count of unpaid invoices with due_date <= as_of_date", example=3)
    oldest_overdue_invoice_due_date: Optional[date] = Field(None, description="Due date of the oldest overdue invoice for this tenant; null if none", example="2025-02-01")

class ArrearsReportResponse(BaseModel):
    property_id: int = Field(..., description="Property identifier used for the report", example=1)
    property_name: Optional[str] = Field(None, description="Property name", example="120 Market Street")
    as_of_date: date = Field(..., description="Report as-of date", example="2025-03-31")
    tenants: List[ArrearsTenantItem] = Field(..., description="Arrears summary grouped by tenant", example=[])

class RecalculateRentScheduleRequest(BaseModel):
    recalculate_from_date: str = Field(..., description="Date from which future rent_schedules should be updated (YYYY-MM-DD)", example="2025-01-01")
    new_monthly_base_rent: Optional[float] = Field(None, description="New monthly base rent amount to use", example=45000.0)
    replace_turnover_with_annual_indexed: Optional[bool] = Field(None, description="If true, delete future turnover_top_up entries and create indexed_annual entries once per year", example=True)
    annual_indexed_due_day: Optional[str] = Field(None, description="Due date (MM-DD) for new annual indexed entries", example="06-30")
    annual_indexed_start_year: Optional[int] = Field(None, description="Year from which to start new annual indexed entries", example=2025)
    note_for_revised_entries: Optional[str] = Field(None, description="Revision_note to store on revised or new entries", example="Revised lease terms effective 2025-01-01")

class RecalculateRentScheduleResult(BaseModel):
    lease_id: int = Field(..., description="Lease identifier that was recalculated", example=350)
    deleted_rent_schedule_ids: List[int] = Field(..., description="IDs of rent_schedules deleted due to recalculation", example=[9001, 9002, 9003])
    updated_rent_schedule_ids: List[int] = Field(..., description="IDs of existing rent_schedules updated", example=[9010, 9011, 9012])
    created_rent_schedule_ids: List[int] = Field(..., description="IDs of newly created rent_schedules entries", example=[9020, 9021])

class RecalculateRentScheduleResponse(BaseModel):
    result: RecalculateRentScheduleResult = Field(..., description="Recalculation result", example={})

@app.get(
    "/api/users/me",
    response_model=UserMeResponse,
    summary="Get current authenticated user",
    description="Return the current authenticated user (always user_id=1) for context.",
    tags=["users"],
    operation_id="get_current_user",
)
async def get_current_user() -> UserMeResponse:
    session = SessionLocal()
    user = session.query(User).filter(User.id == 1).first()
    if user is None:
        user = User(id=1, username="admin", email="admin@example.com", full_name="LeaseTrack Admin", created_at=now_utc(), updated_at=now_utc())
        session.add(user)
        session.commit()
        session.refresh(user)
    session.close()
    return UserMeResponse(user=UserModel.model_validate(user))

@app.post(
    "/api/properties",
    response_model=PropertySingleResponse,
    summary="Create a new property",
    description="Create a new office or industrial property; created_by is set to current user (id=1).",
    tags=["properties"],
    operation_id="create_property",
)
async def create_property(property_in: PropertyCreateRequest = Body(...)) -> PropertySingleResponse:
    session = SessionLocal()
    prop = Property(
        name=property_in.name,
        address_line=property_in.address_line,
        city=property_in.city,
        state=property_in.state,
        postal_code=property_in.postal_code,
        country=property_in.country,
        property_type=property_in.property_type,
        created_by=1,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    session.add(prop)
    session.commit()
    session.refresh(prop)
    session.close()
    return PropertySingleResponse(property=PropertyModel.model_validate(prop))

@app.get(
    "/api/properties",
    response_model=PropertyListResponse,
    summary="List properties with optional filters",
    description="Retrieve a list of properties created by current user, optionally filtered by type or city.",
    tags=["properties"],
    operation_id="list_properties",
)
async def list_properties(
    property_type: Optional[str] = Query(None, description="Filter by property_type", example="office"),
    city: Optional[str] = Query(None, description="Filter by city name", example="Sydney"),
    address_search: Optional[str] = Query(None, description="Case-insensitive partial search on address_line", example="Market"),
    limit: Optional[int] = Query(50, description="Maximum number of records to return", example=50),
    offset: Optional[int] = Query(0, description="Number of records to skip for pagination", example=0),
) -> PropertyListResponse:
    session = SessionLocal()
    q = session.query(Property).filter(Property.created_by == 1)
    if property_type is not None:
        q = q.filter(Property.property_type == property_type)
    if city is not None:
        q = q.filter(Property.city == city)
    if address_search is not None:
        pattern = f"%{address_search}%"
        q = q.filter(Property.address_line.ilike(pattern))
    props = q.offset(offset).limit(limit).all()
    session.close()
    return PropertyListResponse(properties=[PropertyModel.model_validate(p) for p in props])

@app.get(
    "/api/properties/{property_id}",
    response_model=PropertySingleResponse,
    summary="Get a property by ID",
    description="Retrieve a single property by id ensuring it was created by the current user.",
    tags=["properties"],
    operation_id="get_property_by_id",
)
async def get_property_by_id(
    property_id: int = Path(..., description="Property identifier", example=1)
) -> PropertySingleResponse:
    session = SessionLocal()
    prop = session.query(Property).filter(Property.id == property_id, Property.created_by == 1).first()
    session.close()
    if prop is None:
        return PropertySingleResponse(property=PropertyModel.model_validate(Property(id=0, name=None, address_line="", city=None, state=None, postal_code=None, country=None, property_type="office", created_by=1, created_at=now_utc(), updated_at=now_utc())))
    return PropertySingleResponse(property=PropertyModel.model_validate(prop))

@app.patch(
    "/api/properties/{property_id}",
    response_model=PropertySingleResponse,
    summary="Update a property",
    description="Partially update property fields such as name, address, or property_type.",
    tags=["properties"],
    operation_id="update_property",
)
async def update_property(
    property_id: int = Path(..., description="Property identifier to update", example=1),
    property_in: PropertyUpdateRequest = Body(...),
) -> PropertySingleResponse:
    session = SessionLocal()
    prop = session.query(Property).filter(Property.id == property_id, Property.created_by == 1).first()
    if prop is None:
        session.close()
        return PropertySingleResponse(property=PropertyModel.model_validate(Property(id=0, name=None, address_line="", city=None, state=None, postal_code=None, country=None, property_type="office", created_by=1, created_at=now_utc(), updated_at=now_utc())))
    if property_in.name is not None:
        prop.name = property_in.name
    if property_in.address_line is not None:
        prop.address_line = property_in.address_line
    if property_in.city is not None:
        prop.city = property_in.city
    if property_in.state is not None:
        prop.state = property_in.state
    if property_in.postal_code is not None:
        prop.postal_code = property_in.postal_code
    if property_in.country is not None:
        prop.country = property_in.country
    if property_in.property_type is not None:
        prop.property_type = property_in.property_type
    prop.updated_at = now_utc()
    session.commit()
    session.refresh(prop)
    session.close()
    return PropertySingleResponse(property=PropertyModel.model_validate(prop))

@app.delete(
    "/api/properties/{property_id}",
    response_model=PropertyDeleteResponse,
    summary="Delete a property",
    description="Delete a property by ID; related units, features, and maintenance requests cascade.",
    tags=["properties"],
    operation_id="delete_property",
)
async def delete_property(
    property_id: int = Path(..., description="Property identifier to delete", example=1)
) -> PropertyDeleteResponse:
    session = SessionLocal()
    prop = session.query(Property).filter(Property.id == property_id, Property.created_by == 1).first()
    success = False
    if prop is not None:
        session.delete(prop)
        session.commit()
        success = True
    session.close()
    return PropertyDeleteResponse(result=PropertyDeleteResult(success=success, deleted_property_id=property_id))

@app.post(
    "/api/properties/{property_id}/features",
    response_model=PropertyFeatureSingleResponse,
    summary="Add a feature to a property",
    description="Create a new property_features row for the specified property.",
    tags=["property_features"],
    operation_id="add_property_feature",
)
async def add_property_feature(
    property_id: int = Path(..., description="Property ID to attach the feature to", example=1),
    feature_in: PropertyFeatureCreateRequest = Body(...),
) -> PropertyFeatureSingleResponse:
    session = SessionLocal()
    feat = PropertyFeature(property_id=property_id, feature=feature_in.feature, created_at=now_utc())
    session.add(feat)
    session.commit()
    session.refresh(feat)
    session.close()
    return PropertyFeatureSingleResponse(feature=PropertyFeatureModel.model_validate(feat))

@app.get(
    "/api/properties/{property_id}/features",
    response_model=PropertyFeatureListResponse,
    summary="List features for a property",
    description="Retrieve all property_features entries for a given property_id.",
    tags=["property_features"],
    operation_id="list_property_features",
)
async def list_property_features(
    property_id: int = Path(..., description="Property identifier", example=1)
) -> PropertyFeatureListResponse:
    session = SessionLocal()
    feats = session.query(PropertyFeature).filter(PropertyFeature.property_id == property_id).all()
    session.close()
    return PropertyFeatureListResponse(features=[PropertyFeatureModel.model_validate(f) for f in feats])

@app.delete(
    "/api/property_features/{feature_id}",
    response_model=PropertyFeatureDeleteResponse,
    summary="Delete a property feature",
    description="Delete a single property_features record by ID.",
    tags=["property_features"],
    operation_id="delete_property_feature",
)
async def delete_property_feature(
    feature_id: int = Path(..., description="Feature identifier to delete", example=10)
) -> PropertyFeatureDeleteResponse:
    session = SessionLocal()
    feat = session.query(PropertyFeature).filter(PropertyFeature.id == feature_id).first()
    success = False
    if feat is not None:
        session.delete(feat)
        session.commit()
        success = True
    session.close()
    return PropertyFeatureDeleteResponse(result=PropertyFeatureDeleteResult(success=success, deleted_feature_id=feature_id))

@app.post(
    "/api/properties/{property_id}/units",
    response_model=UnitSingleResponse,
    summary="Create a unit within a property",
    description="Add a new unit record for a given property.",
    tags=["units"],
    operation_id="create_unit",
)
async def create_unit(
    property_id: int = Path(..., description="Property identifier the unit belongs to", example=1),
    unit_in: UnitCreateRequest = Body(...),
) -> UnitSingleResponse:
    session = SessionLocal()
    unit = Unit(
        property_id=property_id,
        unit_name=unit_in.unit_name,
        floor_number=unit_in.floor_number,
        floor_area_sqm=unit_in.floor_area_sqm,
        fitout_type=unit_in.fitout_type,
        occupancy_status=unit_in.occupancy_status,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    session.add(unit)
    session.commit()
    session.refresh(unit)
    session.close()
    return UnitSingleResponse(unit=UnitModel.model_validate(unit))

@app.get(
    "/api/properties/{property_id}/units",
    response_model=UnitListResponse,
    summary="List units in a property",
    description="Retrieve all units for a given property with optional occupancy_status filter.",
    tags=["units"],
    operation_id="list_units_for_property",
)
async def list_units_for_property(
    property_id: int = Path(..., description="Property identifier to list units for", example=1),
    occupancy_status: Optional[str] = Query(None, description="Filter by occupancy_status", example="vacant"),
) -> UnitListResponse:
    session = SessionLocal()
    q = session.query(Unit).filter(Unit.property_id == property_id)
    if occupancy_status is not None:
        q = q.filter(Unit.occupancy_status == occupancy_status)
    units = q.all()
    session.close()
    return UnitListResponse(units=[UnitModel.model_validate(u) for u in units])

@app.get(
    "/api/units/{unit_id}",
    response_model=UnitSingleResponse,
    summary="Get a unit by ID",
    description="Retrieve a unit by its id including details such as floor, area, and fitout.",
    tags=["units"],
    operation_id="get_unit_by_id",
)
async def get_unit_by_id(
    unit_id: int = Path(..., description="Unit identifier", example=100)
) -> UnitSingleResponse:
    session = SessionLocal()
    unit = session.query(Unit).filter(Unit.id == unit_id).first()
    session.close()
    if unit is None:
        return UnitSingleResponse(unit=UnitModel.model_validate(Unit(id=0, property_id=0, unit_name="", floor_number=None, floor_area_sqm=None, fitout_type=None, occupancy_status="vacant", created_at=now_utc(), updated_at=now_utc())))
    return UnitSingleResponse(unit=UnitModel.model_validate(unit))

@app.patch(
    "/api/units/{unit_id}",
    response_model=UnitSingleResponse,
    summary="Update a unit",
    description="Partially update fields of a unit such as floor_area_sqm, fitout_type, or occupancy_status.",
    tags=["units"],
    operation_id="update_unit",
)
async def update_unit(
    unit_id: int = Path(..., description="Unit identifier to update", example=100),
    unit_in: UnitUpdateRequest = Body(...),
) -> UnitSingleResponse:
    session = SessionLocal()
    unit = session.query(Unit).filter(Unit.id == unit_id).first()
    if unit is None:
        session.close()
        return UnitSingleResponse(unit=UnitModel.model_validate(Unit(id=0, property_id=0, unit_name="", floor_number=None, floor_area_sqm=None, fitout_type=None, occupancy_status="vacant", created_at=now_utc(), updated_at=now_utc())))
    if unit_in.unit_name is not None:
        unit.unit_name = unit_in.unit_name
    if unit_in.floor_number is not None:
        unit.floor_number = unit_in.floor_number
    if unit_in.floor_area_sqm is not None:
        unit.floor_area_sqm = unit_in.floor_area_sqm
    if unit_in.fitout_type is not None:
        unit.fitout_type = unit_in.fitout_type
    if unit_in.occupancy_status is not None:
        unit.occupancy_status = unit_in.occupancy_status
    unit.updated_at = now_utc()
    session.commit()
    session.refresh(unit)
    session.close()
    return UnitSingleResponse(unit=UnitModel.model_validate(unit))

@app.delete(
    "/api/units/{unit_id}",
    response_model=UnitDeleteResponse,
    summary="Delete a unit",
    description="Delete a unit by its id.",
    tags=["units"],
    operation_id="delete_unit",
)
async def delete_unit(
    unit_id: int = Path(..., description="Unit identifier to delete", example=100)
) -> UnitDeleteResponse:
    session = SessionLocal()
    unit = session.query(Unit).filter(Unit.id == unit_id).first()
    success = False
    if unit is not None:
        session.delete(unit)
        session.commit()
        success = True
    session.close()
    return UnitDeleteResponse(result=UnitDeleteResult(success=success, deleted_unit_id=unit_id))

@app.post(
    "/api/tenants",
    response_model=TenantSingleResponse,
    summary="Create a new tenant",
    description="Create a tenant record including legal_name, ABN, billing details, and risk_rating.",
    tags=["tenants"],
    operation_id="create_tenant",
)
async def create_tenant(
    tenant_in: TenantCreateRequest = Body(...),
) -> TenantSingleResponse:
    session = SessionLocal()
    tenant = Tenant(
        legal_name=tenant_in.legal_name,
        abn=tenant_in.abn,
        billing_address=tenant_in.billing_address,
        risk_rating=tenant_in.risk_rating,
        primary_contact_name=tenant_in.primary_contact_name,
        primary_contact_email=tenant_in.primary_contact_email,
        primary_contact_phone=tenant_in.primary_contact_phone,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    session.close()
    return TenantSingleResponse(tenant=TenantModel.model_validate(tenant))

@app.get(
    "/api/tenants",
    response_model=TenantListResponse,
    summary="List tenants with optional search",
    description="Retrieve tenants with optional filters on legal_name, ABN, or risk_rating.",
    tags=["tenants"],
    operation_id="list_tenants",
)
async def list_tenants(
    legal_name_search: Optional[str] = Query(None, description="Case-insensitive partial search on legal_name", example="Bluewave"),
    abn: Optional[str] = Query(None, description="Filter tenants by exact ABN", example="22 345 678 901"),
    risk_rating: Optional[str] = Query(None, description="Filter by risk_rating ('low','medium','high')", example="medium"),
    limit: Optional[int] = Query(50, description="Maximum records to return", example=50),
    offset: Optional[int] = Query(0, description="Records to skip for pagination", example=0),
) -> TenantListResponse:
    session = SessionLocal()
    q = session.query(Tenant)
    if legal_name_search is not None:
        pattern = f"%{legal_name_search}%"
        q = q.filter(Tenant.legal_name.ilike(pattern))
    if abn is not None:
        q = q.filter(Tenant.abn == abn)
    if risk_rating is not None:
        q = q.filter(Tenant.risk_rating == risk_rating)
    tenants = q.offset(offset).limit(limit).all()
    session.close()
    return TenantListResponse(tenants=[TenantModel.model_validate(t) for t in tenants])

@app.get(
    "/api/tenants/{tenant_id}",
    response_model=TenantSingleResponse,
    summary="Get tenant by ID",
    description="Retrieve a single tenant by id including contact and risk information.",
    tags=["tenants"],
    operation_id="get_tenant_by_id",
)
async def get_tenant_by_id(
    tenant_id: int = Path(..., description="Tenant identifier", example=200)
) -> TenantSingleResponse:
    session = SessionLocal()
    tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
    session.close()
    if tenant is None:
        return TenantSingleResponse(tenant=TenantModel.model_validate(Tenant(id=0, legal_name="", abn=None, billing_address=None, risk_rating=None, primary_contact_name=None, primary_contact_email=None, primary_contact_phone=None, created_at=now_utc(), updated_at=now_utc())))
    return TenantSingleResponse(tenant=TenantModel.model_validate(tenant))

@app.patch(
    "/api/tenants/{tenant_id}",
    response_model=TenantSingleResponse,
    summary="Update a tenant",
    description="Partially update tenant details such as billing_address or risk_rating.",
    tags=["tenants"],
    operation_id="update_tenant",
)
async def update_tenant(
    tenant_id: int = Path(..., description="Tenant identifier to update", example=200),
    tenant_in: TenantUpdateRequest = Body(...),
) -> TenantSingleResponse:
    session = SessionLocal()
    tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant is None:
        session.close()
        return TenantSingleResponse(tenant=TenantModel.model_validate(Tenant(id=0, legal_name="", abn=None, billing_address=None, risk_rating=None, primary_contact_name=None, primary_contact_email=None, primary_contact_phone=None, created_at=now_utc(), updated_at=now_utc())))
    if tenant_in.legal_name is not None:
        tenant.legal_name = tenant_in.legal_name
    if tenant_in.abn is not None:
        tenant.abn = tenant_in.abn
    if tenant_in.billing_address is not None:
        tenant.billing_address = tenant_in.billing_address
    if tenant_in.risk_rating is not None:
        tenant.risk_rating = tenant_in.risk_rating
    if tenant_in.primary_contact_name is not None:
        tenant.primary_contact_name = tenant_in.primary_contact_name
    if tenant_in.primary_contact_email is not None:
        tenant.primary_contact_email = tenant_in.primary_contact_email
    if tenant_in.primary_contact_phone is not None:
        tenant.primary_contact_phone = tenant_in.primary_contact_phone
    tenant.updated_at = now_utc()
    session.commit()
    session.refresh(tenant)
    session.close()
    return TenantSingleResponse(tenant=TenantModel.model_validate(tenant))

@app.delete(
    "/api/tenants/{tenant_id}",
    response_model=TenantDeleteResponse,
    summary="Delete a tenant",
    description="Delete a tenant record by id.",
    tags=["tenants"],
    operation_id="delete_tenant",
)
async def delete_tenant(
    tenant_id: int = Path(..., description="Tenant identifier to delete", example=200)
) -> TenantDeleteResponse:
    session = SessionLocal()
    tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
    success = False
    if tenant is not None:
        session.delete(tenant)
        session.commit()
        success = True
    session.close()
    return TenantDeleteResponse(result=TenantDeleteResult(success=success, deleted_tenant_id=tenant_id))

@app.post(
    "/api/leases",
    response_model=LeaseSingleResponse,
    summary="Create a new lease",
    description="Create a lease linking tenant and unit with dates, rent_type, and security_deposit.",
    tags=["leases"],
    operation_id="create_lease",
)
async def create_lease(
    lease_in: LeaseCreateRequest = Body(...),
) -> LeaseSingleResponse:
    session = SessionLocal()
    lease = Lease(
        tenant_id=lease_in.tenant_id,
        unit_id=lease_in.unit_id,
        lease_start_date=date.fromisoformat(lease_in.lease_start_date),
        lease_end_date=date.fromisoformat(lease_in.lease_end_date),
        rent_type=lease_in.rent_type,
        security_deposit=lease_in.security_deposit,
        break_options=lease_in.break_options,
        status=lease_in.status if lease_in.status is not None else "active",
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    session.add(lease)
    session.commit()
    session.refresh(lease)
    session.close()
    return LeaseSingleResponse(lease=LeaseModel.model_validate(lease))

@app.get(
    "/api/leases",
    response_model=LeaseListResponse,
    summary="List leases with filters",
    description="Retrieve leases filtered by tenant_id, unit_id, status, or rent_type.",
    tags=["leases"],
    operation_id="list_leases",
)
async def list_leases(
    tenant_id: Optional[int] = Query(None, description="Filter leases by tenant_id", example=200),
    unit_id: Optional[int] = Query(None, description="Filter leases by unit_id", example=100),
    status: Optional[str] = Query(None, description="Filter by status", example="active"),
    rent_type: Optional[str] = Query(None, description="Filter by rent_type", example="indexed"),
    active_on_date: Optional[str] = Query(None, description="Return leases active on this date (YYYY-MM-DD)", example="2025-03-31"),
    limit: Optional[int] = Query(50, description="Maximum records to return", example=50),
    offset: Optional[int] = Query(0, description="Records to skip for pagination", example=0),
) -> LeaseListResponse:
    session = SessionLocal()
    q = session.query(Lease)
    if tenant_id is not None:
        q = q.filter(Lease.tenant_id == tenant_id)
    if unit_id is not None:
        q = q.filter(Lease.unit_id == unit_id)
    if status is not None:
        q = q.filter(Lease.status == status)
    if rent_type is not None:
        q = q.filter(Lease.rent_type == rent_type)
    if active_on_date is not None:
        d = date.fromisoformat(active_on_date)
        q = q.filter(Lease.lease_start_date <= d, Lease.lease_end_date >= d)
    leases = q.offset(offset).limit(limit).all()
    session.close()
    return LeaseListResponse(leases=[LeaseModel.model_validate(l) for l in leases])

@app.get(
    "/api/leases/{lease_id}",
    response_model=LeaseSingleResponse,
    summary="Get lease by ID",
    description="Retrieve full lease details by id.",
    tags=["leases"],
    operation_id="get_lease_by_id",
)
async def get_lease_by_id(
    lease_id: int = Path(..., description="Lease identifier", example=300)
) -> LeaseSingleResponse:
    session = SessionLocal()
    lease = session.query(Lease).filter(Lease.id == lease_id).first()
    session.close()
    if lease is None:
        return LeaseSingleResponse(lease=LeaseModel.model_validate(Lease(id=0, tenant_id=0, unit_id=0, lease_start_date=date.today(), lease_end_date=date.today(), rent_type="indexed", security_deposit=0.0, break_options=None, status="draft", created_at=now_utc(), updated_at=now_utc())))
    return LeaseSingleResponse(lease=LeaseModel.model_validate(lease))

@app.patch(
    "/api/leases/{lease_id}",
    response_model=LeaseSingleResponse,
    summary="Update a lease",
    description="Partially update lease fields including dates, rent_type, deposit, break_options, or status.",
    tags=["leases"],
    operation_id="update_lease",
)
async def update_lease(
    lease_id: int = Path(..., description="Lease identifier to update", example=300),
    lease_in: LeaseUpdateRequest = Body(...),
) -> LeaseSingleResponse:
    session = SessionLocal()
    lease = session.query(Lease).filter(Lease.id == lease_id).first()
    if lease is None:
        session.close()
        return LeaseSingleResponse(lease=LeaseModel.model_validate(Lease(id=0, tenant_id=0, unit_id=0, lease_start_date=date.today(), lease_end_date=date.today(), rent_type="indexed", security_deposit=0.0, break_options=None, status="draft", created_at=now_utc(), updated_at=now_utc())))
    if lease_in.lease_start_date is not None:
        lease.lease_start_date = date.fromisoformat(lease_in.lease_start_date)
    if lease_in.lease_end_date is not None:
        lease.lease_end_date = date.fromisoformat(lease_in.lease_end_date)
    if lease_in.rent_type is not None:
        lease.rent_type = lease_in.rent_type
    if lease_in.security_deposit is not None:
        lease.security_deposit = lease_in.security_deposit
    if lease_in.break_options is not None:
        lease.break_options = lease_in.break_options
    if lease_in.status is not None:
        lease.status = lease_in.status
    lease.updated_at = now_utc()
    session.commit()
    session.refresh(lease)
    session.close()
    return LeaseSingleResponse(lease=LeaseModel.model_validate(lease))

@app.delete(
    "/api/leases/{lease_id}",
    response_model=LeaseDeleteResponse,
    summary="Delete a lease",
    description="Delete a lease by id.",
    tags=["leases"],
    operation_id="delete_lease",
)
async def delete_lease(
    lease_id: int = Path(..., description="Lease identifier to delete", example=300)
) -> LeaseDeleteResponse:
    session = SessionLocal()
    lease = session.query(Lease).filter(Lease.id == lease_id).first()
    success = False
    if lease is not None:
        session.delete(lease)
        session.commit()
        success = True
    session.close()
    return LeaseDeleteResponse(result=LeaseDeleteResult(success=success, deleted_lease_id=lease_id))

@app.post(
    "/api/rent_schedules",
    response_model=RentScheduleSingleResponse,
    summary="Create a single rent schedule entry",
    description="Create one rent_schedules row for a lease.",
    tags=["rent_schedules"],
    operation_id="create_rent_schedule",
)
async def create_rent_schedule(
    rs_in: RentScheduleCreateRequest = Body(...),
) -> RentScheduleSingleResponse:
    session = SessionLocal()
    rs = RentSchedule(
        lease_id=rs_in.lease_id,
        charge_type=rs_in.charge_type,
        period_start=date.fromisoformat(rs_in.period_start),
        period_end=date.fromisoformat(rs_in.period_end),
        due_date=date.fromisoformat(rs_in.due_date),
        amount=rs_in.amount,
        currency=rs_in.currency if rs_in.currency is not None else "AUD",
        is_generated=rs_in.is_generated if rs_in.is_generated is not None else 1,
        is_revised=rs_in.is_revised if rs_in.is_revised is not None else 0,
        revision_note=rs_in.revision_note,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    session.add(rs)
    session.commit()
    session.refresh(rs)
    session.close()
    return RentScheduleSingleResponse(rent_schedule=RentScheduleModel.model_validate(rs))

@app.post(
    "/api/rent_schedules/bulk",
    response_model=RentScheduleBulkCreateResponse,
    summary="Bulk create rent schedule entries",
    description="Create multiple rent_schedules rows in one call.",
    tags=["rent_schedules"],
    operation_id="bulk_create_rent_schedules",
)
async def bulk_create_rent_schedules(
    rs_in: RentScheduleBulkCreateRequest = Body(...),
) -> RentScheduleBulkCreateResponse:
    session = SessionLocal()
    created_list: List[RentSchedule] = []
    for item in rs_in.items:
        rs = RentSchedule(
            lease_id=item.lease_id,
            charge_type=item.charge_type,
            period_start=date.fromisoformat(item.period_start),
            period_end=date.fromisoformat(item.period_end),
            due_date=date.fromisoformat(item.due_date),
            amount=item.amount,
            currency=item.currency if item.currency is not None else "AUD",
            is_generated=item.is_generated if item.is_generated is not None else 1,
            is_revised=item.is_revised if item.is_revised is not None else 0,
            revision_note=item.revision_note,
            created_at=now_utc(),
            updated_at=now_utc(),
        )
        session.add(rs)
        session.flush()
        created_list.append(rs)
    session.commit()
    for c in created_list:
        session.refresh(c)
    session.close()
    return RentScheduleBulkCreateResponse(rent_schedules=[RentScheduleModel.model_validate(r) for r in created_list])

@app.get(
    "/api/rent_schedules",
    response_model=RentScheduleListResponse,
    summary="List rent schedules with filters",
    description="Retrieve rent_schedules filtered by lease_id, charge_type, and date ranges.",
    tags=["rent_schedules"],
    operation_id="list_rent_schedules",
)
async def list_rent_schedules(
    lease_id: Optional[int] = Query(None, description="Filter by lease_id", example=300),
    charge_type: Optional[str] = Query(None, description="Filter by charge_type", example="base_rent"),
    due_date_from: Optional[str] = Query(None, description="Filter due_date >= this date", example="2025-01-01"),
    due_date_to: Optional[str] = Query(None, description="Filter due_date <= this date", example="2025-12-31"),
    period_start_from: Optional[str] = Query(None, description="Filter period_start >= this date", example="2025-01-01"),
    period_start_to: Optional[str] = Query(None, description="Filter period_start <= this date", example="2025-12-31"),
    limit: Optional[int] = Query(100, description="Maximum entries", example=100),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> RentScheduleListResponse:
    session = SessionLocal()
    q = session.query(RentSchedule)
    if lease_id is not None:
        q = q.filter(RentSchedule.lease_id == lease_id)
    if charge_type is not None:
        q = q.filter(RentSchedule.charge_type == charge_type)
    if due_date_from is not None:
        q = q.filter(RentSchedule.due_date >= date.fromisoformat(due_date_from))
    if due_date_to is not None:
        q = q.filter(RentSchedule.due_date <= date.fromisoformat(due_date_to))
    if period_start_from is not None:
        q = q.filter(RentSchedule.period_start >= date.fromisoformat(period_start_from))
    if period_start_to is not None:
        q = q.filter(RentSchedule.period_start <= date.fromisoformat(period_start_to))
    rs_list = q.offset(offset).limit(limit).all()
    session.close()
    return RentScheduleListResponse(rent_schedules=[RentScheduleModel.model_validate(r) for r in rs_list])

@app.patch(
    "/api/rent_schedules/{rent_schedule_id}",
    response_model=RentScheduleSingleResponse,
    summary="Update a rent schedule entry",
    description="Partially update a rent_schedules row such as amount, dates, or revision flags.",
    tags=["rent_schedules"],
    operation_id="update_rent_schedule",
)
async def update_rent_schedule(
    rent_schedule_id: int = Path(..., description="Rent schedule identifier", example=400),
    rs_in: RentScheduleUpdateRequest = Body(...),
) -> RentScheduleSingleResponse:
    session = SessionLocal()
    rs = session.query(RentSchedule).filter(RentSchedule.id == rent_schedule_id).first()
    if rs is None:
        session.close()
        dummy = RentSchedule(id=0, lease_id=0, charge_type="base_rent", period_start=date.today(), period_end=date.today(), due_date=date.today(), amount=0.0, currency="AUD", is_generated=1, is_revised=0, revision_note=None, created_at=now_utc(), updated_at=now_utc())
        return RentScheduleSingleResponse(rent_schedule=RentScheduleModel.model_validate(dummy))
    if rs_in.charge_type is not None:
        rs.charge_type = rs_in.charge_type
    if rs_in.period_start is not None:
        rs.period_start = date.fromisoformat(rs_in.period_start)
    if rs_in.period_end is not None:
        rs.period_end = date.fromisoformat(rs_in.period_end)
    if rs_in.due_date is not None:
        rs.due_date = date.fromisoformat(rs_in.due_date)
    if rs_in.amount is not None:
        rs.amount = rs_in.amount
    if rs_in.currency is not None:
        rs.currency = rs_in.currency
    if rs_in.is_generated is not None:
        rs.is_generated = rs_in.is_generated
    if rs_in.is_revised is not None:
        rs.is_revised = rs_in.is_revised
    if rs_in.revision_note is not None:
        rs.revision_note = rs_in.revision_note
    rs.updated_at = now_utc()
    session.commit()
    session.refresh(rs)
    session.close()
    return RentScheduleSingleResponse(rent_schedule=RentScheduleModel.model_validate(rs))

@app.delete(
    "/api/rent_schedules/{rent_schedule_id}",
    response_model=RentScheduleDeleteResponse,
    summary="Delete a rent schedule entry",
    description="Delete a rent_schedules row by id.",
    tags=["rent_schedules"],
    operation_id="delete_rent_schedule",
)
async def delete_rent_schedule(
    rent_schedule_id: int = Path(..., description="Rent schedule identifier to delete", example=400)
) -> RentScheduleDeleteResponse:
    session = SessionLocal()
    rs = session.query(RentSchedule).filter(RentSchedule.id == rent_schedule_id).first()
    success = False
    if rs is not None:
        session.delete(rs)
        session.commit()
        success = True
    session.close()
    return RentScheduleDeleteResponse(result=RentScheduleDeleteResult(success=success, deleted_rent_schedule_id=rent_schedule_id))

@app.post(
    "/api/invoices",
    response_model=InvoiceSingleResponse,
    summary="Create an invoice",
    description="Create a single invoice row linked optionally to rent_schedule_id.",
    tags=["invoices"],
    operation_id="create_invoice",
)
async def create_invoice(
    inv_in: InvoiceCreateRequest = Body(...),
) -> InvoiceSingleResponse:
    session = SessionLocal()
    invoice = Invoice(
        tenant_id=inv_in.tenant_id,
        lease_id=inv_in.lease_id,
        rent_schedule_id=inv_in.rent_schedule_id,
        invoice_number=inv_in.invoice_number,
        charge_type=inv_in.charge_type,
        description=inv_in.description,
        issue_date=date.fromisoformat(inv_in.issue_date),
        due_date=date.fromisoformat(inv_in.due_date),
        amount=inv_in.amount,
        amount_paid=inv_in.amount_paid if inv_in.amount_paid is not None else 0.0,
        allocation_status=inv_in.allocation_status if inv_in.allocation_status is not None else "unallocated",
        status=inv_in.status if inv_in.status is not None else "unpaid",
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    session.close()
    return InvoiceSingleResponse(invoice=InvoiceModel.model_validate(invoice))

@app.post(
    "/api/invoices/bulk",
    response_model=InvoiceBulkCreateResponse,
    summary="Bulk create invoices",
    description="Create multiple invoices at once, typically from rent_schedules.",
    tags=["invoices"],
    operation_id="bulk_create_invoices",
)
async def bulk_create_invoices(
    inv_in: InvoiceBulkCreateRequest = Body(...),
) -> InvoiceBulkCreateResponse:
    session = SessionLocal()
    created: List[Invoice] = []
    for item in inv_in.items:
        invoice = Invoice(
            tenant_id=item.tenant_id,
            lease_id=item.lease_id,
            rent_schedule_id=item.rent_schedule_id,
            invoice_number=item.invoice_number,
            charge_type=item.charge_type,
            description=item.description,
            issue_date=date.fromisoformat(item.issue_date),
            due_date=date.fromisoformat(item.due_date),
            amount=item.amount,
            amount_paid=item.amount_paid if item.amount_paid is not None else 0.0,
            allocation_status=item.allocation_status if item.allocation_status is not None else "unallocated",
            status=item.status if item.status is not None else "unpaid",
            created_at=now_utc(),
            updated_at=now_utc(),
        )
        session.add(invoice)
        session.flush()
        created.append(invoice)
    session.commit()
    for c in created:
        session.refresh(c)
    session.close()
    return InvoiceBulkCreateResponse(invoices=[InvoiceModel.model_validate(i) for i in created])

@app.get(
    "/api/invoices",
    response_model=InvoiceListResponse,
    summary="List invoices with filters",
    description="Retrieve invoices filtered by tenant, lease, status, due_date, or charge_type.",
    tags=["invoices"],
    operation_id="list_invoices",
)
async def list_invoices(
    tenant_id: Optional[int] = Query(None, description="Filter by tenant_id", example=200),
    lease_id: Optional[int] = Query(None, description="Filter by lease_id", example=300),
    status: Optional[str] = Query(None, description="Filter by status", example="unpaid"),
    allocation_status: Optional[str] = Query(None, description="Filter by allocation_status", example="unallocated"),
    charge_type: Optional[str] = Query(None, description="Filter by charge_type", example="base_rent"),
    due_date_to: Optional[str] = Query(None, description="Filter invoices due on or before this date", example="2025-03-31"),
    overdue_only: Optional[bool] = Query(False, description="If true, return only overdue invoices", example=True),
    limit: Optional[int] = Query(100, description="Maximum invoices to return", example=100),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> InvoiceListResponse:
    session = SessionLocal()
    q = session.query(Invoice)
    if tenant_id is not None:
        q = q.filter(Invoice.tenant_id == tenant_id)
    if lease_id is not None:
        q = q.filter(Invoice.lease_id == lease_id)
    if status is not None:
        q = q.filter(Invoice.status == status)
    if allocation_status is not None:
        q = q.filter(Invoice.allocation_status == allocation_status)
    if charge_type is not None:
        q = q.filter(Invoice.charge_type == charge_type)
    today_date = date.today()
    if due_date_to is not None:
        q = q.filter(Invoice.due_date <= date.fromisoformat(due_date_to))
    if overdue_only:
        q = q.filter(Invoice.due_date < today_date, Invoice.status != "paid")
    invoices = q.offset(offset).limit(limit).all()
    session.close()
    return InvoiceListResponse(invoices=[InvoiceModel.model_validate(i) for i in invoices])

@app.patch(
    "/api/invoices/{invoice_id}",
    response_model=InvoiceSingleResponse,
    summary="Update an invoice",
    description="Partially update invoice fields such as amount_paid, allocation_status, or status.",
    tags=["invoices"],
    operation_id="update_invoice",
)
async def update_invoice(
    invoice_id: int = Path(..., description="Invoice identifier to update", example=500),
    inv_in: InvoiceUpdateRequest = Body(...),
) -> InvoiceSingleResponse:
    session = SessionLocal()
    invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        session.close()
        dummy = Invoice(id=0, tenant_id=0, lease_id=0, rent_schedule_id=None, invoice_number=None, charge_type="base_rent", description=None, issue_date=date.today(), due_date=date.today(), amount=0.0, amount_paid=0.0, allocation_status="unallocated", status="unpaid", created_at=now_utc(), updated_at=now_utc())
        return InvoiceSingleResponse(invoice=InvoiceModel.model_validate(dummy))
    if inv_in.invoice_number is not None:
        invoice.invoice_number = inv_in.invoice_number
    if inv_in.description is not None:
        invoice.description = inv_in.description
    if inv_in.issue_date is not None:
        invoice.issue_date = date.fromisoformat(inv_in.issue_date)
    if inv_in.due_date is not None:
        invoice.due_date = date.fromisoformat(inv_in.due_date)
    if inv_in.amount is not None:
        invoice.amount = inv_in.amount
    if inv_in.amount_paid is not None:
        invoice.amount_paid = inv_in.amount_paid
    if inv_in.allocation_status is not None:
        invoice.allocation_status = inv_in.allocation_status
    if inv_in.status is not None:
        invoice.status = inv_in.status
    invoice.updated_at = now_utc()
    session.commit()
    session.refresh(invoice)
    session.close()
    return InvoiceSingleResponse(invoice=InvoiceModel.model_validate(invoice))

@app.delete(
    "/api/invoices/{invoice_id}",
    response_model=InvoiceDeleteResponse,
    summary="Delete an invoice",
    description="Delete an invoice by id.",
    tags=["invoices"],
    operation_id="delete_invoice",
)
async def delete_invoice(
    invoice_id: int = Path(..., description="Invoice identifier to delete", example=500)
) -> InvoiceDeleteResponse:
    session = SessionLocal()
    invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
    success = False
    if invoice is not None:
        session.delete(invoice)
        session.commit()
        success = True
    session.close()
    return InvoiceDeleteResponse(result=InvoiceDeleteResult(success=success, deleted_invoice_id=invoice_id))

@app.post(
    "/api/indexation_events",
    response_model=IndexationEventSingleResponse,
    summary="Create an indexation event",
    description="Create an indexation_events row recording an index_rate effective from a given date.",
    tags=["indexation_events"],
    operation_id="create_indexation_event",
)
async def create_indexation_event(
    idx_in: IndexationEventCreateRequest = Body(...),
) -> IndexationEventSingleResponse:
    session = SessionLocal()
    ev = IndexationEvent(
        lease_id=idx_in.lease_id,
        effective_date=date.fromisoformat(idx_in.effective_date),
        index_rate=idx_in.index_rate,
        description=idx_in.description,
        applied=idx_in.applied if idx_in.applied is not None else 0,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)
    session.close()
    return IndexationEventSingleResponse(indexation_event=IndexationEventModel.model_validate(ev))

@app.get(
    "/api/indexation_events",
    response_model=IndexationEventListResponse,
    summary="List indexation events",
    description="Retrieve indexation_events filtered by lease_id or applied flag.",
    tags=["indexation_events"],
    operation_id="list_indexation_events",
)
async def list_indexation_events(
    lease_id: Optional[int] = Query(None, description="Filter events by lease_id", example=300),
    applied: Optional[int] = Query(None, description="Filter by applied flag (0 or 1)", example=0),
) -> IndexationEventListResponse:
    session = SessionLocal()
    q = session.query(IndexationEvent)
    if lease_id is not None:
        q = q.filter(IndexationEvent.lease_id == lease_id)
    if applied is not None:
        q = q.filter(IndexationEvent.applied == applied)
    events = q.all()
    session.close()
    return IndexationEventListResponse(indexation_events=[IndexationEventModel.model_validate(e) for e in events])

@app.patch(
    "/api/indexation_events/{event_id}",
    response_model=IndexationEventSingleResponse,
    summary="Update an indexation event",
    description="Partially update indexation_events fields such as applied flag or description.",
    tags=["indexation_events"],
    operation_id="update_indexation_event",
)
async def update_indexation_event(
    event_id: int = Path(..., description="Indexation event identifier", example=600),
    idx_in: IndexationEventUpdateRequest = Body(...),
) -> IndexationEventSingleResponse:
    session = SessionLocal()
    ev = session.query(IndexationEvent).filter(IndexationEvent.id == event_id).first()
    if ev is None:
        session.close()
        dummy = IndexationEvent(id=0, lease_id=0, effective_date=date.today(), index_rate=0.0, description=None, applied=0, created_at=now_utc(), updated_at=now_utc())
        return IndexationEventSingleResponse(indexation_event=IndexationEventModel.model_validate(dummy))
    if idx_in.effective_date is not None:
        ev.effective_date = date.fromisoformat(idx_in.effective_date)
    if idx_in.index_rate is not None:
        ev.index_rate = idx_in.index_rate
    if idx_in.description is not None:
        ev.description = idx_in.description
    if idx_in.applied is not None:
        ev.applied = idx_in.applied
    ev.updated_at = now_utc()
    session.commit()
    session.refresh(ev)
    session.close()
    return IndexationEventSingleResponse(indexation_event=IndexationEventModel.model_validate(ev))

@app.delete(
    "/api/indexation_events/{event_id}",
    response_model=IndexationEventDeleteResponse,
    summary="Delete an indexation event",
    description="Delete an indexation_events record by id.",
    tags=["indexation_events"],
    operation_id="delete_indexation_event",
)
async def delete_indexation_event(
    event_id: int = Path(..., description="Indexation event identifier to delete", example=600)
) -> IndexationEventDeleteResponse:
    session = SessionLocal()
    ev = session.query(IndexationEvent).filter(IndexationEvent.id == event_id).first()
    success = False
    if ev is not None:
        session.delete(ev)
        session.commit()
        success = True
    session.close()
    return IndexationEventDeleteResponse(result=IndexationEventDeleteResult(success=success, deleted_indexation_event_id=event_id))

@app.post(
    "/api/leases/{lease_id}/apply_indexation",
    response_model=ApplyIndexationResponse,
    summary="Apply an indexation event to rent schedules",
    description="Apply a specific indexation_event to a lease and update base_rent rent_schedules.",
    tags=["indexation_events", "rent_schedules"],
    operation_id="apply_indexation_to_lease",
)
async def apply_indexation_to_lease(
    lease_id: int = Path(..., description="Lease identifier for which indexation will be applied", example=300),
    body: ApplyIndexationRequest = Body(...),
) -> ApplyIndexationResponse:
    session = SessionLocal()
    ev = session.query(IndexationEvent).filter(IndexationEvent.id == body.indexation_event_id, IndexationEvent.lease_id == lease_id).first()
    updated_ids: List[int] = []
    if ev is not None:
        if body.apply_from_due_date is not None:
            from_date = date.fromisoformat(body.apply_from_due_date)
        else:
            from_date = ev.effective_date
        rs_list = session.query(RentSchedule).filter(RentSchedule.lease_id == lease_id, RentSchedule.charge_type == "base_rent", RentSchedule.due_date >= from_date).all()
        factor = 1.0 + ev.index_rate / 100.0
        for rs in rs_list:
            rs.amount = rs.amount * factor
            rs.is_revised = 1
            note = "Indexation applied"
            if rs.revision_note is not None and rs.revision_note != "":
                rs.revision_note = rs.revision_note + "; " + note
            else:
                rs.revision_note = note
            rs.updated_at = now_utc()
            updated_ids.append(rs.id)
        ev.applied = 1
        ev.updated_at = now_utc()
        session.commit()
    session.close()
    result = ApplyIndexationAllocationResult(
        indexation_event_id=body.indexation_event_id,
        lease_id=lease_id,
        updated_rent_schedule_ids=updated_ids,
        applied_index_rate=ev.index_rate if ev is not None else 0.0,
    )
    return ApplyIndexationResponse(result=result)

@app.post(
    "/api/payments",
    response_model=PaymentSingleResponse,
    summary="Record a payment",
    description="Create a payment row for a tenant specifying amount, received_date, method, and reference.",
    tags=["payments"],
    operation_id="create_payment",
)
async def create_payment(
    pay_in: PaymentCreateRequest = Body(...),
) -> PaymentSingleResponse:
    session = SessionLocal()
    pay = Payment(
        tenant_id=pay_in.tenant_id,
        received_date=date.fromisoformat(pay_in.received_date),
        amount=pay_in.amount,
        payment_method=pay_in.payment_method,
        reference=pay_in.reference,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    session.add(pay)
    session.commit()
    session.refresh(pay)
    session.close()
    return PaymentSingleResponse(payment=PaymentModel.model_validate(pay))

@app.get(
    "/api/payments",
    response_model=PaymentListResponse,
    summary="List payments",
    description="Retrieve payments filtered by tenant_id or date range.",
    tags=["payments"],
    operation_id="list_payments",
)
async def list_payments(
    tenant_id: Optional[int] = Query(None, description="Filter by tenant_id", example=200),
    received_date_from: Optional[str] = Query(None, description="Filter payments received on or after this date", example="2025-01-01"),
    received_date_to: Optional[str] = Query(None, description="Filter payments received on or before this date", example="2025-12-31"),
    limit: Optional[int] = Query(100, description="Maximum payments to return", example=100),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> PaymentListResponse:
    session = SessionLocal()
    q = session.query(Payment)
    if tenant_id is not None:
        q = q.filter(Payment.tenant_id == tenant_id)
    if received_date_from is not None:
        q = q.filter(Payment.received_date >= date.fromisoformat(received_date_from))
    if received_date_to is not None:
        q = q.filter(Payment.received_date <= date.fromisoformat(received_date_to))
    pays = q.offset(offset).limit(limit).all()
    session.close()
    return PaymentListResponse(payments=[PaymentModel.model_validate(p) for p in pays])

@app.get(
    "/api/payments/{payment_id}",
    response_model=PaymentSingleResponse,
    summary="Get payment by ID",
    description="Retrieve a payment by its identifier.",
    tags=["payments"],
    operation_id="get_payment_by_id",
)
async def get_payment_by_id(
    payment_id: int = Path(..., description="Payment identifier", example=700)
) -> PaymentSingleResponse:
    session = SessionLocal()
    pay = session.query(Payment).filter(Payment.id == payment_id).first()
    session.close()
    if pay is None:
        dummy = Payment(id=0, tenant_id=0, received_date=date.today(), amount=0.0, payment_method="", reference=None, created_at=now_utc(), updated_at=now_utc())
        return PaymentSingleResponse(payment=PaymentModel.model_validate(dummy))
    return PaymentSingleResponse(payment=PaymentModel.model_validate(pay))

@app.delete(
    "/api/payments/{payment_id}",
    response_model=PaymentDeleteResponse,
    summary="Delete a payment",
    description="Delete a payment record by id; associated allocations are cascade deleted.",
    tags=["payments"],
    operation_id="delete_payment",
)
async def delete_payment(
    payment_id: int = Path(..., description="Payment identifier to delete", example=700)
) -> PaymentDeleteResponse:
    session = SessionLocal()
    pay = session.query(Payment).filter(Payment.id == payment_id).first()
    success = False
    if pay is not None:
        session.delete(pay)
        session.commit()
        success = True
    session.close()
    return PaymentDeleteResponse(result=PaymentDeleteResult(success=success, deleted_payment_id=payment_id))

@app.post(
    "/api/payment_allocations",
    response_model=PaymentAllocationSingleResponse,
    summary="Create a payment allocation",
    description="Allocate a portion of a payment to a specific invoice.",
    tags=["payment_allocations"],
    operation_id="create_payment_allocation",
)
async def create_payment_allocation(
    alloc_in: PaymentAllocationCreateRequest = Body(...),
) -> PaymentAllocationSingleResponse:
    session = SessionLocal()
    alloc = PaymentAllocation(
        payment_id=alloc_in.payment_id,
        invoice_id=alloc_in.invoice_id,
        allocated_amount=alloc_in.allocated_amount,
        created_at=now_utc(),
    )
    session.add(alloc)
    invoice = session.query(Invoice).filter(Invoice.id == alloc_in.invoice_id).first()
    if invoice is not None:
        invoice.amount_paid = invoice.amount_paid + alloc_in.allocated_amount
        if invoice.amount_paid >= invoice.amount:
            invoice.allocation_status = "fully_allocated"
            invoice.status = "paid"
        elif invoice.amount_paid > 0:
            invoice.allocation_status = "partially_allocated"
        invoice.updated_at = now_utc()
    session.commit()
    session.refresh(alloc)
    session.close()
    return PaymentAllocationSingleResponse(payment_allocation=PaymentAllocationModel.model_validate(alloc))

@app.get(
    "/api/payment_allocations",
    response_model=PaymentAllocationListResponse,
    summary="List payment allocations",
    description="Retrieve payment_allocations filtered by payment_id or invoice_id.",
    tags=["payment_allocations"],
    operation_id="list_payment_allocations",
)
async def list_payment_allocations(
    payment_id: Optional[int] = Query(None, description="Filter by payment_id", example=700),
    invoice_id: Optional[int] = Query(None, description="Filter by invoice_id", example=500),
) -> PaymentAllocationListResponse:
    session = SessionLocal()
    q = session.query(PaymentAllocation)
    if payment_id is not None:
        q = q.filter(PaymentAllocation.payment_id == payment_id)
    if invoice_id is not None:
        q = q.filter(PaymentAllocation.invoice_id == invoice_id)
    allocs = q.all()
    session.close()
    return PaymentAllocationListResponse(payment_allocations=[PaymentAllocationModel.model_validate(a) for a in allocs])

@app.delete(
    "/api/payment_allocations/{allocation_id}",
    response_model=PaymentAllocationDeleteResponse,
    summary="Delete a payment allocation",
    description="Delete a payment_allocations record and adjust invoice balances accordingly in logic.",
    tags=["payment_allocations"],
    operation_id="delete_payment_allocation",
)
async def delete_payment_allocation(
    allocation_id: int = Path(..., description="Payment allocation identifier to delete", example=800)
) -> PaymentAllocationDeleteResponse:
    session = SessionLocal()
    alloc = session.query(PaymentAllocation).filter(PaymentAllocation.id == allocation_id).first()
    success = False
    if alloc is not None:
        invoice = session.query(Invoice).filter(Invoice.id == alloc.invoice_id).first()
        if invoice is not None:
            invoice.amount_paid = max(0.0, invoice.amount_paid - alloc.allocated_amount)
            if invoice.amount_paid <= 0:
                invoice.allocation_status = "unallocated"
                if invoice.status != "cancelled":
                    invoice.status = "unpaid"
            elif invoice.amount_paid < invoice.amount:
                invoice.allocation_status = "partially_allocated"
                if invoice.status != "cancelled":
                    invoice.status = "unpaid"
            else:
                invoice.allocation_status = "fully_allocated"
                invoice.status = "paid"
            invoice.updated_at = now_utc()
        session.delete(alloc)
        session.commit()
        success = True
    session.close()
    return PaymentAllocationDeleteResponse(result=PaymentAllocationDeleteResult(success=success, deleted_allocation_id=allocation_id))

@app.post(
    "/api/payments/{payment_id}/auto_allocate",
    response_model=AutoAllocateResponse,
    summary="Auto-allocate a payment to invoices",
    description="Automatically allocate payment amount to tenant invoices in priority order.",
    tags=["payment_allocations", "payments", "invoices"],
    operation_id="auto_allocate_payment_to_invoices",
)
async def auto_allocate_payment_to_invoices(
    payment_id: int = Path(..., description="Payment identifier to allocate", example=700),
    body: AutoAllocateRequest = Body(...),
) -> AutoAllocateResponse:
    session = SessionLocal()
    pay = session.query(Payment).filter(Payment.id == payment_id).first()
    total_allocated = 0.0
    allocations: List[AutoAllocateInvoiceAllocation] = []
    if pay is not None:
        order = body.allocation_order if body.allocation_order is not None else ["base_rent", "service_charge", "parking"]
        up_to_date = date.fromisoformat(body.up_to_due_date) if body.up_to_due_date is not None else None
        q = session.query(Invoice).filter(Invoice.tenant_id == pay.tenant_id, Invoice.status != "paid")
        if up_to_date is not None:
            q = q.filter(Invoice.due_date <= up_to_date)
        invoices = q.all()
        invoices_sorted: List[Invoice] = []
        for charge in order:
            part = [inv for inv in invoices if inv.charge_type == charge]
            part.sort(key=lambda x: x.due_date)
            invoices_sorted.extend(part)
        remaining = pay.amount
        for inv in invoices_sorted:
            if remaining <= 0:
                break
            outstanding = inv.amount - inv.amount_paid
            if outstanding <= 0:
                continue
            alloc_amount = remaining if remaining <= outstanding else outstanding
            remaining = remaining - alloc_amount
            pa = PaymentAllocation(payment_id=payment_id, invoice_id=inv.id, allocated_amount=alloc_amount, created_at=now_utc())
            session.add(pa)
            inv.amount_paid = inv.amount_paid + alloc_amount
            if inv.amount_paid >= inv.amount:
                inv.allocation_status = "fully_allocated"
                inv.status = "paid"
            elif inv.amount_paid > 0:
                inv.allocation_status = "partially_allocated"
                if inv.status != "cancelled":
                    inv.status = "unpaid"
            inv.updated_at = now_utc()
            session.flush()
            total_allocated = total_allocated + alloc_amount
            session.refresh(pa)
            allocations.append(
                AutoAllocateInvoiceAllocation(
                    invoice_id=inv.id,
                    allocated_amount=alloc_amount,
                    allocation_id=pa.id,
                    allocation_status=inv.allocation_status,
                    invoice_status=inv.status,
                )
            )
        session.commit()
    session.close()
    result = AutoAllocateResult(payment_id=payment_id, total_allocated=total_allocated, allocations=allocations)
    return AutoAllocateResponse(result=result)

@app.post(
    "/api/vendors",
    response_model=VendorSingleResponse,
    summary="Create a vendor",
    description="Create a vendor record to be used for maintenance_requests.",
    tags=["vendors"],
    operation_id="create_vendor",
)
async def create_vendor(
    vendor_in: VendorCreateRequest = Body(...),
) -> VendorSingleResponse:
    session = SessionLocal()
    vendor = Vendor(
        name=vendor_in.name,
        contact_name=vendor_in.contact_name,
        contact_email=vendor_in.contact_email,
        contact_phone=vendor_in.contact_phone,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    session.add(vendor)
    session.commit()
    session.refresh(vendor)
    session.close()
    return VendorSingleResponse(vendor=VendorModel.model_validate(vendor))

@app.get(
    "/api/vendors",
    response_model=VendorListResponse,
    summary="List vendors",
    description="Retrieve vendors with optional name search.",
    tags=["vendors"],
    operation_id="list_vendors",
)
async def list_vendors(
    name_search: Optional[str] = Query(None, description="Case-insensitive partial search on vendor name", example="ChillTech"),
) -> VendorListResponse:
    session = SessionLocal()
    q = session.query(Vendor)
    if name_search is not None:
        pattern = f"%{name_search}%"
        q = q.filter(Vendor.name.ilike(pattern))
    vendors = q.all()
    session.close()
    return VendorListResponse(vendors=[VendorModel.model_validate(v) for v in vendors])

@app.get(
    "/api/vendors/{vendor_id}",
    response_model=VendorSingleResponse,
    summary="Get vendor by ID",
    description="Retrieve a vendor by id.",
    tags=["vendors"],
    operation_id="get_vendor_by_id",
)
async def get_vendor_by_id(
    vendor_id: int = Path(..., description="Vendor identifier", example=900)
) -> VendorSingleResponse:
    session = SessionLocal()
    vendor = session.query(Vendor).filter(Vendor.id == vendor_id).first()
    session.close()
    if vendor is None:
        dummy = Vendor(id=0, name="", contact_name=None, contact_email=None, contact_phone=None, created_at=now_utc(), updated_at=now_utc())
        return VendorSingleResponse(vendor=VendorModel.model_validate(dummy))
    return VendorSingleResponse(vendor=VendorModel.model_validate(vendor))

@app.patch(
    "/api/vendors/{vendor_id}",
    response_model=VendorSingleResponse,
    summary="Update a vendor",
    description="Partially update vendor contact information.",
    tags=["vendors"],
    operation_id="update_vendor",
)
async def update_vendor(
    vendor_id: int = Path(..., description="Vendor identifier to update", example=900),
    vendor_in: VendorUpdateRequest = Body(...),
) -> VendorSingleResponse:
    session = SessionLocal()
    vendor = session.query(Vendor).filter(Vendor.id == vendor_id).first()
    if vendor is None:
        session.close()
        dummy = Vendor(id=0, name="", contact_name=None, contact_email=None, contact_phone=None, created_at=now_utc(), updated_at=now_utc())
        return VendorSingleResponse(vendor=VendorModel.model_validate(dummy))
    if vendor_in.name is not None:
        vendor.name = vendor_in.name
    if vendor_in.contact_name is not None:
        vendor.contact_name = vendor_in.contact_name
    if vendor_in.contact_email is not None:
        vendor.contact_email = vendor_in.contact_email
    if vendor_in.contact_phone is not None:
        vendor.contact_phone = vendor_in.contact_phone
    vendor.updated_at = now_utc()
    session.commit()
    session.refresh(vendor)
    session.close()
    return VendorSingleResponse(vendor=VendorModel.model_validate(vendor))

@app.delete(
    "/api/vendors/{vendor_id}",
    response_model=VendorDeleteResponse,
    summary="Delete a vendor",
    description="Delete a vendor by id.",
    tags=["vendors"],
    operation_id="delete_vendor",
)
async def delete_vendor(
    vendor_id: int = Path(..., description="Vendor identifier to delete", example=900)
) -> VendorDeleteResponse:
    session = SessionLocal()
    vendor = session.query(Vendor).filter(Vendor.id == vendor_id).first()
    success = False
    if vendor is not None:
        session.delete(vendor)
        session.commit()
        success = True
    session.close()
    return VendorDeleteResponse(result=VendorDeleteResult(success=success, deleted_vendor_id=vendor_id))

@app.post(
    "/api/maintenance_requests",
    response_model=MaintenanceRequestSingleResponse,
    summary="Create a maintenance request",
    description="Create a maintenance_requests row with property, unit, tenant, priority, and issue details.",
    tags=["maintenance_requests"],
    operation_id="create_maintenance_request",
)
async def create_maintenance_request(
    mr_in: MaintenanceRequestCreateRequest = Body(...),
) -> MaintenanceRequestSingleResponse:
    session = SessionLocal()
    req_date = date.fromisoformat(mr_in.requested_date) if mr_in.requested_date is not None else date.today()
    mr = MaintenanceRequest(
        property_id=mr_in.property_id,
        unit_id=mr_in.unit_id,
        tenant_id=mr_in.tenant_id,
        priority_level=mr_in.priority_level,
        issue_category=mr_in.issue_category,
        description=mr_in.description,
        photos_metadata=mr_in.photos_metadata,
        preferred_access_times=mr_in.preferred_access_times,
        status=mr_in.status,
        vendor_id=mr_in.vendor_id,
        resolution_notes=mr_in.resolution_notes,
        requested_date=req_date,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    session.add(mr)
    session.commit()
    session.refresh(mr)
    session.close()
    return MaintenanceRequestSingleResponse(maintenance_request=MaintenanceRequestModel.model_validate(mr))

@app.get(
    "/api/maintenance_requests",
    response_model=MaintenanceRequestListResponse,
    summary="List maintenance requests",
    description="Retrieve maintenance_requests filtered by property, tenant, status, or vendor.",
    tags=["maintenance_requests"],
    operation_id="list_maintenance_requests",
)
async def list_maintenance_requests(
    property_id: Optional[int] = Query(None, description="Filter by property_id", example=1),
    unit_id: Optional[int] = Query(None, description="Filter by unit_id", example=100),
    tenant_id: Optional[int] = Query(None, description="Filter by tenant_id", example=200),
    status: Optional[str] = Query(None, description="Filter by status", example="in_progress"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor_id", example=900),
    priority_level: Optional[str] = Query(None, description="Filter by priority_level", example="high"),
) -> MaintenanceRequestListResponse:
    session = SessionLocal()
    q = session.query(MaintenanceRequest)
    if property_id is not None:
        q = q.filter(MaintenanceRequest.property_id == property_id)
    if unit_id is not None:
        q = q.filter(MaintenanceRequest.unit_id == unit_id)
    if tenant_id is not None:
        q = q.filter(MaintenanceRequest.tenant_id == tenant_id)
    if status is not None:
        q = q.filter(MaintenanceRequest.status == status)
    if vendor_id is not None:
        q = q.filter(MaintenanceRequest.vendor_id == vendor_id)
    if priority_level is not None:
        q = q.filter(MaintenanceRequest.priority_level == priority_level)
    mrs = q.all()
    session.close()
    return MaintenanceRequestListResponse(maintenance_requests=[MaintenanceRequestModel.model_validate(m) for m in mrs])

@app.patch(
    "/api/maintenance_requests/{request_id}",
    response_model=MaintenanceRequestSingleResponse,
    summary="Update a maintenance request",
    description="Partially update maintenance request fields such as status, vendor_id, or resolution_notes.",
    tags=["maintenance_requests"],
    operation_id="update_maintenance_request",
)
async def update_maintenance_request(
    request_id: int = Path(..., description="Maintenance request identifier", example=1000),
    mr_in: MaintenanceRequestUpdateRequest = Body(...),
) -> MaintenanceRequestSingleResponse:
    session = SessionLocal()
    mr = session.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if mr is None:
        session.close()
        dummy = MaintenanceRequest(id=0, property_id=0, unit_id=None, tenant_id=None, priority_level="low", issue_category="", description="", photos_metadata=None, preferred_access_times=None, status="open", vendor_id=None, resolution_notes=None, requested_date=date.today(), created_at=now_utc(), updated_at=now_utc())
        return MaintenanceRequestSingleResponse(maintenance_request=MaintenanceRequestModel.model_validate(dummy))
    if mr_in.priority_level is not None:
        mr.priority_level = mr_in.priority_level
    if mr_in.issue_category is not None:
        mr.issue_category = mr_in.issue_category
    if mr_in.description is not None:
        mr.description = mr_in.description
    if mr_in.photos_metadata is not None:
        mr.photos_metadata = mr_in.photos_metadata
    if mr_in.preferred_access_times is not None:
        mr.preferred_access_times = mr_in.preferred_access_times
    if mr_in.status is not None:
        mr.status = mr_in.status
    if mr_in.vendor_id is not None:
        mr.vendor_id = mr_in.vendor_id
    if mr_in.resolution_notes is not None:
        mr.resolution_notes = mr_in.resolution_notes
    mr.updated_at = now_utc()
    session.commit()
    session.refresh(mr)
    session.close()
    return MaintenanceRequestSingleResponse(maintenance_request=MaintenanceRequestModel.model_validate(mr))

@app.delete(
    "/api/maintenance_requests/{request_id}",
    response_model=MaintenanceRequestDeleteResponse,
    summary="Delete a maintenance request",
    description="Delete a maintenance_requests row by id.",
    tags=["maintenance_requests"],
    operation_id="delete_maintenance_request",
)
async def delete_maintenance_request(
    request_id: int = Path(..., description="Maintenance request identifier to delete", example=1000)
) -> MaintenanceRequestDeleteResponse:
    session = SessionLocal()
    mr = session.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    success = False
    if mr is not None:
        session.delete(mr)
        session.commit()
        success = True
    session.close()
    return MaintenanceRequestDeleteResponse(result=MaintenanceRequestDeleteResult(success=success, deleted_request_id=request_id))

@app.post(
    "/api/inspections",
    response_model=InspectionSingleResponse,
    summary="Create an inspection record",
    description="Create an inspections row for a property with type, scheduled_date, outcome, and follow_up_actions.",
    tags=["inspections"],
    operation_id="create_inspection",
)
async def create_inspection(
    ins_in: InspectionCreateRequest = Body(...),
) -> InspectionSingleResponse:
    session = SessionLocal()
    ins = Inspection(
        property_id=ins_in.property_id,
        inspection_type=ins_in.inspection_type,
        scheduled_date=date.fromisoformat(ins_in.scheduled_date),
        outcome=ins_in.outcome,
        follow_up_actions=ins_in.follow_up_actions,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    session.add(ins)
    session.commit()
    session.refresh(ins)
    session.close()
    return InspectionSingleResponse(inspection=InspectionModel.model_validate(ins))

@app.get(
    "/api/inspections",
    response_model=InspectionListResponse,
    summary="List inspections",
    description="Retrieve inspections filtered by property_id, outcome, or date range.",
    tags=["inspections"],
    operation_id="list_inspections",
)
async def list_inspections(
    property_id: Optional[int] = Query(None, description="Filter by property_id", example=1),
    outcome: Optional[str] = Query(None, description="Filter by outcome ('pass','fail','pending')", example="fail"),
    scheduled_date_from: Optional[str] = Query(None, description="Filter scheduled_date >= this date", example="2025-02-01"),
    scheduled_date_to: Optional[str] = Query(None, description="Filter scheduled_date <= this date", example="2025-03-31"),
) -> InspectionListResponse:
    session = SessionLocal()
    q = session.query(Inspection)
    if property_id is not None:
        q = q.filter(Inspection.property_id == property_id)
    if outcome is not None:
        q = q.filter(Inspection.outcome == outcome)
    if scheduled_date_from is not None:
        q = q.filter(Inspection.scheduled_date >= date.fromisoformat(scheduled_date_from))
    if scheduled_date_to is not None:
        q = q.filter(Inspection.scheduled_date <= date.fromisoformat(scheduled_date_to))
    inspections = q.all()
    session.close()
    return InspectionListResponse(inspections=[InspectionModel.model_validate(i) for i in inspections])

@app.patch(
    "/api/inspections/{inspection_id}",
    response_model=InspectionSingleResponse,
    summary="Update an inspection record",
    description="Partially update inspections fields including outcome and follow_up_actions.",
    tags=["inspections"],
    operation_id="update_inspection",
)
async def update_inspection(
    inspection_id: int = Path(..., description="Inspection identifier to update", example=1101),
    ins_in: InspectionUpdateRequest = Body(...),
) -> InspectionSingleResponse:
    session = SessionLocal()
    ins = session.query(Inspection).filter(Inspection.id == inspection_id).first()
    if ins is None:
        session.close()
        dummy = Inspection(id=0, property_id=0, inspection_type="", scheduled_date=date.today(), outcome=None, follow_up_actions=None, created_at=now_utc(), updated_at=now_utc())
        return InspectionSingleResponse(inspection=InspectionModel.model_validate(dummy))
    if ins_in.inspection_type is not None:
        ins.inspection_type = ins_in.inspection_type
    if ins_in.scheduled_date is not None:
        ins.scheduled_date = date.fromisoformat(ins_in.scheduled_date)
    if ins_in.outcome is not None:
        ins.outcome = ins_in.outcome
    if ins_in.follow_up_actions is not None:
        ins.follow_up_actions = ins_in.follow_up_actions
    ins.updated_at = now_utc()
    session.commit()
    session.refresh(ins)
    session.close()
    return InspectionSingleResponse(inspection=InspectionModel.model_validate(ins))

@app.delete(
    "/api/inspections/{inspection_id}",
    response_model=InspectionDeleteResponse,
    summary="Delete an inspection record",
    description="Delete an inspections row by id.",
    tags=["inspections"],
    operation_id="delete_inspection",
)
async def delete_inspection(
    inspection_id: int = Path(..., description="Inspection identifier to delete", example=1101)
) -> InspectionDeleteResponse:
    session = SessionLocal()
    ins = session.query(Inspection).filter(Inspection.id == inspection_id).first()
    success = False
    if ins is not None:
        session.delete(ins)
        session.commit()
        success = True
    session.close()
    return InspectionDeleteResponse(result=InspectionDeleteResult(success=success, deleted_inspection_id=inspection_id))

@app.get(
    "/api/inspections/failed",
    response_model=FailedInspectionReportResponse,
    summary="List failed inspections with follow-up actions",
    description="Retrieve inspections where outcome='fail' with property details and follow_up_actions for reporting.",
    tags=["inspections", "reports"],
    operation_id="list_failed_inspections_with_followups",
)
async def list_failed_inspections_with_followups(
    property_id: Optional[int] = Query(None, description="Filter failed inspections by property_id", example=1),
    scheduled_date_to: Optional[str] = Query(None, description="Filter failed inspections scheduled on or before this date", example="2025-03-31"),
) -> FailedInspectionReportResponse:
    session = SessionLocal()
    q = session.query(Inspection, Property).join(Property, Inspection.property_id == Property.id, isouter=True).filter(Inspection.outcome == "fail")
    if property_id is not None:
        q = q.filter(Inspection.property_id == property_id)
    if scheduled_date_to is not None:
        q = q.filter(Inspection.scheduled_date <= date.fromisoformat(scheduled_date_to))
    results = q.all()
    session.close()
    items: List[FailedInspectionReportItem] = []
    for ins, prop in results:
        items.append(
            FailedInspectionReportItem(
                inspection_id=ins.id,
                property_id=ins.property_id,
                property_name=prop.name if prop is not None else None,
                inspection_type=ins.inspection_type,
                scheduled_date=ins.scheduled_date,
                outcome=ins.outcome if ins.outcome is not None else "fail",
                follow_up_actions=ins.follow_up_actions,
            )
        )
    return FailedInspectionReportResponse(failed_inspections=items)

@app.get(
    "/api/reports/arrears",
    response_model=ArrearsReportResponse,
    summary="Generate arrears report for a property",
    description="Generate an arrears report as of a date for a property summarizing overdue amounts per tenant.",
    tags=["reports", "invoices"],
    operation_id="generate_arrears_report_by_property",
)
async def generate_arrears_report_by_property(
    property_id: int = Query(..., description="Property identifier to report on", example=1),
    as_of_date: str = Query(..., description="Date to evaluate arrears as of (YYYY-MM-DD)", example="2025-03-31"),
) -> ArrearsReportResponse:
    session = SessionLocal()
    prop = session.query(Property).filter(Property.id == property_id).first()
    as_of = date.fromisoformat(as_of_date)
    q = (
        session.query(Invoice, Lease, Unit, Tenant)
        .join(Lease, Invoice.lease_id == Lease.id)
        .join(Unit, Lease.unit_id == Unit.id)
        .join(Tenant, Invoice.tenant_id == Tenant.id)
        .filter(Unit.property_id == property_id, Invoice.due_date <= as_of, Invoice.status != "paid")
    )
    rows = q.all()
    session.close()
    per_tenant: Dict[int, Dict[str, object]] = {}
    for inv, lease, unit, tenant in rows:
        tid = tenant.id
        if tid not in per_tenant:
            per_tenant[tid] = {
                "tenant_id": tid,
                "tenant_legal_name": tenant.legal_name,
                "total_overdue_amount": 0.0,
                "number_of_unpaid_invoices": 0,
                "oldest_overdue_invoice_due_date": None,
            }
        entry = per_tenant[tid]
        overdue_amount = inv.amount - inv.amount_paid
        if overdue_amount < 0:
            overdue_amount = 0.0
        entry["total_overdue_amount"] = float(entry["total_overdue_amount"]) + overdue_amount
        entry["number_of_unpaid_invoices"] = int(entry["number_of_unpaid_invoices"]) + 1
        if entry["oldest_overdue_invoice_due_date"] is None or inv.due_date < entry["oldest_overdue_invoice_due_date"]:
            entry["oldest_overdue_invoice_due_date"] = inv.due_date
    tenants_items: List[ArrearsTenantItem] = []
    for data in per_tenant.values():
        tenants_items.append(
            ArrearsTenantItem(
                tenant_id=data["tenant_id"],
                tenant_legal_name=data["tenant_legal_name"],
                total_overdue_amount=float(data["total_overdue_amount"]),
                number_of_unpaid_invoices=int(data["number_of_unpaid_invoices"]),
                oldest_overdue_invoice_due_date=data["oldest_overdue_invoice_due_date"],
            )
        )
    tenants_items.sort(key=lambda x: x.total_overdue_amount, reverse=True)
    return ArrearsReportResponse(property_id=property_id, property_name=prop.name if prop is not None else None, as_of_date=as_of, tenants=tenants_items)

@app.post(
    "/api/leases/{lease_id}/recalculate_rent_schedule",
    response_model=RecalculateRentScheduleResponse,
    summary="Recalculate future rent schedules for a lease",
    description="Recalculate all future rent_schedules from a given date for a lease.",
    tags=["leases", "rent_schedules"],
    operation_id="recalculate_future_rent_schedules_for_lease",
)
async def recalculate_future_rent_schedules_for_lease(
    lease_id: int = Path(..., description="Lease identifier whose schedules will be recalculated", example=350),
    body: RecalculateRentScheduleRequest = Body(...),
) -> RecalculateRentScheduleResponse:
    session = SessionLocal()
    from_date = date.fromisoformat(body.recalculate_from_date)
    deleted_ids: List[int] = []
    updated_ids: List[int] = []
    created_ids: List[int] = []
    if body.replace_turnover_with_annual_indexed:
        future_ts = session.query(RentSchedule).filter(RentSchedule.lease_id == lease_id, RentSchedule.charge_type == "turnover_top_up", RentSchedule.due_date >= from_date).all()
        for rs in future_ts:
            deleted_ids.append(rs.id)
            session.delete(rs)
    if body.new_monthly_base_rent is not None:
        future_base = session.query(RentSchedule).filter(RentSchedule.lease_id == lease_id, RentSchedule.charge_type == "base_rent", RentSchedule.due_date >= from_date).all()
        for rs in future_base:
            rs.amount = body.new_monthly_base_rent
            rs.is_revised = 1
            rs.revision_note = body.note_for_revised_entries
            rs.updated_at = now_utc()
            updated_ids.append(rs.id)
    if body.replace_turnover_with_annual_indexed and body.annual_indexed_due_day is not None and body.annual_indexed_start_year is not None:
        year = body.annual_indexed_start_year
        due_month, due_day = body.annual_indexed_due_day.split("-")
        for y in range(year, year + 3):
            due = date.fromisoformat(f"{y}-{due_month}-{due_day}")
            if due >= from_date:
                rs = RentSchedule(
                    lease_id=lease_id,
                    charge_type="indexed_annual",
                    period_start=due,
                    period_end=due,
                    due_date=due,
                    amount=0.0,
                    currency="AUD",
                    is_generated=1,
                    is_revised=1 if body.note_for_revised_entries is not None else 0,
                    revision_note=body.note_for_revised_entries,
                    created_at=now_utc(),
                    updated_at=now_utc(),
                )
                session.add(rs)
                session.flush()
                created_ids.append(rs.id)
    session.commit()
    session.close()
    result = RecalculateRentScheduleResult(
        lease_id=lease_id,
        deleted_rent_schedule_ids=deleted_ids,
        updated_rent_schedule_ids=updated_ids,
        created_rent_schedule_ids=created_ids,
    )
    return RecalculateRentScheduleResponse(result=result)

if __name__ == "__main__":
    import uvicorn, os
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)