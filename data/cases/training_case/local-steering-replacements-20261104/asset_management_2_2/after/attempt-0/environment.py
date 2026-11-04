from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Date,
    ForeignKey,
    Text,
    Float,
    LargeBinary,
    UniqueConstraint,
    Index,
    and_,
    or_,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, date
import base64
import csv
import io
import os

database_url = os.getenv("DATABASE_PATH", "sqlite:///outputs/databases/asset_panda.db")

engine = create_engine("sqlite:////mnt/genming/training-replacement-rerun-20261104/cases/asset_management_2_2/after/attempt-0/final.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String)
    profile_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class UserGroup(Base):
    __tablename__ = "user_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class UserGroupMembership(Base):
    __tablename__ = "user_group_memberships"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("user_groups.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "group_id", name="uq_user_group_memberships_user_group"),)

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("locations.id"))
    full_path = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class DepreciationPolicy(Base):
    __tablename__ = "depreciation_policies"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    method = Column(String, nullable=False)
    useful_life_years = Column(Integer, nullable=False)
    salvage_value_percent = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class CategoryDepreciationPolicy(Base):
    __tablename__ = "category_depreciation_policies"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    policy_id = Column(Integer, ForeignKey("depreciation_policies.id"), nullable=False)
    effective_from = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("category_id", "effective_from", name="uq_cat_depr_category_effective"),)

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    asset_tag = Column(String, unique=True, nullable=False, index=True)
    serial_number = Column(String, unique=True, index=True)
    name = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), index=True)
    status = Column(String, nullable=False, default="Active", index=True)
    condition = Column(String)
    assigned_user_id = Column(Integer, ForeignKey("users.id"))
    purchase_date = Column(Date)
    purchase_cost = Column(Float)
    currency = Column(String, default="USD")
    depreciation_policy_id = Column(Integer, ForeignKey("depreciation_policies.id"))
    depreciation_start_date = Column(Date)
    salvage_value = Column(Float)
    book_value = Column(Float)
    disposal_date = Column(Date)
    disposal_method = Column(String)
    disposal_reason = Column(String)
    retired_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class AssetPhoto(Base):
    __tablename__ = "asset_photos"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    file_name = Column(String)
    content_type = Column(String)
    data = Column(LargeBinary)
    is_primary = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class AssetMovement(Base):
    __tablename__ = "asset_movements"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    from_location_id = Column(Integer, ForeignKey("locations.id"))
    to_location_id = Column(Integer, ForeignKey("locations.id"))
    moved_at = Column(DateTime, nullable=False, index=True)
    reason = Column(Text)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class AssetAssignment(Base):
    __tablename__ = "asset_assignments"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"))
    to_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    project_name = Column(String)
    assigned_at = Column(DateTime, nullable=False)
    unassigned_at = Column(DateTime)
    note = Column(Text)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class AssetCheckout(Base):
    __tablename__ = "asset_checkouts"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_name = Column(String)
    checkout_location_id = Column(Integer, ForeignKey("locations.id"))
    due_date = Column(Date, index=True)
    checked_out_at = Column(DateTime, nullable=False)
    checked_in_at = Column(DateTime)
    note = Column(Text)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class MaintenanceTicket(Base):
    __tablename__ = "maintenance_tickets"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    title = Column(String)
    description = Column(Text, nullable=False)
    type = Column(String)
    priority = Column(String)
    status = Column(String, nullable=False, default="Open", index=True)
    assigned_team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    due_date = Column(Date)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    closed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class MaintenanceTicketComment(Base):
    __tablename__ = "maintenance_ticket_comments"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("maintenance_tickets.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class MaintenanceTicketAttachment(Base):
    __tablename__ = "maintenance_ticket_attachments"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("maintenance_tickets.id"), nullable=False, index=True)
    file_name = Column(String)
    content_type = Column(String)
    data = Column(LargeBinary)
    created_at = Column(DateTime, default=datetime.utcnow)

class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    ticket_id = Column(Integer, ForeignKey("maintenance_tickets.id"))
    event_type = Column(String, nullable=False)
    description = Column(Text)
    performed_by_team_id = Column(Integer, ForeignKey("teams.id"))
    performed_at = Column(DateTime, nullable=False, index=True)
    metrics_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class AssetUsageCounter(Base):
    __tablename__ = "asset_usage_counters"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    counter_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("asset_id", "counter_type", name="uq_asset_usage_counter_asset_type"),)

class AssetDepreciationHistory(Base):
    __tablename__ = "asset_depreciation_history"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False)
    method = Column(String, nullable=False)
    opening_book_value = Column(Float, nullable=False)
    depreciation_expense = Column(Float, nullable=False)
    closing_book_value = Column(Float, nullable=False)
    policy_id = Column(Integer, ForeignKey("depreciation_policies.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class WorkflowRule(Base):
    __tablename__ = "workflow_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text)
    is_active = Column(Integer, nullable=False, default=1)
    trigger_type = Column(String, nullable=False, index=True)
    config_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class WorkflowRuleAction(Base):
    __tablename__ = "workflow_rule_actions"
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("workflow_rules.id"), nullable=False, index=True)
    action_type = Column(String, nullable=False)
    config_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AssetDisposalEvent(Base):
    __tablename__ = "asset_disposal_events"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    disposal_date = Column(Date, nullable=False, index=True)
    method = Column(String, nullable=False)
    reason = Column(Text)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"))
    approval_note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Asset Panda Simplified API", version="1.0.0")

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="User ID", example=12)
    username: str = Field(..., description="Unique username", example="jsmith")
    email: str = Field(..., description="User email", example="jane.smith@company.com")
    full_name: Optional[str] = Field(None, description="Full name of the user", example="Jane Smith")
    profile_data: Optional[str] = Field(None, description="JSON-encoded profile data if present", example='{"title":"Photographer"}')
    created_at: Optional[datetime] = Field(None, description="User creation timestamp", example="2025-01-10T12:45:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last user update timestamp", example="2025-02-01T09:21:00Z")

class UsersListResponse(BaseModel):
    users: List[UserOut] = Field(..., description="List of users", example=[])

class UserGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Group ID", example=3)
    name: str = Field(..., description="Unique group name", example="Elementary School - Grade 3")
    description: Optional[str] = Field(None, description="Optional description", example="Students in Grade 3 homerooms")
    created_at: Optional[datetime] = Field(None, description="Group creation timestamp", example="2024-08-31T00:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last group update timestamp", example="2025-01-10T10:22:00Z")

class UserGroupsListResponse(BaseModel):
    groups: List[UserGroupOut] = Field(..., description="List of user groups", example=[])

class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Team ID", example=5)
    name: str = Field(..., description="Unique team name", example="IT Hardware")
    description: Optional[str] = Field(None, description="Team description", example="Handles all IT hardware repairs and preventive maintenance")
    created_at: Optional[datetime] = Field(None, description="Team creation timestamp", example="2024-01-01T00:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last team update timestamp", example="2025-01-15T10:00:00Z")

class TeamsListResponse(BaseModel):
    teams: List[TeamOut] = Field(..., description="List of teams", example=[])

class LocationCreateRequest(BaseModel):
    name: str = Field(..., description="Location short name", example="London Campus")
    parent_id: Optional[int] = Field(None, description="Parent location ID to nest under", example=10)

class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Location ID", example=101)
    name: str = Field(..., description="Location name", example="London Campus")
    parent_id: Optional[int] = Field(None, description="Parent location ID or null", example=None)
    full_path: Optional[str] = Field(None, description="Computed full path of the location", example="London Campus > Building A > Floor 1 > A1-101")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-20T09:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-20T09:00:00Z")

class LocationsListResponse(BaseModel):
    locations: List[LocationOut] = Field(..., description="List of locations", example=[])

class LocationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="New location name", example="Floor 2")
    parent_id: Optional[int] = Field(None, description="New parent location ID", example=150)

class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Category ID", example=2)
    name: str = Field(..., description="Category name", example="Laptop")
    description: Optional[str] = Field(None, description="Category description", example="Employee and shared laptops")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2024-01-01T00:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2024-06-01T00:00:00Z")

class CategoriesListResponse(BaseModel):
    categories: List[CategoryOut] = Field(..., description="List of categories", example=[])

class DepreciationPolicyCreateRequest(BaseModel):
    name: str = Field(..., description="Policy name", example="Server Hardware 5Y SL 5% salvage")
    method: str = Field(..., description="Depreciation method", example="straight_line")
    useful_life_years: int = Field(..., description="Useful life in years", example=5)
    salvage_value_percent: float = Field(..., description="Salvage value percent", example=5.0)

class DepreciationPolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Policy ID", example=4)
    name: str = Field(..., description="Policy name", example="Server Hardware 5Y SL 5% salvage")
    method: str = Field(..., description="Depreciation method", example="straight_line")
    useful_life_years: int = Field(..., description="Useful life in years", example=5)
    salvage_value_percent: float = Field(..., description="Salvage percent", example=5.0)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-22T08:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-22T08:00:00Z")

class DepreciationPoliciesListResponse(BaseModel):
    policies: List[DepreciationPolicyOut] = Field(..., description="List of depreciation policies", example=[])

class CategoryDepreciationPolicyRequest(BaseModel):
    category_id: int = Field(..., description="Category ID to assign policy", example=7)
    policy_id: int = Field(..., description="Depreciation policy ID", example=4)
    effective_from: str = Field(..., description="Effective from date (YYYY-MM-DD)", example="2023-01-01")

class CategoryDepreciationPolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Category depreciation policy row ID", example=12)
    category_id: int = Field(..., description="Category ID", example=7)
    policy_id: int = Field(..., description="Policy ID", example=4)
    effective_from: str = Field(..., description="Effective from date", example="2023-01-01")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-22T08:30:00Z")

class DepreciationRecalculateRequest(BaseModel):
    category_name: Optional[str] = Field(None, description="Filter assets by category name", example="Server Hardware")
    purchased_before: Optional[str] = Field(None, description="Filter assets purchased before this date", example="2023-01-01")
    policy_id: Optional[int] = Field(None, description="Override to use this depreciation policy ID", example=4)
    as_of_date: Optional[str] = Field(None, description="Date to calculate value as of", example="2025-01-01")

class DepreciationRecalculateAssetResult(BaseModel):
    asset_id: int = Field(..., description="Asset ID that was recalculated", example=501)
    previous_book_value: Optional[float] = Field(None, description="Book value before recalculation", example=6500.0)
    new_book_value: Optional[float] = Field(None, description="Book value after recalculation", example=5800.0)
    policy_id: Optional[int] = Field(None, description="Policy used for calculation", example=4)

class DepreciationRecalculateResponse(BaseModel):
    processed_assets: List[DepreciationRecalculateAssetResult] = Field(..., description="Processed assets list", example=[])

class AssetCreateRequest(BaseModel):
    asset_tag: str = Field(..., description="Unique asset tag", example="LAP-CHI-1024")
    serial_number: Optional[str] = Field(None, description="Serial number of the asset", example="DL7440-CH1024")
    name: Optional[str] = Field(None, description="Human-readable asset name", example="Dell Latitude 7440")
    category_name: str = Field(..., description="Category name to look up category_id", example="Laptop")
    location_full_path: Optional[str] = Field(None, description="Location full_path to set location_id", example="Chicago HQ > 12th Floor > IT Storage")
    status: Optional[str] = Field(None, description="Asset lifecycle status", example="Active")
    condition: Optional[str] = Field(None, description="Current physical condition", example="New")
    assigned_user_email: Optional[str] = Field(None, description="Email of user to assign asset to", example="john.doe@company.com")
    purchase_date: Optional[str] = Field(None, description="Purchase date (YYYY-MM-DD)", example="2025-01-15")
    purchase_cost: Optional[float] = Field(None, description="Purchase cost in currency", example=1450.0)
    currency: Optional[str] = Field(None, description="Currency code for costs", example="USD")
    notes: Optional[str] = Field(None, description="Free-form notes", example="Q1 2025 Chicago IT stock")

class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Asset ID", example=1001)
    asset_tag: str = Field(..., description="Asset tag", example="LAP-CHI-1024")
    serial_number: Optional[str] = Field(None, description="Serial number", example="DL7440-CH1024")
    name: Optional[str] = Field(None, description="Asset name", example="Dell Latitude 7440")
    category_id: int = Field(..., description="Category ID", example=2)
    location_id: Optional[int] = Field(None, description="Location ID or null", example=30)
    status: str = Field(..., description="Asset status", example="Active")
    condition: Optional[str] = Field(None, description="Condition", example="New")
    assigned_user_id: Optional[int] = Field(None, description="Assigned user ID or null", example=None)
    purchase_date: Optional[date] = Field(None, description="Purchase date", example="2025-01-15")
    purchase_cost: Optional[float] = Field(None, description="Purchase cost", example=1450.0)
    currency: Optional[str] = Field(None, description="Currency code", example="USD")
    depreciation_policy_id: Optional[int] = Field(None, description="Linked policy ID or null", example=None)
    depreciation_start_date: Optional[date] = Field(None, description="Start date of depreciation or null", example=None)
    salvage_value: Optional[float] = Field(None, description="Salvage value amount or null", example=None)
    book_value: Optional[float] = Field(None, description="Current book value or null", example=None)
    disposal_date: Optional[date] = Field(None, description="Disposal date or null", example=None)
    disposal_method: Optional[str] = Field(None, description="Disposal method or null", example=None)
    disposal_reason: Optional[str] = Field(None, description="Disposal reason or null", example=None)
    retired_at: Optional[datetime] = Field(None, description="Retirement timestamp or null", example=None)
    notes: Optional[str] = Field(None, description="Notes", example="Q1 2025 Chicago IT stock")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-15T10:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-15T10:00:00Z")

class AssetsListOut(BaseModel):
    id: int = Field(..., description="Asset ID", example=4001)
    asset_tag: str = Field(..., description="Asset tag", example="CAM-NYC-0007")
    serial_number: Optional[str] = Field(None, description="Serial number", example="SN-CAM-NYC-0007")
    name: Optional[str] = Field(None, description="Asset name", example="Canon EOS R6")
    category_id: int = Field(..., description="Category ID", example=8)
    location_id: Optional[int] = Field(None, description="Location ID", example=42)
    status: str = Field(..., description="Asset status", example="Active")
    condition: Optional[str] = Field(None, description="Condition", example="Good")
    assigned_user_id: Optional[int] = Field(None, description="Assigned user ID or null", example=None)
    purchase_date: Optional[date] = Field(None, description="Purchase date", example="2022-10-10")
    purchase_cost: Optional[float] = Field(None, description="Purchase cost", example=2400.0)
    currency: Optional[str] = Field(None, description="Currency", example="USD")
    disposal_date: Optional[date] = Field(None, description="Disposal date or null", example=None)
    retired_at: Optional[datetime] = Field(None, description="Retirement timestamp or null", example=None)

class AssetsListResponse(BaseModel):
    assets: List[AssetsListOut] = Field(..., description="List of assets", example=[])

class AssetUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="New status value", example="Retired")
    condition: Optional[str] = Field(None, description="Updated condition", example="Beyond economical repair")
    location_id: Optional[int] = Field(None, description="New location ID", example=310)
    disposal_date: Optional[str] = Field(None, description="Disposal date if disposed (YYYY-MM-DD)", example="2025-04-30")
    disposal_method: Optional[str] = Field(None, description="Method of disposal", example="E-waste recycler")
    disposal_reason: Optional[str] = Field(None, description="Reason for disposal", example="Beyond economical repair")
    retired_at: Optional[str] = Field(None, description="Timestamp when asset was retired", example="2025-04-30T09:00:00Z")
    book_value: Optional[float] = Field(None, description="Updated book value", example=0.0)
    depreciation_policy_id: Optional[int] = Field(None, description="Policy ID to link", example=4)
    depreciation_start_date: Optional[str] = Field(None, description="Date depreciation begins", example="2020-01-01")
    salvage_value: Optional[float] = Field(None, description="Salvage value amount", example=250.0)
    notes: Optional[str] = Field(None, description="Updated notes", example="Unit retired and sent to recycler.")

class AssetUpdateOut(BaseModel):
    id: int = Field(..., description="Asset ID", example=4001)
    asset_tag: str = Field(..., description="Asset tag", example="LAP-SF-0089")
    status: str = Field(..., description="Updated status", example="Retired")
    condition: Optional[str] = Field(None, description="Updated condition", example="Beyond economical repair")
    location_id: Optional[int] = Field(None, description="Location ID", example=310)
    disposal_date: Optional[date] = Field(None, description="Disposal date", example="2025-04-30")
    disposal_method: Optional[str] = Field(None, description="Disposal method", example="E-waste recycler")
    disposal_reason: Optional[str] = Field(None, description="Disposal reason", example="Beyond economical repair")
    retired_at: Optional[datetime] = Field(None, description="Retired timestamp", example="2025-04-30T09:00:00Z")
    book_value: Optional[float] = Field(None, description="Updated book value", example=0.0)
    depreciation_policy_id: Optional[int] = Field(None, description="Policy ID or null", example=4)
    depreciation_start_date: Optional[date] = Field(None, description="Depreciation start date", example="2020-01-01")
    salvage_value: Optional[float] = Field(None, description="Salvage value amount", example=250.0)
    notes: Optional[str] = Field(None, description="Notes", example="Unit retired and sent to recycler.")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-04-30T09:01:00Z")

class AssetMoveRequest(BaseModel):
    to_location_id: int = Field(..., description="Destination location ID", example=305)
    reason: Optional[str] = Field(None, description="Reason for movement", example="Moved from Temporary London Storage into A1-101")
    moved_at: Optional[str] = Field(None, description="Movement timestamp; defaults to now if omitted", example="2025-01-25T10:15:00Z")

class AssetMoveOut(BaseModel):
    movement_id: int = Field(..., description="Created asset_movements row ID", example=9001)
    asset_id: int = Field(..., description="Moved asset ID", example=5001)
    from_location_id: Optional[int] = Field(None, description="Source location ID or null", example=280)
    to_location_id: int = Field(..., description="Destination location ID", example=305)
    moved_at: datetime = Field(..., description="Movement timestamp", example="2025-01-25T10:15:00Z")
    reason: Optional[str] = Field(None, description="Movement reason", example="Moved from Temporary London Storage into A1-101")

class AssetBulkMoveRequest(BaseModel):
    from_location_full_path: str = Field(..., description="Move assets currently at this location full_path", example="Temporary London Storage")
    to_location_full_path: str = Field(..., description="Destination location full_path", example="London Campus > Building A > Floor 1 > A1-101")
    reason: Optional[str] = Field(None, description="Movement reason to record for all assets", example="New London Campus go-live; moved from temporary storage")

class AssetBulkMoveOut(BaseModel):
    moved_asset_ids: List[int] = Field(..., description="Asset IDs that were moved", example=[5100])
    movement_ids: List[int] = Field(..., description="Associated asset_movements IDs", example=[9100])
    count: int = Field(..., description="Total moved assets", example=37)

class AssetCheckoutRequest(BaseModel):
    user_email: str = Field(..., description="Email of user receiving the asset", example="jane.smith@company.com")
    project_name: Optional[str] = Field(None, description="Name of the project linked to this checkout", example="Q3 Brand Shoot")
    checkout_location_full_path: Optional[str] = Field(None, description="Location full_path where checkout occurs", example="NYC Office > Media Closet")
    due_date: Optional[str] = Field(None, description="Due date for return (YYYY-MM-DD)", example="2025-08-15")
    note: Optional[str] = Field(None, description="Additional instructions or notes", example="Return with both batteries and SD card.")
    checked_out_at: Optional[str] = Field(None, description="Checkout timestamp; defaults to now", example="2025-08-01T09:00:00Z")

class AssetCheckoutOut(BaseModel):
    checkout_id: int = Field(..., description="Created asset_checkouts ID", example=7001)
    asset_id: int = Field(..., description="Checked-out asset ID", example=4001)
    user_id: int = Field(..., description="Recipient user ID", example=34)
    project_name: Optional[str] = Field(None, description="Project name", example="Q3 Brand Shoot")
    checkout_location_id: Optional[int] = Field(None, description="Location where checkout occurred", example=80)
    due_date: Optional[date] = Field(None, description="Due date", example="2025-08-15")
    checked_out_at: datetime = Field(..., description="Checkout timestamp", example="2025-08-01T09:00:00Z")
    checked_in_at: Optional[datetime] = Field(None, description="Return timestamp if checked in", example=None)
    note: Optional[str] = Field(None, description="Checkout note", example="Return with both batteries and SD card.")

class AssetUsageCounterRequest(BaseModel):
    counter_type: str = Field(..., description="Type of usage metric", example="print_hours")
    value: float = Field(..., description="Current counter value", example=512.5)

class AssetUsageCounterOut(BaseModel):
    id: int = Field(..., description="asset_usage_counters row ID", example=3001)
    asset_id: int = Field(..., description="Asset ID", example=6001)
    counter_type: str = Field(..., description="Counter type", example="print_hours")
    value: float = Field(..., description="Counter value", example=512.5)
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-05-01T10:00:00Z")

class AssetPhotoRequest(BaseModel):
    file_name: str = Field(..., description="Original file name", example="monitor_current_photo.jpg")
    content_type: str = Field(..., description="MIME type of the image", example="image/jpeg")
    data_base64: str = Field(..., description="Base64-encoded binary image data", example="/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDA...")
    is_primary: Optional[bool] = Field(None, description="Whether this is the primary asset photo", example=True)

class AssetPhotoOut(BaseModel):
    id: int = Field(..., description="asset_photos row ID", example=1101)
    asset_id: int = Field(..., description="Asset ID", example=8001)
    file_name: Optional[str] = Field(None, description="Stored file name", example="monitor_current_photo.jpg")
    content_type: Optional[str] = Field(None, description="MIME type", example="image/jpeg")
    is_primary: bool = Field(..., description="True if primary, False otherwise", example=True)
    created_at: datetime = Field(..., description="Upload timestamp", example="2025-01-25T11:00:00Z")

class AssetMovementsListItem(BaseModel):
    id: int = Field(..., description="Movement ID", example=9100)
    asset_id: int = Field(..., description="Asset ID", example=5001)
    from_location_id: Optional[int] = Field(None, description="Original location or null", example=280)
    to_location_id: Optional[int] = Field(None, description="Destination location", example=305)
    moved_at: datetime = Field(..., description="Movement timestamp", example="2025-02-15T10:30:00Z")
    reason: Optional[str] = Field(None, description="Reason or note", example="Relocated for capacity expansion")
    created_by_user_id: Optional[int] = Field(None, description="User who recorded movement", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-02-15T10:31:00Z")

class AssetMovementsListResponse(BaseModel):
    movements: List[AssetMovementsListItem] = Field(..., description="List of asset movements", example=[])

class AssetAssignmentsListItem(BaseModel):
    id: int = Field(..., description="Assignment ID", example=1201)
    asset_id: int = Field(..., description="Asset ID", example=4001)
    from_user_id: Optional[int] = Field(None, description="User asset was transferred from or null", example=None)
    to_user_id: Optional[int] = Field(None, description="User receiving asset", example=34)
    project_name: Optional[str] = Field(None, description="Project name if provided", example="Q3 Brand Shoot")
    assigned_at: datetime = Field(..., description="Assignment timestamp", example="2025-08-01T09:00:00Z")
    unassigned_at: Optional[datetime] = Field(None, description="Unassignment timestamp or null", example=None)
    note: Optional[str] = Field(None, description="Assignment note", example="Assigned for Q3 Brand Shoot campaign")
    created_by_user_id: Optional[int] = Field(None, description="User who created the assignment record", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-08-01T09:01:00Z")

class AssetAssignmentsListResponse(BaseModel):
    assignments: List[AssetAssignmentsListItem] = Field(..., description="List of asset assignments", example=[])

class MaintenanceTicketCreateRequest(BaseModel):
    asset_id: int = Field(..., description="Asset ID for which ticket is created", example=8001)
    title: Optional[str] = Field(None, description="Short ticket title", example="Monitor flickering issue")
    description: str = Field(..., description="Detailed problem description", example="Random flickering and occasional blackout of the display.")
    type: Optional[str] = Field(None, description="Ticket type", example="Corrective")
    priority: Optional[str] = Field(None, description="Priority level", example="High")
    assigned_team_name: Optional[str] = Field(None, description="Team name to assign ticket to", example="Facilities - AV Team")
    due_date: Optional[str] = Field(None, description="Due date for resolving ticket (YYYY-MM-DD)", example="2025-02-10")

class MaintenanceTicketOut(BaseModel):
    id: int = Field(..., description="Ticket ID", example=6001)
    asset_id: int = Field(..., description="Asset ID", example=8001)
    title: Optional[str] = Field(None, description="Ticket title", example="Monitor flickering issue")
    description: str = Field(..., description="Ticket description", example="Random flickering and occasional blackout of the display.")
    type: Optional[str] = Field(None, description="Ticket type", example="Corrective")
    priority: Optional[str] = Field(None, description="Priority", example="High")
    status: str = Field(..., description="Ticket status", example="Open")
    assigned_team_id: Optional[int] = Field(None, description="Assigned team ID", example=2)
    due_date: Optional[date] = Field(None, description="Due date", example="2025-02-10")
    created_by_user_id: Optional[int] = Field(None, description="User who created ticket", example=1)
    closed_at: Optional[datetime] = Field(None, description="Closing timestamp or null", example=None)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-25T11:10:00Z")
    updated_at: datetime = Field(..., description="Update timestamp", example="2025-01-25T11:10:00Z")

class MaintenanceTicketUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Updated title", example="Monitor flickering / blackout issue")
    description: Optional[str] = Field(None, description="Updated description", example="Flickering observed more often when using HDMI input.")
    type: Optional[str] = Field(None, description="Updated ticket type", example="Corrective")
    priority: Optional[str] = Field(None, description="Updated priority", example="High")
    status: Optional[str] = Field(None, description="Updated ticket status", example="In Progress")
    assigned_team_id: Optional[int] = Field(None, description="Updated team ID", example=2)
    due_date: Optional[str] = Field(None, description="Updated due date (YYYY-MM-DD)", example="2025-02-12")
    closed_at: Optional[str] = Field(None, description="Closing timestamp if closing", example="2025-02-11T16:00:00Z")

class MaintenanceTicketUpdateOut(BaseModel):
    id: int = Field(..., description="Ticket ID", example=6001)
    status: str = Field(..., description="Updated ticket status", example="In Progress")
    priority: Optional[str] = Field(None, description="Updated priority", example="High")
    assigned_team_id: Optional[int] = Field(None, description="Updated team ID", example=2)
    due_date: Optional[date] = Field(None, description="Updated due date", example="2025-02-12")
    closed_at: Optional[datetime] = Field(None, description="Closing timestamp or null", example=None)
    updated_at: datetime = Field(..., description="Update timestamp", example="2025-02-10T09:00:00Z")

class MaintenanceTicketsListItem(BaseModel):
    id: int = Field(..., description="Ticket ID", example=6101)
    asset_id: int = Field(..., description="Asset ID", example=9001)
    title: Optional[str] = Field(None, description="Ticket title", example="iPad screen unresponsive")
    description: str = Field(..., description="Ticket description", example="Student reports the iPad screen is not responding to touch.")
    type: Optional[str] = Field(None, description="Ticket type", example="Corrective")
    priority: Optional[str] = Field(None, description="Priority", example="Medium")
    status: str = Field(..., description="Status", example="Open")
    assigned_team_id: Optional[int] = Field(None, description="Assigned team ID", example=5)
    due_date: Optional[date] = Field(None, description="Due date", example="2025-05-10")
    created_by_user_id: Optional[int] = Field(None, description="User who created ticket", example=1)
    closed_at: Optional[datetime] = Field(None, description="Closed timestamp or null", example=None)
    created_at: datetime = Field(..., description="Created timestamp", example="2025-05-05T09:30:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-05-05T09:30:00Z")

class MaintenanceTicketsListResponse(BaseModel):
    tickets: List[MaintenanceTicketsListItem] = Field(..., description="List of tickets", example=[])

class MaintenanceTicketCommentRequest(BaseModel):
    comment: str = Field(..., description="Comment text", example="Issue acknowledged by IT on 2025-05-05; diagnostics in progress.")

class MaintenanceTicketCommentOut(BaseModel):
    id: int = Field(..., description="Comment ID", example=7101)
    ticket_id: int = Field(..., description="Ticket ID", example=6101)
    user_id: Optional[int] = Field(None, description="User who added the comment", example=1)
    comment: str = Field(..., description="Comment text", example="Issue acknowledged by IT on 2025-05-05; diagnostics in progress.")
    created_at: datetime = Field(..., description="Comment creation timestamp", example="2025-05-05T10:00:00Z")

class MaintenanceTicketAttachmentRequest(BaseModel):
    file_name: str = Field(..., description="File name of attachment", example="monitor_current_photo.jpg")
    content_type: str = Field(..., description="Attachment MIME type", example="image/jpeg")
    data_base64: str = Field(..., description="Base64-encoded attachment data", example="/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDA...")

class MaintenanceTicketAttachmentOut(BaseModel):
    id: int = Field(..., description="Attachment ID", example=8101)
    ticket_id: int = Field(..., description="Ticket ID", example=6001)
    file_name: Optional[str] = Field(None, description="File name", example="monitor_current_photo.jpg")
    content_type: Optional[str] = Field(None, description="MIME type", example="image/jpeg")
    created_at: datetime = Field(..., description="Attachment creation timestamp", example="2025-01-25T11:12:00Z")

class MaintenanceEventCreateRequest(BaseModel):
    asset_id: int = Field(..., description="Asset ID that maintenance was performed on", example=6001)
    ticket_id: Optional[int] = Field(None, description="Related ticket ID if any", example=6001)
    event_type: str = Field(..., description="Type of event", example="maintenance_completed")
    description: Optional[str] = Field(None, description="Description of work performed", example="Replaced HDMI cable and updated monitor firmware.")
    performed_by_team_id: Optional[int] = Field(None, description="Team ID that performed maintenance", example=2)
    performed_at: str = Field(..., description="Timestamp of event (ISO8601)", example="2025-02-09T14:00:00Z")
    metrics_json: Optional[str] = Field(None, description="JSON string with metrics", example='{"print_hours_since_last": 100}')

class MaintenanceEventOut(BaseModel):
    id: int = Field(..., description="Maintenance event ID", example=9001)
    asset_id: int = Field(..., description="Asset ID", example=6001)
    ticket_id: Optional[int] = Field(None, description="Related ticket ID or null", example=6001)
    event_type: str = Field(..., description="Event type", example="maintenance_completed")
    description: Optional[str] = Field(None, description="Event description", example="Replaced HDMI cable and updated firmware.")
    performed_by_team_id: Optional[int] = Field(None, description="Performing team ID or null", example=2)
    performed_at: datetime = Field(..., description="Event timestamp", example="2025-02-09T14:00:00Z")
    metrics_json: Optional[str] = Field(None, description="JSON metrics string", example='{"print_hours_since_last": 100}')
    created_at: datetime = Field(..., description="Row creation timestamp", example="2025-02-09T14:01:00Z")

class WorkflowRuleCreateRequest(BaseModel):
    name: str = Field(..., description="Unique workflow rule name", example="3D Printer Preventive Maintenance 500h or 90d")
    description: Optional[str] = Field(None, description="Rule description", example="Auto-create preventive maintenance for 3D printers at 500 print hours or 90 days since last maintenance.")
    trigger_type: str = Field(..., description="Trigger type identifier used by automation engine", example="asset_usage_or_maintenance_interval")
    config_json: str = Field(..., description="JSON string with trigger configuration and filters", example='{"category_name":"3D Printer"}')
    is_active: Optional[bool] = Field(None, description="Whether rule is active", example=True)

class WorkflowRuleOut(BaseModel):
    id: int = Field(..., description="Workflow rule ID", example=1001)
    name: str = Field(..., description="Rule name", example="3D Printer Preventive Maintenance 500h or 90d")
    description: Optional[str] = Field(None, description="Rule description", example="Auto-create preventive maintenance for 3D printers at 500h or 90d.")
    is_active: bool = Field(..., description="True if active, False if inactive", example=True)
    trigger_type: str = Field(..., description="Trigger type", example="asset_usage_or_maintenance_interval")
    config_json: str = Field(..., description="Configuration JSON string", example='{"category_name":"3D Printer"}')
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-02-01T09:00:00Z")
    updated_at: datetime = Field(..., description="Update timestamp", example="2025-02-01T09:00:00Z")

class WorkflowRuleActionCreateRequest(BaseModel):
    action_type: str = Field(..., description="Type of action", example="create_maintenance_ticket")
    config_json: str = Field(..., description="JSON configuration for the action", example='{"ticket_type":"Preventive Maintenance"}')

class WorkflowRuleActionOut(BaseModel):
    id: int = Field(..., description="Workflow rule action ID", example=2001)
    rule_id: int = Field(..., description="Associated rule ID", example=1001)
    action_type: str = Field(..., description="Action type", example="create_maintenance_ticket")
    config_json: str = Field(..., description="Action configuration JSON", example='{"ticket_type":"Preventive Maintenance"}')
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-02-01T09:05:00Z")

class AssetDisposalEventCreateRequest(BaseModel):
    disposal_date: str = Field(..., description="Date of disposal (YYYY-MM-DD)", example="2025-04-30")
    method: str = Field(..., description="Disposal method", example="E-waste recycler")
    reason: Optional[str] = Field(None, description="Reason for disposal", example="Beyond economical repair")
    approved_by_user_email: Optional[str] = Field(None, description="Email of user who approved disposal", example="ops.director@company.com")
    approval_note: Optional[str] = Field(None, description="Notes regarding approval", example="Approved based on April 2025 hardware review.")

class AssetDisposalEventOut(BaseModel):
    id: int = Field(..., description="Disposal event ID", example=3001)
    asset_id: int = Field(..., description="Asset ID", example=4001)
    disposal_date: date = Field(..., description="Disposal date", example="2025-04-30")
    method: str = Field(..., description="Disposal method", example="E-waste recycler")
    reason: Optional[str] = Field(None, description="Disposal reason", example="Beyond economical repair")
    approved_by_user_id: Optional[int] = Field(None, description="User ID who approved disposal, if set", example=22)
    approval_note: Optional[str] = Field(None, description="Approval note", example="Approved based on April 2025 hardware review.")
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-04-30T10:00:00Z")

class MaintenanceTicketsBulkUpdateRequest(BaseModel):
    ticket_ids: List[int] = Field(..., description="List of ticket IDs to update", example=[6101, 6102, 6103])
    status: Optional[str] = Field(None, description="New status for all tickets", example="In Progress")
    priority: Optional[str] = Field(None, description="New priority for all tickets", example="High")
    assigned_team_id: Optional[int] = Field(None, description="New team ID for all tickets", example=5)
    due_date: Optional[str] = Field(None, description="New due date (YYYY-MM-DD) for all tickets", example="2025-05-15")

class MaintenanceTicketsBulkUpdateOut(BaseModel):
    updated_ticket_ids: List[int] = Field(..., description="Ticket IDs that were successfully updated", example=[6101])
    count: int = Field(..., description="Number of tickets updated", example=3)

class MaintenanceTicketsBulkCommentRequest(BaseModel):
    ticket_ids: List[int] = Field(..., description="Ticket IDs to comment on", example=[6101, 6102, 6103])
    comment: str = Field(..., description="Comment text to add to each ticket", example="Issue acknowledged by IT on 2025-05-05; diagnostics in progress.")

class MaintenanceTicketsBulkCommentOut(BaseModel):
    comment_ids: List[int] = Field(..., description="IDs of created comments", example=[7201])
    count: int = Field(..., description="Number of comments created", example=3)

class AuditReportEvent(BaseModel):
    event_type: str = Field(..., description="Type of event", example="movement")
    timestamp: str = Field(..., description="Event timestamp", example="2025-02-10T11:00:00Z")
    details: Dict[str, Optional[str]] = Field(..., description="Event-specific details", example={"movement_id": "9100"})

class AuditReportAsset(BaseModel):
    asset_id: int = Field(..., description="Asset ID", example=5001)
    asset_tag: str = Field(..., description="Asset tag", example="SRV-DAL-0001")
    serial_number: Optional[str] = Field(None, description="Serial number", example="SRV-DAL-0001-SN")
    current_location_id: Optional[int] = Field(None, description="Current location ID", example=210)
    current_location_full_path: Optional[str] = Field(None, description="Full path of current location", example="Dallas Data Center > Row 1 > Rack 3")
    events: List[AuditReportEvent] = Field(..., description="Events for the asset", example=[])

class AuditReportResponse(BaseModel):
    location_root: str = Field(..., description="Root location full_path used for the report", example="Dallas Data Center")
    from_date: str = Field(..., description="Start date of period", example="2025-01-01")
    to_date: str = Field(..., description="End date of period", example="2025-03-31")
    assets: List[AuditReportAsset] = Field(..., description="Assets included in the report", example=[])

class BulkImportAssetsRequest(BaseModel):
    file_name: str = Field(..., description="Name of the CSV file for reference", example="q2_onboarding_laptops.csv")
    file_content_base64: str = Field(..., description="Base64-encoded CSV file content", example="QXNzZXQgVGFnLFNlcmlhbCBOdW1iZXIsVXNlciBFbWFpbCxMb2NhdGlvbixQdXJjaGFzZSBEYXRlLENvc3QsQ29uZGl0aW9uCkxBUC1DSEktMTAyNCxETDc0NDA...")
    category_name: str = Field(..., description="Category name to assign to all imported assets", example="Laptop")
    default_status: str = Field(..., description="Status value to set on all imported assets", example="Active")
    column_mapping: Dict[str, str] = Field(..., description="Mapping of CSV column headers to asset fields", example={"Asset Tag": "asset_tag"})

class BulkImportAssetsRowError(BaseModel):
    row_number: int = Field(..., description="1-based row index in CSV (excluding header)", example=10)
    message: str = Field(..., description="Error message for this row", example="User email not found")

class BulkImportAssetsResponse(BaseModel):
    imported_count: int = Field(..., description="Number of successfully created assets", example=500)
    failed_count: int = Field(..., description="Number of rows that failed to import", example=3)
    errors: List[BulkImportAssetsRowError] = Field(..., description="Row-level errors", example=[])
    asset_ids: List[int] = Field(..., description="IDs of created assets", example=[2001])

@app.get(
    "/api/users",
    response_model=UsersListResponse,
    summary="List users by filters",
    description="Retrieve users by optional email, username, or group name filters.",
    tags=["users"],
    operation_id="list_users",
)
async def list_users(
    email: Optional[str] = Query(None, description="Filter by exact user email", example="jane.smith@company.com"),
    username: Optional[str] = Query(None, description="Filter by exact username", example="jsmith"),
    group_name: Optional[str] = Query(None, description="Filter users that belong to the given user group name", example="Elementary School - Grade 3"),
    limit: Optional[int] = Query(50, description="Max number of users to return", example=50),
    offset: Optional[int] = Query(0, description="Number of users to skip for pagination", example=0),
) -> UsersListResponse:
    session = SessionLocal()
    query = session.query(User)
    if email is not None:
        query = query.filter(User.email == email)
    if username is not None:
        query = query.filter(User.username == username)
    if group_name is not None:
        query = query.join(UserGroupMembership, User.id == UserGroupMembership.user_id).join(UserGroup, UserGroupMembership.group_id == UserGroup.id).filter(UserGroup.name == group_name)
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    users = query.all()
    session.close()
    return UsersListResponse(users=[UserOut.model_validate(u) for u in users])

@app.get(
    "/api/user-groups",
    response_model=UserGroupsListResponse,
    summary="List user groups by name",
    description="Get user groups optionally filtered by name.",
    tags=["user_groups"],
    operation_id="list_user_groups",
)
async def list_user_groups(
    name: Optional[str] = Query(None, description="Filter by exact or partial group name", example="Elementary School - Grade 3"),
    limit: Optional[int] = Query(50, description="Max number of groups to return", example=50),
    offset: Optional[int] = Query(0, description="Number of groups to skip", example=0),
) -> UserGroupsListResponse:
    session = SessionLocal()
    query = session.query(UserGroup)
    if name is not None:
        query = query.filter(UserGroup.name.like(f"%{name}%"))
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    groups = query.all()
    session.close()
    return UserGroupsListResponse(groups=[UserGroupOut.model_validate(g) for g in groups])

@app.get(
    "/api/teams",
    response_model=TeamsListResponse,
    summary="List teams by name",
    description="Retrieve teams optionally filtering by name.",
    tags=["teams"],
    operation_id="list_teams",
)
async def list_teams(
    name: Optional[str] = Query(None, description="Filter by exact or partial team name", example="Facilities - AV Team"),
    limit: Optional[int] = Query(50, description="Max number of teams to return", example=50),
    offset: Optional[int] = Query(0, description="Number of teams to skip", example=0),
) -> TeamsListResponse:
    session = SessionLocal()
    query = session.query(Team)
    if name is not None:
        query = query.filter(Team.name.like(f"%{name}%"))
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    teams = query.all()
    session.close()
    return TeamsListResponse(teams=[TeamOut.model_validate(t) for t in teams])

@app.post(
    "/api/locations",
    response_model=LocationOut,
    summary="Create a new location",
    description="Create a location with optional parent to build hierarchy.",
    tags=["locations"],
    operation_id="create_location",
)
async def create_location(
    payload: LocationCreateRequest = Body(..., description="Location create payload"),
) -> LocationOut:
    session = SessionLocal()
    parent = None
    if payload.parent_id is not None:
        parent = session.query(Location).filter(Location.id == payload.parent_id).first()
    full_path = payload.name
    if parent is not None and parent.full_path is not None:
        full_path = parent.full_path + " > " + payload.name
    now = datetime.utcnow()
    loc = Location(name=payload.name, parent_id=payload.parent_id, full_path=full_path, created_at=now, updated_at=now)
    session.add(loc)
    session.commit()
    session.refresh(loc)
    session.close()
    return LocationOut.model_validate(loc)

@app.get(
    "/api/locations",
    response_model=LocationsListResponse,
    summary="List locations with filters",
    description="Retrieve locations filtered by name or path.",
    tags=["locations"],
    operation_id="list_locations",
)
async def list_locations(
    name: Optional[str] = Query(None, description="Filter by exact or partial location name", example="Dallas Data Center"),
    full_path: Optional[str] = Query(None, description="Filter by exact full_path", example="London Campus > Building A > Floor 1 > A1-101"),
    parent_id: Optional[int] = Query(None, description="Filter by parent location ID", example=101),
    starts_with_full_path: Optional[str] = Query(None, description="Return locations whose full_path begins with this path", example="Dallas Data Center"),
    limit: Optional[int] = Query(100, description="Max locations to return", example=100),
    offset: Optional[int] = Query(0, description="Locations to skip", example=0),
) -> LocationsListResponse:
    session = SessionLocal()
    query = session.query(Location)
    if name is not None:
        query = query.filter(Location.name.like(f"%{name}%"))
    if full_path is not None:
        query = query.filter(Location.full_path == full_path)
    if parent_id is not None:
        query = query.filter(Location.parent_id == parent_id)
    if starts_with_full_path is not None:
        query = query.filter(Location.full_path.like(f"{starts_with_full_path}%"))
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    locations = query.all()
    session.close()
    return LocationsListResponse(locations=[LocationOut.model_validate(l) for l in locations])

@app.patch(
    "/api/locations/{location_id}",
    response_model=LocationOut,
    summary="Update a location",
    description="Update location name or parent for hierarchy changes.",
    tags=["locations"],
    operation_id="update_location",
)
async def update_location(
    location_id: int = Path(..., description="ID of the location to update", example=201),
    payload: LocationUpdateRequest = Body(..., description="Location update payload"),
) -> LocationOut:
    session = SessionLocal()
    loc = session.query(Location).filter(Location.id == location_id).first()
    if loc is None:
        session.close()
        return LocationOut(id=0, name="", parent_id=None, full_path=None, created_at=None, updated_at=None)
    if payload.name is not None:
        loc.name = payload.name
    if payload.parent_id is not None:
        loc.parent_id = payload.parent_id
    new_parent = None
    if loc.parent_id is not None:
        new_parent = session.query(Location).filter(Location.id == loc.parent_id).first()
    if new_parent is not None and new_parent.full_path is not None:
        loc.full_path = new_parent.full_path + " > " + loc.name
    else:
        loc.full_path = loc.name
    loc.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(loc)
    session.close()
    return LocationOut.model_validate(loc)

@app.get(
    "/api/categories",
    response_model=CategoriesListResponse,
    summary="List asset categories",
    description="Retrieve categories optionally filtered by name.",
    tags=["categories"],
    operation_id="list_categories",
)
async def list_categories(
    name: Optional[str] = Query(None, description="Filter by exact or partial category name", example="Laptop"),
    limit: Optional[int] = Query(50, description="Max categories to return", example=50),
    offset: Optional[int] = Query(0, description="Categories to skip", example=0),
) -> CategoriesListResponse:
    session = SessionLocal()
    query = session.query(Category)
    if name is not None:
        query = query.filter(Category.name.like(f"%{name}%"))
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    categories = query.all()
    session.close()
    return CategoriesListResponse(categories=[CategoryOut.model_validate(c) for c in categories])

@app.post(
    "/api/depreciation-policies",
    response_model=DepreciationPolicyOut,
    summary="Create depreciation policy",
    description="Create a depreciation policy for book value calculation.",
    tags=["depreciation"],
    operation_id="create_depreciation_policy",
)
async def create_depreciation_policy(
    payload: DepreciationPolicyCreateRequest = Body(..., description="Depreciation policy create payload"),
) -> DepreciationPolicyOut:
    session = SessionLocal()
    now = datetime.utcnow()
    policy = DepreciationPolicy(
        name=payload.name,
        method=payload.method,
        useful_life_years=payload.useful_life_years,
        salvage_value_percent=payload.salvage_value_percent,
        created_at=now,
        updated_at=now,
    )
    session.add(policy)
    session.commit()
    session.refresh(policy)
    session.close()
    return DepreciationPolicyOut.model_validate(policy)

@app.get(
    "/api/depreciation-policies",
    response_model=DepreciationPoliciesListResponse,
    summary="List depreciation policies",
    description="Retrieve depreciation policies by optional name filter.",
    tags=["depreciation"],
    operation_id="list_depreciation_policies",
)
async def list_depreciation_policies(
    name: Optional[str] = Query(None, description="Filter by exact or partial policy name", example="Server Hardware 5Y"),
) -> DepreciationPoliciesListResponse:
    session = SessionLocal()
    query = session.query(DepreciationPolicy)
    if name is not None:
        query = query.filter(DepreciationPolicy.name.like(f"%{name}%"))
    policies = query.all()
    session.close()
    return DepreciationPoliciesListResponse(policies=[DepreciationPolicyOut.model_validate(p) for p in policies])

@app.post(
    "/api/category-depreciation-policies",
    response_model=CategoryDepreciationPolicyOut,
    summary="Assign depreciation policy to category",
    description="Create or update category depreciation policy entry.",
    tags=["depreciation"],
    operation_id="assign_depreciation_policy_to_category",
)
async def assign_depreciation_policy_to_category(
    payload: CategoryDepreciationPolicyRequest = Body(..., description="Category depreciation policy payload"),
) -> CategoryDepreciationPolicyOut:
    session = SessionLocal()
    eff_date = date.fromisoformat(payload.effective_from)
    existing = (
        session.query(CategoryDepreciationPolicy)
        .filter(CategoryDepreciationPolicy.category_id == payload.category_id)
        .filter(CategoryDepreciationPolicy.effective_from == eff_date)
        .first()
    )
    now = datetime.utcnow()
    if existing is None:
        obj = CategoryDepreciationPolicy(
            category_id=payload.category_id,
            policy_id=payload.policy_id,
            effective_from=eff_date,
            created_at=now,
        )
        session.add(obj)
        session.commit()
        session.refresh(obj)
    else:
        existing.policy_id = payload.policy_id
        session.commit()
        obj = existing
    session.close()
    return CategoryDepreciationPolicyOut(
        id=obj.id,
        category_id=obj.category_id,
        policy_id=obj.policy_id,
        effective_from=obj.effective_from.isoformat(),
        created_at=obj.created_at,
    )

@app.post(
    "/api/assets/depreciation/recalculate",
    response_model=DepreciationRecalculateResponse,
    summary="Recalculate depreciation for assets",
    description="Recalculate book values and record depreciation history.",
    tags=["depreciation", "assets"],
    operation_id="recalculate_asset_depreciation",
)
async def recalculate_asset_depreciation(
    payload: DepreciationRecalculateRequest = Body(..., description="Recalculation request payload"),
) -> DepreciationRecalculateResponse:
    session = SessionLocal()
    query = session.query(Asset)
    if payload.category_name is not None:
        query = query.join(Category, Asset.category_id == Category.id).filter(Category.name == payload.category_name)
    if payload.purchased_before is not None:
        pb = date.fromisoformat(payload.purchased_before)
        query = query.filter(Asset.purchase_date != None).filter(Asset.purchase_date < pb)
    assets = query.all()
    results: List[DepreciationRecalculateAssetResult] = []
    as_of = date.today()
    if payload.as_of_date is not None:
        as_of = date.fromisoformat(payload.as_of_date)
    for asset in assets:
        prev_book = asset.book_value
        policy_id = payload.policy_id if payload.policy_id is not None else asset.depreciation_policy_id
        if policy_id is not None and asset.purchase_cost is not None and asset.purchase_date is not None:
            policy = session.query(DepreciationPolicy).filter(DepreciationPolicy.id == policy_id).first()
            if policy is not None:
                salvage_amount = asset.purchase_cost * policy.salvage_value_percent / 100.0
                life_days = policy.useful_life_years * 365
                days_used = (as_of - asset.purchase_date).days
                if days_used < 0:
                    days_used = 0
                if days_used > life_days:
                    days_used = life_days
                depreciable_base = asset.purchase_cost - salvage_amount
                per_day = depreciable_base / float(life_days) if life_days > 0 else 0.0
                new_book = asset.purchase_cost - per_day * days_used
                if new_book < salvage_amount:
                    new_book = salvage_amount
                asset.book_value = new_book
                asset.depreciation_policy_id = policy_id
                asset.depreciation_start_date = asset.purchase_date
                asset.salvage_value = salvage_amount
                hist = AssetDepreciationHistory(
                    asset_id=asset.id,
                    period_start=asset.purchase_date,
                    period_end=as_of,
                    method=policy.method,
                    opening_book_value=prev_book if prev_book is not None else asset.purchase_cost,
                    depreciation_expense=(asset.purchase_cost if asset.purchase_cost is not None else 0.0) - (new_book if new_book is not None else 0.0),
                    closing_book_value=new_book if new_book is not None else 0.0,
                    policy_id=policy_id,
                    created_at=datetime.utcnow(),
                )
                session.add(hist)
                results.append(
                    DepreciationRecalculateAssetResult(
                        asset_id=asset.id,
                        previous_book_value=prev_book,
                        new_book_value=new_book,
                        policy_id=policy_id,
                    )
                )
            else:
                results.append(
                    DepreciationRecalculateAssetResult(
                        asset_id=asset.id,
                        previous_book_value=prev_book,
                        new_book_value=prev_book,
                        policy_id=policy_id,
                    )
                )
        else:
            results.append(
                DepreciationRecalculateAssetResult(
                    asset_id=asset.id,
                    previous_book_value=prev_book,
                    new_book_value=prev_book,
                    policy_id=policy_id,
                )
            )
    session.commit()
    session.close()
    return DepreciationRecalculateResponse(processed_assets=results)

@app.post(
    "/api/assets",
    response_model=AssetOut,
    summary="Create a new asset",
    description="Create an asset record with category, location, and assignment.",
    tags=["assets"],
    operation_id="create_asset",
)
async def create_asset(
    payload: AssetCreateRequest = Body(..., description="Asset create payload"),
) -> AssetOut:
    session = SessionLocal()
    category = session.query(Category).filter(Category.name == payload.category_name).first()
    location_id = None
    if payload.location_full_path is not None:
        loc = session.query(Location).filter(Location.full_path == payload.location_full_path).first()
        if loc is not None:
            location_id = loc.id
    assigned_user_id = None
    if payload.assigned_user_email is not None:
        user = session.query(User).filter(User.email == payload.assigned_user_email).first()
        if user is not None:
            assigned_user_id = user.id
    purchase_date_val = None
    if payload.purchase_date is not None:
        purchase_date_val = date.fromisoformat(payload.purchase_date)
    now = datetime.utcnow()
    asset = Asset(
        asset_tag=payload.asset_tag,
        serial_number=payload.serial_number,
        name=payload.name,
        category_id=category.id if category is not None else 0,
        location_id=location_id,
        status=payload.status if payload.status is not None else "Active",
        condition=payload.condition,
        assigned_user_id=assigned_user_id,
        purchase_date=purchase_date_val,
        purchase_cost=payload.purchase_cost,
        currency=payload.currency if payload.currency is not None else "USD",
        depreciation_policy_id=None,
        depreciation_start_date=None,
        salvage_value=None,
        book_value=None,
        disposal_date=None,
        disposal_method=None,
        disposal_reason=None,
        retired_at=None,
        notes=payload.notes,
        created_at=now,
        updated_at=now,
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)
    session.close()
    return AssetOut.model_validate(asset)

@app.post(
    "/api/assets/bulk-import/csv",
    response_model=BulkImportAssetsResponse,
    summary="Bulk import assets from CSV",
    description="Upload CSV and map columns to asset fields to create assets.",
    tags=["assets", "bulk"],
    operation_id="bulk_import_assets_from_csv",
)
async def bulk_import_assets_from_csv(
    payload: BulkImportAssetsRequest = Body(..., description="Bulk import assets CSV payload"),
) -> BulkImportAssetsResponse:
    session = SessionLocal()
    category = session.query(Category).filter(Category.name == payload.category_name).first()
    category_id = category.id if category is not None else 0
    decoded = base64.b64decode(payload.file_content_base64)
    text = decoded.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    imported_ids: List[int] = []
    errors: List[BulkImportAssetsRowError] = []
    row_index = 0
    for row in reader:
        row_index += 1
        asset_tag_val = None
        if "asset_tag" in payload.column_mapping.values():
            for k, v in payload.column_mapping.items():
                if v == "asset_tag":
                    asset_tag_val = row.get(k, None)
        if asset_tag_val is None or asset_tag_val == "":
            errors.append(BulkImportAssetsRowError(row_number=row_index, message="Missing asset_tag"))
            continue
        serial_number_val = None
        name_val = None
        condition_val = None
        assigned_user_id = None
        location_id = None
        purchase_date_val = None
        purchase_cost_val = None
        for col_name, field_name in payload.column_mapping.items():
            value = row.get(col_name, None)
            if field_name == "serial_number":
                serial_number_val = value
            elif field_name == "name":
                name_val = value
            elif field_name == "condition":
                condition_val = value
            elif field_name == "assigned_user_email":
                if value is not None and value != "":
                    user = session.query(User).filter(User.email == value).first()
                    if user is not None:
                        assigned_user_id = user.id
                    else:
                        errors.append(BulkImportAssetsRowError(row_number=row_index, message="User email not found: " + value))
                        assigned_user_id = None
            elif field_name == "location_full_path":
                if value is not None and value != "":
                    loc = session.query(Location).filter(Location.full_path == value).first()
                    if loc is not None:
                        location_id = loc.id
            elif field_name == "purchase_date":
                if value is not None and value != "":
                    purchase_date_val = date.fromisoformat(value)
            elif field_name == "purchase_cost":
                if value is not None and value != "":
                    try:
                        purchase_cost_val = float(value)
                    except ValueError:
                        purchase_cost_val = None
        now = datetime.utcnow()
        asset = Asset(
            asset_tag=asset_tag_val,
            serial_number=serial_number_val,
            name=name_val,
            category_id=category_id,
            location_id=location_id,
            status=payload.default_status,
            condition=condition_val,
            assigned_user_id=assigned_user_id,
            purchase_date=purchase_date_val,
            purchase_cost=purchase_cost_val,
            currency="USD",
            created_at=now,
            updated_at=now,
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)
        imported_ids.append(asset.id)
    session.close()
    return BulkImportAssetsResponse(
        imported_count=len(imported_ids),
        failed_count=len(errors),
        errors=errors,
        asset_ids=imported_ids,
    )

@app.get(
    "/api/assets",
    response_model=AssetsListResponse,
    summary="List assets with filters",
    description="Retrieve assets with filters like tag, serial, category, location, and user.",
    tags=["assets"],
    operation_id="list_assets",
)
async def list_assets(
    asset_tag: Optional[str] = Query(None, description="Filter by exact asset tag", example="CAM-NYC-0007"),
    serial_number: Optional[str] = Query(None, description="Filter by exact serial number", example="MON-27UL850-0091"),
    category_name: Optional[str] = Query(None, description="Filter by category name", example="Server Hardware"),
    status: Optional[str] = Query(None, description="Filter by asset status", example="Active"),
    location_full_path: Optional[str] = Query(None, description="Filter by exact location full_path", example="Dallas Data Center"),
    location_starts_with: Optional[str] = Query(None, description="Filter assets whose location full_path starts with this string", example="Dallas Data Center"),
    assigned_user_email: Optional[str] = Query(None, description="Filter by assigned user email", example="jane.smith@company.com"),
    purchased_before: Optional[str] = Query(None, description="Filter assets purchased before this date", example="2023-01-01"),
    purchased_after: Optional[str] = Query(None, description="Filter assets purchased after this date", example="2022-01-01"),
    limit: Optional[int] = Query(100, description="Max assets to return", example=100),
    offset: Optional[int] = Query(0, description="Assets to skip", example=0),
) -> AssetsListResponse:
    session = SessionLocal()
    query = session.query(Asset)
    if asset_tag is not None:
        query = query.filter(Asset.asset_tag == asset_tag)
    if serial_number is not None:
        query = query.filter(Asset.serial_number == serial_number)
    if category_name is not None:
        query = query.join(Category, Asset.category_id == Category.id).filter(Category.name == category_name)
    if status is not None:
        query = query.filter(Asset.status == status)
    if location_full_path is not None:
        query = query.join(Location, Asset.location_id == Location.id).filter(Location.full_path == location_full_path)
    if location_starts_with is not None:
        query = query.join(Location, Asset.location_id == Location.id).filter(Location.full_path.like(f"{location_starts_with}%"))
    if assigned_user_email is not None:
        query = query.join(User, Asset.assigned_user_id == User.id).filter(User.email == assigned_user_email)
    if purchased_before is not None:
        pb = date.fromisoformat(purchased_before)
        query = query.filter(Asset.purchase_date != None).filter(Asset.purchase_date < pb)
    if purchased_after is not None:
        pa = date.fromisoformat(purchased_after)
        query = query.filter(Asset.purchase_date != None).filter(Asset.purchase_date > pa)
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    rows = query.all()
    assets_list: List[AssetsListOut] = []
    for a in rows:
        assets_list.append(
            AssetsListOut(
                id=a.id,
                asset_tag=a.asset_tag,
                serial_number=a.serial_number,
                name=a.name,
                category_id=a.category_id,
                location_id=a.location_id,
                status=a.status,
                condition=a.condition,
                assigned_user_id=a.assigned_user_id,
                purchase_date=a.purchase_date,
                purchase_cost=a.purchase_cost,
                currency=a.currency,
                disposal_date=a.disposal_date,
                retired_at=a.retired_at,
            )
        )
    session.close()
    return AssetsListResponse(assets=assets_list)

@app.patch(
    "/api/assets/{asset_id}",
    response_model=AssetUpdateOut,
    summary="Update asset core fields",
    description="Update mutable asset fields like status, condition, location, and depreciation.",
    tags=["assets"],
    operation_id="update_asset",
)
async def update_asset(
    asset_id: int = Path(..., description="Asset ID to update", example=4001),
    payload: AssetUpdateRequest = Body(..., description="Asset update payload"),
) -> AssetUpdateOut:
    session = SessionLocal()
    asset = session.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        session.close()
        return AssetUpdateOut(
            id=0,
            asset_tag="",
            status="",
            condition=None,
            location_id=None,
            disposal_date=None,
            disposal_method=None,
            disposal_reason=None,
            retired_at=None,
            book_value=None,
            depreciation_policy_id=None,
            depreciation_start_date=None,
            salvage_value=None,
            notes=None,
            updated_at=datetime.utcnow(),
        )
    if payload.status is not None:
        asset.status = payload.status
    if payload.condition is not None:
        asset.condition = payload.condition
    if payload.location_id is not None:
        asset.location_id = payload.location_id
    if payload.disposal_date is not None:
        asset.disposal_date = date.fromisoformat(payload.disposal_date)
    if payload.disposal_method is not None:
        asset.disposal_method = payload.disposal_method
    if payload.disposal_reason is not None:
        asset.disposal_reason = payload.disposal_reason
    if payload.retired_at is not None:
        asset.retired_at = datetime.fromisoformat(payload.retired_at)
    if payload.book_value is not None:
        asset.book_value = payload.book_value
    if payload.depreciation_policy_id is not None:
        asset.depreciation_policy_id = payload.depreciation_policy_id
    if payload.depreciation_start_date is not None:
        asset.depreciation_start_date = date.fromisoformat(payload.depreciation_start_date)
    if payload.salvage_value is not None:
        asset.salvage_value = payload.salvage_value
    if payload.notes is not None:
        asset.notes = payload.notes
    asset.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(asset)
    out = AssetUpdateOut(
        id=asset.id,
        asset_tag=asset.asset_tag,
        status=asset.status,
        condition=asset.condition,
        location_id=asset.location_id,
        disposal_date=asset.disposal_date,
        disposal_method=asset.disposal_method,
        disposal_reason=asset.disposal_reason,
        retired_at=asset.retired_at,
        book_value=asset.book_value,
        depreciation_policy_id=asset.depreciation_policy_id,
        depreciation_start_date=asset.depreciation_start_date,
        salvage_value=asset.salvage_value,
        notes=asset.notes,
        updated_at=asset.updated_at,
    )
    session.close()
    return out

@app.post(
    "/api/assets/{asset_id}/move",
    response_model=AssetMoveOut,
    summary="Move an asset to a new location",
    description="Record an asset_movements entry and update asset location.",
    tags=["assets", "movements"],
    operation_id="move_asset",
)
async def move_asset(
    asset_id: int = Path(..., description="ID of asset to move", example=5001),
    payload: AssetMoveRequest = Body(..., description="Asset move payload"),
) -> AssetMoveOut:
    session = SessionLocal()
    asset = session.query(Asset).filter(Asset.id == asset_id).first()
    from_location_id = None
    if asset is not None:
        from_location_id = asset.location_id
    moved_at_dt = datetime.utcnow()
    if payload.moved_at is not None:
        moved_at_dt = datetime.fromisoformat(payload.moved_at)
    move = AssetMovement(
        asset_id=asset_id,
        from_location_id=from_location_id,
        to_location_id=payload.to_location_id,
        moved_at=moved_at_dt,
        reason=payload.reason,
        created_by_user_id=1,
        created_at=datetime.utcnow(),
    )
    if asset is not None:
        asset.location_id = payload.to_location_id
    session.add(move)
    session.commit()
    session.refresh(move)
    out = AssetMoveOut(
        movement_id=move.id,
        asset_id=move.asset_id,
        from_location_id=move.from_location_id,
        to_location_id=move.to_location_id,
        moved_at=move.moved_at,
        reason=move.reason,
    )
    session.close()
    return out

@app.post(
    "/api/assets/bulk-move",
    response_model=AssetBulkMoveOut,
    summary="Bulk move assets by filters",
    description="Move multiple assets matching from and to location paths.",
    tags=["assets", "movements", "bulk"],
    operation_id="bulk_move_assets",
)
async def bulk_move_assets(
    payload: AssetBulkMoveRequest = Body(..., description="Bulk asset move payload"),
) -> AssetBulkMoveOut:
    session = SessionLocal()
    from_loc = session.query(Location).filter(Location.full_path == payload.from_location_full_path).first()
    to_loc = session.query(Location).filter(Location.full_path == payload.to_location_full_path).first()
    moved_ids: List[int] = []
    movement_ids: List[int] = []
    if from_loc is not None and to_loc is not None:
        assets = session.query(Asset).filter(Asset.location_id == from_loc.id).all()
        for asset in assets:
            moved_at_dt = datetime.utcnow()
            move = AssetMovement(
                asset_id=asset.id,
                from_location_id=asset.location_id,
                to_location_id=to_loc.id,
                moved_at=moved_at_dt,
                reason=payload.reason,
                created_by_user_id=1,
                created_at=datetime.utcnow(),
            )
            asset.location_id = to_loc.id
            session.add(move)
            session.commit()
            session.refresh(move)
            moved_ids.append(asset.id)
            movement_ids.append(move.id)
    session.close()
    return AssetBulkMoveOut(moved_asset_ids=moved_ids, movement_ids=movement_ids, count=len(moved_ids))

@app.post(
    "/api/assets/{asset_id}/checkout",
    response_model=AssetCheckoutOut,
    summary="Check out an asset to a user",
    description="Create an asset_checkouts row and associate asset to user.",
    tags=["assets", "checkouts"],
    operation_id="checkout_asset",
)
async def checkout_asset(
    asset_id: int = Path(..., description="ID of asset to check out", example=4001),
    payload: AssetCheckoutRequest = Body(..., description="Asset checkout payload"),
) -> AssetCheckoutOut:
    session = SessionLocal()
    user = session.query(User).filter(User.email == payload.user_email).first()
    user_id = user.id if user is not None else 0
    checkout_location_id = None
    if payload.checkout_location_full_path is not None:
        loc = session.query(Location).filter(Location.full_path == payload.checkout_location_full_path).first()
        if loc is not None:
            checkout_location_id = loc.id
    due_date_val = None
    if payload.due_date is not None:
        due_date_val = date.fromisoformat(payload.due_date)
    checked_out_at_dt = datetime.utcnow()
    if payload.checked_out_at is not None:
        checked_out_at_dt = datetime.fromisoformat(payload.checked_out_at)
    now = datetime.utcnow()
    checkout = AssetCheckout(
        asset_id=asset_id,
        user_id=user_id,
        project_name=payload.project_name,
        checkout_location_id=checkout_location_id,
        due_date=due_date_val,
        checked_out_at=checked_out_at_dt,
        checked_in_at=None,
        note=payload.note,
        created_by_user_id=1,
        created_at=now,
        updated_at=now,
    )
    session.add(checkout)
    session.commit()
    session.refresh(checkout)
    out = AssetCheckoutOut(
        checkout_id=checkout.id,
        asset_id=checkout.asset_id,
        user_id=checkout.user_id,
        project_name=checkout.project_name,
        checkout_location_id=checkout.checkout_location_id,
        due_date=checkout.due_date,
        checked_out_at=checkout.checked_out_at,
        checked_in_at=checkout.checked_in_at,
        note=checkout.note,
    )
    session.close()
    return out

@app.put(
    "/api/assets/{asset_id}/usage-counters",
    response_model=AssetUsageCounterOut,
    summary="Set asset usage counter",
    description="Create or update an asset usage counter entry.",
    tags=["assets", "usage"],
    operation_id="set_asset_usage_counter",
)
async def set_asset_usage_counter(
    asset_id: int = Path(..., description="Asset ID whose counter is updated", example=6001),
    payload: AssetUsageCounterRequest = Body(..., description="Usage counter payload"),
) -> AssetUsageCounterOut:
    session = SessionLocal()
    counter = (
        session.query(AssetUsageCounter)
        .filter(AssetUsageCounter.asset_id == asset_id)
        .filter(AssetUsageCounter.counter_type == payload.counter_type)
        .first()
    )
    now = datetime.utcnow()
    if counter is None:
        counter = AssetUsageCounter(
            asset_id=asset_id,
            counter_type=payload.counter_type,
            value=payload.value,
            updated_at=now,
        )
        session.add(counter)
        session.commit()
        session.refresh(counter)
    else:
        counter.value = payload.value
        counter.updated_at = now
        session.commit()
        session.refresh(counter)
    out = AssetUsageCounterOut(
        id=counter.id,
        asset_id=counter.asset_id,
        counter_type=counter.counter_type,
        value=counter.value,
        updated_at=counter.updated_at,
    )
    session.close()
    return out

@app.post(
    "/api/assets/{asset_id}/photos",
    response_model=AssetPhotoOut,
    summary="Attach a photo to an asset",
    description="Upload a photo BLOB for an asset and optionally mark as primary.",
    tags=["assets", "photos"],
    operation_id="add_asset_photo",
)
async def add_asset_photo(
    asset_id: int = Path(..., description="Asset ID to attach photo to", example=8001),
    payload: AssetPhotoRequest = Body(..., description="Asset photo payload"),
) -> AssetPhotoOut:
    session = SessionLocal()
    data_bytes = base64.b64decode(payload.data_base64)
    is_primary_int = 1 if (payload.is_primary is not None and payload.is_primary) else 0
    if is_primary_int == 1:
        existing_primary = (
            session.query(AssetPhoto)
            .filter(AssetPhoto.asset_id == asset_id)
            .filter(AssetPhoto.is_primary == 1)
            .all()
        )
        for ep in existing_primary:
            ep.is_primary = 0
    now = datetime.utcnow()
    photo = AssetPhoto(
        asset_id=asset_id,
        file_name=payload.file_name,
        content_type=payload.content_type,
        data=data_bytes,
        is_primary=is_primary_int,
        created_at=now,
    )
    session.add(photo)
    session.commit()
    session.refresh(photo)
    out = AssetPhotoOut(
        id=photo.id,
        asset_id=photo.asset_id,
        file_name=photo.file_name,
        content_type=photo.content_type,
        is_primary=True if photo.is_primary == 1 else False,
        created_at=photo.created_at,
    )
    session.close()
    return out

@app.get(
    "/api/asset-movements",
    response_model=AssetMovementsListResponse,
    summary="List asset movements by filters",
    description="Retrieve asset movements filtered by asset, location, or date.",
    tags=["movements"],
    operation_id="list_asset_movements",
)
async def list_asset_movements(
    asset_id: Optional[int] = Query(None, description="Filter movements by asset ID", example=4001),
    location_id: Optional[int] = Query(None, description="Filter movements involving this location as from or to", example=50),
    from_date: Optional[str] = Query(None, description="Include movements on/after this datetime (ISO8601)", example="2025-01-01T00:00:00Z"),
    to_date: Optional[str] = Query(None, description="Include movements on/before this datetime (ISO8601)", example="2025-03-31T23:59:59Z"),
    limit: Optional[int] = Query(500, description="Max movements to return", example=500),
    offset: Optional[int] = Query(0, description="Movements to skip", example=0),
) -> AssetMovementsListResponse:
    session = SessionLocal()
    query = session.query(AssetMovement)
    if asset_id is not None:
        query = query.filter(AssetMovement.asset_id == asset_id)
    if location_id is not None:
        query = query.filter(or_(AssetMovement.from_location_id == location_id, AssetMovement.to_location_id == location_id))
    if from_date is not None:
        fd = datetime.fromisoformat(from_date)
        query = query.filter(AssetMovement.moved_at >= fd)
    if to_date is not None:
        td = datetime.fromisoformat(to_date)
        query = query.filter(AssetMovement.moved_at <= td)
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    moves = query.all()
    items: List[AssetMovementsListItem] = []
    for m in moves:
        items.append(
            AssetMovementsListItem(
                id=m.id,
                asset_id=m.asset_id,
                from_location_id=m.from_location_id,
                to_location_id=m.to_location_id,
                moved_at=m.moved_at,
                reason=m.reason,
                created_by_user_id=m.created_by_user_id,
                created_at=m.created_at,
            )
        )
    session.close()
    return AssetMovementsListResponse(movements=items)

@app.get(
    "/api/asset-assignments",
    response_model=AssetAssignmentsListResponse,
    summary="List asset assignments",
    description="Retrieve asset assignments records by asset, user, project, or date.",
    tags=["assignments"],
    operation_id="list_asset_assignments",
)
async def list_asset_assignments(
    asset_id: Optional[int] = Query(None, description="Filter by asset ID", example=4001),
    to_user_id: Optional[int] = Query(None, description="Filter assignments where this user received the asset", example=34),
    project_name: Optional[str] = Query(None, description="Filter by project name", example="Q3 Brand Shoot"),
    from_date: Optional[str] = Query(None, description="Include assignments on/after this date", example="2025-01-01"),
    to_date: Optional[str] = Query(None, description="Include assignments on/before this date", example="2025-03-31"),
    only_active: Optional[bool] = Query(False, description="If true, only include assignments with null unassigned_at", example=True),
) -> AssetAssignmentsListResponse:
    session = SessionLocal()
    query = session.query(AssetAssignment)
    if asset_id is not None:
        query = query.filter(AssetAssignment.asset_id == asset_id)
    if to_user_id is not None:
        query = query.filter(AssetAssignment.to_user_id == to_user_id)
    if project_name is not None:
        query = query.filter(AssetAssignment.project_name == project_name)
    if from_date is not None:
        fd = datetime.fromisoformat(from_date + "T00:00:00")
        query = query.filter(AssetAssignment.assigned_at >= fd)
    if to_date is not None:
        td = datetime.fromisoformat(to_date + "T23:59:59")
        query = query.filter(AssetAssignment.assigned_at <= td)
    if only_active:
        query = query.filter(AssetAssignment.unassigned_at == None)
    assignments = query.all()
    items: List[AssetAssignmentsListItem] = []
    for a in assignments:
        items.append(
            AssetAssignmentsListItem(
                id=a.id,
                asset_id=a.asset_id,
                from_user_id=a.from_user_id,
                to_user_id=a.to_user_id,
                project_name=a.project_name,
                assigned_at=a.assigned_at,
                unassigned_at=a.unassigned_at,
                note=a.note,
                created_by_user_id=a.created_by_user_id,
                created_at=a.created_at,
            )
        )
    session.close()
    return AssetAssignmentsListResponse(assignments=items)

@app.post(
    "/api/maintenance-tickets",
    response_model=MaintenanceTicketOut,
    summary="Create a maintenance ticket",
    description="Create a maintenance ticket for an asset with details.",
    tags=["maintenance"],
    operation_id="create_maintenance_ticket",
)
async def create_maintenance_ticket(
    payload: MaintenanceTicketCreateRequest = Body(..., description="Maintenance ticket create payload"),
) -> MaintenanceTicketOut:
    session = SessionLocal()
    assigned_team_id = None
    if payload.assigned_team_name is not None:
        team = session.query(Team).filter(Team.name == payload.assigned_team_name).first()
        if team is not None:
            assigned_team_id = team.id
    due_date_val = None
    if payload.due_date is not None:
        due_date_val = date.fromisoformat(payload.due_date)
    now = datetime.utcnow()
    ticket = MaintenanceTicket(
        asset_id=payload.asset_id,
        title=payload.title,
        description=payload.description,
        type=payload.type,
        priority=payload.priority,
        status="Open",
        assigned_team_id=assigned_team_id,
        due_date=due_date_val,
        created_by_user_id=1,
        closed_at=None,
        created_at=now,
        updated_at=now,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    out = MaintenanceTicketOut(
        id=ticket.id,
        asset_id=ticket.asset_id,
        title=ticket.title,
        description=ticket.description,
        type=ticket.type,
        priority=ticket.priority,
        status=ticket.status,
        assigned_team_id=ticket.assigned_team_id,
        due_date=ticket.due_date,
        created_by_user_id=ticket.created_by_user_id,
        closed_at=ticket.closed_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )
    session.close()
    return out

@app.patch(
    "/api/maintenance-tickets/{ticket_id}",
    response_model=MaintenanceTicketUpdateOut,
    summary="Update maintenance ticket fields",
    description="Update ticket status, priority, team, type, and dates.",
    tags=["maintenance"],
    operation_id="update_maintenance_ticket",
)
async def update_maintenance_ticket(
    ticket_id: int = Path(..., description="Ticket ID to update", example=6001),
    payload: MaintenanceTicketUpdateRequest = Body(..., description="Maintenance ticket update payload"),
) -> MaintenanceTicketUpdateOut:
    session = SessionLocal()
    ticket = session.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
    if ticket is None:
        session.close()
        return MaintenanceTicketUpdateOut(
            id=0,
            status="",
            priority=None,
            assigned_team_id=None,
            due_date=None,
            closed_at=None,
            updated_at=datetime.utcnow(),
        )
    if payload.title is not None:
        ticket.title = payload.title
    if payload.description is not None:
        ticket.description = payload.description
    if payload.type is not None:
        ticket.type = payload.type
    if payload.priority is not None:
        ticket.priority = payload.priority
    if payload.status is not None:
        ticket.status = payload.status
    if payload.assigned_team_id is not None:
        ticket.assigned_team_id = payload.assigned_team_id
    if payload.due_date is not None:
        ticket.due_date = date.fromisoformat(payload.due_date)
    if payload.closed_at is not None:
        ticket.closed_at = datetime.fromisoformat(payload.closed_at)
    ticket.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(ticket)
    out = MaintenanceTicketUpdateOut(
        id=ticket.id,
        status=ticket.status,
        priority=ticket.priority,
        assigned_team_id=ticket.assigned_team_id,
        due_date=ticket.due_date,
        closed_at=ticket.closed_at,
        updated_at=ticket.updated_at,
    )
    session.close()
    return out

@app.get(
    "/api/maintenance-tickets",
    response_model=MaintenanceTicketsListResponse,
    summary="List maintenance tickets",
    description="Retrieve maintenance tickets by asset, status, priority, team, or group.",
    tags=["maintenance"],
    operation_id="list_maintenance_tickets",
)
async def list_maintenance_tickets(
    status: Optional[str] = Query(None, description="Filter tickets by status", example="Open"),
    priority: Optional[str] = Query(None, description="Filter by priority", example="High"),
    category_name: Optional[str] = Query(None, description="Filter tickets whose asset is in this category", example="Student iPad"),
    assigned_team_name: Optional[str] = Query(None, description="Filter by assigned team name", example="IT Hardware"),
    assigned_user_group_name: Optional[str] = Query(None, description="Filter by group name of the asset's assigned user", example="Elementary School - Grade 3"),
    asset_id: Optional[int] = Query(None, description="Filter by asset ID", example=8001),
    limit: Optional[int] = Query(100, description="Max tickets to return", example=100),
    offset: Optional[int] = Query(0, description="Tickets to skip", example=0),
) -> MaintenanceTicketsListResponse:
    session = SessionLocal()
    query = session.query(MaintenanceTicket)
    if asset_id is not None or category_name is not None or assigned_user_group_name is not None:
        query = query.join(Asset, MaintenanceTicket.asset_id == Asset.id)
    if category_name is not None:
        query = query.join(Category, Asset.category_id == Category.id).filter(Category.name == category_name)
    if assigned_user_group_name is not None:
        query = query.join(User, Asset.assigned_user_id == User.id)
        query = query.join(UserGroupMembership, User.id == UserGroupMembership.user_id)
        query = query.join(UserGroup, UserGroupMembership.group_id == UserGroup.id)
        query = query.filter(UserGroup.name == assigned_user_group_name)
    if asset_id is not None:
        query = query.filter(MaintenanceTicket.asset_id == asset_id)
    if assigned_team_name is not None:
        query = query.join(Team, MaintenanceTicket.assigned_team_id == Team.id).filter(Team.name == assigned_team_name)
    if status is not None:
        query = query.filter(MaintenanceTicket.status == status)
    if priority is not None:
        query = query.filter(MaintenanceTicket.priority == priority)
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    tickets = query.all()
    items: List[MaintenanceTicketsListItem] = []
    for t in tickets:
        items.append(
            MaintenanceTicketsListItem(
                id=t.id,
                asset_id=t.asset_id,
                title=t.title,
                description=t.description,
                type=t.type,
                priority=t.priority,
                status=t.status,
                assigned_team_id=t.assigned_team_id,
                due_date=t.due_date,
                created_by_user_id=t.created_by_user_id,
                closed_at=t.closed_at,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
        )
    session.close()
    return MaintenanceTicketsListResponse(tickets=items)

@app.post(
    "/api/maintenance-tickets/{ticket_id}/comments",
    response_model=MaintenanceTicketCommentOut,
    summary="Add comment to maintenance ticket",
    description="Create a comment entry linked to a ticket using current user.",
    tags=["maintenance", "comments"],
    operation_id="add_maintenance_ticket_comment",
)
async def add_maintenance_ticket_comment(
    ticket_id: int = Path(..., description="Ticket ID to comment on", example=6101),
    payload: MaintenanceTicketCommentRequest = Body(..., description="Maintenance ticket comment payload"),
) -> MaintenanceTicketCommentOut:
    session = SessionLocal()
    now = datetime.utcnow()
    comment = MaintenanceTicketComment(
        ticket_id=ticket_id,
        user_id=1,
        comment=payload.comment,
        created_at=now,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    out = MaintenanceTicketCommentOut(
        id=comment.id,
        ticket_id=comment.ticket_id,
        user_id=comment.user_id,
        comment=comment.comment,
        created_at=comment.created_at,
    )
    session.close()
    return out

@app.post(
    "/api/maintenance-tickets/{ticket_id}/attachments",
    response_model=MaintenanceTicketAttachmentOut,
    summary="Attach file to maintenance ticket",
    description="Upload a BLOB attachment for a maintenance ticket.",
    tags=["maintenance", "attachments"],
    operation_id="add_maintenance_ticket_attachment",
)
async def add_maintenance_ticket_attachment(
    ticket_id: int = Path(..., description="Ticket ID to attach file to", example=6001),
    payload: MaintenanceTicketAttachmentRequest = Body(..., description="Maintenance ticket attachment payload"),
) -> MaintenanceTicketAttachmentOut:
    session = SessionLocal()
    data_bytes = base64.b64decode(payload.data_base64)
    now = datetime.utcnow()
    attachment = MaintenanceTicketAttachment(
        ticket_id=ticket_id,
        file_name=payload.file_name,
        content_type=payload.content_type,
        data=data_bytes,
        created_at=now,
    )
    session.add(attachment)
    session.commit()
    session.refresh(attachment)
    out = MaintenanceTicketAttachmentOut(
        id=attachment.id,
        ticket_id=attachment.ticket_id,
        file_name=attachment.file_name,
        content_type=attachment.content_type,
        created_at=attachment.created_at,
    )
    session.close()
    return out

@app.post(
    "/api/maintenance-events",
    response_model=MaintenanceEventOut,
    summary="Create maintenance event for asset",
    description="Create a maintenance event representing work performed on an asset.",
    tags=["maintenance", "events"],
    operation_id="create_maintenance_event",
)
async def create_maintenance_event(
    payload: MaintenanceEventCreateRequest = Body(..., description="Maintenance event create payload"),
) -> MaintenanceEventOut:
    session = SessionLocal()
    performed_at_dt = datetime.fromisoformat(payload.performed_at)
    now = datetime.utcnow()
    event = MaintenanceEvent(
        asset_id=payload.asset_id,
        ticket_id=payload.ticket_id,
        event_type=payload.event_type,
        description=payload.description,
        performed_by_team_id=payload.performed_by_team_id,
        performed_at=performed_at_dt,
        metrics_json=payload.metrics_json,
        created_at=now,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    out = MaintenanceEventOut(
        id=event.id,
        asset_id=event.asset_id,
        ticket_id=event.ticket_id,
        event_type=event.event_type,
        description=event.description,
        performed_by_team_id=event.performed_by_team_id,
        performed_at=event.performed_at,
        metrics_json=event.metrics_json,
        created_at=event.created_at,
    )
    session.close()
    return out

@app.post(
    "/api/workflow-rules",
    response_model=WorkflowRuleOut,
    summary="Create a workflow rule",
    description="Create a workflow rule for asset-based automations.",
    tags=["workflow"],
    operation_id="create_workflow_rule",
)
async def create_workflow_rule(
    payload: WorkflowRuleCreateRequest = Body(..., description="Workflow rule create payload"),
) -> WorkflowRuleOut:
    session = SessionLocal()
    now = datetime.utcnow()
    is_active_int = 1 if (payload.is_active is None or payload.is_active) else 0
    rule = WorkflowRule(
        name=payload.name,
        description=payload.description,
        is_active=is_active_int,
        trigger_type=payload.trigger_type,
        config_json=payload.config_json,
        created_at=now,
        updated_at=now,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    out = WorkflowRuleOut(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        is_active=True if rule.is_active == 1 else False,
        trigger_type=rule.trigger_type,
        config_json=rule.config_json,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )
    session.close()
    return out

@app.post(
    "/api/workflow-rules/{rule_id}/actions",
    response_model=WorkflowRuleActionOut,
    summary="Create workflow rule action",
    description="Create a workflow_rule_actions entry for a rule.",
    tags=["workflow"],
    operation_id="create_workflow_rule_action",
)
async def create_workflow_rule_action(
    rule_id: int = Path(..., description="Workflow rule ID this action belongs to", example=1001),
    payload: WorkflowRuleActionCreateRequest = Body(..., description="Workflow rule action create payload"),
) -> WorkflowRuleActionOut:
    session = SessionLocal()
    now = datetime.utcnow()
    act = WorkflowRuleAction(
        rule_id=rule_id,
        action_type=payload.action_type,
        config_json=payload.config_json,
        created_at=now,
    )
    session.add(act)
    session.commit()
    session.refresh(act)
    out = WorkflowRuleActionOut(
        id=act.id,
        rule_id=act.rule_id,
        action_type=act.action_type,
        config_json=act.config_json,
        created_at=act.created_at,
    )
    session.close()
    return out

@app.post(
    "/api/assets/{asset_id}/disposal-events",
    response_model=AssetDisposalEventOut,
    summary="Record asset disposal event",
    description="Create a disposal event capturing date, method, reason, and approver.",
    tags=["assets", "disposals"],
    operation_id="create_asset_disposal_event",
)
async def create_asset_disposal_event(
    asset_id: int = Path(..., description="Asset ID that was disposed", example=4001),
    payload: AssetDisposalEventCreateRequest = Body(..., description="Asset disposal event payload"),
) -> AssetDisposalEventOut:
    session = SessionLocal()
    disposal_date_val = date.fromisoformat(payload.disposal_date)
    approved_by_user_id = None
    if payload.approved_by_user_email is not None:
        user = session.query(User).filter(User.email == payload.approved_by_user_email).first()
        if user is not None:
            approved_by_user_id = user.id
    now = datetime.utcnow()
    evt = AssetDisposalEvent(
        asset_id=asset_id,
        disposal_date=disposal_date_val,
        method=payload.method,
        reason=payload.reason,
        approved_by_user_id=approved_by_user_id,
        approval_note=payload.approval_note,
        created_at=now,
    )
    session.add(evt)
    session.commit()
    session.refresh(evt)
    out = AssetDisposalEventOut(
        id=evt.id,
        asset_id=evt.asset_id,
        disposal_date=evt.disposal_date,
        method=evt.method,
        reason=evt.reason,
        approved_by_user_id=evt.approved_by_user_id,
        approval_note=evt.approval_note,
        created_at=evt.created_at,
    )
    session.close()
    return out

@app.post(
    "/api/maintenance-tickets/bulk-update",
    response_model=MaintenanceTicketsBulkUpdateOut,
    summary="Bulk update maintenance tickets",
    description="Update status, priority, team, or due_date on multiple tickets.",
    tags=["maintenance", "bulk"],
    operation_id="bulk_update_maintenance_tickets",
)
async def bulk_update_maintenance_tickets(
    payload: MaintenanceTicketsBulkUpdateRequest = Body(..., description="Bulk maintenance tickets update payload"),
) -> MaintenanceTicketsBulkUpdateOut:
    session = SessionLocal()
    updated_ids: List[int] = []
    for tid in payload.ticket_ids:
        ticket = session.query(MaintenanceTicket).filter(MaintenanceTicket.id == tid).first()
        if ticket is None:
            continue
        if payload.status is not None:
            ticket.status = payload.status
        if payload.priority is not None:
            ticket.priority = payload.priority
        if payload.assigned_team_id is not None:
            ticket.assigned_team_id = payload.assigned_team_id
        if payload.due_date is not None:
            ticket.due_date = date.fromisoformat(payload.due_date)
        ticket.updated_at = datetime.utcnow()
        session.commit()
        updated_ids.append(ticket.id)
    session.close()
    return MaintenanceTicketsBulkUpdateOut(updated_ticket_ids=updated_ids, count=len(updated_ids))

@app.post(
    "/api/maintenance-tickets/bulk-add-comment",
    response_model=MaintenanceTicketsBulkCommentOut,
    summary="Bulk add comment to tickets",
    description="Add the same comment text to each ticket in the given list.",
    tags=["maintenance", "comments", "bulk"],
    operation_id="bulk_add_comment_to_tickets",
)
async def bulk_add_comment_to_tickets(
    payload: MaintenanceTicketsBulkCommentRequest = Body(..., description="Bulk maintenance tickets comment payload"),
) -> MaintenanceTicketsBulkCommentOut:
    session = SessionLocal()
    comment_ids: List[int] = []
    now = datetime.utcnow()
    for tid in payload.ticket_ids:
        comment = MaintenanceTicketComment(
            ticket_id=tid,
            user_id=1,
            comment=payload.comment,
            created_at=now,
        )
        session.add(comment)
        session.commit()
        session.refresh(comment)
        comment_ids.append(comment.id)
    session.close()
    return MaintenanceTicketsBulkCommentOut(comment_ids=comment_ids, count=len(comment_ids))

@app.get(
    "/api/reports/audit",
    response_model=AuditReportResponse,
    summary="Generate asset audit report",
    description="Produce an audit report with movements, assignments, and maintenance events.",
    tags=["reports", "audit"],
    operation_id="generate_asset_audit_report",
)
async def generate_asset_audit_report(
    location_root_full_path: str = Query(..., description="Full path of root location whose subtree assets are included", example="Dallas Data Center"),
    from_date: str = Query(..., description="Start of audit period (YYYY-MM-DD)", example="2025-01-01"),
    to_date: str = Query(..., description="End of audit period (YYYY-MM-DD)", example="2025-03-31"),
    include_only_with_location_changes: Optional[bool] = Query(False, description="If true, only include assets with location change", example=True),
    status: Optional[str] = Query(None, description="Filter assets by status", example="Active"),
) -> AuditReportResponse:
    session = SessionLocal()
    root = session.query(Location).filter(Location.full_path == location_root_full_path).first()
    assets_result: List[AuditReportAsset] = []
    if root is not None:
        subtree_locs = session.query(Location).filter(Location.full_path.like(f"{root.full_path}%")).all()
        loc_ids = [l.id for l in subtree_locs]
        asset_query = session.query(Asset).filter(Asset.location_id.in_(loc_ids))
        if status is not None:
            asset_query = asset_query.filter(Asset.status == status)
        audit_from = datetime.fromisoformat(from_date + "T00:00:00")
        audit_to = datetime.fromisoformat(to_date + "T23:59:59")
        for asset in asset_query.all():
            movements = (
                session.query(AssetMovement)
                .filter(AssetMovement.asset_id == asset.id)
                .filter(AssetMovement.moved_at >= audit_from)
                .filter(AssetMovement.moved_at <= audit_to)
                .all()
            )
            assignments = (
                session.query(AssetAssignment)
                .filter(AssetAssignment.asset_id == asset.id)
                .filter(AssetAssignment.assigned_at >= audit_from)
                .filter(AssetAssignment.assigned_at <= audit_to)
                .all()
            )
            events = (
                session.query(MaintenanceEvent)
                .filter(MaintenanceEvent.asset_id == asset.id)
                .filter(MaintenanceEvent.performed_at >= audit_from)
                .filter(MaintenanceEvent.performed_at <= audit_to)
                .all()
            )
            if include_only_with_location_changes and len(movements) == 0:
                continue
            events_list: List[AuditReportEvent] = []
            for m in movements:
                events_list.append(
                    AuditReportEvent(
                        event_type="movement",
                        timestamp=m.moved_at.isoformat(),
                        details={
                            "movement_id": str(m.id),
                            "from_location_id": str(m.from_location_id) if m.from_location_id is not None else None,
                            "to_location_id": str(m.to_location_id) if m.to_location_id is not None else None,
                            "reason": m.reason,
                        },
                    )
                )
            for a in assignments:
                events_list.append(
                    AuditReportEvent(
                        event_type="assignment",
                        timestamp=a.assigned_at.isoformat(),
                        details={
                            "assignment_id": str(a.id),
                            "from_user_id": str(a.from_user_id) if a.from_user_id is not None else None,
                            "to_user_id": str(a.to_user_id) if a.to_user_id is not None else None,
                            "project_name": a.project_name,
                            "note": a.note,
                        },
                    )
                )
            for e in events:
                events_list.append(
                    AuditReportEvent(
                        event_type="maintenance",
                        timestamp=e.performed_at.isoformat(),
                        details={
                            "maintenance_event_id": str(e.id),
                            "ticket_id": str(e.ticket_id) if e.ticket_id is not None else None,
                            "event_type": e.event_type,
                            "description": e.description,
                        },
                    )
                )
            current_location = None
            current_location_full_path = None
            if asset.location_id is not None:
                loc = session.query(Location).filter(Location.id == asset.location_id).first()
                if loc is not None:
                    current_location = loc.id
                    current_location_full_path = loc.full_path
            assets_result.append(
                AuditReportAsset(
                    asset_id=asset.id,
                    asset_tag=asset.asset_tag,
                    serial_number=asset.serial_number,
                    current_location_id=current_location,
                    current_location_full_path=current_location_full_path,
                    events=events_list,
                )
            )
    session.close()
    return AuditReportResponse(location_root=location_root_full_path, from_date=from_date, to_date=to_date, assets=assets_result)

if __name__ == "__main__":
    import uvicorn, os
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)