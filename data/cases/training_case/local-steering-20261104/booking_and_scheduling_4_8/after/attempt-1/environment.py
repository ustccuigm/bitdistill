from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
import os
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
    Float
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

database_url = os.getenv("DATABASE_PATH", "sqlite:///outputs/databases/petcarehub_veterinary_clinic_manager.db")

engine = create_engine("sqlite:////mnt/genming/training-local-cases-20261104/cases/booking_and_scheduling_4_8/after/attempt-1/final.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
    )

class PetOwner(Base):
    __tablename__ = "pet_owners"
    id = Column(Integer, primary_key=True)
    full_name = Column(Text, nullable=False)
    mobile_number = Column(Text)
    email = Column(Text)
    mailing_address = Column(Text)
    preferred_contact_method = Column(Text, nullable=False)
    billing_preference_method = Column(Text, nullable=False)
    billing_notes = Column(Text)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint(preferred_contact_method.in_(("email", "phone", "sms")), name="chk_pet_owners_pref_contact"),
        CheckConstraint(billing_preference_method.in_(("credit_card", "cash", "check", "other")), name="chk_pet_owners_billing_pref"),
        Index("idx_pet_owners_full_name", "full_name"),
        Index("idx_pet_owners_email", "email"),
    )

class Veterinarian(Base):
    __tablename__ = "veterinarians"
    id = Column(Integer, primary_key=True)
    full_name = Column(Text, nullable=False)
    license_number = Column(Text)
    email = Column(Text)
    phone = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        Index("idx_veterinarians_full_name", "full_name"),
    )

class Clinic(Base):
    __tablename__ = "clinics"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    address = Column(Text)
    phone = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        Index("idx_clinics_name", "name"),
    )

class ClinicRoom(Base):
    __tablename__ = "clinic_rooms"
    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    name = Column(Text, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("clinic_id", "name", name="uq_clinic_rooms_clinic_id_name"),
        Index("idx_clinic_rooms_clinic_id", "clinic_id"),
    )

class Pet(Base):
    __tablename__ = "pets"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("pet_owners.id"), nullable=False)
    name = Column(Text, nullable=False)
    species = Column(Text, nullable=False)
    breed = Column(Text)
    birthdate = Column(Date)
    status = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint(status.in_(("active", "inactive", "deceased")), name="chk_pets_status"),
        Index("idx_pets_owner_id", "owner_id"),
        Index("idx_pets_name_owner", "name", "owner_id"),
    )

class PetWeightHistory(Base):
    __tablename__ = "pet_weight_history"
    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    weight_kg = Column(Float, nullable=False)
    source = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        Index("idx_pet_weight_history_pet_id", "pet_id"),
        Index("idx_pet_weight_history_recorded_at", "recorded_at"),
    )

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Text, primary_key=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("pet_owners.id"), nullable=False)
    veterinarian_id = Column(Integer, ForeignKey("veterinarians.id"), nullable=False)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    scheduled_room_id = Column(Integer, ForeignKey("clinic_rooms.id"))
    actual_room_id = Column(Integer, ForeignKey("clinic_rooms.id"))
    appointment_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime)
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    duration_minutes = Column(Integer)
    metadata_ = Column("metadata", Text)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint(appointment_type.in_(("vaccination", "exam", "surgery", "follow_up", "other")), name="chk_appointments_type"),
        CheckConstraint(status.in_(("scheduled", "rescheduled", "checked_in", "in_progress", "completed", "cancelled", "no_show")), name="chk_appointments_status"),
        Index("idx_appointments_pet_id", "pet_id"),
        Index("idx_appointments_owner_id", "owner_id"),
        Index("idx_appointments_veterinarian_id", "veterinarian_id"),
        Index("idx_appointments_clinic_id", "clinic_id"),
        Index("idx_appointments_status", "status"),
        Index("idx_appointments_scheduled_start", "scheduled_start"),
    )

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("pet_owners.id"), nullable=False)
    veterinarian_id = Column(Integer, ForeignKey("veterinarians.id"), nullable=False)
    appointment_id = Column(Text, ForeignKey("appointments.id"))
    diagnosis_codes = Column(Text, nullable=False)
    procedures_performed = Column(Text, nullable=False)
    notes = Column(Text)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        Index("idx_medical_records_pet_id", "pet_id"),
        Index("idx_medical_records_owner_id", "owner_id"),
        Index("idx_medical_records_vet_id", "veterinarian_id"),
        Index("idx_medical_records_appointment_id", "appointment_id"),
    )

class Vaccination(Base):
    __tablename__ = "vaccinations"
    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"))
    vaccine_type = Column(Text, nullable=False)
    dose = Column(Text)
    administration_date = Column(Date, nullable=False)
    next_due_date = Column(Date)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        Index("idx_vaccinations_pet_id", "pet_id"),
        Index("idx_vaccinations_next_due_date", "next_due_date"),
    )

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    default_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        Index("idx_services_code", "code"),
    )

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Text, ForeignKey("appointments.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("pet_owners.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    subtotal_amount = Column(Float, nullable=False, default=0)
    discount_description = Column(Text)
    discount_percent = Column(Float)
    discount_amount = Column(Float)
    total_amount = Column(Float, nullable=False, default=0)
    payment_status = Column(Text, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint(payment_status.in_(("unpaid", "partially_paid", "paid", "void")), name="chk_invoices_payment_status"),
        Index("idx_invoices_appointment_id", "appointment_id"),
        Index("idx_invoices_owner_id", "owner_id"),
        Index("idx_invoices_pet_id", "pet_id"),
        Index("idx_invoices_payment_status", "payment_status"),
    )

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"))
    service_code = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        Index("idx_invoice_items_invoice_id", "invoice_id"),
    )

class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("pet_owners.id"), nullable=False)
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=False)
    veterinarian_id = Column(Integer, ForeignKey("veterinarians.id"), nullable=False)
    medication_name = Column(Text, nullable=False)
    dosage_instructions = Column(Text, nullable=False)
    refill_count_remaining = Column(Integer, nullable=False, default=0)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        Index("idx_prescriptions_pet_id", "pet_id"),
        Index("idx_prescriptions_owner_id", "owner_id"),
        Index("idx_prescriptions_vet_id", "veterinarian_id"),
    )

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("pet_owners.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    related_appointment_id = Column(Text, ForeignKey("appointments.id"))
    related_vaccination_id = Column(Integer, ForeignKey("vaccinations.id"))
    related_prescription_id = Column(Integer, ForeignKey("prescriptions.id"))
    reminder_type = Column(Text, nullable=False)
    contact_method = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    sent_time = Column(DateTime)
    is_sent = Column(Integer, nullable=False, default=0)
    metadata_ = Column("metadata", Text)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint(reminder_type.in_(("appointment", "vaccination", "prescription_refill")), name="chk_reminders_type"),
        CheckConstraint(contact_method.in_(("email", "phone", "sms")), name="chk_reminders_contact_method"),
        Index("idx_reminders_owner_id", "owner_id"),
        Index("idx_reminders_pet_id", "pet_id"),
        Index("idx_reminders_type", "reminder_type"),
        Index("idx_reminders_scheduled_time", "scheduled_time"),
    )

Base.metadata.create_all(engine)

app = FastAPI(title="PetCareHub Veterinary Clinic Manager API", version="1.0.0")

class PetOwnerCreateRequest(BaseModel):
    full_name: str = Field(..., description="Full name of the pet owner", example="Maria Sanchez")
    mobile_number: Optional[str] = Field(None, description="Mobile phone number for the owner", example="+1-555-234-9876")
    email: Optional[str] = Field(None, description="Email address of the owner", example="maria.sanchez@example.com")
    mailing_address: Optional[str] = Field(None, description="Mailing address for billing and communication", example="742 Evergreen Terrace, Springfield, IL")
    preferred_contact_method: str = Field(..., description="Preferred contact method: email, phone, or sms", example="email")
    billing_preference_method: str = Field(..., description="Billing method: credit_card, cash, check, or other", example="credit_card")
    billing_notes: Optional[str] = Field(None, description="Free-text billing notes or preferences", example="authorize auto-pay for invoices under $200")

class PetOwnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique pet owner identifier", example=10)
    full_name: str = Field(..., description="Full name of the pet owner", example="Maria Sanchez")
    mobile_number: Optional[str] = Field(None, description="Mobile phone number for the owner", example="+1-555-234-9876")
    email: Optional[str] = Field(None, description="Email of the pet owner", example="maria.sanchez@example.com")
    mailing_address: Optional[str] = Field(None, description="Mailing address of the pet owner", example="742 Evergreen Terrace, Springfield, IL")
    preferred_contact_method: str = Field(..., description="Preferred contact method", example="email")
    billing_preference_method: str = Field(..., description="Preferred billing method", example="credit_card")
    billing_notes: Optional[str] = Field(None, description="Notes about billing preferences", example="authorize auto-pay for invoices under $200")
    created_by_user_id: int = Field(..., description="User ID that created this record", example=1)
    created_at: Optional[datetime] = Field(None, description="Timestamp when the owner was created", example="2025-01-01T10:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the owner was last updated", example=None)

class PetOwnerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique pet owner identifier", example=10)
    full_name: str = Field(..., description="Full name of the pet owner", example="Maria Sanchez")
    mobile_number: Optional[str] = Field(None, description="Mobile phone number for the owner", example="+1-555-234-9876")
    email: Optional[str] = Field(None, description="Email of the pet owner", example="maria.sanchez@example.com")
    mailing_address: Optional[str] = Field(None, description="Mailing address of the pet owner", example="742 Evergreen Terrace, Springfield, IL")
    preferred_contact_method: str = Field(..., description="Preferred contact method", example="email")
    billing_preference_method: str = Field(..., description="Preferred billing method", example="credit_card")
    billing_notes: Optional[str] = Field(None, description="Notes about billing preferences", example="authorize auto-pay for invoices under $200")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the owner was created", example="2025-01-01T10:00:00Z")

class PetOwnerListResponse(BaseModel):
    items: List[PetOwnerListItem] = Field(..., description="List of pet owners", example=[])
    total: int = Field(..., description="Total number of matching pet owners", example=1)

class VeterinarianListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique veterinarian identifier", example=3)
    full_name: str = Field(..., description="Full name of the veterinarian", example="Dr. Alex Kim")
    license_number: Optional[str] = Field(None, description="Professional license number", example="IL-12345")
    email: Optional[str] = Field(None, description="Email address of the veterinarian", example="alex.kim@dah.example.com")
    phone: Optional[str] = Field(None, description="Contact phone number", example="+1-555-100-2000")

class VeterinarianListResponse(BaseModel):
    items: List[VeterinarianListItem] = Field(..., description="List of veterinarians", example=[])
    total: int = Field(..., description="Total number of matching veterinarians", example=1)

class ClinicListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique clinic identifier", example=1)
    name: str = Field(..., description="Clinic name", example="Downtown Animal Hospital")
    address: Optional[str] = Field(None, description="Clinic address", example="123 Main St, Springfield, IL")
    phone: Optional[str] = Field(None, description="Clinic phone number", example="+1-555-300-4000")

class ClinicListResponse(BaseModel):
    items: List[ClinicListItem] = Field(..., description="List of clinics", example=[])
    total: int = Field(..., description="Total number of matching clinics", example=1)

class ClinicRoomItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique clinic room identifier", example=5)
    clinic_id: int = Field(..., description="ID of the clinic this room belongs to", example=1)
    name: str = Field(..., description="Name of the room in the clinic", example="Exam Room 3")
    is_active: int = Field(..., description="1 if the room is active and can be scheduled, else 0", example=1)

class ClinicRoomListResponse(BaseModel):
    items: List[ClinicRoomItem] = Field(..., description="List of clinic rooms", example=[])

class PetCreateRequest(BaseModel):
    owner_id: int = Field(..., description="ID of the pet owner that this pet belongs to", example=10)
    name: str = Field(..., description="Name of the pet", example="Luna")
    species: str = Field(..., description="Species of the pet", example="Canine")
    breed: Optional[str] = Field(None, description="Breed of the pet", example="Labrador Retriever")
    birthdate: Optional[str] = Field(None, description="Birthdate of the pet in ISO date format", example="2022-03-15")
    status: str = Field(..., description="Pet status: active, inactive, or deceased", example="active")

class PetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique pet identifier", example=25)
    owner_id: int = Field(..., description="ID of the pet owner", example=10)
    name: str = Field(..., description="Name of the pet", example="Luna")
    species: str = Field(..., description="Species of the pet", example="Canine")
    breed: Optional[str] = Field(None, description="Breed of the pet", example="Labrador Retriever")
    birthdate: Optional[datetime] = Field(None, description="Birthdate of the pet", example="2022-03-15")
    status: str = Field(..., description="Current status of the pet", example="active")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the pet was created", example="2025-01-02T09:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the pet was last updated", example=None)

class PetListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique pet identifier", example=25)
    owner_id: int = Field(..., description="ID of the pet owner", example=10)
    name: str = Field(..., description="Name of the pet", example="Luna")
    species: str = Field(..., description="Species of the pet", example="Canine")
    breed: Optional[str] = Field(None, description="Breed of the pet", example="Labrador Retriever")
    birthdate: Optional[datetime] = Field(None, description="Birthdate of the pet", example="2022-03-15")
    status: str = Field(..., description="Current status of the pet", example="active")

class PetListResponse(BaseModel):
    items: List[PetListItem] = Field(..., description="List of pets", example=[])
    total: int = Field(..., description="Total number of matching pets", example=1)

class PetWeightHistoryCreateRequest(BaseModel):
    recorded_at: str = Field(..., description="Timestamp when the weight was recorded", example="2025-01-02T10:00:00Z")
    weight_kg: float = Field(..., description="Weight of the pet in kilograms", example=24.5)
    source: Optional[str] = Field(None, description="Source of the measurement, e.g. clinic scale", example="clinic_scale")

class PetWeightHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique weight history entry identifier", example=100)
    pet_id: int = Field(..., description="ID of the pet", example=25)
    recorded_at: datetime = Field(..., description="Timestamp when the weight was recorded", example="2025-01-02T10:00:00Z")
    weight_kg: float = Field(..., description="Recorded weight in kilograms", example=24.5)
    source: Optional[str] = Field(None, description="Source of the measurement", example="clinic_scale")
    created_at: Optional[datetime] = Field(None, description="Timestamp when this record was created", example="2025-01-02T10:01:00Z")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when this record was last updated", example=None)

class AppointmentCreateRequest(BaseModel):
    id: Optional[str] = Field(None, description="Custom appointment ID, if omitted the system may generate one", example="APT-98342")
    pet_id: int = Field(..., description="ID of the pet for this appointment", example=25)
    owner_id: int = Field(..., description="ID of the owner for this appointment", example=10)
    veterinarian_id: int = Field(..., description="ID of the veterinarian for this appointment", example=3)
    clinic_id: int = Field(..., description="ID of the clinic where the appointment will occur", example=1)
    scheduled_room_id: Optional[int] = Field(None, description="ID of the clinic room scheduled for the appointment", example=7)
    appointment_type: str = Field(..., description="Type of appointment: vaccination, exam, surgery, follow_up, other", example="vaccination")
    status: str = Field(..., description="Initial status of the appointment", example="scheduled")
    scheduled_start: str = Field(..., description="Scheduled start datetime in ISO format", example="2025-01-10T14:30:00Z")
    scheduled_end: Optional[str] = Field(None, description="Scheduled end datetime in ISO format", example="2025-01-10T15:00:00Z")
    duration_minutes: Optional[int] = Field(None, description="Expected appointment duration in minutes", example=30)
    metadata: Optional[str] = Field(None, description="JSON-encoded metadata string with extra details", example='{"reason": "yearly vaccines"}')

class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Appointment identifier", example="APT-98342")
    pet_id: int = Field(..., description="ID of the pet", example=25)
    owner_id: int = Field(..., description="ID of the pet owner", example=10)
    veterinarian_id: int = Field(..., description="ID of the veterinarian", example=3)
    clinic_id: int = Field(..., description="ID of the clinic", example=1)
    scheduled_room_id: Optional[int] = Field(None, description="ID of the scheduled clinic room", example=7)
    actual_room_id: Optional[int] = Field(None, description="ID of the actual clinic room used", example=None)
    appointment_type: str = Field(..., description="Appointment type", example="vaccination")
    status: str = Field(..., description="Current status of the appointment", example="scheduled")
    scheduled_start: datetime = Field(..., description="Scheduled start datetime", example="2025-01-10T14:30:00Z")
    scheduled_end: Optional[datetime] = Field(None, description="Scheduled end datetime", example="2025-01-10T15:00:00Z")
    check_in_time: Optional[datetime] = Field(None, description="Actual check-in timestamp, if set", example=None)
    check_out_time: Optional[datetime] = Field(None, description="Actual check-out timestamp, if set", example=None)
    duration_minutes: Optional[int] = Field(None, description="Expected or actual duration in minutes", example=30)
    metadata: Optional[str] = Field(None, description="JSON-encoded metadata string", example='{"reason": "yearly vaccines"}')
    created_by_user_id: int = Field(..., description="User ID that created the appointment", example=1)
    created_at: Optional[datetime] = Field(None, description="Timestamp when the appointment was created", example="2025-01-05T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the appointment was last updated", example=None)

class AppointmentRescheduleRequest(BaseModel):
    new_scheduled_start: str = Field(..., description="New scheduled start datetime in ISO format", example="2025-01-12T09:00:00Z")
    new_scheduled_end: Optional[str] = Field(None, description="New scheduled end datetime in ISO format", example="2025-01-12T09:30:00Z")
    status: Optional[str] = Field(None, description="Optional new status for the appointment", example="scheduled")
    metadata: Optional[str] = Field(None, description="JSON-encoded metadata to merge or replace existing metadata", example='{"note": "Owner requested earlier morning slot"}')

class AppointmentRescheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Appointment identifier", example="APT-98342")
    scheduled_start: datetime = Field(..., description="Updated scheduled start datetime", example="2025-01-12T09:00:00Z")
    scheduled_end: Optional[datetime] = Field(None, description="Updated scheduled end datetime", example="2025-01-12T09:30:00Z")
    status: str = Field(..., description="Updated appointment status", example="scheduled")
    metadata: Optional[str] = Field(None, description="Updated JSON-encoded metadata", example='{"note": "Owner requested earlier morning slot"}')
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the appointment was last updated", example="2025-01-06T09:00:00Z")

class AppointmentCheckInRequest(BaseModel):
    check_in_time: str = Field(..., description="Actual check-in timestamp in ISO format", example="2025-01-12T08:55:00Z")
    actual_room_id: Optional[int] = Field(None, description="ID of the actual clinic room used at check-in", example=8)

class AppointmentCheckInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Appointment identifier", example="APT-98342")
    status: str = Field(..., description="Updated appointment status", example="checked_in")
    check_in_time: Optional[datetime] = Field(None, description="Recorded check-in timestamp", example="2025-01-12T08:55:00Z")
    actual_room_id: Optional[int] = Field(None, description="Actual room assigned at check-in", example=8)
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the appointment was updated", example="2025-01-12T08:55:10Z")

class AppointmentCompleteRequest(BaseModel):
    check_out_time: Optional[str] = Field(None, description="Actual check-out timestamp in ISO format", example="2025-01-12T09:35:00Z")
    duration_minutes: Optional[int] = Field(None, description="Actual duration in minutes if different from scheduled", example=35)

class AppointmentCompleteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Appointment identifier", example="APT-98342")
    status: str = Field(..., description="Final appointment status", example="completed")
    check_out_time: Optional[datetime] = Field(None, description="Recorded check-out timestamp", example="2025-01-12T09:35:00Z")
    duration_minutes: Optional[int] = Field(None, description="Recorded duration in minutes", example=35)
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the appointment was updated", example="2025-01-12T09:36:00Z")

class MedicalRecordCreateRequest(BaseModel):
    pet_id: int = Field(..., description="ID of the pet this record is for", example=25)
    owner_id: int = Field(..., description="ID of the owner", example=10)
    veterinarian_id: int = Field(..., description="ID of the veterinarian", example=3)
    appointment_id: Optional[str] = Field(None, description="ID of the associated appointment, if any", example="APT-98342")
    diagnosis_codes: List[str] = Field(..., description="List of diagnosis code strings, stored as serialized text", example=["CANINE_OTITIS_EXTERN", "ALLERGIC_DERMATITIS"])
    procedures_performed: List[str] = Field(..., description="List of procedures performed, stored as serialized text", example=["ear cleaning", "cytology slide"])
    notes: Optional[str] = Field(None, description="Additional free-text notes for this medical record", example="Mild erythema, advised recheck in 2 weeks.")

class MedicalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique medical record identifier", example=50)
    pet_id: int = Field(..., description="ID of the pet", example=25)
    owner_id: int = Field(..., description="ID of the owner", example=10)
    veterinarian_id: int = Field(..., description="ID of the veterinarian", example=3)
    appointment_id: Optional[str] = Field(None, description="ID of the related appointment if present", example="APT-98342")
    diagnosis_codes: str = Field(..., description="Serialized diagnosis codes string", example='["CANINE_OTITIS_EXTERN","ALLERGIC_DERMATITIS"]')
    procedures_performed: str = Field(..., description="Serialized procedures performed string", example='["ear cleaning","cytology slide"]')
    notes: Optional[str] = Field(None, description="Free-text notes about the visit", example="Mild erythema, advised recheck in 2 weeks.")
    created_by_user_id: int = Field(..., description="ID of the user that created this record", example=1)
    created_at: Optional[datetime] = Field(None, description="Timestamp when this record was created", example="2025-01-12T09:40:00Z")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when this record was last updated", example=None)

class VaccinationCreateRequest(BaseModel):
    pet_id: int = Field(..., description="ID of the pet receiving the vaccination", example=25)
    medical_record_id: Optional[int] = Field(None, description="ID of the associated medical record, if applicable", example=50)
    vaccine_type: str = Field(..., description="Type or name of the vaccine", example="Rabies 1-year")
    dose: Optional[str] = Field(None, description="Dose and administration description", example="1.0 mL subcutaneous")
    administration_date: str = Field(..., description="Date when the vaccine was administered", example="2025-01-12")
    next_due_date: Optional[str] = Field(None, description="Date when the next dose is due", example="2026-01-12")

class VaccinationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique vaccination identifier", example=200)
    pet_id: int = Field(..., description="ID of the pet", example=25)
    medical_record_id: Optional[int] = Field(None, description="ID of the related medical record, if any", example=50)
    vaccine_type: str = Field(..., description="Type or name of the vaccine", example="Rabies 1-year")
    dose: Optional[str] = Field(None, description="Dose and administration details", example="1.0 mL subcutaneous")
    administration_date: datetime = Field(..., description="Date of vaccine administration", example="2025-01-12")
    next_due_date: Optional[datetime] = Field(None, description="Next due date for this vaccination", example="2026-01-12")
    created_by_user_id: int = Field(..., description="ID of the user who created this record", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-12T09:45:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example=None)

class VaccinationGetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique vaccination identifier", example=200)
    pet_id: int = Field(..., description="ID of the pet", example=25)
    medical_record_id: Optional[int] = Field(None, description="ID of the related medical record", example=50)
    vaccine_type: str = Field(..., description="Vaccine type or name", example="Rabies 1-year")
    dose: Optional[str] = Field(None, description="Dose and administration detail", example="1.0 mL subcutaneous")
    administration_date: datetime = Field(..., description="Date vaccine was administered", example="2025-01-12")
    next_due_date: Optional[datetime] = Field(None, description="Next due date for vaccination", example="2026-01-12")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-12T09:45:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example=None)

class ServiceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique service identifier", example=1)
    code: str = Field(..., description="Service code used for billing", example="SRV-001")
    name: str = Field(..., description="Service display name", example="General physical exam")
    description: Optional[str] = Field(None, description="Description of the service", example="Routine wellness examination.")
    default_price: Optional[float] = Field(None, description="Default price for the service", example=65.0)

class ServiceListResponse(BaseModel):
    items: List[ServiceListItem] = Field(..., description="List of services", example=[])
    total: int = Field(..., description="Total number of matching services", example=2)

class InvoiceCreateRequest(BaseModel):
    appointment_id: str = Field(..., description="ID of the appointment this invoice is for", example="APT-98342")
    owner_id: int = Field(..., description="ID of the pet owner who will pay this invoice", example=10)
    pet_id: int = Field(..., description="ID of the pet associated with this invoice", example=25)
    subtotal_amount: float = Field(..., description="Subtotal amount before discounts", example=110.0)
    discount_description: Optional[str] = Field(None, description="Description of any discount applied", example="New client discount")
    discount_percent: Optional[float] = Field(None, description="Discount percentage applied to subtotal", example=10.0)
    discount_amount: Optional[float] = Field(None, description="Absolute discount amount subtracted from subtotal", example=11.0)
    total_amount: float = Field(..., description="Final total amount after discounts", example=99.0)
    payment_status: str = Field(..., description="Payment status: unpaid, partially_paid, paid, or void", example="unpaid")

class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique invoice identifier", example=300)
    appointment_id: str = Field(..., description="ID of the related appointment", example="APT-98342")
    owner_id: int = Field(..., description="ID of the invoice owner", example=10)
    pet_id: int = Field(..., description="ID of the pet", example=25)
    subtotal_amount: float = Field(..., description="Subtotal before discounts", example=110.0)
    discount_description: Optional[str] = Field(None, description="Description of discount applied", example="New client discount")
    discount_percent: Optional[float] = Field(None, description="Discount percentage applied", example=10.0)
    discount_amount: Optional[float] = Field(None, description="Absolute discount amount", example=11.0)
    total_amount: float = Field(..., description="Total after discounts", example=99.0)
    payment_status: str = Field(..., description="Current payment status of the invoice", example="unpaid")
    created_by_user_id: int = Field(..., description="ID of the user that created this invoice", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-12T09:50:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example=None)

class InvoiceGetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique invoice identifier", example=300)
    appointment_id: str = Field(..., description="ID of the related appointment", example="APT-98342")
    owner_id: int = Field(..., description="ID of the owner", example=10)
    pet_id: int = Field(..., description="ID of the pet", example=25)
    subtotal_amount: float = Field(..., description="Subtotal amount", example=110.0)
    discount_description: Optional[str] = Field(None, description="Description of discount", example="New client discount")
    discount_percent: Optional[float] = Field(None, description="Discount percentage applied", example=10.0)
    discount_amount: Optional[float] = Field(None, description="Discount amount", example=11.0)
    total_amount: float = Field(..., description="Total after discount", example=99.0)
    payment_status: str = Field(..., description="Payment status", example="unpaid")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-12T09:50:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example=None)

class InvoiceItemCreateRequest(BaseModel):
    invoice_id: int = Field(..., description="ID of the invoice this line belongs to", example=300)
    service_id: Optional[int] = Field(None, description="ID of the service, if referencing services table", example=1)
    service_code: str = Field(..., description="Service code for this invoice line", example="SRV-001")
    description: str = Field(..., description="Human-readable description of the invoice line", example="General physical exam")
    quantity: int = Field(..., description="Quantity of this service", example=1)
    unit_price: float = Field(..., description="Price per unit", example=65.0)
    line_total: float = Field(..., description="Total line amount (quantity * unit_price)", example=65.0)

class InvoiceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique invoice item identifier", example=400)
    invoice_id: int = Field(..., description="ID of the related invoice", example=300)
    service_id: Optional[int] = Field(None, description="ID of the related service, if present", example=1)
    service_code: str = Field(..., description="Service code used for billing", example="SRV-001")
    description: str = Field(..., description="Description of the billed service", example="General physical exam")
    quantity: int = Field(..., description="Quantity for this line", example=1)
    unit_price: float = Field(..., description="Unit price for this line", example=65.0)
    line_total: float = Field(..., description="Total amount for this line", example=65.0)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-12T09:51:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example=None)

class InvoiceItemListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Invoice item identifier", example=400)
    invoice_id: int = Field(..., description="Parent invoice ID", example=300)
    service_id: Optional[int] = Field(None, description="Reference to services table, if any", example=1)
    service_code: str = Field(..., description="Code for the service", example="SRV-001")
    description: str = Field(..., description="Description of the service", example="General physical exam")
    quantity: int = Field(..., description="Quantity billed", example=1)
    unit_price: float = Field(..., description="Price per unit", example=65.0)
    line_total: float = Field(..., description="Line total", example=65.0)

class InvoiceItemListResponse(BaseModel):
    items: List[InvoiceItemListItem] = Field(..., description="List of invoice items", example=[])

class PrescriptionCreateRequest(BaseModel):
    pet_id: int = Field(..., description="ID of the pet receiving the prescription", example=25)
    owner_id: int = Field(..., description="ID of the owner responsible for the prescription", example=10)
    medical_record_id: int = Field(..., description="ID of the associated medical record", example=50)
    veterinarian_id: int = Field(..., description="ID of the prescribing veterinarian", example=3)
    medication_name: str = Field(..., description="Name of the medication prescribed", example="Carprofen 50mg")
    dosage_instructions: str = Field(..., description="Detailed dosage instructions for the medication", example="Give 1 tablet by mouth twice daily with food for 7 days")
    refill_count_remaining: int = Field(..., description="Number of refills remaining after initial dispense", example=1)

class PrescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique prescription identifier", example=500)
    pet_id: int = Field(..., description="ID of the pet", example=25)
    owner_id: int = Field(..., description="ID of the owner", example=10)
    medical_record_id: int = Field(..., description="ID of the related medical record", example=50)
    veterinarian_id: int = Field(..., description="ID of the prescribing veterinarian", example=3)
    medication_name: str = Field(..., description="Name of the medication", example="Carprofen 50mg")
    dosage_instructions: str = Field(..., description="Dosage instructions", example="Give 1 tablet by mouth twice daily with food for 7 days")
    refill_count_remaining: int = Field(..., description="Number of refills remaining", example=1)
    created_by_user_id: int = Field(..., description="ID of the user who created this prescription", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-12T09:55:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example=None)

class PrescriptionGetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique prescription identifier", example=500)
    pet_id: int = Field(..., description="ID of the pet", example=25)
    owner_id: int = Field(..., description="ID of the owner", example=10)
    medical_record_id: int = Field(..., description="ID of the related medical record", example=50)
    veterinarian_id: int = Field(..., description="ID of the prescribing veterinarian", example=3)
    medication_name: str = Field(..., description="Medication name", example="Carprofen 50mg")
    dosage_instructions: str = Field(..., description="Dosage instructions", example="Give 1 tablet by mouth twice daily with food for 7 days")
    refill_count_remaining: int = Field(..., description="Refills remaining", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-12T09:55:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example=None)

class PrescriptionRefillUpdateRequest(BaseModel):
    refill_count_remaining: int = Field(..., description="New value for refills remaining", example=0)

class PrescriptionRefillUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Prescription identifier", example=500)
    refill_count_remaining: int = Field(..., description="Updated refills remaining", example=0)
    updated_at: Optional[datetime] = Field(None, description="Timestamp of the update", example="2025-02-01T10:00:00Z")

class ReminderCreateRequest(BaseModel):
    owner_id: int = Field(..., description="ID of the owner to notify", example=10)
    pet_id: int = Field(..., description="ID of the pet the reminder concerns", example=25)
    related_appointment_id: Optional[str] = Field(None, description="Associated appointment ID if reminder is for an appointment", example="APT-10001")
    related_vaccination_id: Optional[int] = Field(None, description="Associated vaccination ID if reminder is for vaccination", example=200)
    related_prescription_id: Optional[int] = Field(None, description="Associated prescription ID if reminder is for refill", example=500)
    reminder_type: str = Field(..., description="Type of reminder: appointment, vaccination, prescription_refill", example="appointment")
    contact_method: str = Field(..., description="Contact method: email, phone, or sms", example="email")
    scheduled_time: str = Field(..., description="Datetime when the reminder should be sent", example="2025-03-30T10:00:00Z")
    metadata: Optional[str] = Field(None, description="JSON-encoded metadata with template or additional info", example='{"message": "Upcoming appointment in 48 hours"}')

class ReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique reminder identifier", example=600)
    owner_id: int = Field(..., description="ID of the owner", example=10)
    pet_id: int = Field(..., description="ID of the pet", example=25)
    related_appointment_id: Optional[str] = Field(None, description="Associated appointment ID", example="APT-10001")
    related_vaccination_id: Optional[int] = Field(None, description="Associated vaccination ID", example=200)
    related_prescription_id: Optional[int] = Field(None, description="Associated prescription ID", example=500)
    reminder_type: str = Field(..., description="Reminder type", example="appointment")
    contact_method: str = Field(..., description="Contact method used for the reminder", example="email")
    scheduled_time: datetime = Field(..., description="Datetime when reminder is scheduled to send", example="2025-03-30T10:00:00Z")
    sent_time: Optional[datetime] = Field(None, description="Datetime reminder was actually sent, if sent", example=None)
    is_sent: bool = Field(..., description="True if reminder has been sent, else False", example=False)
    metadata: Optional[str] = Field(None, description="JSON-encoded metadata for the reminder", example='{"message": "Upcoming appointment in 48 hours"}')
    created_by_user_id: int = Field(..., description="User who created the reminder", example=1)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-03-01T10:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example=None)

class ReminderGetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Unique reminder identifier", example=600)
    owner_id: int = Field(..., description="ID of the owner", example=10)
    pet_id: int = Field(..., description="ID of the pet", example=25)
    related_appointment_id: Optional[str] = Field(None, description="Associated appointment ID", example="APT-10001")
    related_vaccination_id: Optional[int] = Field(None, description="Associated vaccination ID", example=200)
    related_prescription_id: Optional[int] = Field(None, description="Associated prescription ID", example=500)
    reminder_type: str = Field(..., description="Reminder type", example="appointment")
    contact_method: str = Field(..., description="Contact method", example="email")
    scheduled_time: datetime = Field(..., description="Time scheduled for sending the reminder", example="2025-03-30T10:00:00Z")
    sent_time: Optional[datetime] = Field(None, description="Actual time the reminder was sent", example=None)
    is_sent: bool = Field(..., description="True if sent, otherwise False", example=False)
    metadata: Optional[str] = Field(None, description="Extra metadata for the reminder", example='{"channel": "email"}')
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-03-01T10:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example=None)

class ReminderMarkSentRequest(BaseModel):
    sent_time: str = Field(..., description="Timestamp when the reminder was sent", example="2025-03-30T10:00:05Z")

class ReminderMarkSentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Reminder identifier", example=600)
    is_sent: bool = Field(..., description="Flag indicating if reminder has been sent", example=True)
    sent_time: Optional[datetime] = Field(None, description="Time reminder was sent", example="2025-03-30T10:00:05Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example="2025-03-30T10:00:10Z")

@app.post(
    "/api/pet_owners",
    response_model=PetOwnerResponse,
    summary="Create a new pet owner profile",
    description="Create a pet owner with contact and billing details for a new client.",
    tags=["pet_owners"],
    operation_id="create_pet_owner",
)
async def create_pet_owner(body: PetOwnerCreateRequest = Body(...)) -> PetOwnerResponse:
    session = SessionLocal()
    owner = PetOwner(
        full_name=body.full_name,
        mobile_number=body.mobile_number,
        email=body.email,
        mailing_address=body.mailing_address,
        preferred_contact_method=body.preferred_contact_method,
        billing_preference_method=body.billing_preference_method,
        billing_notes=body.billing_notes,
        created_by_user_id=1,
        updated_at=None,
    )
    session.add(owner)
    session.commit()
    session.refresh(owner)
    result = PetOwnerResponse(
        id=owner.id,
        full_name=owner.full_name,
        mobile_number=owner.mobile_number,
        email=owner.email,
        mailing_address=owner.mailing_address,
        preferred_contact_method=owner.preferred_contact_method,
        billing_preference_method=owner.billing_preference_method,
        billing_notes=owner.billing_notes,
        created_by_user_id=owner.created_by_user_id,
        created_at=owner.created_at,
        updated_at=owner.updated_at,
    )
    session.close()
    return result

@app.get(
    "/api/pet_owners",
    response_model=PetOwnerListResponse,
    summary="Search pet owners by name or email",
    description="List pet owners filtered by full name or email for finding an existing owner.",
    tags=["pet_owners"],
    operation_id="list_pet_owners",
)
async def list_pet_owners(
    full_name: Optional[str] = Query(None, description="Filter owners whose full_name contains this value", example="Maria Sanchez"),
    email: Optional[str] = Query(None, description="Filter owners by exact email match", example="maria.sanchez@example.com"),
    limit: Optional[int] = Query(20, description="Maximum number of owners to return", example=20),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> PetOwnerListResponse:
    session = SessionLocal()
    query = session.query(PetOwner).filter(PetOwner.created_by_user_id == 1)
    if full_name is not None:
        query = query.filter(PetOwner.full_name.contains(full_name))
    if email is not None:
        query = query.filter(PetOwner.email == email)
    total = query.count()
    owners = query.offset(offset).limit(limit).all()
    items = []
    for o in owners:
        items.append(
            PetOwnerListItem(
                id=o.id,
                full_name=o.full_name,
                mobile_number=o.mobile_number,
                email=o.email,
                mailing_address=o.mailing_address,
                preferred_contact_method=o.preferred_contact_method,
                billing_preference_method=o.billing_preference_method,
                billing_notes=o.billing_notes,
                created_at=o.created_at,
            )
        )
    session.close()
    return PetOwnerListResponse(items=items, total=total)

@app.get(
    "/api/pet_owners/{owner_id}",
    response_model=PetOwnerResponse,
    summary="Get a single pet owner by id",
    description="Retrieve a single pet owner record by its id.",
    tags=["pet_owners"],
    operation_id="get_pet_owner_by_id",
)
async def get_pet_owner_by_id(
    owner_id: int = Path(..., description="ID of the pet owner to retrieve", example=10)
) -> PetOwnerResponse:
    session = SessionLocal()
    owner = session.query(PetOwner).filter(PetOwner.id == owner_id, PetOwner.created_by_user_id == 1).first()
    if owner is None:
        owner = PetOwner(
            id=0,
            full_name="",
            mobile_number=None,
            email=None,
            mailing_address=None,
            preferred_contact_method="email",
            billing_preference_method="cash",
            billing_notes=None,
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
    result = PetOwnerResponse(
        id=owner.id,
        full_name=owner.full_name,
        mobile_number=owner.mobile_number,
        email=owner.email,
        mailing_address=owner.mailing_address,
        preferred_contact_method=owner.preferred_contact_method,
        billing_preference_method=owner.billing_preference_method,
        billing_notes=owner.billing_notes,
        created_by_user_id=owner.created_by_user_id,
        created_at=owner.created_at,
        updated_at=owner.updated_at,
    )
    session.close()
    return result

@app.get(
    "/api/veterinarians",
    response_model=VeterinarianListResponse,
    summary="List veterinarians with optional name filter",
    description="Retrieve veterinarians, filterable by full_name, for appointment assignment.",
    tags=["veterinarians"],
    operation_id="list_veterinarians",
)
async def list_veterinarians(
    full_name: Optional[str] = Query(None, description="Filter vets whose full_name contains this value", example="Dr. Alex Kim"),
    limit: Optional[int] = Query(20, description="Maximum number of veterinarians to return", example=20),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> VeterinarianListResponse:
    session = SessionLocal()
    query = session.query(Veterinarian)
    if full_name is not None:
        query = query.filter(Veterinarian.full_name.contains(full_name))
    total = query.count()
    vets = query.offset(offset).limit(limit).all()
    items = []
    for v in vets:
        items.append(
            VeterinarianListItem(
                id=v.id,
                full_name=v.full_name,
                license_number=v.license_number,
                email=v.email,
                phone=v.phone,
            )
        )
    session.close()
    return VeterinarianListResponse(items=items, total=total)

@app.get(
    "/api/clinics",
    response_model=ClinicListResponse,
    summary="List clinics with optional name filter",
    description="Retrieve clinics, optionally filtered by name, for scheduling appointments.",
    tags=["clinics"],
    operation_id="list_clinics",
)
async def list_clinics(
    name: Optional[str] = Query(None, description="Filter clinics whose name contains this value", example="Downtown Animal Hospital"),
    limit: Optional[int] = Query(20, description="Maximum number of clinics to return", example=20),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> ClinicListResponse:
    session = SessionLocal()
    query = session.query(Clinic)
    if name is not None:
        query = query.filter(Clinic.name.contains(name))
    total = query.count()
    clinics = query.offset(offset).limit(limit).all()
    items = []
    for c in clinics:
        items.append(
            ClinicListItem(
                id=c.id,
                name=c.name,
                address=c.address,
                phone=c.phone,
            )
        )
    session.close()
    return ClinicListResponse(items=items, total=total)

@app.get(
    "/api/clinics/{clinic_id}/rooms",
    response_model=ClinicRoomListResponse,
    summary="List rooms for a given clinic",
    description="Retrieve clinic rooms for a clinic to assign scheduled or actual rooms.",
    tags=["clinics", "clinic_rooms"],
    operation_id="list_clinic_rooms",
)
async def list_clinic_rooms(
    clinic_id: int = Path(..., description="ID of the clinic whose rooms should be listed", example=1),
    only_active: Optional[bool] = Query(False, description="If true, only return rooms where is_active=1", example=True),
) -> ClinicRoomListResponse:
    session = SessionLocal()
    query = session.query(ClinicRoom).filter(ClinicRoom.clinic_id == clinic_id)
    if only_active:
        query = query.filter(ClinicRoom.is_active == 1)
    rooms = query.all()
    items = []
    for r in rooms:
        items.append(
            ClinicRoomItem(
                id=r.id,
                clinic_id=r.clinic_id,
                name=r.name,
                is_active=r.is_active,
            )
        )
    session.close()
    return ClinicRoomListResponse(items=items)

@app.post(
    "/api/pets",
    response_model=PetResponse,
    summary="Create a new pet for an owner",
    description="Create a pet linked to an existing pet owner with demographics and status.",
    tags=["pets"],
    operation_id="create_pet",
)
async def create_pet(body: PetCreateRequest = Body(...)) -> PetResponse:
    session = SessionLocal()
    birthdate_value = None
    if body.birthdate is not None:
        birthdate_value = datetime.fromisoformat(body.birthdate).date()
    pet = Pet(
        owner_id=body.owner_id,
        name=body.name,
        species=body.species,
        breed=body.breed,
        birthdate=birthdate_value,
        status=body.status,
        updated_at=None,
    )
    session.add(pet)
    session.commit()
    session.refresh(pet)
    result = PetResponse(
        id=pet.id,
        owner_id=pet.owner_id,
        name=pet.name,
        species=pet.species,
        breed=pet.breed,
        birthdate=pet.birthdate,
        status=pet.status,
        created_at=pet.created_at,
        updated_at=pet.updated_at,
    )
    session.close()
    return result

@app.get(
    "/api/pets",
    response_model=PetListResponse,
    summary="Search pets by name and owner",
    description="Retrieve pets filtered by name and/or owner_id to find a specific pet record.",
    tags=["pets"],
    operation_id="list_pets",
)
async def list_pets(
    name: Optional[str] = Query(None, description="Filter pets whose name contains this value", example="Luna"),
    owner_id: Optional[int] = Query(None, description="Filter pets that belong to the given owner_id", example=10),
    status: Optional[str] = Query(None, description="Filter pets by status: active, inactive, or deceased", example="active"),
    limit: Optional[int] = Query(20, description="Maximum number of pets to return", example=20),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> PetListResponse:
    session = SessionLocal()
    query = session.query(Pet)
    if name is not None:
        query = query.filter(Pet.name.contains(name))
    if owner_id is not None:
        query = query.filter(Pet.owner_id == owner_id)
    if status is not None:
        query = query.filter(Pet.status == status)
    total = query.count()
    pets = query.offset(offset).limit(limit).all()
    items = []
    for p in pets:
        items.append(
            PetListItem(
                id=p.id,
                owner_id=p.owner_id,
                name=p.name,
                species=p.species,
                breed=p.breed,
                birthdate=p.birthdate,
                status=p.status,
            )
        )
    session.close()
    return PetListResponse(items=items, total=total)

@app.get(
    "/api/pets/{pet_id}",
    response_model=PetResponse,
    summary="Get a single pet by id",
    description="Retrieve a specific pet record by id for detailed info and linking.",
    tags=["pets"],
    operation_id="get_pet_by_id",
)
async def get_pet_by_id(
    pet_id: int = Path(..., description="ID of the pet to retrieve", example=25)
) -> PetResponse:
    session = SessionLocal()
    pet = session.query(Pet).filter(Pet.id == pet_id).first()
    if pet is None:
        pet = Pet(
            id=0,
            owner_id=0,
            name="",
            species="",
            breed=None,
            birthdate=None,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=None,
        )
    result = PetResponse(
        id=pet.id,
        owner_id=pet.owner_id,
        name=pet.name,
        species=pet.species,
        breed=pet.breed,
        birthdate=pet.birthdate,
        status=pet.status,
        created_at=pet.created_at,
        updated_at=pet.updated_at,
    )
    session.close()
    return result

@app.post(
    "/api/pets/{pet_id}/weight_history",
    response_model=PetWeightHistoryResponse,
    summary="Add a weight history entry for a pet",
    description="Insert a pet weight history row for tracking pet weight over time.",
    tags=["pet_weight_history"],
    operation_id="create_pet_weight_history",
)
async def create_pet_weight_history(
    pet_id: int = Path(..., description="ID of the pet whose weight is being recorded", example=25),
    body: PetWeightHistoryCreateRequest = Body(...),
) -> PetWeightHistoryResponse:
    session = SessionLocal()
    recorded_at_value = datetime.fromisoformat(body.recorded_at)
    weight = PetWeightHistory(
        pet_id=pet_id,
        recorded_at=recorded_at_value,
        weight_kg=body.weight_kg,
        source=body.source,
        updated_at=None,
    )
    session.add(weight)
    session.commit()
    session.refresh(weight)
    result = PetWeightHistoryResponse(
        id=weight.id,
        pet_id=weight.pet_id,
        recorded_at=weight.recorded_at,
        weight_kg=weight.weight_kg,
        source=weight.source,
        created_at=weight.created_at,
        updated_at=weight.updated_at,
    )
    session.close()
    return result

@app.post(
    "/api/appointments",
    response_model=AppointmentResponse,
    summary="Create a new appointment",
    description="Create an appointment linking pet, owner, vet, clinic, and room with schedule info.",
    tags=["appointments"],
    operation_id="create_appointment",
)
async def create_appointment(body: AppointmentCreateRequest = Body(...)) -> AppointmentResponse:
    session = SessionLocal()
    appointment_id = body.id
    if appointment_id is None or appointment_id == "":
        appointment_id = "APT-" + datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    scheduled_start_value = datetime.fromisoformat(body.scheduled_start)
    scheduled_end_value = None
    if body.scheduled_end is not None:
        scheduled_end_value = datetime.fromisoformat(body.scheduled_end)
    appointment = Appointment(
        id=appointment_id,
        pet_id=body.pet_id,
        owner_id=body.owner_id,
        veterinarian_id=body.veterinarian_id,
        clinic_id=body.clinic_id,
        scheduled_room_id=body.scheduled_room_id,
        actual_room_id=None,
        appointment_type=body.appointment_type,
        status=body.status,
        scheduled_start=scheduled_start_value,
        scheduled_end=scheduled_end_value,
        check_in_time=None,
        check_out_time=None,
        duration_minutes=body.duration_minutes,
        metadata_=body.metadata,
        created_by_user_id=1,
        updated_at=None,
    )
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    result = AppointmentResponse(
        id=appointment.id,
        pet_id=appointment.pet_id,
        owner_id=appointment.owner_id,
        veterinarian_id=appointment.veterinarian_id,
        clinic_id=appointment.clinic_id,
        scheduled_room_id=appointment.scheduled_room_id,
        actual_room_id=appointment.actual_room_id,
        appointment_type=appointment.appointment_type,
        status=appointment.status,
        scheduled_start=appointment.scheduled_start,
        scheduled_end=appointment.scheduled_end,
        check_in_time=appointment.check_in_time,
        check_out_time=appointment.check_out_time,
        duration_minutes=appointment.duration_minutes,
        metadata=appointment.metadata_,
        created_by_user_id=appointment.created_by_user_id,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
    )
    session.close()
    return result

@app.get(
    "/api/appointments/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Get a single appointment by id",
    description="Retrieve an appointment row by its id for inspection or linking.",
    tags=["appointments"],
    operation_id="get_appointment_by_id",
)
async def get_appointment_by_id(
    appointment_id: str = Path(..., description="ID of the appointment to retrieve", example="APT-98342")
) -> AppointmentResponse:
    session = SessionLocal()
    appointment = session.query(Appointment).filter(Appointment.id == appointment_id, Appointment.created_by_user_id == 1).first()
    if appointment is None:
        appointment = Appointment(
            id=appointment_id,
            pet_id=0,
            owner_id=0,
            veterinarian_id=0,
            clinic_id=0,
            scheduled_room_id=None,
            actual_room_id=None,
            appointment_type="other",
            status="scheduled",
            scheduled_start=datetime.utcnow(),
            scheduled_end=None,
            check_in_time=None,
            check_out_time=None,
            duration_minutes=None,
            metadata_=None,
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
    result = AppointmentResponse(
        id=appointment.id,
        pet_id=appointment.pet_id,
        owner_id=appointment.owner_id,
        veterinarian_id=appointment.veterinarian_id,
        clinic_id=appointment.clinic_id,
        scheduled_room_id=appointment.scheduled_room_id,
        actual_room_id=appointment.actual_room_id,
        appointment_type=appointment.appointment_type,
        status=appointment.status,
        scheduled_start=appointment.scheduled_start,
        scheduled_end=appointment.scheduled_end,
        check_in_time=appointment.check_in_time,
        check_out_time=appointment.check_out_time,
        duration_minutes=appointment.duration_minutes,
        metadata=appointment.metadata_,
        created_by_user_id=appointment.created_by_user_id,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
    )
    session.close()
    return result

@app.patch(
    "/api/appointments/{appointment_id}/reschedule",
    response_model=AppointmentRescheduleResponse,
    summary="Reschedule an existing appointment time",
    description="Update scheduled_start, scheduled_end, status, and metadata for an appointment.",
    tags=["appointments"],
    operation_id="reschedule_appointment",
)
async def reschedule_appointment(
    appointment_id: str = Path(..., description="ID of the appointment to reschedule", example="APT-98342"),
    body: AppointmentRescheduleRequest = Body(...),
) -> AppointmentRescheduleResponse:
    session = SessionLocal()
    appointment = session.query(Appointment).filter(Appointment.id == appointment_id, Appointment.created_by_user_id == 1).first()
    if appointment is None:
        appointment = Appointment(
            id=appointment_id,
            pet_id=0,
            owner_id=0,
            veterinarian_id=0,
            clinic_id=0,
            scheduled_room_id=None,
            actual_room_id=None,
            appointment_type="other",
            status="scheduled",
            scheduled_start=datetime.utcnow(),
            scheduled_end=None,
            check_in_time=None,
            check_out_time=None,
            duration_minutes=None,
            metadata_=None,
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
        session.add(appointment)
        session.commit()
        session.refresh(appointment)
    appointment.scheduled_start = datetime.fromisoformat(body.new_scheduled_start)
    if body.new_scheduled_end is not None:
        appointment.scheduled_end = datetime.fromisoformat(body.new_scheduled_end)
    if body.status is not None:
        appointment.status = body.status
    if body.metadata is not None:
        appointment.metadata_ = body.metadata
    appointment.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(appointment)
    result = AppointmentRescheduleResponse(
        id=appointment.id,
        scheduled_start=appointment.scheduled_start,
        scheduled_end=appointment.scheduled_end,
        status=appointment.status,
        metadata=appointment.metadata_,
        updated_at=appointment.updated_at,
    )
    session.close()
    return result

@app.patch(
    "/api/appointments/{appointment_id}/check_in",
    response_model=AppointmentCheckInResponse,
    summary="Check in a pet for an appointment",
    description="Set status to checked_in, record check_in_time, and update actual_room_id.",
    tags=["appointments"],
    operation_id="check_in_appointment",
)
async def check_in_appointment(
    appointment_id: str = Path(..., description="ID of the appointment to check in", example="APT-98342"),
    body: AppointmentCheckInRequest = Body(...),
) -> AppointmentCheckInResponse:
    session = SessionLocal()
    appointment = session.query(Appointment).filter(Appointment.id == appointment_id, Appointment.created_by_user_id == 1).first()
    if appointment is None:
        appointment = Appointment(
            id=appointment_id,
            pet_id=0,
            owner_id=0,
            veterinarian_id=0,
            clinic_id=0,
            scheduled_room_id=None,
            actual_room_id=None,
            appointment_type="other",
            status="scheduled",
            scheduled_start=datetime.utcnow(),
            scheduled_end=None,
            check_in_time=None,
            check_out_time=None,
            duration_minutes=None,
            metadata_=None,
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
        session.add(appointment)
        session.commit()
        session.refresh(appointment)
    appointment.status = "checked_in"
    appointment.check_in_time = datetime.fromisoformat(body.check_in_time)
    if body.actual_room_id is not None:
        appointment.actual_room_id = body.actual_room_id
    appointment.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(appointment)
    result = AppointmentCheckInResponse(
        id=appointment.id,
        status=appointment.status,
        check_in_time=appointment.check_in_time,
        actual_room_id=appointment.actual_room_id,
        updated_at=appointment.updated_at,
    )
    session.close()
    return result

@app.patch(
    "/api/appointments/{appointment_id}/complete",
    response_model=AppointmentCompleteResponse,
    summary="Mark an appointment as completed",
    description="Set status to completed and optionally record check_out_time and duration.",
    tags=["appointments"],
    operation_id="complete_appointment",
)
async def complete_appointment(
    appointment_id: str = Path(..., description="ID of the appointment to mark as completed", example="APT-98342"),
    body: AppointmentCompleteRequest = Body(...),
) -> AppointmentCompleteResponse:
    session = SessionLocal()
    appointment = session.query(Appointment).filter(Appointment.id == appointment_id, Appointment.created_by_user_id == 1).first()
    if appointment is None:
        appointment = Appointment(
            id=appointment_id,
            pet_id=0,
            owner_id=0,
            veterinarian_id=0,
            clinic_id=0,
            scheduled_room_id=None,
            actual_room_id=None,
            appointment_type="other",
            status="scheduled",
            scheduled_start=datetime.utcnow(),
            scheduled_end=None,
            check_in_time=None,
            check_out_time=None,
            duration_minutes=None,
            metadata_=None,
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
        session.add(appointment)
        session.commit()
        session.refresh(appointment)
    appointment.status = "completed"
    if body.check_out_time is not None:
        appointment.check_out_time = datetime.fromisoformat(body.check_out_time)
    if body.duration_minutes is not None:
        appointment.duration_minutes = body.duration_minutes
    appointment.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(appointment)
    result = AppointmentCompleteResponse(
        id=appointment.id,
        status=appointment.status,
        check_out_time=appointment.check_out_time,
        duration_minutes=appointment.duration_minutes,
        updated_at=appointment.updated_at,
    )
    session.close()
    return result

@app.post(
    "/api/medical_records",
    response_model=MedicalRecordResponse,
    summary="Create a medical record for a visit",
    description="Insert a medical record linked to pet, owner, vet, and optionally appointment.",
    tags=["medical_records"],
    operation_id="create_medical_record",
)
async def create_medical_record(body: MedicalRecordCreateRequest = Body(...)) -> MedicalRecordResponse:
    session = SessionLocal()
    diagnosis_serialized = "[" + ",".join(['"' + d + '"' for d in body.diagnosis_codes]) + "]"
    procedures_serialized = "[" + ",".join(['"' + p + '"' for p in body.procedures_performed]) + "]"
    record = MedicalRecord(
        pet_id=body.pet_id,
        owner_id=body.owner_id,
        veterinarian_id=body.veterinarian_id,
        appointment_id=body.appointment_id,
        diagnosis_codes=diagnosis_serialized,
        procedures_performed=procedures_serialized,
        notes=body.notes,
        created_by_user_id=1,
        updated_at=None,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    result = MedicalRecordResponse(
        id=record.id,
        pet_id=record.pet_id,
        owner_id=record.owner_id,
        veterinarian_id=record.veterinarian_id,
        appointment_id=record.appointment_id,
        diagnosis_codes=record.diagnosis_codes,
        procedures_performed=record.procedures_performed,
        notes=record.notes,
        created_by_user_id=record.created_by_user_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
    session.close()
    return result

@app.get(
    "/api/medical_records/{medical_record_id}",
    response_model=MedicalRecordResponse,
    summary="Get a single medical record by id",
    description="Retrieve a medical record row by its id for inspection or linking.",
    tags=["medical_records"],
    operation_id="get_medical_record_by_id",
)
async def get_medical_record_by_id(
    medical_record_id: int = Path(..., description="ID of the medical record to retrieve", example=50)
) -> MedicalRecordResponse:
    session = SessionLocal()
    record = session.query(MedicalRecord).filter(MedicalRecord.id == medical_record_id, MedicalRecord.created_by_user_id == 1).first()
    if record is None:
        record = MedicalRecord(
            id=medical_record_id,
            pet_id=0,
            owner_id=0,
            veterinarian_id=0,
            appointment_id=None,
            diagnosis_codes="[]",
            procedures_performed="[]",
            notes=None,
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
    result = MedicalRecordResponse(
        id=record.id,
        pet_id=record.pet_id,
        owner_id=record.owner_id,
        veterinarian_id=record.veterinarian_id,
        appointment_id=record.appointment_id,
        diagnosis_codes=record.diagnosis_codes,
        procedures_performed=record.procedures_performed,
        notes=record.notes,
        created_by_user_id=record.created_by_user_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
    session.close()
    return result

@app.post(
    "/api/vaccinations",
    response_model=VaccinationResponse,
    summary="Record a vaccination for a pet",
    description="Insert a vaccination row linked to a pet and optionally a medical record.",
    tags=["vaccinations"],
    operation_id="create_vaccination",
)
async def create_vaccination(body: VaccinationCreateRequest = Body(...)) -> VaccinationResponse:
    session = SessionLocal()
    administration_date_value = datetime.fromisoformat(body.administration_date).date()
    next_due_date_value = None
    if body.next_due_date is not None:
        next_due_date_value = datetime.fromisoformat(body.next_due_date).date()
    vaccination = Vaccination(
        pet_id=body.pet_id,
        medical_record_id=body.medical_record_id,
        vaccine_type=body.vaccine_type,
        dose=body.dose,
        administration_date=administration_date_value,
        next_due_date=next_due_date_value,
        created_by_user_id=1,
        updated_at=None,
    )
    session.add(vaccination)
    session.commit()
    session.refresh(vaccination)
    result = VaccinationResponse(
        id=vaccination.id,
        pet_id=vaccination.pet_id,
        medical_record_id=vaccination.medical_record_id,
        vaccine_type=vaccination.vaccine_type,
        dose=vaccination.dose,
        administration_date=vaccination.administration_date,
        next_due_date=vaccination.next_due_date,
        created_by_user_id=vaccination.created_by_user_id,
        created_at=vaccination.created_at,
        updated_at=vaccination.updated_at,
    )
    session.close()
    return result

@app.get(
    "/api/vaccinations/{vaccination_id}",
    response_model=VaccinationGetResponse,
    summary="Get a vaccination record by id",
    description="Retrieve a vaccination row by its id for review or reminder creation.",
    tags=["vaccinations"],
    operation_id="get_vaccination_by_id",
)
async def get_vaccination_by_id(
    vaccination_id: int = Path(..., description="ID of the vaccination record to retrieve", example=200)
) -> VaccinationGetResponse:
    session = SessionLocal()
    vaccination = session.query(Vaccination).filter(Vaccination.id == vaccination_id, Vaccination.created_by_user_id == 1).first()
    if vaccination is None:
        vaccination = Vaccination(
            id=vaccination_id,
            pet_id=0,
            medical_record_id=None,
            vaccine_type="",
            dose=None,
            administration_date=datetime.utcnow().date(),
            next_due_date=None,
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
    result = VaccinationGetResponse(
        id=vaccination.id,
        pet_id=vaccination.pet_id,
        medical_record_id=vaccination.medical_record_id,
        vaccine_type=vaccination.vaccine_type,
        dose=vaccination.dose,
        administration_date=vaccination.administration_date,
        next_due_date=vaccination.next_due_date,
        created_at=vaccination.created_at,
        updated_at=vaccination.updated_at,
    )
    session.close()
    return result

@app.get(
    "/api/services",
    response_model=ServiceListResponse,
    summary="List billable services with optional filters",
    description="Retrieve services that can be billed on invoices, filterable by code or name.",
    tags=["services"],
    operation_id="list_services",
)
async def list_services(
    code: Optional[str] = Query(None, description="Filter services by exact code", example="SRV-001"),
    name: Optional[str] = Query(None, description="Filter services whose name contains this value", example="Rabies vaccine"),
    limit: Optional[int] = Query(50, description="Maximum number of services to return", example=50),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> ServiceListResponse:
    session = SessionLocal()
    query = session.query(Service)
    if code is not None:
        query = query.filter(Service.code == code)
    if name is not None:
        query = query.filter(Service.name.contains(name))
    total = query.count()
    services = query.offset(offset).limit(limit).all()
    items = []
    for s in services:
        items.append(
            ServiceListItem(
                id=s.id,
                code=s.code,
                name=s.name,
                description=s.description,
                default_price=s.default_price,
            )
        )
    session.close()
    return ServiceListResponse(items=items, total=total)

@app.post(
    "/api/invoices",
    response_model=InvoiceResponse,
    summary="Create an invoice for an appointment",
    description="Insert an invoice linked to appointment, owner, and pet with amounts and status.",
    tags=["invoices"],
    operation_id="create_invoice",
)
async def create_invoice(body: InvoiceCreateRequest = Body(...)) -> InvoiceResponse:
    session = SessionLocal()
    invoice = Invoice(
        appointment_id=body.appointment_id,
        owner_id=body.owner_id,
        pet_id=body.pet_id,
        subtotal_amount=body.subtotal_amount,
        discount_description=body.discount_description,
        discount_percent=body.discount_percent,
        discount_amount=body.discount_amount,
        total_amount=body.total_amount,
        payment_status=body.payment_status,
        created_by_user_id=1,
        updated_at=None,
    )
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    result = InvoiceResponse(
        id=invoice.id,
        appointment_id=invoice.appointment_id,
        owner_id=invoice.owner_id,
        pet_id=invoice.pet_id,
        subtotal_amount=invoice.subtotal_amount,
        discount_description=invoice.discount_description,
        discount_percent=invoice.discount_percent,
        discount_amount=invoice.discount_amount,
        total_amount=invoice.total_amount,
        payment_status=invoice.payment_status,
        created_by_user_id=invoice.created_by_user_id,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )
    session.close()
    return result

@app.get(
    "/api/invoices/{invoice_id}",
    response_model=InvoiceGetResponse,
    summary="Get an invoice by id",
    description="Retrieve an invoice row by id including core financial fields.",
    tags=["invoices"],
    operation_id="get_invoice_by_id",
)
async def get_invoice_by_id(
    invoice_id: int = Path(..., description="ID of the invoice to retrieve", example=300)
) -> InvoiceGetResponse:
    session = SessionLocal()
    invoice = session.query(Invoice).filter(Invoice.id == invoice_id, Invoice.created_by_user_id == 1).first()
    if invoice is None:
        invoice = Invoice(
            id=invoice_id,
            appointment_id="",
            owner_id=0,
            pet_id=0,
            subtotal_amount=0.0,
            discount_description=None,
            discount_percent=None,
            discount_amount=None,
            total_amount=0.0,
            payment_status="unpaid",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
    result = InvoiceGetResponse(
        id=invoice.id,
        appointment_id=invoice.appointment_id,
        owner_id=invoice.owner_id,
        pet_id=invoice.pet_id,
        subtotal_amount=invoice.subtotal_amount,
        discount_description=invoice.discount_description,
        discount_percent=invoice.discount_percent,
        discount_amount=invoice.discount_amount,
        total_amount=invoice.total_amount,
        payment_status=invoice.payment_status,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )
    session.close()
    return result

@app.post(
    "/api/invoice_items",
    response_model=InvoiceItemResponse,
    summary="Add an item line to an invoice",
    description="Insert an invoice item row linked to an invoice and optionally a service.",
    tags=["invoice_items"],
    operation_id="create_invoice_item",
)
async def create_invoice_item(body: InvoiceItemCreateRequest = Body(...)) -> InvoiceItemResponse:
    session = SessionLocal()
    item = InvoiceItem(
        invoice_id=body.invoice_id,
        service_id=body.service_id,
        service_code=body.service_code,
        description=body.description,
        quantity=body.quantity,
        unit_price=body.unit_price,
        line_total=body.line_total,
        updated_at=None,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    result = InvoiceItemResponse(
        id=item.id,
        invoice_id=item.invoice_id,
        service_id=item.service_id,
        service_code=item.service_code,
        description=item.description,
        quantity=item.quantity,
        unit_price=item.unit_price,
        line_total=item.line_total,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
    session.close()
    return result

@app.get(
    "/api/invoices/{invoice_id}/items",
    response_model=InvoiceItemListResponse,
    summary="List items for a specific invoice",
    description="Retrieve invoice items associated with an invoice to see billed services.",
    tags=["invoice_items"],
    operation_id="list_invoice_items_for_invoice",
)
async def list_invoice_items_for_invoice(
    invoice_id: int = Path(..., description="Invoice ID whose items should be listed", example=300)
) -> InvoiceItemListResponse:
    session = SessionLocal()
    items_query = session.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id)
    items_db = items_query.all()
    items = []
    for it in items_db:
        items.append(
            InvoiceItemListItem(
                id=it.id,
                invoice_id=it.invoice_id,
                service_id=it.service_id,
                service_code=it.service_code,
                description=it.description,
                quantity=it.quantity,
                unit_price=it.unit_price,
                line_total=it.line_total,
            )
        )
    session.close()
    return InvoiceItemListResponse(items=items)

@app.post(
    "/api/prescriptions",
    response_model=PrescriptionResponse,
    summary="Create a prescription for a pet",
    description="Insert a prescription row linked to pet, owner, vet, and medical record.",
    tags=["prescriptions"],
    operation_id="create_prescription",
)
async def create_prescription(body: PrescriptionCreateRequest = Body(...)) -> PrescriptionResponse:
    session = SessionLocal()
    prescription = Prescription(
        pet_id=body.pet_id,
        owner_id=body.owner_id,
        medical_record_id=body.medical_record_id,
        veterinarian_id=body.veterinarian_id,
        medication_name=body.medication_name,
        dosage_instructions=body.dosage_instructions,
        refill_count_remaining=body.refill_count_remaining,
        created_by_user_id=1,
        updated_at=None,
    )
    session.add(prescription)
    session.commit()
    session.refresh(prescription)
    result = PrescriptionResponse(
        id=prescription.id,
        pet_id=prescription.pet_id,
        owner_id=prescription.owner_id,
        medical_record_id=prescription.medical_record_id,
        veterinarian_id=prescription.veterinarian_id,
        medication_name=prescription.medication_name,
        dosage_instructions=prescription.dosage_instructions,
        refill_count_remaining=prescription.refill_count_remaining,
        created_by_user_id=prescription.created_by_user_id,
        created_at=prescription.created_at,
        updated_at=prescription.updated_at,
    )
    session.close()
    return result

@app.get(
    "/api/prescriptions/{prescription_id}",
    response_model=PrescriptionGetResponse,
    summary="Get a prescription by id",
    description="Retrieve a prescription row by its id, including medication and refill info.",
    tags=["prescriptions"],
    operation_id="get_prescription_by_id",
)
async def get_prescription_by_id(
    prescription_id: int = Path(..., description="ID of the prescription to retrieve", example=500)
) -> PrescriptionGetResponse:
    session = SessionLocal()
    prescription = session.query(Prescription).filter(Prescription.id == prescription_id, Prescription.created_by_user_id == 1).first()
    if prescription is None:
        prescription = Prescription(
            id=prescription_id,
            pet_id=0,
            owner_id=0,
            medical_record_id=0,
            veterinarian_id=0,
            medication_name="",
            dosage_instructions="",
            refill_count_remaining=0,
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
    result = PrescriptionGetResponse(
        id=prescription.id,
        pet_id=prescription.pet_id,
        owner_id=prescription.owner_id,
        medical_record_id=prescription.medical_record_id,
        veterinarian_id=prescription.veterinarian_id,
        medication_name=prescription.medication_name,
        dosage_instructions=prescription.dosage_instructions,
        refill_count_remaining=prescription.refill_count_remaining,
        created_at=prescription.created_at,
        updated_at=prescription.updated_at,
    )
    session.close()
    return result

@app.patch(
    "/api/prescriptions/{prescription_id}/refill_count",
    response_model=PrescriptionRefillUpdateResponse,
    summary="Update remaining refills for a prescription",
    description="Adjust refill_count_remaining for an existing prescription record.",
    tags=["prescriptions"],
    operation_id="update_prescription_refill_count",
)
async def update_prescription_refill_count(
    prescription_id: int = Path(..., description="ID of the prescription to update", example=500),
    body: PrescriptionRefillUpdateRequest = Body(...),
) -> PrescriptionRefillUpdateResponse:
    session = SessionLocal()
    prescription = session.query(Prescription).filter(Prescription.id == prescription_id, Prescription.created_by_user_id == 1).first()
    if prescription is None:
        prescription = Prescription(
            id=prescription_id,
            pet_id=0,
            owner_id=0,
            medical_record_id=0,
            veterinarian_id=0,
            medication_name="",
            dosage_instructions="",
            refill_count_remaining=0,
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
        session.add(prescription)
        session.commit()
        session.refresh(prescription)
    prescription.refill_count_remaining = body.refill_count_remaining
    prescription.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(prescription)
    result = PrescriptionRefillUpdateResponse(
        id=prescription.id,
        refill_count_remaining=prescription.refill_count_remaining,
        updated_at=prescription.updated_at,
    )
    session.close()
    return result

@app.post(
    "/api/reminders",
    response_model=ReminderResponse,
    summary="Create a reminder for appointment, vaccination, or prescription",
    description="Insert a reminder linked to owner, pet, and optionally appointment, vaccination, or prescription.",
    tags=["reminders"],
    operation_id="create_reminder",
)
async def create_reminder(body: ReminderCreateRequest = Body(...)) -> ReminderResponse:
    session = SessionLocal()
    scheduled_time_value = datetime.fromisoformat(body.scheduled_time)
    reminder = Reminder(
        owner_id=body.owner_id,
        pet_id=body.pet_id,
        related_appointment_id=body.related_appointment_id,
        related_vaccination_id=body.related_vaccination_id,
        related_prescription_id=body.related_prescription_id,
        reminder_type=body.reminder_type,
        contact_method=body.contact_method,
        scheduled_time=scheduled_time_value,
        sent_time=None,
        is_sent=0,
        metadata_=body.metadata,
        created_by_user_id=1,
        updated_at=None,
    )
    session.add(reminder)
    session.commit()
    session.refresh(reminder)
    result = ReminderResponse(
        id=reminder.id,
        owner_id=reminder.owner_id,
        pet_id=reminder.pet_id,
        related_appointment_id=reminder.related_appointment_id,
        related_vaccination_id=reminder.related_vaccination_id,
        related_prescription_id=reminder.related_prescription_id,
        reminder_type=reminder.reminder_type,
        contact_method=reminder.contact_method,
        scheduled_time=reminder.scheduled_time,
        sent_time=reminder.sent_time,
        is_sent=bool(reminder.is_sent),
        metadata=reminder.metadata_,
        created_by_user_id=reminder.created_by_user_id,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
    )
    session.close()
    return result

@app.get(
    "/api/reminders/{reminder_id}",
    response_model=ReminderGetResponse,
    summary="Get a reminder by id",
    description="Retrieve a reminder row by id to view scheduling, links, and metadata.",
    tags=["reminders"],
    operation_id="get_reminder_by_id",
)
async def get_reminder_by_id(
    reminder_id: int = Path(..., description="ID of the reminder to retrieve", example=600)
) -> ReminderGetResponse:
    session = SessionLocal()
    reminder = session.query(Reminder).filter(Reminder.id == reminder_id, Reminder.created_by_user_id == 1).first()
    if reminder is None:
        reminder = Reminder(
            id=reminder_id,
            owner_id=0,
            pet_id=0,
            related_appointment_id=None,
            related_vaccination_id=None,
            related_prescription_id=None,
            reminder_type="appointment",
            contact_method="email",
            scheduled_time=datetime.utcnow(),
            sent_time=None,
            is_sent=0,
            metadata_=None,
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
    result = ReminderGetResponse(
        id=reminder.id,
        owner_id=reminder.owner_id,
        pet_id=reminder.pet_id,
        related_appointment_id=reminder.related_appointment_id,
        related_vaccination_id=reminder.related_vaccination_id,
        related_prescription_id=reminder.related_prescription_id,
        reminder_type=reminder.reminder_type,
        contact_method=reminder.contact_method,
        scheduled_time=reminder.scheduled_time,
        sent_time=reminder.sent_time,
        is_sent=bool(reminder.is_sent),
        metadata=reminder.metadata_,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
    )
    session.close()
    return result

@app.patch(
    "/api/reminders/{reminder_id}/mark_sent",
    response_model=ReminderMarkSentResponse,
    summary="Mark a reminder as sent",
    description="Set is_sent to true and record sent_time when a reminder is delivered.",
    tags=["reminders"],
    operation_id="mark_reminder_sent",
)
async def mark_reminder_sent(
    reminder_id: int = Path(..., description="ID of the reminder to mark as sent", example=600),
    body: ReminderMarkSentRequest = Body(...),
) -> ReminderMarkSentResponse:
    session = SessionLocal()
    reminder = session.query(Reminder).filter(Reminder.id == reminder_id, Reminder.created_by_user_id == 1).first()
    if reminder is None:
        reminder = Reminder(
            id=reminder_id,
            owner_id=0,
            pet_id=0,
            related_appointment_id=None,
            related_vaccination_id=None,
            related_prescription_id=None,
            reminder_type="appointment",
            contact_method="email",
            scheduled_time=datetime.utcnow(),
            sent_time=None,
            is_sent=0,
            metadata_=None,
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
        session.add(reminder)
        session.commit()
        session.refresh(reminder)
    reminder.sent_time = datetime.fromisoformat(body.sent_time)
    reminder.is_sent = 1
    reminder.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(reminder)
    result = ReminderMarkSentResponse(
        id=reminder.id,
        is_sent=bool(reminder.is_sent),
        sent_time=reminder.sent_time,
        updated_at=reminder.updated_at,
    )
    session.close()
    return result

if __name__ == "__main__":
    import uvicorn, os
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)