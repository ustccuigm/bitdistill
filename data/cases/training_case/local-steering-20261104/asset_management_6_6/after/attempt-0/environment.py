import os
from datetime import datetime, date, time
from typing import List, Optional, Dict

from fastapi import FastAPI, Query, Path, Body, Depends
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Time,
    Float,
    Text,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    func,
    and_,
    or_,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

database_url = os.getenv("DATABASE_PATH") or "sqlite:///outputs/databases/fleetio.db"
engine = create_engine("sqlite:////mnt/genming/training-local-cases-20261104/cases/asset_management_6_6/after/attempt-0/final.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Fleetio Simplified API", version="1.0.0")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    full_name = Column(String)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


Index("idx_users_email", User.email)


class Fleet(Base):
    __tablename__ = "fleets"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


Index("idx_fleets_name", Fleet.name, unique=True)


class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


Index("idx_drivers_full_name", Driver.full_name)


class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    asset_type = Column(String, nullable=False)
    vin = Column(String)
    license_plate = Column(String)
    external_asset_id = Column(String)
    make = Column(String)
    model = Column(String)
    model_year = Column(Integer)
    name = Column(String)
    status = Column(String, nullable=False, default="active")
    status_reason = Column(Text)
    acquisition_date = Column(Date)
    purchase_price = Column(Float)
    current_odometer = Column(Float)
    current_engine_hours = Column(Float)
    fuel_cost_per_mile = Column(Float)
    fleet_id = Column(Integer, ForeignKey("fleets.id"))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("asset_type IN ('vehicle','equipment')", name="ck_assets_type"),
        CheckConstraint("((asset_type = 'vehicle' AND vin IS NOT NULL) OR asset_type = 'equipment')", name="ck_assets_vehicle_vin"),
    )


Index("idx_assets_vin", Asset.vin, unique=True, sqlite_where=Asset.vin.isnot(None))
Index("idx_assets_license_plate", Asset.license_plate, unique=True, sqlite_where=Asset.license_plate.isnot(None))
Index("idx_assets_external_asset_id", Asset.external_asset_id, unique=True, sqlite_where=Asset.external_asset_id.isnot(None))
Index("idx_assets_fleet_id", Asset.fleet_id)
Index("idx_assets_status", Asset.status)


class AssetDriverAssignment(Base):
    __tablename__ = "asset_driver_assignments"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


Index("idx_asset_driver_assignments_asset", AssetDriverAssignment.asset_id)
Index("idx_asset_driver_assignments_driver", AssetDriverAssignment.driver_id)
Index("idx_asset_driver_assignments_dates", AssetDriverAssignment.asset_id, AssetDriverAssignment.start_date, AssetDriverAssignment.end_date)


class OdometerReading(Base):
    __tablename__ = "odometer_readings"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    reading_value = Column(Float, nullable=False)
    unit = Column(String, nullable=False, default="mi")
    source = Column(String, nullable=False)
    reading_at = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


Index("idx_odometer_readings_asset_time", OdometerReading.asset_id, OdometerReading.reading_at)


class FuelEntry(Base):
    __tablename__ = "fuel_entries"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    vendor_name = Column(Text)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    odometer_at_fill = Column(Float)
    unit = Column(String, nullable=False, default="gal")
    currency = Column(String, nullable=False, default="USD")
    filled_at = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


Index("idx_fuel_entries_asset_time", FuelEntry.asset_id, FuelEntry.filled_at)


class ServiceProgram(Base):
    __tablename__ = "service_programs"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


Index("idx_service_programs_name", ServiceProgram.name, unique=True)


class ServiceSchedule(Base):
    __tablename__ = "service_schedules"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    program_id = Column(Integer, ForeignKey("service_programs.id"))
    service_name = Column(Text, nullable=False)
    trigger_type = Column(String, nullable=False)
    interval_miles = Column(Float)
    interval_months = Column(Integer)
    interval_hours = Column(Float)
    start_odometer = Column(Float)
    start_engine_hours = Column(Float)
    is_active = Column(Integer, nullable=False, default=1)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("trigger_type IN ('mileage_time','engine_hours')", name="ck_service_schedules_trigger_type"),
    )


Index("idx_service_schedules_asset", ServiceSchedule.asset_id)


class ServiceReminder(Base):
    __tablename__ = "service_reminders"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("service_schedules.id"), nullable=False)
    reminder_type = Column(String, nullable=False)
    service_name = Column(Text, nullable=False)
    due_odometer = Column(Float)
    due_date = Column(Date)
    due_engine_hours = Column(Float)
    status = Column(String, nullable=False, default="open")
    triggered_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("reminder_type IN ('service')", name="ck_service_reminders_type"),
        CheckConstraint("status IN ('open','completed','dismissed')", name="ck_service_reminders_status"),
    )


Index("idx_service_reminders_asset_status", ServiceReminder.asset_id, ServiceReminder.status)
Index("idx_service_reminders_schedule", ServiceReminder.schedule_id)


class Shop(Base):
    __tablename__ = "shops"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    address = Column(Text)
    phone = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("type IN ('in_house','external')", name="ck_shops_type"),
    )


Index("idx_shops_name", Shop.name)


class WorkOrder(Base):
    __tablename__ = "work_orders"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    service_reminder_id = Column(Integer, ForeignKey("service_reminders.id"))
    title = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False)
    estimated_total_cost = Column(Float)
    actual_total_cost = Column(Float)
    opened_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("status IN ('open','in_progress','completed','closed','canceled')", name="ck_work_orders_status"),
    )


Index("idx_work_orders_asset_status", WorkOrder.asset_id, WorkOrder.status)
Index("idx_work_orders_shop", WorkOrder.shop_id)
Index("idx_work_orders_service_reminder", WorkOrder.service_reminder_id)


class WorkOrderTask(Base):
    __tablename__ = "work_order_tasks"
    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    description = Column(Text, nullable=False)
    estimated_cost = Column(Float)
    actual_cost = Column(Float)
    status = Column(String, nullable=False, default="open")
    position = Column(Integer)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("status IN ('open','in_progress','completed','canceled')", name="ck_work_order_tasks_status"),
    )


Index("idx_work_order_tasks_work_order", WorkOrderTask.work_order_id)


class InspectionChecklist(Base):
    __tablename__ = "inspection_checklists"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


Index("idx_inspection_checklists_name", InspectionChecklist.name, unique=True)


class InspectionChecklistItem(Base):
    __tablename__ = "inspection_checklist_items"
    id = Column(Integer, primary_key=True)
    checklist_id = Column(Integer, ForeignKey("inspection_checklists.id"), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    position = Column(Integer)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


Index("idx_inspection_checklist_items_checklist", InspectionChecklistItem.checklist_id)


class Inspection(Base):
    __tablename__ = "inspections"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    checklist_id = Column(Integer, ForeignKey("inspection_checklists.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    inspection_date = Column(Date, nullable=False)
    inspection_time = Column(Time)
    overall_status = Column(String, nullable=False)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("overall_status IN ('pass','fail')", name="ck_inspections_overall_status"),
    )


Index("idx_inspections_asset_date", Inspection.asset_id, Inspection.inspection_date)


class InspectionItemResult(Base):
    __tablename__ = "inspection_items_results"
    id = Column(Integer, primary_key=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    checklist_item_id = Column(Integer, ForeignKey("inspection_checklist_items.id"), nullable=False)
    status = Column(String, nullable=False)
    notes = Column(Text)
    photo_ref = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("status IN ('pass','fail','na')", name="ck_inspection_items_results_status"),
    )


Index("idx_inspection_items_results_inspection", InspectionItemResult.inspection_id)


class Issue(Base):
    __tablename__ = "issues"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    source = Column(String, nullable=False)
    source_inspection_item_result_id = Column(Integer, ForeignKey("inspection_items_results.id"))
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False)
    due_date = Column(Date)
    resolution_note = Column(Text)
    actual_cost = Column(Float)
    resolved_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("source IN ('inspection','manual','other')", name="ck_issues_source"),
        CheckConstraint("severity IN ('low','medium','high','critical')", name="ck_issues_severity"),
        CheckConstraint("status IN ('open','in_progress','resolved','closed')", name="ck_issues_status"),
    )


Index("idx_issues_asset_status", Issue.asset_id, Issue.status)
Index("idx_issues_due_date", Issue.due_date)


class IssueWorkOrderLink(Base):
    __tablename__ = "issue_work_order_links"
    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (
        UniqueConstraint("issue_id", "work_order_id", name="uq_issue_work_order"),
    )


Index("idx_issue_work_order_links_issue", IssueWorkOrderLink.issue_id)
Index("idx_issue_work_order_links_work_order", IssueWorkOrderLink.work_order_id)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    return db


class FleetModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Fleet ID", example=1)
    name: str = Field(..., description="Fleet name", example="Delivery Fleet")
    description: Optional[str] = Field(None, description="Fleet description", example="Primary delivery vehicles")
    created_by: int = Field(..., description="User ID who created the fleet", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-01T10:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example="2025-01-02T11:00:00Z")


class FleetsListResponse(BaseModel):
    fleets: List[FleetModel] = Field(..., description="List of fleets", example=[])


class FleetCreateRequest(BaseModel):
    name: str = Field(..., description="Unique fleet name", example="Delivery Fleet")
    description: Optional[str] = Field(None, description="Optional description of the fleet", example="All vans used for local deliveries")


class FleetCreateResponse(BaseModel):
    fleet: FleetModel = Field(..., description="Created fleet", example={})


class DriverModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Driver ID", example=1)
    full_name: str = Field(..., description="Driver full name", example="Maria Lopez")
    email: Optional[str] = Field(None, description="Driver email address", example="maria.lopez@example.com")
    phone: Optional[str] = Field(None, description="Driver phone number", example="+1-555-123-4567")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-01T09:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example="2025-01-02T10:00:00Z")


class DriversListResponse(BaseModel):
    drivers: List[DriverModel] = Field(..., description="List of drivers", example=[])


class DriverCreateRequest(BaseModel):
    full_name: str = Field(..., description="Driver full legal name", example="Maria Lopez")
    email: Optional[str] = Field(None, description="Driver email address", example="maria.lopez@example.com")
    phone: Optional[str] = Field(None, description="Driver phone number", example="+1-555-123-4567")


class DriverCreateResponse(BaseModel):
    driver: DriverModel = Field(..., description="Created driver", example={})


class AssetModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Asset ID", example=10)
    asset_type: str = Field(..., description="Asset type ('vehicle' or 'equipment')", example="vehicle")
    vin: Optional[str] = Field(None, description="Vehicle VIN (null for equipment)", example="1HGCM82633A004352")
    license_plate: Optional[str] = Field(None, description="License plate (vehicles only)", example="ABC-1234")
    external_asset_id: Optional[str] = Field(None, description="External asset identifier for equipment", example="FORKLIFT-001")
    make: Optional[str] = Field(None, description="Manufacturer", example="Ford")
    model: Optional[str] = Field(None, description="Model name", example="Transit 250")
    model_year: Optional[int] = Field(None, description="Model year", example=2022)
    name: Optional[str] = Field(None, description="Human-friendly asset name", example="Hyster H50 forklift")
    status: str = Field(..., description="Operational status", example="active")
    status_reason: Optional[str] = Field(None, description="Optional reason for current status", example="In maintenance")
    acquisition_date: Optional[date] = Field(None, description="Date the asset was acquired", example="2024-01-15")
    purchase_price: Optional[float] = Field(None, description="Purchase price in asset currency", example=42000.0)
    current_odometer: Optional[float] = Field(None, description="Latest known odometer reading in miles", example=75230.0)
    current_engine_hours: Optional[float] = Field(None, description="Latest known engine hours for equipment", example=1200.5)
    fuel_cost_per_mile: Optional[float] = Field(None, description="Calculated fuel cost per mile", example=0.25)
    fleet_id: Optional[int] = Field(None, description="Associated fleet ID", example=1)
    created_by: int = Field(..., description="User ID that created the asset (always 1)", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-01T10:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example="2025-01-07T09:45:00Z")


class AssetsListResponse(BaseModel):
    assets: List[AssetModel] = Field(..., description="List of assets", example=[])


class AssetCreateRequest(BaseModel):
    asset_type: str = Field(..., description="Type of asset ('vehicle' or 'equipment')", example="vehicle")
    vin: Optional[str] = Field(None, description="VIN for vehicles (required when asset_type is 'vehicle')", example="1HGCM82633A004352")
    license_plate: Optional[str] = Field(None, description="License plate for vehicles", example="ABC-1234")
    external_asset_id: Optional[str] = Field(None, description="Unique ID for equipment (e.g., internal tag)", example="FORKLIFT-001")
    make: Optional[str] = Field(None, description="Manufacturer name", example="Ford")
    model: Optional[str] = Field(None, description="Model name", example="Transit 250")
    model_year: Optional[int] = Field(None, description="Model year", example=2022)
    name: Optional[str] = Field(None, description="Display name for asset (often used for equipment)", example="Hyster H50 forklift")
    status: Optional[str] = Field("active", description="Operational status (default 'active')", example="active")
    status_reason: Optional[str] = Field(None, description="Optional reason for the status", example="New vehicle added")
    acquisition_date: Optional[date] = Field(None, description="Date asset was acquired (YYYY-MM-DD)", example="2024-12-15")
    purchase_price: Optional[float] = Field(None, description="Purchase price", example=35000.0)
    fleet_id: Optional[int] = Field(None, description="Fleet ID to associate this asset with", example=1)


class AssetCreateResponse(BaseModel):
    asset: AssetModel = Field(..., description="Created asset", example={})


class AssetUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="New operational status", example="active")
    status_reason: Optional[str] = Field(None, description="Reason for status change", example="Reactivated after inspection")
    fleet_id: Optional[int] = Field(None, description="Change associated fleet", example=1)
    current_odometer: Optional[float] = Field(None, description="Update latest odometer reading", example=75230.0)
    current_engine_hours: Optional[float] = Field(None, description="Update latest engine hours reading", example=1250.0)
    fuel_cost_per_mile: Optional[float] = Field(None, description="Update fuel cost-per-mile metric", example=0.27)


class AssetUpdateResponse(BaseModel):
    asset: AssetModel = Field(..., description="Updated asset", example={})


class BulkEquipmentAssetItem(BaseModel):
    asset_type: str = Field(..., description="Asset type (must be 'equipment')", example="equipment")
    external_asset_id: str = Field(..., description="External asset ID", example="FORKLIFT-001")
    name: Optional[str] = Field(None, description="Asset name", example="Hyster H50 forklift")
    make: Optional[str] = Field(None, description="Manufacturer", example="Hyster")
    model: Optional[str] = Field(None, description="Model", example="H50")
    acquisition_date: Optional[date] = Field(None, description="Acquisition date", example="2024-09-01")
    purchase_price: Optional[float] = Field(None, description="Purchase price", example=25000.0)
    fleet_id: Optional[int] = Field(None, description="Fleet ID", example=1)


class BulkEquipmentAssetRequest(BaseModel):
    assets: List[BulkEquipmentAssetItem] = Field(..., description="Array of equipment asset definitions", example=[])


class BulkEquipmentAssetResponse(BaseModel):
    assets: List[AssetModel] = Field(..., description="Created equipment assets", example=[])


class AssetDriverAssignmentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Assignment ID", example=5)
    asset_id: int = Field(..., description="Assigned asset ID", example=10)
    driver_id: int = Field(..., description="Assigned driver ID", example=3)
    start_date: date = Field(..., description="Start date", example="2025-01-05")
    end_date: Optional[date] = Field(None, description="End date", example="2025-01-10")
    created_by: int = Field(..., description="User ID that created assignment", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-05T09:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-05T09:00:00Z")


class AssetDriverAssignmentCreateRequest(BaseModel):
    asset_id: int = Field(..., description="Asset ID to assign to the driver", example=10)
    driver_id: int = Field(..., description="Driver ID being assigned", example=3)
    start_date: date = Field(..., description="Assignment start date (YYYY-MM-DD)", example="2025-01-05")
    end_date: Optional[date] = Field(None, description="Assignment end date (YYYY-MM-DD), nullable for open-ended", example="2025-01-10")


class AssetDriverAssignmentCreateResponse(BaseModel):
    assignment: AssetDriverAssignmentModel = Field(..., description="Created assignment", example={})


class AssetDriverAssignmentsListResponse(BaseModel):
    assignments: List[AssetDriverAssignmentModel] = Field(..., description="List of assignments", example=[])


class OdometerReadingModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Reading ID", example=100)
    asset_id: int = Field(..., description="Asset ID", example=10)
    reading_value: float = Field(..., description="Odometer value", example=75230.0)
    unit: str = Field(..., description="Unit of measurement", example="mi")
    source: str = Field(..., description="Source of reading", example="driver report")
    reading_at: datetime = Field(..., description="Reading timestamp", example="2025-01-07T09:30:00Z")
    created_by: int = Field(..., description="User ID who logged the reading", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-07T09:31:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example="2025-01-07T09:31:00Z")


class OdometerReadingCreateRequest(BaseModel):
    asset_id: int = Field(..., description="Asset ID for the reading", example=10)
    reading_value: float = Field(..., description="Odometer value in miles", example=75230.0)
    unit: Optional[str] = Field("mi", description="Unit of measurement (default 'mi')", example="mi")
    source: str = Field(..., description="Source of reading, e.g., 'driver report'", example="driver report")
    reading_at: datetime = Field(..., description="Timestamp of the reading (ISO 8601)", example="2025-01-07T09:30:00Z")


class OdometerReadingCreateAssetPart(BaseModel):
    id: int = Field(..., description="Asset ID", example=10)
    current_odometer: Optional[float] = Field(None, description="Updated current odometer value", example=75230.0)


class OdometerReadingCreateResponse(BaseModel):
    odometer_reading: OdometerReadingModel = Field(..., description="Created odometer reading", example={})
    asset: OdometerReadingCreateAssetPart = Field(..., description="Asset with updated odometer", example={})


class OdometerReadingsListResponse(BaseModel):
    odometer_readings: List[OdometerReadingModel] = Field(..., description="List of odometer readings", example=[])


class FuelEntryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Fuel entry ID", example=50)
    asset_id: int = Field(..., description="Asset ID", example=10)
    vendor_name: Optional[str] = Field(None, description="Vendor name", example="Shell Station #204")
    quantity: float = Field(..., description="Quantity purchased", example=14.5)
    unit_price: float = Field(..., description="Price per unit", example=3.65)
    total_cost: float = Field(..., description="Total cost", example=52.93)
    odometer_at_fill: Optional[float] = Field(None, description="Odometer at fill", example=75260.0)
    unit: str = Field(..., description="Fuel unit", example="gal")
    currency: str = Field(..., description="Currency code", example="USD")
    filled_at: datetime = Field(..., description="Fill timestamp", example="2025-01-07T10:00:00Z")
    created_by: int = Field(..., description="Creator user ID", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-07T10:01:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-07T10:01:00Z")


class FuelEntryCreateRequest(BaseModel):
    asset_id: int = Field(..., description="Asset ID the fuel entry belongs to", example=10)
    vendor_name: Optional[str] = Field(None, description="Name of fuel vendor or station", example="Shell Station #204")
    quantity: float = Field(..., description="Fuel quantity purchased", example=14.5)
    unit_price: float = Field(..., description="Price per unit of fuel", example=3.65)
    total_cost: Optional[float] = Field(None, description="Total fuel cost (auto-calculated if omitted)", example=52.93)
    odometer_at_fill: Optional[float] = Field(None, description="Odometer reading at fill time", example=75260.0)
    unit: Optional[str] = Field("gal", description="Fuel unit (default 'gal')", example="gal")
    currency: Optional[str] = Field("USD", description="Currency code (default 'USD')", example="USD")
    filled_at: datetime = Field(..., description="Datetime fuel was filled (ISO 8601)", example="2025-01-07T10:00:00Z")


class FuelEntryCreateResponse(BaseModel):
    fuel_entry: FuelEntryModel = Field(..., description="Created fuel entry", example={})


class FuelCostPerMileMetricResponse(BaseModel):
    asset_id: int = Field(..., description="Asset ID", example=10)
    fuel_cost_per_mile: Optional[float] = Field(None, description="Recalculated fuel cost per mile", example=0.24)
    total_fuel_cost: float = Field(..., description="Total fuel cost used in calculation", example=520.0)
    miles_driven: float = Field(..., description="Total miles driven in calculation window", example=2100.0)
    from_date: Optional[date] = Field(None, description="Effective start date used", example="2024-10-01")
    to_date: Optional[date] = Field(None, description="Effective end date used", example="2025-01-07")


class ServiceProgramModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Service program ID", example=2)
    name: str = Field(..., description="Program name", example="Standard Oil Change")
    description: Optional[str] = Field(None, description="Program description", example="Oil change and filter replacement every 5k miles")
    created_by: int = Field(..., description="Creator user ID", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-05T08:20:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-05T08:20:00Z")


class ServiceProgramCreateRequest(BaseModel):
    name: str = Field(..., description="Unique service program name", example="Standard Oil Change")
    description: Optional[str] = Field(None, description="Description of the service program", example="Oil change and filter replacement every 5k miles")


class ServiceProgramCreateResponse(BaseModel):
    service_program: ServiceProgramModel = Field(..., description="Created service program", example={})


class ServiceScheduleModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Service schedule ID", example=5)
    asset_id: int = Field(..., description="Asset ID", example=10)
    program_id: Optional[int] = Field(None, description="Service program ID", example=2)
    service_name: str = Field(..., description="Service name", example="Oil Change")
    trigger_type: str = Field(..., description="Trigger type", example="mileage_time")
    interval_miles: Optional[float] = Field(None, description="Mileage interval", example=5000.0)
    interval_months: Optional[int] = Field(None, description="Months interval", example=6)
    interval_hours: Optional[float] = Field(None, description="Hours interval", example=None)
    start_odometer: Optional[float] = Field(None, description="Start odometer", example=70000.0)
    start_engine_hours: Optional[float] = Field(None, description="Start engine hours", example=None)
    is_active: int = Field(..., description="Active flag", example=1)
    created_by: int = Field(..., description="Creator user ID", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-05T08:30:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-05T08:30:00Z")


class ServiceScheduleCreateRequest(BaseModel):
    asset_id: int = Field(..., description="Asset ID to attach this schedule to", example=10)
    program_id: Optional[int] = Field(None, description="Optional service program ID", example=2)
    service_name: str = Field(..., description="Name of the service (e.g., 'Oil Change')", example="Oil Change")
    trigger_type: str = Field(..., description="Trigger type: 'mileage_time' or 'engine_hours'", example="mileage_time")
    interval_miles: Optional[float] = Field(None, description="Mileage interval between services", example=5000.0)
    interval_months: Optional[int] = Field(None, description="Months interval between services", example=6)
    interval_hours: Optional[float] = Field(None, description="Engine hour interval for equipment schedules", example=250.0)
    start_odometer: Optional[float] = Field(None, description="Base odometer from which to start scheduling", example=70000.0)
    start_engine_hours: Optional[float] = Field(None, description="Base engine hours for equipment schedules", example=0.0)
    is_active: Optional[int] = Field(1, description="Whether the schedule is active (1) or inactive (0)", example=1)


class ServiceScheduleCreateResponse(BaseModel):
    service_schedule: ServiceScheduleModel = Field(..., description="Created service schedule", example={})


class ServiceReminderModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Service reminder ID", example=8)
    asset_id: int = Field(..., description="Asset ID", example=10)
    schedule_id: int = Field(..., description="Service schedule ID", example=5)
    reminder_type: str = Field(..., description="Reminder type (always 'service')", example="service")
    service_name: str = Field(..., description="Service name", example="Oil Change")
    due_odometer: Optional[float] = Field(None, description="Odometer at which service is due", example=75000.0)
    due_date: Optional[date] = Field(None, description="Date by which service is due", example="2025-07-07")
    due_engine_hours: Optional[float] = Field(None, description="Engine hours at which service is due", example=None)
    status: str = Field(..., description="Reminder status", example="open")
    triggered_at: Optional[datetime] = Field(None, description="When the reminder was generated", example="2025-01-07T11:00:00Z")
    completed_at: Optional[datetime] = Field(None, description="When reminder was completed", example=None)
    created_by: int = Field(..., description="Creator user ID", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-07T11:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-07T11:00:00Z")


class ServiceRemindersListResponse(BaseModel):
    service_reminders: List[ServiceReminderModel] = Field(..., description="List of service reminders", example=[])


class ServiceReminderUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="New status: 'open','completed','dismissed'", example="completed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp (ISO 8601)", example="2025-01-08T15:00:00Z")


class ServiceReminderUpdateResponse(BaseModel):
    service_reminder: ServiceReminderModel = Field(..., description="Updated service reminder", example={})


class GenerateServiceRemindersResponse(BaseModel):
    created_reminders: List[ServiceReminderModel] = Field(..., description="Created service reminders", example=[])


class ShopModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Shop ID", example=1)
    name: str = Field(..., description="Shop name", example="Main In-House Shop")
    type: str = Field(..., description="Shop type", example="in_house")
    address: Optional[str] = Field(None, description="Shop address", example="1234 Service Rd, Springfield, IL")
    phone: Optional[str] = Field(None, description="Shop phone number", example="+1-555-987-6543")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2024-12-01T08:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2024-12-15T09:00:00Z")


class ShopsListResponse(BaseModel):
    shops: List[ShopModel] = Field(..., description="List of shops", example=[])


class WorkOrderModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Work order ID", example=30)
    asset_id: int = Field(..., description="Asset ID", example=10)
    shop_id: int = Field(..., description="Shop ID", example=1)
    service_reminder_id: Optional[int] = Field(None, description="Linked service reminder ID", example=8)
    title: str = Field(..., description="Work order title", example="Oil Change - January 2025")
    description: Optional[str] = Field(None, description="Work order description", example="Perform scheduled oil and filter change.")
    status: str = Field(..., description="Work order status", example="open")
    estimated_total_cost: Optional[float] = Field(None, description="Estimated total cost", example=105.0)
    actual_total_cost: Optional[float] = Field(None, description="Actual total cost", example=None)
    opened_at: datetime = Field(..., description="Opened timestamp", example="2025-01-07T12:00:00Z")
    completed_at: Optional[datetime] = Field(None, description="Completed timestamp", example=None)
    created_by: int = Field(..., description="Creator user ID", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-07T12:01:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-07T12:01:00Z")


class WorkOrderCreateRequest(BaseModel):
    asset_id: int = Field(..., description="Asset ID the work order is for", example=10)
    shop_id: int = Field(..., description="Shop ID handling the work order", example=1)
    service_reminder_id: Optional[int] = Field(None, description="Optional linked service reminder ID", example=8)
    title: str = Field(..., description="Work order title", example="Oil Change - January 2025")
    description: Optional[str] = Field(None, description="Detailed description of work", example="Perform scheduled oil and filter change.")
    status: str = Field(..., description="Initial status: 'open','in_progress','completed','closed','canceled'", example="open")
    estimated_total_cost: Optional[float] = Field(None, description="Estimated total cost of work", example=105.0)
    opened_at: datetime = Field(..., description="Datetime the work order is opened", example="2025-01-07T12:00:00Z")


class WorkOrderCreateResponse(BaseModel):
    work_order: WorkOrderModel = Field(..., description="Created work order", example={})


class WorkOrderUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="New status", example="completed")
    estimated_total_cost: Optional[float] = Field(None, description="Updated estimated cost", example=105.0)
    actual_total_cost: Optional[float] = Field(None, description="Actual total cost after completion", example=110.0)
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp", example="2025-01-08T14:30:00Z")


class WorkOrderUpdateResponse(BaseModel):
    work_order: WorkOrderModel = Field(..., description="Updated work order", example={})


class WorkOrderTaskModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Task ID", example=101)
    work_order_id: int = Field(..., description="Work order ID", example=30)
    description: str = Field(..., description="Task description", example="Replace engine oil")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost", example=80.0)
    actual_cost: Optional[float] = Field(None, description="Actual cost", example=None)
    status: str = Field(..., description="Task status", example="open")
    position: Optional[int] = Field(None, description="Order in work order", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-07T12:02:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-07T12:02:00Z")


class WorkOrderTaskCreateRequest(BaseModel):
    work_order_id: int = Field(..., description="Work order ID this task belongs to", example=30)
    description: str = Field(..., description="Description of the maintenance task", example="Replace engine oil")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost for this task", example=80.0)
    position: Optional[int] = Field(None, description="Display order of the task in work order", example=1)


class WorkOrderTaskCreateResponse(BaseModel):
    work_order_task: WorkOrderTaskModel = Field(..., description="Created work order task", example={})


class WorkOrderTaskUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="Task status: 'open','in_progress','completed','canceled'", example="completed")
    estimated_cost: Optional[float] = Field(None, description="Updated estimated cost", example=80.0)
    actual_cost: Optional[float] = Field(None, description="Actual cost", example=90.0)
    position: Optional[int] = Field(None, description="Task position in work order", example=1)


class WorkOrderTaskUpdateResponse(BaseModel):
    work_order_task: WorkOrderTaskModel = Field(..., description="Updated work order task", example={})


class InspectionChecklistModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Checklist ID", example=1)
    name: str = Field(..., description="Checklist name", example="DOT Pre-Trip")
    description: Optional[str] = Field(None, description="Checklist description", example="Daily DOT-compliant pre-trip inspection")
    created_by: int = Field(..., description="Creator user ID", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2024-10-01T08:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2024-10-15T09:00:00Z")


class InspectionChecklistsListResponse(BaseModel):
    inspection_checklists: List[InspectionChecklistModel] = Field(..., description="List of inspection checklists", example=[])


class InspectionChecklistItemModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Checklist item ID", example=10)
    checklist_id: int = Field(..., description="Checklist ID", example=1)
    name: str = Field(..., description="Item name", example="Left rear tire tread")
    description: Optional[str] = Field(None, description="Item description", example="Check tread depth and condition of left rear tire.")
    position: Optional[int] = Field(None, description="Order of item in checklist", example=5)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2024-10-01T08:05:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2024-10-01T08:05:00Z")


class InspectionChecklistItemsListResponse(BaseModel):
    items: List[InspectionChecklistItemModel] = Field(..., description="Checklist items", example=[])


class InspectionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Inspection ID", example=40)
    asset_id: int = Field(..., description="Asset ID", example=10)
    checklist_id: int = Field(..., description="Checklist ID", example=1)
    driver_id: Optional[int] = Field(None, description="Driver ID", example=3)
    inspection_date: date = Field(..., description="Inspection date", example="2025-01-07")
    inspection_time: Optional[time] = Field(None, description="Inspection time", example="09:35:00")
    overall_status: str = Field(..., description="Overall status", example="fail")
    notes: Optional[str] = Field(None, description="Inspection notes", example="Left rear tire tread below limit.")
    created_by: int = Field(..., description="Creator user ID", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-07T09:40:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-07T09:40:00Z")


class InspectionCreateRequest(BaseModel):
    asset_id: int = Field(..., description="Inspected asset ID", example=10)
    checklist_id: int = Field(..., description="Checklist template used", example=1)
    driver_id: Optional[int] = Field(None, description="Driver who performed the inspection", example=3)
    inspection_date: date = Field(..., description="Inspection date (YYYY-MM-DD)", example="2025-01-07")
    inspection_time: Optional[time] = Field(None, description="Inspection time (HH:MM:SS)", example="09:35:00")
    overall_status: str = Field(..., description="Overall inspection status: 'pass' or 'fail'", example="fail")
    notes: Optional[str] = Field(None, description="General notes about the inspection", example="Left rear tire tread below limit.")


class InspectionCreateResponse(BaseModel):
    inspection: InspectionModel = Field(..., description="Created inspection", example={})


class InspectionItemResultModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Item result ID", example=200)
    inspection_id: int = Field(..., description="Inspection ID", example=40)
    checklist_item_id: int = Field(..., description="Checklist item ID", example=10)
    status: str = Field(..., description="Result status", example="fail")
    notes: Optional[str] = Field(None, description="Item notes", example="Tread worn below legal limit.")
    photo_ref: Optional[str] = Field(None, description="Photo reference", example="photo_2025-01-07_0935.jpg")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-07T09:41:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-07T09:41:00Z")


class InspectionItemResultCreateRequest(BaseModel):
    inspection_id: int = Field(..., description="Inspection ID this result belongs to", example=40)
    checklist_item_id: int = Field(..., description="Checklist item ID inspected", example=10)
    status: str = Field(..., description="Result: 'pass','fail','na'", example="fail")
    notes: Optional[str] = Field(None, description="Notes about this item", example="Tread worn below legal limit.")
    photo_ref: Optional[str] = Field(None, description="Reference to stored photo evidence", example="photo_2025-01-07_0935.jpg")


class InspectionItemResultCreateResponse(BaseModel):
    inspection_item_result: InspectionItemResultModel = Field(..., description="Created inspection item result", example={})


class IssueModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Issue ID", example=60)
    asset_id: int = Field(..., description="Asset ID", example=10)
    title: str = Field(..., description="Title", example="Left rear tire tread below limit")
    description: Optional[str] = Field(None, description="Description", example="Daily inspection found rear left tire below legal tread depth.")
    source: str = Field(..., description="Source", example="inspection")
    source_inspection_item_result_id: Optional[int] = Field(None, description="Linked inspection item result ID", example=200)
    severity: str = Field(..., description="Severity level", example="high")
    status: str = Field(..., description="Issue status", example="open")
    due_date: Optional[date] = Field(None, description="Due date", example="2025-01-10")
    resolution_note: Optional[str] = Field(None, description="Resolution details", example=None)
    actual_cost: Optional[float] = Field(None, description="Actual resolution cost", example=None)
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp", example=None)
    created_by: int = Field(..., description="Creator user ID", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-07T09:45:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-07T09:45:00Z")


class IssueCreateRequest(BaseModel):
    asset_id: int = Field(..., description="Asset ID the issue affects", example=10)
    title: str = Field(..., description="Short issue title", example="Left rear tire tread below limit")
    description: Optional[str] = Field(None, description="Detailed issue description", example="Daily inspection found rear left tire below legal tread depth.")
    source: str = Field(..., description="Source: 'inspection','manual','other'", example="inspection")
    source_inspection_item_result_id: Optional[int] = Field(None, description="ID of related inspection item result, if any", example=200)
    severity: str = Field(..., description="Severity: 'low','medium','high','critical'", example="high")
    status: str = Field(..., description="Initial status: 'open','in_progress','resolved','closed'", example="open")
    due_date: Optional[date] = Field(None, description="Due date to resolve issue (YYYY-MM-DD)", example="2025-01-10")


class IssueCreateResponse(BaseModel):
    issue: IssueModel = Field(..., description="Created issue", example={})


class IssueUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="New status", example="resolved")
    resolution_note: Optional[str] = Field(None, description="Note describing resolution", example="Tire replaced at Goodyear Shop #18 on 2025-01-08")
    actual_cost: Optional[float] = Field(None, description="Actual cost to resolve the issue", example=210.0)
    resolved_at: Optional[datetime] = Field(None, description="Datetime when issue was resolved", example="2025-01-08T16:00:00Z")
    due_date: Optional[date] = Field(None, description="Updated due date if not resolved", example="2025-01-10")


class IssueUpdateResponse(BaseModel):
    issue: IssueModel = Field(..., description="Updated issue", example={})


class IssueWorkOrderLinkModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Link ID", example=5)
    issue_id: int = Field(..., description="Issue ID", example=60)
    work_order_id: int = Field(..., description="Work order ID", example=30)
    created_at: Optional[datetime] = Field(None, description="Link creation timestamp", example="2025-01-08T16:05:00Z")


class IssueWorkOrderLinkCreateRequest(BaseModel):
    issue_id: int = Field(..., description="Issue ID to link", example=60)
    work_order_id: int = Field(..., description="Work order ID to link", example=30)


class IssueWorkOrderLinkCreateResponse(BaseModel):
    issue_work_order_link: IssueWorkOrderLinkModel = Field(..., description="Created issue-work order link", example={})


class FleetReportVehicleEntry(BaseModel):
    asset_id: int = Field(..., description="Vehicle asset ID", example=10)
    vin: Optional[str] = Field(None, description="Vehicle VIN", example="1HGCM82633A004352")
    license_plate: Optional[str] = Field(None, description="Vehicle license plate", example="ABC-1234")
    make: Optional[str] = Field(None, description="Make", example="Ford")
    model: Optional[str] = Field(None, description="Model", example="Transit 250")
    model_year: Optional[int] = Field(None, description="Model year", example=2022)
    total_miles_driven: float = Field(..., description="Miles driven in period (based on odometer readings)", example=3200.0)
    total_fuel_cost: float = Field(..., description="Sum of fuel total_cost in period", example=850.0)
    total_maintenance_cost: float = Field(..., description="Sum of work_order actual_total_cost in period", example=420.0)
    average_cost_per_mile: Optional[float] = Field(None, description="Average combined cost per mile (fuel + maintenance)", example=0.4)


class FleetReportResponse(BaseModel):
    fleet_name: str = Field(..., description="Reported fleet name", example="Delivery Fleet")
    from_date: date = Field(..., description="Report period start date", example="2025-10-03")
    to_date: date = Field(..., description="Report period end date", example="2025-12-31")
    vehicles: List[FleetReportVehicleEntry] = Field(..., description="Per-vehicle metrics", example=[])


@app.get(
    "/api/fleets",
    response_model=FleetsListResponse,
    summary="List fleets for current user",
    description="Retrieve all fleets created by the current authenticated user.",
    tags=["fleets"],
    operation_id="list_fleets",
)
async def list_fleets(name: Optional[str] = Query(None, description="Optional case-insensitive name filter", example="Delivery Fleet"), db: Session = Depends(get_db)) -> FleetsListResponse:
    query = db.query(Fleet).filter(Fleet.created_by == 1)
    if name is not None:
        like_pattern = f"%{name.lower()}%"
        query = query.filter(func.lower(Fleet.name).like(like_pattern))
    fleets = query.all()
    db.close()
    return FleetsListResponse(fleets=fleets)


@app.post(
    "/api/fleets",
    response_model=FleetCreateResponse,
    summary="Create a new fleet",
    description="Create a new fleet owned by the current authenticated user.",
    tags=["fleets"],
    operation_id="create_fleet",
)
async def create_fleet(body: FleetCreateRequest = Body(...), db: Session = Depends(get_db)) -> FleetCreateResponse:
    fleet = Fleet(
        name=body.name,
        description=body.description,
        created_by=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    db.close()
    return FleetCreateResponse(fleet=fleet)


@app.get(
    "/api/drivers",
    response_model=DriversListResponse,
    summary="List drivers",
    description="Retrieve all drivers with optional name filtering.",
    tags=["drivers"],
    operation_id="list_drivers",
)
async def list_drivers(full_name: Optional[str] = Query(None, description="Optional case-insensitive partial name filter", example="Maria Lopez"), db: Session = Depends(get_db)) -> DriversListResponse:
    query = db.query(Driver)
    if full_name is not None:
        like_pattern = f"%{full_name.lower()}%"
        query = query.filter(func.lower(Driver.full_name).like(like_pattern))
    drivers = query.all()
    db.close()
    return DriversListResponse(drivers=drivers)


@app.post(
    "/api/drivers",
    response_model=DriverCreateResponse,
    summary="Create a driver",
    description="Create a new driver record for assignment to assets.",
    tags=["drivers"],
    operation_id="create_driver",
)
async def create_driver(body: DriverCreateRequest = Body(...), db: Session = Depends(get_db)) -> DriverCreateResponse:
    driver = Driver(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    db.close()
    return DriverCreateResponse(driver=driver)


@app.get(
    "/api/assets",
    response_model=AssetsListResponse,
    summary="List assets",
    description="Retrieve assets for current user with optional filters.",
    tags=["assets"],
    operation_id="list_assets",
)
async def list_assets(
    asset_type: Optional[str] = Query(None, description="Filter by asset_type ('vehicle' or 'equipment')", example="vehicle"),
    fleet_name: Optional[str] = Query(None, description="Filter by associated fleet name (case-insensitive)", example="Delivery Fleet"),
    status: Optional[str] = Query(None, description="Filter by asset operational status", example="active"),
    vin: Optional[str] = Query(None, description="Filter vehicles by VIN", example="1HGCM82633A004352"),
    license_plate: Optional[str] = Query(None, description="Filter vehicles by license plate", example="ABC-1234"),
    external_asset_id: Optional[str] = Query(None, description="Filter equipment by external_asset_id", example="FORKLIFT-001"),
    db: Session = Depends(get_db),
) -> AssetsListResponse:
    query = db.query(Asset).filter(Asset.created_by == 1)
    if asset_type is not None:
        query = query.filter(Asset.asset_type == asset_type)
    if status is not None:
        query = query.filter(Asset.status == status)
    if vin is not None:
        query = query.filter(Asset.vin == vin)
    if license_plate is not None:
        query = query.filter(Asset.license_plate == license_plate)
    if external_asset_id is not None:
        query = query.filter(Asset.external_asset_id == external_asset_id)
    if fleet_name is not None:
        fleet_sub = db.query(Fleet.id).filter(Fleet.created_by == 1, func.lower(Fleet.name) == fleet_name.lower()).subquery()
        query = query.filter(Asset.fleet_id.in_(fleet_sub))
    assets = query.all()
    db.close()
    return AssetsListResponse(assets=assets)


@app.post(
    "/api/assets",
    response_model=AssetCreateResponse,
    summary="Create an asset",
    description="Create a new vehicle or equipment asset and associate it with a fleet.",
    tags=["assets"],
    operation_id="create_asset",
)
async def create_asset(body: AssetCreateRequest = Body(...), db: Session = Depends(get_db)) -> AssetCreateResponse:
    asset = Asset(
        asset_type=body.asset_type,
        vin=body.vin,
        license_plate=body.license_plate,
        external_asset_id=body.external_asset_id,
        make=body.make,
        model=body.model,
        model_year=body.model_year,
        name=body.name,
        status=body.status if body.status is not None else "active",
        status_reason=body.status_reason,
        acquisition_date=body.acquisition_date,
        purchase_price=body.purchase_price,
        current_odometer=0.0,
        current_engine_hours=0.0,
        fuel_cost_per_mile=None,
        fleet_id=body.fleet_id,
        created_by=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    db.close()
    return AssetCreateResponse(asset=asset)


@app.patch(
    "/api/assets/{asset_id}",
    response_model=AssetUpdateResponse,
    summary="Update asset fields",
    description="Partially update fields of an asset such as status, fleet, or metrics.",
    tags=["assets"],
    operation_id="update_asset",
)
async def update_asset(
    asset_id: int = Path(..., description="Asset ID to update", example=10),
    body: AssetUpdateRequest = Body(...),
    db: Session = Depends(get_db),
) -> AssetUpdateResponse:
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.created_by == 1).first()
    if body.status is not None:
        asset.status = body.status
    if body.status_reason is not None:
        asset.status_reason = body.status_reason
    if body.fleet_id is not None:
        asset.fleet_id = body.fleet_id
    if body.current_odometer is not None:
        asset.current_odometer = body.current_odometer
    if body.current_engine_hours is not None:
        asset.current_engine_hours = body.current_engine_hours
    if body.fuel_cost_per_mile is not None:
        asset.fuel_cost_per_mile = body.fuel_cost_per_mile
    asset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(asset)
    db.close()
    return AssetUpdateResponse(asset=asset)


@app.post(
    "/api/assets/bulk",
    response_model=BulkEquipmentAssetResponse,
    summary="Bulk create equipment assets",
    description="Create multiple equipment assets in one request using external_asset_id.",
    tags=["assets"],
    operation_id="bulk_create_equipment_assets",
)
async def bulk_create_equipment_assets(body: BulkEquipmentAssetRequest = Body(...), db: Session = Depends(get_db)) -> BulkEquipmentAssetResponse:
    created_assets: List[Asset] = []
    for item in body.assets:
        asset = Asset(
            asset_type=item.asset_type,
            vin=None,
            license_plate=None,
            external_asset_id=item.external_asset_id,
            make=item.make,
            model=item.model,
            model_year=None,
            name=item.name,
            status="active",
            status_reason=None,
            acquisition_date=item.acquisition_date,
            purchase_price=item.purchase_price,
            current_odometer=None,
            current_engine_hours=0.0,
            fuel_cost_per_mile=None,
            fleet_id=item.fleet_id,
            created_by=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        created_assets.append(asset)
    db.close()
    return BulkEquipmentAssetResponse(assets=created_assets)


@app.post(
    "/api/asset_driver_assignments",
    response_model=AssetDriverAssignmentCreateResponse,
    summary="Assign driver to asset",
    description="Create a new asset-driver assignment for a date range.",
    tags=["asset_driver_assignments"],
    operation_id="create_asset_driver_assignment",
)
async def create_asset_driver_assignment(body: AssetDriverAssignmentCreateRequest = Body(...), db: Session = Depends(get_db)) -> AssetDriverAssignmentCreateResponse:
    assignment = AssetDriverAssignment(
        asset_id=body.asset_id,
        driver_id=body.driver_id,
        start_date=body.start_date,
        end_date=body.end_date,
        created_by=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    db.close()
    return AssetDriverAssignmentCreateResponse(assignment=assignment)


@app.get(
    "/api/asset_driver_assignments",
    response_model=AssetDriverAssignmentsListResponse,
    summary="List asset-driver assignments",
    description="Retrieve asset-driver assignments filtered by asset, driver, or date range.",
    tags=["asset_driver_assignments"],
    operation_id="list_asset_driver_assignments",
)
async def list_asset_driver_assignments(
    asset_id: Optional[int] = Query(None, description="Filter by asset ID", example=10),
    driver_id: Optional[int] = Query(None, description="Filter by driver ID", example=3),
    start_date_from: Optional[date] = Query(None, description="Filter assignments starting on or after this date", example="2025-01-01"),
    start_date_to: Optional[date] = Query(None, description="Filter assignments starting on or before this date", example="2025-01-31"),
    db: Session = Depends(get_db),
) -> AssetDriverAssignmentsListResponse:
    query = db.query(AssetDriverAssignment)
    if asset_id is not None:
        query = query.filter(AssetDriverAssignment.asset_id == asset_id)
    if driver_id is not None:
        query = query.filter(AssetDriverAssignment.driver_id == driver_id)
    if start_date_from is not None:
        query = query.filter(AssetDriverAssignment.start_date >= start_date_from)
    if start_date_to is not None:
        query = query.filter(AssetDriverAssignment.start_date <= start_date_to)
    assignments = query.all()
    db.close()
    return AssetDriverAssignmentsListResponse(assignments=assignments)


@app.post(
    "/api/odometer_readings",
    response_model=OdometerReadingCreateResponse,
    summary="Log odometer reading",
    description="Record a new odometer reading for an asset and update its current_odometer.",
    tags=["odometer_readings"],
    operation_id="create_odometer_reading",
)
async def create_odometer_reading(body: OdometerReadingCreateRequest = Body(...), db: Session = Depends(get_db)) -> OdometerReadingCreateResponse:
    reading = OdometerReading(
        asset_id=body.asset_id,
        reading_value=body.reading_value,
        unit=body.unit if body.unit is not None else "mi",
        source=body.source,
        reading_at=body.reading_at,
        created_by=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(reading)
    asset = db.query(Asset).filter(Asset.id == body.asset_id, Asset.created_by == 1).first()
    asset.current_odometer = body.reading_value
    asset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(reading)
    db.refresh(asset)
    db.close()
    asset_part = OdometerReadingCreateAssetPart(id=asset.id, current_odometer=asset.current_odometer)
    return OdometerReadingCreateResponse(odometer_reading=reading, asset=asset_part)


@app.get(
    "/api/odometer_readings",
    response_model=OdometerReadingsListResponse,
    summary="List odometer readings",
    description="Retrieve odometer readings for an asset with optional time range filtering.",
    tags=["odometer_readings"],
    operation_id="list_odometer_readings",
)
async def list_odometer_readings(
    asset_id: int = Query(..., description="Asset ID to filter readings", example=10),
    from_ts: Optional[datetime] = Query(None, alias="from", description="Start timestamp (inclusive) for readings", example="2025-01-01T00:00:00Z"),
    to_ts: Optional[datetime] = Query(None, alias="to", description="End timestamp (inclusive) for readings", example="2025-01-31T23:59:59Z"),
    db: Session = Depends(get_db),
) -> OdometerReadingsListResponse:
    query = db.query(OdometerReading).filter(OdometerReading.asset_id == asset_id)
    if from_ts is not None:
        query = query.filter(OdometerReading.reading_at >= from_ts)
    if to_ts is not None:
        query = query.filter(OdometerReading.reading_at <= to_ts)
    readings = query.all()
    db.close()
    return OdometerReadingsListResponse(odometer_readings=readings)


@app.post(
    "/api/fuel_entries",
    response_model=FuelEntryCreateResponse,
    summary="Create fuel entry",
    description="Log a fuel purchase for an asset and optionally update fuel metrics.",
    tags=["fuel_entries"],
    operation_id="create_fuel_entry",
)
async def create_fuel_entry(body: FuelEntryCreateRequest = Body(...), db: Session = Depends(get_db)) -> FuelEntryCreateResponse:
    total_cost = body.total_cost if body.total_cost is not None else body.quantity * body.unit_price
    fuel = FuelEntry(
        asset_id=body.asset_id,
        vendor_name=body.vendor_name,
        quantity=body.quantity,
        unit_price=body.unit_price,
        total_cost=total_cost,
        odometer_at_fill=body.odometer_at_fill,
        unit=body.unit if body.unit is not None else "gal",
        currency=body.currency if body.currency is not None else "USD",
        filled_at=body.filled_at,
        created_by=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(fuel)
    db.commit()
    db.refresh(fuel)
    db.close()
    return FuelEntryCreateResponse(fuel_entry=fuel)


@app.post(
    "/api/assets/{asset_id}/metrics/fuel_cost_per_mile",
    response_model=FuelCostPerMileMetricResponse,
    summary="Recalculate fuel cost per mile",
    description="Recompute and store fuel_cost_per_mile for an asset based on entries and readings.",
    tags=["assets", "metrics"],
    operation_id="recalculate_fuel_cost_per_mile",
)
async def recalculate_fuel_cost_per_mile(
    asset_id: int = Path(..., description="Asset ID whose metric will be recalculated", example=10),
    from_date: Optional[date] = Query(None, description="Optional start date for calculation window", example="2024-10-01"),
    to_date: Optional[date] = Query(None, description="Optional end date for calculation window", example="2025-01-07"),
    db: Session = Depends(get_db),
) -> FuelCostPerMileMetricResponse:
    fuel_query = db.query(FuelEntry).filter(FuelEntry.asset_id == asset_id)
    if from_date is not None:
        fuel_query = fuel_query.filter(FuelEntry.filled_at >= datetime.combine(from_date, time.min))
    if to_date is not None:
        fuel_query = fuel_query.filter(FuelEntry.filled_at <= datetime.combine(to_date, time.max))
    fuels = fuel_query.all()
    total_fuel_cost = 0.0
    for f in fuels:
        total_fuel_cost += f.total_cost
    odo_query = db.query(OdometerReading).filter(OdometerReading.asset_id == asset_id)
    if from_date is not None:
        odo_query = odo_query.filter(OdometerReading.reading_at >= datetime.combine(from_date, time.min))
    if to_date is not None:
        odo_query = odo_query.filter(OdometerReading.reading_at <= datetime.combine(to_date, time.max))
    readings = odo_query.order_by(OdometerReading.reading_at.asc()).all()
    miles_driven = 0.0
    if len(readings) >= 2:
        miles_driven = readings[-1].reading_value - readings[0].reading_value
    fuel_cost_per_mile_value: Optional[float] = None
    if miles_driven > 0:
        fuel_cost_per_mile_value = total_fuel_cost / miles_driven
        asset = db.query(Asset).filter(Asset.id == asset_id, Asset.created_by == 1).first()
        if asset is not None:
            asset.fuel_cost_per_mile = fuel_cost_per_mile_value
            asset.updated_at = datetime.utcnow()
            db.commit()
    db.close()
    return FuelCostPerMileMetricResponse(
        asset_id=asset_id,
        fuel_cost_per_mile=fuel_cost_per_mile_value,
        total_fuel_cost=total_fuel_cost,
        miles_driven=miles_driven,
        from_date=from_date,
        to_date=to_date,
    )


@app.post(
    "/api/service_programs",
    response_model=ServiceProgramCreateResponse,
    summary="Create service program",
    description="Create a reusable service program template for grouping schedules.",
    tags=["service_programs"],
    operation_id="create_service_program",
)
async def create_service_program(body: ServiceProgramCreateRequest = Body(...), db: Session = Depends(get_db)) -> ServiceProgramCreateResponse:
    sp = ServiceProgram(
        name=body.name,
        description=body.description,
        created_by=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(sp)
    db.commit()
    db.refresh(sp)
    db.close()
    return ServiceProgramCreateResponse(service_program=sp)


@app.post(
    "/api/service_schedules",
    response_model=ServiceScheduleCreateResponse,
    summary="Create service schedule",
    description="Create a service schedule for an asset based on mileage/time or engine hours.",
    tags=["service_schedules"],
    operation_id="create_service_schedule",
)
async def create_service_schedule(body: ServiceScheduleCreateRequest = Body(...), db: Session = Depends(get_db)) -> ServiceScheduleCreateResponse:
    ss = ServiceSchedule(
        asset_id=body.asset_id,
        program_id=body.program_id,
        service_name=body.service_name,
        trigger_type=body.trigger_type,
        interval_miles=body.interval_miles,
        interval_months=body.interval_months,
        interval_hours=body.interval_hours,
        start_odometer=body.start_odometer,
        start_engine_hours=body.start_engine_hours,
        is_active=body.is_active if body.is_active is not None else 1,
        created_by=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(ss)
    db.commit()
    db.refresh(ss)
    db.close()
    return ServiceScheduleCreateResponse(service_schedule=ss)


@app.post(
    "/api/service_schedules/{schedule_id}/generate_reminders",
    response_model=GenerateServiceRemindersResponse,
    summary="Generate service reminders",
    description="Generate due service_reminders for a schedule based on current metrics.",
    tags=["service_schedules", "service_reminders"],
    operation_id="generate_service_reminders_for_schedule",
)
async def generate_service_reminders_for_schedule(
    schedule_id: int = Path(..., description="Service schedule ID to generate reminders for", example=5),
    as_of_date: Optional[date] = Query(None, description="Logical 'today' date for due_date calculations (YYYY-MM-DD)", example="2025-01-07"),
    db: Session = Depends(get_db),
) -> GenerateServiceRemindersResponse:
    schedule = db.query(ServiceSchedule).filter(ServiceSchedule.id == schedule_id).first()
    asset = db.query(Asset).filter(Asset.id == schedule.asset_id).first()
    today = as_of_date if as_of_date is not None else date.today()
    due_odometer_val: Optional[float] = None
    due_date_val: Optional[date] = None
    due_engine_hours_val: Optional[float] = None
    if schedule.trigger_type == "mileage_time":
        if schedule.start_odometer is not None and schedule.interval_miles is not None:
            due_odometer_val = schedule.start_odometer + schedule.interval_miles
        if schedule.interval_months is not None:
            month = today.month + schedule.interval_months
            year = today.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            day = min(today.day, 28)
            due_date_val = date(year, month, day)
    else:
        if schedule.start_engine_hours is not None and schedule.interval_hours is not None:
            due_engine_hours_val = schedule.start_engine_hours + schedule.interval_hours
    reminder = ServiceReminder(
        asset_id=schedule.asset_id,
        schedule_id=schedule.id,
        reminder_type="service",
        service_name=schedule.service_name,
        due_odometer=due_odometer_val,
        due_date=due_date_val,
        due_engine_hours=due_engine_hours_val,
        status="open",
        triggered_at=datetime.utcnow(),
        completed_at=None,
        created_by=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    db.close()
    return GenerateServiceRemindersResponse(created_reminders=[reminder])


@app.get(
    "/api/service_reminders",
    response_model=ServiceRemindersListResponse,
    summary="List service reminders",
    description="Retrieve service reminders filtered by asset, schedule, or status.",
    tags=["service_reminders"],
    operation_id="list_service_reminders",
)
async def list_service_reminders(
    asset_id: Optional[int] = Query(None, description="Filter reminders by asset ID", example=10),
    schedule_id: Optional[int] = Query(None, description="Filter reminders by schedule ID", example=5),
    status: Optional[str] = Query(None, description="Filter by status: 'open','completed','dismissed'", example="open"),
    db: Session = Depends(get_db),
) -> ServiceRemindersListResponse:
    query = db.query(ServiceReminder)
    if asset_id is not None:
        query = query.filter(ServiceReminder.asset_id == asset_id)
    if schedule_id is not None:
        query = query.filter(ServiceReminder.schedule_id == schedule_id)
    if status is not None:
        query = query.filter(ServiceReminder.status == status)
    reminders = query.all()
    db.close()
    return ServiceRemindersListResponse(service_reminders=reminders)


@app.patch(
    "/api/service_reminders/{reminder_id}",
    response_model=ServiceReminderUpdateResponse,
    summary="Update service reminder status",
    description="Partially update a service reminder, typically to mark it completed or dismissed.",
    tags=["service_reminders"],
    operation_id="update_service_reminder",
)
async def update_service_reminder(
    reminder_id: int = Path(..., description="Service reminder ID to update", example=8),
    body: ServiceReminderUpdateRequest = Body(...),
    db: Session = Depends(get_db),
) -> ServiceReminderUpdateResponse:
    reminder = db.query(ServiceReminder).filter(ServiceReminder.id == reminder_id).first()
    if body.status is not None:
        reminder.status = body.status
    if body.completed_at is not None:
        reminder.completed_at = body.completed_at
    reminder.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(reminder)
    db.close()
    return ServiceReminderUpdateResponse(service_reminder=reminder)


@app.get(
    "/api/shops",
    response_model=ShopsListResponse,
    summary="List shops",
    description="Retrieve all in-house and external shops available for work orders.",
    tags=["shops"],
    operation_id="list_shops",
)
async def list_shops(
    name: Optional[str] = Query(None, description="Optional case-insensitive partial name filter", example="Goodyear"),
    type: Optional[str] = Query(None, description="Filter by shop type: 'in_house' or 'external'", example="in_house"),
    db: Session = Depends(get_db),
) -> ShopsListResponse:
    query = db.query(Shop)
    if name is not None:
        like_pattern = f"%{name.lower()}%"
        query = query.filter(func.lower(Shop.name).like(like_pattern))
    if type is not None:
        query = query.filter(Shop.type == type)
    shops = query.all()
    db.close()
    return ShopsListResponse(shops=shops)


@app.post(
    "/api/work_orders",
    response_model=WorkOrderCreateResponse,
    summary="Create work order",
    description="Create a new work_order for an asset, optionally linked to a service reminder.",
    tags=["work_orders"],
    operation_id="create_work_order",
)
async def create_work_order(body: WorkOrderCreateRequest = Body(...), db: Session = Depends(get_db)) -> WorkOrderCreateResponse:
    wo = WorkOrder(
        asset_id=body.asset_id,
        shop_id=body.shop_id,
        service_reminder_id=body.service_reminder_id,
        title=body.title,
        description=body.description,
        status=body.status,
        estimated_total_cost=body.estimated_total_cost,
        actual_total_cost=None,
        opened_at=body.opened_at,
        completed_at=None,
        created_by=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(wo)
    db.commit()
    db.refresh(wo)
    db.close()
    return WorkOrderCreateResponse(work_order=wo)


@app.patch(
    "/api/work_orders/{work_order_id}",
    response_model=WorkOrderUpdateResponse,
    summary="Update work order",
    description="Partially update a work order such as status, costs, or completion time.",
    tags=["work_orders"],
    operation_id="update_work_order",
)
async def update_work_order(
    work_order_id: int = Path(..., description="Work order ID to update", example=30),
    body: WorkOrderUpdateRequest = Body(...),
    db: Session = Depends(get_db),
) -> WorkOrderUpdateResponse:
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if body.status is not None:
        wo.status = body.status
    if body.estimated_total_cost is not None:
        wo.estimated_total_cost = body.estimated_total_cost
    if body.actual_total_cost is not None:
        wo.actual_total_cost = body.actual_total_cost
    if body.completed_at is not None:
        wo.completed_at = body.completed_at
    wo.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(wo)
    db.close()
    return WorkOrderUpdateResponse(work_order=wo)


@app.post(
    "/api/work_order_tasks",
    response_model=WorkOrderTaskCreateResponse,
    summary="Add task to work order",
    description="Create a new work_order_task line item under a work order.",
    tags=["work_order_tasks"],
    operation_id="create_work_order_task",
)
async def create_work_order_task(body: WorkOrderTaskCreateRequest = Body(...), db: Session = Depends(get_db)) -> WorkOrderTaskCreateResponse:
    task = WorkOrderTask(
        work_order_id=body.work_order_id,
        description=body.description,
        estimated_cost=body.estimated_cost,
        actual_cost=None,
        status="open",
        position=body.position,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    db.close()
    return WorkOrderTaskCreateResponse(work_order_task=task)


@app.patch(
    "/api/work_order_tasks/{task_id}",
    response_model=WorkOrderTaskUpdateResponse,
    summary="Update work order task",
    description="Partially update a work order task status, costs, or position.",
    tags=["work_order_tasks"],
    operation_id="update_work_order_task",
)
async def update_work_order_task(
    task_id: int = Path(..., description="Work order task ID", example=101),
    body: WorkOrderTaskUpdateRequest = Body(...),
    db: Session = Depends(get_db),
) -> WorkOrderTaskUpdateResponse:
    task = db.query(WorkOrderTask).filter(WorkOrderTask.id == task_id).first()
    if body.status is not None:
        task.status = body.status
    if body.estimated_cost is not None:
        task.estimated_cost = body.estimated_cost
    if body.actual_cost is not None:
        task.actual_cost = body.actual_cost
    if body.position is not None:
        task.position = body.position
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    db.close()
    return WorkOrderTaskUpdateResponse(work_order_task=task)


@app.get(
    "/api/inspection_checklists",
    response_model=InspectionChecklistsListResponse,
    summary="List inspection checklists",
    description="Retrieve inspection checklist templates including DOT pre-trip lists.",
    tags=["inspection_checklists"],
    operation_id="list_inspection_checklists",
)
async def list_inspection_checklists(
    name: Optional[str] = Query(None, description="Optional exact name filter", example="DOT Pre-Trip"),
    db: Session = Depends(get_db),
) -> InspectionChecklistsListResponse:
    query = db.query(InspectionChecklist)
    if name is not None:
        query = query.filter(InspectionChecklist.name == name)
    checklists = query.all()
    db.close()
    return InspectionChecklistsListResponse(inspection_checklists=checklists)


@app.get(
    "/api/inspection_checklists/{checklist_id}/items",
    response_model=InspectionChecklistItemsListResponse,
    summary="List items for checklist",
    description="Retrieve inspection_checklist_items for a given checklist to submit inspection results.",
    tags=["inspection_checklists"],
    operation_id="list_inspection_checklist_items",
)
async def list_inspection_checklist_items(
    checklist_id: int = Path(..., description="Checklist ID whose items to retrieve", example=1),
    db: Session = Depends(get_db),
) -> InspectionChecklistItemsListResponse:
    items = db.query(InspectionChecklistItem).filter(InspectionChecklistItem.checklist_id == checklist_id).all()
    db.close()
    return InspectionChecklistItemsListResponse(items=items)


@app.post(
    "/api/inspections",
    response_model=InspectionCreateResponse,
    summary="Create inspection",
    description="Create an inspection header record for an asset using a specific checklist.",
    tags=["inspections"],
    operation_id="create_inspection",
)
async def create_inspection(body: InspectionCreateRequest = Body(...), db: Session = Depends(get_db)) -> InspectionCreateResponse:
    insp = Inspection(
        asset_id=body.asset_id,
        checklist_id=body.checklist_id,
        driver_id=body.driver_id,
        inspection_date=body.inspection_date,
        inspection_time=body.inspection_time,
        overall_status=body.overall_status,
        notes=body.notes,
        created_by=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(insp)
    db.commit()
    db.refresh(insp)
    db.close()
    return InspectionCreateResponse(inspection=insp)


@app.post(
    "/api/inspection_items_results",
    response_model=InspectionItemResultCreateResponse,
    summary="Create inspection item result",
    description="Record the result for a single inspection_checklist_item under an inspection.",
    tags=["inspections"],
    operation_id="create_inspection_item_result",
)
async def create_inspection_item_result(body: InspectionItemResultCreateRequest = Body(...), db: Session = Depends(get_db)) -> InspectionItemResultCreateResponse:
    res = InspectionItemResult(
        inspection_id=body.inspection_id,
        checklist_item_id=body.checklist_item_id,
        status=body.status,
        notes=body.notes,
        photo_ref=body.photo_ref,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    db.close()
    return InspectionItemResultCreateResponse(inspection_item_result=res)


@app.post(
    "/api/issues",
    response_model=IssueCreateResponse,
    summary="Create issue",
    description="Create an issue for an asset, optionally linked to an inspection item result.",
    tags=["issues"],
    operation_id="create_issue",
)
async def create_issue(body: IssueCreateRequest = Body(...), db: Session = Depends(get_db)) -> IssueCreateResponse:
    issue = Issue(
        asset_id=body.asset_id,
        title=body.title,
        description=body.description,
        source=body.source,
        source_inspection_item_result_id=body.source_inspection_item_result_id,
        severity=body.severity,
        status=body.status,
        due_date=body.due_date,
        resolution_note=None,
        actual_cost=None,
        resolved_at=None,
        created_by=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    db.close()
    return IssueCreateResponse(issue=issue)


@app.patch(
    "/api/issues/{issue_id}",
    response_model=IssueUpdateResponse,
    summary="Update issue",
    description="Update issue fields like status, resolution_note, actual_cost, or resolved_at.",
    tags=["issues"],
    operation_id="update_issue",
)
async def update_issue(
    issue_id: int = Path(..., description="Issue ID to update", example=60),
    body: IssueUpdateRequest = Body(...),
    db: Session = Depends(get_db),
) -> IssueUpdateResponse:
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if body.status is not None:
        issue.status = body.status
    if body.resolution_note is not None:
        issue.resolution_note = body.resolution_note
    if body.actual_cost is not None:
        issue.actual_cost = body.actual_cost
    if body.resolved_at is not None:
        issue.resolved_at = body.resolved_at
    if body.due_date is not None:
        issue.due_date = body.due_date
    issue.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(issue)
    db.close()
    return IssueUpdateResponse(issue=issue)


@app.post(
    "/api/issue_work_order_links",
    response_model=IssueWorkOrderLinkCreateResponse,
    summary="Link issue to work order",
    description="Create a link between an issue and a work order for traceability.",
    tags=["issues", "work_orders"],
    operation_id="create_issue_work_order_link",
)
async def create_issue_work_order_link(body: IssueWorkOrderLinkCreateRequest = Body(...), db: Session = Depends(get_db)) -> IssueWorkOrderLinkCreateResponse:
    link = IssueWorkOrderLink(
        issue_id=body.issue_id,
        work_order_id=body.work_order_id,
        created_at=datetime.utcnow(),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    db.close()
    return IssueWorkOrderLinkCreateResponse(issue_work_order_link=link)


@app.get(
    "/api/reports/fleet_utilization_maintenance",
    response_model=FleetReportResponse,
    summary="Fleet utilization and maintenance cost report",
    description="Compute miles, fuel cost, maintenance cost, and cost per mile for vehicles.",
    tags=["reports"],
    operation_id="report_fleet_utilization_maintenance",
)
async def report_fleet_utilization_maintenance(
    fleet_name: str = Query(..., description="Fleet name to report on", example="Delivery Fleet"),
    from_date: date = Query(..., description="Start date (YYYY-MM-DD) inclusive", example="2025-10-03"),
    to_date: date = Query(..., description="End date (YYYY-MM-DD) inclusive", example="2025-12-31"),
    db: Session = Depends(get_db),
) -> FleetReportResponse:
    fleet = db.query(Fleet).filter(Fleet.name == fleet_name, Fleet.created_by == 1).first()
    vehicles = db.query(Asset).filter(Asset.fleet_id == fleet.id, Asset.asset_type == "vehicle").all()
    vehicle_entries: List[FleetReportVehicleEntry] = []
    for v in vehicles:
        odo_q = db.query(OdometerReading).filter(
            OdometerReading.asset_id == v.id,
            OdometerReading.reading_at >= datetime.combine(from_date, time.min),
            OdometerReading.reading_at <= datetime.combine(to_date, time.max),
        ).order_by(OdometerReading.reading_at.asc())
        odo_readings = odo_q.all()
        total_miles = 0.0
        if len(odo_readings) >= 2:
            total_miles = odo_readings[-1].reading_value - odo_readings[0].reading_value
        fuel_q = db.query(FuelEntry).filter(
            FuelEntry.asset_id == v.id,
            FuelEntry.filled_at >= datetime.combine(from_date, time.min),
            FuelEntry.filled_at <= datetime.combine(to_date, time.max),
        )
        fuels = fuel_q.all()
        total_fuel_cost = 0.0
        for f in fuels:
            total_fuel_cost += f.total_cost
        wo_q = db.query(WorkOrder).filter(
            WorkOrder.asset_id == v.id,
            WorkOrder.opened_at >= datetime.combine(from_date, time.min),
            WorkOrder.opened_at <= datetime.combine(to_date, time.max),
            WorkOrder.status.in_(["completed", "closed"]),
        )
        wos = wo_q.all()
        total_maintenance_cost = 0.0
        for w in wos:
            if w.actual_total_cost is not None:
                total_maintenance_cost += w.actual_total_cost
        avg_cost_per_mile: Optional[float] = None
        if total_miles > 0:
            avg_cost_per_mile = (total_fuel_cost + total_maintenance_cost) / total_miles
        entry = FleetReportVehicleEntry(
            asset_id=v.id,
            vin=v.vin,
            license_plate=v.license_plate,
            make=v.make,
            model=v.model,
            model_year=v.model_year,
            total_miles_driven=total_miles,
            total_fuel_cost=total_fuel_cost,
            total_maintenance_cost=total_maintenance_cost,
            average_cost_per_mile=avg_cost_per_mile,
        )
        vehicle_entries.append(entry)
    db.close()
    return FleetReportResponse(fleet_name=fleet_name, from_date=from_date, to_date=to_date, vehicles=vehicle_entries)


if __name__ == "__main__":
    import uvicorn, os as _os
    host = _os.getenv("HOST", "127.0.0.1")
    port = int(_os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)