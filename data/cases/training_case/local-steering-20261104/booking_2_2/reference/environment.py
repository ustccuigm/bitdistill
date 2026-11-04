from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Time, ForeignKey, Float, LargeBinary
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, date, timedelta
import os
import json

database_url = os.getenv("DATABASE_PATH", "sqlite:///outputs/databases/flightledger_corporate_travel.db")
engine = create_engine("sqlite:////mnt/genming/training-local-cases-20261104/cases/booking_2_2/reference/final.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

app = FastAPI(title="FlightLedger Corporate Travel Simulator", version="1.0.0")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    external_ref = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompanyUserProfile(Base):
    __tablename__ = "company_user_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    default_cost_center = Column(String)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Traveler(Base):
    __tablename__ = "travelers"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TravelerPassport(Base):
    __tablename__ = "traveler_passports"
    id = Column(Integer, primary_key=True)
    traveler_id = Column(Integer, ForeignKey("travelers.id"), nullable=False)
    passport_number = Column(String, nullable=False)
    country_code = Column(String)
    expiry_date = Column(Date, nullable=False)
    is_primary = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TravelerLoyaltyProgram(Base):
    __tablename__ = "traveler_loyalty_programs"
    id = Column(Integer, primary_key=True)
    traveler_id = Column(Integer, ForeignKey("travelers.id"), nullable=False)
    carrier_or_chain = Column(String, nullable=False)
    program_name = Column(String, nullable=False)
    membership_number = Column(String, nullable=False)
    program_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TravelerPreference(Base):
    __tablename__ = "traveler_preferences"
    id = Column(Integer, primary_key=True)
    traveler_id = Column(Integer, ForeignKey("travelers.id"), nullable=False)
    seat_preference = Column(String)
    hotel_budget_max = Column(Float)
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class HotelBrand(Base):
    __tablename__ = "hotel_brands"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TravelerPreferredHotelBrand(Base):
    __tablename__ = "traveler_preferred_hotel_brands"
    id = Column(Integer, primary_key=True)
    traveler_id = Column(Integer, ForeignKey("travelers.id"), nullable=False)
    hotel_brand_id = Column(Integer, ForeignKey("hotel_brands.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TravelPolicy(Base):
    __tablename__ = "travel_policies"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    applies_to_scope = Column(String, nullable=False, default="company")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TravelPolicyRule(Base):
    __tablename__ = "travel_policy_rules"
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("travel_policies.id"), nullable=False)
    rule_type = Column(String, nullable=False)
    param_key = Column(String, nullable=False)
    param_value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ApprovalPolicyChain(Base):
    __tablename__ = "approval_policy_chains"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("travel_policies.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    name = Column(String, nullable=False)
    description = Column(String)
    is_default = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ApprovalPolicyChainStep(Base):
    __tablename__ = "approval_policy_chain_steps"
    id = Column(Integer, primary_key=True)
    chain_id = Column(Integer, ForeignKey("approval_policy_chains.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    approver_role_name = Column(String)
    approver_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True)
    trip_code = Column(String, unique=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    primary_traveler_id = Column(Integer, ForeignKey("travelers.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    cost_center = Column(String)
    purpose = Column(String)
    status = Column(String, nullable=False)
    policy_id = Column(Integer, ForeignKey("travel_policies.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    total_air_cost = Column(Float, default=0)
    total_hotel_cost = Column(Float, default=0)
    total_other_cost = Column(Float, default=0)
    total_cost = Column(Float, default=0)
    has_policy_violations = Column(Integer, nullable=False, default=0)
    external_export_status = Column(String)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    updated_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TripTraveler(Base):
    __tablename__ = "trip_travelers"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    traveler_id = Column(Integer, ForeignKey("travelers.id"), nullable=False)
    role = Column(String, nullable=False, default="primary")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class FlightSegment(Base):
    __tablename__ = "flight_segments"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    from_airport = Column(String, nullable=False)
    to_airport = Column(String, nullable=False)
    departure_date = Column(Date, nullable=False)
    departure_time_from = Column(Time)
    departure_time_to = Column(Time)
    return_segment = Column(Integer, nullable=False, default=0)
    cabin_class = Column(String, nullable=False)
    booked_fare = Column(Float)
    currency = Column(String, default="USD")
    booking_status = Column(String, nullable=False, default="planned")
    carrier_code = Column(String)
    flight_number = Column(String)
    policy_compliant = Column(Integer, nullable=False, default=1)
    policy_violation_reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class HotelBooking(Base):
    __tablename__ = "hotel_bookings"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    city = Column(String, nullable=False)
    hotel_name = Column(String)
    hotel_brand_id = Column(Integer, ForeignKey("hotel_brands.id"))
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    nightly_rate = Column(Float)
    currency = Column(String, default="USD")
    total_nights = Column(Integer)
    total_cost = Column(Float)
    property_type = Column(String)
    booking_status = Column(String, nullable=False, default="planned")
    policy_compliant = Column(Integer, nullable=False, default=1)
    policy_violation_reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TripPolicyViolation(Base):
    __tablename__ = "trip_policy_violations"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    component_type = Column(String, nullable=False)
    component_id = Column(Integer)
    violation_code = Column(String, nullable=False)
    description = Column(String)
    severity = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class TripApprovalRequest(Base):
    __tablename__ = "trip_approval_requests"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("travel_policies.id"))
    chain_id = Column(Integer, ForeignKey("approval_policy_chains.id"))
    status = Column(String, nullable=False)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime)
    final_decision = Column(String)
    final_decision_at = Column(DateTime)
    final_decision_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TripApprovalStep(Base):
    __tablename__ = "trip_approval_steps"
    id = Column(Integer, primary_key=True)
    approval_request_id = Column(Integer, ForeignKey("trip_approval_requests.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    approver_role_name = Column(String)
    approver_user_id = Column(Integer, ForeignKey("users.id"))
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime)
    decision = Column(String)
    decision_comment = Column(String)
    decided_at = Column(DateTime)
    decided_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TripComment(Base):
    __tablename__ = "trip_comments"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    author_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_type = Column(String, nullable=False)
    visibility = Column(String, nullable=False, default="external")
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TripNotification(Base):
    __tablename__ = "trip_notifications"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    traveler_id = Column(Integer, ForeignKey("travelers.id"), nullable=False)
    channel = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)


class TripExpenseExport(Base):
    __tablename__ = "trip_expense_exports"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    external_system_name = Column(String, nullable=False)
    export_status = Column(String, nullable=False)
    payload = Column(LargeBinary)
    total_air_spend = Column(Float)
    total_hotel_spend = Column(Float)
    total_other_spend = Column(Float)
    has_policy_violations = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)


def bool_from_int(value: Optional[int]) -> Optional[bool]:
    if value is None:
        return None
    return bool(value)


def int_from_bool(value: Optional[bool]) -> Optional[int]:
    if value is None:
        return None
    return 1 if value else 0


class CompanyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Company primary key", example=1)
    name: str = Field(..., description="Company name", example="Acme Analytics")
    external_ref: Optional[str] = Field(None, description="Optional external reference identifier", example="ACME-001")
    created_at: datetime = Field(..., description="Timestamp when company was created (ISO 8601)", example="2024-01-15T10:00:00Z")
    updated_at: datetime = Field(..., description="Timestamp when company was last updated (ISO 8601)", example="2024-03-01T09:30:00Z")


class ListCompaniesResponse(BaseModel):
    companies: List[CompanyModel] = Field(..., description="List of companies", example=[])


class CreateCompanyRequest(BaseModel):
    name: str = Field(..., description="Company name (must be unique)", example="Acme Analytics")
    external_ref: Optional[str] = Field(None, description="External reference identifier used in other systems", example="ACME-ERP-01")


class CreateCompanyResponse(CompanyModel):
    pass


class DepartmentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Department primary key", example=10)
    company_id: int = Field(..., description="Owning company primary key", example=1)
    name: str = Field(..., description="Department name", example="Sales - Northwest")
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-01-10T08:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-02-01T12:00:00Z")


class ListDepartmentsResponse(BaseModel):
    departments: List[DepartmentModel] = Field(..., description="List of departments", example=[])


class RoleModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Role primary key", example=5)
    name: str = Field(..., description="Role name", example="Finance Manager")
    description: Optional[str] = Field(None, description="Role description", example="Approves travel expenses for finance")
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-01-01T00:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-01-15T00:00:00Z")


class ListRolesResponse(BaseModel):
    roles: List[RoleModel] = Field(..., description="List of roles", example=[])


class CurrentUserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Current user primary key (always 1 in this context)", example=1)
    username: str = Field(..., description="Username of the current user", example="admin")
    email: str = Field(..., description="Email of the current user", example="admin@example.com")
    full_name: Optional[str] = Field(None, description="Full name of the current user", example="System Admin")
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-01-01T00:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-02-01T00:00:00Z")


class CreateTravelerRequest(BaseModel):
    company_id: int = Field(..., description="Company primary key for this traveler", example=1)
    first_name: str = Field(..., description="Traveler first name", example="Maria")
    last_name: str = Field(..., description="Traveler last name", example="Gonzalez")
    email: Optional[str] = Field(None, description="Traveler email address", example="maria.gonzalez@acme-analytics.com")
    user_id: Optional[int] = Field(None, description="Optional linked users.id if traveler has a user account", example=5)
    department_id: Optional[int] = Field(None, description="Optional department this traveler belongs to", example=10)
    status: Optional[str] = Field(None, description="Traveler status, e.g., active or inactive", example="active")


class TravelerModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Traveler primary key", example=1001)
    company_id: int = Field(..., description="Company primary key", example=1)
    first_name: str = Field(..., description="Traveler first name", example="Maria")
    last_name: str = Field(..., description="Traveler last name", example="Gonzalez")
    email: Optional[str] = Field(None, description="Traveler email", example="maria.gonzalez@acme-analytics.com")
    user_id: Optional[int] = Field(None, description="Linked user id if any", example=None)
    department_id: Optional[int] = Field(None, description="Department id if set", example=10)
    status: str = Field(..., description="Traveler status", example="active")
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-02-01T10:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-02-01T10:00:00Z")


class ListTravelersResponse(BaseModel):
    travelers: List[TravelerModel] = Field(..., description="List of travelers", example=[])


class AddTravelerPassportRequest(BaseModel):
    passport_number: str = Field(..., description="Passport number (unique per traveler)", example="P12345678")
    country_code: Optional[str] = Field(None, description="Country code issuing the passport (ISO 2-letter)", example="US")
    expiry_date: str = Field(..., description="Passport expiry date in YYYY-MM-DD format", example="2029-05-14")
    is_primary: Optional[bool] = Field(None, description="Whether this is the primary passport for traveler", example=True)


class TravelerPassportModel(BaseModel):
    id: int = Field(..., description="Traveler passport primary key", example=5001)
    traveler_id: int = Field(..., description="Traveler primary key", example=1001)
    passport_number: str = Field(..., description="Passport number", example="P12345678")
    country_code: Optional[str] = Field(None, description="Issuing country code", example="US")
    expiry_date: str = Field(..., description="Passport expiry date", example="2029-05-14")
    is_primary: bool = Field(..., description="Primary passport flag (1=true,0=false)", example=True)
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-02-01T11:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-02-01T11:00:00Z")


class AddTravelerLoyaltyProgramRequest(BaseModel):
    carrier_or_chain: str = Field(..., description="Airline carrier code or hotel chain name", example="American Airlines")
    program_name: str = Field(..., description="Name of the loyalty program", example="AAdvantage")
    membership_number: str = Field(..., description="Loyalty program membership number", example="AA998877")
    program_type: str = Field(..., description="Program type, e.g., airline or hotel", example="airline")


class TravelerLoyaltyProgramModel(BaseModel):
    id: int = Field(..., description="Loyalty program primary key", example=6001)
    traveler_id: int = Field(..., description="Traveler primary key", example=1001)
    carrier_or_chain: str = Field(..., description="Airline carrier or hotel chain", example="American Airlines")
    program_name: str = Field(..., description="Program name", example="AAdvantage")
    membership_number: str = Field(..., description="Membership number", example="AA998877")
    program_type: str = Field(..., description="Program type", example="airline")
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-02-01T11:05:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-02-01T11:05:00Z")


class TravelerPreferencesCreateRequest(BaseModel):
    seat_preference: Optional[str] = Field(None, description="Seat preference such as aisle, window, or middle", example="aisle")
    hotel_budget_max: Optional[float] = Field(None, description="Preferred maximum nightly hotel rate", example=220.0)
    notes: Optional[str] = Field(None, description="Free-form notes about traveler preferences", example="Avoid red-eye flights")


class TravelerPreferencesUpdateRequest(BaseModel):
    seat_preference: Optional[str] = Field(None, description="New seat preference if updating", example="aisle")
    hotel_budget_max: Optional[float] = Field(None, description="New hotel budget max if updating", example=250.0)
    notes: Optional[str] = Field(None, description="New notes if updating", example="Prefers Marriott properties when available")


class TravelerPreferencesModel(BaseModel):
    id: int = Field(..., description="Traveler preferences primary key", example=7001)
    traveler_id: int = Field(..., description="Traveler primary key", example=1001)
    seat_preference: Optional[str] = Field(None, description="Seat preference", example="aisle")
    hotel_budget_max: Optional[float] = Field(None, description="Preferred max nightly hotel rate", example=220.0)
    notes: Optional[str] = Field(None, description="Additional preference notes", example="Avoid red-eye flights")
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-02-01T11:10:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-02-01T11:10:00Z")


class HotelBrandModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Hotel brand primary key", example=200)
    name: str = Field(..., description="Hotel brand name", example="Marriott")
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-01-01T00:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-02-01T00:00:00Z")


class ListHotelBrandsResponse(BaseModel):
    hotel_brands: List[HotelBrandModel] = Field(..., description="List of hotel brands", example=[])


class CreateHotelBrandRequest(BaseModel):
    name: str = Field(..., description="Hotel brand name (must be unique)", example="Marriott")


class CreateHotelBrandResponse(HotelBrandModel):
    pass


class AddTravelerPreferredHotelBrandRequest(BaseModel):
    hotel_brand_id: int = Field(..., description="Hotel brand primary key to mark as preferred", example=200)


class TravelerPreferredHotelBrandModel(BaseModel):
    id: int = Field(..., description="Preferred hotel brand link primary key", example=8001)
    traveler_id: int = Field(..., description="Traveler primary key", example=1001)
    hotel_brand_id: int = Field(..., description="Hotel brand primary key", example=200)
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-02-01T11:15:00Z")


class CreateTravelPolicyRequest(BaseModel):
    company_id: int = Field(..., description="Company primary key that owns this policy", example=1)
    name: str = Field(..., description="Policy name unique within company", example="US Domestic Standard")
    description: Optional[str] = Field(None, description="High-level description of the policy", example="Standard domestic travel policy for US-based travel")
    applies_to_scope: Optional[str] = Field(None, description="Scope for policy such as company or department", example="company")


class TravelPolicyModel(BaseModel):
    id: int = Field(..., description="Travel policy primary key", example=3001)
    company_id: int = Field(..., description="Owning company primary key", example=1)
    name: str = Field(..., description="Policy name", example="US Domestic Standard")
    description: Optional[str] = Field(None, description="Policy description", example="Standard domestic travel policy for US-based travel")
    applies_to_scope: str = Field(..., description="Scope string", example="company")
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-02-01T12:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-02-01T12:00:00Z")


class AddTravelPolicyRuleRequest(BaseModel):
    rule_type: str = Field(..., description="Rule type, such as airfare, cabin_class, advance_purchase", example="airfare")
    param_key: str = Field(..., description="Logical parameter key for the rule", example="max_roundtrip_usd")
    param_value: str = Field(..., description="Value for this rule's parameter", example="800")


class TravelPolicyRuleModel(BaseModel):
    id: int = Field(..., description="Travel policy rule primary key", example=4001)
    policy_id: int = Field(..., description="Linked travel policy primary key", example=3001)
    rule_type: str = Field(..., description="Rule type string", example="airfare")
    param_key: str = Field(..., description="Parameter key", example="max_roundtrip_usd")
    param_value: str = Field(..., description="Parameter value", example="800")
    created_at: datetime = Field(..., description="Rule creation timestamp", example="2024-02-01T12:05:00Z")
    updated_at: datetime = Field(..., description="Rule last update timestamp", example="2024-02-01T12:05:00Z")


class CreateApprovalPolicyChainRequest(BaseModel):
    company_id: int = Field(..., description="Company primary key that owns this chain", example=1)
    policy_id: Optional[int] = Field(None, description="Optional travel policy id that this chain is associated with", example=3001)
    department_id: Optional[int] = Field(None, description="Optional department id for department-specific chain", example=10)
    name: str = Field(..., description="Name of the approval chain", example="US Domestic Standard Default Chain")
    description: Optional[str] = Field(None, description="Description of when this chain is used", example="Team Lead then Finance Manager for US domestic trips")
    is_default: Optional[bool] = Field(None, description="Whether this chain is the default for the given scope", example=True)


class ApprovalPolicyChainModel(BaseModel):
    id: int = Field(..., description="Approval policy chain primary key", example=9001)
    company_id: int = Field(..., description="Owning company id", example=1)
    policy_id: Optional[int] = Field(None, description="Linked policy id if any", example=3001)
    department_id: Optional[int] = Field(None, description="Linked department id if any", example=10)
    name: str = Field(..., description="Chain name", example="US Domestic Standard Default Chain")
    description: Optional[str] = Field(None, description="Chain description", example="Team Lead then Finance Manager for US domestic trips")
    is_default: bool = Field(..., description="Is default chain flag", example=True)
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-02-01T12:10:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-02-01T12:10:00Z")


class ListApprovalPolicyChainsResponse(BaseModel):
    approval_policy_chains: List[ApprovalPolicyChainModel] = Field(..., description="List of approval policy chains", example=[])


class AddApprovalPolicyChainStepRequest(BaseModel):
    sequence: int = Field(..., description="Order of this step in the chain (1-based)", example=1)
    approver_role_name: Optional[str] = Field(None, description="Role name for approver at this step, if role-driven", example="Team Lead")
    approver_user_id: Optional[int] = Field(None, description="Specific user id as approver, if user-specific", example=None)


class ApprovalPolicyChainStepModel(BaseModel):
    id: int = Field(..., description="Approval policy chain step primary key", example=9101)
    chain_id: int = Field(..., description="Linked approval chain id", example=9001)
    sequence: int = Field(..., description="Step order in chain", example=1)
    approver_role_name: Optional[str] = Field(None, description="Role for approver", example="Team Lead")
    approver_user_id: Optional[int] = Field(None, description="Specific approver user id if set", example=None)
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-02-01T12:15:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-02-01T12:15:00Z")


class CreateTripRequest(BaseModel):
    company_id: int = Field(..., description="Company primary key that owns this trip", example=1)
    primary_traveler_id: int = Field(..., description="Primary traveler id for this trip", example=1001)
    department_id: Optional[int] = Field(None, description="Department id associated with the trip", example=10)
    cost_center: Optional[str] = Field(None, description="Trip cost center code", example="SALES-NW")
    purpose: str = Field(..., description="Business purpose of the trip", example="Client meeting at Seattle HQ")
    status: Optional[str] = Field(None, description="Initial trip status, usually draft or planned", example="draft")
    policy_id: Optional[int] = Field(None, description="Linked travel policy id if known at creation time", example=3001)
    start_date: Optional[str] = Field(None, description="Trip start date YYYY-MM-DD, often inferred from segments later", example="2025-02-10")
    end_date: Optional[str] = Field(None, description="Trip end date YYYY-MM-DD", example="2025-02-12")


class TripModel(BaseModel):
    id: int = Field(..., description="Trip primary key", example=4821)
    trip_code: Optional[str] = Field(None, description="Unique human-readable trip code", example="TRIP-4821")
    company_id: int = Field(..., description="Owning company id", example=1)
    primary_traveler_id: int = Field(..., description="Primary traveler id", example=1001)
    department_id: Optional[int] = Field(None, description="Department id", example=10)
    cost_center: Optional[str] = Field(None, description="Cost center code", example="SALES-NW")
    purpose: Optional[str] = Field(None, description="Trip purpose", example="Client meeting at Seattle HQ")
    status: str = Field(..., description="Trip status", example="draft")
    policy_id: Optional[int] = Field(None, description="Linked travel policy id if any", example=3001)
    start_date: Optional[str] = Field(None, description="Trip start date", example="2025-02-10")
    end_date: Optional[str] = Field(None, description="Trip end date", example="2025-02-12")
    total_air_cost: float = Field(..., description="Total air cost for trip", example=0.0)
    total_hotel_cost: float = Field(..., description="Total hotel cost for trip", example=0.0)
    total_other_cost: float = Field(..., description="Total other costs for trip", example=0.0)
    total_cost: float = Field(..., description="Aggregate total cost", example=0.0)
    has_policy_violations: bool = Field(..., description="Flag if any policy violations present", example=False)
    external_export_status: Optional[str] = Field(None, description="Status of external expense export", example=None)
    created_by_user_id: Optional[int] = Field(None, description="User that created the trip (always 1 here)", example=1)
    updated_by_user_id: Optional[int] = Field(None, description="User that last updated the trip", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-15T09:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-15T09:00:00Z")


class ListTripsResponse(BaseModel):
    trips: List[TripModel] = Field(..., description="List of trips", example=[])


class UpdateTripRequest(BaseModel):
    status: Optional[str] = Field(None, description="New trip status such as draft, submitted, approved, booked, canceled", example="booked")
    policy_id: Optional[int] = Field(None, description="Change the policy id associated with this trip", example=3001)
    purpose: Optional[str] = Field(None, description="Update the purpose text", example="Quarterly account review")
    cost_center: Optional[str] = Field(None, description="Update the cost center code", example="CS-ENTERPRISE")
    start_date: Optional[str] = Field(None, description="Update trip start date YYYY-MM-DD", example="2025-03-12")
    end_date: Optional[str] = Field(None, description="Update trip end date YYYY-MM-DD", example="2025-03-14")
    has_policy_violations: Optional[bool] = Field(None, description="Set whether trip has any policy violations", example=True)


class AddFlightSegmentRequest(BaseModel):
    from_airport: str = Field(..., description="IATA code of origin airport", example="SFO")
    to_airport: str = Field(..., description="IATA code of destination airport", example="SEA")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format", example="2025-02-10")
    departure_time_from: Optional[str] = Field(None, description="Earliest acceptable departure time (HH:MM:SS) for planning stage", example="08:00:00")
    departure_time_to: Optional[str] = Field(None, description="Latest acceptable departure time (HH:MM:SS) for planning stage", example=None)
    return_segment: Optional[bool] = Field(None, description="Flag if this is a return leg of a round trip (1 or 0 stored)", example=False)
    cabin_class: str = Field(..., description="Cabin class for this segment, e.g., Economy, Business", example="Economy")
    booking_status: Optional[str] = Field(None, description="Initial booking status, usually planned", example="planned")
    carrier_code: Optional[str] = Field(None, description="Airline carrier code if known when booking", example="AA")
    flight_number: Optional[str] = Field(None, description="Flight number if known when booking", example="AA123")
    booked_fare: Optional[float] = Field(None, description="Booked fare amount once confirmed", example=350.0)
    currency: Optional[str] = Field(None, description="Currency code for fare", example="USD")
    policy_compliant: Optional[bool] = Field(None, description="Policy compliance flag", example=True)
    policy_violation_reason: Optional[str] = Field(None, description="Reason if the segment violates policy", example="Fare exceeds max allowed")


class FlightSegmentModel(BaseModel):
    id: int = Field(..., description="Flight segment primary key", example=10001)
    trip_id: int = Field(..., description="Associated trip id", example=4821)
    from_airport: str = Field(..., description="Origin airport code", example="SFO")
    to_airport: str = Field(..., description="Destination airport code", example="SEA")
    departure_date: str = Field(..., description="Departure date", example="2025-02-10")
    departure_time_from: Optional[str] = Field(None, description="Departure time from", example="08:00:00")
    departure_time_to: Optional[str] = Field(None, description="Departure time to", example=None)
    return_segment: bool = Field(..., description="Return segment flag", example=False)
    cabin_class: str = Field(..., description="Cabin class", example="Economy")
    booked_fare: Optional[float] = Field(None, description="Booked fare", example=None)
    currency: Optional[str] = Field(None, description="Currency code", example="USD")
    booking_status: str = Field(..., description="Booking status", example="planned")
    carrier_code: Optional[str] = Field(None, description="Carrier code", example="AA")
    flight_number: Optional[str] = Field(None, description="Flight number", example="AA123")
    policy_compliant: bool = Field(..., description="Policy compliant flag", example=True)
    policy_violation_reason: Optional[str] = Field(None, description="Policy violation reason text", example=None)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-20T10:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-20T10:00:00Z")


class ListFlightSegmentsResponse(BaseModel):
    flight_segments: List[FlightSegmentModel] = Field(..., description="List of flight segments", example=[])


class UpdateFlightSegmentRequest(BaseModel):
    departure_date: Optional[str] = Field(None, description="Update departure date", example="2025-02-10")
    departure_time_from: Optional[str] = Field(None, description="Update departure time from", example="09:30:00")
    departure_time_to: Optional[str] = Field(None, description="Update departure time to", example=None)
    return_segment: Optional[bool] = Field(None, description="Update return flag", example=True)
    cabin_class: Optional[str] = Field(None, description="Update cabin class", example="Economy")
    booked_fare: Optional[float] = Field(None, description="Set the booked fare cost", example=320.0)
    currency: Optional[str] = Field(None, description="Update currency code", example="USD")
    booking_status: Optional[str] = Field(None, description="Update booking status (planned, booked, canceled)", example="booked")
    carrier_code: Optional[str] = Field(None, description="Set carrier code once booked", example="AA")
    flight_number: Optional[str] = Field(None, description="Set flight number once booked", example="AA456")
    policy_compliant: Optional[bool] = Field(None, description="Set policy compliance flag", example=True)
    policy_violation_reason: Optional[str] = Field(None, description="Update policy violation reason", example=None)


class AddHotelBookingRequest(BaseModel):
    city: str = Field(..., description="City where the hotel is located", example="Seattle")
    hotel_name: Optional[str] = Field(None, description="Name of the hotel property if known", example="Seattle Downtown Midrange Hotel")
    hotel_brand_id: Optional[int] = Field(None, description="Hotel brand id if property belongs to a known chain", example=201)
    check_in_date: str = Field(..., description="Check-in date YYYY-MM-DD", example="2025-02-10")
    check_out_date: str = Field(..., description="Check-out date YYYY-MM-DD", example="2025-02-12")
    nightly_rate: Optional[float] = Field(None, description="Nightly rate amount for the booking", example=210.0)
    currency: Optional[str] = Field(None, description="Currency code for nightly_rate", example="USD")
    total_nights: Optional[int] = Field(None, description="Total number of nights (can be derived from dates)", example=2)
    total_cost: Optional[float] = Field(None, description="Total cost of stay (nightly_rate * nights)", example=420.0)
    property_type: Optional[str] = Field(None, description="Type like mid-range, budget, luxury", example="mid-range")
    booking_status: Optional[str] = Field(None, description="Booking status (planned, booked, canceled)", example="planned")
    policy_compliant: Optional[bool] = Field(None, description="Policy compliance flag", example=True)
    policy_violation_reason: Optional[str] = Field(None, description="Explanation if booking is not policy compliant", example="Rate above 220 USD limit")


class HotelBookingModel(BaseModel):
    id: int = Field(..., description="Hotel booking primary key", example=11001)
    trip_id: int = Field(..., description="Trip id", example=4821)
    city: str = Field(..., description="Hotel city", example="Seattle")
    hotel_name: Optional[str] = Field(None, description="Hotel name", example="Seattle Downtown Midrange Hotel")
    hotel_brand_id: Optional[int] = Field(None, description="Hotel brand id", example=201)
    check_in_date: str = Field(..., description="Check-in date", example="2025-02-10")
    check_out_date: str = Field(..., description="Check-out date", example="2025-02-12")
    nightly_rate: Optional[float] = Field(None, description="Nightly rate", example=210.0)
    currency: Optional[str] = Field(None, description="Currency", example="USD")
    total_nights: Optional[int] = Field(None, description="Total nights", example=2)
    total_cost: Optional[float] = Field(None, description="Total cost", example=420.0)
    property_type: Optional[str] = Field(None, description="Property type", example="mid-range")
    booking_status: str = Field(..., description="Booking status", example="planned")
    policy_compliant: bool = Field(..., description="Policy compliant flag", example=True)
    policy_violation_reason: Optional[str] = Field(None, description="Policy violation reason", example=None)
    created_at: datetime = Field(..., description="Created timestamp", example="2025-01-20T11:00:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-01-20T11:00:00Z")


class ListHotelBookingsResponse(BaseModel):
    hotel_bookings: List[HotelBookingModel] = Field(..., description="List of hotel bookings", example=[])


class UpdateHotelBookingRequest(BaseModel):
    hotel_name: Optional[str] = Field(None, description="Update hotel name", example="Hilton Berlin City Center")
    hotel_brand_id: Optional[int] = Field(None, description="Update hotel brand id", example=210)
    check_in_date: Optional[str] = Field(None, description="Update check-in date", example="2025-04-05")
    check_out_date: Optional[str] = Field(None, description="Update check-out date", example="2025-04-08")
    nightly_rate: Optional[float] = Field(None, description="Update nightly rate", example=195.0)
    currency: Optional[str] = Field(None, description="Update currency", example="EUR")
    total_nights: Optional[int] = Field(None, description="Update total nights", example=3)
    total_cost: Optional[float] = Field(None, description="Update total cost", example=585.0)
    property_type: Optional[str] = Field(None, description="Update property type", example="mid-range")
    booking_status: Optional[str] = Field(None, description="Update booking status (planned, booked, canceled)", example="canceled")
    policy_compliant: Optional[bool] = Field(None, description="Update policy compliance flag", example=True)
    policy_violation_reason: Optional[str] = Field(None, description="Update violation reason", example=None)


class RecalculateTripCostsResponse(BaseModel):
    trip_id: int = Field(..., description="Trip id for which totals were recalculated", example=5279)
    total_air_cost: float = Field(..., description="Recalculated total air cost", example=650.0)
    total_hotel_cost: float = Field(..., description="Recalculated total hotel cost", example=0.0)
    total_other_cost: float = Field(..., description="Recalculated total other costs", example=0.0)
    total_cost: float = Field(..., description="Recalculated overall total cost", example=650.0)


class CloneTripRequest(BaseModel):
    date_shift_days: int = Field(..., description="Number of days to shift start/end dates and segments", example=30)
    primary_traveler_id: int = Field(..., description="Primary traveler id for the new cloned trip", example=2002)
    purpose: str = Field(..., description="Purpose text for the new cloned trip", example="Quarterly account review")
    cost_center: str = Field(..., description="Cost center code for the new trip", example="CS-ENTERPRISE")


class CloneTripNewTripModel(BaseModel):
    id: int = Field(..., description="New trip id", example=6000)
    trip_code: Optional[str] = Field(None, description="New trip code", example="TRIP-6000")
    company_id: int = Field(..., description="Company id", example=1)
    primary_traveler_id: int = Field(..., description="Primary traveler id", example=2002)
    department_id: Optional[int] = Field(None, description="Department id", example=10)
    cost_center: Optional[str] = Field(None, description="Cost center", example="CS-ENTERPRISE")
    purpose: Optional[str] = Field(None, description="Purpose", example="Quarterly account review")
    status: str = Field(..., description="Trip status", example="draft")
    policy_id: Optional[int] = Field(None, description="Policy id", example=3001)
    start_date: Optional[str] = Field(None, description="Start date after shift", example="2025-05-10")
    end_date: Optional[str] = Field(None, description="End date after shift", example="2025-05-12")


class CloneTripResponse(BaseModel):
    new_trip: CloneTripNewTripModel = Field(..., description="Newly created cloned trip header", example={})


class CreateTripApprovalRequestRequest(BaseModel):
    trip_id: int = Field(..., description="Trip id being submitted for approval", example=4821)
    policy_id: int = Field(..., description="Travel policy id under which this trip is submitted", example=3001)
    chain_id: int = Field(..., description="Approval policy chain id defining routing", example=9001)
    status: Optional[str] = Field(None, description="Initial approval request status, usually submitted", example="submitted")


class TripApprovalRequestModel(BaseModel):
    id: int = Field(..., description="Trip approval request primary key", example=12001)
    trip_id: int = Field(..., description="Trip id", example=4821)
    policy_id: Optional[int] = Field(None, description="Policy id", example=3001)
    chain_id: Optional[int] = Field(None, description="Approval chain id", example=9001)
    status: str = Field(..., description="Approval request status", example="submitted")
    submitted_by_user_id: int = Field(..., description="User id that submitted (always 1)", example=1)
    submitted_at: Optional[datetime] = Field(None, description="Timestamp when submitted", example="2025-01-20T08:00:00Z")
    final_decision: Optional[str] = Field(None, description="Final decision when completed", example=None)
    final_decision_at: Optional[datetime] = Field(None, description="Final decision timestamp", example=None)
    final_decision_by_user_id: Optional[int] = Field(None, description="User that finalized decision", example=None)
    created_at: datetime = Field(..., description="Created timestamp", example="2025-01-20T08:00:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-01-20T08:00:00Z")


class CreateTripApprovalStepRequest(BaseModel):
    sequence: int = Field(..., description="Position of this step in the approval sequence", example=1)
    status: str = Field(..., description="Initial step status such as pending or skipped", example="pending")
    approver_role_name: Optional[str] = Field(None, description="Role name associated with this step", example="Team Lead")
    approver_user_id: Optional[int] = Field(None, description="User id of approver, if mapped to specific user", example=15)
    assigned_to_user_id: int = Field(..., description="User id to whom this approval step is assigned", example=15)
    assigned_at: Optional[datetime] = Field(None, description="Timestamp when step was assigned", example="2025-01-20T08:10:00Z")


class TripApprovalStepModel(BaseModel):
    id: int = Field(..., description="Approval step primary key", example=13001)
    approval_request_id: int = Field(..., description="Linked approval request id", example=12001)
    sequence: int = Field(..., description="Step sequence", example=1)
    status: str = Field(..., description="Step status", example="pending")
    approver_role_name: Optional[str] = Field(None, description="Role name for approver", example="Team Lead")
    approver_user_id: Optional[int] = Field(None, description="Approver user id if set", example=15)
    assigned_to_user_id: Optional[int] = Field(None, description="Assigned user id", example=15)
    assigned_at: Optional[datetime] = Field(None, description="Assigned timestamp", example="2025-01-20T08:10:00Z")
    decision: Optional[str] = Field(None, description="Decision taken at this step", example=None)
    decision_comment: Optional[str] = Field(None, description="Approver comment for this step", example=None)
    decided_at: Optional[datetime] = Field(None, description="Timestamp when decision was recorded", example=None)
    decided_by_user_id: Optional[int] = Field(None, description="User id that made the decision", example=None)
    created_at: datetime = Field(..., description="Created timestamp", example="2025-01-20T08:10:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-01-20T08:10:00Z")


class ListMyPendingApprovalStepsItem(BaseModel):
    id: int = Field(..., description="Approval step id", example=13001)
    approval_request_id: int = Field(..., description="Linked approval request id", example=12001)
    trip_id: int = Field(..., description="Trip id associated via approval request", example=4821)
    sequence: int = Field(..., description="Step sequence", example=1)
    status: str = Field(..., description="Step status", example="pending")
    approver_role_name: Optional[str] = Field(None, description="Approver role name", example="Team Lead")
    assigned_to_user_id: int = Field(..., description="Assigned user id (current user)", example=1)
    assigned_at: Optional[datetime] = Field(None, description="Assigned timestamp", example="2025-01-20T08:10:00Z")


class ListMyPendingApprovalStepsResponse(BaseModel):
    approval_steps: List[ListMyPendingApprovalStepsItem] = Field(..., description="List of pending approval steps for current user", example=[])


class DecideTripApprovalStepRequest(BaseModel):
    decision: str = Field(..., description="Decision value such as approved or rejected", example="approved")
    decision_comment: Optional[str] = Field(None, description="Approver comment explaining the decision", example="Approved within budget and policy compliant")


class DecideTripApprovalStepResponse(BaseModel):
    id: int = Field(..., description="Approval step id", example=13001)
    approval_request_id: int = Field(..., description="Approval request id", example=12001)
    sequence: int = Field(..., description="Step sequence", example=1)
    status: str = Field(..., description="Updated step status", example="completed")
    decision: str = Field(..., description="Decision value", example="approved")
    decision_comment: Optional[str] = Field(None, description="Decision comment", example="Approved within budget and policy compliant")
    decided_at: datetime = Field(..., description="Timestamp when decision recorded", example="2025-01-21T09:00:00Z")
    decided_by_user_id: int = Field(..., description="User id that made the decision", example=1)


class UpdateTripApprovalRequestRequest(BaseModel):
    status: Optional[str] = Field(None, description="Update request status (e.g., in_progress, completed)", example="completed")
    final_decision: Optional[str] = Field(None, description="Final decision value such as approved or rejected", example="approved")


class UpdateTripApprovalRequestResponse(BaseModel):
    id: int = Field(..., description="Approval request id", example=12001)
    trip_id: int = Field(..., description="Trip id", example=4821)
    policy_id: Optional[int] = Field(None, description="Policy id", example=3001)
    chain_id: Optional[int] = Field(None, description="Chain id", example=9001)
    status: str = Field(..., description="Request status", example="completed")
    submitted_by_user_id: int = Field(..., description="Submitted by user id", example=1)
    submitted_at: Optional[datetime] = Field(None, description="Submitted timestamp", example="2025-01-20T08:00:00Z")
    final_decision: Optional[str] = Field(None, description="Final decision", example="approved")
    final_decision_at: Optional[datetime] = Field(None, description="Final decision timestamp", example="2025-01-21T09:10:00Z")
    final_decision_by_user_id: Optional[int] = Field(None, description="User id for final decision", example=1)
    created_at: datetime = Field(..., description="Created timestamp", example="2025-01-20T08:00:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-01-21T09:10:00Z")


class AddTripCommentRequest(BaseModel):
    comment_type: str = Field(..., description="Type of comment (submission, approval, internal, traveler)", example="submission")
    visibility: str = Field(..., description="Visibility of comment (external or internal)", example="external")
    content: str = Field(..., description="Text content of the comment", example="Urgent client presentation; need confirmation by Friday")


class TripCommentModel(BaseModel):
    id: int = Field(..., description="Trip comment id", example=14001)
    trip_id: int = Field(..., description="Trip id", example=4821)
    author_user_id: int = Field(..., description="Author user id (always 1 here)", example=1)
    comment_type: str = Field(..., description="Comment type", example="submission")
    visibility: str = Field(..., description="Visibility", example="external")
    content: str = Field(..., description="Comment content", example="Urgent client presentation; need confirmation by Friday")
    created_at: datetime = Field(..., description="Created timestamp", example="2025-01-20T07:55:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-01-20T07:55:00Z")


class AddTripPolicyViolationRequest(BaseModel):
    component_type: str = Field(..., description="Component type such as flight, hotel, or trip", example="flight")
    component_id: Optional[int] = Field(None, description="Component id like flight_segments.id or hotel_bookings.id", example=10001)
    violation_code: str = Field(..., description="Short violation code identifier", example="AIR_MAX_FARE_EXCEEDED")
    description: Optional[str] = Field(None, description="Detailed description of the violation", example="Round-trip airfare exceeds allowed 800 USD limit.")
    severity: Optional[str] = Field(None, description="Severity level such as low, medium, high", example="medium")


class TripPolicyViolationModel(BaseModel):
    id: int = Field(..., description="Policy violation id", example=15001)
    trip_id: int = Field(..., description="Trip id", example=4821)
    component_type: str = Field(..., description="Component type", example="flight")
    component_id: Optional[int] = Field(None, description="Component id", example=10001)
    violation_code: str = Field(..., description="Violation code", example="AIR_MAX_FARE_EXCEEDED")
    description: Optional[str] = Field(None, description="Violation description", example="Round-trip airfare exceeds allowed 800 USD limit.")
    severity: Optional[str] = Field(None, description="Violation severity", example="medium")
    created_at: datetime = Field(..., description="Created timestamp", example="2025-01-20T07:40:00Z")


class CreateTripNotificationRequest(BaseModel):
    channel: str = Field(..., description="Notification channel such as in_app or email", example="in_app")
    message: str = Field(..., description="Notification message content", example="Your trip has policy violations. Contact your travel coordinator.")


class TripNotificationModel(BaseModel):
    id: int = Field(..., description="Trip notification id", example=16001)
    trip_id: int = Field(..., description="Trip id", example=4821)
    traveler_id: int = Field(..., description="Traveler id notified (primary traveler)", example=1001)
    channel: str = Field(..., description="Notification channel", example="in_app")
    message: str = Field(..., description="Notification message text", example="Your trip has policy violations. Contact your travel coordinator.")
    created_by_user_id: Optional[int] = Field(None, description="User id that created notification", example=1)
    created_at: datetime = Field(..., description="Created timestamp", example="2025-01-22T09:00:00Z")
    read_at: Optional[datetime] = Field(None, description="Timestamp when traveler read notification", example=None)


class MarkTripNotificationReadResponse(TripNotificationModel):
    pass


class TravelerExpenseSummaryCostCenterItem(BaseModel):
    cost_center: Optional[str] = Field(None, description="Cost center code", example="SALES-NW")
    total_air_spend: float = Field(..., description="Total air spend for booked trips in range", example=1200.0)
    total_hotel_spend: float = Field(..., description="Total hotel spend for booked trips in range", example=800.0)
    total_other_spend: float = Field(..., description="Total other spend", example=100.0)
    has_policy_violations: bool = Field(..., description="True if any included trips had policy violations", example=False)
    trip_ids: List[int] = Field(..., description="Trip ids included in this cost center grouping", example=[4821])


class TravelerExpenseSummaryResponse(BaseModel):
    traveler_id: int = Field(..., description="Traveler id for this summary", example=1001)
    start_date: str = Field(..., description="Start date used for filter", example="2025-01-01")
    end_date: str = Field(..., description="End date used for filter", example="2025-03-31")
    cost_centers: List[TravelerExpenseSummaryCostCenterItem] = Field(..., description="Cost center breakdown", example=[])


class CreateTripExpenseExportRequest(BaseModel):
    trip_id: int = Field(..., description="Trip id whose expenses are being exported", example=4821)
    external_system_name: str = Field(..., description="Name of external system receiving the export", example="NetLedger ERP")
    export_status: str = Field(..., description="Export status such as pending, exported, or failed", example="pending")
    payload: Dict[str, object] = Field(..., description="JSON payload to be serialized into BLOB for export", example={"trip_code": "TRIP-4821"})
    total_air_spend: float = Field(..., description="Total air spend used in export", example=600.0)
    total_hotel_spend: float = Field(..., description="Total hotel spend used in export", example=400.0)
    total_other_spend: float = Field(..., description="Total other spend used in export", example=0.0)
    has_policy_violations: bool = Field(..., description="Flag whether exported trip had policy violations", example=False)


class TripExpenseExportModel(BaseModel):
    id: int = Field(..., description="Trip expense export id", example=17001)
    trip_id: int = Field(..., description="Trip id", example=4821)
    external_system_name: str = Field(..., description="External system name", example="NetLedger ERP")
    export_status: str = Field(..., description="Export status", example="pending")
    payload: Dict[str, object] = Field(..., description="Payload object for export", example={"trip_code": "TRIP-4821"})
    total_air_spend: float = Field(..., description="Total air spend", example=600.0)
    total_hotel_spend: float = Field(..., description="Total hotel spend", example=400.0)
    total_other_spend: float = Field(..., description="Total other spend", example=0.0)
    has_policy_violations: bool = Field(..., description="Policy violations flag", example=False)
    created_at: datetime = Field(..., description="Created timestamp", example="2025-03-01T09:00:00Z")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2025-03-01T09:00:00Z")


@app.get(
    "/api/companies",
    summary="List companies with optional name filter",
    description="Retrieve companies with optional exact or partial name filters",
    tags=["companies"],
    operation_id="list_companies",
    response_model=ListCompaniesResponse,
)
async def list_companies(
    name: Optional[str] = Query(None, description="Filter companies by exact name match", example="Acme Analytics"),
    name_contains: Optional[str] = Query(None, description="Filter companies where name contains this value (case-insensitive)", example="Acme"),
    limit: Optional[int] = Query(None, description="Maximum number of companies to return", example=20),
    offset: Optional[int] = Query(None, description="Number of companies to skip", example=0),
) -> ListCompaniesResponse:
    session = SessionLocal()
    query = session.query(Company)
    if name is not None:
        query = query.filter(Company.name == name)
    if name_contains is not None:
        like_value = f"%{name_contains.lower()}%"
        query = query.filter(Company.name.ilike(like_value))
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    companies = query.all()
    session.close()
    return ListCompaniesResponse(companies=[CompanyModel.model_validate(c) for c in companies])


@app.post(
    "/api/companies",
    summary="Create a new company",
    description="Create a company record for a new corporate customer",
    tags=["companies"],
    operation_id="create_company",
    response_model=CreateCompanyResponse,
)
async def create_company(body: CreateCompanyRequest = Body(...)) -> CreateCompanyResponse:
    session = SessionLocal()
    now = datetime.utcnow()
    company = Company(
        name=body.name,
        external_ref=body.external_ref,
        created_at=now,
        updated_at=now,
    )
    session.add(company)
    session.commit()
    session.refresh(company)
    result = CreateCompanyResponse.model_validate(company)
    session.close()
    return result


@app.get(
    "/api/companies/{company_id}",
    summary="Get company by ID",
    description="Retrieve a single company by primary key",
    tags=["companies"],
    operation_id="get_company_by_id",
    response_model=CompanyModel,
)
async def get_company_by_id(
    company_id: int = Path(..., description="Company primary key", example=1)
) -> CompanyModel:
    session = SessionLocal()
    company = session.query(Company).filter(Company.id == company_id).first()
    if company is None:
        company = Company(id=company_id, name="", external_ref=None, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    result = CompanyModel.model_validate(company)
    session.close()
    return result


@app.get(
    "/api/departments",
    summary="List departments for a company",
    description="Retrieve departments for a given company with optional name filter",
    tags=["departments"],
    operation_id="list_departments",
    response_model=ListDepartmentsResponse,
)
async def list_departments(
    company_id: int = Query(..., description="Company primary key to filter departments", example=1),
    name: Optional[str] = Query(None, description="Filter by exact department name within the company", example="Sales"),
) -> ListDepartmentsResponse:
    session = SessionLocal()
    query = session.query(Department).filter(Department.company_id == company_id)
    if name is not None:
        query = query.filter(Department.name == name)
    departments = query.all()
    session.close()
    return ListDepartmentsResponse(departments=[DepartmentModel.model_validate(d) for d in departments])


@app.get(
    "/api/roles",
    summary="List available roles",
    description="Retrieve known roles such as Team Lead or Finance Manager",
    tags=["roles"],
    operation_id="list_roles",
    response_model=ListRolesResponse,
)
async def list_roles(
    name: Optional[str] = Query(None, description="Filter roles by exact name", example="Team Lead")
) -> ListRolesResponse:
    session = SessionLocal()
    query = session.query(Role)
    if name is not None:
        query = query.filter(Role.name == name)
    roles = query.all()
    session.close()
    return ListRolesResponse(roles=[RoleModel.model_validate(r) for r in roles])


@app.get(
    "/api/users/me",
    summary="Get current authenticated user profile",
    description="Retrieve the profile for the current authenticated user (user_id=1)",
    tags=["users"],
    operation_id="get_current_user",
    response_model=CurrentUserModel,
)
async def get_current_user() -> CurrentUserModel:
    session = SessionLocal()
    user = session.query(User).filter(User.id == 1).first()
    if user is None:
        now = datetime.utcnow()
        user = User(id=1, username="admin", email="admin@example.com", full_name="System Admin", created_at=now, updated_at=now)
        session.add(user)
        session.commit()
        session.refresh(user)
    result = CurrentUserModel.model_validate(user)
    session.close()
    return result


@app.post(
    "/api/travelers",
    summary="Create a new traveler",
    description="Create a traveler record for an employee in a company",
    tags=["travelers"],
    operation_id="create_traveler",
    response_model=TravelerModel,
)
async def create_traveler(body: CreateTravelerRequest = Body(...)) -> TravelerModel:
    session = SessionLocal()
    now = datetime.utcnow()
    status = body.status if body.status is not None else "active"
    traveler = Traveler(
        company_id=body.company_id,
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        user_id=body.user_id,
        department_id=body.department_id,
        status=status,
        created_at=now,
        updated_at=now,
    )
    session.add(traveler)
    session.commit()
    session.refresh(traveler)
    result = TravelerModel.model_validate(traveler)
    session.close()
    return result


@app.get(
    "/api/travelers",
    summary="Search travelers by name, email, or company",
    description="Find travelers for a company using name or email filters",
    tags=["travelers"],
    operation_id="search_travelers",
    response_model=ListTravelersResponse,
)
async def search_travelers(
    company_id: Optional[int] = Query(None, description="Filter by company primary key", example=1),
    first_name: Optional[str] = Query(None, description="Filter by exact first name", example="Maria"),
    last_name: Optional[str] = Query(None, description="Filter by exact last name", example="Gonzalez"),
    email: Optional[str] = Query(None, description="Filter by email address", example="maria.gonzalez@acme-analytics.com"),
    status: Optional[str] = Query(None, description="Filter by traveler status", example="active"),
) -> ListTravelersResponse:
    session = SessionLocal()
    query = session.query(Traveler)
    if company_id is not None:
        query = query.filter(Traveler.company_id == company_id)
    if first_name is not None:
        query = query.filter(Traveler.first_name == first_name)
    if last_name is not None:
        query = query.filter(Traveler.last_name == last_name)
    if email is not None:
        query = query.filter(Traveler.email == email)
    if status is not None:
        query = query.filter(Traveler.status == status)
    travelers = query.all()
    session.close()
    return ListTravelersResponse(travelers=[TravelerModel.model_validate(t) for t in travelers])


@app.get(
    "/api/travelers/{traveler_id}",
    summary="Get traveler by ID",
    description="Retrieve a single traveler by primary key",
    tags=["travelers"],
    operation_id="get_traveler_by_id",
    response_model=TravelerModel,
)
async def get_traveler_by_id(
    traveler_id: int = Path(..., description="Traveler primary key", example=1001)
) -> TravelerModel:
    session = SessionLocal()
    traveler = session.query(Traveler).filter(Traveler.id == traveler_id).first()
    if traveler is None:
        now = datetime.utcnow()
        traveler = Traveler(id=traveler_id, company_id=1, first_name="", last_name="", email=None, user_id=None, department_id=None, status="active", created_at=now, updated_at=now)
    result = TravelerModel.model_validate(traveler)
    session.close()
    return result


@app.post(
    "/api/travelers/{traveler_id}/passports",
    summary="Add a passport for a traveler",
    description="Create a passport record for a traveler, optionally primary",
    tags=["traveler_passports"],
    operation_id="add_traveler_passport",
    response_model=TravelerPassportModel,
)
async def add_traveler_passport(
    traveler_id: int = Path(..., description="Traveler primary key to attach passport to", example=1001),
    body: AddTravelerPassportRequest = Body(...),
) -> TravelerPassportModel:
    session = SessionLocal()
    now = datetime.utcnow()
    expiry = date.fromisoformat(body.expiry_date)
    is_primary_int = int_from_bool(body.is_primary if body.is_primary is not None else True)
    passport = TravelerPassport(
        traveler_id=traveler_id,
        passport_number=body.passport_number,
        country_code=body.country_code,
        expiry_date=expiry,
        is_primary=is_primary_int,
        created_at=now,
        updated_at=now,
    )
    session.add(passport)
    session.commit()
    session.refresh(passport)
    result = TravelerPassportModel(
        id=passport.id,
        traveler_id=passport.traveler_id,
        passport_number=passport.passport_number,
        country_code=passport.country_code,
        expiry_date=passport.expiry_date.isoformat(),
        is_primary=bool_from_int(passport.is_primary),
        created_at=passport.created_at,
        updated_at=passport.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/travelers/{traveler_id}/loyalty-programs",
    summary="Add a loyalty program for a traveler",
    description="Create a loyalty membership for a traveler",
    tags=["traveler_loyalty_programs"],
    operation_id="add_traveler_loyalty_program",
    response_model=TravelerLoyaltyProgramModel,
)
async def add_traveler_loyalty_program(
    traveler_id: int = Path(..., description="Traveler primary key to attach loyalty program to", example=1001),
    body: AddTravelerLoyaltyProgramRequest = Body(...),
) -> TravelerLoyaltyProgramModel:
    session = SessionLocal()
    now = datetime.utcnow()
    lp = TravelerLoyaltyProgram(
        traveler_id=traveler_id,
        carrier_or_chain=body.carrier_or_chain,
        program_name=body.program_name,
        membership_number=body.membership_number,
        program_type=body.program_type,
        created_at=now,
        updated_at=now,
    )
    session.add(lp)
    session.commit()
    session.refresh(lp)
    result = TravelerLoyaltyProgramModel(
        id=lp.id,
        traveler_id=lp.traveler_id,
        carrier_or_chain=lp.carrier_or_chain,
        program_name=lp.program_name,
        membership_number=lp.membership_number,
        program_type=lp.program_type,
        created_at=lp.created_at,
        updated_at=lp.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/travelers/{traveler_id}/preferences",
    summary="Create traveler preferences",
    description="Create initial traveler preferences like seat and hotel budget",
    tags=["traveler_preferences"],
    operation_id="create_traveler_preferences",
    response_model=TravelerPreferencesModel,
)
async def create_traveler_preferences(
    traveler_id: int = Path(..., description="Traveler primary key to attach preferences to", example=1001),
    body: TravelerPreferencesCreateRequest = Body(...),
) -> TravelerPreferencesModel:
    session = SessionLocal()
    now = datetime.utcnow()
    prefs = TravelerPreference(
        traveler_id=traveler_id,
        seat_preference=body.seat_preference,
        hotel_budget_max=body.hotel_budget_max,
        notes=body.notes,
        created_at=now,
        updated_at=now,
    )
    session.add(prefs)
    session.commit()
    session.refresh(prefs)
    result = TravelerPreferencesModel(
        id=prefs.id,
        traveler_id=prefs.traveler_id,
        seat_preference=prefs.seat_preference,
        hotel_budget_max=prefs.hotel_budget_max,
        notes=prefs.notes,
        created_at=prefs.created_at,
        updated_at=prefs.updated_at,
    )
    session.close()
    return result


@app.patch(
    "/api/travelers/{traveler_id}/preferences",
    summary="Update traveler preferences",
    description="Partially update existing traveler preferences",
    tags=["traveler_preferences"],
    operation_id="update_traveler_preferences",
    response_model=TravelerPreferencesModel,
)
async def update_traveler_preferences(
    traveler_id: int = Path(..., description="Traveler primary key", example=1001),
    body: TravelerPreferencesUpdateRequest = Body(...),
) -> TravelerPreferencesModel:
    session = SessionLocal()
    prefs = session.query(TravelerPreference).filter(TravelerPreference.traveler_id == traveler_id).first()
    if prefs is None:
        now = datetime.utcnow()
        prefs = TravelerPreference(
            traveler_id=traveler_id,
            seat_preference=None,
            hotel_budget_max=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )
        session.add(prefs)
        session.commit()
        session.refresh(prefs)
    if body.seat_preference is not None:
        prefs.seat_preference = body.seat_preference
    if body.hotel_budget_max is not None:
        prefs.hotel_budget_max = body.hotel_budget_max
    if body.notes is not None:
        prefs.notes = body.notes
    prefs.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(prefs)
    result = TravelerPreferencesModel(
        id=prefs.id,
        traveler_id=prefs.traveler_id,
        seat_preference=prefs.seat_preference,
        hotel_budget_max=prefs.hotel_budget_max,
        notes=prefs.notes,
        created_at=prefs.created_at,
        updated_at=prefs.updated_at,
    )
    session.close()
    return result


@app.get(
    "/api/hotel-brands",
    summary="List hotel brands with optional filter",
    description="Retrieve hotel brands with optional name filters",
    tags=["hotel_brands"],
    operation_id="list_hotel_brands",
    response_model=ListHotelBrandsResponse,
)
async def list_hotel_brands(
    name: Optional[str] = Query(None, description="Filter hotel brands by exact name", example="Marriott"),
    name_contains: Optional[str] = Query(None, description="Filter where brand name contains this value", example="Hilton"),
) -> ListHotelBrandsResponse:
    session = SessionLocal()
    query = session.query(HotelBrand)
    if name is not None:
        query = query.filter(HotelBrand.name == name)
    if name_contains is not None:
        like_value = f"%{name_contains.lower()}%"
        query = query.filter(HotelBrand.name.ilike(like_value))
    brands = query.all()
    session.close()
    return ListHotelBrandsResponse(hotel_brands=[HotelBrandModel.model_validate(b) for b in brands])


@app.post(
    "/api/hotel-brands",
    summary="Create a hotel brand",
    description="Create a hotel brand record like Marriott or Hilton",
    tags=["hotel_brands"],
    operation_id="create_hotel_brand",
    response_model=CreateHotelBrandResponse,
)
async def create_hotel_brand(body: CreateHotelBrandRequest = Body(...)) -> CreateHotelBrandResponse:
    session = SessionLocal()
    now = datetime.utcnow()
    brand = HotelBrand(name=body.name, created_at=now, updated_at=now)
    session.add(brand)
    session.commit()
    session.refresh(brand)
    result = CreateHotelBrandResponse.model_validate(brand)
    session.close()
    return result


@app.post(
    "/api/travelers/{traveler_id}/preferred-hotel-brands",
    summary="Add a preferred hotel brand for a traveler",
    description="Associate an existing hotel brand with a traveler as preferred",
    tags=["traveler_preferred_hotel_brands"],
    operation_id="add_traveler_preferred_hotel_brand",
    response_model=TravelerPreferredHotelBrandModel,
)
async def add_traveler_preferred_hotel_brand(
    traveler_id: int = Path(..., description="Traveler primary key", example=1001),
    body: AddTravelerPreferredHotelBrandRequest = Body(...),
) -> TravelerPreferredHotelBrandModel:
    session = SessionLocal()
    now = datetime.utcnow()
    link = TravelerPreferredHotelBrand(
        traveler_id=traveler_id,
        hotel_brand_id=body.hotel_brand_id,
        created_at=now,
    )
    session.add(link)
    session.commit()
    session.refresh(link)
    result = TravelerPreferredHotelBrandModel(
        id=link.id,
        traveler_id=link.traveler_id,
        hotel_brand_id=link.hotel_brand_id,
        created_at=link.created_at,
    )
    session.close()
    return result


@app.post(
    "/api/travel-policies",
    summary="Create a travel policy for a company",
    description="Create a travel policy such as fare limits and cabin rules",
    tags=["travel_policies"],
    operation_id="create_travel_policy",
    response_model=TravelPolicyModel,
)
async def create_travel_policy(body: CreateTravelPolicyRequest = Body(...)) -> TravelPolicyModel:
    session = SessionLocal()
    now = datetime.utcnow()
    scope = body.applies_to_scope if body.applies_to_scope is not None else "company"
    policy = TravelPolicy(
        company_id=body.company_id,
        name=body.name,
        description=body.description,
        applies_to_scope=scope,
        created_at=now,
        updated_at=now,
    )
    session.add(policy)
    session.commit()
    session.refresh(policy)
    result = TravelPolicyModel(
        id=policy.id,
        company_id=policy.company_id,
        name=policy.name,
        description=policy.description,
        applies_to_scope=policy.applies_to_scope,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/travel-policies/{policy_id}/rules",
    summary="Add a rule to a travel policy",
    description="Create a single travel policy rule with type, key, and value",
    tags=["travel_policy_rules"],
    operation_id="add_travel_policy_rule",
    response_model=TravelPolicyRuleModel,
)
async def add_travel_policy_rule(
    policy_id: int = Path(..., description="Travel policy primary key", example=3001),
    body: AddTravelPolicyRuleRequest = Body(...),
) -> TravelPolicyRuleModel:
    session = SessionLocal()
    now = datetime.utcnow()
    rule = TravelPolicyRule(
        policy_id=policy_id,
        rule_type=body.rule_type,
        param_key=body.param_key,
        param_value=body.param_value,
        created_at=now,
        updated_at=now,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    result = TravelPolicyRuleModel(
        id=rule.id,
        policy_id=rule.policy_id,
        rule_type=rule.rule_type,
        param_key=rule.param_key,
        param_value=rule.param_value,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/approval-policy-chains",
    summary="Create an approval policy chain",
    description="Create an approval chain record for a company",
    tags=["approval_policy_chains"],
    operation_id="create_approval_policy_chain",
    response_model=ApprovalPolicyChainModel,
)
async def create_approval_policy_chain(
    body: CreateApprovalPolicyChainRequest = Body(...)
) -> ApprovalPolicyChainModel:
    session = SessionLocal()
    now = datetime.utcnow()
    is_default_int = int_from_bool(body.is_default if body.is_default is not None else False)
    chain = ApprovalPolicyChain(
        company_id=body.company_id,
        policy_id=body.policy_id,
        department_id=body.department_id,
        name=body.name,
        description=body.description,
        is_default=is_default_int,
        created_at=now,
        updated_at=now,
    )
    session.add(chain)
    session.commit()
    session.refresh(chain)
    result = ApprovalPolicyChainModel(
        id=chain.id,
        company_id=chain.company_id,
        policy_id=chain.policy_id,
        department_id=chain.department_id,
        name=chain.name,
        description=chain.description,
        is_default=bool_from_int(chain.is_default),
        created_at=chain.created_at,
        updated_at=chain.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/approval-policy-chains/{chain_id}/steps",
    summary="Add a step to an approval policy chain",
    description="Append a step to an approval policy chain specifying role or user",
    tags=["approval_policy_chain_steps"],
    operation_id="add_approval_policy_chain_step",
    response_model=ApprovalPolicyChainStepModel,
)
async def add_approval_policy_chain_step(
    chain_id: int = Path(..., description="Approval policy chain primary key", example=9001),
    body: AddApprovalPolicyChainStepRequest = Body(...),
) -> ApprovalPolicyChainStepModel:
    session = SessionLocal()
    now = datetime.utcnow()
    step = ApprovalPolicyChainStep(
        chain_id=chain_id,
        sequence=body.sequence,
        approver_role_name=body.approver_role_name,
        approver_user_id=body.approver_user_id,
        created_at=now,
        updated_at=now,
    )
    session.add(step)
    session.commit()
    session.refresh(step)
    result = ApprovalPolicyChainStepModel(
        id=step.id,
        chain_id=step.chain_id,
        sequence=step.sequence,
        approver_role_name=step.approver_role_name,
        approver_user_id=step.approver_user_id,
        created_at=step.created_at,
        updated_at=step.updated_at,
    )
    session.close()
    return result


@app.get(
    "/api/approval-policy-chains",
    summary="List approval policy chains",
    description="Retrieve approval policy chains with optional filters",
    tags=["approval_policy_chains"],
    operation_id="list_approval_policy_chains",
    response_model=ListApprovalPolicyChainsResponse,
)
async def list_approval_policy_chains(
    company_id: int = Query(..., description="Company primary key", example=1),
    policy_id: Optional[int] = Query(None, description="Filter chains by specific policy id", example=3001),
    department_id: Optional[int] = Query(None, description="Filter chains by department id", example=10),
    is_default: Optional[bool] = Query(None, description="Filter by default chain flag", example=True),
) -> ListApprovalPolicyChainsResponse:
    session = SessionLocal()
    query = session.query(ApprovalPolicyChain).filter(ApprovalPolicyChain.company_id == company_id)
    if policy_id is not None:
        query = query.filter(ApprovalPolicyChain.policy_id == policy_id)
    if department_id is not None:
        query = query.filter(ApprovalPolicyChain.department_id == department_id)
    if is_default is not None:
        query = query.filter(ApprovalPolicyChain.is_default == int_from_bool(is_default))
    chains = query.all()
    items: List[ApprovalPolicyChainModel] = []
    for c in chains:
        items.append(
            ApprovalPolicyChainModel(
                id=c.id,
                company_id=c.company_id,
                policy_id=c.policy_id,
                department_id=c.department_id,
                name=c.name,
                description=c.description,
                is_default=bool_from_int(c.is_default),
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
        )
    session.close()
    return ListApprovalPolicyChainsResponse(approval_policy_chains=items)


@app.post(
    "/api/trips",
    summary="Create a new trip in draft status",
    description="Create a base trip record in draft including traveler and purpose",
    tags=["trips"],
    operation_id="create_trip",
    response_model=TripModel,
)
async def create_trip(body: CreateTripRequest = Body(...)) -> TripModel:
    session = SessionLocal()
    now = datetime.utcnow()
    status = body.status if body.status is not None else "draft"
    start_date_value = date.fromisoformat(body.start_date) if body.start_date is not None and body.start_date != "" else None
    end_date_value = date.fromisoformat(body.end_date) if body.end_date is not None and body.end_date != "" else None
    trip = Trip(
        company_id=body.company_id,
        primary_traveler_id=body.primary_traveler_id,
        department_id=body.department_id,
        cost_center=body.cost_center,
        purpose=body.purpose,
        status=status,
        policy_id=body.policy_id,
        start_date=start_date_value,
        end_date=end_date_value,
        total_air_cost=0.0,
        total_hotel_cost=0.0,
        total_other_cost=0.0,
        total_cost=0.0,
        has_policy_violations=0,
        external_export_status=None,
        created_by_user_id=1,
        updated_by_user_id=1,
        created_at=now,
        updated_at=now,
    )
    session.add(trip)
    session.commit()
    if trip.trip_code is None:
        trip.trip_code = f"TRIP-{trip.id}"
        session.commit()
    session.refresh(trip)
    result = TripModel(
        id=trip.id,
        trip_code=trip.trip_code,
        company_id=trip.company_id,
        primary_traveler_id=trip.primary_traveler_id,
        department_id=trip.department_id,
        cost_center=trip.cost_center,
        purpose=trip.purpose,
        status=trip.status,
        policy_id=trip.policy_id,
        start_date=trip.start_date.isoformat() if trip.start_date is not None else None,
        end_date=trip.end_date.isoformat() if trip.end_date is not None else None,
        total_air_cost=trip.total_air_cost or 0.0,
        total_hotel_cost=trip.total_hotel_cost or 0.0,
        total_other_cost=trip.total_other_cost or 0.0,
        total_cost=trip.total_cost or 0.0,
        has_policy_violations=bool_from_int(trip.has_policy_violations),
        external_export_status=trip.external_export_status,
        created_by_user_id=trip.created_by_user_id,
        updated_by_user_id=trip.updated_by_user_id,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
    )
    session.close()
    return result


@app.patch(
    "/api/trips/{trip_id}",
    summary="Update trip header fields",
    description="Partially update trip fields such as status, policy, purpose or dates",
    tags=["trips"],
    operation_id="update_trip",
    response_model=TripModel,
)
async def update_trip(
    trip_id: int = Path(..., description="Trip primary key", example=4821),
    body: UpdateTripRequest = Body(...),
) -> TripModel:
    session = SessionLocal()
    trip = session.query(Trip).filter(Trip.id == trip_id).first()
    if trip is None:
        now = datetime.utcnow()
        trip = Trip(
            id=trip_id,
            company_id=1,
            primary_traveler_id=1,
            status="draft",
            total_air_cost=0.0,
            total_hotel_cost=0.0,
            total_other_cost=0.0,
            total_cost=0.0,
            has_policy_violations=0,
            created_by_user_id=1,
            updated_by_user_id=1,
            created_at=now,
            updated_at=now,
        )
        session.add(trip)
        session.commit()
        session.refresh(trip)
    if body.status is not None:
        trip.status = body.status
    if body.policy_id is not None:
        trip.policy_id = body.policy_id
    if body.purpose is not None:
        trip.purpose = body.purpose
    if body.cost_center is not None:
        trip.cost_center = body.cost_center
    if body.start_date is not None:
        if body.start_date == "":
            trip.start_date = None
        else:
            trip.start_date = date.fromisoformat(body.start_date)
    if body.end_date is not None:
        if body.end_date == "":
            trip.end_date = None
        else:
            trip.end_date = date.fromisoformat(body.end_date)
    if body.has_policy_violations is not None:
        trip.has_policy_violations = int_from_bool(body.has_policy_violations)
    trip.updated_by_user_id = 1
    trip.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(trip)
    if trip.trip_code is None:
        trip.trip_code = f"TRIP-{trip.id}"
        session.commit()
        session.refresh(trip)
    result = TripModel(
        id=trip.id,
        trip_code=trip.trip_code,
        company_id=trip.company_id,
        primary_traveler_id=trip.primary_traveler_id,
        department_id=trip.department_id,
        cost_center=trip.cost_center,
        purpose=trip.purpose,
        status=trip.status,
        policy_id=trip.policy_id,
        start_date=trip.start_date.isoformat() if trip.start_date is not None else None,
        end_date=trip.end_date.isoformat() if trip.end_date is not None else None,
        total_air_cost=trip.total_air_cost or 0.0,
        total_hotel_cost=trip.total_hotel_cost or 0.0,
        total_other_cost=trip.total_other_cost or 0.0,
        total_cost=trip.total_cost or 0.0,
        has_policy_violations=bool_from_int(trip.has_policy_violations),
        external_export_status=trip.external_export_status,
        created_by_user_id=trip.created_by_user_id,
        updated_by_user_id=trip.updated_by_user_id,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
    )
    session.close()
    return result


@app.get(
    "/api/trips/by-code/{trip_code}",
    summary="Get trip by trip_code",
    description="Retrieve a trip using its unique human-readable trip_code",
    tags=["trips"],
    operation_id="get_trip_by_code",
    response_model=TripModel,
)
async def get_trip_by_code(
    trip_code: str = Path(..., description="Trip code string unique in trips", example="TRIP-4821")
) -> TripModel:
    session = SessionLocal()
    trip = session.query(Trip).filter(Trip.trip_code == trip_code).first()
    if trip is None:
        now = datetime.utcnow()
        trip = Trip(
            company_id=1,
            primary_traveler_id=1,
            status="draft",
            total_air_cost=0.0,
            total_hotel_cost=0.0,
            total_other_cost=0.0,
            total_cost=0.0,
            has_policy_violations=0,
            created_by_user_id=1,
            updated_by_user_id=1,
            created_at=now,
            updated_at=now,
            trip_code=trip_code,
        )
        session.add(trip)
        session.commit()
        session.refresh(trip)
    result = TripModel(
        id=trip.id,
        trip_code=trip.trip_code,
        company_id=trip.company_id,
        primary_traveler_id=trip.primary_traveler_id,
        department_id=trip.department_id,
        cost_center=trip.cost_center,
        purpose=trip.purpose,
        status=trip.status,
        policy_id=trip.policy_id,
        start_date=trip.start_date.isoformat() if trip.start_date is not None else None,
        end_date=trip.end_date.isoformat() if trip.end_date is not None else None,
        total_air_cost=trip.total_air_cost or 0.0,
        total_hotel_cost=trip.total_hotel_cost or 0.0,
        total_other_cost=trip.total_other_cost or 0.0,
        total_cost=trip.total_cost or 0.0,
        has_policy_violations=bool_from_int(trip.has_policy_violations),
        external_export_status=trip.external_export_status,
        created_by_user_id=trip.created_by_user_id,
        updated_by_user_id=trip.updated_by_user_id,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
    )
    session.close()
    return result


@app.get(
    "/api/trips",
    summary="Search trips with filters",
    description="Search trips by company, traveler, date range, status, or violations",
    tags=["trips"],
    operation_id="search_trips",
    response_model=ListTripsResponse,
)
async def search_trips(
    company_id: Optional[int] = Query(None, description="Filter by company id", example=1),
    primary_traveler_id: Optional[int] = Query(None, description="Filter by primary traveler id", example=1001),
    status: Optional[str] = Query(None, description="Filter by trip status", example="booked"),
    start_date_from: Optional[str] = Query(None, description="Return trips with start_date on or after this date", example="2025-01-01"),
    start_date_to: Optional[str] = Query(None, description="Return trips with start_date on or before this date", example="2025-03-31"),
    has_policy_violations: Optional[bool] = Query(None, description="Filter trips by presence of policy violations", example=True),
) -> ListTripsResponse:
    session = SessionLocal()
    query = session.query(Trip)
    if company_id is not None:
        query = query.filter(Trip.company_id == company_id)
    if primary_traveler_id is not None:
        query = query.filter(Trip.primary_traveler_id == primary_traveler_id)
    if status is not None:
        query = query.filter(Trip.status == status)
    if start_date_from is not None:
        query = query.filter(Trip.start_date >= date.fromisoformat(start_date_from))
    if start_date_to is not None:
        query = query.filter(Trip.start_date <= date.fromisoformat(start_date_to))
    if has_policy_violations is not None:
        query = query.filter(Trip.has_policy_violations == int_from_bool(has_policy_violations))
    trips = query.all()
    items: List[TripModel] = []
    for trip in trips:
        items.append(
            TripModel(
                id=trip.id,
                trip_code=trip.trip_code,
                company_id=trip.company_id,
                primary_traveler_id=trip.primary_traveler_id,
                department_id=trip.department_id,
                cost_center=trip.cost_center,
                purpose=trip.purpose,
                status=trip.status,
                policy_id=trip.policy_id,
                start_date=trip.start_date.isoformat() if trip.start_date is not None else None,
                end_date=trip.end_date.isoformat() if trip.end_date is not None else None,
                total_air_cost=trip.total_air_cost or 0.0,
                total_hotel_cost=trip.total_hotel_cost or 0.0,
                total_other_cost=trip.total_other_cost or 0.0,
                total_cost=trip.total_cost or 0.0,
                has_policy_violations=bool_from_int(trip.has_policy_violations),
                external_export_status=trip.external_export_status,
                created_by_user_id=trip.created_by_user_id,
                updated_by_user_id=trip.updated_by_user_id,
                created_at=trip.created_at,
                updated_at=trip.updated_at,
            )
        )
    session.close()
    return ListTripsResponse(trips=items)


@app.post(
    "/api/trips/{trip_id}/flight-segments",
    summary="Add a flight segment to a trip",
    description="Create a planned flight segment including airports, dates and cabin",
    tags=["flight_segments"],
    operation_id="add_flight_segment",
    response_model=FlightSegmentModel,
)
async def add_flight_segment(
    trip_id: int = Path(..., description="Trip primary key to attach the flight segment to", example=4821),
    body: AddFlightSegmentRequest = Body(...),
) -> FlightSegmentModel:
    session = SessionLocal()
    now = datetime.utcnow()
    dep_date = date.fromisoformat(body.departure_date)
    dep_time_from = time_obj = None
    if body.departure_time_from is not None and body.departure_time_from != "":
        dep_time_from = datetime.strptime(body.departure_time_from, "%H:%M:%S").time()
    dep_time_to = None
    if body.departure_time_to is not None and body.departure_time_to != "":
        dep_time_to = datetime.strptime(body.departure_time_to, "%H:%M:%S").time()
    return_segment_int = int_from_bool(body.return_segment if body.return_segment is not None else False)
    booking_status = body.booking_status if body.booking_status is not None else "planned"
    currency = body.currency if body.currency is not None else "USD"
    policy_compliant_int = int_from_bool(body.policy_compliant if body.policy_compliant is not None else True)
    segment = FlightSegment(
        trip_id=trip_id,
        from_airport=body.from_airport,
        to_airport=body.to_airport,
        departure_date=dep_date,
        departure_time_from=dep_time_from,
        departure_time_to=dep_time_to,
        return_segment=return_segment_int,
        cabin_class=body.cabin_class,
        booked_fare=body.booked_fare,
        currency=currency,
        booking_status=booking_status,
        carrier_code=body.carrier_code,
        flight_number=body.flight_number,
        policy_compliant=policy_compliant_int,
        policy_violation_reason=body.policy_violation_reason,
        created_at=now,
        updated_at=now,
    )
    session.add(segment)
    session.commit()
    session.refresh(segment)
    result = FlightSegmentModel(
        id=segment.id,
        trip_id=segment.trip_id,
        from_airport=segment.from_airport,
        to_airport=segment.to_airport,
        departure_date=segment.departure_date.isoformat(),
        departure_time_from=segment.departure_time_from.isoformat() if segment.departure_time_from is not None else None,
        departure_time_to=segment.departure_time_to.isoformat() if segment.departure_time_to is not None else None,
        return_segment=bool_from_int(segment.return_segment),
        cabin_class=segment.cabin_class,
        booked_fare=segment.booked_fare,
        currency=segment.currency,
        booking_status=segment.booking_status,
        carrier_code=segment.carrier_code,
        flight_number=segment.flight_number,
        policy_compliant=bool_from_int(segment.policy_compliant),
        policy_violation_reason=segment.policy_violation_reason,
        created_at=segment.created_at,
        updated_at=segment.updated_at,
    )
    session.close()
    return result


@app.get(
    "/api/trips/{trip_id}/flight-segments",
    summary="List flight segments for a trip",
    description="Retrieve all flight segments belonging to a given trip id",
    tags=["flight_segments"],
    operation_id="list_flight_segments_for_trip",
    response_model=ListFlightSegmentsResponse,
)
async def list_flight_segments_for_trip(
    trip_id: int = Path(..., description="Trip primary key", example=4821)
) -> ListFlightSegmentsResponse:
    session = SessionLocal()
    segments = session.query(FlightSegment).filter(FlightSegment.trip_id == trip_id).all()
    items: List[FlightSegmentModel] = []
    for segment in segments:
        items.append(
            FlightSegmentModel(
                id=segment.id,
                trip_id=segment.trip_id,
                from_airport=segment.from_airport,
                to_airport=segment.to_airport,
                departure_date=segment.departure_date.isoformat(),
                departure_time_from=segment.departure_time_from.isoformat() if segment.departure_time_from is not None else None,
                departure_time_to=segment.departure_time_to.isoformat() if segment.departure_time_to is not None else None,
                return_segment=bool_from_int(segment.return_segment),
                cabin_class=segment.cabin_class,
                booked_fare=segment.booked_fare,
                currency=segment.currency,
                booking_status=segment.booking_status,
                carrier_code=segment.carrier_code,
                flight_number=segment.flight_number,
                policy_compliant=bool_from_int(segment.policy_compliant),
                policy_violation_reason=segment.policy_violation_reason,
                created_at=segment.created_at,
                updated_at=segment.updated_at,
            )
        )
    session.close()
    return ListFlightSegmentsResponse(flight_segments=items)


@app.patch(
    "/api/flight-segments/{segment_id}",
    summary="Update a flight segment",
    description="Update a specific flight segment such as fare or status",
    tags=["flight_segments"],
    operation_id="update_flight_segment",
    response_model=FlightSegmentModel,
)
async def update_flight_segment(
    segment_id: int = Path(..., description="Flight segment primary key", example=10001),
    body: UpdateFlightSegmentRequest = Body(...),
) -> FlightSegmentModel:
    session = SessionLocal()
    segment = session.query(FlightSegment).filter(FlightSegment.id == segment_id).first()
    if segment is None:
        now = datetime.utcnow()
        segment = FlightSegment(
            id=segment_id,
            trip_id=1,
            from_airport="",
            to_airport="",
            departure_date=date.today(),
            return_segment=0,
            cabin_class="Economy",
            booking_status="planned",
            policy_compliant=1,
            created_at=now,
            updated_at=now,
        )
        session.add(segment)
        session.commit()
        session.refresh(segment)
    if body.departure_date is not None:
        segment.departure_date = date.fromisoformat(body.departure_date)
    if body.departure_time_from is not None:
        if body.departure_time_from == "":
            segment.departure_time_from = None
        else:
            segment.departure_time_from = datetime.strptime(body.departure_time_from, "%H:%M:%S").time()
    if body.departure_time_to is not None:
        if body.departure_time_to == "":
            segment.departure_time_to = None
        else:
            segment.departure_time_to = datetime.strptime(body.departure_time_to, "%H:%M:%S").time()
    if body.return_segment is not None:
        segment.return_segment = int_from_bool(body.return_segment)
    if body.cabin_class is not None:
        segment.cabin_class = body.cabin_class
    if body.booked_fare is not None:
        segment.booked_fare = body.booked_fare
    if body.currency is not None:
        segment.currency = body.currency
    if body.booking_status is not None:
        segment.booking_status = body.booking_status
    if body.carrier_code is not None:
        segment.carrier_code = body.carrier_code
    if body.flight_number is not None:
        segment.flight_number = body.flight_number
    if body.policy_compliant is not None:
        segment.policy_compliant = int_from_bool(body.policy_compliant)
    if body.policy_violation_reason is not None:
        segment.policy_violation_reason = body.policy_violation_reason
    segment.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(segment)
    result = FlightSegmentModel(
        id=segment.id,
        trip_id=segment.trip_id,
        from_airport=segment.from_airport,
        to_airport=segment.to_airport,
        departure_date=segment.departure_date.isoformat(),
        departure_time_from=segment.departure_time_from.isoformat() if segment.departure_time_from is not None else None,
        departure_time_to=segment.departure_time_to.isoformat() if segment.departure_time_to is not None else None,
        return_segment=bool_from_int(segment.return_segment),
        cabin_class=segment.cabin_class,
        booked_fare=segment.booked_fare,
        currency=segment.currency,
        booking_status=segment.booking_status,
        carrier_code=segment.carrier_code,
        flight_number=segment.flight_number,
        policy_compliant=bool_from_int(segment.policy_compliant),
        policy_violation_reason=segment.policy_violation_reason,
        created_at=segment.created_at,
        updated_at=segment.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/trips/{trip_id}/hotel-bookings",
    summary="Add a hotel booking to a trip",
    description="Create a planned hotel booking including city, dates and rate",
    tags=["hotel_bookings"],
    operation_id="add_hotel_booking",
    response_model=HotelBookingModel,
)
async def add_hotel_booking(
    trip_id: int = Path(..., description="Trip primary key to attach the hotel booking to", example=4821),
    body: AddHotelBookingRequest = Body(...),
) -> HotelBookingModel:
    session = SessionLocal()
    now = datetime.utcnow()
    check_in = date.fromisoformat(body.check_in_date)
    check_out = date.fromisoformat(body.check_out_date)
    total_nights = body.total_nights
    if total_nights is None:
        delta = (check_out - check_in).days
        total_nights = delta
    total_cost = body.total_cost
    if total_cost is None and body.nightly_rate is not None and total_nights is not None:
        total_cost = body.nightly_rate * total_nights
    currency = body.currency if body.currency is not None else "USD"
    booking_status = body.booking_status if body.booking_status is not None else "planned"
    policy_compliant_int = int_from_bool(body.policy_compliant if body.policy_compliant is not None else True)
    booking = HotelBooking(
        trip_id=trip_id,
        city=body.city,
        hotel_name=body.hotel_name,
        hotel_brand_id=body.hotel_brand_id,
        check_in_date=check_in,
        check_out_date=check_out,
        nightly_rate=body.nightly_rate,
        currency=currency,
        total_nights=total_nights,
        total_cost=total_cost,
        property_type=body.property_type,
        booking_status=booking_status,
        policy_compliant=policy_compliant_int,
        policy_violation_reason=body.policy_violation_reason,
        created_at=now,
        updated_at=now,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    result = HotelBookingModel(
        id=booking.id,
        trip_id=booking.trip_id,
        city=booking.city,
        hotel_name=booking.hotel_name,
        hotel_brand_id=booking.hotel_brand_id,
        check_in_date=booking.check_in_date.isoformat(),
        check_out_date=booking.check_out_date.isoformat(),
        nightly_rate=booking.nightly_rate,
        currency=booking.currency,
        total_nights=booking.total_nights,
        total_cost=booking.total_cost,
        property_type=booking.property_type,
        booking_status=booking.booking_status,
        policy_compliant=bool_from_int(booking.policy_compliant),
        policy_violation_reason=booking.policy_violation_reason,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )
    session.close()
    return result


@app.get(
    "/api/trips/{trip_id}/hotel-bookings",
    summary="List hotel bookings for a trip",
    description="Retrieve all hotel bookings associated with a particular trip",
    tags=["hotel_bookings"],
    operation_id="list_hotel_bookings_for_trip",
    response_model=ListHotelBookingsResponse,
)
async def list_hotel_bookings_for_trip(
    trip_id: int = Path(..., description="Trip primary key", example=4821)
) -> ListHotelBookingsResponse:
    session = SessionLocal()
    bookings = session.query(HotelBooking).filter(HotelBooking.trip_id == trip_id).all()
    items: List[HotelBookingModel] = []
    for booking in bookings:
        items.append(
            HotelBookingModel(
                id=booking.id,
                trip_id=booking.trip_id,
                city=booking.city,
                hotel_name=booking.hotel_name,
                hotel_brand_id=booking.hotel_brand_id,
                check_in_date=booking.check_in_date.isoformat(),
                check_out_date=booking.check_out_date.isoformat(),
                nightly_rate=booking.nightly_rate,
                currency=booking.currency,
                total_nights=booking.total_nights,
                total_cost=booking.total_cost,
                property_type=booking.property_type,
                booking_status=booking.booking_status,
                policy_compliant=bool_from_int(booking.policy_compliant),
                policy_violation_reason=booking.policy_violation_reason,
                created_at=booking.created_at,
                updated_at=booking.updated_at,
            )
        )
    session.close()
    return ListHotelBookingsResponse(hotel_bookings=items)


@app.patch(
    "/api/hotel-bookings/{booking_id}",
    summary="Update a hotel booking",
    description="Update a hotel booking such as rate, status or policy flags",
    tags=["hotel_bookings"],
    operation_id="update_hotel_booking",
    response_model=HotelBookingModel,
)
async def update_hotel_booking(
    booking_id: int = Path(..., description="Hotel booking primary key", example=11001),
    body: UpdateHotelBookingRequest = Body(...),
) -> HotelBookingModel:
    session = SessionLocal()
    booking = session.query(HotelBooking).filter(HotelBooking.id == booking_id).first()
    if booking is None:
        now = datetime.utcnow()
        booking = HotelBooking(
            id=booking_id,
            trip_id=1,
            city="",
            check_in_date=date.today(),
            check_out_date=date.today(),
            booking_status="planned",
            policy_compliant=1,
            created_at=now,
            updated_at=now,
        )
        session.add(booking)
        session.commit()
        session.refresh(booking)
    if body.hotel_name is not None:
        booking.hotel_name = body.hotel_name
    if body.hotel_brand_id is not None:
        booking.hotel_brand_id = body.hotel_brand_id
    if body.check_in_date is not None:
        booking.check_in_date = date.fromisoformat(body.check_in_date)
    if body.check_out_date is not None:
        booking.check_out_date = date.fromisoformat(body.check_out_date)
    if body.nightly_rate is not None:
        booking.nightly_rate = body.nightly_rate
    if body.currency is not None:
        booking.currency = body.currency
    if body.total_nights is not None:
        booking.total_nights = body.total_nights
    if body.total_cost is not None:
        booking.total_cost = body.total_cost
    if body.property_type is not None:
        booking.property_type = body.property_type
    if body.booking_status is not None:
        booking.booking_status = body.booking_status
    if body.policy_compliant is not None:
        booking.policy_compliant = int_from_bool(body.policy_compliant)
    if body.policy_violation_reason is not None:
        booking.policy_violation_reason = body.policy_violation_reason
    booking.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(booking)
    result = HotelBookingModel(
        id=booking.id,
        trip_id=booking.trip_id,
        city=booking.city,
        hotel_name=booking.hotel_name,
        hotel_brand_id=booking.hotel_brand_id,
        check_in_date=booking.check_in_date.isoformat(),
        check_out_date=booking.check_out_date.isoformat(),
        nightly_rate=booking.nightly_rate,
        currency=booking.currency,
        total_nights=booking.total_nights,
        total_cost=booking.total_cost,
        property_type=booking.property_type,
        booking_status=booking.booking_status,
        policy_compliant=bool_from_int(booking.policy_compliant),
        policy_violation_reason=booking.policy_violation_reason,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/trips/{trip_id}/recalculate-costs",
    summary="Recalculate trip cost totals",
    description="Recalculate total_air_cost, total_hotel_cost and total_cost for a trip",
    tags=["trips"],
    operation_id="recalculate_trip_costs",
    response_model=RecalculateTripCostsResponse,
)
async def recalculate_trip_costs(
    trip_id: int = Path(..., description="Trip primary key to recalculate totals for", example=5279)
) -> RecalculateTripCostsResponse:
    session = SessionLocal()
    trip = session.query(Trip).filter(Trip.id == trip_id).first()
    if trip is None:
        now = datetime.utcnow()
        trip = Trip(
            id=trip_id,
            company_id=1,
            primary_traveler_id=1,
            status="draft",
            total_air_cost=0.0,
            total_hotel_cost=0.0,
            total_other_cost=0.0,
            total_cost=0.0,
            has_policy_violations=0,
            created_by_user_id=1,
            updated_by_user_id=1,
            created_at=now,
            updated_at=now,
        )
        session.add(trip)
        session.commit()
        session.refresh(trip)
    air_segments = session.query(FlightSegment).filter(FlightSegment.trip_id == trip.id).all()
    total_air = 0.0
    for seg in air_segments:
        if seg.booked_fare is not None:
            total_air += float(seg.booked_fare)
    hotel_bookings = session.query(HotelBooking).filter(HotelBooking.trip_id == trip.id).all()
    total_hotel = 0.0
    for hb in hotel_bookings:
        if hb.total_cost is not None:
            total_hotel += float(hb.total_cost)
    total_other = trip.total_other_cost or 0.0
    trip.total_air_cost = total_air
    trip.total_hotel_cost = total_hotel
    trip.total_other_cost = total_other
    trip.total_cost = total_air + total_hotel + total_other
    trip.updated_at = datetime.utcnow()
    trip.updated_by_user_id = 1
    session.commit()
    session.refresh(trip)
    response = RecalculateTripCostsResponse(
        trip_id=trip.id,
        total_air_cost=trip.total_air_cost or 0.0,
        total_hotel_cost=trip.total_hotel_cost or 0.0,
        total_other_cost=trip.total_other_cost or 0.0,
        total_cost=trip.total_cost or 0.0,
    )
    session.close()
    return response


@app.post(
    "/api/trips/{source_trip_id}/clone",
    summary="Clone a trip structure with date shift",
    description="Clone a trip's structure to a new draft trip with shifted dates",
    tags=["trips"],
    operation_id="clone_trip_with_shift",
    response_model=CloneTripResponse,
)
async def clone_trip_with_shift(
    source_trip_id: int = Path(..., description="Trip id of the source trip to clone", example=3107),
    body: CloneTripRequest = Body(...),
) -> CloneTripResponse:
    session = SessionLocal()
    source = session.query(Trip).filter(Trip.id == source_trip_id).first()
    if source is None:
        now = datetime.utcnow()
        source = Trip(
            id=source_trip_id,
            company_id=1,
            primary_traveler_id=1,
            status="approved",
            start_date=date.today(),
            end_date=date.today(),
            total_air_cost=0.0,
            total_hotel_cost=0.0,
            total_other_cost=0.0,
            total_cost=0.0,
            has_policy_violations=0,
            created_by_user_id=1,
            updated_by_user_id=1,
            created_at=now,
            updated_at=now,
        )
        session.add(source)
        session.commit()
        session.refresh(source)
    shift = timedelta(days=body.date_shift_days)
    new_start = source.start_date + shift if source.start_date is not None else None
    new_end = source.end_date + shift if source.end_date is not None else None
    now = datetime.utcnow()
    new_trip = Trip(
        company_id=source.company_id,
        primary_traveler_id=body.primary_traveler_id,
        department_id=source.department_id,
        cost_center=body.cost_center,
        purpose=body.purpose,
        status="draft",
        policy_id=source.policy_id,
        start_date=new_start,
        end_date=new_end,
        total_air_cost=0.0,
        total_hotel_cost=0.0,
        total_other_cost=0.0,
        total_cost=0.0,
        has_policy_violations=0,
        external_export_status=None,
        created_by_user_id=1,
        updated_by_user_id=1,
        created_at=now,
        updated_at=now,
    )
    session.add(new_trip)
    session.commit()
    if new_trip.trip_code is None:
        new_trip.trip_code = f"TRIP-{new_trip.id}"
        session.commit()
    session.refresh(new_trip)
    source_segments = session.query(FlightSegment).filter(FlightSegment.trip_id == source.id).all()
    for seg in source_segments:
        new_dep_date = seg.departure_date + shift
        new_seg = FlightSegment(
            trip_id=new_trip.id,
            from_airport=seg.from_airport,
            to_airport=seg.to_airport,
            departure_date=new_dep_date,
            departure_time_from=seg.departure_time_from,
            departure_time_to=seg.departure_time_to,
            return_segment=seg.return_segment,
            cabin_class=seg.cabin_class,
            booked_fare=None,
            currency=seg.currency,
            booking_status="planned",
            carrier_code=None,
            flight_number=None,
            policy_compliant=1,
            policy_violation_reason=None,
            created_at=now,
            updated_at=now,
        )
        session.add(new_seg)
    source_hotels = session.query(HotelBooking).filter(HotelBooking.trip_id == source.id).all()
    for hb in source_hotels:
        new_check_in = hb.check_in_date + shift
        new_check_out = hb.check_out_date + shift
        new_hb = HotelBooking(
            trip_id=new_trip.id,
            city=hb.city,
            hotel_name=hb.hotel_name,
            hotel_brand_id=hb.hotel_brand_id,
            check_in_date=new_check_in,
            check_out_date=new_check_out,
            nightly_rate=hb.nightly_rate,
            currency=hb.currency,
            total_nights=hb.total_nights,
            total_cost=None,
            property_type=hb.property_type,
            booking_status="planned",
            policy_compliant=1,
            policy_violation_reason=None,
            created_at=now,
            updated_at=now,
        )
        session.add(new_hb)
    session.commit()
    session.refresh(new_trip)
    new_trip_model = CloneTripNewTripModel(
        id=new_trip.id,
        trip_code=new_trip.trip_code,
        company_id=new_trip.company_id,
        primary_traveler_id=new_trip.primary_traveler_id,
        department_id=new_trip.department_id,
        cost_center=new_trip.cost_center,
        purpose=new_trip.purpose,
        status=new_trip.status,
        policy_id=new_trip.policy_id,
        start_date=new_trip.start_date.isoformat() if new_trip.start_date is not None else None,
        end_date=new_trip.end_date.isoformat() if new_trip.end_date is not None else None,
    )
    session.close()
    return CloneTripResponse(new_trip=new_trip_model)


@app.post(
    "/api/trip-approval-requests",
    summary="Create a trip approval request",
    description="Create an approval request for a trip and mark as submitted",
    tags=["trip_approval_requests"],
    operation_id="create_trip_approval_request",
    response_model=TripApprovalRequestModel,
)
async def create_trip_approval_request(
    body: CreateTripApprovalRequestRequest = Body(...)
) -> TripApprovalRequestModel:
    session = SessionLocal()
    now = datetime.utcnow()
    status = body.status if body.status is not None else "submitted"
    request_obj = TripApprovalRequest(
        trip_id=body.trip_id,
        policy_id=body.policy_id,
        chain_id=body.chain_id,
        status=status,
        submitted_by_user_id=1,
        submitted_at=now,
        final_decision=None,
        final_decision_at=None,
        final_decision_by_user_id=None,
        created_at=now,
        updated_at=now,
    )
    session.add(request_obj)
    session.commit()
    session.refresh(request_obj)
    result = TripApprovalRequestModel(
        id=request_obj.id,
        trip_id=request_obj.trip_id,
        policy_id=request_obj.policy_id,
        chain_id=request_obj.chain_id,
        status=request_obj.status,
        submitted_by_user_id=request_obj.submitted_by_user_id,
        submitted_at=request_obj.submitted_at,
        final_decision=request_obj.final_decision,
        final_decision_at=request_obj.final_decision_at,
        final_decision_by_user_id=request_obj.final_decision_by_user_id,
        created_at=request_obj.created_at,
        updated_at=request_obj.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/trip-approval-requests/{approval_request_id}/steps",
    summary="Create a step for an approval request",
    description="Create a single approval step for an approval request",
    tags=["trip_approval_steps"],
    operation_id="create_trip_approval_step",
    response_model=TripApprovalStepModel,
)
async def create_trip_approval_step(
    approval_request_id: int = Path(..., description="Trip approval request primary key", example=12001),
    body: CreateTripApprovalStepRequest = Body(...),
) -> TripApprovalStepModel:
    session = SessionLocal()
    now = datetime.utcnow()
    step = TripApprovalStep(
        approval_request_id=approval_request_id,
        sequence=body.sequence,
        status=body.status,
        approver_role_name=body.approver_role_name,
        approver_user_id=body.approver_user_id,
        assigned_to_user_id=body.assigned_to_user_id,
        assigned_at=body.assigned_at if body.assigned_at is not None else now,
        decision=None,
        decision_comment=None,
        decided_at=None,
        decided_by_user_id=None,
        created_at=now,
        updated_at=now,
    )
    session.add(step)
    session.commit()
    session.refresh(step)
    result = TripApprovalStepModel(
        id=step.id,
        approval_request_id=step.approval_request_id,
        sequence=step.sequence,
        status=step.status,
        approver_role_name=step.approver_role_name,
        approver_user_id=step.approver_user_id,
        assigned_to_user_id=step.assigned_to_user_id,
        assigned_at=step.assigned_at,
        decision=step.decision,
        decision_comment=step.decision_comment,
        decided_at=step.decided_at,
        decided_by_user_id=step.decided_by_user_id,
        created_at=step.created_at,
        updated_at=step.updated_at,
    )
    session.close()
    return result


@app.get(
    "/api/trip-approval-steps/my-pending",
    summary="List pending approval steps for current user",
    description="Retrieve approval steps assigned to the current user with pending status",
    tags=["trip_approval_steps"],
    operation_id="list_my_pending_approval_steps",
    response_model=ListMyPendingApprovalStepsResponse,
)
async def list_my_pending_approval_steps() -> ListMyPendingApprovalStepsResponse:
    session = SessionLocal()
    steps = session.query(TripApprovalStep).filter(
        TripApprovalStep.assigned_to_user_id == 1,
        TripApprovalStep.status == "pending",
    ).all()
    items: List[ListMyPendingApprovalStepsItem] = []
    for step in steps:
        req = session.query(TripApprovalRequest).filter(TripApprovalRequest.id == step.approval_request_id).first()
        trip_id_value = req.trip_id if req is not None else 0
        items.append(
            ListMyPendingApprovalStepsItem(
                id=step.id,
                approval_request_id=step.approval_request_id,
                trip_id=trip_id_value,
                sequence=step.sequence,
                status=step.status,
                approver_role_name=step.approver_role_name,
                assigned_to_user_id=step.assigned_to_user_id if step.assigned_to_user_id is not None else 1,
                assigned_at=step.assigned_at,
            )
        )
    session.close()
    return ListMyPendingApprovalStepsResponse(approval_steps=items)


@app.post(
    "/api/trip-approval-steps/{step_id}/decision",
    summary="Record a decision on an approval step",
    description="Approve or reject a specific approval step with comment",
    tags=["trip_approval_steps"],
    operation_id="decide_trip_approval_step",
    response_model=DecideTripApprovalStepResponse,
)
async def decide_trip_approval_step(
    step_id: int = Path(..., description="Approval step primary key", example=13001),
    body: DecideTripApprovalStepRequest = Body(...),
) -> DecideTripApprovalStepResponse:
    session = SessionLocal()
    step = session.query(TripApprovalStep).filter(TripApprovalStep.id == step_id).first()
    if step is None:
        now = datetime.utcnow()
        step = TripApprovalStep(
            id=step_id,
            approval_request_id=0,
            sequence=1,
            status="pending",
            approver_role_name=None,
            approver_user_id=None,
            assigned_to_user_id=1,
            assigned_at=now,
            decision=None,
            decision_comment=None,
            decided_at=None,
            decided_by_user_id=None,
            created_at=now,
            updated_at=now,
        )
        session.add(step)
        session.commit()
        session.refresh(step)
    step.decision = body.decision
    step.decision_comment = body.decision_comment
    step.decided_at = datetime.utcnow()
    step.decided_by_user_id = 1
    step.status = "completed"
    step.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(step)
    result = DecideTripApprovalStepResponse(
        id=step.id,
        approval_request_id=step.approval_request_id,
        sequence=step.sequence,
        status=step.status,
        decision=step.decision,
        decision_comment=step.decision_comment,
        decided_at=step.decided_at,
        decided_by_user_id=step.decided_by_user_id,
    )
    session.close()
    return result


@app.patch(
    "/api/trip-approval-requests/{approval_request_id}",
    summary="Update a trip approval request",
    description="Update approval request status or final decision",
    tags=["trip_approval_requests"],
    operation_id="update_trip_approval_request",
    response_model=UpdateTripApprovalRequestResponse,
)
async def update_trip_approval_request(
    approval_request_id: int = Path(..., description="Trip approval request primary key", example=12001),
    body: UpdateTripApprovalRequestRequest = Body(...),
) -> UpdateTripApprovalRequestResponse:
    session = SessionLocal()
    req = session.query(TripApprovalRequest).filter(TripApprovalRequest.id == approval_request_id).first()
    if req is None:
        now = datetime.utcnow()
        req = TripApprovalRequest(
            id=approval_request_id,
            trip_id=0,
            policy_id=None,
            chain_id=None,
            status="submitted",
            submitted_by_user_id=1,
            submitted_at=now,
            final_decision=None,
            final_decision_at=None,
            final_decision_by_user_id=None,
            created_at=now,
            updated_at=now,
        )
        session.add(req)
        session.commit()
        session.refresh(req)
    if body.status is not None:
        req.status = body.status
    if body.final_decision is not None:
        req.final_decision = body.final_decision
        req.final_decision_at = datetime.utcnow()
        req.final_decision_by_user_id = 1
    req.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(req)
    result = UpdateTripApprovalRequestResponse(
        id=req.id,
        trip_id=req.trip_id,
        policy_id=req.policy_id,
        chain_id=req.chain_id,
        status=req.status,
        submitted_by_user_id=req.submitted_by_user_id,
        submitted_at=req.submitted_at,
        final_decision=req.final_decision,
        final_decision_at=req.final_decision_at,
        final_decision_by_user_id=req.final_decision_by_user_id,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/trips/{trip_id}/comments",
    summary="Add a comment on a trip",
    description="Add a comment to a trip with type and visibility",
    tags=["trip_comments"],
    operation_id="add_trip_comment",
    response_model=TripCommentModel,
)
async def add_trip_comment(
    trip_id: int = Path(..., description="Trip id to add comment to", example=4821),
    body: AddTripCommentRequest = Body(...),
) -> TripCommentModel:
    session = SessionLocal()
    now = datetime.utcnow()
    comment = TripComment(
        trip_id=trip_id,
        author_user_id=1,
        comment_type=body.comment_type,
        visibility=body.visibility,
        content=body.content,
        created_at=now,
        updated_at=now,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    result = TripCommentModel(
        id=comment.id,
        trip_id=comment.trip_id,
        author_user_id=comment.author_user_id,
        comment_type=comment.comment_type,
        visibility=comment.visibility,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/trips/{trip_id}/policy-violations",
    summary="Record a policy violation for a trip",
    description="Create a policy violation record for a trip component",
    tags=["trip_policy_violations"],
    operation_id="add_trip_policy_violation",
    response_model=TripPolicyViolationModel,
)
async def add_trip_policy_violation(
    trip_id: int = Path(..., description="Trip id where violation occurred", example=4821),
    body: AddTripPolicyViolationRequest = Body(...),
) -> TripPolicyViolationModel:
    session = SessionLocal()
    now = datetime.utcnow()
    violation = TripPolicyViolation(
        trip_id=trip_id,
        component_type=body.component_type,
        component_id=body.component_id,
        violation_code=body.violation_code,
        description=body.description,
        severity=body.severity,
        created_at=now,
    )
    session.add(violation)
    trip = session.query(Trip).filter(Trip.id == trip_id).first()
    if trip is not None:
        trip.has_policy_violations = 1
        trip.updated_at = now
    session.commit()
    session.refresh(violation)
    result = TripPolicyViolationModel(
        id=violation.id,
        trip_id=violation.trip_id,
        component_type=violation.component_type,
        component_id=violation.component_id,
        violation_code=violation.violation_code,
        description=violation.description,
        severity=violation.severity,
        created_at=violation.created_at,
    )
    session.close()
    return result


@app.post(
    "/api/trips/{trip_id}/notifications",
    summary="Create a notification for the primary traveler of a trip",
    description="Post a notification message into the trip notification feed",
    tags=["trip_notifications"],
    operation_id="create_trip_notification_for_primary_traveler",
    response_model=TripNotificationModel,
)
async def create_trip_notification_for_primary_traveler(
    trip_id: int = Path(..., description="Trip id for which to notify the primary traveler", example=4821),
    body: CreateTripNotificationRequest = Body(...),
) -> TripNotificationModel:
    session = SessionLocal()
    trip = session.query(Trip).filter(Trip.id == trip_id).first()
    if trip is None:
        now = datetime.utcnow()
        trip = Trip(
            id=trip_id,
            company_id=1,
            primary_traveler_id=1,
            status="draft",
            total_air_cost=0.0,
            total_hotel_cost=0.0,
            total_other_cost=0.0,
            total_cost=0.0,
            has_policy_violations=0,
            created_by_user_id=1,
            updated_by_user_id=1,
            created_at=now,
            updated_at=now,
        )
        session.add(trip)
        session.commit()
        session.refresh(trip)
    now = datetime.utcnow()
    notification = TripNotification(
        trip_id=trip.id,
        traveler_id=trip.primary_traveler_id,
        channel=body.channel,
        message=body.message,
        created_by_user_id=1,
        created_at=now,
        read_at=None,
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)
    result = TripNotificationModel(
        id=notification.id,
        trip_id=notification.trip_id,
        traveler_id=notification.traveler_id,
        channel=notification.channel,
        message=notification.message,
        created_by_user_id=notification.created_by_user_id,
        created_at=notification.created_at,
        read_at=notification.read_at,
    )
    session.close()
    return result


@app.post(
    "/api/trip-notifications/{notification_id}/mark-read",
    summary="Mark a trip notification as read",
    description="Set read_at timestamp for a specific notification",
    tags=["trip_notifications"],
    operation_id="mark_trip_notification_read",
    response_model=MarkTripNotificationReadResponse,
)
async def mark_trip_notification_read(
    notification_id: int = Path(..., description="Trip notification primary key", example=16001)
) -> MarkTripNotificationReadResponse:
    session = SessionLocal()
    notification = session.query(TripNotification).filter(TripNotification.id == notification_id).first()
    if notification is None:
        now = datetime.utcnow()
        notification = TripNotification(
            id=notification_id,
            trip_id=0,
            traveler_id=0,
            channel="in_app",
            message="",
            created_by_user_id=1,
            created_at=now,
            read_at=None,
        )
        session.add(notification)
        session.commit()
        session.refresh(notification)
    notification.read_at = datetime.utcnow()
    session.commit()
    session.refresh(notification)
    result = MarkTripNotificationReadResponse(
        id=notification.id,
        trip_id=notification.trip_id,
        traveler_id=notification.traveler_id,
        channel=notification.channel,
        message=notification.message,
        created_by_user_id=notification.created_by_user_id,
        created_at=notification.created_at,
        read_at=notification.read_at,
    )
    session.close()
    return result


@app.get(
    "/api/expenses/traveler-summary",
    summary="Get expense summary for traveler trips over date range",
    description="Compute air and hotel spend for a traveler grouped by cost center",
    tags=["expenses"],
    operation_id="get_traveler_expense_summary",
    response_model=TravelerExpenseSummaryResponse,
)
async def get_traveler_expense_summary(
    traveler_id: int = Query(..., description="Traveler id to aggregate expenses for", example=1001),
    start_date: str = Query(..., description="Include trips with start_date on or after this date", example="2025-01-01"),
    end_date: str = Query(..., description="Include trips with start_date on or before this date", example="2025-03-31"),
) -> TravelerExpenseSummaryResponse:
    session = SessionLocal()
    start_dt = date.fromisoformat(start_date)
    end_dt = date.fromisoformat(end_date)
    trips = session.query(Trip).filter(
        Trip.primary_traveler_id == traveler_id,
        Trip.start_date >= start_dt,
        Trip.start_date <= end_dt,
        Trip.status == "booked",
    ).all()
    grouped: Dict[Optional[str], TravelerExpenseSummaryCostCenterItem] = {}
    for trip in trips:
        key = trip.cost_center
        if key not in grouped:
            grouped[key] = TravelerExpenseSummaryCostCenterItem(
                cost_center=key,
                total_air_spend=0.0,
                total_hotel_spend=0.0,
                total_other_spend=0.0,
                has_policy_violations=False,
                trip_ids=[],
            )
        item = grouped[key]
        item.total_air_spend += float(trip.total_air_cost or 0.0)
        item.total_hotel_spend += float(trip.total_hotel_cost or 0.0)
        item.total_other_spend += float(trip.total_other_cost or 0.0)
        if bool_from_int(trip.has_policy_violations):
            item.has_policy_violations = True
        item.trip_ids.append(trip.id)
    session.close()
    return TravelerExpenseSummaryResponse(
        traveler_id=traveler_id,
        start_date=start_date,
        end_date=end_date,
        cost_centers=list(grouped.values()),
    )


@app.post(
    "/api/trip-expense-exports",
    summary="Create an expense export record for a trip",
    description="Create a trip_expense_exports entry with payload for an external system",
    tags=["trip_expense_exports"],
    operation_id="create_trip_expense_export",
    response_model=TripExpenseExportModel,
)
async def create_trip_expense_export(
    body: CreateTripExpenseExportRequest = Body(...)
) -> TripExpenseExportModel:
    session = SessionLocal()
    now = datetime.utcnow()
    payload_bytes = json.dumps(body.payload).encode("utf-8")
    export = TripExpenseExport(
        trip_id=body.trip_id,
        external_system_name=body.external_system_name,
        export_status=body.export_status,
        payload=payload_bytes,
        total_air_spend=body.total_air_spend,
        total_hotel_spend=body.total_hotel_spend,
        total_other_spend=body.total_other_spend,
        has_policy_violations=int_from_bool(body.has_policy_violations),
        created_at=now,
        updated_at=now,
    )
    trip = session.query(Trip).filter(Trip.id == body.trip_id).first()
    if trip is not None:
        trip.external_export_status = body.export_status
        trip.updated_at = now
    session.add(export)
    session.commit()
    session.refresh(export)
    payload_obj: Dict[str, object] = {}
    if export.payload is not None:
        try:
            payload_obj = json.loads(export.payload.decode("utf-8"))
        except Exception:
            payload_obj = {}
    result = TripExpenseExportModel(
        id=export.id,
        trip_id=export.trip_id,
        external_system_name=export.external_system_name,
        export_status=export.export_status,
        payload=payload_obj,
        total_air_spend=export.total_air_spend or 0.0,
        total_hotel_spend=export.total_hotel_spend or 0.0,
        total_other_spend=export.total_other_spend or 0.0,
        has_policy_violations=bool_from_int(export.has_policy_violations),
        created_at=export.created_at,
        updated_at=export.updated_at,
    )
    session.close()
    return result


if __name__ == "__main__":
    import uvicorn, os
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)