import os
from datetime import datetime, date
from typing import List, Optional, Dict

from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Text,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    func,
    and_,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

database_url = os.getenv("DATABASE_PATH", "sqlite:///outputs/databases/carequeue_outpatient_clinic_scheduler.db")

engine = create_engine("sqlite:////mnt/genming/case-rerun-20261103/expanded-history/point-3855af42427414/cases/booking_and_scheduling_11_4/teacher_structured/student/final.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())


class Clinic(Base):
    __tablename__ = "clinics"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    __table_args__ = (UniqueConstraint("name", name="idx_clinics_name"),)


class Specialty(Base):
    __tablename__ = "specialties"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())


class Provider(Base):
    __tablename__ = "providers"
    id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False)
    specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=False)
    primary_clinic_id = Column(String, ForeignKey("clinics.id"))
    active_flag = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    specialty = relationship("Specialty", foreign_keys=[specialty_id])


class ProviderWeeklySchedule(Base):
    __tablename__ = "provider_weekly_schedules"
    id = Column(Integer, primary_key=True)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=False)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    lunch_start_time = Column(String)
    lunch_end_time = Column(String)
    slot_duration_minutes = Column(Integer, nullable=False)
    capacity_per_slot = Column(Integer, nullable=False)
    visit_mode = Column(String, nullable=False, default="in_person")
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6"),
        CheckConstraint("visit_mode IN ('in_person','telehealth')"),
    )


class TimeOffBlock(Base):
    __tablename__ = "time_off_blocks"
    id = Column(Integer, primary_key=True)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=False)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    reason = Column(Text)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())


class VisitType(Base):
    __tablename__ = "visit_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    default_duration_minutes = Column(Integer, nullable=False)
    visit_mode = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("visit_mode IN ('in_person','telehealth','either')"),
    )


class ProviderVisitType(Base):
    __tablename__ = "provider_visit_types"
    id = Column(Integer, primary_key=True)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=False)
    visit_type_id = Column(Integer, ForeignKey("visit_types.id"), nullable=False)
    active_flag = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    visit_type = relationship("VisitType", foreign_keys=[visit_type_id])
    __table_args__ = (
        UniqueConstraint("provider_id", "visit_type_id"),
    )


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    preferred_communication_channel = Column(String, nullable=False)
    primary_insurance = Column(String)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("preferred_communication_channel IN ('sms','email','phone','none')"),
    )


class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"
    id = Column(String, primary_key=True)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=False)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    visit_type_id = Column(Integer, ForeignKey("visit_types.id"))
    visit_mode = Column(String, nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    capacity_per_slot = Column(Integer, nullable=False)
    base_capacity_per_slot = Column(Integer, nullable=False)
    is_overbook_capable = Column(Integer, nullable=False, default=0)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("visit_mode IN ('in_person','telehealth')"),
    )


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(String, primary_key=True)
    appointment_slot_id = Column(String, ForeignKey("appointment_slots.id"), nullable=False)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=False)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    visit_type_id = Column(Integer, ForeignKey("visit_types.id"), nullable=False)
    visit_mode = Column(String, nullable=False)
    status = Column(String, nullable=False)
    insurance_at_booking = Column(String)
    communication_channel_at_booking = Column(String)
    is_same_day_booking = Column(Integer, nullable=False, default=0)
    booked_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    __table_args__ = (
        CheckConstraint("visit_mode IN ('in_person','telehealth')"),
        CheckConstraint("status IN ('scheduled','confirmed','checked_in','completed','no_show','canceled_by_patient','canceled_by_clinic')"),
        CheckConstraint("communication_channel_at_booking IN ('sms','email','phone','none')"),
    )


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"
    id = Column(Integer, primary_key=True)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False)
    old_status = Column(String)
    new_status = Column(String, nullable=False)
    changed_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    changed_by_user_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(Text)
    __table_args__ = (
        CheckConstraint("old_status IN ('scheduled','confirmed','checked_in','completed','no_show','canceled_by_patient','canceled_by_clinic')"),
        CheckConstraint("new_status IN ('scheduled','confirmed','checked_in','completed','no_show','canceled_by_patient','canceled_by_clinic')"),
    )


class CheckIn(Base):
    __tablename__ = "check_ins"
    id = Column(Integer, primary_key=True)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False, unique=True)
    arrival_time = Column(DateTime, nullable=False)
    room_assignment = Column(String)
    wait_time_seconds = Column(Integer)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())


class VisitNote(Base):
    __tablename__ = "visit_notes"
    id = Column(String, primary_key=True)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False)
    note_type = Column(String, nullable=False)
    locked_flag = Column(Integer, nullable=False, default=0)
    metadata_json = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())


class BillingCode(Base):
    __tablename__ = "billing_codes"
    code = Column(String, primary_key=True)
    description = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())


class DiagnosisTag(Base):
    __tablename__ = "diagnosis_tags"
    id = Column(Integer, primary_key=True)
    tag = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())


class VisitNoteBillingCode(Base):
    __tablename__ = "visit_note_billing_codes"
    id = Column(Integer, primary_key=True)
    visit_note_id = Column(String, ForeignKey("visit_notes.id"), nullable=False)
    billing_code = Column(String, ForeignKey("billing_codes.code"), nullable=False)
    __table_args__ = (
        UniqueConstraint("visit_note_id", "billing_code"),
    )


class VisitNoteDiagnosisTag(Base):
    __tablename__ = "visit_note_diagnosis_tags"
    id = Column(Integer, primary_key=True)
    visit_note_id = Column(String, ForeignKey("visit_notes.id"), nullable=False)
    diagnosis_tag_id = Column(Integer, ForeignKey("diagnosis_tags.id"), nullable=False)
    __table_args__ = (
        UniqueConstraint("visit_note_id", "diagnosis_tag_id"),
    )


class DailyRosterSummary(Base):
    __tablename__ = "daily_roster_summaries"
    id = Column(Integer, primary_key=True)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    roster_date = Column(Date, nullable=False)
    summary_json = Column(Text, nullable=False)
    generated_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    generated_by_user_id = Column(Integer, ForeignKey("users.id"))
    __table_args__ = (
        UniqueConstraint("clinic_id", "roster_date"),
    )


class UtilizationReport(Base):
    __tablename__ = "utilization_reports"
    id = Column(Integer, primary_key=True)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    report_json = Column(Text, nullable=False)
    generated_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    generated_by_user_id = Column(Integer, ForeignKey("users.id"))


Index("idx_users_email", User.email)
Index("idx_pws_provider_day", ProviderWeeklySchedule.provider_id, ProviderWeeklySchedule.day_of_week)
Index("idx_pws_clinic", ProviderWeeklySchedule.clinic_id)
Index("idx_timeoff_provider_range", TimeOffBlock.provider_id, TimeOffBlock.start_datetime, TimeOffBlock.end_datetime)
Index("idx_timeoff_clinic", TimeOffBlock.clinic_id)
Index("idx_pvt_provider", ProviderVisitType.provider_id)
Index("idx_pvt_visit_type", ProviderVisitType.visit_type_id)
Index("idx_patients_dob", Patient.date_of_birth)
Index("idx_patients_name", Patient.full_name)
Index("idx_slots_provider_time", AppointmentSlot.provider_id, AppointmentSlot.start_datetime)
Index("idx_slots_clinic_time", AppointmentSlot.clinic_id, AppointmentSlot.start_datetime)
Index("idx_slots_visit_type", AppointmentSlot.visit_type_id)
Index("idx_bookings_slot", Booking.appointment_slot_id)
Index("idx_bookings_provider_status", Booking.provider_id, Booking.status)
Index("idx_bookings_clinic_time", Booking.clinic_id, Booking.booked_at)
Index("idx_bookings_patient", Booking.patient_id)
Index("idx_bsh_booking", BookingStatusHistory.booking_id)
Index("idx_checkins_booking", CheckIn.booking_id)
Index("idx_visit_notes_booking", VisitNote.booking_id)
Index("idx_vnbc_visit_note", VisitNoteBillingCode.visit_note_id)
Index("idx_vndt_visit_note", VisitNoteDiagnosisTag.visit_note_id)
Index("idx_roster_clinic_date", DailyRosterSummary.clinic_id, DailyRosterSummary.roster_date)
Index("idx_utilization_clinic_range", UtilizationReport.clinic_id, UtilizationReport.start_date, UtilizationReport.end_date)

Base.metadata.create_all(engine)

app = FastAPI(title="CareQueue Outpatient Clinic Scheduler API", version="1.0.0")

class ClinicModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Clinic ID (e.g. CLIN-01)", example="CLIN-01")
    name: str = Field(..., description="Clinic name", example="Downtown Clinic")
    location: Optional[str] = Field(None, description="Location or address description", example="123 Main St, Downtown")
    created_at: datetime = Field(..., description="Creation timestamp (ISO8601)", example="2025-12-01T10:00:00")
    updated_at: datetime = Field(..., description="Last update timestamp (ISO8601)", example="2025-12-15T09:30:00")


class ClinicsListResponse(BaseModel):
    clinics: List[ClinicModel] = Field(..., description="List of clinics", example=[])


class SpecialtyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Specialty ID", example=1)
    name: str = Field(..., description="Specialty name", example="Pediatrics")
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-10-01T12:00:00")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-11-01T08:45:00")


class SpecialtiesListResponse(BaseModel):
    specialties: List[SpecialtyModel] = Field(..., description="List of specialties", example=[])


class SpecialtyCreateRequest(BaseModel):
    name: str = Field(..., description="Unique specialty name", example="Family Medicine")


class SpecialtyCreateResponse(SpecialtyModel):
    pass


class ProviderModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Provider ID", example="PROV-4401")
    full_name: str = Field(..., description="Provider full name", example="Dr. Alice Nguyen")
    specialty_id: int = Field(..., description="Associated specialty ID", example=2)
    primary_clinic_id: Optional[str] = Field(None, description="Primary clinic ID or null", example="CLIN-02")
    active_flag: int = Field(..., description="Active status flag", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2026-01-02T09:00:00")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2026-01-02T09:00:00")


class ProviderCreateRequest(BaseModel):
    id: Optional[str] = Field(None, description="Optional provider ID; if omitted, generated like PROV-xxxx", example="PROV-4401")
    full_name: str = Field(..., description="Provider full legal name", example="Dr. Alice Nguyen")
    specialty_id: int = Field(..., description="ID of specialty from specialties table", example=2)
    primary_clinic_id: Optional[str] = Field(None, description="Clinic ID where provider primarily practices", example="CLIN-02")
    active_flag: Optional[int] = Field(1, description="1 if provider is active, 0 if inactive", example=1)


class ProvidersListItemModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Provider ID", example="PROV-2201")
    full_name: str = Field(..., description="Provider full name", example="Dr. John Smith")
    specialty_id: int = Field(..., description="Specialty ID", example=1)
    specialty_name: Optional[str] = Field(None, description="Specialty name from specialties", example="Family Medicine")
    primary_clinic_id: Optional[str] = Field(None, description="Primary clinic ID", example="CLIN-01")
    active_flag: int = Field(..., description="Active status flag", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-10T08:00:00")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-11-20T14:30:00")


class ProvidersListResponse(BaseModel):
    providers: List[ProvidersListItemModel] = Field(..., description="List of providers", example=[])


class WeeklyScheduleCreateRequest(BaseModel):
    clinic_id: str = Field(..., description="Clinic where this schedule applies", example="CLIN-01")
    day_of_week: int = Field(..., description="0=Monday through 6=Sunday", example=0)
    start_time: str = Field(..., description="Daily start time in HH:MM format", example="09:00")
    end_time: str = Field(..., description="Daily end time in HH:MM format", example="17:00")
    lunch_start_time: Optional[str] = Field(None, description="Lunch start time in HH:MM, or null", example="12:00")
    lunch_end_time: Optional[str] = Field(None, description="Lunch end time in HH:MM, or null", example="13:00")
    slot_duration_minutes: int = Field(..., description="Default appointment slot duration in minutes", example=30)
    capacity_per_slot: int = Field(..., description="Number of patients allowed per base slot", example=2)
    visit_mode: str = Field(..., description="Visit mode for slots (in_person or telehealth)", example="in_person")


class WeeklyScheduleModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Weekly schedule ID", example=101)
    provider_id: str = Field(..., description="Provider ID", example="PROV-4401")
    clinic_id: str = Field(..., description="Clinic ID where schedule applies", example="CLIN-01")
    day_of_week: int = Field(..., description="0=Monday through 6=Sunday", example=0)
    start_time: str = Field(..., description="Start time HH:MM", example="09:00")
    end_time: str = Field(..., description="End time HH:MM", example="17:00")
    lunch_start_time: Optional[str] = Field(None, description="Lunch start time HH:MM or null", example="12:00")
    lunch_end_time: Optional[str] = Field(None, description="Lunch end time HH:MM or null", example="13:00")
    slot_duration_minutes: int = Field(..., description="Slot duration in minutes", example=30)
    capacity_per_slot: int = Field(..., description="Capacity per base slot", example=2)
    visit_mode: str = Field(..., description="Visit mode (in_person or telehealth)", example="in_person")
    created_at: datetime = Field(..., description="Creation timestamp", example="2026-01-02T09:05:00")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2026-01-02T09:05:00")


class WeeklySchedulesListResponse(BaseModel):
    weekly_schedules: List[WeeklyScheduleModel] = Field(..., description="List of weekly schedules", example=[])


class VisitTypeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Visit type ID", example=5)
    name: str = Field(..., description="Visit type name", example="New Patient Visit")
    default_duration_minutes: int = Field(..., description="Default duration in minutes", example=30)
    visit_mode: str = Field(..., description="Supported mode: in_person, telehealth, or either", example="either")
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-06-01T10:00:00")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-07-01T10:00:00")


class VisitTypesListResponse(BaseModel):
    visit_types: List[VisitTypeModel] = Field(..., description="List of visit types", example=[])


class VisitTypeCreateRequest(BaseModel):
    name: str = Field(..., description="Unique visit type name", example="Annual Wellness Visit")
    default_duration_minutes: int = Field(..., description="Default duration for appointments of this type", example=30)
    visit_mode: str = Field(..., description="in_person, telehealth, or either", example="in_person")


class VisitTypeCreateResponse(VisitTypeModel):
    pass


class ProviderVisitTypeCreateRequest(BaseModel):
    visit_type_id: int = Field(..., description="Visit type ID to associate", example=5)
    active_flag: Optional[int] = Field(1, description="1 to mark active, 0 inactive", example=1)


class ProviderVisitTypeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Provider-visit-type mapping ID", example=201)
    provider_id: str = Field(..., description="Provider ID", example="PROV-4401")
    visit_type_id: int = Field(..., description="Visit type ID", example=5)
    visit_type_name: Optional[str] = Field(None, description="Visit type name from visit_types", example="New Patient Visit")
    active_flag: int = Field(..., description="Active flag for this mapping", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2026-01-02T09:15:00")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2026-01-02T09:15:00")


class ProviderVisitTypesListResponse(BaseModel):
    provider_visit_types: List[ProviderVisitTypeModel] = Field(..., description="List of provider visit types", example=[])


class TimeOffBlockCreateRequest(BaseModel):
    provider_id: str = Field(..., description="Provider ID taking time off", example="PROV-2201")
    clinic_id: str = Field(..., description="Clinic where time off applies", example="CLIN-02")
    start_datetime: str = Field(..., description="Start of time off (ISO8601)", example="2026-01-15T13:00:00")
    end_datetime: str = Field(..., description="End of time off (ISO8601)", example="2026-01-15T15:00:00")
    reason: Optional[str] = Field(None, description="Optional reason for time off", example="Provider in training")


class TimeOffBlockModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Time-off block ID", example=301)
    provider_id: str = Field(..., description="Provider ID", example="PROV-2201")
    clinic_id: str = Field(..., description="Clinic ID", example="CLIN-02")
    start_datetime: datetime = Field(..., description="Start datetime of time off", example="2026-01-15T13:00:00")
    end_datetime: datetime = Field(..., description="End datetime of time off", example="2026-01-15T15:00:00")
    reason: Optional[str] = Field(None, description="Reason for time off", example="Admin time")
    created_by_user_id: Optional[int] = Field(None, description="User ID who created this block (implicit user 1)", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2026-01-10T10:00:00")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2026-01-10T10:00:00")


class TimeOffBlocksListResponse(BaseModel):
    time_off_blocks: List[TimeOffBlockModel] = Field(..., description="List of time-off blocks", example=[])


class PatientCreateRequest(BaseModel):
    full_name: str = Field(..., description="Patient full name", example="John Doe")
    date_of_birth: str = Field(..., description="Date of birth in YYYY-MM-DD format", example="1985-04-12")
    preferred_communication_channel: str = Field(..., description="sms, email, phone, or none", example="sms")
    primary_insurance: Optional[str] = Field(None, description="Primary insurance payer name", example="BlueCross")


class PatientModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Patient ID", example=1001)
    full_name: str = Field(..., description="Patient full name", example="John Doe")
    date_of_birth: date = Field(..., description="Date of birth", example="1985-04-12")
    preferred_communication_channel: str = Field(..., description="Preferred communication channel", example="sms")
    primary_insurance: Optional[str] = Field(None, description="Primary insurance name", example="BlueCross")
    created_at: datetime = Field(..., description="Creation timestamp", example="2026-01-02T09:20:00")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2026-01-02T09:20:00")


class PatientsListResponse(BaseModel):
    patients: List[PatientModel] = Field(..., description="List of patients", example=[])


class AppointmentSlotCreateRequest(BaseModel):
    id: Optional[str] = Field(None, description="Optional slot ID; if omitted, generated like S-uuid", example="SLOT-20260203-0800-1")
    provider_id: str = Field(..., description="Provider ID for the slot", example="PROV-3344")
    clinic_id: str = Field(..., description="Clinic ID where the slot occurs", example="CLIN-01")
    visit_type_id: Optional[int] = Field(None, description="Optional visit type ID associated with slot", example=5)
    visit_mode: str = Field(..., description="Visit mode: in_person or telehealth", example="in_person")
    start_datetime: str = Field(..., description="Start datetime (ISO8601)", example="2026-02-03T08:00:00")
    end_datetime: str = Field(..., description="End datetime (ISO8601)", example="2026-02-03T08:15:00")
    capacity_per_slot: int = Field(..., description="Current capacity for this slot (includes overbook capacity)", example=3)
    base_capacity_per_slot: int = Field(..., description="Baseline capacity without overbooking", example=2)
    is_overbook_capable: Optional[int] = Field(0, description="1 if slot permits overbooking beyond base capacity", example=1)


class AppointmentSlotModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Appointment slot ID", example="SLOT-20260203-0800-1")
    provider_id: str = Field(..., description="Provider ID", example="PROV-3344")
    clinic_id: str = Field(..., description="Clinic ID", example="CLIN-01")
    visit_type_id: Optional[int] = Field(None, description="Visit type ID or null", example=5)
    visit_mode: str = Field(..., description="Visit mode", example="in_person")
    start_datetime: datetime = Field(..., description="Slot start datetime", example="2026-02-03T08:00:00")
    end_datetime: datetime = Field(..., description="Slot end datetime", example="2026-02-03T08:15:00")
    capacity_per_slot: int = Field(..., description="Current capacity per slot", example=3)
    base_capacity_per_slot: int = Field(..., description="Base capacity without overbooking", example=2)
    is_overbook_capable: int = Field(..., description="1 if overbook capable, else 0", example=1)
    created_by_user_id: Optional[int] = Field(None, description="User who created slot (implicit 1)", example=1)
    created_at: datetime = Field(..., description="Created timestamp", example="2026-01-02T09:25:00")
    updated_at: datetime = Field(..., description="Updated timestamp", example="2026-01-02T09:25:00")


class AppointmentSlotUpdateRequest(BaseModel):
    capacity_per_slot: Optional[int] = Field(None, description="New capacity_per_slot value", example=3)
    is_overbook_capable: Optional[int] = Field(None, description="1 to allow overbooking, 0 to disallow", example=1)
    visit_type_id: Optional[int] = Field(None, description="Optional new visit_type_id for slot", example=5)


class AppointmentSlotWithAvailabilityModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Slot ID", example="SLOT-20260103-0900-1")
    provider_id: str = Field(..., description="Provider ID", example="PROV-2201")
    clinic_id: str = Field(..., description="Clinic ID", example="CLIN-01")
    visit_type_id: Optional[int] = Field(None, description="Visit type ID or null", example=5)
    visit_mode: str = Field(..., description="Visit mode", example="in_person")
    start_datetime: datetime = Field(..., description="Start datetime", example="2026-01-03T09:00:00")
    end_datetime: datetime = Field(..., description="End datetime", example="2026-01-03T09:30:00")
    capacity_per_slot: int = Field(..., description="Total capacity for this slot", example=2)
    base_capacity_per_slot: int = Field(..., description="Base capacity without overbooking", example=2)
    is_overbook_capable: int = Field(..., description="Overbook capability flag", example=0)
    current_bookings_count: int = Field(..., description="Count of non-canceled bookings in this slot", example=1)
    remaining_capacity: int = Field(..., description="capacity_per_slot - current_bookings_count", example=1)
    created_by_user_id: Optional[int] = Field(None, description="User who created slot", example=1)
    created_at: datetime = Field(..., description="Created at", example="2025-12-15T10:00:00")
    updated_at: datetime = Field(..., description="Updated at", example="2025-12-15T10:00:00")


class AppointmentSlotsListResponse(BaseModel):
    appointment_slots: List[AppointmentSlotWithAvailabilityModel] = Field(..., description="List of appointment slots", example=[])


class BookingCreateRequest(BaseModel):
    id: Optional[str] = Field(None, description="Optional booking ID; if omitted, generated like BK-xxxxx", example="BK-15001")
    appointment_slot_id: str = Field(..., description="Appointment slot ID to book", example="SLOT-20260103-0900-1")
    provider_id: str = Field(..., description="Provider ID (must match slot)", example="PROV-2201")
    clinic_id: str = Field(..., description="Clinic ID (must match slot)", example="CLIN-01")
    patient_id: int = Field(..., description="Patient ID for the booking", example=1001)
    visit_type_id: int = Field(..., description="Visit type ID being booked", example=5)
    visit_mode: str = Field(..., description="Visit mode: in_person or telehealth", example="in_person")
    status: str = Field(..., description="Initial booking status", example="scheduled")
    insurance_at_booking: Optional[str] = Field(None, description="Insurance name captured at booking", example="BlueCross")
    communication_channel_at_booking: Optional[str] = Field(None, description="Communication channel at booking", example="sms")
    is_same_day_booking: Optional[int] = Field(0, description="1 if booked on same day as appointment date", example=0)


class BookingModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Booking ID", example="BK-15001")
    appointment_slot_id: str = Field(..., description="Appointment slot ID", example="SLOT-20260103-0900-1")
    provider_id: str = Field(..., description="Provider ID", example="PROV-2201")
    clinic_id: str = Field(..., description="Clinic ID", example="CLIN-01")
    patient_id: int = Field(..., description="Patient ID", example=1001)
    visit_type_id: int = Field(..., description="Visit type ID", example=5)
    visit_mode: str = Field(..., description="Visit mode", example="in_person")
    status: str = Field(..., description="Current booking status", example="scheduled")
    insurance_at_booking: Optional[str] = Field(None, description="Insurance at booking", example="BlueCross")
    communication_channel_at_booking: Optional[str] = Field(None, description="Communication channel at booking", example="sms")
    is_same_day_booking: int = Field(..., description="Same-day flag", example=0)
    booked_at: datetime = Field(..., description="Time when booking was created", example="2026-01-02T09:30:00")
    created_by_user_id: Optional[int] = Field(None, description="User who created booking (1)", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2026-01-02T09:30:00")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2026-01-02T09:30:00")


class BookingStatusUpdateRequest(BaseModel):
    new_status: str = Field(..., description="New booking status", example="scheduled")
    reason: Optional[str] = Field(None, description="Why the status changed, stored in booking_status_history.reason", example="Rescheduled by patient")


class BookingStatusHistoryEntryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Status history record ID", example=501)
    booking_id: str = Field(..., description="Booking ID", example="BK-10293")
    old_status: Optional[str] = Field(None, description="Previous status", example="confirmed")
    new_status: str = Field(..., description="New status", example="scheduled")
    changed_at: datetime = Field(..., description="Time of change", example="2026-01-03T10:00:00")
    changed_by_user_id: Optional[int] = Field(None, description="User who changed status (1)", example=1)
    reason: Optional[str] = Field(None, description="Reason for status change", example="Rescheduled by clinic")


class BookingStatusUpdateBookingPart(BaseModel):
    id: str = Field(..., description="Booking ID", example="BK-10293")
    status: str = Field(..., description="Updated status", example="scheduled")
    updated_at: datetime = Field(..., description="Timestamp when status was updated", example="2026-01-03T10:00:00")


class BookingStatusUpdateResponse(BaseModel):
    booking: BookingStatusUpdateBookingPart = Field(..., description="Updated booking", example={})
    status_history_entry: BookingStatusHistoryEntryModel = Field(..., description="Created status history entry", example={})


class BookingListItemModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Booking ID", example="BK-8891")
    appointment_slot_id: str = Field(..., description="Slot ID", example="SLOT-20260105-0900-1")
    provider_id: str = Field(..., description="Provider ID", example="PROV-2201")
    clinic_id: str = Field(..., description="Clinic ID", example="CLIN-01")
    patient_id: int = Field(..., description="Patient ID", example=1001)
    visit_type_id: int = Field(..., description="Visit type ID", example=5)
    visit_mode: str = Field(..., description="Visit mode", example="in_person")
    status: str = Field(..., description="Booking status", example="scheduled")
    booked_at: datetime = Field(..., description="Booked timestamp", example="2026-01-02T10:00:00")
    slot_start_datetime: Optional[datetime] = Field(None, description="Start of appointment slot (if joined)", example="2026-01-15T13:00:00")
    slot_end_datetime: Optional[datetime] = Field(None, description="End of appointment slot (if joined)", example="2026-01-15T13:30:00")


class BookingsListResponse(BaseModel):
    bookings: List[BookingListItemModel] = Field(..., description="List of bookings", example=[])


class BookingSlotUpdateRequest(BaseModel):
    new_appointment_slot_id: str = Field(..., description="Target appointment slot ID", example="SLOT-20260110-1000-1")
    new_provider_id: Optional[str] = Field(None, description="Override provider_id (normally matches new slot)", example="PROV-2201")
    new_clinic_id: Optional[str] = Field(None, description="Override clinic_id (normally matches new slot)", example="CLIN-01")


class BookingSlotUpdateResponse(BaseModel):
    id: str = Field(..., description="Booking ID", example="BK-10293")
    appointment_slot_id: str = Field(..., description="Updated appointment slot ID", example="SLOT-20260110-1000-1")
    provider_id: str = Field(..., description="Updated provider ID", example="PROV-2201")
    clinic_id: str = Field(..., description="Updated clinic ID", example="CLIN-01")
    updated_at: datetime = Field(..., description="Timestamp after update", example="2026-01-03T10:05:00")


class CheckInCreateRequest(BaseModel):
    booking_id: str = Field(..., description="Booking ID to check in", example="BK-8891")
    arrival_time: str = Field(..., description="Recorded arrival time (ISO8601)", example="2026-01-05T09:07:00")
    room_assignment: Optional[str] = Field(None, description="Optional room or bay assignment", example="Exam Room 3")


class CheckInModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Check-in ID", example=601)
    booking_id: str = Field(..., description="Booking ID", example="BK-8891")
    arrival_time: datetime = Field(..., description="Arrival timestamp", example="2026-01-05T09:07:00")
    room_assignment: Optional[str] = Field(None, description="Assigned room", example="Exam Room 3")
    wait_time_seconds: Optional[int] = Field(None, description="Calculated wait time from slot start", example=420)
    created_at: datetime = Field(..., description="Check-in creation time", example="2026-01-05T09:07:05")
    updated_at: datetime = Field(..., description="Check-in update time", example="2026-01-05T09:07:05")


class CheckInBookingPart(BaseModel):
    id: str = Field(..., description="Booking ID", example="BK-8891")
    status: str = Field(..., description="Updated booking status", example="checked_in")
    updated_at: datetime = Field(..., description="Booking update time", example="2026-01-05T09:07:05")


class CheckInCreateResponse(BaseModel):
    check_in: CheckInModel = Field(..., description="Created check-in", example={})
    booking: CheckInBookingPart = Field(..., description="Updated booking", example={})


class VisitNoteCreateRequest(BaseModel):
    id: str = Field(..., description="Visit note ID (e.g. VN-5507-A)", example="VN-5507-A")
    booking_id: str = Field(..., description="Booking ID associated with this note", example="BK-5507")
    note_type: str = Field(..., description="Note type identifier", example="standard_progress_note")
    locked_flag: int = Field(..., description="1 if note is locked, 0 if editable", example=1)
    metadata_json: Optional[str] = Field(None, description="JSON string containing metadata such as author, version, or templates", example='{"author":"Dr. Smith","version":1}')


class VisitNoteModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Visit note ID", example="VN-5507-A")
    booking_id: str = Field(..., description="Associated booking ID", example="BK-5507")
    note_type: str = Field(..., description="Type of note", example="standard_progress_note")
    locked_flag: int = Field(..., description="Locked flag (1 locked, 0 unlocked)", example=1)
    metadata_json: Optional[str] = Field(None, description="JSON metadata string", example='{"author":"Dr. Smith","version":1}')
    created_at: datetime = Field(..., description="Creation timestamp", example="2026-01-05T11:30:00")
    updated_at: datetime = Field(..., description="Update timestamp", example="2026-01-05T11:30:00")


class BillingCodeCreateRequest(BaseModel):
    code: str = Field(..., description="Billing code string", example="99213")
    description: Optional[str] = Field(None, description="Description for the billing code", example="Office/outpatient visit, established patient")


class BillingCodeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str = Field(..., description="Billing code", example="99213")
    description: Optional[str] = Field(None, description="Billing code description", example="Office/outpatient visit, established patient")
    created_at: datetime = Field(..., description="Creation timestamp", example="2026-01-05T11:35:00")
    updated_at: datetime = Field(..., description="Update timestamp", example="2026-01-05T11:35:00")


class DiagnosisTagCreateRequest(BaseModel):
    tag: str = Field(..., description="Diagnosis tag string", example="hypertension")


class DiagnosisTagModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Diagnosis tag ID", example=701)
    tag: str = Field(..., description="Diagnosis tag string", example="hypertension")
    created_at: datetime = Field(..., description="Creation timestamp", example="2026-01-05T11:36:00")
    updated_at: datetime = Field(..., description="Update timestamp", example="2026-01-05T11:36:00")


class VisitNoteBillingCodesAttachRequest(BaseModel):
    billing_codes: List[str] = Field(..., description="Array of billing code strings to attach", example=["99213", "Z00.00"])


class VisitNoteBillingCodeItem(BaseModel):
    code: str = Field(..., description="Billing code", example="99213")


class VisitNoteBillingCodesAttachResponse(BaseModel):
    visit_note_id: str = Field(..., description="Visit note ID", example="VN-5507-A")
    billing_codes: List[VisitNoteBillingCodeItem] = Field(..., description="List of billing codes now attached to the visit note", example=[])


class VisitNoteDiagnosisTagsAttachRequest(BaseModel):
    diagnosis_tag_ids: List[int] = Field(..., description="Array of diagnosis_tag IDs to attach", example=[701, 702])


class VisitNoteDiagnosisTagItem(BaseModel):
    id: int = Field(..., description="Diagnosis tag ID", example=701)


class VisitNoteDiagnosisTagsAttachResponse(BaseModel):
    visit_note_id: str = Field(..., description="Visit note ID", example="VN-5507-A")
    diagnosis_tags: List[VisitNoteDiagnosisTagItem] = Field(..., description="Diagnosis tags now attached to the visit note", example=[])


class EarliestSlotResponseSlot(BaseModel):
    id: str = Field(..., description="Appointment slot ID chosen as earliest available", example="SLOT-20260103-0900-1")
    provider_id: str = Field(..., description="Provider ID for this slot", example="PROV-3100")
    provider_full_name: str = Field(..., description="Provider full name", example="Dr. Jane Smith")
    clinic_id: str = Field(..., description="Clinic ID", example="CLIN-02")
    visit_type_id: Optional[int] = Field(None, description="Visit type ID", example=5)
    visit_type_name: Optional[str] = Field(None, description="Visit type name", example="New Patient Visit")
    visit_mode: str = Field(..., description="Visit mode", example="in_person")
    start_datetime: datetime = Field(..., description="Slot start datetime", example="2026-01-03T09:00:00")
    end_datetime: datetime = Field(..., description="Slot end datetime", example="2026-01-03T09:30:00")
    remaining_capacity: int = Field(..., description="Remaining capacity after booked patients", example=1)


class EarliestSlotResponse(BaseModel):
    slot: Optional[EarliestSlotResponseSlot] = Field(None, description="Earliest available slot", example=None)


class NextSlotForBookingResponseSlot(BaseModel):
    id: str = Field(..., description="Next available slot ID", example="SLOT-20260110-1000-1")
    provider_id: str = Field(..., description="Provider ID (same as original booking)", example="PROV-2201")
    clinic_id: str = Field(..., description="Clinic ID for this slot", example="CLIN-01")
    visit_type_id: Optional[int] = Field(None, description="Visit type ID for this slot", example=6)
    visit_mode: str = Field(..., description="Visit mode for this slot", example="telehealth")
    start_datetime: datetime = Field(..., description="Start datetime", example="2026-01-10T10:00:00")
    end_datetime: datetime = Field(..., description="End datetime", example="2026-01-10T10:15:00")
    remaining_capacity: int = Field(..., description="Remaining capacity", example=1)


class NextSlotForBookingResponse(BaseModel):
    slot: Optional[NextSlotForBookingResponseSlot] = Field(None, description="Next available slot for booking", example=None)


class ConflictingBookingItem(BaseModel):
    id: str = Field(..., description="Conflicting booking ID", example="BK-16001")
    appointment_slot_id: str = Field(..., description="Slot ID that overlaps time off", example="SLOT-20260115-1330-1")
    slot_start_datetime: datetime = Field(..., description="Slot start datetime", example="2026-01-15T13:30:00")
    slot_end_datetime: datetime = Field(..., description="Slot end datetime", example="2026-01-15T14:00:00")
    status: str = Field(..., description="Booking status", example="confirmed")


class ConflictingBookingsResponse(BaseModel):
    bookings: List[ConflictingBookingItem] = Field(..., description="Conflicting bookings", example=[])


class DailyRosterGenerateRequest(BaseModel):
    clinic_id: str = Field(..., description="Clinic ID to generate roster for", example="CLIN-01")
    roster_date: str = Field(..., description="Date for the roster (YYYY-MM-DD)", example="2026-01-20")


class DailyRosterSummaryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Daily roster summary ID", example=801)
    clinic_id: str = Field(..., description="Clinic ID", example="CLIN-01")
    roster_date: date = Field(..., description="Date of roster", example="2026-01-20")
    summary_json: str = Field(..., description="JSON string containing structured roster summary", example='{"providers":[]}')
    generated_at: datetime = Field(..., description="When the roster was generated", example="2026-01-19T18:00:00")
    generated_by_user_id: Optional[int] = Field(None, description="User who generated roster (1)", example=1)


class DailyRosterGetProviderSlotBookingCounts(BaseModel):
    scheduled: int = Field(..., description="Number of scheduled bookings", example=1)
    confirmed: int = Field(..., description="Number of confirmed bookings", example=0)
    checked_in: int = Field(..., description="Number of checked_in bookings", example=0)
    completed: int = Field(..., description="Number of completed bookings", example=0)
    no_show: int = Field(..., description="Number of no_show bookings", example=0)
    canceled_by_patient: int = Field(..., description="Number of bookings canceled by patient", example=0)
    canceled_by_clinic: int = Field(..., description="Number of bookings canceled by clinic", example=0)


class DailyRosterGetProviderSlot(BaseModel):
    slot_id: str = Field(..., description="Appointment slot ID", example="SLOT-20260120-0900-1")
    start_datetime: datetime = Field(..., description="Slot start datetime", example="2026-01-20T09:00:00")
    end_datetime: datetime = Field(..., description="Slot end datetime", example="2026-01-20T09:30:00")
    capacity_per_slot: int = Field(..., description="Slot capacity", example=2)
    booking_counts: DailyRosterGetProviderSlotBookingCounts = Field(..., description="Booking counts by status", example={})


class DailyRosterGetProvider(BaseModel):
    provider_id: str = Field(..., description="Provider ID", example="PROV-2201")
    provider_full_name: str = Field(..., description="Provider full name", example="Dr. John Smith")
    slots: List[DailyRosterGetProviderSlot] = Field(..., description="Slots for provider", example=[])


class DailyRosterGetResponse(BaseModel):
    clinic_id: str = Field(..., description="Clinic ID", example="CLIN-01")
    roster_date: str = Field(..., description="Date of roster", example="2026-01-20")
    generated_at: datetime = Field(..., description="Generation timestamp", example="2026-01-19T18:00:00")
    providers: List[DailyRosterGetProvider] = Field(..., description="Providers in roster", example=[])


class UtilizationReportGenerateRequest(BaseModel):
    clinic_id: str = Field(..., description="Clinic ID for report", example="CLIN-03")
    start_date: str = Field(..., description="Report start date (YYYY-MM-DD)", example="2026-01-01")
    end_date: str = Field(..., description="Report end date (YYYY-MM-DD, inclusive)", example="2026-01-31")


class UtilizationReportModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Utilization report ID", example=901)
    clinic_id: str = Field(..., description="Clinic ID", example="CLIN-03")
    start_date: date = Field(..., description="Start date", example="2026-01-01")
    end_date: date = Field(..., description="End date", example="2026-01-31")
    report_json: str = Field(..., description="JSON string with utilization metrics per provider", example='{"providers":[]}')
    generated_at: datetime = Field(..., description="Generation timestamp", example="2026-02-01T09:00:00")
    generated_by_user_id: Optional[int] = Field(None, description="User who generated report (1)", example=1)


class UtilizationReportGetProvider(BaseModel):
    provider_id: str = Field(..., description="Provider ID", example="PROV-3100")
    total_available_appointment_slots: int = Field(..., description="Total number of appointment slots", example=80)
    booked_slots: int = Field(..., description="Number of slots having at least one booking", example=70)
    overbooked_slots: int = Field(..., description="Number of slots where bookings exceed base capacity", example=5)
    no_show_count: int = Field(..., description="Total bookings with status no_show", example=3)
    same_day_bookings_count: int = Field(..., description="Bookings with is_same_day_booking=1", example=10)
    average_fill_rate_percentage: float = Field(..., description="Average fill rate across all slots for provider in range", example=87.5)


class UtilizationReportGetResponse(BaseModel):
    clinic_id: str = Field(..., description="Clinic ID", example="CLIN-03")
    start_date: str = Field(..., description="Start date", example="2026-01-01")
    end_date: str = Field(..., description="End date", example="2026-01-31")
    generated_at: datetime = Field(..., description="Existing report generation timestamp", example="2026-02-01T09:00:00")
    providers: List[UtilizationReportGetProvider] = Field(..., description="Utilization per provider", example=[])


@app.get(
    "/api/clinics",
    summary="List clinics with optional filters",
    description="Retrieve clinics with optional name and location filters",
    tags=["clinics"],
    operation_id="list_clinics",
    response_model=ClinicsListResponse,
)
async def list_clinics(
    name: Optional[str] = Query(None, description="Exact clinic name filter", example="Downtown Clinic"),
    location: Optional[str] = Query(None, description="Filter clinics by location string", example="Downtown"),
    limit: Optional[int] = Query(50, description="Maximum number of clinics to return", example=50),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> ClinicsListResponse:
    session = SessionLocal()
    query = session.query(Clinic)
    if name is not None:
        query = query.filter(Clinic.name == name)
    if location is not None:
        like_pattern = f"%{location}%"
        query = query.filter(Clinic.location.like(like_pattern))
    clinics = query.offset(offset).limit(limit).all()
    session.close()
    return ClinicsListResponse(clinics=[ClinicModel.model_validate(c) for c in clinics])


@app.get(
    "/api/specialties",
    summary="List specialties with filters",
    description="Retrieve specialties with optional name filter",
    tags=["specialties"],
    operation_id="list_specialties",
    response_model=SpecialtiesListResponse,
)
async def list_specialties(
    name: Optional[str] = Query(None, description="Exact or partial specialty name search", example="Family Medicine"),
    limit: Optional[int] = Query(50, description="Maximum number of specialties to return", example=50),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> SpecialtiesListResponse:
    session = SessionLocal()
    query = session.query(Specialty)
    if name is not None:
        like_pattern = f"%{name}%"
        query = query.filter(Specialty.name.like(like_pattern))
    specialties = query.offset(offset).limit(limit).all()
    session.close()
    return SpecialtiesListResponse(specialties=[SpecialtyModel.model_validate(s) for s in specialties])


@app.post(
    "/api/specialties",
    summary="Create a new specialty",
    description="Create a new specialty record if not existing",
    tags=["specialties"],
    operation_id="create_specialty",
    response_model=SpecialtyCreateResponse,
)
async def create_specialty(
    payload: SpecialtyCreateRequest = Body(..., description="Specialty create payload"),
) -> SpecialtyCreateResponse:
    session = SessionLocal()
    existing = session.query(Specialty).filter(Specialty.name == payload.name).first()
    if existing is None:
        now = datetime.utcnow()
        specialty = Specialty(name=payload.name, created_at=now, updated_at=now)
        session.add(specialty)
        session.commit()
        session.refresh(specialty)
    else:
        specialty = existing
    session.close()
    return SpecialtyCreateResponse.model_validate(specialty)


@app.post(
    "/api/providers",
    summary="Create a new provider profile",
    description="Create a provider with profile fields",
    tags=["providers"],
    operation_id="create_provider",
    response_model=ProviderModel,
)
async def create_provider(
    payload: ProviderCreateRequest = Body(..., description="Provider create payload"),
) -> ProviderModel:
    session = SessionLocal()
    provider_id = payload.id
    if provider_id is None:
        count = session.query(func.count(Provider.id)).scalar() or 0
        provider_id = f"PROV-{count + 1:04d}"
    now = datetime.utcnow()
    provider = Provider(
        id=provider_id,
        full_name=payload.full_name,
        specialty_id=payload.specialty_id,
        primary_clinic_id=payload.primary_clinic_id,
        active_flag=payload.active_flag if payload.active_flag is not None else 1,
        created_at=now,
        updated_at=now,
    )
    session.add(provider)
    session.commit()
    session.refresh(provider)
    session.close()
    return ProviderModel.model_validate(provider)


@app.get(
    "/api/providers",
    summary="List providers with optional filters",
    description="Retrieve providers filtered by various fields",
    tags=["providers"],
    operation_id="list_providers",
    response_model=ProvidersListResponse,
)
async def list_providers(
    specialty_id: Optional[int] = Query(None, description="Filter providers by specialty_id", example=1),
    specialty_name: Optional[str] = Query(None, description="Filter providers by specialty name", example="Family Medicine"),
    clinic_id: Optional[str] = Query(None, description="Filter by primary_clinic_id", example="CLIN-01"),
    active_flag: Optional[int] = Query(None, description="Filter by active_flag", example=1),
    full_name: Optional[str] = Query(None, description="Exact or partial match on full_name", example="Nguyen"),
    limit: Optional[int] = Query(50, description="Maximum number of providers to return", example=50),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> ProvidersListResponse:
    session = SessionLocal()
    query = session.query(Provider, Specialty.name.label("specialty_name")).join(Specialty, Provider.specialty_id == Specialty.id)
    if specialty_id is not None:
        query = query.filter(Provider.specialty_id == specialty_id)
    if specialty_name is not None:
        like_pattern = f"%{specialty_name}%"
        query = query.filter(Specialty.name.like(like_pattern))
    if clinic_id is not None:
        query = query.filter(Provider.primary_clinic_id == clinic_id)
    if active_flag is not None:
        query = query.filter(Provider.active_flag == active_flag)
    if full_name is not None:
        like_pattern_name = f"%{full_name}%"
        query = query.filter(Provider.full_name.like(like_pattern_name))
    rows = query.offset(offset).limit(limit).all()
    providers_list: List[ProvidersListItemModel] = []
    for provider, spec_name in rows:
        item = ProvidersListItemModel(
            id=provider.id,
            full_name=provider.full_name,
            specialty_id=provider.specialty_id,
            specialty_name=spec_name,
            primary_clinic_id=provider.primary_clinic_id,
            active_flag=provider.active_flag,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )
        providers_list.append(item)
    session.close()
    return ProvidersListResponse(providers=providers_list)


@app.post(
    "/api/providers/{provider_id}/weekly-schedules",
    summary="Create provider weekly schedule rule",
    description="Create a recurring weekly schedule row",
    tags=["provider_weekly_schedules"],
    operation_id="create_weekly_schedule",
    response_model=WeeklyScheduleModel,
)
async def create_weekly_schedule(
    provider_id: str = Path(..., description="Provider ID to attach this weekly schedule to", example="PROV-4401"),
    payload: WeeklyScheduleCreateRequest = Body(..., description="Weekly schedule create payload"),
) -> WeeklyScheduleModel:
    session = SessionLocal()
    now = datetime.utcnow()
    ws = ProviderWeeklySchedule(
        provider_id=provider_id,
        clinic_id=payload.clinic_id,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
        lunch_start_time=payload.lunch_start_time,
        lunch_end_time=payload.lunch_end_time,
        slot_duration_minutes=payload.slot_duration_minutes,
        capacity_per_slot=payload.capacity_per_slot,
        visit_mode=payload.visit_mode,
        created_at=now,
        updated_at=now,
    )
    session.add(ws)
    session.commit()
    session.refresh(ws)
    session.close()
    return WeeklyScheduleModel.model_validate(ws)


@app.get(
    "/api/providers/{provider_id}/weekly-schedules",
    summary="List weekly schedules for a provider",
    description="Retrieve weekly schedule definitions for a provider",
    tags=["provider_weekly_schedules"],
    operation_id="list_weekly_schedules",
    response_model=WeeklySchedulesListResponse,
)
async def list_weekly_schedules(
    provider_id: str = Path(..., description="Provider ID whose weekly schedules are requested", example="PROV-4401"),
    clinic_id: Optional[str] = Query(None, description="Filter by clinic_id", example="CLIN-01"),
    day_of_week: Optional[int] = Query(None, description="Filter by day_of_week (0=Mon..6=Sun)", example=0),
) -> WeeklySchedulesListResponse:
    session = SessionLocal()
    query = session.query(ProviderWeeklySchedule).filter(ProviderWeeklySchedule.provider_id == provider_id)
    if clinic_id is not None:
        query = query.filter(ProviderWeeklySchedule.clinic_id == clinic_id)
    if day_of_week is not None:
        query = query.filter(ProviderWeeklySchedule.day_of_week == day_of_week)
    rows = query.all()
    session.close()
    return WeeklySchedulesListResponse(weekly_schedules=[WeeklyScheduleModel.model_validate(ws) for ws in rows])


@app.get(
    "/api/visit-types",
    summary="List visit types",
    description="Retrieve visit types with optional filters",
    tags=["visit_types"],
    operation_id="list_visit_types",
    response_model=VisitTypesListResponse,
)
async def list_visit_types(
    name: Optional[str] = Query(None, description="Exact or partial visit type name", example="New Patient Visit"),
    visit_mode: Optional[str] = Query(None, description="Filter by visit_mode (in_person, telehealth, either)", example="in_person"),
    limit: Optional[int] = Query(50, description="Maximum number of visit types to return", example=50),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> VisitTypesListResponse:
    session = SessionLocal()
    query = session.query(VisitType)
    if name is not None:
        like_pattern = f"%{name}%"
        query = query.filter(VisitType.name.like(like_pattern))
    if visit_mode is not None:
        query = query.filter(VisitType.visit_mode == visit_mode)
    rows = query.offset(offset).limit(limit).all()
    session.close()
    return VisitTypesListResponse(visit_types=[VisitTypeModel.model_validate(v) for v in rows])


@app.post(
    "/api/visit-types",
    summary="Create a new visit type",
    description="Create a visit type with duration and mode",
    tags=["visit_types"],
    operation_id="create_visit_type",
    response_model=VisitTypeCreateResponse,
)
async def create_visit_type(
    payload: VisitTypeCreateRequest = Body(..., description="Visit type create payload"),
) -> VisitTypeCreateResponse:
    session = SessionLocal()
    existing = session.query(VisitType).filter(VisitType.name == payload.name).first()
    if existing is None:
        now = datetime.utcnow()
        vt = VisitType(
            name=payload.name,
            default_duration_minutes=payload.default_duration_minutes,
            visit_mode=payload.visit_mode,
            created_at=now,
            updated_at=now,
        )
        session.add(vt)
        session.commit()
        session.refresh(vt)
    else:
        vt = existing
    session.close()
    return VisitTypeCreateResponse.model_validate(vt)


@app.post(
    "/api/providers/{provider_id}/visit-types",
    summary="Associate a visit type with provider",
    description="Activate a visit type for a provider",
    tags=["provider_visit_types"],
    operation_id="create_provider_visit_type",
    response_model=ProviderVisitTypeModel,
)
async def create_provider_visit_type(
    provider_id: str = Path(..., description="Provider ID", example="PROV-4401"),
    payload: ProviderVisitTypeCreateRequest = Body(..., description="Provider visit type create payload"),
) -> ProviderVisitTypeModel:
    session = SessionLocal()
    now = datetime.utcnow()
    mapping = session.query(ProviderVisitType).filter(
        ProviderVisitType.provider_id == provider_id,
        ProviderVisitType.visit_type_id == payload.visit_type_id,
    ).first()
    if mapping is None:
        mapping = ProviderVisitType(
            provider_id=provider_id,
            visit_type_id=payload.visit_type_id,
            active_flag=payload.active_flag if payload.active_flag is not None else 1,
            created_at=now,
            updated_at=now,
        )
        session.add(mapping)
        session.commit()
        session.refresh(mapping)
    else:
        if payload.active_flag is not None:
            mapping.active_flag = payload.active_flag
            mapping.updated_at = now
            session.commit()
            session.refresh(mapping)
    vt = session.query(VisitType).filter(VisitType.id == mapping.visit_type_id).first()
    vt_name = vt.name if vt is not None else None
    result = ProviderVisitTypeModel(
        id=mapping.id,
        provider_id=mapping.provider_id,
        visit_type_id=mapping.visit_type_id,
        visit_type_name=vt_name,
        active_flag=mapping.active_flag,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )
    session.close()
    return result


@app.get(
    "/api/providers/{provider_id}/visit-types",
    summary="List visit types for a provider",
    description="Retrieve visit types that a provider can perform",
    tags=["provider_visit_types"],
    operation_id="list_provider_visit_types",
    response_model=ProviderVisitTypesListResponse,
)
async def list_provider_visit_types(
    provider_id: str = Path(..., description="Provider ID", example="PROV-4401"),
    only_active: Optional[bool] = Query(False, description="If true, only return rows with active_flag=1", example=True),
) -> ProviderVisitTypesListResponse:
    session = SessionLocal()
    query = session.query(ProviderVisitType, VisitType.name.label("visit_type_name")).join(
        VisitType, ProviderVisitType.visit_type_id == VisitType.id
    ).filter(ProviderVisitType.provider_id == provider_id)
    if only_active:
        query = query.filter(ProviderVisitType.active_flag == 1)
    rows = query.all()
    items: List[ProviderVisitTypeModel] = []
    for mapping, vt_name in rows:
        item = ProviderVisitTypeModel(
            id=mapping.id,
            provider_id=mapping.provider_id,
            visit_type_id=mapping.visit_type_id,
            visit_type_name=vt_name,
            active_flag=mapping.active_flag,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
        )
        items.append(item)
    session.close()
    return ProviderVisitTypesListResponse(provider_visit_types=items)


@app.post(
    "/api/time-off-blocks",
    summary="Create a provider time-off block",
    description="Add a time_off_block for a provider at a clinic",
    tags=["time_off_blocks"],
    operation_id="create_time_off_block",
    response_model=TimeOffBlockModel,
)
async def create_time_off_block(
    payload: TimeOffBlockCreateRequest = Body(..., description="Time off block create payload"),
) -> TimeOffBlockModel:
    session = SessionLocal()
    now = datetime.utcnow()
    block = TimeOffBlock(
        provider_id=payload.provider_id,
        clinic_id=payload.clinic_id,
        start_datetime=datetime.fromisoformat(payload.start_datetime),
        end_datetime=datetime.fromisoformat(payload.end_datetime),
        reason=payload.reason,
        created_by_user_id=1,
        created_at=now,
        updated_at=now,
    )
    session.add(block)
    session.commit()
    session.refresh(block)
    session.close()
    return TimeOffBlockModel.model_validate(block)


@app.get(
    "/api/time-off-blocks",
    summary="List time-off blocks",
    description="Retrieve provider time_off_blocks with filters",
    tags=["time_off_blocks"],
    operation_id="list_time_off_blocks",
    response_model=TimeOffBlocksListResponse,
)
async def list_time_off_blocks(
    provider_id: Optional[str] = Query(None, description="Filter by provider_id", example="PROV-2201"),
    clinic_id: Optional[str] = Query(None, description="Filter by clinic_id", example="CLIN-02"),
    start_from: Optional[str] = Query(None, description="Include blocks ending after this datetime", example="2026-01-01T00:00:00"),
    end_until: Optional[str] = Query(None, description="Include blocks starting before this datetime", example="2026-01-31T23:59:59"),
) -> TimeOffBlocksListResponse:
    session = SessionLocal()
    query = session.query(TimeOffBlock)
    if provider_id is not None:
        query = query.filter(TimeOffBlock.provider_id == provider_id)
    if clinic_id is not None:
        query = query.filter(TimeOffBlock.clinic_id == clinic_id)
    if start_from is not None:
        dt_start = datetime.fromisoformat(start_from)
        query = query.filter(TimeOffBlock.end_datetime >= dt_start)
    if end_until is not None:
        dt_end = datetime.fromisoformat(end_until)
        query = query.filter(TimeOffBlock.start_datetime <= dt_end)
    blocks = query.all()
    session.close()
    return TimeOffBlocksListResponse(time_off_blocks=[TimeOffBlockModel.model_validate(b) for b in blocks])


@app.post(
    "/api/patients",
    summary="Create a new patient",
    description="Create a new patient record",
    tags=["patients"],
    operation_id="create_patient",
    response_model=PatientModel,
)
async def create_patient(
    payload: PatientCreateRequest = Body(..., description="Patient create payload"),
) -> PatientModel:
    session = SessionLocal()
    now = datetime.utcnow()
    patient = Patient(
        full_name=payload.full_name,
        date_of_birth=datetime.fromisoformat(payload.date_of_birth).date(),
        preferred_communication_channel=payload.preferred_communication_channel,
        primary_insurance=payload.primary_insurance,
        created_at=now,
        updated_at=now,
    )
    session.add(patient)
    session.commit()
    session.refresh(patient)
    session.close()
    return PatientModel.model_validate(patient)


@app.get(
    "/api/patients",
    summary="Search patients by name and DOB",
    description="Retrieve patients by full_name and/or date_of_birth",
    tags=["patients"],
    operation_id="search_patients",
    response_model=PatientsListResponse,
)
async def search_patients(
    full_name: Optional[str] = Query(None, description="Exact or partial full name filter", example="John Doe"),
    date_of_birth: Optional[str] = Query(None, description="DOB filter in YYYY-MM-DD", example="1985-04-12"),
    limit: Optional[int] = Query(25, description="Maximum number of patients to return", example=25),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> PatientsListResponse:
    session = SessionLocal()
    query = session.query(Patient)
    if full_name is not None:
        like_pattern = f"%{full_name}%"
        query = query.filter(Patient.full_name.like(like_pattern))
    if date_of_birth is not None:
        dob = datetime.fromisoformat(date_of_birth).date()
        query = query.filter(Patient.date_of_birth == dob)
    rows = query.offset(offset).limit(limit).all()
    session.close()
    return PatientsListResponse(patients=[PatientModel.model_validate(p) for p in rows])


@app.post(
    "/api/appointment-slots",
    summary="Create a single appointment slot",
    description="Create one appointment_slots row",
    tags=["appointment_slots"],
    operation_id="create_appointment_slot",
    response_model=AppointmentSlotModel,
)
async def create_appointment_slot(
    payload: AppointmentSlotCreateRequest = Body(..., description="Appointment slot create payload"),
) -> AppointmentSlotModel:
    session = SessionLocal()
    slot_id = payload.id
    if slot_id is None:
        count = session.query(func.count(AppointmentSlot.id)).scalar() or 0
        slot_id = f"SLOT-{count + 1}"
    now = datetime.utcnow()
    slot = AppointmentSlot(
        id=slot_id,
        provider_id=payload.provider_id,
        clinic_id=payload.clinic_id,
        visit_type_id=payload.visit_type_id,
        visit_mode=payload.visit_mode,
        start_datetime=datetime.fromisoformat(payload.start_datetime),
        end_datetime=datetime.fromisoformat(payload.end_datetime),
        capacity_per_slot=payload.capacity_per_slot,
        base_capacity_per_slot=payload.base_capacity_per_slot,
        is_overbook_capable=payload.is_overbook_capable if payload.is_overbook_capable is not None else 0,
        created_by_user_id=1,
        created_at=now,
        updated_at=now,
    )
    session.add(slot)
    session.commit()
    session.refresh(slot)
    session.close()
    return AppointmentSlotModel.model_validate(slot)


@app.patch(
    "/api/appointment-slots/{slot_id}",
    summary="Update appointment slot",
    description="Partially update an appointment slot",
    tags=["appointment_slots"],
    operation_id="update_appointment_slot",
    response_model=AppointmentSlotModel,
)
async def update_appointment_slot(
    slot_id: str = Path(..., description="Appointment slot ID to update", example="SLOT-20260203-0800-1"),
    payload: AppointmentSlotUpdateRequest = Body(..., description="Appointment slot update payload"),
) -> AppointmentSlotModel:
    session = SessionLocal()
    slot = session.query(AppointmentSlot).filter(AppointmentSlot.id == slot_id).first()
    now = datetime.utcnow()
    if payload.capacity_per_slot is not None:
        slot.capacity_per_slot = payload.capacity_per_slot
    if payload.is_overbook_capable is not None:
        slot.is_overbook_capable = payload.is_overbook_capable
    if payload.visit_type_id is not None:
        slot.visit_type_id = payload.visit_type_id
    slot.updated_at = now
    session.commit()
    session.refresh(slot)
    session.close()
    return AppointmentSlotModel.model_validate(slot)


@app.get(
    "/api/appointment-slots",
    summary="List appointment slots with availability",
    description="Retrieve appointment_slots with filters and capacity info",
    tags=["appointment_slots"],
    operation_id="list_appointment_slots",
    response_model=AppointmentSlotsListResponse,
)
async def list_appointment_slots(
    provider_id: Optional[str] = Query(None, description="Filter by provider_id", example="PROV-2201"),
    clinic_id: Optional[str] = Query(None, description="Filter by clinic_id", example="CLIN-01"),
    visit_type_id: Optional[int] = Query(None, description="Filter by visit_type_id", example=5),
    visit_mode: Optional[str] = Query(None, description="Filter by visit_mode", example="in_person"),
    start_from: Optional[str] = Query(None, description="Only slots starting at or after this datetime", example="2026-01-01T00:00:00"),
    end_until: Optional[str] = Query(None, description="Only slots starting at or before this datetime", example="2026-01-07T23:59:59"),
    only_with_capacity: Optional[bool] = Query(False, description="If true, only slots where remaining capacity>0", example=True),
    limit: Optional[int] = Query(100, description="Maximum number of slots to return", example=100),
    offset: Optional[int] = Query(0, description="Pagination offset", example=0),
) -> AppointmentSlotsListResponse:
    session = SessionLocal()
    query = session.query(AppointmentSlot)
    if provider_id is not None:
        query = query.filter(AppointmentSlot.provider_id == provider_id)
    if clinic_id is not None:
        query = query.filter(AppointmentSlot.clinic_id == clinic_id)
    if visit_type_id is not None:
        query = query.filter(AppointmentSlot.visit_type_id == visit_type_id)
    if visit_mode is not None:
        query = query.filter(AppointmentSlot.visit_mode == visit_mode)
    if start_from is not None:
        dt_start = datetime.fromisoformat(start_from)
        query = query.filter(AppointmentSlot.start_datetime >= dt_start)
    if end_until is not None:
        dt_end = datetime.fromisoformat(end_until)
        query = query.filter(AppointmentSlot.start_datetime <= dt_end)
    slots = query.offset(offset).limit(limit).all()
    result_slots: List[AppointmentSlotWithAvailabilityModel] = []
    for slot in slots:
        bookings_query = session.query(Booking).filter(
            Booking.appointment_slot_id == slot.id,
            Booking.status.notin_(["canceled_by_patient", "canceled_by_clinic"]),
        )
        bookings_count = bookings_query.count()
        remaining_capacity = slot.capacity_per_slot - bookings_count
        if only_with_capacity and remaining_capacity <= 0:
            continue
        item = AppointmentSlotWithAvailabilityModel(
            id=slot.id,
            provider_id=slot.provider_id,
            clinic_id=slot.clinic_id,
            visit_type_id=slot.visit_type_id,
            visit_mode=slot.visit_mode,
            start_datetime=slot.start_datetime,
            end_datetime=slot.end_datetime,
            capacity_per_slot=slot.capacity_per_slot,
            base_capacity_per_slot=slot.base_capacity_per_slot,
            is_overbook_capable=slot.is_overbook_capable,
            current_bookings_count=bookings_count,
            remaining_capacity=remaining_capacity,
            created_by_user_id=slot.created_by_user_id,
            created_at=slot.created_at,
            updated_at=slot.updated_at,
        )
        result_slots.append(item)
    session.close()
    return AppointmentSlotsListResponse(appointment_slots=result_slots)


@app.post(
    "/api/bookings",
    summary="Create a booking on a slot",
    description="Create a bookings row for a patient on a slot",
    tags=["bookings"],
    operation_id="create_booking",
    response_model=BookingModel,
)
async def create_booking(
    payload: BookingCreateRequest = Body(..., description="Booking create payload"),
) -> BookingModel:
    session = SessionLocal()
    booking_id = payload.id
    if booking_id is None:
        count = session.query(func.count(Booking.id)).scalar() or 0
        booking_id = f"BK-{count + 1}"
    now = datetime.utcnow()
    booking = Booking(
        id=booking_id,
        appointment_slot_id=payload.appointment_slot_id,
        provider_id=payload.provider_id,
        clinic_id=payload.clinic_id,
        patient_id=payload.patient_id,
        visit_type_id=payload.visit_type_id,
        visit_mode=payload.visit_mode,
        status=payload.status,
        insurance_at_booking=payload.insurance_at_booking,
        communication_channel_at_booking=payload.communication_channel_at_booking,
        is_same_day_booking=payload.is_same_day_booking if payload.is_same_day_booking is not None else 0,
        booked_at=now,
        created_by_user_id=1,
        created_at=now,
        updated_at=now,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    session.close()
    return BookingModel.model_validate(booking)


@app.get(
    "/api/bookings/{booking_id}",
    summary="Get booking details by ID",
    description="Retrieve a booking by ID with status fields",
    tags=["bookings"],
    operation_id="get_booking",
    response_model=BookingModel,
)
async def get_booking(
    booking_id: str = Path(..., description="Booking ID to retrieve", example="BK-10293"),
) -> BookingModel:
    session = SessionLocal()
    booking = session.query(Booking).filter(Booking.id == booking_id).first()
    session.close()
    return BookingModel.model_validate(booking)


@app.patch(
    "/api/bookings/{booking_id}/status",
    summary="Update booking status",
    description="Change status for a booking and add history",
    tags=["bookings", "booking_status_history"],
    operation_id="update_booking_status",
    response_model=BookingStatusUpdateResponse,
)
async def update_booking_status(
    booking_id: str = Path(..., description="Booking ID whose status is changing", example="BK-10293"),
    payload: BookingStatusUpdateRequest = Body(..., description="Status update payload"),
) -> BookingStatusUpdateResponse:
    session = SessionLocal()
    booking = session.query(Booking).filter(Booking.id == booking_id).first()
    old_status_val = booking.status
    now = datetime.utcnow()
    booking.status = payload.new_status
    booking.updated_at = now
    history = BookingStatusHistory(
        booking_id=booking.id,
        old_status=old_status_val,
        new_status=payload.new_status,
        changed_at=now,
        changed_by_user_id=1,
        reason=payload.reason,
    )
    session.add(history)
    session.commit()
    session.refresh(booking)
    session.refresh(history)
    booking_part = BookingStatusUpdateBookingPart(id=booking.id, status=booking.status, updated_at=booking.updated_at)
    history_part = BookingStatusHistoryEntryModel.model_validate(history)
    session.close()
    return BookingStatusUpdateResponse(booking=booking_part, status_history_entry=history_part)


@app.get(
    "/api/bookings",
    summary="List bookings with filters",
    description="Retrieve bookings filtered by provider, clinic, patient, etc.",
    tags=["bookings"],
    operation_id="list_bookings",
    response_model=BookingsListResponse,
)
async def list_bookings(
    provider_id: Optional[str] = Query(None, description="Filter bookings by provider_id", example="PROV-2201"),
    clinic_id: Optional[str] = Query(None, description="Filter by clinic_id", example="CLIN-01"),
    patient_id: Optional[int] = Query(None, description="Filter by patient_id", example=1001),
    status: Optional[str] = Query(None, description="Filter by booking status", example="scheduled"),
    appointment_start_from: Optional[str] = Query(None, description="Slots starting on/after this datetime", example="2026-01-15T00:00:00"),
    appointment_start_until: Optional[str] = Query(None, description="Slots starting on/before this datetime", example="2026-01-15T23:59:59"),
    include_slot_details: Optional[bool] = Query(False, description="If true, join appointment_slots to include time info", example=True),
    limit: Optional[int] = Query(200, description="Max number of bookings to return", example=200),
    offset: Optional[int] = Query(0, description="Pagination offset", example=0),
) -> BookingsListResponse:
    session = SessionLocal()
    if include_slot_details:
        query = session.query(
            Booking,
            AppointmentSlot.start_datetime.label("slot_start"),
            AppointmentSlot.end_datetime.label("slot_end"),
        ).join(AppointmentSlot, Booking.appointment_slot_id == AppointmentSlot.id)
    else:
        query = session.query(Booking, func.null().label("slot_start"), func.null().label("slot_end"))
    if provider_id is not None:
        query = query.filter(Booking.provider_id == provider_id)
    if clinic_id is not None:
        query = query.filter(Booking.clinic_id == clinic_id)
    if patient_id is not None:
        query = query.filter(Booking.patient_id == patient_id)
    if status is not None:
        query = query.filter(Booking.status == status)
    if appointment_start_from is not None:
        dt_start = datetime.fromisoformat(appointment_start_from)
        if include_slot_details:
            query = query.filter(AppointmentSlot.start_datetime >= dt_start)
    if appointment_start_until is not None:
        dt_end = datetime.fromisoformat(appointment_start_until)
        if include_slot_details:
            query = query.filter(AppointmentSlot.start_datetime <= dt_end)
    rows = query.offset(offset).limit(limit).all()
    items: List[BookingListItemModel] = []
    for booking, slot_start, slot_end in rows:
        item = BookingListItemModel(
            id=booking.id,
            appointment_slot_id=booking.appointment_slot_id,
            provider_id=booking.provider_id,
            clinic_id=booking.clinic_id,
            patient_id=booking.patient_id,
            visit_type_id=booking.visit_type_id,
            visit_mode=booking.visit_mode,
            status=booking.status,
            booked_at=booking.booked_at,
            slot_start_datetime=slot_start if include_slot_details else None,
            slot_end_datetime=slot_end if include_slot_details else None,
        )
        items.append(item)
    session.close()
    return BookingsListResponse(bookings=items)


@app.patch(
    "/api/bookings/{booking_id}/appointment-slot",
    summary="Change booking appointment slot",
    description="Update booking.appointment_slot_id and related fields",
    tags=["bookings"],
    operation_id="update_booking_slot",
    response_model=BookingSlotUpdateResponse,
)
async def update_booking_slot(
    booking_id: str = Path(..., description="Booking ID to move", example="BK-10293"),
    payload: BookingSlotUpdateRequest = Body(..., description="Booking slot update payload"),
) -> BookingSlotUpdateResponse:
    session = SessionLocal()
    booking = session.query(Booking).filter(Booking.id == booking_id).first()
    booking.appointment_slot_id = payload.new_appointment_slot_id
    if payload.new_provider_id is not None:
        booking.provider_id = payload.new_provider_id
    if payload.new_clinic_id is not None:
        booking.clinic_id = payload.new_clinic_id
    booking.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(booking)
    resp = BookingSlotUpdateResponse(
        id=booking.id,
        appointment_slot_id=booking.appointment_slot_id,
        provider_id=booking.provider_id,
        clinic_id=booking.clinic_id,
        updated_at=booking.updated_at,
    )
    session.close()
    return resp


@app.post(
    "/api/check-ins",
    summary="Record a check-in for a booking",
    description="Create a check_in row and update booking status",
    tags=["check_ins", "bookings"],
    operation_id="create_check_in_for_booking",
    response_model=CheckInCreateResponse,
)
async def create_check_in_for_booking(
    payload: CheckInCreateRequest = Body(..., description="Check-in create payload"),
) -> CheckInCreateResponse:
    session = SessionLocal()
    booking = session.query(Booking).filter(Booking.id == payload.booking_id).first()
    slot = session.query(AppointmentSlot).filter(AppointmentSlot.id == booking.appointment_slot_id).first()
    arrival_dt = datetime.fromisoformat(payload.arrival_time)
    wait_seconds_val = int((arrival_dt - slot.start_datetime).total_seconds())
    now = datetime.utcnow()
    check_in = CheckIn(
        booking_id=booking.id,
        arrival_time=arrival_dt,
        room_assignment=payload.room_assignment,
        wait_time_seconds=wait_seconds_val,
        created_at=now,
        updated_at=now,
    )
    session.add(check_in)
    booking.status = "checked_in"
    booking.updated_at = now
    session.commit()
    session.refresh(check_in)
    session.refresh(booking)
    check_in_part = CheckInModel.model_validate(check_in)
    booking_part = CheckInBookingPart(id=booking.id, status=booking.status, updated_at=booking.updated_at)
    session.close()
    return CheckInCreateResponse(check_in=check_in_part, booking=booking_part)


@app.post(
    "/api/visit-notes",
    summary="Create visit notes metadata",
    description="Create a visit_notes row for a booking",
    tags=["visit_notes"],
    operation_id="create_visit_note",
    response_model=VisitNoteModel,
)
async def create_visit_note(
    payload: VisitNoteCreateRequest = Body(..., description="Visit note create payload"),
) -> VisitNoteModel:
    session = SessionLocal()
    now = datetime.utcnow()
    vn = VisitNote(
        id=payload.id,
        booking_id=payload.booking_id,
        note_type=payload.note_type,
        locked_flag=payload.locked_flag,
        metadata_json=payload.metadata_json,
        created_at=now,
        updated_at=now,
    )
    session.add(vn)
    session.commit()
    session.refresh(vn)
    session.close()
    return VisitNoteModel.model_validate(vn)


@app.post(
    "/api/billing-codes",
    summary="Ensure or create a billing code",
    description="Create a billing_codes row if not existing",
    tags=["billing_codes"],
    operation_id="create_billing_code",
    response_model=BillingCodeModel,
)
async def create_billing_code(
    payload: BillingCodeCreateRequest = Body(..., description="Billing code create payload"),
) -> BillingCodeModel:
    session = SessionLocal()
    bc = session.query(BillingCode).filter(BillingCode.code == payload.code).first()
    now = datetime.utcnow()
    if bc is None:
        bc = BillingCode(
            code=payload.code,
            description=payload.description,
            created_at=now,
            updated_at=now,
        )
        session.add(bc)
        session.commit()
        session.refresh(bc)
    else:
        if payload.description is not None:
            bc.description = payload.description
            bc.updated_at = now
            session.commit()
            session.refresh(bc)
    session.close()
    return BillingCodeModel.model_validate(bc)


@app.post(
    "/api/diagnosis-tags",
    summary="Ensure or create a diagnosis tag",
    description="Create a diagnosis_tags row if not existing",
    tags=["diagnosis_tags"],
    operation_id="create_diagnosis_tag",
    response_model=DiagnosisTagModel,
)
async def create_diagnosis_tag(
    payload: DiagnosisTagCreateRequest = Body(..., description="Diagnosis tag create payload"),
) -> DiagnosisTagModel:
    session = SessionLocal()
    dt_row = session.query(DiagnosisTag).filter(DiagnosisTag.tag == payload.tag).first()
    now = datetime.utcnow()
    if dt_row is None:
        dt_row = DiagnosisTag(
            tag=payload.tag,
            created_at=now,
            updated_at=now,
        )
        session.add(dt_row)
        session.commit()
        session.refresh(dt_row)
    session.close()
    return DiagnosisTagModel.model_validate(dt_row)


@app.post(
    "/api/visit-notes/{visit_note_id}/billing-codes",
    summary="Attach billing codes to a visit note",
    description="Create visit_note_billing_codes rows for given codes",
    tags=["visit_note_billing_codes"],
    operation_id="attach_billing_codes_to_visit_note",
    response_model=VisitNoteBillingCodesAttachResponse,
)
async def attach_billing_codes_to_visit_note(
    visit_note_id: str = Path(..., description="Visit note ID", example="VN-5507-A"),
    payload: VisitNoteBillingCodesAttachRequest = Body(..., description="Billing codes attach payload"),
) -> VisitNoteBillingCodesAttachResponse:
    session = SessionLocal()
    for code_str in payload.billing_codes:
        existing = session.query(VisitNoteBillingCode).filter(
            VisitNoteBillingCode.visit_note_id == visit_note_id,
            VisitNoteBillingCode.billing_code == code_str,
        ).first()
        if existing is None:
            vnbc = VisitNoteBillingCode(visit_note_id=visit_note_id, billing_code=code_str)
            session.add(vnbc)
    session.commit()
    rows = session.query(VisitNoteBillingCode).filter(VisitNoteBillingCode.visit_note_id == visit_note_id).all()
    codes_items = [VisitNoteBillingCodeItem(code=r.billing_code) for r in rows]
    session.close()
    return VisitNoteBillingCodesAttachResponse(visit_note_id=visit_note_id, billing_codes=codes_items)


@app.post(
    "/api/visit-notes/{visit_note_id}/diagnosis-tags",
    summary="Attach diagnosis tags to a visit note",
    description="Create visit_note_diagnosis_tags rows for given tag IDs",
    tags=["visit_note_diagnosis_tags"],
    operation_id="attach_diagnosis_tags_to_visit_note",
    response_model=VisitNoteDiagnosisTagsAttachResponse,
)
async def attach_diagnosis_tags_to_visit_note(
    visit_note_id: str = Path(..., description="Visit note ID", example="VN-5507-A"),
    payload: VisitNoteDiagnosisTagsAttachRequest = Body(..., description="Diagnosis tags attach payload"),
) -> VisitNoteDiagnosisTagsAttachResponse:
    session = SessionLocal()
    for tag_id in payload.diagnosis_tag_ids:
        existing = session.query(VisitNoteDiagnosisTag).filter(
            VisitNoteDiagnosisTag.visit_note_id == visit_note_id,
            VisitNoteDiagnosisTag.diagnosis_tag_id == tag_id,
        ).first()
        if existing is None:
            vndt = VisitNoteDiagnosisTag(visit_note_id=visit_note_id, diagnosis_tag_id=tag_id)
            session.add(vndt)
    session.commit()
    rows = session.query(VisitNoteDiagnosisTag).filter(VisitNoteDiagnosisTag.visit_note_id == visit_note_id).all()
    items = [VisitNoteDiagnosisTagItem(id=r.diagnosis_tag_id) for r in rows]
    session.close()
    return VisitNoteDiagnosisTagsAttachResponse(visit_note_id=visit_note_id, diagnosis_tags=items)


@app.get(
    "/api/scheduling/earliest-available-slot",
    summary="Find earliest available slot",
    description="Search slots to find earliest available with capacity",
    tags=["scheduling"],
    operation_id="find_earliest_available_slot",
    response_model=EarliestSlotResponse,
)
async def find_earliest_available_slot(
    clinic_id: Optional[str] = Query(None, description="Restrict search to a specific clinic_id", example="CLIN-01"),
    specialty_name: Optional[str] = Query(None, description="Filter providers by specialty name", example="Family Medicine"),
    visit_type_name: Optional[str] = Query(None, description="Filter slots by visit type name", example="New Patient Visit"),
    visit_mode: str = Query(..., description="Required visit_mode: in_person or telehealth", example="in_person"),
    start_from: str = Query(..., description="Earliest allowed slot start (ISO8601)", example="2026-01-01T00:00:00"),
    end_until: str = Query(..., description="Latest allowed slot start (ISO8601)", example="2026-01-08T00:00:00"),
) -> EarliestSlotResponse:
    session = SessionLocal()
    query = session.query(
        AppointmentSlot,
        Provider.full_name.label("provider_full_name"),
        VisitType.name.label("visit_type_name"),
    ).join(Provider, AppointmentSlot.provider_id == Provider.id).outerjoin(
        VisitType, AppointmentSlot.visit_type_id == VisitType.id
    )
    query = query.filter(AppointmentSlot.visit_mode == visit_mode)
    dt_start = datetime.fromisoformat(start_from)
    dt_end = datetime.fromisoformat(end_until)
    query = query.filter(AppointmentSlot.start_datetime >= dt_start, AppointmentSlot.start_datetime <= dt_end)
    if clinic_id is not None:
        query = query.filter(AppointmentSlot.clinic_id == clinic_id)
    if specialty_name is not None:
        spec_sub = session.query(Specialty.id).filter(Specialty.name == specialty_name).subquery()
        query = query.filter(Provider.specialty_id.in_(spec_sub))
    if visit_type_name is not None:
        vt_sub = session.query(VisitType.id).filter(VisitType.name == visit_type_name).subquery()
        query = query.filter(AppointmentSlot.visit_type_id.in_(vt_sub))
    query = query.order_by(AppointmentSlot.start_datetime.asc())
    rows = query.all()
    chosen_slot: Optional[EarliestSlotResponseSlot] = None
    for slot, provider_full_name, vt_name in rows:
        bookings_count = session.query(Booking).filter(
            Booking.appointment_slot_id == slot.id,
            Booking.status.notin_(["canceled_by_patient", "canceled_by_clinic"]),
        ).count()
        remaining_capacity = slot.capacity_per_slot - bookings_count
        if remaining_capacity > 0:
            chosen_slot = EarliestSlotResponseSlot(
                id=slot.id,
                provider_id=slot.provider_id,
                provider_full_name=provider_full_name,
                clinic_id=slot.clinic_id,
                visit_type_id=slot.visit_type_id,
                visit_type_name=vt_name,
                visit_mode=slot.visit_mode,
                start_datetime=slot.start_datetime,
                end_datetime=slot.end_datetime,
                remaining_capacity=remaining_capacity,
            )
            break
    session.close()
    return EarliestSlotResponse(slot=chosen_slot)


@app.get(
    "/api/scheduling/next-available-slot-for-booking",
    summary="Next available slot for booking",
    description="Find next appointment_slot for the same provider with capacity",
    tags=["scheduling"],
    operation_id="find_next_available_slot_for_booking",
    response_model=NextSlotForBookingResponse,
)
async def find_next_available_slot_for_booking(
    booking_id: str = Query(..., description="Existing booking whose provider is used to search", example="BK-10293"),
    visit_type_name: str = Query(..., description="Visit type name", example="Follow-up Visit"),
    visit_mode: str = Query(..., description="Visit mode required", example="telehealth"),
    start_from: str = Query(..., description="Search window start datetime", example="2026-01-03T00:00:00"),
    end_until: str = Query(..., description="Search window end datetime", example="2026-01-17T23:59:59"),
) -> NextSlotForBookingResponse:
    session = SessionLocal()
    booking = session.query(Booking).filter(Booking.id == booking_id).first()
    vt = session.query(VisitType).filter(VisitType.name == visit_type_name).first()
    vt_id = vt.id if vt is not None else None
    query = session.query(AppointmentSlot).filter(
        AppointmentSlot.provider_id == booking.provider_id,
        AppointmentSlot.visit_mode == visit_mode,
    )
    dt_start = datetime.fromisoformat(start_from)
    dt_end = datetime.fromisoformat(end_until)
    query = query.filter(AppointmentSlot.start_datetime >= dt_start, AppointmentSlot.start_datetime <= dt_end)
    if vt_id is not None:
        query = query.filter(AppointmentSlot.visit_type_id == vt_id)
    query = query.order_by(AppointmentSlot.start_datetime.asc())
    slots = query.all()
    chosen_slot: Optional[NextSlotForBookingResponseSlot] = None
    for slot in slots:
        bookings_count = session.query(Booking).filter(
            Booking.appointment_slot_id == slot.id,
            Booking.status.notin_(["canceled_by_patient", "canceled_by_clinic"]),
        ).count()
        remaining_capacity = slot.capacity_per_slot - bookings_count
        if remaining_capacity > 0:
            chosen_slot = NextSlotForBookingResponseSlot(
                id=slot.id,
                provider_id=slot.provider_id,
                clinic_id=slot.clinic_id,
                visit_type_id=slot.visit_type_id,
                visit_mode=slot.visit_mode,
                start_datetime=slot.start_datetime,
                end_datetime=slot.end_datetime,
                remaining_capacity=remaining_capacity,
            )
            break
    session.close()
    return NextSlotForBookingResponse(slot=chosen_slot)


@app.get(
    "/api/scheduling/conflicting-bookings-for-time-off",
    summary="Find bookings conflicting with time-off",
    description="List bookings whose slots overlap a time-off window",
    tags=["scheduling"],
    operation_id="list_conflicting_bookings_for_time_off",
    response_model=ConflictingBookingsResponse,
)
async def list_conflicting_bookings_for_time_off(
    provider_id: str = Query(..., description="Provider ID", example="PROV-2201"),
    clinic_id: str = Query(..., description="Clinic ID", example="CLIN-02"),
    start_datetime: str = Query(..., description="Start datetime of time-off window", example="2026-01-15T13:00:00"),
    end_datetime: str = Query(..., description="End datetime of time-off window", example="2026-01-15T15:00:00"),
) -> ConflictingBookingsResponse:
    session = SessionLocal()
    dt_start = datetime.fromisoformat(start_datetime)
    dt_end = datetime.fromisoformat(end_datetime)
    query = session.query(
        Booking,
        AppointmentSlot.start_datetime.label("slot_start"),
        AppointmentSlot.end_datetime.label("slot_end"),
    ).join(AppointmentSlot, Booking.appointment_slot_id == AppointmentSlot.id).filter(
        AppointmentSlot.provider_id == provider_id,
        AppointmentSlot.clinic_id == clinic_id,
        AppointmentSlot.start_datetime < dt_end,
        AppointmentSlot.end_datetime > dt_start,
    )
    rows = query.all()
    items: List[ConflictingBookingItem] = []
    for booking, slot_start, slot_end in rows:
        item = ConflictingBookingItem(
            id=booking.id,
            appointment_slot_id=booking.appointment_slot_id,
            slot_start_datetime=slot_start,
            slot_end_datetime=slot_end,
            status=booking.status,
        )
        items.append(item)
    session.close()
    return ConflictingBookingsResponse(bookings=items)


@app.post(
    "/api/rosters/daily",
    summary="Generate and store daily roster",
    description="Compute and upsert daily_roster_summaries for a clinic and date",
    tags=["daily_roster_summaries"],
    operation_id="generate_daily_roster",
    response_model=DailyRosterSummaryModel,
)
async def generate_daily_roster(
    payload: DailyRosterGenerateRequest = Body(..., description="Daily roster generate payload"),
) -> DailyRosterSummaryModel:
    session = SessionLocal()
    roster_date_val = datetime.fromisoformat(payload.roster_date).date()
    day_start = datetime.combine(roster_date_val, datetime.min.time())
    day_end = datetime.combine(roster_date_val, datetime.max.time())
    slots = session.query(AppointmentSlot).filter(
        AppointmentSlot.clinic_id == payload.clinic_id,
        AppointmentSlot.start_datetime >= day_start,
        AppointmentSlot.start_datetime <= day_end,
    ).all()
    providers_map: Dict[str, Dict] = {}
    for slot in slots:
        if slot.provider_id not in providers_map:
            provider = session.query(Provider).filter(Provider.id == slot.provider_id).first()
            providers_map[slot.provider_id] = {
                "provider_id": slot.provider_id,
                "provider_full_name": provider.full_name if provider is not None else "",
                "slots": [],
            }
        booking_counts = {
            "scheduled": 0,
            "confirmed": 0,
            "checked_in": 0,
            "completed": 0,
            "no_show": 0,
            "canceled_by_patient": 0,
            "canceled_by_clinic": 0,
        }
        bookings = session.query(Booking).filter(Booking.appointment_slot_id == slot.id).all()
        for b in bookings:
            if b.status in booking_counts:
                booking_counts[b.status] += 1
        providers_map[slot.provider_id]["slots"].append(
            {
                "slot_id": slot.id,
                "start_datetime": slot.start_datetime.isoformat(),
                "end_datetime": slot.end_datetime.isoformat(),
                "capacity_per_slot": slot.capacity_per_slot,
                "booking_counts": booking_counts,
            }
        )
    summary_dict = {
        "providers": list(providers_map.values()),
    }
    summary_json_str = __import__("json").dumps(summary_dict)
    existing = session.query(DailyRosterSummary).filter(
        DailyRosterSummary.clinic_id == payload.clinic_id,
        DailyRosterSummary.roster_date == roster_date_val,
    ).first()
    now = datetime.utcnow()
    if existing is None:
        roster = DailyRosterSummary(
            clinic_id=payload.clinic_id,
            roster_date=roster_date_val,
            summary_json=summary_json_str,
            generated_at=now,
            generated_by_user_id=1,
        )
        session.add(roster)
        session.commit()
        session.refresh(roster)
    else:
        existing.summary_json = summary_json_str
        existing.generated_at = now
        existing.generated_by_user_id = 1
        session.commit()
        session.refresh(existing)
        roster = existing
    session.close()
    return DailyRosterSummaryModel.model_validate(roster)


@app.get(
    "/api/rosters/daily",
    summary="Get a clinic daily roster summary",
    description="Retrieve roster summary as structured JSON",
    tags=["daily_roster_summaries"],
    operation_id="get_daily_roster",
    response_model=DailyRosterGetResponse,
)
async def get_daily_roster(
    clinic_id: str = Query(..., description="Clinic ID", example="CLIN-01"),
    roster_date: str = Query(..., description="Date for the roster (YYYY-MM-DD)", example="2026-01-20"),
) -> DailyRosterGetResponse:
    session = SessionLocal()
    roster_date_val = datetime.fromisoformat(roster_date).date()
    roster = session.query(DailyRosterSummary).filter(
        DailyRosterSummary.clinic_id == clinic_id,
        DailyRosterSummary.roster_date == roster_date_val,
    ).first()
    session.close()
    if roster is None:
        providers_list: List[DailyRosterGetProvider] = []
        return DailyRosterGetResponse(
            clinic_id=clinic_id,
            roster_date=roster_date,
            generated_at=datetime.utcnow(),
            providers=providers_list,
        )
    data = __import__("json").loads(roster.summary_json)
    providers_raw = data.get("providers", [])
    providers_list: List[DailyRosterGetProvider] = []
    for p in providers_raw:
        slots_raw = p.get("slots", [])
        slots_list: List[DailyRosterGetProviderSlot] = []
        for s in slots_raw:
            bc_raw = s.get("booking_counts", {})
            counts = DailyRosterGetProviderSlotBookingCounts(
                scheduled=bc_raw.get("scheduled", 0),
                confirmed=bc_raw.get("confirmed", 0),
                checked_in=bc_raw.get("checked_in", 0),
                completed=bc_raw.get("completed", 0),
                no_show=bc_raw.get("no_show", 0),
                canceled_by_patient=bc_raw.get("canceled_by_patient", 0),
                canceled_by_clinic=bc_raw.get("canceled_by_clinic", 0),
            )
            slot_item = DailyRosterGetProviderSlot(
                slot_id=s.get("slot_id", ""),
                start_datetime=datetime.fromisoformat(s.get("start_datetime")),
                end_datetime=datetime.fromisoformat(s.get("end_datetime")),
                capacity_per_slot=s.get("capacity_per_slot", 0),
                booking_counts=counts,
            )
            slots_list.append(slot_item)
        provider_item = DailyRosterGetProvider(
            provider_id=p.get("provider_id", ""),
            provider_full_name=p.get("provider_full_name", ""),
            slots=slots_list,
        )
        providers_list.append(provider_item)
    return DailyRosterGetResponse(
        clinic_id=clinic_id,
        roster_date=roster_date,
        generated_at=roster.generated_at,
        providers=providers_list,
    )


@app.post(
    "/api/utilization-reports",
    summary="Generate a clinic utilization report",
    description="Compute utilization_reports for a clinic and date range",
    tags=["utilization_reports"],
    operation_id="generate_utilization_report",
    response_model=UtilizationReportModel,
)
async def generate_utilization_report(
    payload: UtilizationReportGenerateRequest = Body(..., description="Utilization report generate payload"),
) -> UtilizationReportModel:
    session = SessionLocal()
    start_date_val = datetime.fromisoformat(payload.start_date).date()
    end_date_val = datetime.fromisoformat(payload.end_date).date()
    day_start = datetime.combine(start_date_val, datetime.min.time())
    day_end = datetime.combine(end_date_val, datetime.max.time())
    slots = session.query(AppointmentSlot).filter(
        AppointmentSlot.clinic_id == payload.clinic_id,
        AppointmentSlot.start_datetime >= day_start,
        AppointmentSlot.start_datetime <= day_end,
    ).all()
    providers_data: Dict[str, Dict] = {}
    for slot in slots:
        if slot.provider_id not in providers_data:
            providers_data[slot.provider_id] = {
                "total_slots": 0,
                "booked_slots": 0,
                "overbooked_slots": 0,
                "no_show_count": 0,
                "same_day_bookings": 0,
                "total_capacity": 0,
                "total_bookings": 0,
            }
        pdata = providers_data[slot.provider_id]
        pdata["total_slots"] += 1
        pdata["total_capacity"] += slot.capacity_per_slot
        bookings = session.query(Booking).filter(Booking.appointment_slot_id == slot.id).all()
        booking_count = len(bookings)
        if booking_count > 0:
            pdata["booked_slots"] += 1
        no_show_count_slot = 0
        same_day_bookings_slot = 0
        for b in bookings:
            pdata["total_bookings"] += 1
            if b.status == "no_show":
                no_show_count_slot += 1
            if b.is_same_day_booking == 1:
                same_day_bookings_slot += 1
        pdata["no_show_count"] += no_show_count_slot
        pdata["same_day_bookings"] += same_day_bookings_slot
        if booking_count > slot.base_capacity_per_slot:
            pdata["overbooked_slots"] += 1
    providers_list: List[Dict] = []
    for provider_id_val, pdata in providers_data.items():
        if pdata["total_capacity"] > 0:
            fill_rate = (pdata["total_bookings"] / pdata["total_capacity"]) * 100.0
        else:
            fill_rate = 0.0
        providers_list.append(
            {
                "provider_id": provider_id_val,
                "total_slots": pdata["total_slots"],
                "booked_slots": pdata["booked_slots"],
                "overbooked_slots": pdata["overbooked_slots"],
                "no_show_count": pdata["no_show_count"],
                "same_day_bookings": pdata["same_day_bookings"],
                "average_fill_rate": fill_rate,
            }
        )
    report_dict = {
        "providers": providers_list,
    }
    report_json_str = __import__("json").dumps(report_dict)
    now = datetime.utcnow()
    report = UtilizationReport(
        clinic_id=payload.clinic_id,
        start_date=start_date_val,
        end_date=end_date_val,
        report_json=report_json_str,
        generated_at=now,
        generated_by_user_id=1,
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    session.close()
    return UtilizationReportModel.model_validate(report)


@app.get(
    "/api/utilization-reports",
    summary="Get a clinic utilization report",
    description="Retrieve utilization_reports and parse report_json",
    tags=["utilization_reports"],
    operation_id="get_utilization_report",
    response_model=UtilizationReportGetResponse,
)
async def get_utilization_report(
    clinic_id: str = Query(..., description="Clinic ID to load report for", example="CLIN-03"),
    start_date: str = Query(..., description="Report start date (YYYY-MM-DD)", example="2026-01-01"),
    end_date: str = Query(..., description="Report end date (YYYY-MM-DD)", example="2026-01-31"),
) -> UtilizationReportGetResponse:
    session = SessionLocal()
    start_date_val = datetime.fromisoformat(start_date).date()
    end_date_val = datetime.fromisoformat(end_date).date()
    report = session.query(UtilizationReport).filter(
        UtilizationReport.clinic_id == clinic_id,
        UtilizationReport.start_date == start_date_val,
        UtilizationReport.end_date == end_date_val,
    ).first()
    session.close()
    if report is None:
        return UtilizationReportGetResponse(
            clinic_id=clinic_id,
            start_date=start_date,
            end_date=end_date,
            generated_at=datetime.utcnow(),
            providers=[],
        )
    data = __import__("json").loads(report.report_json)
    providers_raw = data.get("providers", [])
    providers_list: List[UtilizationReportGetProvider] = []
    for p in providers_raw:
        providers_list.append(
            UtilizationReportGetProvider(
                provider_id=p.get("provider_id", ""),
                total_available_appointment_slots=p.get("total_slots", 0),
                booked_slots=p.get("booked_slots", 0),
                overbooked_slots=p.get("overbooked_slots", 0),
                no_show_count=p.get("no_show_count", 0),
                same_day_bookings_count=p.get("same_day_bookings", 0),
                average_fill_rate_percentage=p.get("average_fill_rate", 0.0),
            )
        )
    return UtilizationReportGetResponse(
        clinic_id=clinic_id,
        start_date=start_date,
        end_date=end_date,
        generated_at=report.generated_at,
        providers=providers_list,
    )


if __name__ == "__main__":
    import uvicorn, os as _os
    host = _os.getenv("HOST", "127.0.0.1")
    port = int(_os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)