from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os

database_url = os.getenv(
    "DATABASE_PATH", "sqlite:///outputs/databases/clinicconnect_multi_specialty_appointment_center.db"
)

engine = create_engine("sqlite:////mnt/genming/case-rerun-20261101/booking_and_reservations_5_0/unsteered/student/final.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

app = FastAPI(
    title="ClinicConnect Multi-Specialty Appointment Center",
    version="1.0.0",
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    email = Column(Text, nullable=False, unique=True)
    full_name = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    full_name = Column(Text, nullable=False)
    date_of_birth = Column(Date)
    sex = Column(Text)
    primary_phone = Column(Text)
    home_address_line1 = Column(Text)
    home_address_line2 = Column(Text)
    home_city = Column(Text)
    home_state = Column(Text)
    home_postal_code = Column(Text)
    home_country = Column(Text)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class PatientContact(Base):
    __tablename__ = "patient_contacts"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    contact_type = Column(Text, nullable=False)
    value = Column(Text, nullable=False)
    is_primary = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class PatientDependent(Base):
    __tablename__ = "patient_dependents"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    dependent_name = Column(Text, nullable=False)
    date_of_birth = Column(Date)
    relationship = Column(Text)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class InsuranceProvider(Base):
    __tablename__ = "insurance_providers"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class PatientInsurance(Base):
    __tablename__ = "patient_insurances"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    insurance_provider_id = Column(Integer, ForeignKey("insurance_providers.id"), nullable=False)
    member_id = Column(Text, nullable=False)
    is_default = Column(Integer, nullable=False, default=0)
    effective_date = Column(Date)
    expiration_date = Column(Date)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    __table_args__ = (UniqueConstraint("patient_id", "member_id"),)


class Specialty(Base):
    __tablename__ = "specialties"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    specialty_id = Column(Integer, ForeignKey("specialties.id"))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class ClinicLocation(Base):
    __tablename__ = "clinic_locations"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    code = Column(Text)
    address_line1 = Column(Text)
    address_line2 = Column(Text)
    city = Column(Text)
    state = Column(Text)
    postal_code = Column(Text)
    country = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True)
    full_name = Column(Text, nullable=False)
    npi_number = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class ProviderSpecialty(Base):
    __tablename__ = "provider_specialties"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class AppointmentType(Base):
    __tablename__ = "appointment_types"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    default_duration_minutes = Column(Integer, nullable=False)
    visit_mode = Column(Text, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class ProviderClinicSchedule(Base):
    __tablename__ = "provider_clinic_schedules"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    clinic_location_id = Column(Integer, ForeignKey("clinic_locations.id"), nullable=False)
    appointment_type_id = Column(Integer, ForeignKey("appointment_types.id"))
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Text, nullable=False)
    end_time = Column(Text, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class TimeSlot(Base):
    __tablename__ = "time_slots"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    clinic_location_id = Column(Integer, ForeignKey("clinic_locations.id"), nullable=False)
    appointment_type_id = Column(Integer, ForeignKey("appointment_types.id"), nullable=False)
    specialty_id = Column(Integer, ForeignKey("specialties.id"))
    visit_mode = Column(Text, nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    capacity_total = Column(Integer, nullable=False, default=1)
    capacity_booked = Column(Integer, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Text, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    dependent_id = Column(Integer, ForeignKey("patient_dependents.id"))
    provider_id = Column(Integer, ForeignKey("providers.id"))
    clinic_location_id = Column(Integer, ForeignKey("clinic_locations.id"), nullable=False)
    appointment_type_id = Column(Integer, ForeignKey("appointment_types.id"), nullable=False)
    specialty_id = Column(Integer, ForeignKey("specialties.id"))
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"))
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    visit_mode = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    reason_for_visit = Column(Text)
    insurance_id = Column(Integer, ForeignKey("patient_insurances.id"))
    referral_id = Column(Integer)
    is_imaging = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class AppointmentReminderSetting(Base):
    __tablename__ = "appointment_reminder_settings"
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Text, ForeignKey("appointments.id"), nullable=False)
    send_email = Column(Integer, nullable=False, default=0)
    send_sms = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    dependent_id = Column(Integer, ForeignKey("patient_dependents.id"))
    specialty_id = Column(Integer, ForeignKey("specialties.id"))
    provider_id = Column(Integer, ForeignKey("providers.id"))
    clinic_location_id = Column(Integer, ForeignKey("clinic_locations.id"))
    appointment_type_id = Column(Integer, ForeignKey("appointment_types.id"), nullable=False)
    visit_mode = Column(Text, nullable=False)
    preferred_after_time = Column(Text)
    preferred_before_time = Column(Text)
    weekdays_only = Column(Integer, nullable=False, default=0)
    min_notice_minutes = Column(Integer, nullable=False, default=0)
    auto_accept = Column(Integer, nullable=False, default=0)
    status = Column(Text, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class DiagnosisCode(Base):
    __tablename__ = "diagnosis_codes"
    id = Column(Integer, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    specialty_id = Column(Integer, ForeignKey("specialties.id"))
    referring_provider_name = Column(Text, nullable=False)
    diagnosis_code_id = Column(Integer, ForeignKey("diagnosis_codes.id"))
    referral_expiration_date = Column(Date, nullable=False)
    status = Column(Text, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class AppointmentReferral(Base):
    __tablename__ = "appointment_referrals"
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Text, ForeignKey("appointments.id"), nullable=False)
    referral_id = Column(Integer, ForeignKey("referrals.id"), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class AppointmentStatusHistory(Base):
    __tablename__ = "appointment_status_history"
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Text, ForeignKey("appointments.id"), nullable=False)
    old_status = Column(Text)
    new_status = Column(Text, nullable=False)
    changed_at = Column(DateTime)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"))
    note = Column(Text)


class AppointmentCheckin(Base):
    __tablename__ = "appointment_checkins"
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Text, ForeignKey("appointments.id"), nullable=False)
    check_in_time = Column(DateTime, nullable=False)
    exam_room = Column(Text)
    created_at = Column(DateTime)


class SatisfactionSurvey(Base):
    __tablename__ = "satisfaction_surveys"
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Text, ForeignKey("appointments.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    wait_time_minutes = Column(Integer)
    comments = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


Base.metadata.create_all(engine)


class PatientModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Patient unique identifier", example=10)
    user_id: int = Field(..., description="Linked users.id", example=1)
    full_name: str = Field(..., description="Patient full legal name", example="Jane Doe")
    date_of_birth: Optional[str] = Field(
        None, description="Date of birth in ISO format", example="1985-04-12"
    )
    sex: Optional[str] = Field(None, description="Sex of the patient", example="F")
    primary_phone: Optional[str] = Field(
        None,
        description="Primary phone number stored on patient record",
        example="+1-555-123-4567",
    )
    home_address_line1: Optional[str] = Field(
        None, description="Home address line 1", example="123 Main St"
    )
    home_address_line2: Optional[str] = Field(
        None, description="Home address line 2", example="Apt 4B"
    )
    home_city: Optional[str] = Field(
        None, description="Home city", example="Springfield"
    )
    home_state: Optional[str] = Field(
        None, description="Home state or region", example="IL"
    )
    home_postal_code: Optional[str] = Field(
        None, description="Postal code", example="62704"
    )
    home_country: Optional[str] = Field(
        None, description="Country name or code", example="USA"
    )
    is_active: bool = Field(
        ..., description="True if patient profile is active", example=True
    )
    created_at: Optional[str] = Field(
        None, description="Record creation timestamp", example="2025-01-01T10:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Record last update timestamp", example="2025-01-15T15:30:00Z"
    )


class PatientResponse(BaseModel):
    patient: PatientModel = Field(
        ..., description="Current patient profile", example={}
    )


class PatientUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(
        None, description="Updated full name for the patient", example="Jane A. Doe"
    )
    date_of_birth: Optional[str] = Field(
        None,
        description="Updated date of birth in ISO format",
        example="1985-04-12",
    )
    sex: Optional[str] = Field(
        None, description="Updated sex value", example="F"
    )
    primary_phone: Optional[str] = Field(
        None,
        description="Updated primary phone number",
        example="+1-555-777-8888",
    )
    home_address_line1: Optional[str] = Field(
        None, description="Updated home address line 1", example="456 Oak Avenue"
    )
    home_address_line2: Optional[str] = Field(
        None, description="Updated home address line 2", example="Unit 12"
    )
    home_city: Optional[str] = Field(
        None, description="Updated home city", example="Centerville"
    )
    home_state: Optional[str] = Field(
        None, description="Updated home state", example="CA"
    )
    home_postal_code: Optional[str] = Field(
        None, description="Updated home postal code", example="90001"
    )
    home_country: Optional[str] = Field(
        None, description="Updated home country", example="USA"
    )


class DependentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Dependent unique identifier", example=3)
    patient_id: int = Field(
        ..., description="Associated patient_id", example=10
    )
    dependent_name: str = Field(
        ..., description="Dependent's full name", example="Sam Doe"
    )
    date_of_birth: Optional[str] = Field(
        None,
        description="Dependent's date of birth in ISO format",
        example="2015-06-01",
    )
    relationship: Optional[str] = Field(
        None, description="Relationship to patient", example="Child"
    )
    is_active: bool = Field(
        ..., description="True if dependent is active", example=True
    )
    created_at: Optional[str] = Field(
        None,
        description="Record creation timestamp",
        example="2025-01-10T12:00:00Z",
    )
    updated_at: Optional[str] = Field(
        None,
        description="Record last update timestamp",
        example="2025-01-10T12:00:00Z",
    )


class DependentsResponse(BaseModel):
    dependents: List[DependentModel] = Field(
        ..., description="List of dependents", example=[]
    )


class PatientContactModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Contact record identifier", example=5)
    patient_id: int = Field(..., description="Linked patient id", example=10)
    contact_type: str = Field(
        ..., description="Type of contact", example="mobile"
    )
    value: str = Field(
        ..., description="Contact value like email or phone", example="+1-555-123-9000"
    )
    is_primary: bool = Field(
        ..., description="True if primary contact of this type", example=True
    )
    created_at: Optional[str] = Field(
        None, description="Record creation time", example="2025-01-02T10:15:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Record last update time", example="2025-01-02T10:15:00Z"
    )


class PatientContactsResponse(BaseModel):
    contacts: List[PatientContactModel] = Field(
        ..., description="List of contact records", example=[]
    )


class PatientContactCreateRequest(BaseModel):
    contact_type: str = Field(
        ..., description="Contact type", example="email"
    )
    value: str = Field(
        ..., description="Contact detail such as an email or phone number", example="jane.doe@example.com"
    )
    is_primary: Optional[bool] = Field(
        None,
        description="If true, mark this contact as primary for its type",
        example=True,
    )


class PatientContactCreateResponse(BaseModel):
    contact: PatientContactModel = Field(
        ..., description="Created contact record", example={}
    )


class InsuranceProviderModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Insurance provider identifier", example=4)
    name: str = Field(
        ..., description="Insurance provider name", example="HealthPlus Gold"
    )
    created_at: Optional[str] = Field(
        None, description="Creation timestamp", example="2024-06-01T09:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp", example="2024-06-01T09:00:00Z"
    )


class InsuranceProvidersResponse(BaseModel):
    insurance_providers: List[InsuranceProviderModel] = Field(
        ..., description="List of insurance providers", example=[]
    )


class PatientInsuranceModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Patient insurance record id", example=7)
    patient_id: int = Field(..., description="Linked patient id", example=10)
    insurance_provider_id: int = Field(
        ..., description="Linked insurance_providers.id", example=4
    )
    member_id: str = Field(
        ..., description="Member or policy identifier", example="HPG1234567"
    )
    is_default: bool = Field(
        ..., description="True if this is the default insurance", example=True
    )
    effective_date: Optional[str] = Field(
        None, description="Coverage effective date", example="2025-01-01"
    )
    expiration_date: Optional[str] = Field(
        None, description="Coverage end date", example="2025-12-31"
    )
    created_at: Optional[str] = Field(
        None, description="Creation timestamp", example="2025-01-05T09:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp", example="2025-01-05T09:00:00Z"
    )


class PatientInsurancesResponse(BaseModel):
    patient_insurances: List[PatientInsuranceModel] = Field(
        ..., description="List of patient insurances", example=[]
    )


class PatientInsuranceCreateRequest(BaseModel):
    insurance_provider_name: str = Field(
        ..., description="Name of insurance provider", example="HealthPlus Gold"
    )
    member_id: str = Field(
        ..., description="Member or policy ID", example="HPG1234567"
    )
    effective_date: Optional[str] = Field(
        None, description="Coverage start date in ISO format", example="2025-01-01"
    )
    expiration_date: Optional[str] = Field(
        None, description="Coverage end date in ISO format", example="2025-12-31"
    )
    set_as_default: Optional[bool] = Field(
        None,
        description="If true, make this the default insurance",
        example=True,
    )


class PatientInsuranceCreateResponse(BaseModel):
    patient_insurance: PatientInsuranceModel = Field(
        ..., description="Created patient insurance", example={}
    )


class PatientInsuranceSetDefaultResponse(BaseModel):
    patient_insurance: PatientInsuranceModel = Field(
        ..., description="Updated default patient insurance", example={}
    )


class SpecialtyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Specialty id", example=2)
    name: str = Field(..., description="Specialty name", example="Cardiology")
    created_at: Optional[str] = Field(
        None, description="Creation timestamp", example="2024-01-01T00:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp", example="2024-01-01T00:00:00Z"
    )


class SpecialtiesResponse(BaseModel):
    specialties: List[SpecialtyModel] = Field(
        ..., description="List of specialties", example=[]
    )


class DepartmentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Department id", example=5)
    name: str = Field(..., description="Department name", example="Cardiology Department")
    specialty_id: Optional[int] = Field(
        None, description="Linked specialty id or null", example=2
    )
    created_at: Optional[str] = Field(
        None, description="Creation timestamp", example="2024-01-10T00:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp", example="2024-01-10T00:00:00Z"
    )


class DepartmentsResponse(BaseModel):
    departments: List[DepartmentModel] = Field(
        ..., description="List of departments", example=[]
    )


class ClinicLocationModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Clinic location id", example=3)
    name: str = Field(..., description="Clinic name", example="Downtown Clinic")
    code: Optional[str] = Field(
        None, description="Short code for clinic", example="DTWN"
    )
    address_line1: Optional[str] = Field(
        None, description="Address line 1", example="100 Market St"
    )
    address_line2: Optional[str] = Field(
        None, description="Address line 2", example="Suite 200"
    )
    city: Optional[str] = Field(
        None, description="City name", example="Metropolis"
    )
    state: Optional[str] = Field(
        None, description="State or region", example="NY"
    )
    postal_code: Optional[str] = Field(
        None, description="Postal code", example="10001"
    )
    country: Optional[str] = Field(
        None, description="Country", example="USA"
    )
    created_at: Optional[str] = Field(
        None, description="Creation time", example="2024-05-01T00:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update time", example="2024-05-01T00:00:00Z"
    )


class ClinicLocationsResponse(BaseModel):
    clinic_locations: List[ClinicLocationModel] = Field(
        ..., description="List of clinic locations", example=[]
    )


class ProviderModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Provider id", example=11)
    full_name: str = Field(
        ..., description="Provider full name", example="Dr. Anita Rao"
    )
    npi_number: Optional[str] = Field(
        None,
        description="National Provider Identifier or similar id",
        example="1234567890",
    )
    created_at: Optional[str] = Field(
        None, description="Creation time", example="2023-01-01T00:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update time", example="2023-01-01T00:00:00Z"
    )


class ProvidersResponse(BaseModel):
    providers: List[ProviderModel] = Field(
        ..., description="List of providers", example=[]
    )


class AppointmentTypeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Appointment type id", example=1)
    name: str = Field(
        ..., description="Appointment type name", example="Standard consultation"
    )
    default_duration_minutes: int = Field(
        ..., description="Default duration in minutes", example=30
    )
    visit_mode: str = Field(
        ..., description="Visit mode", example="in_person"
    )
    created_at: Optional[str] = Field(
        None, description="Creation timestamp", example="2024-01-05T00:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp", example="2024-01-05T00:00:00Z"
    )


class AppointmentTypesResponse(BaseModel):
    appointment_types: List[AppointmentTypeModel] = Field(
        ..., description="List of appointment types", example=[]
    )


class TimeSlotModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Time slot identifier", example=1001)
    provider_id: Optional[int] = Field(
        None, description="Provider assigned to the slot, may be null", example=11
    )
    clinic_location_id: int = Field(
        ..., description="Clinic location for this slot", example=3
    )
    appointment_type_id: int = Field(
        ..., description="Appointment type allowed in this slot", example=1
    )
    specialty_id: Optional[int] = Field(
        None, description="Specialty associated with this slot", example=2
    )
    visit_mode: str = Field(
        ..., description="Visit mode for the slot", example="in_person"
    )
    start_datetime: str = Field(
        ..., description="Slot start datetime (ISO)", example="2025-03-02T09:00:00Z"
    )
    end_datetime: str = Field(
        ..., description="Slot end datetime (ISO)", example="2025-03-02T09:30:00Z"
    )
    capacity_total: int = Field(
        ..., description="Total capacity for this slot", example=1
    )
    capacity_booked: int = Field(
        ..., description="Already booked capacity", example=0
    )
    is_active: bool = Field(
        ..., description="True if slot is active", example=True
    )
    created_at: Optional[str] = Field(
        None, description="Creation timestamp", example="2025-02-20T10:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp", example="2025-02-20T10:00:00Z"
    )


class TimeSlotsResponse(BaseModel):
    time_slots: List[TimeSlotModel] = Field(
        ..., description="List of time slots", example=[]
    )


class AppointmentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Appointment id", example="APT-20451")
    patient_id: int = Field(..., description="Linked patient id", example=10)
    dependent_id: Optional[int] = Field(
        None, description="Dependent id if appointment is for a dependent", example=None
    )
    provider_id: Optional[int] = Field(
        None,
        description="Provider id or null for imaging without named provider",
        example=11,
    )
    clinic_location_id: int = Field(
        ..., description="Clinic location id", example=3
    )
    appointment_type_id: int = Field(
        ..., description="Appointment type id", example=1
    )
    specialty_id: Optional[int] = Field(
        None, description="Specialty id or null", example=2
    )
    time_slot_id: Optional[int] = Field(
        None, description="Booked time_slots.id if slot-based", example=1001
    )
    start_datetime: str = Field(
        ..., description="Appointment start datetime", example="2025-02-28T09:00:00Z"
    )
    end_datetime: str = Field(
        ..., description="Appointment end datetime", example="2025-02-28T09:30:00Z"
    )
    visit_mode: str = Field(
        ..., description="Visit mode string", example="in_person"
    )
    status: str = Field(
        ..., description="Appointment status value", example="completed"
    )
    reason_for_visit: Optional[str] = Field(
        None, description="Reason for visit text", example="Chest pain evaluation"
    )
    insurance_id: Optional[int] = Field(
        None, description="Linked patient_insurances.id or null", example=8
    )
    referral_id: Optional[int] = Field(
        None, description="Linked referrals.id if any", example=12
    )
    is_imaging: bool = Field(
        ..., description="True if this appointment is imaging", example=False
    )
    created_at: Optional[str] = Field(
        None, description="Creation timestamp", example="2025-02-20T10:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last updated timestamp", example="2025-02-20T10:30:00Z"
    )


class AppointmentsResponse(BaseModel):
    appointments: List[AppointmentModel] = Field(
        ..., description="List of appointments", example=[]
    )


class AppointmentCreateRequest(BaseModel):
    time_slot_id: int = Field(
        ..., description="time_slots.id to book", example=1001
    )
    dependent_id: Optional[int] = Field(
        None,
        description="patient_dependents.id if booking for a dependent child",
        example=3,
    )
    reason_for_visit: str = Field(
        ..., description="Free-text reason for visit", example="Intermittent chest pain for 2 weeks"
    )
    insurance_id: Optional[int] = Field(
        None,
        description="patient_insurances.id to link or null to use default",
        example=8,
    )
    referral_id: Optional[int] = Field(
        None, description="referrals.id for this visit if applicable", example=15
    )
    status: Optional[str] = Field(
        None, description="Initial status for the appointment", example="booked"
    )
    send_email: Optional[bool] = Field(
        None,
        description="If true, create appointment_reminder_settings with email",
        example=True,
    )
    send_sms: Optional[bool] = Field(
        None,
        description="If true, create appointment_reminder_settings with sms",
        example=True,
    )


class AppointmentReminderSettingsModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(
        ..., description="appointment_reminder_settings id", example=20
    )
    appointment_id: str = Field(
        ..., description="Associated appointment id", example="APT-50001"
    )
    send_email: bool = Field(
        ..., description="True if email reminders are enabled", example=True
    )
    send_sms: bool = Field(
        ..., description="True if SMS reminders are enabled", example=True
    )
    created_at: Optional[str] = Field(
        None,
        description="Reminder settings creation time",
        example="2025-02-25T08:00:00Z",
    )
    updated_at: Optional[str] = Field(
        None,
        description="Reminder settings last update time",
        example="2025-02-25T08:00:00Z",
    )


class AppointmentCreateResponse(BaseModel):
    appointment: AppointmentModel = Field(
        ..., description="Created appointment", example={}
    )
    reminder_settings: Optional[AppointmentReminderSettingsModel] = Field(
        None, description="Created reminder settings if any", example={}
    )


class AppointmentByIdResponse(BaseModel):
    appointment: AppointmentModel = Field(
        ..., description="Appointment details", example={}
    )


class AppointmentPatchRequest(BaseModel):
    reason_for_visit: Optional[str] = Field(
        None, description="New reason for visit text", example="Follow-up MRI for left shoulder tear"
    )
    insurance_id: Optional[int] = Field(
        None, description="Updated patient_insurances.id to link", example=8
    )
    status: Optional[str] = Field(
        None, description="New appointment status value", example="confirmed"
    )


class AppointmentPatchResponse(BaseModel):
    appointment: AppointmentModel = Field(
        ..., description="Updated appointment", example={}
    )


class AppointmentRescheduleRequest(BaseModel):
    new_time_slot_id: int = Field(
        ..., description="time_slots.id representing the new desired slot", example=1050
    )


class AppointmentRescheduleResponse(BaseModel):
    appointment: AppointmentModel = Field(
        ..., description="Rescheduled appointment", example={}
    )


class AppointmentReminderSettingsResponse(BaseModel):
    reminder_settings: Optional[AppointmentReminderSettingsModel] = Field(
        None, description="Reminder settings for appointment", example={}
    )


class AppointmentReminderSettingsPutRequest(BaseModel):
    send_email: bool = Field(
        ..., description="Whether to send email reminders", example=True
    )
    send_sms: bool = Field(
        ..., description="Whether to send SMS reminders", example=False
    )


class AppointmentReminderSettingsPutResponse(BaseModel):
    reminder_settings: AppointmentReminderSettingsModel = Field(
        ..., description="Created or updated reminder settings", example={}
    )


class WaitlistEntryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Waitlist entry id", example=30)
    patient_id: int = Field(..., description="Current patient id", example=10)
    dependent_id: Optional[int] = Field(
        None, description="Dependent id or null", example=None
    )
    specialty_id: Optional[int] = Field(
        None, description="Target specialty id", example=4
    )
    provider_id: Optional[int] = Field(
        None, description="Preferred provider id if any", example=None
    )
    clinic_location_id: Optional[int] = Field(
        None,
        description="Specific clinic location id",
        example=3,
    )
    appointment_type_id: int = Field(
        ..., description="Appointment type id", example=10
    )
    visit_mode: str = Field(
        ..., description="Visit mode", example="in_person"
    )
    preferred_after_time: Optional[str] = Field(
        None,
        description="Earliest acceptable daily start time (HH:MM)",
        example="17:00",
    )
    preferred_before_time: Optional[str] = Field(
        None,
        description="Latest acceptable daily time (HH:MM) or null",
        example=None,
    )
    weekdays_only: bool = Field(
        ..., description="True if restricted to weekdays", example=True
    )
    min_notice_minutes: int = Field(
        ..., description="Minimum notice in minutes", example=120
    )
    auto_accept: bool = Field(
        ..., description="True if auto-accept is enabled", example=True
    )
    status: str = Field(
        ..., description="Current waitlist status", example="active"
    )
    created_at: Optional[str] = Field(
        None, description="Creation timestamp", example="2025-02-25T10:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp", example="2025-02-25T10:00:00Z"
    )


class WaitlistEntryCreateRequest(BaseModel):
    dependent_id: Optional[int] = Field(
        None,
        description="patient_dependents.id if waitlist is for a dependent",
        example=None,
    )
    specialty_id: Optional[int] = Field(
        None, description="Specialty to waitlist for", example=4
    )
    provider_id: Optional[int] = Field(
        None, description="Specific provider_id if requested", example=None
    )
    clinic_location_id: Optional[int] = Field(
        None,
        description="Specific clinic_locations.id to restrict",
        example=3,
    )
    appointment_type_id: int = Field(
        ..., description="Target appointment_types.id", example=10
    )
    visit_mode: str = Field(
        ..., description="Visit mode", example="in_person"
    )
    preferred_after_time: Optional[str] = Field(
        None,
        description="Daily time-of-day HH:MM after which slots are acceptable",
        example="17:00",
    )
    preferred_before_time: Optional[str] = Field(
        None,
        description="Daily time-of-day HH:MM before which slots are acceptable",
        example=None,
    )
    weekdays_only: Optional[bool] = Field(
        None, description="If true, limit to weekdays only", example=True
    )
    min_notice_minutes: int = Field(
        ..., description="Minimum lead time in minutes", example=120
    )
    auto_accept: bool = Field(
        ..., description="If true, automatically accept matching slots", example=True
    )
    status: Optional[str] = Field(
        None, description="Initial waitlist status", example="active"
    )


class WaitlistEntryCreateResponse(BaseModel):
    waitlist_entry: WaitlistEntryModel = Field(
        ..., description="Created waitlist entry", example={}
    )


class DiagnosisCodeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Diagnosis code id", example=50)
    code: str = Field(..., description="Diagnosis code string", example="I10")
    description: Optional[str] = Field(
        None,
        description="Description of diagnosis",
        example="Essential (primary) hypertension",
    )
    created_at: Optional[str] = Field(
        None, description="Creation time", example="2023-06-01T00:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update time", example="2023-06-01T00:00:00Z"
    )


class DiagnosisCodesResponse(BaseModel):
    diagnosis_codes: List[DiagnosisCodeModel] = Field(
        ..., description="List of diagnosis codes", example=[]
    )


class ReferralModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Referral id", example=15)
    patient_id: int = Field(..., description="Current patient id", example=10)
    department_id: Optional[int] = Field(
        None, description="Department id if set", example=5
    )
    specialty_id: Optional[int] = Field(
        None, description="Specialty id if set", example=2
    )
    referring_provider_name: str = Field(
        ..., description="Referring provider's name", example="Dr. Michael Green"
    )
    diagnosis_code_id: Optional[int] = Field(
        None, description="Linked diagnosis_codes.id", example=50
    )
    referral_expiration_date: str = Field(
        ..., description="Expiration date for referral", example="2025-05-31"
    )
    status: str = Field(
        ..., description="Referral status", example="active"
    )
    created_at: Optional[str] = Field(
        None, description="Creation time", example="2025-02-25T10:30:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update time", example="2025-02-25T10:30:00Z"
    )


class ReferralCreateRequest(BaseModel):
    department_id: Optional[int] = Field(
        None, description="departments.id for the referred department", example=5
    )
    specialty_id: Optional[int] = Field(
        None,
        description="specialties.id for the specialty if department_id not used",
        example=2,
    )
    referring_provider_name: str = Field(
        ..., description="Name of the provider who created the referral", example="Dr. Michael Green"
    )
    diagnosis_code: str = Field(
        ..., description="Diagnosis code string", example="I10"
    )
    referral_expiration_date: str = Field(
        ..., description="Referral expiration date in ISO date format", example="2025-05-31"
    )
    status: Optional[str] = Field(
        None, description="Initial referral status", example="active"
    )


class ReferralCreateResponse(BaseModel):
    referral: ReferralModel = Field(
        ..., description="Created referral", example={}
    )


class AppointmentReferralModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Appointment referral id", example=40)
    appointment_id: str = Field(
        ..., description="Linked appointment id", example="APT-50001"
    )
    referral_id: int = Field(
        ..., description="Linked referral id", example=15
    )
    created_at: Optional[str] = Field(
        None, description="Creation time", example="2025-02-25T11:00:00Z"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update time", example="2025-02-25T11:00:00Z"
    )


class AppointmentReferralCreateRequest(BaseModel):
    appointment_id: str = Field(
        ..., description="appointments.id to link", example="APT-50001"
    )
    referral_id: int = Field(
        ..., description="referrals.id to associate with this appointment", example=15
    )


class AppointmentReferralCreateResponse(BaseModel):
    appointment_referral: AppointmentReferralModel = Field(
        ..., description="Created appointment_referral", example={}
    )


class AppointmentCheckinModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Check-in record id", example=60)
    appointment_id: str = Field(
        ..., description="Linked appointment id", example="APT-41200"
    )
    check_in_time: str = Field(
        ..., description="Check-in time", example="2025-02-25T14:05:00Z"
    )
    exam_room: Optional[str] = Field(
        None, description="Assigned exam room", example="Room 5B"
    )
    created_at: Optional[str] = Field(
        None,
        description="Record creation time",
        example="2025-02-25T14:05:01Z",
    )


class AppointmentCheckinCreateRequest(BaseModel):
    appointment_id: str = Field(
        ..., description="appointments.id being checked in", example="APT-41200"
    )
    check_in_time: str = Field(
        ..., description="Check-in timestamp (ISO datetime)", example="2025-02-25T14:05:00Z"
    )
    exam_room: Optional[str] = Field(
        None, description="Assigned exam room label", example="Room 5B"
    )


class AppointmentCheckinCreateResponse(BaseModel):
    checkin: AppointmentCheckinModel = Field(
        ..., description="Created check-in record", example={}
    )


class AppointmentStatusHistoryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Status history record id", example=70)
    appointment_id: str = Field(
        ..., description="Linked appointment id", example="APT-41200"
    )
    old_status: Optional[str] = Field(
        None, description="Previous status before change", example="confirmed"
    )
    new_status: str = Field(
        ..., description="New status value after change", example="checked_in"
    )
    changed_at: Optional[str] = Field(
        None,
        description="When status change was recorded",
        example="2025-02-25T14:05:01Z",
    )
    changed_by_user_id: Optional[int] = Field(
        None, description="User id that made the change", example=1
    )
    note: Optional[str] = Field(
        None, description="Optional note for context", example="Patient arrived at front desk"
    )


class AppointmentStatusChangeRequest(BaseModel):
    new_status: str = Field(
        ..., description="New status value for the appointment", example="checked_in"
    )
    note: Optional[str] = Field(
        None,
        description="Optional note describing reason for status change",
        example="Patient arrived at front desk",
    )


class AppointmentStatusChangeAppointmentModel(BaseModel):
    id: str = Field(..., description="Appointment id", example="APT-41200")
    status: str = Field(
        ..., description="Updated status value", example="checked_in"
    )
    updated_at: Optional[str] = Field(
        None,
        description="Timestamp of this status change",
        example="2025-02-25T14:05:01Z",
    )


class AppointmentStatusChangeResponse(BaseModel):
    appointment: AppointmentStatusChangeAppointmentModel = Field(
        ..., description="Appointment status info", example={}
    )
    status_history: AppointmentStatusHistoryModel = Field(
        ..., description="Status history entry", example={}
    )


class SatisfactionSurveyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Survey id", example=80)
    appointment_id: str = Field(
        ..., description="Linked appointment id", example="APT-20451"
    )
    patient_id: int = Field(..., description="Patient id for this survey", example=10)
    rating: int = Field(
        ..., description="Numeric rating given by patient", example=5
    )
    wait_time_minutes: Optional[int] = Field(
        None, description="Recorded wait time in minutes", example=10
    )
    comments: Optional[str] = Field(
        None, description="Optional free-text comments", example="Very satisfied with the visit"
    )
    created_at: Optional[str] = Field(
        None,
        description="Survey creation timestamp",
        example="2025-02-20T16:00:00Z",
    )
    updated_at: Optional[str] = Field(
        None,
        description="Last update timestamp",
        example="2025-02-20T16:00:00Z",
    )


class SatisfactionSurveysResponse(BaseModel):
    satisfaction_surveys: List[SatisfactionSurveyModel] = Field(
        ..., description="List of satisfaction surveys", example=[]
    )


class SatisfactionSurveyCreateRequest(BaseModel):
    appointment_id: str = Field(
        ..., description="appointments.id that this survey is for", example="APT-20451"
    )
    rating: int = Field(
        ..., description="Numeric rating value (e.g., 1-5)", example=5
    )
    wait_time_minutes: Optional[int] = Field(
        None,
        description="Patient-reported wait time in minutes",
        example=10,
    )
    comments: Optional[str] = Field(
        None,
        description="Additional comments about the visit",
        example="Quick check-in and thorough explanation.",
    )


class SatisfactionSurveyCreateResponse(BaseModel):
    satisfaction_survey: SatisfactionSurveyModel = Field(
        ..., description="Created satisfaction survey", example={}
    )


def get_current_patient(session):
    user = session.query(User).filter(User.id == 1).first()
    if user is None:
        user = User(
            id=1,
            username="demo",
            email="demo@example.com",
            full_name="Demo User",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(user)
        session.commit()
    patient = session.query(Patient).filter(Patient.user_id == 1).first()
    if patient is None:
        patient = Patient(
            user_id=1,
            full_name="Demo Patient",
            date_of_birth=None,
            sex=None,
            primary_phone=None,
            home_address_line1=None,
            home_address_line2=None,
            home_city=None,
            home_state=None,
            home_postal_code=None,
            home_country=None,
            is_active=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(patient)
        session.commit()
    return patient


def bool_from_int(value):
    return value is not None and value != 0


def int_from_bool(value: bool) -> int:
    return 1 if value else 0


@app.get(
    "/api/patients/me",
    response_model=PatientResponse,
    summary="Get current user's patient profile",
    description="Retrieve the patient record associated with the authenticated user.",
    tags=["patients"],
    operation_id="get_current_patient_profile",
)
async def get_current_patient_profile() -> PatientResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    model = PatientModel(
        id=patient.id,
        user_id=patient.user_id,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        sex=patient.sex,
        primary_phone=patient.primary_phone,
        home_address_line1=patient.home_address_line1,
        home_address_line2=patient.home_address_line2,
        home_city=patient.home_city,
        home_state=patient.home_state,
        home_postal_code=patient.home_postal_code,
        home_country=patient.home_country,
        is_active=bool_from_int(patient.is_active),
        created_at=patient.created_at.isoformat() if patient.created_at else None,
        updated_at=patient.updated_at.isoformat() if patient.updated_at else None,
    )
    session.close()
    return PatientResponse(patient=model)


@app.put(
    "/api/patients/me",
    response_model=PatientResponse,
    summary="Update current patient's demographic info",
    description="Update fields like address, phone and demographics for the current patient.",
    tags=["patients"],
    operation_id="update_current_patient_profile",
)
async def update_current_patient_profile(body: PatientUpdateRequest = Body(...)) -> PatientResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    if body.full_name is not None:
        patient.full_name = body.full_name
    if body.date_of_birth is not None:
        try:
            patient.date_of_birth = datetime.fromisoformat(body.date_of_birth).date()
        except Exception:
            patient.date_of_birth = None
    if body.sex is not None:
        patient.sex = body.sex
    if body.primary_phone is not None:
        patient.primary_phone = body.primary_phone
    if body.home_address_line1 is not None:
        patient.home_address_line1 = body.home_address_line1
    if body.home_address_line2 is not None:
        patient.home_address_line2 = body.home_address_line2
    if body.home_city is not None:
        patient.home_city = body.home_city
    if body.home_state is not None:
        patient.home_state = body.home_state
    if body.home_postal_code is not None:
        patient.home_postal_code = body.home_postal_code
    if body.home_country is not None:
        patient.home_country = body.home_country
    patient.updated_at = datetime.utcnow()
    session.commit()
    model = PatientModel(
        id=patient.id,
        user_id=patient.user_id,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        sex=patient.sex,
        primary_phone=patient.primary_phone,
        home_address_line1=patient.home_address_line1,
        home_address_line2=patient.home_address_line2,
        home_city=patient.home_city,
        home_state=patient.home_state,
        home_postal_code=patient.home_postal_code,
        home_country=patient.home_country,
        is_active=bool_from_int(patient.is_active),
        created_at=patient.created_at.isoformat() if patient.created_at else None,
        updated_at=patient.updated_at.isoformat() if patient.updated_at else None,
    )
    session.close()
    return PatientResponse(patient=model)


@app.get(
    "/api/patient_dependents",
    response_model=DependentsResponse,
    summary="List dependents for current patient",
    description="Retrieve all active dependents linked to the current patient's profile.",
    tags=["dependents"],
    operation_id="list_patient_dependents",
)
async def list_patient_dependents() -> DependentsResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    rows = (
        session.query(PatientDependent)
        .filter(
            PatientDependent.patient_id == patient.id,
            PatientDependent.is_active == 1,
        )
        .all()
    )
    dependents_list = []
    for d in rows:
        dependents_list.append(
            DependentModel(
                id=d.id,
                patient_id=d.patient_id,
                dependent_name=d.dependent_name,
                date_of_birth=d.date_of_birth.isoformat() if d.date_of_birth else None,
                relationship=d.relationship,
                is_active=bool_from_int(d.is_active),
                created_at=d.created_at.isoformat() if d.created_at else None,
                updated_at=d.updated_at.isoformat() if d.updated_at else None,
            )
        )
    session.close()
    return DependentsResponse(dependents=dependents_list)


@app.get(
    "/api/patient_contacts",
    response_model=PatientContactsResponse,
    summary="List contact channels for current patient",
    description="Retrieve all contact records for the current patient's profile.",
    tags=["patient_contacts"],
    operation_id="list_patient_contacts",
)
async def list_patient_contacts(
    include_inactive: Optional[bool] = Query(
        None,
        description="If true, include non-primary contacts as well",
        example=False,
    )
) -> PatientContactsResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    query = session.query(PatientContact).filter(PatientContact.patient_id == patient.id)
    if not include_inactive:
        query = query.filter(PatientContact.is_primary == 1)
    rows = query.all()
    contacts = []
    for c in rows:
        contacts.append(
            PatientContactModel(
                id=c.id,
                patient_id=c.patient_id,
                contact_type=c.contact_type,
                value=c.value,
                is_primary=bool_from_int(c.is_primary),
                created_at=c.created_at.isoformat() if c.created_at else None,
                updated_at=c.updated_at.isoformat() if c.updated_at else None,
            )
        )
    session.close()
    return PatientContactsResponse(contacts=contacts)


@app.post(
    "/api/patient_contacts",
    response_model=PatientContactCreateResponse,
    summary="Create a new contact for current patient",
    description="Add a new contact record for the authenticated patient's profile.",
    tags=["patient_contacts"],
    operation_id="create_patient_contact",
)
async def create_patient_contact(
    body: PatientContactCreateRequest = Body(...)
) -> PatientContactCreateResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    is_primary_val = 0
    if body.is_primary:
        other_contacts = (
            session.query(PatientContact)
            .filter(
                PatientContact.patient_id == patient.id,
                PatientContact.contact_type == body.contact_type,
                PatientContact.is_primary == 1,
            )
            .all()
        )
        for oc in other_contacts:
            oc.is_primary = 0
            oc.updated_at = datetime.utcnow()
        is_primary_val = 1
    new_c = PatientContact(
        patient_id=patient.id,
        contact_type=body.contact_type,
        value=body.value,
        is_primary=is_primary_val,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(new_c)
    session.commit()
    model = PatientContactModel(
        id=new_c.id,
        patient_id=new_c.patient_id,
        contact_type=new_c.contact_type,
        value=new_c.value,
        is_primary=bool_from_int(new_c.is_primary),
        created_at=new_c.created_at.isoformat() if new_c.created_at else None,
        updated_at=new_c.updated_at.isoformat() if new_c.updated_at else None,
    )
    session.close()
    return PatientContactCreateResponse(contact=model)


@app.get(
    "/api/insurance_providers",
    response_model=InsuranceProvidersResponse,
    summary="Search insurance providers by name",
    description="Lookup insurance_providers records by optional name filter.",
    tags=["insurance"],
    operation_id="search_insurance_providers",
)
async def search_insurance_providers(
    name_contains: Optional[str] = Query(
        None,
        description="Case-insensitive substring match on provider name",
        example="HealthPlus",
    ),
    limit: Optional[int] = Query(
        None, description="Maximum number of providers to return", example=20
    ),
) -> InsuranceProvidersResponse:
    session = SessionLocal()
    query = session.query(InsuranceProvider)
    if name_contains:
        query = query.filter(InsuranceProvider.name.ilike(f"%{name_contains}%"))
    if limit:
        query = query.limit(limit)
    rows = query.all()
    providers_list = []
    for p in rows:
        providers_list.append(
            InsuranceProviderModel(
                id=p.id,
                name=p.name,
                created_at=p.created_at.isoformat() if p.created_at else None,
                updated_at=p.updated_at.isoformat() if p.updated_at else None,
            )
        )
    session.close()
    return InsuranceProvidersResponse(insurance_providers=providers_list)


@app.get(
    "/api/patient_insurances",
    response_model=PatientInsurancesResponse,
    summary="List all insurances for current patient",
    description="Retrieve all patient_insurances linked to the current patient.",
    tags=["insurance"],
    operation_id="list_patient_insurances",
)
async def list_patient_insurances() -> PatientInsurancesResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    rows = session.query(PatientInsurance).filter(PatientInsurance.patient_id == patient.id).all()
    ins_list = []
    for r in rows:
        ins_list.append(
            PatientInsuranceModel(
                id=r.id,
                patient_id=r.patient_id,
                insurance_provider_id=r.insurance_provider_id,
                member_id=r.member_id,
                is_default=bool_from_int(r.is_default),
                effective_date=r.effective_date.isoformat() if r.effective_date else None,
                expiration_date=r.expiration_date.isoformat() if r.expiration_date else None,
                created_at=r.created_at.isoformat() if r.created_at else None,
                updated_at=r.updated_at.isoformat() if r.updated_at else None,
            )
        )
    session.close()
    return PatientInsurancesResponse(patient_insurances=ins_list)


@app.post(
    "/api/patient_insurances",
    response_model=PatientInsuranceCreateResponse,
    summary="Create a new insurance for current patient",
    description="Create a patient_insurances record and optionally mark it as default.",
    tags=["insurance"],
    operation_id="create_patient_insurance",
)
async def create_patient_insurance(
    body: PatientInsuranceCreateRequest = Body(...)
) -> PatientInsuranceCreateResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    provider = (
        session.query(InsuranceProvider)
        .filter(InsuranceProvider.name == body.insurance_provider_name)
        .first()
    )
    if provider is None:
        provider = InsuranceProvider(
            name=body.insurance_provider_name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(provider)
        session.commit()
    is_default_val = 0
    if body.set_as_default:
        existing = (
            session.query(PatientInsurance)
            .filter(
                PatientInsurance.patient_id == patient.id,
                PatientInsurance.is_default == 1,
            )
            .all()
        )
        for e in existing:
            e.is_default = 0
            e.updated_at = datetime.utcnow()
        is_default_val = 1
    eff_date = None
    exp_date = None
    if body.effective_date:
        try:
            eff_date = datetime.fromisoformat(body.effective_date).date()
        except Exception:
            eff_date = None
    if body.expiration_date:
        try:
            exp_date = datetime.fromisoformat(body.expiration_date).date()
        except Exception:
            exp_date = None
    new_ins = PatientInsurance(
        patient_id=patient.id,
        insurance_provider_id=provider.id,
        member_id=body.member_id,
        is_default=is_default_val,
        effective_date=eff_date,
        expiration_date=exp_date,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(new_ins)
    session.commit()
    model = PatientInsuranceModel(
        id=new_ins.id,
        patient_id=new_ins.patient_id,
        insurance_provider_id=new_ins.insurance_provider_id,
        member_id=new_ins.member_id,
        is_default=bool_from_int(new_ins.is_default),
        effective_date=new_ins.effective_date.isoformat() if new_ins.effective_date else None,
        expiration_date=new_ins.expiration_date.isoformat() if new_ins.expiration_date else None,
        created_at=new_ins.created_at.isoformat() if new_ins.created_at else None,
        updated_at=new_ins.updated_at.isoformat() if new_ins.updated_at else None,
    )
    session.close()
    return PatientInsuranceCreateResponse(patient_insurance=model)


@app.post(
    "/api/patient_insurances/{insurance_id}/set_default",
    response_model=PatientInsuranceSetDefaultResponse,
    summary="Set a patient insurance as default",
    description="Mark a specific patient_insurances record as default for current patient.",
    tags=["insurance"],
    operation_id="set_default_patient_insurance",
)
async def set_default_patient_insurance(
    insurance_id: int = Path(
        ...,
        description="patient_insurances.id to set as default for current patient",
        example=8,
    )
) -> PatientInsuranceSetDefaultResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    target = (
        session.query(PatientInsurance)
        .filter(
            PatientInsurance.id == insurance_id,
            PatientInsurance.patient_id == patient.id,
        )
        .first()
    )
    if target is not None:
        existing = (
            session.query(PatientInsurance)
            .filter(
                PatientInsurance.patient_id == patient.id,
                PatientInsurance.is_default == 1,
            )
            .all()
        )
        for e in existing:
            e.is_default = 0
            e.updated_at = datetime.utcnow()
        target.is_default = 1
        target.updated_at = datetime.utcnow()
        session.commit()
        model = PatientInsuranceModel(
            id=target.id,
            patient_id=target.patient_id,
            insurance_provider_id=target.insurance_provider_id,
            member_id=target.member_id,
            is_default=bool_from_int(target.is_default),
            effective_date=target.effective_date.isoformat() if target.effective_date else None,
            expiration_date=target.expiration_date.isoformat() if target.expiration_date else None,
            created_at=target.created_at.isoformat() if target.created_at else None,
            updated_at=target.updated_at.isoformat() if target.updated_at else None,
        )
    else:
        model = PatientInsuranceModel(
            id=0,
            patient_id=patient.id,
            insurance_provider_id=0,
            member_id="",
            is_default=False,
            effective_date=None,
            expiration_date=None,
            created_at=None,
            updated_at=None,
        )
    session.close()
    return PatientInsuranceSetDefaultResponse(patient_insurance=model)


@app.get(
    "/api/specialties",
    response_model=SpecialtiesResponse,
    summary="List specialties with optional name filter",
    description="Retrieve specialties by optional name filter.",
    tags=["reference"],
    operation_id="list_specialties",
)
async def list_specialties(
    name: Optional[str] = Query(
        None,
        description="Exact or partial specialty name to match",
        example="Cardiology",
    )
) -> SpecialtiesResponse:
    session = SessionLocal()
    query = session.query(Specialty)
    if name:
        query = query.filter(Specialty.name.ilike(f"%{name}%"))
    rows = query.all()
    specs = []
    for s in rows:
        specs.append(
            SpecialtyModel(
                id=s.id,
                name=s.name,
                created_at=s.created_at.isoformat() if s.created_at else None,
                updated_at=s.updated_at.isoformat() if s.updated_at else None,
            )
        )
    session.close()
    return SpecialtiesResponse(specialties=specs)


@app.get(
    "/api/departments",
    response_model=DepartmentsResponse,
    summary="List departments with optional filters",
    description="Retrieve departments filtered by name or specialty.",
    tags=["reference"],
    operation_id="list_departments",
)
async def list_departments(
    name: Optional[str] = Query(
        None,
        description="Exact or partial department name",
        example="Cardiology",
    ),
    specialty_id: Optional[int] = Query(
        None,
        description="Filter by specialties.id",
        example=2,
    ),
) -> DepartmentsResponse:
    session = SessionLocal()
    query = session.query(Department)
    if name:
        query = query.filter(Department.name.ilike(f"%{name}%"))
    if specialty_id:
        query = query.filter(Department.specialty_id == specialty_id)
    rows = query.all()
    depts = []
    for d in rows:
        depts.append(
            DepartmentModel(
                id=d.id,
                name=d.name,
                specialty_id=d.specialty_id,
                created_at=d.created_at.isoformat() if d.created_at else None,
                updated_at=d.updated_at.isoformat() if d.updated_at else None,
            )
        )
    session.close()
    return DepartmentsResponse(departments=depts)


@app.get(
    "/api/clinic_locations",
    response_model=ClinicLocationsResponse,
    summary="List clinic locations with optional name filter",
    description="Retrieve clinic_locations, optionally filtering by name or city.",
    tags=["reference"],
    operation_id="list_clinic_locations",
)
async def list_clinic_locations(
    name: Optional[str] = Query(
        None,
        description="Exact or partial clinic name to search",
        example="Downtown",
    ),
    city: Optional[str] = Query(
        None,
        description="Filter clinics by city",
        example="Metropolis",
    ),
) -> ClinicLocationsResponse:
    session = SessionLocal()
    query = session.query(ClinicLocation)
    if name:
        query = query.filter(ClinicLocation.name.ilike(f"%{name}%"))
    if city:
        query = query.filter(ClinicLocation.city.ilike(f"%{city}%"))
    rows = query.all()
    clinics = []
    for c in rows:
        clinics.append(
            ClinicLocationModel(
                id=c.id,
                name=c.name,
                code=c.code,
                address_line1=c.address_line1,
                address_line2=c.address_line2,
                city=c.city,
                state=c.state,
                postal_code=c.postal_code,
                country=c.country,
                created_at=c.created_at.isoformat() if c.created_at else None,
                updated_at=c.updated_at.isoformat() if c.updated_at else None,
            )
        )
    session.close()
    return ClinicLocationsResponse(clinic_locations=clinics)


@app.get(
    "/api/providers",
    response_model=ProvidersResponse,
    summary="Search providers by name or specialty",
    description="Retrieve providers, optionally filtered by full_name and specialty.",
    tags=["reference"],
    operation_id="search_providers",
)
async def search_providers(
    full_name: Optional[str] = Query(
        None,
        description="Exact or partial provider full_name to match",
        example="Dr. Anita Rao",
    ),
    specialty_id: Optional[int] = Query(
        None,
        description="Filter providers by specialties.id via provider_specialties",
        example=2,
    ),
) -> ProvidersResponse:
    session = SessionLocal()
    query = session.query(Provider)
    if full_name:
        query = query.filter(Provider.full_name.ilike(f"%{full_name}%"))
    if specialty_id:
        ps = (
            session.query(ProviderSpecialty)
            .filter(ProviderSpecialty.specialty_id == specialty_id)
            .all()
        )
        provider_ids = [p.provider_id for p in ps]
        if provider_ids:
            query = query.filter(Provider.id.in_(provider_ids))
        else:
            query = query.filter(Provider.id == -1)
    rows = query.all()
    providers_list = []
    for p in rows:
        providers_list.append(
            ProviderModel(
                id=p.id,
                full_name=p.full_name,
                npi_number=p.npi_number,
                created_at=p.created_at.isoformat() if p.created_at else None,
                updated_at=p.updated_at.isoformat() if p.updated_at else None,
            )
        )
    session.close()
    return ProvidersResponse(providers=providers_list)


@app.get(
    "/api/appointment_types",
    response_model=AppointmentTypesResponse,
    summary="List appointment types with filters",
    description="Retrieve appointment_types filtered by name or visit_mode.",
    tags=["reference"],
    operation_id="list_appointment_types",
)
async def list_appointment_types(
    name: Optional[str] = Query(
        None,
        description="Exact or partial appointment type name",
        example="Standard consultation",
    ),
    visit_mode: Optional[str] = Query(
        None,
        description="Visit mode type, such as in_person or telehealth",
        example="in_person",
    ),
) -> AppointmentTypesResponse:
    session = SessionLocal()
    query = session.query(AppointmentType)
    if name:
        query = query.filter(AppointmentType.name.ilike(f"%{name}%"))
    if visit_mode:
        query = query.filter(AppointmentType.visit_mode == visit_mode)
    rows = query.all()
    types_list = []
    for t in rows:
        types_list.append(
            AppointmentTypeModel(
                id=t.id,
                name=t.name,
                default_duration_minutes=t.default_duration_minutes,
                visit_mode=t.visit_mode,
                created_at=t.created_at.isoformat() if t.created_at else None,
                updated_at=t.updated_at.isoformat() if t.updated_at else None,
            )
        )
    session.close()
    return AppointmentTypesResponse(appointment_types=types_list)


@app.get(
    "/api/time_slots",
    response_model=TimeSlotsResponse,
    summary="Search available time slots",
    description="Search time_slots by filters and date range, returning slots.",
    tags=["time_slots"],
    operation_id="search_time_slots",
)
async def search_time_slots(
    provider_id: Optional[int] = Query(
        None, description="Filter slots by specific provider_id", example=11
    ),
    specialty_id: Optional[int] = Query(
        None,
        description="Filter by specialties.id",
        example=2,
    ),
    clinic_location_id: Optional[int] = Query(
        None,
        description="Filter by clinic_locations.id",
        example=3,
    ),
    appointment_type_id: Optional[int] = Query(
        None,
        description="Filter by appointment_types.id",
        example=1,
    ),
    visit_mode: Optional[str] = Query(
        None,
        description="Visit mode string such as in_person or telehealth",
        example="telehealth",
    ),
    start_datetime_from: str = Query(
        ...,
        description="Earliest slot start time (ISO datetime)",
        example="2025-03-01T00:00:00Z",
    ),
    start_datetime_to: str = Query(
        ...,
        description="Latest slot start time (ISO datetime)",
        example="2025-03-08T23:59:59Z",
    ),
    only_with_capacity: Optional[bool] = Query(
        None,
        description="If true, only return slots where capacity_booked < capacity_total",
        example=True,
    ),
    limit: Optional[int] = Query(
        None,
        description="Maximum number of slots to return ordered by start_datetime",
        example=50,
    ),
) -> TimeSlotsResponse:
    session = SessionLocal()
    try:
        dt_from = datetime.fromisoformat(start_datetime_from.replace("Z", "+00:00"))
    except Exception:
        dt_from = datetime.min
    try:
        dt_to = datetime.fromisoformat(start_datetime_to.replace("Z", "+00:00"))
    except Exception:
        dt_to = datetime.max
    query = session.query(TimeSlot).filter(
        TimeSlot.start_datetime >= dt_from,
        TimeSlot.start_datetime <= dt_to,
    )
    if provider_id:
        query = query.filter(TimeSlot.provider_id == provider_id)
    if specialty_id:
        query = query.filter(TimeSlot.specialty_id == specialty_id)
    if clinic_location_id:
        query = query.filter(TimeSlot.clinic_location_id == clinic_location_id)
    if appointment_type_id:
        query = query.filter(TimeSlot.appointment_type_id == appointment_type_id)
    if visit_mode:
        query = query.filter(TimeSlot.visit_mode == visit_mode)
    if only_with_capacity:
        query = query.filter(TimeSlot.capacity_booked < TimeSlot.capacity_total)
    query = query.order_by(TimeSlot.start_datetime.asc())
    if limit:
        query = query.limit(limit)
    rows = query.all()
    slots = []
    for s in rows:
        slots.append(
            TimeSlotModel(
                id=s.id,
                provider_id=s.provider_id,
                clinic_location_id=s.clinic_location_id,
                appointment_type_id=s.appointment_type_id,
                specialty_id=s.specialty_id,
                visit_mode=s.visit_mode,
                start_datetime=s.start_datetime.isoformat() if s.start_datetime else "",
                end_datetime=s.end_datetime.isoformat() if s.end_datetime else "",
                capacity_total=s.capacity_total,
                capacity_booked=s.capacity_booked,
                is_active=bool_from_int(s.is_active),
                created_at=s.created_at.isoformat() if s.created_at else None,
                updated_at=s.updated_at.isoformat() if s.updated_at else None,
            )
        )
    session.close()
    return TimeSlotsResponse(time_slots=slots)


@app.get(
    "/api/appointments",
    response_model=AppointmentsResponse,
    summary="List current patient's appointments",
    description="Retrieve appointments for the authenticated patient with filters.",
    tags=["appointments"],
    operation_id="list_patient_appointments",
)
async def list_patient_appointments(
    status: Optional[str] = Query(
        None,
        description="Filter appointments by status",
        example="completed",
    ),
    start_datetime_from: Optional[str] = Query(
        None,
        description="Start of appointment date range (ISO datetime)",
        example="2024-09-01T00:00:00Z",
    ),
    start_datetime_to: Optional[str] = Query(
        None,
        description="End of appointment date range (ISO datetime)",
        example="2025-03-01T00:00:00Z",
    ),
    is_imaging: Optional[bool] = Query(
        None,
        description="If set, filter on imaging flag",
        example=False,
    ),
    limit: Optional[int] = Query(
        None,
        description="Maximum number of appointments ordered by start_datetime",
        example=100,
    ),
) -> AppointmentsResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    query = session.query(Appointment).filter(Appointment.patient_id == patient.id)
    if status:
        query = query.filter(Appointment.status == status)
    if start_datetime_from:
        try:
            dt_from = datetime.fromisoformat(start_datetime_from.replace("Z", "+00:00"))
            query = query.filter(Appointment.start_datetime >= dt_from)
        except Exception:
            pass
    if start_datetime_to:
        try:
            dt_to = datetime.fromisoformat(start_datetime_to.replace("Z", "+00:00"))
            query = query.filter(Appointment.start_datetime <= dt_to)
        except Exception:
            pass
    if is_imaging is not None:
        query = query.filter(Appointment.is_imaging == int_from_bool(is_imaging))
    query = query.order_by(Appointment.start_datetime.asc())
    if limit:
        query = query.limit(limit)
    rows = query.all()
    appts = []
    for a in rows:
        appts.append(
            AppointmentModel(
                id=a.id,
                patient_id=a.patient_id,
                dependent_id=a.dependent_id,
                provider_id=a.provider_id,
                clinic_location_id=a.clinic_location_id,
                appointment_type_id=a.appointment_type_id,
                specialty_id=a.specialty_id,
                time_slot_id=a.time_slot_id,
                start_datetime=a.start_datetime.isoformat() if a.start_datetime else "",
                end_datetime=a.end_datetime.isoformat() if a.end_datetime else "",
                visit_mode=a.visit_mode,
                status=a.status,
                reason_for_visit=a.reason_for_visit,
                insurance_id=a.insurance_id,
                referral_id=a.referral_id,
                is_imaging=bool_from_int(a.is_imaging),
                created_at=a.created_at.isoformat() if a.created_at else None,
                updated_at=a.updated_at.isoformat() if a.updated_at else None,
            )
        )
    session.close()
    return AppointmentsResponse(appointments=appts)


@app.post(
    "/api/appointments",
    response_model=AppointmentCreateResponse,
    summary="Create a new appointment for current patient",
    description="Create an appointment using a time_slot and optional extras.",
    tags=["appointments"],
    operation_id="create_appointment",
)
async def create_appointment(
    body: AppointmentCreateRequest = Body(...)
) -> AppointmentCreateResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    slot = session.query(TimeSlot).filter(TimeSlot.id == body.time_slot_id).first()
    if slot is None:
        session.close()
        empty_appointment = AppointmentModel(
            id="",
            patient_id=patient.id,
            dependent_id=None,
            provider_id=None,
            clinic_location_id=0,
            appointment_type_id=0,
            specialty_id=None,
            time_slot_id=None,
            start_datetime="",
            end_datetime="",
            visit_mode="",
            status="",
            reason_for_visit=None,
            insurance_id=None,
            referral_id=None,
            is_imaging=False,
            created_at=None,
            updated_at=None,
        )
        return AppointmentCreateResponse(appointment=empty_appointment, reminder_settings=None)
    prefix = "APT-"
    existing_ids = (
        session.query(Appointment.id)
        .filter(Appointment.id.like(f"{prefix}%"))
        .all()
    )
    max_num = 0
    for (aid,) in existing_ids:
        try:
            if aid.startswith(prefix):
                num = int(aid[len(prefix) :])
                if num > max_num:
                    max_num = num
        except Exception:
            pass
    new_id = f"{prefix}{max_num + 1}"
    status_val = body.status if body.status else "booked"
    insurance_id_val = body.insurance_id
    if insurance_id_val is None:
        default_ins = (
            session.query(PatientInsurance)
            .filter(
                PatientInsurance.patient_id == patient.id,
                PatientInsurance.is_default == 1,
            )
            .first()
        )
        if default_ins:
            insurance_id_val = default_ins.id
    new_appt = Appointment(
        id=new_id,
        patient_id=patient.id,
        dependent_id=body.dependent_id,
        provider_id=slot.provider_id,
        clinic_location_id=slot.clinic_location_id,
        appointment_type_id=slot.appointment_type_id,
        specialty_id=slot.specialty_id,
        time_slot_id=slot.id,
        start_datetime=slot.start_datetime,
        end_datetime=slot.end_datetime,
        visit_mode=slot.visit_mode,
        status=status_val,
        reason_for_visit=body.reason_for_visit,
        insurance_id=insurance_id_val,
        referral_id=body.referral_id,
        is_imaging=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(new_appt)
    slot.capacity_booked = slot.capacity_booked + 1
    session.commit()
    reminder = None
    if body.send_email or body.send_sms:
        send_email_val = int_from_bool(bool(body.send_email))
        send_sms_val = int_from_bool(bool(body.send_sms))
        rem = AppointmentReminderSetting(
            appointment_id=new_appt.id,
            send_email=send_email_val,
            send_sms=send_sms_val,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(rem)
        session.commit()
        reminder = AppointmentReminderSettingsModel(
            id=rem.id,
            appointment_id=rem.appointment_id,
            send_email=bool_from_int(rem.send_email),
            send_sms=bool_from_int(rem.send_sms),
            created_at=rem.created_at.isoformat() if rem.created_at else None,
            updated_at=rem.updated_at.isoformat() if rem.updated_at else None,
        )
    appt_model = AppointmentModel(
        id=new_appt.id,
        patient_id=new_appt.patient_id,
        dependent_id=new_appt.dependent_id,
        provider_id=new_appt.provider_id,
        clinic_location_id=new_appt.clinic_location_id,
        appointment_type_id=new_appt.appointment_type_id,
        specialty_id=new_appt.specialty_id,
        time_slot_id=new_appt.time_slot_id,
        start_datetime=new_appt.start_datetime.isoformat() if new_appt.start_datetime else "",
        end_datetime=new_appt.end_datetime.isoformat() if new_appt.end_datetime else "",
        visit_mode=new_appt.visit_mode,
        status=new_appt.status,
        reason_for_visit=new_appt.reason_for_visit,
        insurance_id=new_appt.insurance_id,
        referral_id=new_appt.referral_id,
        is_imaging=bool_from_int(new_appt.is_imaging),
        created_at=new_appt.created_at.isoformat() if new_appt.created_at else None,
        updated_at=new_appt.updated_at.isoformat() if new_appt.updated_at else None,
    )
    session.close()
    return AppointmentCreateResponse(appointment=appt_model, reminder_settings=reminder)


@app.get(
    "/api/appointments/{appointment_id}",
    response_model=AppointmentByIdResponse,
    summary="Get details for a specific appointment",
    description="Retrieve a single appointment by id belonging to the current patient.",
    tags=["appointments"],
    operation_id="get_appointment_by_id",
)
async def get_appointment_by_id(
    appointment_id: str = Path(
        ...,
        description="appointments.id to retrieve",
        example="APT-20451",
    )
) -> AppointmentByIdResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    a = (
        session.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient.id,
        )
        .first()
    )
    if a is None:
        empty = AppointmentModel(
            id="",
            patient_id=patient.id,
            dependent_id=None,
            provider_id=None,
            clinic_location_id=0,
            appointment_type_id=0,
            specialty_id=None,
            time_slot_id=None,
            start_datetime="",
            end_datetime="",
            visit_mode="",
            status="",
            reason_for_visit=None,
            insurance_id=None,
            referral_id=None,
            is_imaging=False,
            created_at=None,
            updated_at=None,
        )
        session.close()
        return AppointmentByIdResponse(appointment=empty)
    model = AppointmentModel(
        id=a.id,
        patient_id=a.patient_id,
        dependent_id=a.dependent_id,
        provider_id=a.provider_id,
        clinic_location_id=a.clinic_location_id,
        appointment_type_id=a.appointment_type_id,
        specialty_id=a.specialty_id,
        time_slot_id=a.time_slot_id,
        start_datetime=a.start_datetime.isoformat() if a.start_datetime else "",
        end_datetime=a.end_datetime.isoformat() if a.end_datetime else "",
        visit_mode=a.visit_mode,
        status=a.status,
        reason_for_visit=a.reason_for_visit,
        insurance_id=a.insurance_id,
        referral_id=a.referral_id,
        is_imaging=bool_from_int(a.is_imaging),
        created_at=a.created_at.isoformat() if a.created_at else None,
        updated_at=a.updated_at.isoformat() if a.updated_at else None,
    )
    session.close()
    return AppointmentByIdResponse(appointment=model)


@app.patch(
    "/api/appointments/{appointment_id}",
    response_model=AppointmentPatchResponse,
    summary="Update basic fields on an appointment",
    description="Partially update fields like reason_for_visit, insurance_id, or status.",
    tags=["appointments"],
    operation_id="patch_appointment",
)
async def patch_appointment(
    appointment_id: str = Path(
        ...,
        description="appointments.id to update",
        example="APT-30987",
    ),
    body: AppointmentPatchRequest = Body(...),
) -> AppointmentPatchResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    a = (
        session.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient.id,
        )
        .first()
    )
    if a is not None:
        old_status = a.status
        if body.reason_for_visit is not None:
            a.reason_for_visit = body.reason_for_visit
        if body.insurance_id is not None:
            a.insurance_id = body.insurance_id
        if body.status is not None:
            a.status = body.status
        a.updated_at = datetime.utcnow()
        if body.status is not None and body.status != old_status:
            hist = AppointmentStatusHistory(
                appointment_id=a.id,
                old_status=old_status,
                new_status=a.status,
                changed_at=datetime.utcnow(),
                changed_by_user_id=1,
                note=None,
            )
            session.add(hist)
        session.commit()
        model = AppointmentModel(
            id=a.id,
            patient_id=a.patient_id,
            dependent_id=a.dependent_id,
            provider_id=a.provider_id,
            clinic_location_id=a.clinic_location_id,
            appointment_type_id=a.appointment_type_id,
            specialty_id=a.specialty_id,
            time_slot_id=a.time_slot_id,
            start_datetime=a.start_datetime.isoformat() if a.start_datetime else "",
            end_datetime=a.end_datetime.isoformat() if a.end_datetime else "",
            visit_mode=a.visit_mode,
            status=a.status,
            reason_for_visit=a.reason_for_visit,
            insurance_id=a.insurance_id,
            referral_id=a.referral_id,
            is_imaging=bool_from_int(a.is_imaging),
            created_at=a.created_at.isoformat() if a.created_at else None,
            updated_at=a.updated_at.isoformat() if a.updated_at else None,
        )
    else:
        model = AppointmentModel(
            id="",
            patient_id=patient.id,
            dependent_id=None,
            provider_id=None,
            clinic_location_id=0,
            appointment_type_id=0,
            specialty_id=None,
            time_slot_id=None,
            start_datetime="",
            end_datetime="",
            visit_mode="",
            status="",
            reason_for_visit=None,
            insurance_id=None,
            referral_id=None,
            is_imaging=False,
            created_at=None,
            updated_at=None,
        )
    session.close()
    return AppointmentPatchResponse(appointment=model)


@app.post(
    "/api/appointments/{appointment_id}/reschedule",
    response_model=AppointmentRescheduleResponse,
    summary="Reschedule an appointment to a new time slot",
    description="Move an existing appointment to a new time_slot.",
    tags=["appointments"],
    operation_id="reschedule_appointment_to_slot",
)
async def reschedule_appointment_to_slot(
    appointment_id: str = Path(
        ...,
        description="Existing appointments.id to reschedule",
        example="APT-20451",
    ),
    body: AppointmentRescheduleRequest = Body(...),
) -> AppointmentRescheduleResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    a = (
        session.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient.id,
        )
        .first()
    )
    slot = session.query(TimeSlot).filter(TimeSlot.id == body.new_time_slot_id).first()
    if a is not None and slot is not None:
        old_slot = None
        if a.time_slot_id:
            old_slot = session.query(TimeSlot).filter(TimeSlot.id == a.time_slot_id).first()
        if old_slot is not None:
            if old_slot.capacity_booked > 0:
                old_slot.capacity_booked = old_slot.capacity_booked - 1
                old_slot.updated_at = datetime.utcnow()
        slot.capacity_booked = slot.capacity_booked + 1
        slot.updated_at = datetime.utcnow()
        old_status = a.status
        a.time_slot_id = slot.id
        a.start_datetime = slot.start_datetime
        a.end_datetime = slot.end_datetime
        a.status = "booked"
        a.provider_id = slot.provider_id
        a.clinic_location_id = slot.clinic_location_id
        a.appointment_type_id = slot.appointment_type_id
        a.updated_at = datetime.utcnow()
        hist = AppointmentStatusHistory(
            appointment_id=a.id,
            old_status=old_status,
            new_status=a.status,
            changed_at=datetime.utcnow(),
            changed_by_user_id=1,
            note="Rescheduled",
        )
        session.add(hist)
        session.commit()
        model = AppointmentModel(
            id=a.id,
            patient_id=a.patient_id,
            dependent_id=a.dependent_id,
            provider_id=a.provider_id,
            clinic_location_id=a.clinic_location_id,
            appointment_type_id=a.appointment_type_id,
            specialty_id=a.specialty_id,
            time_slot_id=a.time_slot_id,
            start_datetime=a.start_datetime.isoformat() if a.start_datetime else "",
            end_datetime=a.end_datetime.isoformat() if a.end_datetime else "",
            visit_mode=a.visit_mode,
            status=a.status,
            reason_for_visit=a.reason_for_visit,
            insurance_id=a.insurance_id,
            referral_id=a.referral_id,
            is_imaging=bool_from_int(a.is_imaging),
            created_at=a.created_at.isoformat() if a.created_at else None,
            updated_at=a.updated_at.isoformat() if a.updated_at else None,
        )
    else:
        model = AppointmentModel(
            id="",
            patient_id=patient.id,
            dependent_id=None,
            provider_id=None,
            clinic_location_id=0,
            appointment_type_id=0,
            specialty_id=None,
            time_slot_id=None,
            start_datetime="",
            end_datetime="",
            visit_mode="",
            status="",
            reason_for_visit=None,
            insurance_id=None,
            referral_id=None,
            is_imaging=False,
            created_at=None,
            updated_at=None,
        )
    session.close()
    return AppointmentRescheduleResponse(appointment=model)


@app.get(
    "/api/appointment_reminder_settings/{appointment_id}",
    response_model=AppointmentReminderSettingsResponse,
    summary="Get reminder settings for an appointment",
    description="Retrieve appointment_reminder_settings for a specific appointment id.",
    tags=["appointment_reminders"],
    operation_id="get_appointment_reminder_settings",
)
async def get_appointment_reminder_settings(
    appointment_id: str = Path(
        ...,
        description="appointments.id whose reminders should be fetched",
        example="APT-30987",
    )
) -> AppointmentReminderSettingsResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    appt = (
        session.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient.id,
        )
        .first()
    )
    if appt is None:
        session.close()
        return AppointmentReminderSettingsResponse(reminder_settings=None)
    rem = (
        session.query(AppointmentReminderSetting)
        .filter(AppointmentReminderSetting.appointment_id == appointment_id)
        .first()
    )
    if rem is None:
        session.close()
        return AppointmentReminderSettingsResponse(reminder_settings=None)
    model = AppointmentReminderSettingsModel(
        id=rem.id,
        appointment_id=rem.appointment_id,
        send_email=bool_from_int(rem.send_email),
        send_sms=bool_from_int(rem.send_sms),
        created_at=rem.created_at.isoformat() if rem.created_at else None,
        updated_at=rem.updated_at.isoformat() if rem.updated_at else None,
    )
    session.close()
    return AppointmentReminderSettingsResponse(reminder_settings=model)


@app.put(
    "/api/appointment_reminder_settings/{appointment_id}",
    response_model=AppointmentReminderSettingsPutResponse,
    summary="Create or replace reminder settings",
    description="Create or fully replace appointment_reminder_settings for the appointment.",
    tags=["appointment_reminders"],
    operation_id="put_appointment_reminder_settings",
)
async def put_appointment_reminder_settings(
    appointment_id: str = Path(
        ...,
        description="appointments.id to update reminder settings for",
        example="APT-30987",
    ),
    body: AppointmentReminderSettingsPutRequest = Body(...),
) -> AppointmentReminderSettingsPutResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    appt = (
        session.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient.id,
        )
        .first()
    )
    if appt is None:
        empty = AppointmentReminderSettingsModel(
            id=0,
            appointment_id=appointment_id,
            send_email=False,
            send_sms=False,
            created_at=None,
            updated_at=None,
        )
        session.close()
        return AppointmentReminderSettingsPutResponse(reminder_settings=empty)
    rem = (
        session.query(AppointmentReminderSetting)
        .filter(AppointmentReminderSetting.appointment_id == appointment_id)
        .first()
    )
    now = datetime.utcnow()
    if rem is None:
        rem = AppointmentReminderSetting(
            appointment_id=appointment_id,
            send_email=int_from_bool(body.send_email),
            send_sms=int_from_bool(body.send_sms),
            created_at=now,
            updated_at=now,
        )
        session.add(rem)
    else:
        rem.send_email = int_from_bool(body.send_email)
        rem.send_sms = int_from_bool(body.send_sms)
        rem.updated_at = now
    session.commit()
    model = AppointmentReminderSettingsModel(
        id=rem.id,
        appointment_id=rem.appointment_id,
        send_email=bool_from_int(rem.send_email),
        send_sms=bool_from_int(rem.send_sms),
        created_at=rem.created_at.isoformat() if rem.created_at else None,
        updated_at=rem.updated_at.isoformat() if rem.updated_at else None,
    )
    session.close()
    return AppointmentReminderSettingsPutResponse(reminder_settings=model)


@app.post(
    "/api/waitlist_entries",
    response_model=WaitlistEntryCreateResponse,
    summary="Create a new waitlist entry",
    description="Add the current patient or dependent to waitlist_entries.",
    tags=["waitlist"],
    operation_id="create_waitlist_entry",
)
async def create_waitlist_entry(
    body: WaitlistEntryCreateRequest = Body(...)
) -> WaitlistEntryCreateResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    weekdays_only_val = int_from_bool(bool(body.weekdays_only))
    auto_accept_val = int_from_bool(body.auto_accept)
    status_val = body.status if body.status else "active"
    new_entry = WaitlistEntry(
        patient_id=patient.id,
        dependent_id=body.dependent_id,
        specialty_id=body.specialty_id,
        provider_id=body.provider_id,
        clinic_location_id=body.clinic_location_id,
        appointment_type_id=body.appointment_type_id,
        visit_mode=body.visit_mode,
        preferred_after_time=body.preferred_after_time,
        preferred_before_time=body.preferred_before_time,
        weekdays_only=weekdays_only_val,
        min_notice_minutes=body.min_notice_minutes,
        auto_accept=auto_accept_val,
        status=status_val,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(new_entry)
    session.commit()
    model = WaitlistEntryModel(
        id=new_entry.id,
        patient_id=new_entry.patient_id,
        dependent_id=new_entry.dependent_id,
        specialty_id=new_entry.specialty_id,
        provider_id=new_entry.provider_id,
        clinic_location_id=new_entry.clinic_location_id,
        appointment_type_id=new_entry.appointment_type_id,
        visit_mode=new_entry.visit_mode,
        preferred_after_time=new_entry.preferred_after_time,
        preferred_before_time=new_entry.preferred_before_time,
        weekdays_only=bool_from_int(new_entry.weekdays_only),
        min_notice_minutes=new_entry.min_notice_minutes,
        auto_accept=bool_from_int(new_entry.auto_accept),
        status=new_entry.status,
        created_at=new_entry.created_at.isoformat() if new_entry.created_at else None,
        updated_at=new_entry.updated_at.isoformat() if new_entry.updated_at else None,
    )
    session.close()
    return WaitlistEntryCreateResponse(waitlist_entry=model)


@app.get(
    "/api/diagnosis_codes",
    response_model=DiagnosisCodesResponse,
    summary="Search diagnosis codes by code or description",
    description="Lookup diagnosis_codes entries using code or text.",
    tags=["referrals"],
    operation_id="search_diagnosis_codes",
)
async def search_diagnosis_codes(
    code: Optional[str] = Query(
        None,
        description="Diagnosis code exact or prefix match",
        example="I10",
    ),
    description_contains: Optional[str] = Query(
        None,
        description="Wildcard search on description",
        example="hypertension",
    ),
    limit: Optional[int] = Query(
        None,
        description="Max records to return",
        example=20,
    ),
) -> DiagnosisCodesResponse:
    session = SessionLocal()
    query = session.query(DiagnosisCode)
    if code:
        query = query.filter(DiagnosisCode.code.ilike(f"{code}%"))
    if description_contains:
        query = query.filter(DiagnosisCode.description.ilike(f"%{description_contains}%"))
    if limit:
        query = query.limit(limit)
    rows = query.all()
    codes = []
    for d in rows:
        codes.append(
            DiagnosisCodeModel(
                id=d.id,
                code=d.code,
                description=d.description,
                created_at=d.created_at.isoformat() if d.created_at else None,
                updated_at=d.updated_at.isoformat() if d.updated_at else None,
            )
        )
    session.close()
    return DiagnosisCodesResponse(diagnosis_codes=codes)


@app.post(
    "/api/referrals",
    response_model=ReferralCreateResponse,
    summary="Create a new referral for current patient",
    description="Create a referrals record for the current patient.",
    tags=["referrals"],
    operation_id="create_referral",
)
async def create_referral(
    body: ReferralCreateRequest = Body(...)
) -> ReferralCreateResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    diag = (
        session.query(DiagnosisCode)
        .filter(DiagnosisCode.code == body.diagnosis_code)
        .first()
    )
    if diag is None:
        diag = DiagnosisCode(
            code=body.diagnosis_code,
            description=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(diag)
        session.commit()
    status_val = body.status if body.status else "active"
    try:
        ref_exp_date = datetime.fromisoformat(body.referral_expiration_date).date()
    except Exception:
        ref_exp_date = datetime.utcnow().date()
    new_ref = Referral(
        patient_id=patient.id,
        department_id=body.department_id,
        specialty_id=body.specialty_id,
        referring_provider_name=body.referring_provider_name,
        diagnosis_code_id=diag.id,
        referral_expiration_date=ref_exp_date,
        status=status_val,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(new_ref)
    session.commit()
    model = ReferralModel(
        id=new_ref.id,
        patient_id=new_ref.patient_id,
        department_id=new_ref.department_id,
        specialty_id=new_ref.specialty_id,
        referring_provider_name=new_ref.referring_provider_name,
        diagnosis_code_id=new_ref.diagnosis_code_id,
        referral_expiration_date=new_ref.referral_expiration_date.isoformat()
        if new_ref.referral_expiration_date
        else "",
        status=new_ref.status,
        created_at=new_ref.created_at.isoformat() if new_ref.created_at else None,
        updated_at=new_ref.updated_at.isoformat() if new_ref.updated_at else None,
    )
    session.close()
    return ReferralCreateResponse(referral=model)


@app.post(
    "/api/appointment_referrals",
    response_model=AppointmentReferralCreateResponse,
    summary="Link a referral to an appointment",
    description="Create an appointment_referrals record linking an appointment to a referral.",
    tags=["referrals"],
    operation_id="link_referral_to_appointment",
)
async def link_referral_to_appointment(
    body: AppointmentReferralCreateRequest = Body(...)
) -> AppointmentReferralCreateResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    appt = (
        session.query(Appointment)
        .filter(
            Appointment.id == body.appointment_id,
            Appointment.patient_id == patient.id,
        )
        .first()
    )
    ref = (
        session.query(Referral)
        .filter(
            Referral.id == body.referral_id,
            Referral.patient_id == patient.id,
        )
        .first()
    )
    if appt is None or ref is None:
        empty = AppointmentReferralModel(
            id=0,
            appointment_id=body.appointment_id,
            referral_id=body.referral_id,
            created_at=None,
            updated_at=None,
        )
        session.close()
        return AppointmentReferralCreateResponse(appointment_referral=empty)
    existing = (
        session.query(AppointmentReferral)
        .filter(
            AppointmentReferral.appointment_id == body.appointment_id,
            AppointmentReferral.referral_id == body.referral_id,
        )
        .first()
    )
    if existing is None:
        new_ar = AppointmentReferral(
            appointment_id=body.appointment_id,
            referral_id=body.referral_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(new_ar)
        session.commit()
        ar = new_ar
    else:
        ar = existing
    model = AppointmentReferralModel(
        id=ar.id,
        appointment_id=ar.appointment_id,
        referral_id=ar.referral_id,
        created_at=ar.created_at.isoformat() if ar.created_at else None,
        updated_at=ar.updated_at.isoformat() if ar.updated_at else None,
    )
    session.close()
    return AppointmentReferralCreateResponse(appointment_referral=model)


@app.post(
    "/api/appointment_checkins",
    response_model=AppointmentCheckinCreateResponse,
    summary="Record a new check-in event",
    description="Insert a new appointment_checkins row for an appointment.",
    tags=["checkins"],
    operation_id="create_appointment_checkin",
)
async def create_appointment_checkin(
    body: AppointmentCheckinCreateRequest = Body(...)
) -> AppointmentCheckinCreateResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    appt = (
        session.query(Appointment)
        .filter(
            Appointment.id == body.appointment_id,
            Appointment.patient_id == patient.id,
        )
        .first()
    )
    if appt is None:
        empty = AppointmentCheckinModel(
            id=0,
            appointment_id=body.appointment_id,
            check_in_time="",
            exam_room=None,
            created_at=None,
        )
        session.close()
        return AppointmentCheckinCreateResponse(checkin=empty)
    try:
        check_in_dt = datetime.fromisoformat(body.check_in_time.replace("Z", "+00:00"))
    except Exception:
        check_in_dt = datetime.utcnow()
    new_checkin = AppointmentCheckin(
        appointment_id=body.appointment_id,
        check_in_time=check_in_dt,
        exam_room=body.exam_room,
        created_at=datetime.utcnow(),
    )
    session.add(new_checkin)
    session.commit()
    model = AppointmentCheckinModel(
        id=new_checkin.id,
        appointment_id=new_checkin.appointment_id,
        check_in_time=new_checkin.check_in_time.isoformat()
        if new_checkin.check_in_time
        else "",
        exam_room=new_checkin.exam_room,
        created_at=new_checkin.created_at.isoformat() if new_checkin.created_at else None,
    )
    session.close()
    return AppointmentCheckinCreateResponse(checkin=model)


@app.post(
    "/api/appointments/{appointment_id}/status",
    response_model=AppointmentStatusChangeResponse,
    summary="Change appointment status and record history",
    description="Update an appointment's status field and create history.",
    tags=["appointments"],
    operation_id="change_appointment_status",
)
async def change_appointment_status(
    appointment_id: str = Path(
        ...,
        description="appointments.id whose status will be updated",
        example="APT-41200",
    ),
    body: AppointmentStatusChangeRequest = Body(...),
) -> AppointmentStatusChangeResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    a = (
        session.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient.id,
        )
        .first()
    )
    if a is None:
        empty_appt = AppointmentStatusChangeAppointmentModel(
            id=appointment_id,
            status="",
            updated_at=None,
        )
        empty_hist = AppointmentStatusHistoryModel(
            id=0,
            appointment_id=appointment_id,
            old_status=None,
            new_status="",
            changed_at=None,
            changed_by_user_id=None,
            note=None,
        )
        session.close()
        return AppointmentStatusChangeResponse(
            appointment=empty_appt, status_history=empty_hist
        )
    old_status = a.status
    a.status = body.new_status
    now = datetime.utcnow()
    a.updated_at = now
    hist = AppointmentStatusHistory(
        appointment_id=a.id,
        old_status=old_status,
        new_status=a.status,
        changed_at=now,
        changed_by_user_id=1,
        note=body.note,
    )
    session.add(hist)
    session.commit()
    appt_model = AppointmentStatusChangeAppointmentModel(
        id=a.id,
        status=a.status,
        updated_at=a.updated_at.isoformat() if a.updated_at else None,
    )
    hist_model = AppointmentStatusHistoryModel(
        id=hist.id,
        appointment_id=hist.appointment_id,
        old_status=hist.old_status,
        new_status=hist.new_status,
        changed_at=hist.changed_at.isoformat() if hist.changed_at else None,
        changed_by_user_id=hist.changed_by_user_id,
        note=hist.note,
    )
    session.close()
    return AppointmentStatusChangeResponse(
        appointment=appt_model, status_history=hist_model
    )


@app.get(
    "/api/satisfaction_surveys",
    response_model=SatisfactionSurveysResponse,
    summary="List satisfaction surveys for current patient",
    description="Retrieve satisfaction_surveys entries for the current patient's appointments.",
    tags=["surveys"],
    operation_id="list_satisfaction_surveys",
)
async def list_satisfaction_surveys(
    appointment_id: Optional[str] = Query(
        None,
        description="Filter surveys by specific appointment id",
        example="APT-20451",
    ),
    has_rating: Optional[bool] = Query(
        None,
        description="If true, only return surveys where rating is not null",
        example=True,
    ),
) -> SatisfactionSurveysResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    query = session.query(SatisfactionSurvey).filter(
        SatisfactionSurvey.patient_id == patient.id
    )
    if appointment_id:
        query = query.filter(SatisfactionSurvey.appointment_id == appointment_id)
    if has_rating:
        query = query.filter(SatisfactionSurvey.rating.isnot(None))
    rows = query.all()
    surveys = []
    for s in rows:
        surveys.append(
            SatisfactionSurveyModel(
                id=s.id,
                appointment_id=s.appointment_id,
                patient_id=s.patient_id,
                rating=s.rating,
                wait_time_minutes=s.wait_time_minutes,
                comments=s.comments,
                created_at=s.created_at.isoformat() if s.created_at else None,
                updated_at=s.updated_at.isoformat() if s.updated_at else None,
            )
        )
    session.close()
    return SatisfactionSurveysResponse(satisfaction_surveys=surveys)


@app.post(
    "/api/satisfaction_surveys",
    response_model=SatisfactionSurveyCreateResponse,
    summary="Create a satisfaction survey for an appointment",
    description="Insert a new satisfaction_surveys record for a completed appointment.",
    tags=["surveys"],
    operation_id="create_satisfaction_survey",
)
async def create_satisfaction_survey(
    body: SatisfactionSurveyCreateRequest = Body(...)
) -> SatisfactionSurveyCreateResponse:
    session = SessionLocal()
    patient = get_current_patient(session)
    appt = (
        session.query(Appointment)
        .filter(
            Appointment.id == body.appointment_id,
            Appointment.patient_id == patient.id,
        )
        .first()
    )
    if appt is None:
        empty = SatisfactionSurveyModel(
            id=0,
            appointment_id=body.appointment_id,
            patient_id=patient.id,
            rating=body.rating,
            wait_time_minutes=body.wait_time_minutes,
            comments=body.comments,
            created_at=None,
            updated_at=None,
        )
        session.close()
        return SatisfactionSurveyCreateResponse(satisfaction_survey=empty)
    existing = (
        session.query(SatisfactionSurvey)
        .filter(SatisfactionSurvey.appointment_id == body.appointment_id)
        .first()
    )
    now = datetime.utcnow()
    if existing is None:
        new_s = SatisfactionSurvey(
            appointment_id=body.appointment_id,
            patient_id=patient.id,
            rating=body.rating,
            wait_time_minutes=body.wait_time_minutes,
            comments=body.comments,
            created_at=now,
            updated_at=now,
        )
        session.add(new_s)
        session.commit()
        s = new_s
    else:
        existing.rating = body.rating
        existing.wait_time_minutes = body.wait_time_minutes
        existing.comments = body.comments
        existing.updated_at = now
        session.commit()
        s = existing
    model = SatisfactionSurveyModel(
        id=s.id,
        appointment_id=s.appointment_id,
        patient_id=s.patient_id,
        rating=s.rating,
        wait_time_minutes=s.wait_time_minutes,
        comments=s.comments,
        created_at=s.created_at.isoformat() if s.created_at else None,
        updated_at=s.updated_at.isoformat() if s.updated_at else None,
    )
    session.close()
    return SatisfactionSurveyCreateResponse(satisfaction_survey=model)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)