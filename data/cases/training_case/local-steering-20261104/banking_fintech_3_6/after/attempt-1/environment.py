from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
import os
from datetime import datetime

database_url = os.getenv("DATABASE_PATH", "sqlite:///outputs/databases/chime.db")
engine = create_engine("sqlite:////mnt/genming/training-local-cases-20261104/cases/banking_fintech_3_6/after/attempt-1/final.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Chime-like API", version="1.0.0")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    profile_json = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    is_primary = Column(Integer, nullable=False, default=0)
    balance_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String, nullable=False, default="USD")
    status = Column(String, nullable=False, default="open")
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class DebitCard(Base):
    __tablename__ = "debit_cards"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    last4 = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    is_default_for_debit = Column(Integer, nullable=False, default=0)
    physical_card = Column(Integer, nullable=False, default=1)
    expiration_month = Column(Integer)
    expiration_year = Column(Integer)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class CardReplacementRequest(Base):
    __tablename__ = "card_replacement_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_card_id = Column(Integer, ForeignKey("debit_cards.id"), nullable=False)
    replacement_card_id = Column(Integer, ForeignKey("debit_cards.id"))
    mail_to_address_id = Column(Integer)
    reason = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")
    requested_at = Column(DateTime, server_default=func.current_timestamp())
    processed_at = Column(DateTime)


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey("categories.id"))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    description = Column(Text)
    merchant_name = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id"))
    related_card_id = Column(Integer, ForeignKey("debit_cards.id"))
    related_transfer_id = Column(Integer)
    related_bill_payment_id = Column(Integer)
    related_direct_deposit_id = Column(Integer)
    status = Column(String, nullable=False, default="pending")
    authorized_at = Column(DateTime)
    posted_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class DirectDepositInstruction(Base):
    __tablename__ = "direct_deposit_instructions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employer_name = Column(Text, nullable=False)
    routing_number = Column(Text, nullable=False)
    account_number_masked = Column(Text, nullable=False)
    destination_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    allocation_type = Column(Text, nullable=False)
    allocation_value = Column(Integer, nullable=False)
    is_primary = Column(Integer, nullable=False, default=0)
    status = Column(Text, nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class DirectDepositEvent(Base):
    __tablename__ = "direct_deposit_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instruction_id = Column(Integer, ForeignKey("direct_deposit_instructions.id"))
    source_employer_name = Column(Text)
    gross_amount_cents = Column(Integer)
    net_amount_cents = Column(Integer, nullable=False)
    received_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class BillPayee(Base):
    __tablename__ = "bill_payees"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(Text, nullable=False)
    address_json = Column(Text)
    account_number_with_payee = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class BillPaymentSchedule(Base):
    __tablename__ = "bill_payment_schedules"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    payee_id = Column(Integer, ForeignKey("bill_payees.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(Text, nullable=False, default="USD")
    frequency = Column(Text, nullable=False)
    day_of_month = Column(Integer)
    day_of_week = Column(Integer)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    occurrences_total = Column(Integer)
    occurrences_completed = Column(Integer, nullable=False, default=0)
    status = Column(Text, nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class BillPayment(Base):
    __tablename__ = "bill_payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("bill_payment_schedules.id"))
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    payee_id = Column(Integer, ForeignKey("bill_payees.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(Text, nullable=False, default="USD")
    scheduled_for = Column(DateTime, nullable=False)
    executed_at = Column(DateTime)
    status = Column(Text, nullable=False, default="scheduled")
    failure_reason = Column(Text)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class AccountTransfer(Base):
    __tablename__ = "account_transfers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(Text, nullable=False, default="USD")
    initiated_at = Column(DateTime, server_default=func.current_timestamp())
    completed_at = Column(DateTime)
    status = Column(Text, nullable=False, default="pending")
    failure_reason = Column(Text)
    debit_transaction_id = Column(Integer, ForeignKey("transactions.id"))
    credit_transaction_id = Column(Integer, ForeignKey("transactions.id"))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class RecurringTransfer(Base):
    __tablename__ = "recurring_transfers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(Text, nullable=False, default="USD")
    frequency = Column(Text, nullable=False)
    day_of_week = Column(Integer)
    day_of_month = Column(Integer)
    time_of_day = Column(Text)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    status = Column(Text, nullable=False, default="active")
    occurrences_total = Column(Integer)
    occurrences_completed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class OverdraftSetting(Base):
    __tablename__ = "overdraft_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, unique=True)
    is_enabled = Column(Integer, nullable=False, default=0)
    limit_cents = Column(Integer, nullable=False, default=0)
    enrolled_at = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class SavingsRule(Base):
    __tablename__ = "savings_rules"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    type = Column(Text, nullable=False)
    is_enabled = Column(Integer, nullable=False, default=1)
    round_up_to_next = Column(Integer)
    dd_min_amount_cents = Column(Integer)
    dd_percentage = Column(Integer)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class SavingsRuleExecution(Base):
    __tablename__ = "savings_rule_executions"
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("savings_rules.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_transaction_id = Column(Integer, ForeignKey("transactions.id"))
    destination_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    executed_at = Column(DateTime, server_default=func.current_timestamp())


class NotificationRule(Base):
    __tablename__ = "notification_rules"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Text, nullable=False)
    threshold_cents = Column(Integer)
    channel_push = Column(Integer, nullable=False, default=1)
    channel_email = Column(Integer, nullable=False, default=0)
    is_enabled = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class NotificationEvent(Base):
    __tablename__ = "notification_events"
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("notification_rules.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    related_transaction_id = Column(Integer, ForeignKey("transactions.id"))
    related_account_id = Column(Integer, ForeignKey("accounts.id"))
    event_type = Column(Text, nullable=False)
    delivered_push = Column(Integer, nullable=False, default=0)
    delivered_email = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.current_timestamp())


class P2PContact(Base):
    __tablename__ = "p2p_contacts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_user_id = Column(Integer, ForeignKey("users.id"))
    handle = Column(Text, nullable=False)
    display_name = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class P2PTransfer(Base):
    __tablename__ = "p2p_transfers"
    id = Column(Integer, primary_key=True)
    sender_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    recipient_user_id = Column(Integer, ForeignKey("users.id"))
    recipient_handle = Column(Text, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(Text, nullable=False, default="USD")
    note = Column(Text)
    status = Column(Text, nullable=False, default="pending")
    initiated_at = Column(DateTime, server_default=func.current_timestamp())
    completed_at = Column(DateTime)
    failure_reason = Column(Text)
    debit_transaction_id = Column(Integer, ForeignKey("transactions.id"))
    credit_transaction_id = Column(Integer, ForeignKey("transactions.id"))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


Base.metadata.create_all(bind=engine)


class AccountModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Account ID", example=10)
    type: str = Field(..., description="Account type", example="checking")
    name: str = Field(..., description="Account nickname", example="Primary Checking")
    is_primary: bool = Field(..., description="Whether this is the primary account of its type", example=True)
    balance_cents: int = Field(..., description="Current balance in cents", example=152340)
    currency: str = Field(..., description="Currency code", example="USD")
    status: str = Field(..., description="Account status", example="open")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-10T15:30:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example="2025-01-11T12:00:00Z")


class AccountsListResponse(BaseModel):
    accounts: List[AccountModel] = Field(..., description="List of accounts", example=[])


class AccountUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="New account nickname", example="Daily Spending")
    is_primary: Optional[bool] = Field(None, description="Set as primary account for its type", example=True)


class DebitCardModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Debit card ID", example=5)
    account_id: int = Field(..., description="Linked account ID", example=10)
    last4: str = Field(..., description="Last 4 digits of card", example="4321")
    status: str = Field(..., description="Card status", example="active")
    is_default_for_debit: bool = Field(..., description="Whether this is the default card for debit", example=True)
    physical_card: bool = Field(..., description="True if physical card", example=True)
    expiration_month: Optional[int] = Field(None, description="Expiration month", example=12)
    expiration_year: Optional[int] = Field(None, description="Expiration year", example=2030)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-10T15:30:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-11T12:00:00Z")


class DebitCardsListResponse(BaseModel):
    debit_cards: List[DebitCardModel] = Field(..., description="List of debit cards", example=[])


class DebitCardUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="New card status", example="locked")
    is_default_for_debit: Optional[bool] = Field(None, description="Set as default card for debit transactions", example=True)


class CardReplacementRequestModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Replacement request ID", example=12)
    user_id: int = Field(..., description="Current user ID", example=1)
    original_card_id: int = Field(..., description="Original card ID", example=5)
    replacement_card_id: Optional[int] = Field(None, description="New card ID when issued", example=None)
    mail_to_address_id: Optional[int] = Field(None, description="Address ID to mail replacement to", example=101)
    reason: str = Field(..., description="Replacement reason", example="suspected_loss")
    status: str = Field(..., description="Request status", example="pending")
    requested_at: Optional[datetime] = Field(None, description="Request timestamp", example="2025-02-01T11:00:00Z")
    processed_at: Optional[datetime] = Field(None, description="Processed timestamp if completed", example=None)


class CardReplacementRequestCreate(BaseModel):
    original_card_id: int = Field(..., description="ID of the card to replace", example=5)
    mail_to_address_id: Optional[int] = Field(None, description="Address ID to mail replacement to", example=101)
    reason: str = Field(..., description="Reason for replacement", example="suspected_loss")


class CardReplacementRequestsListResponse(BaseModel):
    card_replacement_requests: List[CardReplacementRequestModel] = Field(..., description="List of card replacement requests", example=[])


class CategoryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Category ID", example=3)
    name: str = Field(..., description="Category name", example="Restaurant")
    parent_id: Optional[int] = Field(None, description="Parent category ID if any", example=None)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-01T00:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-01-02T00:00:00Z")


class CategoriesListResponse(BaseModel):
    categories: List[CategoryModel] = Field(..., description="List of categories", example=[])


class TransactionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Transaction ID", example=2001)
    account_id: int = Field(..., description="Account ID", example=10)
    type: str = Field(..., description="Transaction type", example="card")
    direction: str = Field(..., description="Transaction direction", example="debit")
    amount_cents: int = Field(..., description="Amount in cents", example=4500)
    currency: str = Field(..., description="Currency code", example="USD")
    description: Optional[str] = Field(None, description="Transaction description", example="Chipotle order")
    merchant_name: Optional[str] = Field(None, description="Merchant name if applicable", example="Chipotle")
    category_id: Optional[int] = Field(None, description="Category ID", example=3)
    related_card_id: Optional[int] = Field(None, description="Related debit card ID", example=5)
    related_transfer_id: Optional[int] = Field(None, description="Related account transfer ID", example=None)
    related_bill_payment_id: Optional[int] = Field(None, description="Related bill payment ID", example=None)
    related_direct_deposit_id: Optional[int] = Field(None, description="Related direct deposit event ID", example=None)
    status: str = Field(..., description="Transaction status", example="posted")
    authorized_at: Optional[datetime] = Field(None, description="Authorization timestamp", example="2025-09-15T18:03:00Z")
    posted_at: Optional[datetime] = Field(None, description="Posting timestamp", example="2025-09-16T08:00:00Z")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-09-15T18:03:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-09-16T08:00:00Z")


class TransactionsListResponse(BaseModel):
    transactions: List[TransactionModel] = Field(..., description="List of transactions", example=[])


class TransactionSummaryItem(BaseModel):
    id: int = Field(..., description="Transaction ID", example=2100)
    amount_cents: int = Field(..., description="Amount in cents", example=3200)
    currency: str = Field(..., description="Currency code", example="USD")
    merchant_name: Optional[str] = Field(None, description="Merchant name", example="Olive Garden")
    description: Optional[str] = Field(None, description="Transaction description", example="Dinner with friends")
    posted_at: Optional[datetime] = Field(None, description="Posting timestamp", example="2025-09-12T20:10:00Z")


class TransactionSummaryResponse(BaseModel):
    total_amount_cents: int = Field(..., description="Sum of matching transaction amounts in cents", example=123450)
    currency: str = Field(..., description="Currency code", example="USD")
    count: int = Field(..., description="Number of matching transactions", example=24)
    largest_transactions: List[TransactionSummaryItem] = Field(..., description="Largest transactions in the period", example=[])


class DirectDepositInstructionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Direct deposit instruction ID", example=7)
    user_id: int = Field(..., description="Current user ID", example=1)
    employer_name: str = Field(..., description="Employer or payer name", example="Acme Corp")
    routing_number: str = Field(..., description="ACH routing number", example="123456789")
    account_number_masked: str = Field(..., description="Masked external account number or token", example="0001234567")
    destination_account_id: int = Field(..., description="Destination account ID", example=10)
    allocation_type: str = Field(..., description="Allocation type", example="percent")
    allocation_value: float = Field(..., description="Allocation value", example=100.0)
    is_primary: bool = Field(..., description="Primary instruction flag", example=True)
    status: str = Field(..., description="Instruction status", example="active")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-02-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-01T12:00:00Z")


class DirectDepositInstructionCreate(BaseModel):
    employer_name: str = Field(..., description="Employer or payer name", example="Acme Corp")
    routing_number: str = Field(..., description="ACH routing number", example="123456789")
    account_number_masked: str = Field(..., description="Masked external account number or token", example="0001234567")
    destination_account_id: int = Field(..., description="Internal destination account ID", example=10)
    allocation_type: str = Field(..., description="Allocation type: percent, amount, or remainder", example="percent")
    allocation_value: float = Field(..., description="Allocation value", example=100.0)
    is_primary: Optional[bool] = Field(None, description="Mark this instruction as primary", example=True)


class DirectDepositInstructionListResponse(BaseModel):
    direct_deposit_instructions: List[DirectDepositInstructionModel] = Field(..., description="List of direct deposit instructions", example=[])


class DirectDepositEventModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Event ID", example=100)
    instruction_id: Optional[int] = Field(None, description="Related instruction ID", example=7)
    source_employer_name: Optional[str] = Field(None, description="Employer name as received", example="Acme Corp")
    gross_amount_cents: Optional[int] = Field(None, description="Gross amount in cents", example=300000)
    net_amount_cents: int = Field(..., description="Net amount in cents", example=245000)
    received_at: datetime = Field(..., description="When funds were received", example="2025-02-15T09:00:00Z")
    processed_at: Optional[datetime] = Field(None, description="When funds were processed", example="2025-02-15T09:05:00Z")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-02-15T09:00:01Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-15T09:05:01Z")


class DirectDepositEventListResponse(BaseModel):
    direct_deposit_events: List[DirectDepositEventModel] = Field(..., description="List of direct deposit events", example=[])


class AddressModel(BaseModel):
    line1: Optional[str] = Field(None, description="Address line 1", example="123 Main St")
    city: Optional[str] = Field(None, description="City", example="Metro City")
    state: Optional[str] = Field(None, description="State", example="CA")
    postal_code: Optional[str] = Field(None, description="Postal code", example="90001")


class BillPayeeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Bill payee ID", example=20)
    user_id: int = Field(..., description="Current user ID", example=1)
    name: str = Field(..., description="Payee name", example="Metro City Utilities")
    address_json: Optional[Dict[str, str]] = Field(None, description="Stored address JSON", example={"line1": "123 Main St", "city": "Metro City", "state": "CA", "postal_code": "90001"})
    account_number_with_payee: Optional[str] = Field(None, description="Account number with payee", example="ACC-987654321")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-02-01T12:30:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-01T12:30:00Z")


class BillPayeeCreate(BaseModel):
    name: str = Field(..., description="Payee display name", example="Metro City Utilities")
    address_json: Optional[Dict[str, str]] = Field(None, description="JSON structure for mailing address", example={"line1": "123 Main St", "city": "Metro City", "state": "CA", "postal_code": "90001"})
    account_number_with_payee: Optional[str] = Field(None, description="Account number with the payee if needed", example="ACC-987654321")


class BillPayeesListResponse(BaseModel):
    bill_payees: List[BillPayeeModel] = Field(..., description="List of bill payees", example=[])


class BillPaymentScheduleModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Bill payment schedule ID", example=30)
    user_id: int = Field(..., description="Current user ID", example=1)
    from_account_id: int = Field(..., description="Source account ID", example=10)
    payee_id: int = Field(..., description="Bill payee ID", example=20)
    amount_cents: int = Field(..., description="Payment amount in cents", example=12000)
    currency: str = Field(..., description="Currency code", example="USD")
    frequency: str = Field(..., description="Payment frequency", example="monthly")
    day_of_month: Optional[int] = Field(None, description="Day of month for payments", example=5)
    day_of_week: Optional[int] = Field(None, description="Day of week for payments", example=None)
    start_date: datetime = Field(..., description="Schedule start date", example="2025-03-05")
    end_date: Optional[datetime] = Field(None, description="Schedule end date if set", example="2026-02-05")
    occurrences_total: Optional[int] = Field(None, description="Total occurrences planned", example=12)
    occurrences_completed: int = Field(..., description="Completed payment count", example=0)
    status: str = Field(..., description="Schedule status", example="active")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-02-01T13:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-01T13:00:00Z")


class BillPaymentScheduleCreate(BaseModel):
    from_account_id: int = Field(..., description="Source account ID for payments", example=10)
    payee_id: int = Field(..., description="Bill payee ID", example=20)
    amount_cents: int = Field(..., description="Payment amount in cents", example=12000)
    currency: Optional[str] = Field(None, description="Currency code", example="USD")
    frequency: str = Field(..., description="Payment frequency", example="monthly")
    day_of_month: Optional[int] = Field(None, description="Day of month for monthly/yearly schedules", example=5)
    day_of_week: Optional[int] = Field(None, description="Day of week for weekly/biweekly schedules", example=None)
    start_date: str = Field(..., description="Schedule start date (YYYY-MM-DD)", example="2025-03-05")
    end_date: Optional[str] = Field(None, description="Schedule end date (YYYY-MM-DD)", example="2026-02-05")
    occurrences_total: Optional[int] = Field(None, description="Total number of occurrences if finite", example=12)


class BillPaymentSchedulesListResponse(BaseModel):
    bill_payment_schedules: List[BillPaymentScheduleModel] = Field(..., description="List of bill payment schedules", example=[])


class BillPaymentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Bill payment ID", example=40)
    schedule_id: Optional[int] = Field(None, description="Related schedule ID", example=30)
    from_account_id: int = Field(..., description="Source account ID", example=10)
    payee_id: int = Field(..., description="Payee ID", example=20)
    amount_cents: int = Field(..., description="Payment amount in cents", example=12000)
    currency: str = Field(..., description="Currency", example="USD")
    scheduled_for: datetime = Field(..., description="Scheduled execution datetime", example="2025-03-05T09:00:00Z")
    executed_at: Optional[datetime] = Field(None, description="Actual execution time", example=None)
    status: str = Field(..., description="Payment status", example="scheduled")
    failure_reason: Optional[str] = Field(None, description="Failure reason if any", example=None)
    transaction_id: Optional[int] = Field(None, description="Linked transaction ID if executed", example=None)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-02-01T13:10:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-01T13:10:00Z")


class BillPaymentsListResponse(BaseModel):
    bill_payments: List[BillPaymentModel] = Field(..., description="List of bill payments", example=[])


class AccountTransferModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Transfer ID", example=50)
    user_id: int = Field(..., description="Current user ID", example=1)
    from_account_id: int = Field(..., description="Source account ID", example=10)
    to_account_id: int = Field(..., description="Destination account ID", example=11)
    amount_cents: int = Field(..., description="Transfer amount in cents", example=25000)
    currency: str = Field(..., description="Currency", example="USD")
    initiated_at: Optional[datetime] = Field(None, description="Initiation timestamp", example="2025-02-01T14:00:00Z")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp if completed", example="2025-02-01T14:00:05Z")
    status: str = Field(..., description="Transfer status", example="completed")
    failure_reason: Optional[str] = Field(None, description="Failure reason if failed", example=None)
    debit_transaction_id: Optional[int] = Field(None, description="Debit transaction ID", example=3001)
    credit_transaction_id: Optional[int] = Field(None, description="Credit transaction ID", example=3002)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-02-01T14:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-01T14:00:05Z")


class AccountTransferCreate(BaseModel):
    from_account_id: int = Field(..., description="Source account ID", example=10)
    to_account_id: int = Field(..., description="Destination account ID", example=11)
    amount_cents: int = Field(..., description="Transfer amount in cents", example=25000)
    currency: Optional[str] = Field(None, description="Currency code", example="USD")


class AccountTransfersListResponse(BaseModel):
    account_transfers: List[AccountTransferModel] = Field(..., description="List of account transfers", example=[])


class RecurringTransferModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Recurring transfer schedule ID", example=60)
    user_id: int = Field(..., description="Current user ID", example=1)
    from_account_id: int = Field(..., description="Source account ID", example=10)
    to_account_id: int = Field(..., description="Destination account ID", example=11)
    amount_cents: int = Field(..., description="Transfer amount in cents", example=2500)
    currency: str = Field(..., description="Currency code", example="USD")
    frequency: str = Field(..., description="Transfer frequency", example="weekly")
    day_of_week: Optional[int] = Field(None, description="Day of week if applicable", example=4)
    day_of_month: Optional[int] = Field(None, description="Day of month if applicable", example=None)
    time_of_day: Optional[str] = Field(None, description="Time of day for execution", example="09:00")
    start_date: datetime = Field(..., description="Schedule start date", example="2025-02-07")
    end_date: Optional[datetime] = Field(None, description="Schedule end date if any", example=None)
    status: str = Field(..., description="Schedule status", example="active")
    occurrences_total: Optional[int] = Field(None, description="Total planned occurrences", example=None)
    occurrences_completed: int = Field(..., description="Completed occurrences count", example=0)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-02-01T14:30:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-01T14:30:00Z")


class RecurringTransferCreate(BaseModel):
    from_account_id: int = Field(..., description="Source account ID", example=10)
    to_account_id: int = Field(..., description="Destination account ID", example=11)
    amount_cents: int = Field(..., description="Transfer amount in cents", example=2500)
    currency: Optional[str] = Field(None, description="Currency code", example="USD")
    frequency: str = Field(..., description="Frequency: weekly, biweekly, or monthly", example="weekly")
    day_of_week: Optional[int] = Field(None, description="Day of week for weekly/biweekly", example=4)
    day_of_month: Optional[int] = Field(None, description="Day of month for monthly transfers", example=None)
    time_of_day: Optional[str] = Field(None, description="Time of day in HH:MM format", example="09:00")
    start_date: str = Field(..., description="Start date for the schedule (YYYY-MM-DD)", example="2025-02-07")
    end_date: Optional[str] = Field(None, description="End date for the schedule (YYYY-MM-DD)", example=None)
    occurrences_total: Optional[int] = Field(None, description="Total number of occurrences if finite", example=None)


class RecurringTransfersListResponse(BaseModel):
    recurring_transfers: List[RecurringTransferModel] = Field(..., description="List of recurring transfers", example=[])


class OverdraftSettingModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Overdraft settings ID", example=70)
    user_id: int = Field(..., description="Current user ID", example=1)
    account_id: int = Field(..., description="Account ID", example=10)
    is_enabled: bool = Field(..., description="Whether overdraft is enabled", example=True)
    limit_cents: int = Field(..., description="Overdraft limit in cents", example=15000)
    enrolled_at: Optional[datetime] = Field(None, description="Enrollment timestamp if enabled", example="2025-02-01T15:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-01T15:00:00Z")


class OverdraftSettingCreate(BaseModel):
    account_id: int = Field(..., description="Account ID to create overdraft settings for", example=10)
    is_enabled: Optional[bool] = Field(None, description="Whether overdraft is enabled", example=True)
    limit_cents: Optional[int] = Field(None, description="Overdraft limit in cents", example=15000)


class OverdraftSettingsListResponse(BaseModel):
    overdraft_settings: List[OverdraftSettingModel] = Field(..., description="List of overdraft settings", example=[])


class OverdraftSettingUpdate(BaseModel):
    is_enabled: Optional[bool] = Field(None, description="Enable or disable overdraft", example=True)
    limit_cents: Optional[int] = Field(None, description="New overdraft limit in cents", example=15000)


class SavingsRuleModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Savings rule ID", example=80)
    user_id: int = Field(..., description="Current user ID", example=1)
    destination_account_id: int = Field(..., description="Destination account ID", example=11)
    type: str = Field(..., description="Rule type", example="round_up")
    is_enabled: bool = Field(..., description="Rule enabled flag", example=True)
    round_up_to_next: Optional[int] = Field(None, description="Whole dollar to round transactions up to", example=1)
    dd_min_amount_cents: Optional[int] = Field(None, description="Minimum direct deposit amount to trigger rule", example=100000)
    dd_percentage: Optional[float] = Field(None, description="Percentage of direct deposit to transfer", example=10.0)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-02-01T16:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-01T16:00:00Z")


class SavingsRuleCreate(BaseModel):
    destination_account_id: int = Field(..., description="Destination savings account ID", example=11)
    type: str = Field(..., description="Rule type: round_up or direct_deposit_percentage", example="round_up")
    is_enabled: Optional[bool] = Field(None, description="Whether rule starts enabled", example=True)
    round_up_to_next: Optional[int] = Field(None, description="Whole dollar to round up to", example=1)
    dd_min_amount_cents: Optional[int] = Field(None, description="Minimum direct deposit amount for rule in cents", example=100000)
    dd_percentage: Optional[float] = Field(None, description="Percentage of qualifying direct deposit to save", example=10.0)


class SavingsRulesListResponse(BaseModel):
    savings_rules: List[SavingsRuleModel] = Field(..., description="List of savings rules", example=[])


class SavingsRuleUpdate(BaseModel):
    is_enabled: Optional[bool] = Field(None, description="Enable or disable rule", example=True)
    round_up_to_next: Optional[int] = Field(None, description="Whole dollar for round-up rule", example=1)
    dd_min_amount_cents: Optional[int] = Field(None, description="Minimum direct deposit amount in cents", example=100000)
    dd_percentage: Optional[float] = Field(None, description="Percentage for direct deposit rule", example=10.0)


class SavingsRuleExecutionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Execution ID", example=90)
    rule_id: int = Field(..., description="Savings rule ID", example=80)
    user_id: int = Field(..., description="Current user ID", example=1)
    source_transaction_id: Optional[int] = Field(None, description="Related source transaction ID", example=2001)
    destination_account_id: int = Field(..., description="Destination account ID", example=11)
    amount_cents: int = Field(..., description="Saved amount in cents", example=75)
    executed_at: Optional[datetime] = Field(None, description="Execution timestamp", example="2025-02-01T16:10:00Z")


class SavingsRuleExecutionsListResponse(BaseModel):
    savings_rule_executions: List[SavingsRuleExecutionModel] = Field(..., description="List of savings rule executions", example=[])


class NotificationRuleModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Notification rule ID", example=100)
    user_id: int = Field(..., description="Current user ID", example=1)
    type: str = Field(..., description="Rule type", example="high_transaction")
    threshold_cents: Optional[int] = Field(None, description="Threshold in cents if applicable", example=20000)
    channel_push: bool = Field(..., description="Push channel flag", example=True)
    channel_email: bool = Field(..., description="Email channel flag", example=True)
    is_enabled: bool = Field(..., description="Rule enabled flag", example=True)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-02-01T17:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-01T17:00:00Z")


class NotificationRuleCreate(BaseModel):
    type: str = Field(..., description="Rule type", example="high_transaction")
    threshold_cents: Optional[int] = Field(None, description="Threshold in cents", example=20000)
    channel_push: Optional[bool] = Field(None, description="Enable push notifications", example=True)
    channel_email: Optional[bool] = Field(None, description="Enable email notifications", example=True)
    is_enabled: Optional[bool] = Field(None, description="Whether the rule is enabled", example=True)


class NotificationRulesListResponse(BaseModel):
    notification_rules: List[NotificationRuleModel] = Field(..., description="List of notification rules", example=[])


class NotificationRuleUpdate(BaseModel):
    threshold_cents: Optional[int] = Field(None, description="Updated threshold in cents", example=20000)
    channel_push: Optional[bool] = Field(None, description="Updated push channel flag", example=True)
    channel_email: Optional[bool] = Field(None, description="Updated email channel flag", example=True)
    is_enabled: Optional[bool] = Field(None, description="Updated enabled state", example=True)


class NotificationEventModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Notification event ID", example=110)
    rule_id: int = Field(..., description="Rule that triggered the event", example=100)
    user_id: int = Field(..., description="Current user ID", example=1)
    related_transaction_id: Optional[int] = Field(None, description="Related transaction if any", example=2001)
    related_account_id: Optional[int] = Field(None, description="Related account if any", example=10)
    event_type: str = Field(..., description="Event type string", example="transaction_over_threshold")
    delivered_push: bool = Field(..., description="Whether push was delivered", example=True)
    delivered_email: bool = Field(..., description="Whether email was delivered", example=True)
    created_at: Optional[datetime] = Field(None, description="Event creation timestamp", example="2025-02-01T17:10:00Z")


class NotificationEventsListResponse(BaseModel):
    notification_events: List[NotificationEventModel] = Field(..., description="List of notification events", example=[])


class P2PContactModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Contact record ID", example=120)
    user_id: int = Field(..., description="Owner user ID", example=1)
    contact_user_id: Optional[int] = Field(None, description="Contact user ID if resolved", example=2)
    handle: str = Field(..., description="P2P handle", example="@roommate_jane")
    display_name: Optional[str] = Field(None, description="Display name for contact", example="Jane Doe")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-02-01T18:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-01T18:00:00Z")


class P2PContactsListResponse(BaseModel):
    p2p_contacts: List[P2PContactModel] = Field(..., description="List of P2P contacts", example=[])


class P2PTransferModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="P2P transfer ID", example=130)
    sender_user_id: int = Field(..., description="Sender user ID", example=1)
    sender_account_id: int = Field(..., description="Sender account ID", example=10)
    recipient_user_id: Optional[int] = Field(None, description="Recipient user ID if resolved", example=2)
    recipient_handle: str = Field(..., description="Recipient handle", example="@roommate_jane")
    amount_cents: int = Field(..., description="Amount in cents", example=4500)
    currency: str = Field(..., description="Currency code", example="USD")
    note: Optional[str] = Field(None, description="Transfer note", example="January utilities")
    status: str = Field(..., description="Transfer status", example="pending")
    initiated_at: Optional[datetime] = Field(None, description="Initiation timestamp", example="2025-02-01T18:30:00Z")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp if completed", example=None)
    failure_reason: Optional[str] = Field(None, description="Failure reason if any", example=None)
    debit_transaction_id: Optional[int] = Field(None, description="Debit transaction ID", example=None)
    credit_transaction_id: Optional[int] = Field(None, description="Credit transaction ID", example=None)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-02-01T18:30:00Z")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp", example="2025-02-01T18:30:00Z")


class P2PTransferCreate(BaseModel):
    sender_account_id: int = Field(..., description="Sender's account ID", example=10)
    recipient_handle: str = Field(..., description="Recipient's handle", example="@roommate_jane")
    amount_cents: int = Field(..., description="Amount to send in cents", example=4500)
    currency: Optional[str] = Field(None, description="Currency code", example="USD")
    note: Optional[str] = Field(None, description="Optional note for the transfer", example="January utilities")


class P2PTransfersListResponse(BaseModel):
    p2p_transfers: List[P2PTransferModel] = Field(..., description="List of P2P transfers", example=[])


@app.get(
    "/api/accounts",
    response_model=AccountsListResponse,
    summary="List accounts for current user",
    description="Retrieve all checking and savings accounts for the authenticated user.",
    tags=["accounts"],
    operation_id="list_accounts",
)
async def list_accounts() -> AccountsListResponse:
    session = SessionLocal()
    rows = session.query(Account).filter(Account.user_id == 1).all()
    result_list: List[AccountModel] = []
    for row in rows:
        result_list.append(
            AccountModel(
                id=row.id,
                type=row.type,
                name=row.name,
                is_primary=bool(row.is_primary),
                balance_cents=row.balance_cents,
                currency=row.currency,
                status=row.status,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        )
    session.close()
    return AccountsListResponse(accounts=result_list)


@app.get(
    "/api/accounts/{account_id}",
    response_model=AccountModel,
    summary="Get account by ID",
    description="Retrieve details for a specific account owned by the authenticated user.",
    tags=["accounts"],
    operation_id="get_account",
)
async def get_account(account_id: int = Path(..., description="ID of the account to retrieve", example=10)) -> AccountModel:
    session = SessionLocal()
    row = session.query(Account).filter(Account.user_id == 1, Account.id == account_id).first()
    if row is None:
        row = Account(
            id=0,
            user_id=1,
            type="checking",
            name="",
            is_primary=0,
            balance_cents=0,
            currency="USD",
            status="open",
        )
    model = AccountModel(
        id=row.id,
        type=row.type,
        name=row.name,
        is_primary=bool(row.is_primary),
        balance_cents=row.balance_cents,
        currency=row.currency,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
    session.close()
    return model


@app.patch(
    "/api/accounts/{account_id}",
    response_model=AccountModel,
    summary="Update account fields",
    description="Update an account's name or primary flag for the authenticated user.",
    tags=["accounts"],
    operation_id="update_account",
)
async def update_account(
    account_id: int = Path(..., description="Account ID to update", example=10),
    payload: AccountUpdateRequest = Body(..., description="Account update payload"),
) -> AccountModel:
    session = SessionLocal()
    row = session.query(Account).filter(Account.user_id == 1, Account.id == account_id).first()
    if row is None:
        row = Account(
            id=0,
            user_id=1,
            type="checking",
            name="",
            is_primary=0,
            balance_cents=0,
            currency="USD",
            status="open",
        )
        session.add(row)
        session.commit()
    if payload.name is not None:
        row.name = payload.name
    if payload.is_primary is not None:
        if payload.is_primary:
            same_type = session.query(Account).filter(Account.user_id == 1, Account.type == row.type).all()
            for other in same_type:
                other.is_primary = 0
        row.is_primary = 1 if payload.is_primary else 0
    row.updated_at = datetime.utcnow()
    session.commit()
    model = AccountModel(
        id=row.id,
        type=row.type,
        name=row.name,
        is_primary=bool(row.is_primary),
        balance_cents=row.balance_cents,
        currency=row.currency,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/debit_cards",
    response_model=DebitCardsListResponse,
    summary="List debit cards",
    description="Retrieve all debit cards for the authenticated user.",
    tags=["debit_cards"],
    operation_id="list_debit_cards",
)
async def list_debit_cards() -> DebitCardsListResponse:
    session = SessionLocal()
    rows = session.query(DebitCard).filter(DebitCard.user_id == 1).all()
    result_list: List[DebitCardModel] = []
    for row in rows:
        result_list.append(
            DebitCardModel(
                id=row.id,
                account_id=row.account_id,
                last4=row.last4,
                status=row.status,
                is_default_for_debit=bool(row.is_default_for_debit),
                physical_card=bool(row.physical_card),
                expiration_month=row.expiration_month,
                expiration_year=row.expiration_year,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        )
    session.close()
    return DebitCardsListResponse(debit_cards=result_list)


@app.get(
    "/api/debit_cards/{card_id}",
    response_model=DebitCardModel,
    summary="Get debit card by ID",
    description="Retrieve details for a specific debit card owned by the authenticated user.",
    tags=["debit_cards"],
    operation_id="get_debit_card",
)
async def get_debit_card(card_id: int = Path(..., description="Debit card ID to retrieve", example=5)) -> DebitCardModel:
    session = SessionLocal()
    row = session.query(DebitCard).filter(DebitCard.user_id == 1, DebitCard.id == card_id).first()
    if row is None:
        row = DebitCard(
            id=0,
            user_id=1,
            account_id=0,
            last4="0000",
            status="active",
            is_default_for_debit=0,
            physical_card=1,
        )
        session.add(row)
        session.commit()
    model = DebitCardModel(
        id=row.id,
        account_id=row.account_id,
        last4=row.last4,
        status=row.status,
        is_default_for_debit=bool(row.is_default_for_debit),
        physical_card=bool(row.physical_card),
        expiration_month=row.expiration_month,
        expiration_year=row.expiration_year,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
    session.close()
    return model


@app.patch(
    "/api/debit_cards/{card_id}",
    response_model=DebitCardModel,
    summary="Update debit card",
    description="Lock, unlock, or set a debit card as default for debit transactions.",
    tags=["debit_cards"],
    operation_id="update_debit_card",
)
async def update_debit_card(
    card_id: int = Path(..., description="Debit card ID to update", example=5),
    payload: DebitCardUpdateRequest = Body(..., description="Debit card update payload"),
) -> DebitCardModel:
    session = SessionLocal()
    row = session.query(DebitCard).filter(DebitCard.user_id == 1, DebitCard.id == card_id).first()
    if row is None:
        row = DebitCard(
            id=0,
            user_id=1,
            account_id=0,
            last4="0000",
            status="active",
            is_default_for_debit=0,
            physical_card=1,
        )
        session.add(row)
        session.commit()
    if payload.status is not None:
        row.status = payload.status
    if payload.is_default_for_debit is not None:
        if payload.is_default_for_debit:
            others = session.query(DebitCard).filter(DebitCard.user_id == 1).all()
            for other in others:
                other.is_default_for_debit = 0
        row.is_default_for_debit = 1 if payload.is_default_for_debit else 0
    row.updated_at = datetime.utcnow()
    session.commit()
    model = DebitCardModel(
        id=row.id,
        account_id=row.account_id,
        last4=row.last4,
        status=row.status,
        is_default_for_debit=bool(row.is_default_for_debit),
        physical_card=bool(row.physical_card),
        expiration_month=row.expiration_month,
        expiration_year=row.expiration_year,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/debit_cards/by_last4/{last4}",
    response_model=DebitCardModel,
    summary="Find debit card by last4",
    description="Lookup a debit card for the current user using its last 4 digits.",
    tags=["debit_cards"],
    operation_id="get_debit_card_by_last4",
)
async def get_debit_card_by_last4(last4: str = Path(..., description="Last 4 digits of the debit card", example="4321")) -> DebitCardModel:
    session = SessionLocal()
    row = session.query(DebitCard).filter(DebitCard.user_id == 1, DebitCard.last4 == last4).first()
    if row is None:
        row = DebitCard(
            id=0,
            user_id=1,
            account_id=0,
            last4=last4,
            status="active",
            is_default_for_debit=0,
            physical_card=1,
        )
        session.add(row)
        session.commit()
    model = DebitCardModel(
        id=row.id,
        account_id=row.account_id,
        last4=row.last4,
        status=row.status,
        is_default_for_debit=bool(row.is_default_for_debit),
        physical_card=bool(row.physical_card),
        expiration_month=row.expiration_month,
        expiration_year=row.expiration_year,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
    session.close()
    return model


@app.post(
    "/api/card_replacement_requests",
    response_model=CardReplacementRequestModel,
    summary="Create card replacement request",
    description="Request a replacement for a debit card with a specified reason and address.",
    tags=["card_replacement"],
    operation_id="create_card_replacement_request",
)
async def create_card_replacement_request(
    payload: CardReplacementRequestCreate = Body(..., description="Card replacement request payload"),
) -> CardReplacementRequestModel:
    session = SessionLocal()
    obj = CardReplacementRequest(
        user_id=1,
        original_card_id=payload.original_card_id,
        replacement_card_id=None,
        mail_to_address_id=payload.mail_to_address_id,
        reason=payload.reason,
        status="pending",
        requested_at=datetime.utcnow(),
        processed_at=None,
    )
    session.add(obj)
    session.commit()
    model = CardReplacementRequestModel(
        id=obj.id,
        user_id=obj.user_id,
        original_card_id=obj.original_card_id,
        replacement_card_id=obj.replacement_card_id,
        mail_to_address_id=obj.mail_to_address_id,
        reason=obj.reason,
        status=obj.status,
        requested_at=obj.requested_at,
        processed_at=obj.processed_at,
    )
    session.close()
    return model


@app.get(
    "/api/card_replacement_requests",
    response_model=CardReplacementRequestsListResponse,
    summary="List card replacement requests",
    description="Retrieve all card replacement requests created by the authenticated user.",
    tags=["card_replacement"],
    operation_id="list_card_replacement_requests",
)
async def list_card_replacement_requests() -> CardReplacementRequestsListResponse:
    session = SessionLocal()
    rows = session.query(CardReplacementRequest).filter(CardReplacementRequest.user_id == 1).all()
    result_list: List[CardReplacementRequestModel] = []
    for obj in rows:
        result_list.append(
            CardReplacementRequestModel(
                id=obj.id,
                user_id=obj.user_id,
                original_card_id=obj.original_card_id,
                replacement_card_id=obj.replacement_card_id,
                mail_to_address_id=obj.mail_to_address_id,
                reason=obj.reason,
                status=obj.status,
                requested_at=obj.requested_at,
                processed_at=obj.processed_at,
            )
        )
    session.close()
    return CardReplacementRequestsListResponse(card_replacement_requests=result_list)


@app.get(
    "/api/categories",
    response_model=CategoriesListResponse,
    summary="List categories",
    description="Retrieve all categories that can be associated with transactions.",
    tags=["categories"],
    operation_id="list_categories",
)
async def list_categories() -> CategoriesListResponse:
    session = SessionLocal()
    rows = session.query(Category).all()
    result_list: List[CategoryModel] = []
    for row in rows:
        result_list.append(
            CategoryModel(
                id=row.id,
                name=row.name,
                parent_id=row.parent_id,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        )
    session.close()
    return CategoriesListResponse(categories=result_list)


@app.get(
    "/api/transactions",
    response_model=TransactionsListResponse,
    summary="List transactions",
    description="Retrieve transactions for current user with optional filters and pagination.",
    tags=["transactions"],
    operation_id="list_transactions",
)
async def list_transactions(
    account_id: Optional[int] = Query(None, description="Filter by account ID", example=10),
    type_filter: Optional[str] = Query(None, alias="type", description="Filter by transaction type", example="card"),
    direction: Optional[str] = Query(None, description="Filter by transaction direction", example="debit"),
    category_name: Optional[str] = Query(None, description="Filter by category name", example="Restaurant"),
    posted_from: Optional[str] = Query(None, description="Filter posted_at from (ISO8601)", example="2025-09-01T00:00:00Z"),
    posted_to: Optional[str] = Query(None, description="Filter posted_at to (ISO8601)", example="2025-09-30T23:59:59Z"),
    status: Optional[str] = Query(None, description="Filter by transaction status", example="posted"),
    limit: Optional[int] = Query(None, description="Max number of records to return", example=100),
    offset: Optional[int] = Query(None, description="Number of records to skip", example=0),
) -> TransactionsListResponse:
    session = SessionLocal()
    query = session.query(Transaction).filter(Transaction.user_id == 1)
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)
    if type_filter is not None:
        query = query.filter(Transaction.type == type_filter)
    if direction is not None:
        query = query.filter(Transaction.direction == direction)
    if status is not None:
        query = query.filter(Transaction.status == status)
    if posted_from is not None:
        try:
            dt_from = datetime.fromisoformat(posted_from.replace("Z", "+00:00"))
            query = query.filter(Transaction.posted_at >= dt_from)
        except ValueError:
            pass
    if posted_to is not None:
        try:
            dt_to = datetime.fromisoformat(posted_to.replace("Z", "+00:00"))
            query = query.filter(Transaction.posted_at <= dt_to)
        except ValueError:
            pass
    if category_name is not None:
        cat = session.query(Category).filter(Category.name == category_name).first()
        if cat is not None:
            query = query.filter(Transaction.category_id == cat.id)
        else:
            query = query.filter(Transaction.category_id == -1)
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    rows = query.all()
    result_list: List[TransactionModel] = []
    for row in rows:
        result_list.append(
            TransactionModel(
                id=row.id,
                account_id=row.account_id,
                type=row.type,
                direction=row.direction,
                amount_cents=row.amount_cents,
                currency=row.currency,
                description=row.description,
                merchant_name=row.merchant_name,
                category_id=row.category_id,
                related_card_id=row.related_card_id,
                related_transfer_id=row.related_transfer_id,
                related_bill_payment_id=row.related_bill_payment_id,
                related_direct_deposit_id=row.related_direct_deposit_id,
                status=row.status,
                authorized_at=row.authorized_at,
                posted_at=row.posted_at,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        )
    session.close()
    return TransactionsListResponse(transactions=result_list)


@app.get(
    "/api/transactions/summary",
    response_model=TransactionSummaryResponse,
    summary="Transaction summary",
    description="Compute totals and top transactions for a period and optional filters.",
    tags=["transactions"],
    operation_id="get_transaction_summary",
)
async def get_transaction_summary(
    account_id: Optional[int] = Query(None, description="Filter by account ID", example=10),
    type_filter: Optional[str] = Query(None, alias="type", description="Transaction type filter", example="card"),
    direction: Optional[str] = Query(None, description="Direction filter", example="debit"),
    category_name: Optional[str] = Query(None, description="Filter by category name", example="Restaurant"),
    posted_from: str = Query(..., description="Start of posted_at window (ISO8601)", example="2025-09-01T00:00:00Z"),
    posted_to: str = Query(..., description="End of posted_at window (ISO8601)", example="2025-09-30T23:59:59Z"),
    status: Optional[str] = Query(None, description="Status filter", example="posted"),
    top_n: Optional[int] = Query(None, description="Number of largest transactions to return", example=3),
) -> TransactionSummaryResponse:
    session = SessionLocal()
    query = session.query(Transaction).filter(Transaction.user_id == 1)
    try:
        dt_from = datetime.fromisoformat(posted_from.replace("Z", "+00:00"))
        query = query.filter(Transaction.posted_at >= dt_from)
    except ValueError:
        pass
    try:
        dt_to = datetime.fromisoformat(posted_to.replace("Z", "+00:00"))
        query = query.filter(Transaction.posted_at <= dt_to)
    except ValueError:
        pass
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)
    if type_filter is not None:
        query = query.filter(Transaction.type == type_filter)
    if direction is not None:
        query = query.filter(Transaction.direction == direction)
    if status is not None:
        query = query.filter(Transaction.status == status)
    if category_name is not None:
        cat = session.query(Category).filter(Category.name == category_name).first()
        if cat is not None:
            query = query.filter(Transaction.category_id == cat.id)
        else:
            query = query.filter(Transaction.category_id == -1)
    rows = query.all()
    total_amount = 0
    count = 0
    for row in rows:
        total_amount += row.amount_cents
        count += 1
    sorted_rows = sorted(rows, key=lambda r: abs(r.amount_cents), reverse=True)
    if top_n is not None:
        sorted_rows = sorted_rows[:top_n]
    largest_list: List[TransactionSummaryItem] = []
    for row in sorted_rows:
        largest_list.append(
            TransactionSummaryItem(
                id=row.id,
                amount_cents=row.amount_cents,
                currency=row.currency,
                merchant_name=row.merchant_name,
                description=row.description,
                posted_at=row.posted_at,
            )
        )
    currency_value = "USD"
    if rows:
        currency_value = rows[0].currency
    session.close()
    return TransactionSummaryResponse(
        total_amount_cents=total_amount,
        currency=currency_value,
        count=count,
        largest_transactions=largest_list,
    )


@app.post(
    "/api/direct_deposit_instructions",
    response_model=DirectDepositInstructionModel,
    summary="Create direct deposit instruction",
    description="Create an instruction to receive payroll or other direct deposits into an account.",
    tags=["direct_deposit_instructions"],
    operation_id="create_direct_deposit_instruction",
)
async def create_direct_deposit_instruction(
    payload: DirectDepositInstructionCreate = Body(..., description="Direct deposit instruction payload"),
) -> DirectDepositInstructionModel:
    session = SessionLocal()
    if payload.is_primary:
        existing = session.query(DirectDepositInstruction).filter(DirectDepositInstruction.user_id == 1).all()
        for e in existing:
            e.is_primary = 0
    obj = DirectDepositInstruction(
        user_id=1,
        employer_name=payload.employer_name,
        routing_number=payload.routing_number,
        account_number_masked=payload.account_number_masked,
        destination_account_id=payload.destination_account_id,
        allocation_type=payload.allocation_type,
        allocation_value=int(payload.allocation_value),
        is_primary=1 if payload.is_primary else 0,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(obj)
    session.commit()
    model = DirectDepositInstructionModel(
        id=obj.id,
        user_id=obj.user_id,
        employer_name=obj.employer_name,
        routing_number=obj.routing_number,
        account_number_masked=obj.account_number_masked,
        destination_account_id=obj.destination_account_id,
        allocation_type=obj.allocation_type,
        allocation_value=float(obj.allocation_value),
        is_primary=bool(obj.is_primary),
        status=obj.status,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/direct_deposit_instructions",
    response_model=DirectDepositInstructionListResponse,
    summary="List direct deposit instructions",
    description="Retrieve all direct deposit instructions configured by the current user.",
    tags=["direct_deposit_instructions"],
    operation_id="list_direct_deposit_instructions",
)
async def list_direct_deposit_instructions(
    employer_name: Optional[str] = Query(None, description="Filter instructions by employer name", example="Acme Corp"),
    status: Optional[str] = Query(None, description="Filter by status", example="active"),
) -> DirectDepositInstructionListResponse:
    session = SessionLocal()
    query = session.query(DirectDepositInstruction).filter(DirectDepositInstruction.user_id == 1)
    if employer_name is not None:
        query = query.filter(DirectDepositInstruction.employer_name == employer_name)
    if status is not None:
        query = query.filter(DirectDepositInstruction.status == status)
    rows = query.all()
    result_list: List[DirectDepositInstructionModel] = []
    for obj in rows:
        result_list.append(
            DirectDepositInstructionModel(
                id=obj.id,
                user_id=obj.user_id,
                employer_name=obj.employer_name,
                routing_number=obj.routing_number,
                account_number_masked=obj.account_number_masked,
                destination_account_id=obj.destination_account_id,
                allocation_type=obj.allocation_type,
                allocation_value=float(obj.allocation_value),
                is_primary=bool(obj.is_primary),
                status=obj.status,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return DirectDepositInstructionListResponse(direct_deposit_instructions=result_list)


@app.get(
    "/api/direct_deposit_events",
    response_model=DirectDepositEventListResponse,
    summary="List direct deposit events",
    description="Retrieve direct deposit events received by the current user with filters.",
    tags=["direct_deposit_events"],
    operation_id="list_direct_deposit_events",
)
async def list_direct_deposit_events(
    instruction_id: Optional[int] = Query(None, description="Filter by related instruction ID", example=7),
    source_employer_name: Optional[str] = Query(None, description="Filter by employer name", example="Acme Corp"),
    received_from: Optional[str] = Query(None, description="Filter received_at from (ISO8601)", example="2025-01-01T00:00:00Z"),
    received_to: Optional[str] = Query(None, description="Filter received_at to (ISO8601)", example="2025-12-31T23:59:59Z"),
) -> DirectDepositEventListResponse:
    session = SessionLocal()
    query = session.query(DirectDepositEvent).filter(DirectDepositEvent.user_id == 1)
    if instruction_id is not None:
        query = query.filter(DirectDepositEvent.instruction_id == instruction_id)
    if source_employer_name is not None:
        query = query.filter(DirectDepositEvent.source_employer_name == source_employer_name)
    if received_from is not None:
        try:
            dt_from = datetime.fromisoformat(received_from.replace("Z", "+00:00"))
            query = query.filter(DirectDepositEvent.received_at >= dt_from)
        except ValueError:
            pass
    if received_to is not None:
        try:
            dt_to = datetime.fromisoformat(received_to.replace("Z", "+00:00"))
            query = query.filter(DirectDepositEvent.received_at <= dt_to)
        except ValueError:
            pass
    rows = query.all()
    result_list: List[DirectDepositEventModel] = []
    for obj in rows:
        result_list.append(
            DirectDepositEventModel(
                id=obj.id,
                instruction_id=obj.instruction_id,
                source_employer_name=obj.source_employer_name,
                gross_amount_cents=obj.gross_amount_cents,
                net_amount_cents=obj.net_amount_cents,
                received_at=obj.received_at,
                processed_at=obj.processed_at,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return DirectDepositEventListResponse(direct_deposit_events=result_list)


@app.post(
    "/api/bill_payees",
    response_model=BillPayeeModel,
    summary="Create bill payee",
    description="Create a new bill payee with name, address, and account number details.",
    tags=["bill_payees"],
    operation_id="create_bill_payee",
)
async def create_bill_payee(
    payload: BillPayeeCreate = Body(..., description="Bill payee creation payload"),
) -> BillPayeeModel:
    session = SessionLocal()
    address_text = None
    if payload.address_json is not None:
        address_text = str(payload.address_json)
    obj = BillPayee(
        user_id=1,
        name=payload.name,
        address_json=address_text,
        account_number_with_payee=payload.account_number_with_payee,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(obj)
    session.commit()
    address_data = None
    if obj.address_json is not None:
        try:
            import ast

            address_data = ast.literal_eval(obj.address_json)
        except Exception:
            address_data = None
    model = BillPayeeModel(
        id=obj.id,
        user_id=obj.user_id,
        name=obj.name,
        address_json=address_data,
        account_number_with_payee=obj.account_number_with_payee,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/bill_payees",
    response_model=BillPayeesListResponse,
    summary="List bill payees",
    description="Retrieve all bill payees created by the current user with optional name filter.",
    tags=["bill_payees"],
    operation_id="list_bill_payees",
)
async def list_bill_payees(
    name: Optional[str] = Query(None, description="Filter payees by name substring", example="Metro City Utilities"),
) -> BillPayeesListResponse:
    session = SessionLocal()
    query = session.query(BillPayee).filter(BillPayee.user_id == 1)
    if name is not None:
        query = query.filter(BillPayee.name.contains(name))
    rows = query.all()
    result_list: List[BillPayeeModel] = []
    for obj in rows:
        address_data = None
        if obj.address_json is not None:
            try:
                import ast

                address_data = ast.literal_eval(obj.address_json)
            except Exception:
                address_data = None
        result_list.append(
            BillPayeeModel(
                id=obj.id,
                user_id=obj.user_id,
                name=obj.name,
                address_json=address_data,
                account_number_with_payee=obj.account_number_with_payee,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return BillPayeesListResponse(bill_payees=result_list)


@app.post(
    "/api/bill_payment_schedules",
    response_model=BillPaymentScheduleModel,
    summary="Create bill payment schedule",
    description="Create a one-time or recurring bill payment schedule from a source account to a payee.",
    tags=["bill_payment_schedules"],
    operation_id="create_bill_payment_schedule",
)
async def create_bill_payment_schedule(
    payload: BillPaymentScheduleCreate = Body(..., description="Bill payment schedule creation payload"),
) -> BillPaymentScheduleModel:
    session = SessionLocal()
    start_date_obj = datetime.fromisoformat(payload.start_date).date()
    end_date_obj = None
    if payload.end_date is not None:
        end_date_obj = datetime.fromisoformat(payload.end_date).date()
    currency_value = payload.currency if payload.currency is not None else "USD"
    obj = BillPaymentSchedule(
        user_id=1,
        from_account_id=payload.from_account_id,
        payee_id=payload.payee_id,
        amount_cents=payload.amount_cents,
        currency=currency_value,
        frequency=payload.frequency,
        day_of_month=payload.day_of_month,
        day_of_week=payload.day_of_week,
        start_date=start_date_obj,
        end_date=end_date_obj,
        occurrences_total=payload.occurrences_total,
        occurrences_completed=0,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(obj)
    session.commit()
    model = BillPaymentScheduleModel(
        id=obj.id,
        user_id=obj.user_id,
        from_account_id=obj.from_account_id,
        payee_id=obj.payee_id,
        amount_cents=obj.amount_cents,
        currency=obj.currency,
        frequency=obj.frequency,
        day_of_month=obj.day_of_month,
        day_of_week=obj.day_of_week,
        start_date=datetime.combine(obj.start_date, datetime.min.time()),
        end_date=datetime.combine(obj.end_date, datetime.min.time()) if obj.end_date is not None else None,
        occurrences_total=obj.occurrences_total,
        occurrences_completed=obj.occurrences_completed,
        status=obj.status,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/bill_payment_schedules",
    response_model=BillPaymentSchedulesListResponse,
    summary="List bill payment schedules",
    description="Retrieve all bill payment schedules for the current user with filters.",
    tags=["bill_payment_schedules"],
    operation_id="list_bill_payment_schedules",
)
async def list_bill_payment_schedules(
    status: Optional[str] = Query(None, description="Filter by schedule status", example="active"),
    from_account_id: Optional[int] = Query(None, description="Filter by source account ID", example=10),
    payee_id: Optional[int] = Query(None, description="Filter by payee ID", example=20),
) -> BillPaymentSchedulesListResponse:
    session = SessionLocal()
    query = session.query(BillPaymentSchedule).filter(BillPaymentSchedule.user_id == 1)
    if status is not None:
        query = query.filter(BillPaymentSchedule.status == status)
    if from_account_id is not None:
        query = query.filter(BillPaymentSchedule.from_account_id == from_account_id)
    if payee_id is not None:
        query = query.filter(BillPaymentSchedule.payee_id == payee_id)
    rows = query.all()
    result_list: List[BillPaymentScheduleModel] = []
    for obj in rows:
        result_list.append(
            BillPaymentScheduleModel(
                id=obj.id,
                user_id=obj.user_id,
                from_account_id=obj.from_account_id,
                payee_id=obj.payee_id,
                amount_cents=obj.amount_cents,
                currency=obj.currency,
                frequency=obj.frequency,
                day_of_month=obj.day_of_month,
                day_of_week=obj.day_of_week,
                start_date=datetime.combine(obj.start_date, datetime.min.time()),
                end_date=datetime.combine(obj.end_date, datetime.min.time()) if obj.end_date is not None else None,
                occurrences_total=obj.occurrences_total,
                occurrences_completed=obj.occurrences_completed,
                status=obj.status,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return BillPaymentSchedulesListResponse(bill_payment_schedules=result_list)


@app.get(
    "/api/bill_payments",
    response_model=BillPaymentsListResponse,
    summary="List bill payments",
    description="Retrieve scheduled and executed bill payments for the current user.",
    tags=["bill_payments"],
    operation_id="list_bill_payments",
)
async def list_bill_payments(
    schedule_id: Optional[int] = Query(None, description="Filter by schedule ID", example=30),
    status: Optional[str] = Query(None, description="Filter by payment status", example="scheduled"),
    scheduled_from: Optional[str] = Query(None, description="Filter by scheduled_for from (ISO8601)", example="2025-03-01T00:00:00Z"),
    scheduled_to: Optional[str] = Query(None, description="Filter by scheduled_for to (ISO8601)", example="2025-03-31T23:59:59Z"),
) -> BillPaymentsListResponse:
    session = SessionLocal()
    query = session.query(BillPayment).filter(BillPayment.user_id == 1)
    if schedule_id is not None:
        query = query.filter(BillPayment.schedule_id == schedule_id)
    if status is not None:
        query = query.filter(BillPayment.status == status)
    if scheduled_from is not None:
        try:
            dt_from = datetime.fromisoformat(scheduled_from.replace("Z", "+00:00"))
            query = query.filter(BillPayment.scheduled_for >= dt_from)
        except ValueError:
            pass
    if scheduled_to is not None:
        try:
            dt_to = datetime.fromisoformat(scheduled_to.replace("Z", "+00:00"))
            query = query.filter(BillPayment.scheduled_for <= dt_to)
        except ValueError:
            pass
    rows = query.all()
    result_list: List[BillPaymentModel] = []
    for obj in rows:
        result_list.append(
            BillPaymentModel(
                id=obj.id,
                schedule_id=obj.schedule_id,
                from_account_id=obj.from_account_id,
                payee_id=obj.payee_id,
                amount_cents=obj.amount_cents,
                currency=obj.currency,
                scheduled_for=obj.scheduled_for,
                executed_at=obj.executed_at,
                status=obj.status,
                failure_reason=obj.failure_reason,
                transaction_id=obj.transaction_id,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return BillPaymentsListResponse(bill_payments=result_list)


@app.post(
    "/api/account_transfers",
    response_model=AccountTransferModel,
    summary="Create account transfer",
    description="Transfer funds immediately between two accounts owned by the current user.",
    tags=["account_transfers"],
    operation_id="create_account_transfer",
)
async def create_account_transfer(
    payload: AccountTransferCreate = Body(..., description="Account transfer creation payload"),
) -> AccountTransferModel:
    session = SessionLocal()
    currency_value = payload.currency if payload.currency is not None else "USD"
    obj = AccountTransfer(
        user_id=1,
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount_cents=payload.amount_cents,
        currency=currency_value,
        initiated_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        status="completed",
        failure_reason=None,
        debit_transaction_id=None,
        credit_transaction_id=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(obj)
    session.commit()
    model = AccountTransferModel(
        id=obj.id,
        user_id=obj.user_id,
        from_account_id=obj.from_account_id,
        to_account_id=obj.to_account_id,
        amount_cents=obj.amount_cents,
        currency=obj.currency,
        initiated_at=obj.initiated_at,
        completed_at=obj.completed_at,
        status=obj.status,
        failure_reason=obj.failure_reason,
        debit_transaction_id=obj.debit_transaction_id,
        credit_transaction_id=obj.credit_transaction_id,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/account_transfers",
    response_model=AccountTransfersListResponse,
    summary="List account transfers",
    description="Retrieve account transfers between the user's own accounts with filters.",
    tags=["account_transfers"],
    operation_id="list_account_transfers",
)
async def list_account_transfers(
    from_account_id: Optional[int] = Query(None, description="Filter by source account ID", example=10),
    to_account_id: Optional[int] = Query(None, description="Filter by destination account ID", example=11),
    status: Optional[str] = Query(None, description="Filter by transfer status", example="completed"),
    initiated_from: Optional[str] = Query(None, description="Filter initiated_at from (ISO8601)", example="2025-02-01T00:00:00Z"),
    initiated_to: Optional[str] = Query(None, description="Filter initiated_at to (ISO8601)", example="2025-02-28T23:59:59Z"),
) -> AccountTransfersListResponse:
    session = SessionLocal()
    query = session.query(AccountTransfer).filter(AccountTransfer.user_id == 1)
    if from_account_id is not None:
        query = query.filter(AccountTransfer.from_account_id == from_account_id)
    if to_account_id is not None:
        query = query.filter(AccountTransfer.to_account_id == to_account_id)
    if status is not None:
        query = query.filter(AccountTransfer.status == status)
    if initiated_from is not None:
        try:
            dt_from = datetime.fromisoformat(initiated_from.replace("Z", "+00:00"))
            query = query.filter(AccountTransfer.initiated_at >= dt_from)
        except ValueError:
            pass
    if initiated_to is not None:
        try:
            dt_to = datetime.fromisoformat(initiated_to.replace("Z", "+00:00"))
            query = query.filter(AccountTransfer.initiated_at <= dt_to)
        except ValueError:
            pass
    rows = query.all()
    result_list: List[AccountTransferModel] = []
    for obj in rows:
        result_list.append(
            AccountTransferModel(
                id=obj.id,
                user_id=obj.user_id,
                from_account_id=obj.from_account_id,
                to_account_id=obj.to_account_id,
                amount_cents=obj.amount_cents,
                currency=obj.currency,
                initiated_at=obj.initiated_at,
                completed_at=obj.completed_at,
                status=obj.status,
                failure_reason=obj.failure_reason,
                debit_transaction_id=obj.debit_transaction_id,
                credit_transaction_id=obj.credit_transaction_id,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return AccountTransfersListResponse(account_transfers=result_list)


@app.post(
    "/api/recurring_transfers",
    response_model=RecurringTransferModel,
    summary="Create recurring transfer",
    description="Schedule a recurring transfer between two user accounts.",
    tags=["recurring_transfers"],
    operation_id="create_recurring_transfer",
)
async def create_recurring_transfer(
    payload: RecurringTransferCreate = Body(..., description="Recurring transfer creation payload"),
) -> RecurringTransferModel:
    session = SessionLocal()
    start_date_obj = datetime.fromisoformat(payload.start_date).date()
    end_date_obj = None
    if payload.end_date is not None:
        end_date_obj = datetime.fromisoformat(payload.end_date).date()
    currency_value = payload.currency if payload.currency is not None else "USD"
    obj = RecurringTransfer(
        user_id=1,
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount_cents=payload.amount_cents,
        currency=currency_value,
        frequency=payload.frequency,
        day_of_week=payload.day_of_week,
        day_of_month=payload.day_of_month,
        time_of_day=payload.time_of_day,
        start_date=start_date_obj,
        end_date=end_date_obj,
        status="active",
        occurrences_total=payload.occurrences_total,
        occurrences_completed=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(obj)
    session.commit()
    model = RecurringTransferModel(
        id=obj.id,
        user_id=obj.user_id,
        from_account_id=obj.from_account_id,
        to_account_id=obj.to_account_id,
        amount_cents=obj.amount_cents,
        currency=obj.currency,
        frequency=obj.frequency,
        day_of_week=obj.day_of_week,
        day_of_month=obj.day_of_month,
        time_of_day=obj.time_of_day,
        start_date=datetime.combine(obj.start_date, datetime.min.time()),
        end_date=datetime.combine(obj.end_date, datetime.min.time()) if obj.end_date is not None else None,
        status=obj.status,
        occurrences_total=obj.occurrences_total,
        occurrences_completed=obj.occurrences_completed,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/recurring_transfers",
    response_model=RecurringTransfersListResponse,
    summary="List recurring transfers",
    description="Retrieve recurring transfer schedules for the current user with filters.",
    tags=["recurring_transfers"],
    operation_id="list_recurring_transfers",
)
async def list_recurring_transfers(
    from_account_id: Optional[int] = Query(None, description="Filter by source account ID", example=10),
    to_account_id: Optional[int] = Query(None, description="Filter by destination account ID", example=11),
    status: Optional[str] = Query(None, description="Filter by status", example="active"),
) -> RecurringTransfersListResponse:
    session = SessionLocal()
    query = session.query(RecurringTransfer).filter(RecurringTransfer.user_id == 1)
    if from_account_id is not None:
        query = query.filter(RecurringTransfer.from_account_id == from_account_id)
    if to_account_id is not None:
        query = query.filter(RecurringTransfer.to_account_id == to_account_id)
    if status is not None:
        query = query.filter(RecurringTransfer.status == status)
    rows = query.all()
    result_list: List[RecurringTransferModel] = []
    for obj in rows:
        result_list.append(
            RecurringTransferModel(
                id=obj.id,
                user_id=obj.user_id,
                from_account_id=obj.from_account_id,
                to_account_id=obj.to_account_id,
                amount_cents=obj.amount_cents,
                currency=obj.currency,
                frequency=obj.frequency,
                day_of_week=obj.day_of_week,
                day_of_month=obj.day_of_month,
                time_of_day=obj.time_of_day,
                start_date=datetime.combine(obj.start_date, datetime.min.time()),
                end_date=datetime.combine(obj.end_date, datetime.min.time()) if obj.end_date is not None else None,
                status=obj.status,
                occurrences_total=obj.occurrences_total,
                occurrences_completed=obj.occurrences_completed,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return RecurringTransfersListResponse(recurring_transfers=result_list)


@app.post(
    "/api/overdraft_settings",
    response_model=OverdraftSettingModel,
    summary="Create overdraft settings",
    description="Initialize overdraft settings for a specific account if not already present.",
    tags=["overdraft_settings"],
    operation_id="create_overdraft_settings",
)
async def create_overdraft_settings(
    payload: OverdraftSettingCreate = Body(..., description="Overdraft settings creation payload"),
) -> OverdraftSettingModel:
    session = SessionLocal()
    existing = session.query(OverdraftSetting).filter(OverdraftSetting.account_id == payload.account_id, OverdraftSetting.user_id == 1).first()
    if existing is not None:
        obj = existing
    else:
        is_enabled_int = 1 if payload.is_enabled else 0
        limit_value = payload.limit_cents if payload.limit_cents is not None else 0
        enrolled_at_value = datetime.utcnow() if payload.is_enabled else None
        obj = OverdraftSetting(
            user_id=1,
            account_id=payload.account_id,
            is_enabled=is_enabled_int,
            limit_cents=limit_value,
            enrolled_at=enrolled_at_value,
            updated_at=datetime.utcnow(),
        )
        session.add(obj)
    session.commit()
    model = OverdraftSettingModel(
        id=obj.id,
        user_id=obj.user_id,
        account_id=obj.account_id,
        is_enabled=bool(obj.is_enabled),
        limit_cents=obj.limit_cents,
        enrolled_at=obj.enrolled_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/overdraft_settings",
    response_model=OverdraftSettingsListResponse,
    summary="List overdraft settings",
    description="Retrieve overdraft settings for all accounts owned by the current user.",
    tags=["overdraft_settings"],
    operation_id="list_overdraft_settings",
)
async def list_overdraft_settings() -> OverdraftSettingsListResponse:
    session = SessionLocal()
    rows = session.query(OverdraftSetting).filter(OverdraftSetting.user_id == 1).all()
    result_list: List[OverdraftSettingModel] = []
    for obj in rows:
        result_list.append(
            OverdraftSettingModel(
                id=obj.id,
                user_id=obj.user_id,
                account_id=obj.account_id,
                is_enabled=bool(obj.is_enabled),
                limit_cents=obj.limit_cents,
                enrolled_at=obj.enrolled_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return OverdraftSettingsListResponse(overdraft_settings=result_list)


@app.patch(
    "/api/overdraft_settings/{account_id}",
    response_model=OverdraftSettingModel,
    summary="Update overdraft settings",
    description="Enable, disable, or change the overdraft limit for a specific account.",
    tags=["overdraft_settings"],
    operation_id="update_overdraft_settings",
)
async def update_overdraft_settings(
    account_id: int = Path(..., description="Account ID whose overdraft settings are updated", example=10),
    payload: OverdraftSettingUpdate = Body(..., description="Overdraft settings update payload"),
) -> OverdraftSettingModel:
    session = SessionLocal()
    obj = session.query(OverdraftSetting).filter(OverdraftSetting.user_id == 1, OverdraftSetting.account_id == account_id).first()
    if obj is None:
        obj = OverdraftSetting(
            user_id=1,
            account_id=account_id,
            is_enabled=0,
            limit_cents=0,
            enrolled_at=None,
            updated_at=datetime.utcnow(),
        )
        session.add(obj)
        session.commit()
    if payload.is_enabled is not None:
        obj.is_enabled = 1 if payload.is_enabled else 0
        if payload.is_enabled and obj.enrolled_at is None:
            obj.enrolled_at = datetime.utcnow()
    if payload.limit_cents is not None:
        obj.limit_cents = payload.limit_cents
    obj.updated_at = datetime.utcnow()
    session.commit()
    model = OverdraftSettingModel(
        id=obj.id,
        user_id=obj.user_id,
        account_id=obj.account_id,
        is_enabled=bool(obj.is_enabled),
        limit_cents=obj.limit_cents,
        enrolled_at=obj.enrolled_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.post(
    "/api/savings_rules",
    response_model=SavingsRuleModel,
    summary="Create savings rule",
    description="Create a round-up or direct deposit percentage savings rule to move funds to savings.",
    tags=["savings_rules"],
    operation_id="create_savings_rule",
)
async def create_savings_rule(
    payload: SavingsRuleCreate = Body(..., description="Savings rule creation payload"),
) -> SavingsRuleModel:
    session = SessionLocal()
    obj = SavingsRule(
        user_id=1,
        destination_account_id=payload.destination_account_id,
        type=payload.type,
        is_enabled=1 if (payload.is_enabled is None or payload.is_enabled) else 0,
        round_up_to_next=payload.round_up_to_next,
        dd_min_amount_cents=payload.dd_min_amount_cents,
        dd_percentage=int(payload.dd_percentage) if payload.dd_percentage is not None else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(obj)
    session.commit()
    model = SavingsRuleModel(
        id=obj.id,
        user_id=obj.user_id,
        destination_account_id=obj.destination_account_id,
        type=obj.type,
        is_enabled=bool(obj.is_enabled),
        round_up_to_next=obj.round_up_to_next,
        dd_min_amount_cents=obj.dd_min_amount_cents,
        dd_percentage=float(obj.dd_percentage) if obj.dd_percentage is not None else None,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/savings_rules",
    response_model=SavingsRulesListResponse,
    summary="List savings rules",
    description="Retrieve all savings rules configured by the current user with optional type filter.",
    tags=["savings_rules"],
    operation_id="list_savings_rules",
)
async def list_savings_rules(
    type_filter: Optional[str] = Query(None, alias="type", description="Filter by rule type", example="round_up"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled state", example=True),
) -> SavingsRulesListResponse:
    session = SessionLocal()
    query = session.query(SavingsRule).filter(SavingsRule.user_id == 1)
    if type_filter is not None:
        query = query.filter(SavingsRule.type == type_filter)
    if is_enabled is not None:
        query = query.filter(SavingsRule.is_enabled == (1 if is_enabled else 0))
    rows = query.all()
    result_list: List[SavingsRuleModel] = []
    for obj in rows:
        result_list.append(
            SavingsRuleModel(
                id=obj.id,
                user_id=obj.user_id,
                destination_account_id=obj.destination_account_id,
                type=obj.type,
                is_enabled=bool(obj.is_enabled),
                round_up_to_next=obj.round_up_to_next,
                dd_min_amount_cents=obj.dd_min_amount_cents,
                dd_percentage=float(obj.dd_percentage) if obj.dd_percentage is not None else None,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return SavingsRulesListResponse(savings_rules=result_list)


@app.patch(
    "/api/savings_rules/{rule_id}",
    response_model=SavingsRuleModel,
    summary="Update savings rule",
    description="Enable, disable, or modify parameters of an existing savings rule.",
    tags=["savings_rules"],
    operation_id="update_savings_rule",
)
async def update_savings_rule(
    rule_id: int = Path(..., description="Savings rule ID to update", example=80),
    payload: SavingsRuleUpdate = Body(..., description="Savings rule update payload"),
) -> SavingsRuleModel:
    session = SessionLocal()
    obj = session.query(SavingsRule).filter(SavingsRule.user_id == 1, SavingsRule.id == rule_id).first()
    if obj is None:
        obj = SavingsRule(
            user_id=1,
            destination_account_id=0,
            type="round_up",
            is_enabled=1,
            round_up_to_next=None,
            dd_min_amount_cents=None,
            dd_percentage=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(obj)
        session.commit()
    if payload.is_enabled is not None:
        obj.is_enabled = 1 if payload.is_enabled else 0
    if payload.round_up_to_next is not None:
        obj.round_up_to_next = payload.round_up_to_next
    if payload.dd_min_amount_cents is not None:
        obj.dd_min_amount_cents = payload.dd_min_amount_cents
    if payload.dd_percentage is not None:
        obj.dd_percentage = int(payload.dd_percentage)
    obj.updated_at = datetime.utcnow()
    session.commit()
    model = SavingsRuleModel(
        id=obj.id,
        user_id=obj.user_id,
        destination_account_id=obj.destination_account_id,
        type=obj.type,
        is_enabled=bool(obj.is_enabled),
        round_up_to_next=obj.round_up_to_next,
        dd_min_amount_cents=obj.dd_min_amount_cents,
        dd_percentage=float(obj.dd_percentage) if obj.dd_percentage is not None else None,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/savings_rule_executions",
    response_model=SavingsRuleExecutionsListResponse,
    summary="List savings rule executions",
    description="Retrieve historical executions of savings rules for the current user.",
    tags=["savings_rules"],
    operation_id="list_savings_rule_executions",
)
async def list_savings_rule_executions(
    rule_id: Optional[int] = Query(None, description="Filter by savings rule ID", example=80),
) -> SavingsRuleExecutionsListResponse:
    session = SessionLocal()
    query = session.query(SavingsRuleExecution).filter(SavingsRuleExecution.user_id == 1)
    if rule_id is not None:
        query = query.filter(SavingsRuleExecution.rule_id == rule_id)
    rows = query.all()
    result_list: List[SavingsRuleExecutionModel] = []
    for obj in rows:
        result_list.append(
            SavingsRuleExecutionModel(
                id=obj.id,
                rule_id=obj.rule_id,
                user_id=obj.user_id,
                source_transaction_id=obj.source_transaction_id,
                destination_account_id=obj.destination_account_id,
                amount_cents=obj.amount_cents,
                executed_at=obj.executed_at,
            )
        )
    session.close()
    return SavingsRuleExecutionsListResponse(savings_rule_executions=result_list)


@app.post(
    "/api/notification_rules",
    response_model=NotificationRuleModel,
    summary="Create notification rule",
    description="Create a new notification rule for high transaction, direct deposit, or low balance.",
    tags=["notification_rules"],
    operation_id="create_notification_rule",
)
async def create_notification_rule(
    payload: NotificationRuleCreate = Body(..., description="Notification rule creation payload"),
) -> NotificationRuleModel:
    session = SessionLocal()
    obj = NotificationRule(
        user_id=1,
        type=payload.type,
        threshold_cents=payload.threshold_cents,
        channel_push=1 if (payload.channel_push is None or payload.channel_push) else 0,
        channel_email=1 if (payload.channel_email is not None and payload.channel_email) else 0,
        is_enabled=1 if (payload.is_enabled is None or payload.is_enabled) else 0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(obj)
    session.commit()
    model = NotificationRuleModel(
        id=obj.id,
        user_id=obj.user_id,
        type=obj.type,
        threshold_cents=obj.threshold_cents,
        channel_push=bool(obj.channel_push),
        channel_email=bool(obj.channel_email),
        is_enabled=bool(obj.is_enabled),
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/notification_rules",
    response_model=NotificationRulesListResponse,
    summary="List notification rules",
    description="Retrieve all notification rules configured by the current user.",
    tags=["notification_rules"],
    operation_id="list_notification_rules",
)
async def list_notification_rules(
    type_filter: Optional[str] = Query(None, alias="type", description="Filter by rule type", example="high_transaction"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled state", example=True),
) -> NotificationRulesListResponse:
    session = SessionLocal()
    query = session.query(NotificationRule).filter(NotificationRule.user_id == 1)
    if type_filter is not None:
        query = query.filter(NotificationRule.type == type_filter)
    if is_enabled is not None:
        query = query.filter(NotificationRule.is_enabled == (1 if is_enabled else 0))
    rows = query.all()
    result_list: List[NotificationRuleModel] = []
    for obj in rows:
        result_list.append(
            NotificationRuleModel(
                id=obj.id,
                user_id=obj.user_id,
                type=obj.type,
                threshold_cents=obj.threshold_cents,
                channel_push=bool(obj.channel_push),
                channel_email=bool(obj.channel_email),
                is_enabled=bool(obj.is_enabled),
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return NotificationRulesListResponse(notification_rules=result_list)


@app.patch(
    "/api/notification_rules/{rule_id}",
    response_model=NotificationRuleModel,
    summary="Update notification rule",
    description="Enable, disable, or adjust threshold or channels for a notification rule.",
    tags=["notification_rules"],
    operation_id="update_notification_rule",
)
async def update_notification_rule(
    rule_id: int = Path(..., description="Notification rule ID to update", example=100),
    payload: NotificationRuleUpdate = Body(..., description="Notification rule update payload"),
) -> NotificationRuleModel:
    session = SessionLocal()
    obj = session.query(NotificationRule).filter(NotificationRule.user_id == 1, NotificationRule.id == rule_id).first()
    if obj is None:
        obj = NotificationRule(
            user_id=1,
            type="high_transaction",
            threshold_cents=None,
            channel_push=1,
            channel_email=0,
            is_enabled=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(obj)
        session.commit()
    if payload.threshold_cents is not None:
        obj.threshold_cents = payload.threshold_cents
    if payload.channel_push is not None:
        obj.channel_push = 1 if payload.channel_push else 0
    if payload.channel_email is not None:
        obj.channel_email = 1 if payload.channel_email else 0
    if payload.is_enabled is not None:
        obj.is_enabled = 1 if payload.is_enabled else 0
    obj.updated_at = datetime.utcnow()
    session.commit()
    model = NotificationRuleModel(
        id=obj.id,
        user_id=obj.user_id,
        type=obj.type,
        threshold_cents=obj.threshold_cents,
        channel_push=bool(obj.channel_push),
        channel_email=bool(obj.channel_email),
        is_enabled=bool(obj.is_enabled),
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/notification_events",
    response_model=NotificationEventsListResponse,
    summary="List notification events",
    description="Retrieve historical notification events generated by rules for the user.",
    tags=["notification_rules"],
    operation_id="list_notification_events",
)
async def list_notification_events(
    rule_id: Optional[int] = Query(None, description="Filter by notification rule ID", example=100),
    event_type: Optional[str] = Query(None, description="Filter by event type string", example="transaction_over_threshold"),
) -> NotificationEventsListResponse:
    session = SessionLocal()
    query = session.query(NotificationEvent).filter(NotificationEvent.user_id == 1)
    if rule_id is not None:
        query = query.filter(NotificationEvent.rule_id == rule_id)
    if event_type is not None:
        query = query.filter(NotificationEvent.event_type == event_type)
    rows = query.all()
    result_list: List[NotificationEventModel] = []
    for obj in rows:
        result_list.append(
            NotificationEventModel(
                id=obj.id,
                rule_id=obj.rule_id,
                user_id=obj.user_id,
                related_transaction_id=obj.related_transaction_id,
                related_account_id=obj.related_account_id,
                event_type=obj.event_type,
                delivered_push=bool(obj.delivered_push),
                delivered_email=bool(obj.delivered_email),
                created_at=obj.created_at,
            )
        )
    session.close()
    return NotificationEventsListResponse(notification_events=result_list)


@app.get(
    "/api/p2p_contacts",
    response_model=P2PContactsListResponse,
    summary="List P2P contacts",
    description="Retrieve saved P2P contacts for the current user.",
    tags=["p2p_contacts"],
    operation_id="list_p2p_contacts",
)
async def list_p2p_contacts() -> P2PContactsListResponse:
    session = SessionLocal()
    rows = session.query(P2PContact).filter(P2PContact.user_id == 1).all()
    result_list: List[P2PContactModel] = []
    for obj in rows:
        result_list.append(
            P2PContactModel(
                id=obj.id,
                user_id=obj.user_id,
                contact_user_id=obj.contact_user_id,
                handle=obj.handle,
                display_name=obj.display_name,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return P2PContactsListResponse(p2p_contacts=result_list)


@app.post(
    "/api/p2p_transfers",
    response_model=P2PTransferModel,
    summary="Create P2P transfer",
    description="Send a P2P payment from an account to a recipient handle with an optional note.",
    tags=["p2p_transfers"],
    operation_id="create_p2p_transfer",
)
async def create_p2p_transfer(
    payload: P2PTransferCreate = Body(..., description="P2P transfer creation payload"),
) -> P2PTransferModel:
    session = SessionLocal()
    currency_value = payload.currency if payload.currency is not None else "USD"
    obj = P2PTransfer(
        sender_user_id=1,
        sender_account_id=payload.sender_account_id,
        recipient_user_id=None,
        recipient_handle=payload.recipient_handle,
        amount_cents=payload.amount_cents,
        currency=currency_value,
        note=payload.note,
        status="pending",
        initiated_at=datetime.utcnow(),
        completed_at=None,
        failure_reason=None,
        debit_transaction_id=None,
        credit_transaction_id=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(obj)
    session.commit()
    model = P2PTransferModel(
        id=obj.id,
        sender_user_id=obj.sender_user_id,
        sender_account_id=obj.sender_account_id,
        recipient_user_id=obj.recipient_user_id,
        recipient_handle=obj.recipient_handle,
        amount_cents=obj.amount_cents,
        currency=obj.currency,
        note=obj.note,
        status=obj.status,
        initiated_at=obj.initiated_at,
        completed_at=obj.completed_at,
        failure_reason=obj.failure_reason,
        debit_transaction_id=obj.debit_transaction_id,
        credit_transaction_id=obj.credit_transaction_id,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


@app.get(
    "/api/p2p_transfers",
    response_model=P2PTransfersListResponse,
    summary="List P2P transfers",
    description="Retrieve P2P transfers sent by the current user with optional filters.",
    tags=["p2p_transfers"],
    operation_id="list_p2p_transfers",
)
async def list_p2p_transfers(
    status: Optional[str] = Query(None, description="Filter by transfer status", example="completed"),
    recipient_handle: Optional[str] = Query(None, description="Filter by recipient handle", example="@roommate_jane"),
) -> P2PTransfersListResponse:
    session = SessionLocal()
    query = session.query(P2PTransfer).filter(P2PTransfer.sender_user_id == 1)
    if status is not None:
        query = query.filter(P2PTransfer.status == status)
    if recipient_handle is not None:
        query = query.filter(P2PTransfer.recipient_handle == recipient_handle)
    rows = query.all()
    result_list: List[P2PTransferModel] = []
    for obj in rows:
        result_list.append(
            P2PTransferModel(
                id=obj.id,
                sender_user_id=obj.sender_user_id,
                sender_account_id=obj.sender_account_id,
                recipient_user_id=obj.recipient_user_id,
                recipient_handle=obj.recipient_handle,
                amount_cents=obj.amount_cents,
                currency=obj.currency,
                note=obj.note,
                status=obj.status,
                initiated_at=obj.initiated_at,
                completed_at=obj.completed_at,
                failure_reason=obj.failure_reason,
                debit_transaction_id=obj.debit_transaction_id,
                credit_transaction_id=obj.credit_transaction_id,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
            )
        )
    session.close()
    return P2PTransfersListResponse(p2p_transfers=result_list)


@app.get(
    "/api/p2p_transfers/{transfer_id}",
    response_model=P2PTransferModel,
    summary="Get P2P transfer",
    description="Retrieve details and status for a specific P2P transfer sent by the user.",
    tags=["p2p_transfers"],
    operation_id="get_p2p_transfer",
)
async def get_p2p_transfer(
    transfer_id: int = Path(..., description="P2P transfer ID to retrieve", example=130),
) -> P2PTransferModel:
    session = SessionLocal()
    obj = session.query(P2PTransfer).filter(P2PTransfer.sender_user_id == 1, P2PTransfer.id == transfer_id).first()
    if obj is None:
        obj = P2PTransfer(
            id=0,
            sender_user_id=1,
            sender_account_id=0,
            recipient_user_id=None,
            recipient_handle="",
            amount_cents=0,
            currency="USD",
            note=None,
            status="pending",
            initiated_at=datetime.utcnow(),
            completed_at=None,
            failure_reason=None,
            debit_transaction_id=None,
            credit_transaction_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(obj)
        session.commit()
    model = P2PTransferModel(
        id=obj.id,
        sender_user_id=obj.sender_user_id,
        sender_account_id=obj.sender_account_id,
        recipient_user_id=obj.recipient_user_id,
        recipient_handle=obj.recipient_handle,
        amount_cents=obj.amount_cents,
        currency=obj.currency,
        note=obj.note,
        status=obj.status,
        initiated_at=obj.initiated_at,
        completed_at=obj.completed_at,
        failure_reason=obj.failure_reason,
        debit_transaction_id=obj.debit_transaction_id,
        credit_transaction_id=obj.credit_transaction_id,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
    session.close()
    return model


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)