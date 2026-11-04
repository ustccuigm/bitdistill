from fastapi import FastAPI, Query, Path, Body, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Float, ForeignKey, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from datetime import datetime, date
import os

database_url = os.getenv("DATABASE_PATH", "sqlite:///outputs/databases/flowgate_b2b_payments_invoicing_network.db")
engine = create_engine("sqlite:////mnt/genming/training-local-cases-20261104/cases/b2b_payments_2_9/before/final.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    default_currency = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class OrganizationCustomer(Base):
    __tablename__ = "organization_customers"
    id = Column(Integer, primary_key=True)
    seller_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    buyer_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("seller_org_id", "buyer_org_id"),)

class CustomerContact(Base):
    __tablename__ = "customer_contacts"
    id = Column(Integer, primary_key=True)
    buyer_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    email = Column(String, nullable=False)
    is_primary = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True)
    line1 = Column(String, nullable=False)
    line2 = Column(String)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    country = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class OrganizationAddress(Base):
    __tablename__ = "organization_addresses"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    address_type = Column(String, nullable=False)
    is_primary = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class PaymentTerm(Base):
    __tablename__ = "payment_terms"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    net_days = Column(Integer, nullable=False)
    discount_percentage = Column(Float)
    discount_days = Column(Integer)
    applicable_currency = Column(String)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("org_id", "name"),)

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String, nullable=False)
    seller_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    buyer_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    currency = Column(String, nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_terms_id = Column(Integer, ForeignKey("payment_terms.id"))
    workflow_stage = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    open_balance = Column(Float, nullable=False, default=0.0)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("seller_org_id", "invoice_number"),)

class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    tax_rate = Column(Float, nullable=False, default=0.0)
    line_subtotal = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    line_total = Column(Float, nullable=False, default=0.0)
    approval_status = Column(String, nullable=False, default="pending")
    dispute_reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("invoice_id", "line_number"),)

class BankAccount(Base):
    __tablename__ = "bank_accounts"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    bank_account_code = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    bank_name = Column(String)
    account_number_masked = Column(String)
    routing_number_masked = Column(String)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("org_id", "bank_account_code"),)

class PaymentRequest(Base):
    __tablename__ = "payment_requests"
    id = Column(Integer, primary_key=True)
    payment_request_number = Column(String)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    vendor_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    buyer_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=False)
    requested_amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    payment_method = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    payment_id = Column(String, nullable=False)
    buyer_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    payer_bank_account_id = Column(Integer, ForeignKey("bank_accounts.id"))
    method = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    scheduled_date = Column(Date)
    total_amount = Column(Float, nullable=False)
    reconciliation_status = Column(String, nullable=False, default="unreconciled")
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("payment_id",),)

class RemittanceAdvice(Base):
    __tablename__ = "remittance_advices"
    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    allocated_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False, default=0.0)
    write_off_amount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class CreditNote(Base):
    __tablename__ = "credit_notes"
    id = Column(Integer, primary_key=True)
    credit_note_number = Column(String, nullable=False)
    seller_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    buyer_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    currency = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    remaining_amount = Column(Float, nullable=False)
    reason = Column(String)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("seller_org_id", "credit_note_number"),)

class CreditNoteApplication(Base):
    __tablename__ = "credit_note_applications"
    id = Column(Integer, primary_key=True)
    credit_note_id = Column(Integer, ForeignKey("credit_notes.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    applied_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FlowGate B2B Payments & Invoicing Network", version="1.0.0")

def get_db() -> Session:
    db = SessionLocal()
    return db

class OrganizationModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Organization primary key", example=2)
    name: str = Field(..., description="Organization legal name", example="Acme Retail LLC")
    default_currency: str = Field(..., description="Default ISO currency code used by this organization", example="USD")
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-12-01T10:15:30Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-12-10T08:22:11Z")

class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., description="Unique legal name of the organization", example="Acme Retail LLC")
    default_currency: str = Field(..., description="Default ISO currency code for this organization", example="USD")

class OrganizationListResponse(BaseModel):
    organizations: List[OrganizationModel] = Field(..., description="List of organizations", example=[])

class AddressModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Address primary key", example=10)
    line1: str = Field(..., description="Primary street address line", example="120 Market St")
    line2: Optional[str] = Field(None, description="Secondary address information", example="Suite 300")
    city: Optional[str] = Field(None, description="City or locality", example="Denver")
    state: Optional[str] = Field(None, description="State or region code", example="CO")
    postal_code: Optional[str] = Field(None, description="Postal or ZIP code", example="80202")
    country: str = Field(..., description="Country name or code", example="USA")
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-02T09:05:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-02T09:05:00Z")

class AddressCreateRequest(BaseModel):
    line1: str = Field(..., description="Primary street address line", example="120 Market St")
    line2: Optional[str] = Field(None, description="Secondary address information such as suite or floor", example="Suite 300")
    city: Optional[str] = Field(None, description="City or locality", example="Denver")
    state: Optional[str] = Field(None, description="State or region code", example="CO")
    postal_code: Optional[str] = Field(None, description="Postal or ZIP code", example="80202")
    country: str = Field(..., description="ISO country name or code", example="USA")

class OrganizationAddressModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Organization address link primary key", example=15)
    org_id: int = Field(..., description="Organization id", example=3)
    address_id: int = Field(..., description="Linked address id", example=10)
    address_type: str = Field(..., description="Address usage type for this organization", example="billing")
    is_primary: bool = Field(..., description="True if this is the primary address of this type", example=True)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-02T09:06:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-02T09:06:00Z")

class OrganizationAddressCreateRequest(BaseModel):
    org_id: int = Field(..., description="Organization id to which the address belongs", example=3)
    address_id: int = Field(..., description="Existing address id to link", example=10)
    address_type: str = Field(..., description="Type of address for the organization", example="billing")
    is_primary: Optional[bool] = Field(False, description="Mark this as the primary address for this type", example=True)

class CustomerContactModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Customer contact primary key", example=22)
    buyer_org_id: int = Field(..., description="Buyer organization id", example=5)
    email: str = Field(..., description="Contact email address", example="jane.doe@acmeretail.com")
    is_primary: bool = Field(..., description="True if this is the primary contact", example=True)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-02T09:07:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-02T09:07:00Z")

class CustomerContactCreateRequest(BaseModel):
    buyer_org_id: int = Field(..., description="Buyer organization id this contact belongs to", example=5)
    email: str = Field(..., description="Contact email address", example="jane.doe@acmeretail.com")
    is_primary: Optional[bool] = Field(False, description="Whether this contact should be primary for the buyer", example=True)

class OrganizationCustomerModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Organization customer link primary key", example=30)
    seller_org_id: int = Field(..., description="Seller organization id", example=1)
    buyer_org_id: int = Field(..., description="Buyer organization id", example=5)
    status: str = Field(..., description="Customer relationship status", example="active")
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-02T09:08:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-02T09:08:00Z")

class OrganizationCustomerCreateRequest(BaseModel):
    seller_org_id: int = Field(..., description="Organization id of the seller", example=1)
    buyer_org_id: int = Field(..., description="Organization id of the buyer organization", example=5)
    status: str = Field(..., description="Customer relationship status", example="active")

class PaymentTermModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Payment terms primary key", example=12)
    org_id: int = Field(..., description="Owning organization id", example=1)
    name: str = Field(..., description="Payment terms name", example="Net 45 with 2% 10, Net 30")
    description: Optional[str] = Field(None, description="Payment terms description", example="2% discount if paid within 10 days, net 45 standard")
    net_days: int = Field(..., description="Number of days to standard due date", example=45)
    discount_percentage: Optional[float] = Field(None, description="Early payment discount percent if any", example=2.0)
    discount_days: Optional[int] = Field(None, description="Early payment discount window in days", example=10)
    applicable_currency: Optional[str] = Field(None, description="Currency code this term applies to", example="USD")
    is_active: bool = Field(..., description="True if the terms are active", example=True)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-02T09:10:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-02T09:10:00Z")

class PaymentTermCreateRequest(BaseModel):
    org_id: int = Field(..., description="Owning organization id for these payment terms", example=1)
    name: str = Field(..., description="Unique payment terms name per organization", example="Net 45 with 2% 10, Net 30")
    description: Optional[str] = Field(None, description="Human-readable description of the payment terms", example="2% discount if paid within 10 days, net 45 standard")
    net_days: int = Field(..., description="Number of days from invoice_date to standard due date", example=45)
    discount_percentage: Optional[float] = Field(None, description="Early payment discount percentage if applicable", example=2.0)
    discount_days: Optional[int] = Field(None, description="Number of days for early payment discount to apply", example=10)
    applicable_currency: Optional[str] = Field(None, description="Currency code these terms apply to, null means all", example="USD")
    is_active: Optional[bool] = Field(True, description="Whether these payment terms are active and usable", example=True)

class PaymentTermListResponse(BaseModel):
    payment_terms: List[PaymentTermModel] = Field(..., description="List of payment terms", example=[])

class InvoiceModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Invoice primary key", example=1001)
    invoice_number: str = Field(..., description="Invoice number unique per seller", example="INV-2025-0142")
    seller_org_id: int = Field(..., description="Seller organization id", example=1)
    buyer_org_id: int = Field(..., description="Buyer organization id", example=5)
    currency: str = Field(..., description="Invoice currency code", example="USD")
    invoice_date: date = Field(..., description="Invoice date", example="2025-01-05")
    due_date: date = Field(..., description="Invoice due date", example="2025-02-04")
    payment_terms_id: Optional[int] = Field(None, description="Linked payment terms id if any", example=10)
    workflow_stage: str = Field(..., description="Current workflow stage", example="draft")
    total_amount: float = Field(..., description="Current total amount including tax from all line items", example=305.0)
    open_balance: float = Field(..., description="Current unpaid balance after credits and payments", example=305.0)
    created_by_user_id: Optional[int] = Field(None, description="Id of the user who created the invoice", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-02T09:15:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-02T09:15:00Z")

class InvoiceCreateRequest(BaseModel):
    invoice_number: str = Field(..., description="Unique invoice number per seller organization", example="INV-2025-0142")
    seller_org_id: int = Field(..., description="Seller organization id issuing the invoice", example=1)
    buyer_org_id: int = Field(..., description="Buyer organization id for this invoice", example=5)
    currency: str = Field(..., description="Invoice currency code", example="USD")
    invoice_date: date = Field(..., description="Invoice issue date in ISO format YYYY-MM-DD", example="2025-01-05")
    due_date: date = Field(..., description="Invoice due date in ISO format YYYY-MM-DD", example="2025-02-04")
    payment_terms_id: Optional[int] = Field(None, description="Optional payment_terms.id linked to this invoice", example=10)
    workflow_stage: str = Field(..., description="Workflow stage for the invoice lifecycle", example="draft")
    total_amount: Optional[float] = Field(0.0, description="Starting total amount", example=0.0)
    open_balance: Optional[float] = Field(0.0, description="Starting open balance", example=0.0)

class InvoiceWorkflowUpdateModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Invoice primary key", example=1001)
    invoice_number: str = Field(..., description="Invoice number", example="INV-2025-0110")
    workflow_stage: str = Field(..., description="Updated workflow_stage value", example="sent_to_buyer")
    updated_at: datetime = Field(..., description="Timestamp when workflow_stage was updated", example="2025-01-02T09:30:00Z")

class InvoiceWorkflowUpdateRequest(BaseModel):
    workflow_stage: str = Field(..., description="New workflow_stage value for the invoice", example="sent_to_buyer")

class InvoiceAmountsUpdateModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Invoice primary key", example=1001)
    invoice_number: str = Field(..., description="Invoice number", example="INV-2024-1201")
    total_amount: float = Field(..., description="Updated total_amount", example=7500.0)
    open_balance: float = Field(..., description="Updated open_balance", example=2000.0)
    updated_at: datetime = Field(..., description="Timestamp of the monetary update", example="2025-01-02T10:00:00Z")

class InvoiceAmountsUpdateRequest(BaseModel):
    total_amount: Optional[float] = Field(None, description="New total_amount for the invoice, if recalculated", example=5500.0)
    open_balance: Optional[float] = Field(None, description="New open_balance for the invoice after allocations", example=1500.0)

class InvoiceLineItemModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Line item primary key", example=2001)
    invoice_id: int = Field(..., description="Invoice primary key this line belongs to", example=1001)
    line_number: int = Field(..., description="Line sequence number", example=1)
    description: str = Field(..., description="Line description", example="Steel bolts M8")
    quantity: float = Field(..., description="Quantity ordered", example=500.0)
    unit_price: float = Field(..., description="Unit price", example=0.35)
    tax_rate: float = Field(..., description="Tax rate percentage", example=7.5)
    line_subtotal: float = Field(..., description="Quantity times unit_price", example=175.0)
    tax_amount: float = Field(..., description="Tax amount for this line", example=13.13)
    line_total: float = Field(..., description="Total for this line including tax", example=188.13)
    approval_status: str = Field(..., description="Current approval_status of the line", example="pending")
    dispute_reason: Optional[str] = Field(None, description="Dispute reason if line is disputed", example=None)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-02T09:40:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-02T09:40:00Z")

class InvoiceLineItemCreateRequest(BaseModel):
    line_number: int = Field(..., description="Sequential line number within the invoice", example=1)
    description: str = Field(..., description="Line item description", example="Steel bolts M8")
    quantity: float = Field(..., description="Quantity of items or units", example=500.0)
    unit_price: float = Field(..., description="Unit price in invoice currency", example=0.35)
    tax_rate: float = Field(..., description="Tax rate percentage applied to this line", example=7.5)
    line_subtotal: Optional[float] = Field(None, description="Precomputed quantity * unit_price, if client calculates", example=175.0)
    tax_amount: Optional[float] = Field(None, description="Precomputed tax_amount, if client calculates", example=13.13)
    line_total: Optional[float] = Field(None, description="Precomputed line_total, if client calculates", example=188.13)

class InvoiceLineItemListResponse(BaseModel):
    line_items: List[InvoiceLineItemModel] = Field(..., description="List of invoice line items", example=[])

class InvoiceLineItemApprovalUpdateModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Line item primary key", example=2005)
    invoice_id: int = Field(..., description="Invoice primary key", example=1042)
    line_number: int = Field(..., description="Line sequence number", example=3)
    description: str = Field(..., description="Line description", example="Custom machining surcharge")
    approval_status: str = Field(..., description="Updated approval_status", example="disputed")
    dispute_reason: Optional[str] = Field(None, description="Updated dispute_reason if any", example="Unapproved additional charge")
    updated_at: datetime = Field(..., description="Timestamp when the line was last updated", example="2025-01-10T12:00:00Z")

class InvoiceLineItemApprovalUpdateRequest(BaseModel):
    approval_status: str = Field(..., description="New approval_status value for this line", example="disputed")
    dispute_reason: Optional[str] = Field(None, description="Reason for dispute when marking a line as disputed", example="Unapproved additional charge")

class AgingBucketModel(BaseModel):
    bucket_name: str = Field(..., description="Label of the aging bucket", example="0-30")
    min_days_overdue: int = Field(..., description="Minimum days overdue in this bucket, inclusive", example=0)
    max_days_overdue: Optional[int] = Field(None, description="Maximum days overdue in this bucket, inclusive, null for open-ended", example=30)
    total_open_balance: float = Field(..., description="Sum of open_balance of invoices in this bucket", example=125000.5)

class ReceivablesAgingResponse(BaseModel):
    seller_org_id: int = Field(..., description="Seller organization id for this report", example=1)
    currency: str = Field(..., description="Currency code used in this report", example="USD")
    as_of_date: date = Field(..., description="Reference date used for aging calculation", example="2025-03-01")
    buckets: List[AgingBucketModel] = Field(..., description="Aging buckets with totals", example=[])

class BankAccountModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Bank account primary key", example=7)
    org_id: int = Field(..., description="Organization id that owns the account", example=1)
    bank_account_code: str = Field(..., description="Short code used in API calls to reference this account", example="BA-PRIMARY-USD")
    currency: str = Field(..., description="Currency supported by this bank account", example="USD")
    bank_name: Optional[str] = Field(None, description="Name of the bank", example="First National Bank")
    account_number_masked: Optional[str] = Field(None, description="Masked bank account number for display", example="****5678")
    routing_number_masked: Optional[str] = Field(None, description="Masked routing number for display", example="*****123")
    is_active: bool = Field(..., description="True if the bank account is active", example=True)
    created_at: datetime = Field(..., description="Creation timestamp", example="2024-07-01T09:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2024-08-01T09:00:00Z")

class BankAccountListResponse(BaseModel):
    bank_accounts: List[BankAccountModel] = Field(..., description="List of bank accounts", example=[])

class PaymentRequestModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Payment request primary key", example=3001)
    payment_request_number: Optional[str] = Field(None, description="Payment request number if provided", example="PR-2025-00015")
    invoice_id: int = Field(..., description="Related invoice primary key", example=1010)
    vendor_org_id: int = Field(..., description="Vendor organization id", example=1)
    buyer_org_id: int = Field(..., description="Buyer organization id", example=5)
    bank_account_id: int = Field(..., description="Bank account id for payment receipt", example=7)
    requested_amount: float = Field(..., description="Requested payment amount", example=2500.0)
    currency: str = Field(..., description="Currency used for this payment request", example="USD")
    scheduled_date: date = Field(..., description="Requested payment date", example="2025-01-20")
    payment_method: str = Field(..., description="Payment method such as ACH or wire", example="ACH")
    status: str = Field(..., description="Current payment request status", example="pending")
    created_by_user_id: Optional[int] = Field(None, description="User who created the payment request", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-02T10:15:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-02T10:15:00Z")

class PaymentRequestCreateRequest(BaseModel):
    payment_request_number: Optional[str] = Field(None, description="Optional externally visible payment request number", example="PR-2025-00015")
    invoice_id: int = Field(..., description="Invoice primary key this payment request relates to", example=1010)
    vendor_org_id: int = Field(..., description="Vendor organization id initiating the request", example=1)
    buyer_org_id: int = Field(..., description="Buyer organization id expected to pay", example=5)
    bank_account_id: int = Field(..., description="Bank account id where funds should be received", example=7)
    requested_amount: float = Field(..., description="Amount requested for payment", example=2500.0)
    currency: str = Field(..., description="Currency of the payment request", example="USD")
    scheduled_date: date = Field(..., description="Requested payment date YYYY-MM-DD", example="2025-01-20")
    payment_method: str = Field(..., description="Expected payment method type", example="ACH")
    status: Optional[str] = Field("pending", description="Initial status of the payment request", example="pending")

class PaymentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Payment primary key", example=4001)
    payment_id: str = Field(..., description="External payment identifier", example="PMT-2025-00077")
    buyer_org_id: int = Field(..., description="Buyer organization id", example=5)
    payer_bank_account_id: Optional[int] = Field(None, description="Payer bank account id if any", example=None)
    method: str = Field(..., description="Payment method used", example="wire")
    currency: str = Field(..., description="Payment currency code", example="USD")
    scheduled_date: Optional[date] = Field(None, description="Scheduled payment date", example="2025-01-22")
    total_amount: float = Field(..., description="Total payment amount", example=12500.0)
    reconciliation_status: str = Field(..., description="Current reconciliation status", example="unreconciled")
    created_by_user_id: Optional[int] = Field(None, description="User who created the payment record", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-02T10:20:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-02T10:20:00Z")

class PaymentCreateRequest(BaseModel):
    payment_id: str = Field(..., description="External unique payment identifier", example="PMT-2025-00077")
    buyer_org_id: int = Field(..., description="Buyer organization that is paying", example=5)
    payer_bank_account_id: Optional[int] = Field(None, description="Optional payer bank account id if stored", example=None)
    method: str = Field(..., description="Payment method code such as wire or ACH", example="wire")
    currency: str = Field(..., description="Payment currency code", example="USD")
    scheduled_date: Optional[date] = Field(None, description="Scheduled or expected settlement date YYYY-MM-DD", example="2025-01-22")
    total_amount: float = Field(..., description="Total payment amount", example=12500.0)
    reconciliation_status: Optional[str] = Field("unreconciled", description="Initial reconciliation status", example="unreconciled")

class PaymentReconciliationUpdateModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Payment primary key", example=4001)
    payment_id: str = Field(..., description="External payment identifier", example="PMT-2025-00077")
    reconciliation_status: str = Field(..., description="Updated reconciliation_status value", example="reconciled")
    updated_at: datetime = Field(..., description="Timestamp when reconciliation_status was updated", example="2025-01-25T12:00:00Z")

class PaymentReconciliationUpdateRequest(BaseModel):
    reconciliation_status: str = Field(..., description="New reconciliation_status value", example="reconciled")

class RemittanceAdviceModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Remittance advice primary key", example=5001)
    payment_id: int = Field(..., description="Payment primary key used for this allocation", example=4001)
    invoice_id: int = Field(..., description="Invoice primary key receiving the allocation", example=9001)
    allocated_amount: float = Field(..., description="Allocated amount applied to the invoice", example=8000.0)
    discount_amount: float = Field(..., description="Discount amount associated with this allocation", example=160.0)
    write_off_amount: float = Field(..., description="Write-off amount associated with this allocation", example=0.0)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-25T11:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-25T11:00:00Z")

class RemittanceAdviceCreateRequest(BaseModel):
    payment_id: int = Field(..., description="Payment internal id this allocation uses", example=4001)
    invoice_id: int = Field(..., description="Invoice internal id receiving the allocation", example=9001)
    allocated_amount: float = Field(..., description="Amount from the payment applied to this invoice", example=8000.0)
    discount_amount: Optional[float] = Field(0.0, description="Discount applied as part of this payment", example=160.0)
    write_off_amount: Optional[float] = Field(0.0, description="Amount written off and not expected to be collected", example=40.0)

class CreditNoteModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Credit note primary key", example=6001)
    credit_note_number: str = Field(..., description="Credit note number", example="CN-2025-0003")
    seller_org_id: int = Field(..., description="Seller organization id", example=1)
    buyer_org_id: int = Field(..., description="Buyer organization id", example=5)
    currency: str = Field(..., description="Currency of the credit note", example="USD")
    total_amount: float = Field(..., description="Total credit note amount", example=750.0)
    remaining_amount: float = Field(..., description="Unapplied credit amount still available", example=750.0)
    reason: Optional[str] = Field(None, description="Reason for the credit", example="Volume rebate Q4 2024")
    created_by_user_id: Optional[int] = Field(None, description="User who created the credit note", example=1)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-02T10:30:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-02T10:30:00Z")

class CreditNoteCreateRequest(BaseModel):
    credit_note_number: str = Field(..., description="Unique credit note number per seller organization", example="CN-2025-0003")
    seller_org_id: int = Field(..., description="Seller organization issuing the credit note", example=1)
    buyer_org_id: int = Field(..., description="Buyer organization receiving the credit", example=5)
    currency: str = Field(..., description="Currency of the credit note", example="USD")
    total_amount: float = Field(..., description="Total credit amount granted", example=750.0)
    remaining_amount: float = Field(..., description="Remaining amount that can still be applied", example=750.0)
    reason: Optional[str] = Field(None, description="Reason for issuing the credit note", example="Volume rebate Q4 2024")

class CreditNoteApplicationModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Credit note application primary key", example=7001)
    credit_note_id: int = Field(..., description="Credit note primary key", example=6001)
    invoice_id: int = Field(..., description="Invoice primary key", example=8001)
    applied_amount: float = Field(..., description="Amount of credit applied to this invoice", example=500.0)
    created_at: datetime = Field(..., description="Creation timestamp", example="2025-01-02T11:00:00Z")
    updated_at: datetime = Field(..., description="Last update timestamp", example="2025-01-02T11:00:00Z")

class CreditNoteApplicationCreateRequest(BaseModel):
    credit_note_id: int = Field(..., description="Credit note primary key being applied", example=6001)
    invoice_id: int = Field(..., description="Invoice primary key receiving the credit", example=8001)
    applied_amount: float = Field(..., description="Amount of the credit_note applied to this invoice", example=500.0)

class CreditNoteRemainingUpdateModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Credit note primary key", example=6001)
    credit_note_number: str = Field(..., description="Credit note number", example="CN-2025-0003")
    remaining_amount: float = Field(..., description="Updated remaining_amount", example=0.0)
    updated_at: datetime = Field(..., description="Timestamp when remaining_amount was updated", example="2025-01-02T11:05:00Z")

class CreditNoteRemainingUpdateRequest(BaseModel):
    remaining_amount: float = Field(..., description="New remaining_amount value for this credit note", example=0.0)

class PaymentListResponse(BaseModel):
    payments: List[PaymentModel] = Field(..., description="List of payments", example=[])

class PaymentTermSingleResponse(BaseModel):
    payment_term: PaymentTermModel = Field(..., description="Payment term", example={})

@app.get(
    "/api/organizations",
    response_model=OrganizationListResponse,
    summary="List organizations with optional name filter",
    description="List organizations optionally filtered by name substring with pagination",
    tags=["organizations"],
    operation_id="list_organizations",
)
async def list_organizations(
    name: Optional[str] = Query(None, description="Optional case-insensitive substring match on organization name", example="Acme Retail"),
    limit: Optional[int] = Query(50, description="Maximum number of organizations to return", example=50),
    offset: Optional[int] = Query(0, description="Number of organizations to skip for pagination", example=0),
    db: Session = Depends(get_db),
) -> OrganizationListResponse:
    query = db.query(Organization)
    if name is not None:
        like_value = f"%{name}%"
        query = query.filter(Organization.name.ilike(like_value))
    query = query.order_by(Organization.id).offset(offset).limit(limit)
    organizations = query.all()
    db.close()
    return OrganizationListResponse(organizations=organizations)

@app.post(
    "/api/organizations",
    response_model=OrganizationModel,
    summary="Create a new organization",
    description="Create a new organization with a default currency",
    tags=["organizations"],
    operation_id="create_organization",
)
async def create_organization(
    body: OrganizationCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> OrganizationModel:
    now = datetime.utcnow()
    org = Organization(
        name=body.name,
        default_currency=body.default_currency,
        created_at=now,
        updated_at=now,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    db.close()
    return org

@app.post(
    "/api/addresses",
    response_model=AddressModel,
    summary="Create a postal address record",
    description="Create a reusable postal address row",
    tags=["addresses"],
    operation_id="create_address",
)
async def create_address(
    body: AddressCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> AddressModel:
    now = datetime.utcnow()
    addr = Address(
        line1=body.line1,
        line2=body.line2,
        city=body.city,
        state=body.state,
        postal_code=body.postal_code,
        country=body.country,
        created_at=now,
        updated_at=now,
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)
    db.close()
    return addr

@app.post(
    "/api/organization-addresses",
    response_model=OrganizationAddressModel,
    summary="Link an address to an organization",
    description="Associate an existing address with an organization",
    tags=["organizations", "addresses"],
    operation_id="create_organization_address",
)
async def create_organization_address(
    body: OrganizationAddressCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> OrganizationAddressModel:
    now = datetime.utcnow()
    is_primary_int = 1 if body.is_primary else 0
    org_addr = OrganizationAddress(
        org_id=body.org_id,
        address_id=body.address_id,
        address_type=body.address_type,
        is_primary=is_primary_int,
        created_at=now,
        updated_at=now,
    )
    db.add(org_addr)
    db.commit()
    db.refresh(org_addr)
    db.close()
    result = OrganizationAddress(
        id=org_addr.id,
        org_id=org_addr.org_id,
        address_id=org_addr.address_id,
        address_type=org_addr.address_type,
        is_primary=org_addr.is_primary,
        created_at=org_addr.created_at,
        updated_at=org_addr.updated_at,
    )
    return result

@app.post(
    "/api/customer-contacts",
    response_model=CustomerContactModel,
    summary="Create a customer contact for an organization",
    description="Register a contact email for a buyer organization",
    tags=["customer_contacts"],
    operation_id="create_customer_contact",
)
async def create_customer_contact(
    body: CustomerContactCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> CustomerContactModel:
    now = datetime.utcnow()
    is_primary_int = 1 if body.is_primary else 0
    contact = CustomerContact(
        buyer_org_id=body.buyer_org_id,
        email=body.email,
        is_primary=is_primary_int,
        created_at=now,
        updated_at=now,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    db.close()
    return contact

@app.post(
    "/api/organization-customers",
    response_model=OrganizationCustomerModel,
    summary="Create a seller-buyer customer relationship",
    description="Link a seller organization to a buyer organization",
    tags=["organization_customers"],
    operation_id="create_organization_customer",
)
async def create_organization_customer(
    body: OrganizationCustomerCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> OrganizationCustomerModel:
    now = datetime.utcnow()
    org_cust = OrganizationCustomer(
        seller_org_id=body.seller_org_id,
        buyer_org_id=body.buyer_org_id,
        status=body.status,
        created_at=now,
        updated_at=now,
    )
    db.add(org_cust)
    db.commit()
    db.refresh(org_cust)
    db.close()
    return org_cust

@app.post(
    "/api/payment-terms",
    response_model=PaymentTermModel,
    summary="Create payment terms for an organization",
    description="Create payment terms like Net 30 or early payment discounts",
    tags=["payment_terms"],
    operation_id="create_payment_terms",
)
async def create_payment_terms(
    body: PaymentTermCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> PaymentTermModel:
    now = datetime.utcnow()
    is_active_int = 1 if (body.is_active is None or body.is_active) else 0
    pt = PaymentTerm(
        org_id=body.org_id,
        name=body.name,
        description=body.description,
        net_days=body.net_days,
        discount_percentage=body.discount_percentage,
        discount_days=body.discount_days,
        applicable_currency=body.applicable_currency,
        is_active=is_active_int,
        created_at=now,
        updated_at=now,
    )
    db.add(pt)
    db.commit()
    db.refresh(pt)
    db.close()
    return pt

@app.get(
    "/api/payment-terms",
    response_model=PaymentTermListResponse,
    summary="List payment terms for an organization",
    description="Search payment terms by organization, name, and currency",
    tags=["payment_terms"],
    operation_id="list_payment_terms",
)
async def list_payment_terms(
    org_id: int = Query(..., description="Owning organization id to filter payment terms", example=1),
    name: Optional[str] = Query(None, description="Optional exact name filter for payment terms", example="Net 30"),
    applicable_currency: Optional[str] = Query(None, description="Optional currency code filter", example="USD"),
    is_active: Optional[bool] = Query(None, description="Filter by active status if provided", example=True),
    db: Session = Depends(get_db),
) -> PaymentTermListResponse:
    query = db.query(PaymentTerm).filter(PaymentTerm.org_id == org_id)
    if name is not None:
        query = query.filter(PaymentTerm.name == name)
    if applicable_currency is not None:
        query = query.filter(PaymentTerm.applicable_currency == applicable_currency)
    if is_active is not None:
        active_int = 1 if is_active else 0
        query = query.filter(PaymentTerm.is_active == active_int)
    items = query.order_by(PaymentTerm.id).all()
    db.close()
    return PaymentTermListResponse(payment_terms=items)

@app.post(
    "/api/invoices",
    response_model=InvoiceModel,
    summary="Create a new invoice header",
    description="Create the invoice header row without line items",
    tags=["invoices"],
    operation_id="create_invoice",
)
async def create_invoice(
    body: InvoiceCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> InvoiceModel:
    now = datetime.utcnow()
    created_by_user_id = 1
    total_amount_value = body.total_amount if body.total_amount is not None else 0.0
    open_balance_value = body.open_balance if body.open_balance is not None else 0.0
    inv = Invoice(
        invoice_number=body.invoice_number,
        seller_org_id=body.seller_org_id,
        buyer_org_id=body.buyer_org_id,
        currency=body.currency,
        invoice_date=body.invoice_date,
        due_date=body.due_date,
        payment_terms_id=body.payment_terms_id,
        workflow_stage=body.workflow_stage,
        total_amount=total_amount_value,
        open_balance=open_balance_value,
        created_by_user_id=created_by_user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    db.close()
    return inv

@app.get(
    "/api/invoices/{invoice_id}",
    response_model=InvoiceModel,
    summary="Get an invoice by id",
    description="Retrieve full invoice header details by internal invoice id",
    tags=["invoices"],
    operation_id="get_invoice_by_id",
)
async def get_invoice_by_id(
    invoice_id: int = Path(..., description="Internal invoice primary key", example=1001),
    db: Session = Depends(get_db),
) -> InvoiceModel:
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    db.close()
    return inv

@app.get(
    "/api/invoices/by-number",
    response_model=InvoiceModel,
    summary="Get an invoice by seller and invoice_number",
    description="Look up an invoice using seller_org_id and invoice_number",
    tags=["invoices"],
    operation_id="get_invoice_by_number",
)
async def get_invoice_by_number(
    seller_org_id: int = Query(..., description="Seller organization id that owns the invoice number", example=1),
    invoice_number: str = Query(..., description="Invoice number within the seller org", example="INV-2025-0142"),
    db: Session = Depends(get_db),
) -> InvoiceModel:
    inv = db.query(Invoice).filter(Invoice.seller_org_id == seller_org_id, Invoice.invoice_number == invoice_number).first()
    db.close()
    return inv

@app.patch(
    "/api/invoices/{invoice_id}/workflow-stage",
    response_model=InvoiceWorkflowUpdateModel,
    summary="Update invoice workflow_stage only",
    description="Transition an invoice to a new workflow_stage",
    tags=["invoices"],
    operation_id="update_invoice_workflow_stage",
)
async def update_invoice_workflow_stage(
    invoice_id: int = Path(..., description="Invoice primary key to update", example=1001),
    body: InvoiceWorkflowUpdateRequest = Body(...),
    db: Session = Depends(get_db),
) -> InvoiceWorkflowUpdateModel:
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    now = datetime.utcnow()
    inv.workflow_stage = body.workflow_stage
    inv.updated_at = now
    db.commit()
    db.refresh(inv)
    db.close()
    return InvoiceWorkflowUpdateModel(
        id=inv.id,
        invoice_number=inv.invoice_number,
        workflow_stage=inv.workflow_stage,
        updated_at=inv.updated_at,
    )

@app.patch(
    "/api/invoices/{invoice_id}/amounts",
    response_model=InvoiceAmountsUpdateModel,
    summary="Update invoice total_amount and open_balance",
    description="Adjust invoice monetary amounts after changes",
    tags=["invoices"],
    operation_id="update_invoice_amounts",
)
async def update_invoice_amounts(
    invoice_id: int = Path(..., description="Invoice primary key", example=1001),
    body: InvoiceAmountsUpdateRequest = Body(...),
    db: Session = Depends(get_db),
) -> InvoiceAmountsUpdateModel:
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    now = datetime.utcnow()
    if body.total_amount is not None:
        inv.total_amount = body.total_amount
    if body.open_balance is not None:
        inv.open_balance = body.open_balance
    inv.updated_at = now
    db.commit()
    db.refresh(inv)
    db.close()
    return InvoiceAmountsUpdateModel(
        id=inv.id,
        invoice_number=inv.invoice_number,
        total_amount=inv.total_amount,
        open_balance=inv.open_balance,
        updated_at=inv.updated_at,
    )

@app.post(
    "/api/invoices/{invoice_id}/line-items",
    response_model=InvoiceLineItemModel,
    summary="Add a line item to an invoice",
    description="Append a single line item to an existing invoice",
    tags=["invoice_line_items"],
    operation_id="create_invoice_line_item",
)
async def create_invoice_line_item(
    invoice_id: int = Path(..., description="Invoice id this line will belong to", example=1001),
    body: InvoiceLineItemCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> InvoiceLineItemModel:
    now = datetime.utcnow()
    line_subtotal_value = body.line_subtotal
    if line_subtotal_value is None:
        line_subtotal_value = body.quantity * body.unit_price
    tax_amount_value = body.tax_amount
    if tax_amount_value is None:
        tax_amount_value = line_subtotal_value * body.tax_rate / 100.0
    line_total_value = body.line_total
    if line_total_value is None:
        line_total_value = line_subtotal_value + tax_amount_value
    li = InvoiceLineItem(
        invoice_id=invoice_id,
        line_number=body.line_number,
        description=body.description,
        quantity=body.quantity,
        unit_price=body.unit_price,
        tax_rate=body.tax_rate,
        line_subtotal=line_subtotal_value,
        tax_amount=tax_amount_value,
        line_total=line_total_value,
        approval_status="pending",
        dispute_reason=None,
        created_at=now,
        updated_at=now,
    )
    db.add(li)
    db.commit()
    db.refresh(li)
    db.close()
    return li

@app.get(
    "/api/invoices/{invoice_id}/line-items",
    response_model=InvoiceLineItemListResponse,
    summary="List line items for an invoice",
    description="Fetch all line items for an invoice",
    tags=["invoice_line_items"],
    operation_id="list_invoice_line_items",
)
async def list_invoice_line_items(
    invoice_id: int = Path(..., description="Invoice primary key whose lines to fetch", example=1001),
    db: Session = Depends(get_db),
) -> InvoiceLineItemListResponse:
    items = db.query(InvoiceLineItem).filter(InvoiceLineItem.invoice_id == invoice_id).order_by(InvoiceLineItem.line_number).all()
    db.close()
    return InvoiceLineItemListResponse(line_items=items)

@app.patch(
    "/api/invoice-line-items/{line_item_id}/approval",
    response_model=InvoiceLineItemApprovalUpdateModel,
    summary="Update line item approval_status and dispute_reason",
    description="Approve or dispute line items while setting dispute_reason",
    tags=["invoice_line_items"],
    operation_id="update_invoice_line_item_approval",
)
async def update_invoice_line_item_approval(
    line_item_id: int = Path(..., description="Invoice line item primary key", example=2005),
    body: InvoiceLineItemApprovalUpdateRequest = Body(...),
    db: Session = Depends(get_db),
) -> InvoiceLineItemApprovalUpdateModel:
    li = db.query(InvoiceLineItem).filter(InvoiceLineItem.id == line_item_id).first()
    now = datetime.utcnow()
    li.approval_status = body.approval_status
    li.dispute_reason = body.dispute_reason
    li.updated_at = now
    db.commit()
    db.refresh(li)
    db.close()
    return InvoiceLineItemApprovalUpdateModel(
        id=li.id,
        invoice_id=li.invoice_id,
        line_number=li.line_number,
        description=li.description,
        approval_status=li.approval_status,
        dispute_reason=li.dispute_reason,
        updated_at=li.updated_at,
    )

@app.get(
    "/api/reports/receivables-aging",
    response_model=ReceivablesAgingResponse,
    summary="Get receivables aging buckets for an organization",
    description="Compute open receivables grouped into aging buckets",
    tags=["reports", "invoices"],
    operation_id="get_receivables_aging",
)
async def get_receivables_aging(
    seller_org_id: int = Query(..., description="Seller organization id whose receivables to analyze", example=1),
    as_of_date: date = Query(..., description="Cutoff date YYYY-MM-DD to compute aging", example="2025-03-01"),
    currency: str = Query(..., description="Currency code to include in the report", example="USD"),
    db: Session = Depends(get_db),
) -> ReceivablesAgingResponse:
    invoices = db.query(Invoice).filter(
        Invoice.seller_org_id == seller_org_id,
        Invoice.currency == currency,
        Invoice.open_balance > 0.0,
    ).all()
    bucket_defs = [
        ("0-30", 0, 30),
        ("31-60", 31, 60),
        ("61-90", 61, 90),
        (">90", 91, None),
    ]
    bucket_totals: Dict[str, float] = {}
    for name, _, _ in bucket_defs:
        bucket_totals[name] = 0.0
    for inv in invoices:
        days_overdue = (as_of_date - inv.due_date).days
        if days_overdue < 0:
            bucket_name = "0-30"
        elif days_overdue <= 30:
            bucket_name = "0-30"
        elif days_overdue <= 60:
            bucket_name = "31-60"
        elif days_overdue <= 90:
            bucket_name = "61-90"
        else:
            bucket_name = ">90"
        bucket_totals[bucket_name] = bucket_totals[bucket_name] + inv.open_balance
    buckets: List[AgingBucketModel] = []
    for name, min_days, max_days in bucket_defs:
        total = bucket_totals[name]
        buckets.append(
            AgingBucketModel(
                bucket_name=name,
                min_days_overdue=min_days,
                max_days_overdue=max_days,
                total_open_balance=total,
            )
        )
    db.close()
    return ReceivablesAgingResponse(
        seller_org_id=seller_org_id,
        currency=currency,
        as_of_date=as_of_date,
        buckets=buckets,
    )

@app.get(
    "/api/bank-accounts",
    response_model=BankAccountListResponse,
    summary="List bank accounts for an organization",
    description="Fetch active bank accounts for an organization",
    tags=["bank_accounts"],
    operation_id="list_bank_accounts",
)
async def list_bank_accounts(
    org_id: int = Query(..., description="Organization id that owns the bank accounts", example=1),
    bank_account_code: Optional[str] = Query(None, description="Optional code filter to get a single bank account", example="BA-PRIMARY-USD"),
    is_active: Optional[bool] = Query(None, description="Filter by active status when provided", example=True),
    db: Session = Depends(get_db),
) -> BankAccountListResponse:
    query = db.query(BankAccount).filter(BankAccount.org_id == org_id)
    if bank_account_code is not None:
        query = query.filter(BankAccount.bank_account_code == bank_account_code)
    if is_active is not None:
        active_int = 1 if is_active else 0
        query = query.filter(BankAccount.is_active == active_int)
    accounts = query.order_by(BankAccount.id).all()
    db.close()
    return BankAccountListResponse(bank_accounts=accounts)

@app.post(
    "/api/payment-requests",
    response_model=PaymentRequestModel,
    summary="Create a payment request for an invoice",
    description="Create a payment request for a specific invoice",
    tags=["payment_requests"],
    operation_id="create_payment_request",
)
async def create_payment_request(
    body: PaymentRequestCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> PaymentRequestModel:
    now = datetime.utcnow()
    created_by_user_id = 1
    pr = PaymentRequest(
        payment_request_number=body.payment_request_number,
        invoice_id=body.invoice_id,
        vendor_org_id=body.vendor_org_id,
        buyer_org_id=body.buyer_org_id,
        bank_account_id=body.bank_account_id,
        requested_amount=body.requested_amount,
        currency=body.currency,
        scheduled_date=body.scheduled_date,
        payment_method=body.payment_method,
        status=body.status if body.status is not None else "pending",
        created_by_user_id=created_by_user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    db.close()
    return pr

@app.post(
    "/api/payments",
    response_model=PaymentModel,
    summary="Create or record a payment metadata entry",
    description="Record inbound payments with metadata and status",
    tags=["payments"],
    operation_id="create_payment",
)
async def create_payment(
    body: PaymentCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> PaymentModel:
    now = datetime.utcnow()
    created_by_user_id = 1
    pay = Payment(
        payment_id=body.payment_id,
        buyer_org_id=body.buyer_org_id,
        payer_bank_account_id=body.payer_bank_account_id,
        method=body.method,
        currency=body.currency,
        scheduled_date=body.scheduled_date,
        total_amount=body.total_amount,
        reconciliation_status=body.reconciliation_status if body.reconciliation_status is not None else "unreconciled",
        created_by_user_id=created_by_user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(pay)
    db.commit()
    db.refresh(pay)
    db.close()
    return pay

@app.get(
    "/api/payments/by-payment-id",
    response_model=PaymentModel,
    summary="Get payment by external payment_id",
    description="Retrieve a payment row using the external payment_id string",
    tags=["payments"],
    operation_id="get_payment_by_payment_id",
)
async def get_payment_by_payment_id(
    payment_id: str = Query(..., description="External payment identifier to look up", example="PMT-2025-00077"),
    db: Session = Depends(get_db),
) -> PaymentModel:
    pay = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    db.close()
    return pay

@app.patch(
    "/api/payments/{id}/reconciliation-status",
    response_model=PaymentReconciliationUpdateModel,
    summary="Update payment reconciliation_status",
    description="Mark a payment as partially_reconciled or reconciled",
    tags=["payments"],
    operation_id="update_payment_reconciliation_status",
)
async def update_payment_reconciliation_status(
    id: int = Path(..., description="Payment internal primary key", example=4001),
    body: PaymentReconciliationUpdateRequest = Body(...),
    db: Session = Depends(get_db),
) -> PaymentReconciliationUpdateModel:
    pay = db.query(Payment).filter(Payment.id == id).first()
    now = datetime.utcnow()
    pay.reconciliation_status = body.reconciliation_status
    pay.updated_at = now
    db.commit()
    db.refresh(pay)
    db.close()
    return PaymentReconciliationUpdateModel(
        id=pay.id,
        payment_id=pay.payment_id,
        reconciliation_status=pay.reconciliation_status,
        updated_at=pay.updated_at,
    )

@app.post(
    "/api/remittance-advices",
    response_model=RemittanceAdviceModel,
    summary="Create a remittance advice allocation",
    description="Allocate a portion of a payment to an invoice",
    tags=["remittance_advices"],
    operation_id="create_remittance_advice",
)
async def create_remittance_advice(
    body: RemittanceAdviceCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> RemittanceAdviceModel:
    now = datetime.utcnow()
    discount_amount_value = body.discount_amount if body.discount_amount is not None else 0.0
    write_off_amount_value = body.write_off_amount if body.write_off_amount is not None else 0.0
    ra = RemittanceAdvice(
        payment_id=body.payment_id,
        invoice_id=body.invoice_id,
        allocated_amount=body.allocated_amount,
        discount_amount=discount_amount_value,
        write_off_amount=write_off_amount_value,
        created_at=now,
        updated_at=now,
    )
    db.add(ra)
    db.commit()
    db.refresh(ra)
    db.close()
    return ra

@app.post(
    "/api/credit-notes",
    response_model=CreditNoteModel,
    summary="Create a credit note for a buyer",
    description="Issue a credit note from a seller to a buyer",
    tags=["credit_notes"],
    operation_id="create_credit_note",
)
async def create_credit_note(
    body: CreditNoteCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> CreditNoteModel:
    now = datetime.utcnow()
    created_by_user_id = 1
    cn = CreditNote(
        credit_note_number=body.credit_note_number,
        seller_org_id=body.seller_org_id,
        buyer_org_id=body.buyer_org_id,
        currency=body.currency,
        total_amount=body.total_amount,
        remaining_amount=body.remaining_amount,
        reason=body.reason,
        created_by_user_id=created_by_user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(cn)
    db.commit()
    db.refresh(cn)
    db.close()
    return cn

@app.get(
    "/api/credit-notes/by-number",
    response_model=CreditNoteModel,
    summary="Get credit note by seller and credit_note_number",
    description="Fetch a specific credit note by seller_org_id and number",
    tags=["credit_notes"],
    operation_id="get_credit_note_by_number",
)
async def get_credit_note_by_number(
    seller_org_id: int = Query(..., description="Seller organization id that owns the credit note", example=1),
    credit_note_number: str = Query(..., description="Credit note number to look up", example="CN-2025-0003"),
    db: Session = Depends(get_db),
) -> CreditNoteModel:
    cn = db.query(CreditNote).filter(
        CreditNote.seller_org_id == seller_org_id,
        CreditNote.credit_note_number == credit_note_number,
    ).first()
    db.close()
    return cn

@app.post(
    "/api/credit-note-applications",
    response_model=CreditNoteApplicationModel,
    summary="Apply a credit note amount to an invoice",
    description="Apply part of a credit note to an invoice",
    tags=["credit_note_applications"],
    operation_id="create_credit_note_application",
)
async def create_credit_note_application(
    body: CreditNoteApplicationCreateRequest = Body(...),
    db: Session = Depends(get_db),
) -> CreditNoteApplicationModel:
    now = datetime.utcnow()
    cna = CreditNoteApplication(
        credit_note_id=body.credit_note_id,
        invoice_id=body.invoice_id,
        applied_amount=body.applied_amount,
        created_at=now,
        updated_at=now,
    )
    db.add(cna)
    db.commit()
    db.refresh(cna)
    db.close()
    return cna

@app.patch(
    "/api/credit-notes/{id}/remaining-amount",
    response_model=CreditNoteRemainingUpdateModel,
    summary="Update credit note remaining_amount",
    description="Decrease remaining_amount on a credit note after applications",
    tags=["credit_notes"],
    operation_id="update_credit_note_remaining_amount",
)
async def update_credit_note_remaining_amount(
    id: int = Path(..., description="Credit note primary key", example=6001),
    body: CreditNoteRemainingUpdateRequest = Body(...),
    db: Session = Depends(get_db),
) -> CreditNoteRemainingUpdateModel:
    cn = db.query(CreditNote).filter(CreditNote.id == id).first()
    now = datetime.utcnow()
    cn.remaining_amount = body.remaining_amount
    cn.updated_at = now
    db.commit()
    db.refresh(cn)
    db.close()
    return CreditNoteRemainingUpdateModel(
        id=cn.id,
        credit_note_number=cn.credit_note_number,
        remaining_amount=cn.remaining_amount,
        updated_at=cn.updated_at,
    )

if __name__ == "__main__":
    import uvicorn, os
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)