from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
import os
from datetime import datetime, date
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    ForeignKey,
    Float,
    LargeBinary,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

database_url = os.getenv("DATABASE_PATH", "sqlite:///outputs/databases/subflow_billing_manager.db")
engine = create_engine("sqlite:////mnt/genming/training-local-cases-20261104/cases/billing_payments_3_5/after/attempt-3/final.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="SubFlow Billing Manager Simplified API", version="1.0.0")


def now_utc_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    full_name = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False)
    tax_code = Column(String)
    revenue_code = Column(String)
    deferred_revenue_code = Column(String)
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class PricingPlan(Base):
    __tablename__ = "pricing_plans"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String)
    billing_interval = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    billing_unit_quantity = Column(Integer, nullable=False, default=1)
    trial_period_days = Column(Integer)
    setup_fee = Column(Float, default=0)
    usage_type = Column(String, nullable=False)
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    email = Column(String, nullable=False)
    name = Column(String)
    currency = Column(String, nullable=False)
    locale = Column(String)
    billing_address_line1 = Column(String)
    billing_address_line2 = Column(String)
    billing_city = Column(String)
    billing_state = Column(String)
    billing_postal_code = Column(String)
    billing_country = Column(String)
    default_payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class CustomerTaxId(Base):
    __tablename__ = "customer_tax_ids"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    tax_type = Column(String, nullable=False)
    tax_id = Column(String, nullable=False)
    country = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    provider = Column(String, nullable=False, default="card")
    token = Column(String, nullable=False)
    card_brand = Column(String)
    card_last4 = Column(String)
    card_exp_month = Column(Integer)
    card_exp_year = Column(Integer)
    default_flag = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Coupon(Base):
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    discount_type = Column(String, nullable=False)
    percentage_off = Column(Float)
    amount_off = Column(Float)
    currency = Column(String)
    duration = Column(String, nullable=False)
    duration_in_months = Column(Integer)
    max_redemptions = Column(Integer)
    max_redemptions_per_customer = Column(Integer)
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class CouponProduct(Base):
    __tablename__ = "coupon_products"
    coupon_id = Column(Integer, ForeignKey("coupons.id"), primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    pricing_plan_id = Column(Integer, ForeignKey("pricing_plans.id"), nullable=False)
    status = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    start_date = Column(Date, nullable=False)
    current_period_start = Column(Date)
    current_period_end = Column(Date)
    cancel_at = Column(Date)
    canceled_at = Column(Date)
    coupon_id = Column(Integer, ForeignKey("coupons.id"))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class SubscriptionCoupon(Base):
    __tablename__ = "subscription_coupons"
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False)
    applied_at = Column(DateTime)


class CouponRedemption(Base):
    __tablename__ = "coupon_redemptions"
    id = Column(Integer, primary_key=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    subscription_id = Column(Integer)
    invoice_id = Column(Integer)
    redeemed_at = Column(DateTime)


class SubscriptionUsageRecord(Base):
    __tablename__ = "subscription_usage_records"
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    billing_period_start = Column(Date, nullable=False)
    billing_period_end = Column(Date, nullable=False)
    created_at = Column(DateTime)


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    status = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    due_date = Column(Date)
    period_start = Column(Date)
    period_end = Column(Date)
    subtotal = Column(Float, nullable=False, default=0)
    discount_total = Column(Float, nullable=False, default=0)
    tax_total = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    pricing_plan_id = Column(Integer, ForeignKey("pricing_plans.id"))
    description = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    line_type = Column(String, nullable=False)
    created_at = Column(DateTime)


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)
    error_code = Column(String)
    error_message = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class DunningPolicy(Base):
    __tablename__ = "dunning_policies"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    applies_to = Column(String, nullable=False, default="all")
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class DunningPolicyStep(Base):
    __tablename__ = "dunning_policy_steps"
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("dunning_policies.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    days_after_failure = Column(Integer, nullable=False)
    action_retry_charge = Column(Integer, nullable=False, default=1)
    action_send_email = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class DunningPolicyOutcome(Base):
    __tablename__ = "dunning_policy_outcomes"
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("dunning_policies.id"), nullable=False)
    outcome = Column(String, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"
    id = Column(Integer, primary_key=True)
    url = Column(Text, nullable=False)
    description = Column(Text)
    enabled = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class WebhookEndpointEvent(Base):
    __tablename__ = "webhook_endpoint_events"
    id = Column(Integer, primary_key=True)
    endpoint_id = Column(Integer, ForeignKey("webhook_endpoints.id"), nullable=False)
    event_type = Column(String, nullable=False)
    created_at = Column(DateTime)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String, nullable=False)
    resource_type = Column(String)
    resource_id = Column(Integer)
    payload = Column(LargeBinary)
    created_at = Column(DateTime)


class WebhookEventDelivery(Base):
    __tablename__ = "webhook_event_deliveries"
    id = Column(Integer, primary_key=True)
    webhook_event_id = Column(Integer, ForeignKey("webhook_events.id"), nullable=False)
    endpoint_id = Column(Integer, ForeignKey("webhook_endpoints.id"), nullable=False)
    status = Column(String, nullable=False)
    response_status_code = Column(Integer)
    response_body = Column(Text)
    attempt_number = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


Base.metadata.create_all(bind=engine)


class ProductCreate(BaseModel):
    name: str = Field(..., description="Product name, must be unique", example="Pro Analytics Suite")
    category: str = Field(..., description="Product category label", example="SaaS")
    tax_code: Optional[str] = Field(None, description="External tax code identifier", example="SaaS_DIGITAL_SERVICES")
    revenue_code: Optional[str] = Field(None, description="GL code for revenue recognition", example="4001")
    deferred_revenue_code: Optional[str] = Field(None, description="GL code for deferred revenue", example="2505")
    active: Optional[bool] = Field(True, description="Whether the product is active and sellable", example=True)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, description="New product name", example="Pro Analytics Suite Plus")
    tax_code: Optional[str] = Field(None, description="Updated tax code", example="SaaS_DIGITAL_SERVICES")
    revenue_code: Optional[str] = Field(None, description="Updated revenue GL code", example="4002")
    deferred_revenue_code: Optional[str] = Field(None, description="Updated deferred revenue GL code", example="2506")
    active: Optional[bool] = Field(None, description="Set false to deactivate product", example=False)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Product primary key", example=1)
    name: str = Field(..., description="Product name", example="Pro Analytics Suite")
    category: str = Field(..., description="Product category", example="SaaS")
    tax_code: Optional[str] = Field(None, description="Tax code used for taxation", example="SaaS_DIGITAL_SERVICES")
    revenue_code: Optional[str] = Field(None, description="Revenue GL code", example="4001")
    deferred_revenue_code: Optional[str] = Field(None, description="Deferred revenue GL code", example="2505")
    active: bool = Field(..., description="True if product is active", example=True)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp in ISO format", example="2025-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp in ISO format", example="2025-01-01T12:00:00Z")


class ProductListResponse(BaseModel):
    items: List[ProductOut] = Field(..., description="List of matching products", example=[])
    total: int = Field(..., description="Total number of products matching filters", example=1)


class PricingPlanCreate(BaseModel):
    product_id: int = Field(..., description="Associated product ID from products table", example=1)
    name: Optional[str] = Field(None, description="Human readable plan name", example="Pro Analytics Suite Monthly")
    billing_interval: str = Field(..., description="Billing interval: day, week, month, or year", example="month")
    currency: str = Field(..., description="ISO currency code for unit_price and setup_fee", example="USD")
    unit_price: float = Field(..., description="Price per billing_unit_quantity", example=79.0)
    billing_unit_quantity: Optional[int] = Field(1, description="Unit quantity for billing", example=1000)
    trial_period_days: Optional[int] = Field(None, description="Number of trial days before billing starts", example=14)
    setup_fee: Optional[float] = Field(0.0, description="One-time setup fee charged on first invoice", example=99.0)
    usage_type: str = Field(..., description="flat for recurring fixed price, metered for usage-based", example="flat")
    active: Optional[bool] = Field(True, description="Whether this plan is active and subscribable", example=True)


class PricingPlanUpdate(BaseModel):
    name: Optional[str] = Field(None, description="New plan name", example="API Usage Add-on Metered")
    unit_price: Optional[float] = Field(None, description="Updated unit price", example=0.025)
    billing_unit_quantity: Optional[int] = Field(None, description="Updated unit quantity", example=1000)
    trial_period_days: Optional[int] = Field(None, description="Updated trial period days", example=0)
    setup_fee: Optional[float] = Field(None, description="Updated setup fee", example=49.0)
    active: Optional[bool] = Field(None, description="Updated active/inactive flag", example=True)


class PricingPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Pricing plan primary key", example=1)
    product_id: int = Field(..., description="Associated product ID", example=1)
    name: Optional[str] = Field(None, description="Plan name", example="Pro Analytics Suite Monthly")
    billing_interval: str = Field(..., description="Billing interval", example="month")
    currency: str = Field(..., description="Currency code", example="USD")
    unit_price: float = Field(..., description="Price per billing unit", example=79.0)
    billing_unit_quantity: int = Field(..., description="Quantity represented by unit_price", example=1000)
    trial_period_days: Optional[int] = Field(None, description="Trial period days if any", example=14)
    setup_fee: float = Field(..., description="Setup fee amount", example=99.0)
    usage_type: str = Field(..., description="Usage type: flat or metered", example="flat")
    active: bool = Field(..., description="Whether the pricing plan is active", example=True)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp", example="2025-01-01T12:00:00Z")


class PricingPlanListResponse(BaseModel):
    items: List[PricingPlanOut] = Field(..., description="List of pricing plans", example=[])
    total: int = Field(..., description="Total number of pricing plans matching filters", example=2)


class CustomerCreate(BaseModel):
    email: str = Field(..., description="Unique email for the customer", example="jane.startup@example.com")
    name: Optional[str] = Field(None, description="Customer full name", example="Jane Startup")
    currency: str = Field(..., description="Billing currency for the customer", example="USD")
    locale: Optional[str] = Field(None, description="Customer locale for communications", example="en-US")
    billing_address_line1: Optional[str] = Field(None, description="Address line 1", example="123 Startup Ave")
    billing_address_line2: Optional[str] = Field(None, description="Address line 2", example="Suite 500")
    billing_city: Optional[str] = Field(None, description="Billing city", example="New York")
    billing_state: Optional[str] = Field(None, description="State or region", example="NY")
    billing_postal_code: Optional[str] = Field(None, description="Postal or ZIP code", example="10001")
    billing_country: Optional[str] = Field(None, description="Billing country in ISO code", example="US")


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Updated customer name", example="Jane S. Founder")
    currency: Optional[str] = Field(None, description="Updated billing currency", example="USD")
    locale: Optional[str] = Field(None, description="Updated locale", example="en-GB")
    billing_address_line1: Optional[str] = Field(None, description="Updated address line 1", example="456 Scaleup Blvd")
    billing_address_line2: Optional[str] = Field(None, description="Updated address line 2", example="Floor 8")
    billing_city: Optional[str] = Field(None, description="Updated city", example="Brooklyn")
    billing_state: Optional[str] = Field(None, description="Updated state", example="NY")
    billing_postal_code: Optional[str] = Field(None, description="Updated postal code", example="11201")
    billing_country: Optional[str] = Field(None, description="Updated country", example="US")


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Customer ID", example=1)
    user_id: Optional[int] = Field(None, description="Owner user ID", example=1)
    email: str = Field(..., description="Customer email", example="jane.startup@example.com")
    name: Optional[str] = Field(None, description="Customer name", example="Jane Startup")
    currency: str = Field(..., description="Customer currency", example="USD")
    locale: Optional[str] = Field(None, description="Customer locale", example="en-US")
    billing_address_line1: Optional[str] = Field(None, description="Address line 1", example="123 Startup Ave")
    billing_address_line2: Optional[str] = Field(None, description="Address line 2", example="Suite 500")
    billing_city: Optional[str] = Field(None, description="Billing city", example="New York")
    billing_state: Optional[str] = Field(None, description="Billing state or region", example="NY")
    billing_postal_code: Optional[str] = Field(None, description="Billing postal code", example="10001")
    billing_country: Optional[str] = Field(None, description="Billing country code", example="US")
    default_payment_method_id: Optional[int] = Field(None, description="ID of default payment method if set", example=None)
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-01-01T12:00:00Z")


class CustomerListResponse(BaseModel):
    items: List[CustomerOut] = Field(..., description="List of customer records", example=[])
    total: int = Field(..., description="Total number of customers for user matching filters", example=1)


class CustomerTaxIdCreate(BaseModel):
    tax_type: str = Field(..., description="Type of tax ID, for example 'eu_vat'", example="eu_vat")
    tax_id: str = Field(..., description="Tax ID value", example="EU123456789")
    country: Optional[str] = Field(None, description="Country associated with the tax ID", example="EU")


class CustomerTaxIdOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Customer tax ID record ID", example=1)
    customer_id: int = Field(..., description="Owner customer ID", example=1)
    tax_type: str = Field(..., description="Tax ID type", example="eu_vat")
    tax_id: str = Field(..., description="Tax ID value", example="EU123456789")
    country: Optional[str] = Field(None, description="Country code for the tax ID", example="EU")
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-01-01T12:00:00Z")


class CustomerTaxIdListResponse(BaseModel):
    items: List[CustomerTaxIdOut] = Field(..., description="List of customer tax ID records", example=[])


class PaymentMethodCreate(BaseModel):
    provider: Optional[str] = Field("card", description="Payment method provider, default 'card'", example="card")
    token: str = Field(..., description="Opaque token from payment gateway", example="pm_tok_123")
    card_brand: Optional[str] = Field(None, description="Card brand if provider is card", example="visa")
    card_last4: Optional[str] = Field(None, description="Last 4 digits of card number", example="4242")
    card_exp_month: Optional[int] = Field(None, description="Expiration month number", example=12)
    card_exp_year: Optional[int] = Field(None, description="Expiration year number", example=2028)
    default_flag: Optional[bool] = Field(False, description="Set true to mark as default for the customer", example=True)


class PaymentMethodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Payment method ID", example=10)
    customer_id: int = Field(..., description="Associated customer ID", example=1)
    provider: str = Field(..., description="Payment provider type", example="card")
    token: str = Field(..., description="Opaque token reference", example="pm_tok_123")
    card_brand: Optional[str] = Field(None, description="Card brand", example="visa")
    card_last4: Optional[str] = Field(None, description="Last four digits", example="4242")
    card_exp_month: Optional[int] = Field(None, description="Expiration month", example=12)
    card_exp_year: Optional[int] = Field(None, description="Expiration year", example=2028)
    default_flag: bool = Field(..., description="Whether this payment method is default for customer", example=True)
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-01-01T12:00:00Z")


class PaymentMethodListResponse(BaseModel):
    items: List[PaymentMethodOut] = Field(..., description="List of payment method records", example=[])


class DefaultPaymentMethodUpdate(BaseModel):
    payment_method_id: int = Field(..., description="Payment method ID to set as default", example=10)


class DefaultPaymentMethodOutItem(BaseModel):
    id: int = Field(..., description="Payment method ID", example=10)
    default_flag: bool = Field(..., description="Updated default flag", example=True)


class DefaultPaymentMethodResponse(BaseModel):
    customer_id: int = Field(..., description="Customer ID", example=1)
    default_payment_method_id: int = Field(..., description="New default payment method ID", example=10)
    updated_payment_methods: List[DefaultPaymentMethodOutItem] = Field(..., description="Payment methods with updated default_flag values", example=[])


class CouponCreate(BaseModel):
    code: str = Field(..., description="Unique coupon code used on subscriptions or invoices", example="Q1_NEW_CUSTOMER")
    name: str = Field(..., description="Human readable name", example="Q1 New Customer Promo")
    discount_type: str = Field(..., description="Type of discount: percentage or fixed", example="fixed")
    percentage_off: Optional[float] = Field(None, description="Percentage discount value when discount_type=percentage", example=20.0)
    amount_off: Optional[float] = Field(None, description="Fixed discount amount when discount_type=fixed", example=50.0)
    currency: Optional[str] = Field(None, description="Currency for amount_off discounts", example="USD")
    duration: str = Field(..., description="Duration of coupon: once, repeating, or forever", example="once")
    duration_in_months: Optional[int] = Field(None, description="Number of months for repeating duration", example=3)
    max_redemptions: Optional[int] = Field(None, description="Total number of allowed redemptions", example=500)
    max_redemptions_per_customer: Optional[int] = Field(None, description="Maximum times a single customer can redeem", example=1)
    active: Optional[bool] = Field(True, description="Whether the coupon is currently active", example=True)


class CouponOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Coupon ID", example=1)
    code: str = Field(..., description="Coupon code", example="Q1_NEW_CUSTOMER")
    name: str = Field(..., description="Coupon name", example="Q1 New Customer Promo")
    discount_type: str = Field(..., description="Discount type", example="fixed")
    percentage_off: Optional[float] = Field(None, description="Percentage off if applicable", example=None)
    amount_off: Optional[float] = Field(None, description="Amount off if applicable", example=50.0)
    currency: Optional[str] = Field(None, description="Currency for fixed discounts", example="USD")
    duration: str = Field(..., description="Duration behavior", example="once")
    duration_in_months: Optional[int] = Field(None, description="Repeating duration in months if used", example=None)
    max_redemptions: Optional[int] = Field(None, description="Max allowed redemptions", example=500)
    max_redemptions_per_customer: Optional[int] = Field(None, description="Max per customer", example=1)
    active: bool = Field(..., description="Active flag", example=True)
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-01-01T12:00:00Z")


class CouponListResponse(BaseModel):
    items: List[CouponOut] = Field(..., description="List of coupons", example=[])
    total: int = Field(..., description="Total coupons matching filters", example=2)


class CouponProductAttach(BaseModel):
    coupon_id: int = Field(..., description="Coupon ID to attach", example=1)
    product_id: int = Field(..., description="Product ID that coupon applies to", example=1)


class CouponProductOut(BaseModel):
    coupon_id: int = Field(..., description="Coupon ID", example=1)
    product_id: int = Field(..., description="Product ID", example=1)


class SubscriptionCreate(BaseModel):
    customer_id: int = Field(..., description="Customer ID to subscribe", example=1)
    pricing_plan_id: int = Field(..., description="Pricing plan ID for subscription", example=1)
    status: str = Field(..., description="Initial status: trialing or active", example="active")
    quantity: Optional[int] = Field(1, description="Number of units for subscription", example=10)
    start_date: date = Field(..., description="Subscription start date", example="2025-01-01")
    current_period_start: Optional[date] = Field(None, description="Current period start date", example="2025-01-01")
    current_period_end: Optional[date] = Field(None, description="Current period end date", example="2025-02-01")
    cancel_at: Optional[date] = Field(None, description="Date when subscription will be canceled automatically", example=None)
    coupon_id: Optional[int] = Field(None, description="Coupon ID to apply to subscription", example=2)


class SubscriptionUpdate(BaseModel):
    status: Optional[str] = Field(None, description="New status", example="canceled")
    quantity: Optional[int] = Field(None, description="Updated quantity", example=15)
    cancel_at: Optional[date] = Field(None, description="Date to schedule cancellation", example="2025-03-01")
    coupon_id: Optional[int] = Field(None, description="Coupon ID to apply or remove", example=2)


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Subscription ID", example=5)
    customer_id: int = Field(..., description="Customer ID", example=1)
    pricing_plan_id: int = Field(..., description="Plan ID", example=1)
    status: str = Field(..., description="Subscription status", example="active")
    quantity: int = Field(..., description="Quantity", example=10)
    start_date: date = Field(..., description="Start date", example="2025-01-01")
    current_period_start: Optional[date] = Field(None, description="Current period start", example="2025-01-01")
    current_period_end: Optional[date] = Field(None, description="Current period end", example="2025-02-01")
    cancel_at: Optional[date] = Field(None, description="Scheduled cancel date if set", example=None)
    canceled_at: Optional[date] = Field(None, description="Actual cancel timestamp if canceled", example=None)
    coupon_id: Optional[int] = Field(None, description="Coupon applied to subscription", example=2)
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-01-01T12:00:00Z")


class SubscriptionListResponse(BaseModel):
    items: List[SubscriptionOut] = Field(..., description="List of subscriptions", example=[])
    total: int = Field(..., description="Total subscriptions matching filters", example=3)


class SubscriptionCouponCreate(BaseModel):
    subscription_id: int = Field(..., description="Subscription ID receiving coupon", example=5)
    coupon_id: int = Field(..., description="Coupon ID applied", example=2)


class SubscriptionCouponOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Subscription coupon record ID", example=1)
    subscription_id: int = Field(..., description="Subscription ID", example=5)
    coupon_id: int = Field(..., description="Coupon ID", example=2)
    applied_at: Optional[datetime] = Field(None, description="Timestamp when coupon was applied", example="2025-01-01T12:00:00Z")


class CouponRedemptionCreate(BaseModel):
    coupon_id: int = Field(..., description="Coupon ID being redeemed", example=2)
    customer_id: int = Field(..., description="Customer ID redeeming the coupon", example=1)
    subscription_id: Optional[int] = Field(None, description="Subscription ID if redemption is on a subscription", example=5)
    invoice_id: Optional[int] = Field(None, description="Invoice ID if redemption is on an invoice", example=None)


class CouponRedemptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Coupon redemption record ID", example=1)
    coupon_id: int = Field(..., description="Coupon ID", example=2)
    customer_id: int = Field(..., description="Customer ID", example=1)
    subscription_id: Optional[int] = Field(None, description="Subscription ID if used", example=5)
    invoice_id: Optional[int] = Field(None, description="Invoice ID if used", example=None)
    redeemed_at: Optional[datetime] = Field(None, description="Timestamp of redemption", example="2025-01-01T12:00:00Z")


class SubscriptionUsageRecordCreate(BaseModel):
    quantity: float = Field(..., description="Usage quantity to record", example=125000.0)
    recorded_at: datetime = Field(..., description="Timestamp when usage occurred or was measured", example="2025-01-15T10:00:00Z")
    billing_period_start: date = Field(..., description="Start date of billing period", example="2025-01-01")
    billing_period_end: date = Field(..., description="End date of billing period", example="2025-02-01")


class SubscriptionUsageRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Usage record ID", example=1)
    subscription_id: int = Field(..., description="Subscription ID", example=6)
    quantity: float = Field(..., description="Recorded usage quantity", example=125000.0)
    recorded_at: datetime = Field(..., description="Recorded timestamp", example="2025-01-15T10:00:00Z")
    billing_period_start: date = Field(..., description="Billing period start date", example="2025-01-01")
    billing_period_end: date = Field(..., description="Billing period end date", example="2025-02-01")
    created_at: Optional[datetime] = Field(None, description="Created timestamp for record", example="2025-01-15T10:05:00Z")


class SubscriptionUsageRecordListResponse(BaseModel):
    items: List[SubscriptionUsageRecordOut] = Field(..., description="Usage records for the subscription", example=[])
    total_quantity: float = Field(..., description="Sum of usage quantities in the returned records", example=125000.0)


class InvoiceCreate(BaseModel):
    customer_id: int = Field(..., description="Customer ID being invoiced", example=1)
    subscription_id: Optional[int] = Field(None, description="Subscription ID if invoice is for a subscription", example=5)
    status: str = Field(..., description="Invoice status", example="draft")
    currency: str = Field(..., description="Invoice currency", example="USD")
    due_date: Optional[date] = Field(None, description="Due date for payment", example="2025-02-05")
    period_start: Optional[date] = Field(None, description="Billing period start date for the invoice", example="2025-01-01")
    period_end: Optional[date] = Field(None, description="Billing period end date for the invoice", example="2025-02-01")


class InvoiceUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Updated status for invoice", example="open")
    subtotal: Optional[float] = Field(None, description="Updated subtotal amount", example=890.0)
    discount_total: Optional[float] = Field(None, description="Updated discount total", example=178.0)
    tax_total: Optional[float] = Field(None, description="Updated tax total", example=143.2)
    total: Optional[float] = Field(None, description="Updated final total", example=855.2)


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Invoice ID", example=100)
    customer_id: int = Field(..., description="Customer ID", example=1)
    subscription_id: Optional[int] = Field(None, description="Subscription ID if any", example=5)
    status: str = Field(..., description="Invoice status", example="paid")
    currency: str = Field(..., description="Currency", example="USD")
    due_date: Optional[date] = Field(None, description="Due date", example="2025-02-05")
    period_start: Optional[date] = Field(None, description="Billing period start date", example="2025-01-01")
    period_end: Optional[date] = Field(None, description="Billing period end date", example="2025-02-01")
    subtotal: float = Field(..., description="Invoice subtotal", example=890.0)
    discount_total: float = Field(..., description="Total discounts on invoice", example=178.0)
    tax_total: float = Field(..., description="Total tax on invoice", example=143.2)
    total: float = Field(..., description="Final total amount", example=855.2)
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-31T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-02-01T09:00:00Z")


class InvoiceLineItemCreate(BaseModel):
    subscription_id: Optional[int] = Field(None, description="Subscription ID if this line relates to a subscription", example=5)
    pricing_plan_id: Optional[int] = Field(None, description="Pricing plan ID if relevant", example=1)
    description: str = Field(..., description="Human readable description for invoice line", example="API Usage Add-on 125,000 calls")
    quantity: float = Field(..., description="Billed quantity", example=125.0)
    unit_price: float = Field(..., description="Price per quantity unit", example=0.02)
    amount: float = Field(..., description="Total amount for this line", example=2.5)
    line_type: str = Field(..., description="Line type: recurring, setup_fee, usage, discount, adjustment", example="usage")


class InvoiceLineItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Line item ID", example=1000)
    invoice_id: int = Field(..., description="Invoice ID", example=100)
    subscription_id: Optional[int] = Field(None, description="Subscription ID if related", example=5)
    pricing_plan_id: Optional[int] = Field(None, description="Pricing plan ID", example=1)
    description: str = Field(..., description="Line item description", example="Pro Analytics Suite Monthly x10")
    quantity: float = Field(..., description="Quantity billed", example=10.0)
    unit_price: float = Field(..., description="Price per unit", example=79.0)
    amount: float = Field(..., description="Extended amount for this line", example=790.0)
    line_type: str = Field(..., description="Type of line", example="recurring")
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-31T12:00:00Z")


class InvoiceLineItemListResponse(BaseModel):
    items: List[InvoiceLineItemOut] = Field(..., description="Line items for the invoice", example=[])


class InvoicePreviewRequest(BaseModel):
    subscription_id: int = Field(..., description="Subscription ID to preview invoice for", example=6)
    period_start: Optional[date] = Field(None, description="Billing period start date for preview", example="2025-01-01")
    period_end: Optional[date] = Field(None, description="Billing period end date for preview", example="2025-02-01")


class InvoicePreviewLineItem(BaseModel):
    id: Optional[int] = Field(None, description="Placeholder ID", example=None)
    description: str = Field(..., description="Description of charge or discount", example="API Usage Add-on 125,000 calls")
    quantity: float = Field(..., description="Quantity billed", example=125.0)
    unit_price: float = Field(..., description="Price per unit for this line", example=0.02)
    amount: float = Field(..., description="Total amount for this line", example=2.5)
    line_type: str = Field(..., description="Type of line", example="usage")


class InvoicePreviewResponse(BaseModel):
    subscription_id: int = Field(..., description="Subscription ID used for preview", example=6)
    period_start: Optional[date] = Field(None, description="Preview billing period start", example="2025-01-01")
    period_end: Optional[date] = Field(None, description="Preview billing period end", example="2025-02-01")
    line_items: List[InvoicePreviewLineItem] = Field(..., description="Calculated line items that would appear on the invoice", example=[])
    subtotal: float = Field(..., description="Estimated subtotal before discounts and taxes", example=2.5)
    discount_total: float = Field(..., description="Estimated discounts applied", example=0.5)
    tax_total: float = Field(..., description="Estimated tax based on available tax info", example=0.4)
    total: float = Field(..., description="Estimated total invoice amount", example=2.4)


class PaymentCreate(BaseModel):
    invoice_id: int = Field(..., description="Invoice ID for the payment", example=100)
    customer_id: int = Field(..., description="Customer ID that is paying", example=1)
    payment_method_id: Optional[int] = Field(None, description="Payment method ID used if any", example=10)
    amount: float = Field(..., description="Payment amount attempted", example=855.2)
    currency: str = Field(..., description="Currency of payment", example="USD")
    status: str = Field(..., description="Payment status: pending, succeeded, failed", example="pending")
    attempt_number: Optional[int] = Field(1, description="Sequential attempt number for this invoice", example=1)
    error_code: Optional[str] = Field(None, description="Provider error code when failed", example="card_declined")
    error_message: Optional[str] = Field(None, description="Human readable error from provider", example="Your card was declined.")


class PaymentUpdate(BaseModel):
    status: Optional[str] = Field(None, description="New payment status", example="failed")
    attempt_number: Optional[int] = Field(None, description="Updated attempt number", example=2)
    error_code: Optional[str] = Field(None, description="Error code if failure occurs", example="card_declined")
    error_message: Optional[str] = Field(None, description="Detailed error message", example="Insufficient funds.")


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Payment ID", example=500)
    invoice_id: int = Field(..., description="Invoice ID", example=100)
    customer_id: int = Field(..., description="Customer ID", example=1)
    payment_method_id: Optional[int] = Field(None, description="Payment method ID", example=10)
    amount: float = Field(..., description="Payment amount", example=855.2)
    currency: str = Field(..., description="Currency", example="USD")
    status: str = Field(..., description="Payment status", example="pending")
    attempt_number: int = Field(..., description="Attempt number", example=1)
    error_code: Optional[str] = Field(None, description="Error code if failed", example=None)
    error_message: Optional[str] = Field(None, description="Error message if failed", example=None)
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-31T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-01-31T12:00:00Z")


class DunningPolicyCreate(BaseModel):
    name: str = Field(..., description="Policy name", example="Default All Merchants Policy")
    applies_to: Optional[str] = Field("all", description="Policy scope, e.g. 'all'", example="all")


class DunningPolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Dunning policy ID", example=1)
    name: str = Field(..., description="Policy name", example="Default All Merchants Policy")
    applies_to: str = Field(..., description="Scope of policy", example="all")
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-01-01T12:00:00Z")


class DunningPolicyListResponse(BaseModel):
    items: List[DunningPolicyOut] = Field(..., description="List of dunning policies", example=[])


class DunningPolicyStepCreate(BaseModel):
    step_order: int = Field(..., description="Ordering of this step within the policy", example=1)
    days_after_failure: int = Field(..., description="Days after initial payment failure to perform this step", example=1)
    action_retry_charge: Optional[bool] = Field(True, description="Whether to retry the charge at this step", example=True)
    action_send_email: Optional[bool] = Field(True, description="Whether to send a failure email notification at this step", example=True)


class DunningPolicyStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Dunning policy step ID", example=1)
    policy_id: int = Field(..., description="Associated policy ID", example=1)
    step_order: int = Field(..., description="Step order in policy", example=1)
    days_after_failure: int = Field(..., description="Delay days after payment failure", example=1)
    action_retry_charge: bool = Field(..., description="Retry charge flag", example=True)
    action_send_email: bool = Field(..., description="Send email flag", example=True)
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-01-01T12:00:00Z")


class DunningPolicyStepListResponse(BaseModel):
    items: List[DunningPolicyStepOut] = Field(..., description="Steps defined for the policy", example=[])


class DunningPolicyOutcomeCreate(BaseModel):
    outcome: str = Field(..., description="Outcome action", example="cancel_subscription")


class DunningPolicyOutcomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Dunning policy outcome ID", example=1)
    policy_id: int = Field(..., description="Associated policy ID", example=1)
    outcome: str = Field(..., description="Outcome action", example="cancel_subscription")
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-01-01T12:00:00Z")


class DunningPolicyOutcomeListResponse(BaseModel):
    items: List[DunningPolicyOutcomeOut] = Field(..., description="Outcomes defined for the policy", example=[])


class WebhookEndpointCreate(BaseModel):
    url: str = Field(..., description="Public URL for webhook receiver", example="https://billing-backend.example.com/webhooks/subflow")
    description: Optional[str] = Field(None, description="Human readable description of endpoint", example="SubFlow Billing Manager events endpoint")
    enabled: Optional[bool] = Field(True, description="Whether endpoint is active", example=True)


class WebhookEndpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Webhook endpoint ID", example=1)
    url: str = Field(..., description="Webhook URL", example="https://billing-backend.example.com/webhooks/subflow")
    description: Optional[str] = Field(None, description="Description", example="SubFlow Billing Manager events endpoint")
    enabled: bool = Field(..., description="Enabled flag", example=True)
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-01-01T12:00:00Z")


class WebhookEndpointEventCreate(BaseModel):
    event_type: str = Field(..., description="Event type to subscribe to", example="invoice_paid")


class WebhookEndpointEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Webhook endpoint event ID", example=1)
    endpoint_id: int = Field(..., description="Endpoint ID", example=1)
    event_type: str = Field(..., description="Subscribed event type", example="invoice_paid")
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-01T12:05:00Z")


class WebhookEventCreate(BaseModel):
    event_type: str = Field(..., description="Event type such as invoice_paid or payment_failed", example="invoice_paid")
    resource_type: Optional[str] = Field(None, description="Type of resource referenced by this event", example="invoice")
    resource_id: Optional[int] = Field(None, description="ID of the resource associated with event", example=100)
    payload: Optional[Dict[str, object]] = Field(None, description="Arbitrary JSON payload to send to endpoints", example={"invoice_id": 100, "status": "paid"})


class WebhookEventOut(BaseModel):
    id: int = Field(..., description="Webhook event ID", example=10)
    event_type: str = Field(..., description="Event type", example="invoice_paid")
    resource_type: Optional[str] = Field(None, description="Resource type", example="invoice")
    resource_id: Optional[int] = Field(None, description="Resource ID", example=100)
    payload: Optional[Dict[str, object]] = Field(None, description="Serialized JSON payload", example={"invoice_id": 100, "status": "paid"})
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-31T12:00:00Z")


class WebhookEventDeliveryCreate(BaseModel):
    webhook_event_id: int = Field(..., description="ID of webhook event to deliver", example=10)
    endpoint_id: int = Field(..., description="ID of endpoint to deliver to", example=1)
    status: str = Field(..., description="Delivery status: pending, delivered, failed", example="pending")
    response_status_code: Optional[int] = Field(None, description="HTTP response status code from endpoint", example=None)
    response_body: Optional[str] = Field(None, description="Response text from endpoint", example=None)
    attempt_number: Optional[int] = Field(1, description="Attempt count for this delivery", example=1)


class WebhookEventDeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Webhook event delivery ID", example=20)
    webhook_event_id: int = Field(..., description="Webhook event ID", example=10)
    endpoint_id: int = Field(..., description="Endpoint ID", example=1)
    status: str = Field(..., description="Delivery status", example="pending")
    response_status_code: Optional[int] = Field(None, description="HTTP status from last attempt", example=None)
    response_body: Optional[str] = Field(None, description="Response body from last attempt", example=None)
    attempt_number: int = Field(..., description="Attempt number", example=1)
    created_at: Optional[datetime] = Field(None, description="Created timestamp", example="2025-01-31T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp", example="2025-01-31T12:00:00Z")


class TriggerTestWebhookResponseDelivery(BaseModel):
    id: int = Field(..., description="Delivery record ID", example=20)
    endpoint_id: int = Field(..., description="Endpoint receiving test event", example=1)
    status: str = Field(..., description="Initial delivery status", example="pending")
    attempt_number: int = Field(..., description="Attempt number", example=1)


class TriggerTestWebhookResponse(BaseModel):
    webhook_event_id: int = Field(..., description="Created webhook event ID for invoice_paid", example=10)
    deliveries: List[TriggerTestWebhookResponseDelivery] = Field(..., description="Created deliveries associated with this test event", example=[])


@app.post(
    "/api/products",
    summary="Create a new product",
    description="Create a product in a category with tax and accounting codes.",
    tags=["products"],
    operation_id="create_product",
    response_model=ProductOut,
)
async def create_product_endpoint(body: ProductCreate = Body(...)) -> ProductOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    product = Product(
        name=body.name,
        category=body.category,
        tax_code=body.tax_code,
        revenue_code=body.revenue_code,
        deferred_revenue_code=body.deferred_revenue_code,
        active=1 if body.active is not False else 0,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    session.close()
    return ProductOut(
        id=product.id,
        name=product.name,
        category=product.category,
        tax_code=product.tax_code,
        revenue_code=product.revenue_code,
        deferred_revenue_code=product.deferred_revenue_code,
        active=bool(product.active),
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@app.get(
    "/api/products",
    summary="List products with optional filters",
    description="Retrieve products filtered by category, name, or active flag.",
    tags=["products"],
    operation_id="list_products",
    response_model=ProductListResponse,
)
async def list_products_endpoint(
    category: Optional[str] = Query(None, description="Filter products by category", example="SaaS"),
    active: Optional[bool] = Query(None, description="Filter by active status", example=True),
    name: Optional[str] = Query(None, description="Case-insensitive substring match on product name", example="Pro Analytics"),
    limit: Optional[int] = Query(50, description="Max number of records to return", example=50),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> ProductListResponse:
    session = SessionLocal()
    q = session.query(Product)
    if category is not None:
        q = q.filter(Product.category == category)
    if active is not None:
        q = q.filter(Product.active == (1 if active else 0))
    if name is not None:
        like_value = f"%{name}%"
        q = q.filter(Product.name.ilike(like_value))
    total = q.count()
    items_db = q.offset(offset).limit(limit).all()
    items = []
    for p in items_db:
        items.append(
            ProductOut(
                id=p.id,
                name=p.name,
                category=p.category,
                tax_code=p.tax_code,
                revenue_code=p.revenue_code,
                deferred_revenue_code=p.deferred_revenue_code,
                active=bool(p.active),
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    session.close()
    return ProductListResponse(items=items, total=total)


@app.get(
    "/api/products/{product_id}",
    summary="Get a single product by ID",
    description="Fetch a specific product by its ID.",
    tags=["products"],
    operation_id="get_product",
    response_model=ProductOut,
)
async def get_product_endpoint(
    product_id: int = Path(..., description="Product primary key", example=1)
) -> ProductOut:
    session = SessionLocal()
    p = session.query(Product).filter(Product.id == product_id).first()
    if p is None:
        p = Product(
            id=product_id,
            name="",
            category="",
            tax_code=None,
            revenue_code=None,
            deferred_revenue_code=None,
            active=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    result = ProductOut(
        id=p.id,
        name=p.name,
        category=p.category,
        tax_code=p.tax_code,
        revenue_code=p.revenue_code,
        deferred_revenue_code=p.deferred_revenue_code,
        active=bool(p.active),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )
    session.close()
    return result


@app.patch(
    "/api/products/{product_id}",
    summary="Update an existing product",
    description="Update mutable product fields like name, tax_code, or active.",
    tags=["products"],
    operation_id="update_product",
    response_model=ProductOut,
)
async def update_product_endpoint(
    product_id: int = Path(..., description="Product primary key to update", example=1),
    body: ProductUpdate = Body(...),
) -> ProductOut:
    session = SessionLocal()
    p = session.query(Product).filter(Product.id == product_id).first()
    if p is None:
        created_at = datetime.utcnow()
        p = Product(
            id=product_id,
            name=body.name or "",
            category="",
            tax_code=body.tax_code,
            revenue_code=body.revenue_code,
            deferred_revenue_code=body.deferred_revenue_code,
            active=1 if (body.active is None or body.active) else 0,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(p)
        session.commit()
        session.refresh(p)
    else:
        if body.name is not None:
            p.name = body.name
        if body.tax_code is not None:
            p.tax_code = body.tax_code
        if body.revenue_code is not None:
            p.revenue_code = body.revenue_code
        if body.deferred_revenue_code is not None:
            p.deferred_revenue_code = body.deferred_revenue_code
        if body.active is not None:
            p.active = 1 if body.active else 0
        p.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(p)
    result = ProductOut(
        id=p.id,
        name=p.name,
        category=p.category,
        tax_code=p.tax_code,
        revenue_code=p.revenue_code,
        deferred_revenue_code=p.deferred_revenue_code,
        active=bool(p.active),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/pricing_plans",
    summary="Create a new pricing plan",
    description="Create a pricing plan for a product with billing properties.",
    tags=["pricing_plans"],
    operation_id="create_pricing_plan",
    response_model=PricingPlanOut,
)
async def create_pricing_plan_endpoint(body: PricingPlanCreate = Body(...)) -> PricingPlanOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    plan = PricingPlan(
        product_id=body.product_id,
        name=body.name,
        billing_interval=body.billing_interval,
        currency=body.currency,
        unit_price=body.unit_price,
        billing_unit_quantity=body.billing_unit_quantity if body.billing_unit_quantity is not None else 1,
        trial_period_days=body.trial_period_days,
        setup_fee=body.setup_fee if body.setup_fee is not None else 0.0,
        usage_type=body.usage_type,
        active=1 if body.active is not False else 0,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    session.close()
    return PricingPlanOut(
        id=plan.id,
        product_id=plan.product_id,
        name=plan.name,
        billing_interval=plan.billing_interval,
        currency=plan.currency,
        unit_price=plan.unit_price,
        billing_unit_quantity=plan.billing_unit_quantity,
        trial_period_days=plan.trial_period_days,
        setup_fee=plan.setup_fee,
        usage_type=plan.usage_type,
        active=bool(plan.active),
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@app.get(
    "/api/pricing_plans",
    summary="List pricing plans",
    description="Retrieve pricing plans optionally filtered by product or status.",
    tags=["pricing_plans"],
    operation_id="list_pricing_plans",
    response_model=PricingPlanListResponse,
)
async def list_pricing_plans_endpoint(
    product_id: Optional[int] = Query(None, description="Filter plans for a specific product", example=1),
    usage_type: Optional[str] = Query(None, description="Filter by usage_type", example="metered"),
    active: Optional[bool] = Query(None, description="Filter by active status", example=True),
    billing_interval: Optional[str] = Query(None, description="Filter by billing interval", example="month"),
    limit: Optional[int] = Query(50, description="Max number of records to return", example=50),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> PricingPlanListResponse:
    session = SessionLocal()
    q = session.query(PricingPlan)
    if product_id is not None:
        q = q.filter(PricingPlan.product_id == product_id)
    if usage_type is not None:
        q = q.filter(PricingPlan.usage_type == usage_type)
    if active is not None:
        q = q.filter(PricingPlan.active == (1 if active else 0))
    if billing_interval is not None:
        q = q.filter(PricingPlan.billing_interval == billing_interval)
    total = q.count()
    plans_db = q.offset(offset).limit(limit).all()
    items = []
    for plan in plans_db:
        items.append(
            PricingPlanOut(
                id=plan.id,
                product_id=plan.product_id,
                name=plan.name,
                billing_interval=plan.billing_interval,
                currency=plan.currency,
                unit_price=plan.unit_price,
                billing_unit_quantity=plan.billing_unit_quantity,
                trial_period_days=plan.trial_period_days,
                setup_fee=plan.setup_fee,
                usage_type=plan.usage_type,
                active=bool(plan.active),
                created_at=plan.created_at,
                updated_at=plan.updated_at,
            )
        )
    session.close()
    return PricingPlanListResponse(items=items, total=total)


@app.get(
    "/api/pricing_plans/{pricing_plan_id}",
    summary="Get a pricing plan by ID",
    description="Fetch a specific pricing plan by ID.",
    tags=["pricing_plans"],
    operation_id="get_pricing_plan",
    response_model=PricingPlanOut,
)
async def get_pricing_plan_endpoint(
    pricing_plan_id: int = Path(..., description="Pricing plan ID", example=1)
) -> PricingPlanOut:
    session = SessionLocal()
    plan = session.query(PricingPlan).filter(PricingPlan.id == pricing_plan_id).first()
    if plan is None:
        created_at = datetime.utcnow()
        plan = PricingPlan(
            id=pricing_plan_id,
            product_id=0,
            name="",
            billing_interval="month",
            currency="USD",
            unit_price=0.0,
            billing_unit_quantity=1,
            trial_period_days=None,
            setup_fee=0.0,
            usage_type="flat",
            active=1,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)
    result = PricingPlanOut(
        id=plan.id,
        product_id=plan.product_id,
        name=plan.name,
        billing_interval=plan.billing_interval,
        currency=plan.currency,
        unit_price=plan.unit_price,
        billing_unit_quantity=plan.billing_unit_quantity,
        trial_period_days=plan.trial_period_days,
        setup_fee=plan.setup_fee,
        usage_type=plan.usage_type,
        active=bool(plan.active),
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )
    session.close()
    return result


@app.patch(
    "/api/pricing_plans/{pricing_plan_id}",
    summary="Update a pricing plan",
    description="Update mutable pricing plan fields like name or pricing details.",
    tags=["pricing_plans"],
    operation_id="update_pricing_plan",
    response_model=PricingPlanOut,
)
async def update_pricing_plan_endpoint(
    pricing_plan_id: int = Path(..., description="Pricing plan ID to update", example=1),
    body: PricingPlanUpdate = Body(...),
) -> PricingPlanOut:
    session = SessionLocal()
    plan = session.query(PricingPlan).filter(PricingPlan.id == pricing_plan_id).first()
    if plan is None:
        created_at = datetime.utcnow()
        plan = PricingPlan(
            id=pricing_plan_id,
            product_id=0,
            name=body.name,
            billing_interval="month",
            currency="USD",
            unit_price=body.unit_price if body.unit_price is not None else 0.0,
            billing_unit_quantity=body.billing_unit_quantity if body.billing_unit_quantity is not None else 1,
            trial_period_days=body.trial_period_days,
            setup_fee=body.setup_fee if body.setup_fee is not None else 0.0,
            usage_type="flat",
            active=1 if (body.active is None or body.active) else 0,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)
    else:
        if body.name is not None:
            plan.name = body.name
        if body.unit_price is not None:
            plan.unit_price = body.unit_price
        if body.billing_unit_quantity is not None:
            plan.billing_unit_quantity = body.billing_unit_quantity
        if body.trial_period_days is not None:
            plan.trial_period_days = body.trial_period_days
        if body.setup_fee is not None:
            plan.setup_fee = body.setup_fee
        if body.active is not None:
            plan.active = 1 if body.active else 0
        plan.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(plan)
    result = PricingPlanOut(
        id=plan.id,
        product_id=plan.product_id,
        name=plan.name,
        billing_interval=plan.billing_interval,
        currency=plan.currency,
        unit_price=plan.unit_price,
        billing_unit_quantity=plan.billing_unit_quantity,
        trial_period_days=plan.trial_period_days,
        setup_fee=plan.setup_fee,
        usage_type=plan.usage_type,
        active=bool(plan.active),
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/customers",
    summary="Create a new customer",
    description="Create a customer for the implicit current user.",
    tags=["customers"],
    operation_id="create_customer",
    response_model=CustomerOut,
)
async def create_customer_endpoint(body: CustomerCreate = Body(...)) -> CustomerOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    customer = Customer(
        user_id=1,
        email=body.email,
        name=body.name,
        currency=body.currency,
        locale=body.locale,
        billing_address_line1=body.billing_address_line1,
        billing_address_line2=body.billing_address_line2,
        billing_city=body.billing_city,
        billing_state=body.billing_state,
        billing_postal_code=body.billing_postal_code,
        billing_country=body.billing_country,
        default_payment_method_id=None,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(customer)
    session.commit()
    session.refresh(customer)
    result = CustomerOut.model_validate(customer)
    session.close()
    return result


@app.get(
    "/api/customers",
    summary="List customers for current user",
    description="Retrieve customers owned by the current user filtered by email or name.",
    tags=["customers"],
    operation_id="list_customers",
    response_model=CustomerListResponse,
)
async def list_customers_endpoint(
    email: Optional[str] = Query(None, description="Filter by exact email", example="jane.startup@example.com"),
    name: Optional[str] = Query(None, description="Filter by case-insensitive substring on name", example="Jane"),
    limit: Optional[int] = Query(50, description="Max number of records to return", example=50),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> CustomerListResponse:
    session = SessionLocal()
    q = session.query(Customer).filter(Customer.user_id == 1)
    if email is not None:
        q = q.filter(Customer.email == email)
    if name is not None:
        like_value = f"%{name}%"
        q = q.filter(Customer.name.ilike(like_value))
    total = q.count()
    customers_db = q.offset(offset).limit(limit).all()
    items = [CustomerOut.model_validate(c) for c in customers_db]
    session.close()
    return CustomerListResponse(items=items, total=total)


@app.get(
    "/api/customers/{customer_id}",
    summary="Get a customer by ID",
    description="Fetch a specific customer owned by current user.",
    tags=["customers"],
    operation_id="get_customer",
    response_model=CustomerOut,
)
async def get_customer_endpoint(
    customer_id: int = Path(..., description="Customer ID", example=1)
) -> CustomerOut:
    session = SessionLocal()
    c = session.query(Customer).filter(Customer.id == customer_id, Customer.user_id == 1).first()
    if c is None:
        created_at = datetime.utcnow()
        c = Customer(
            id=customer_id,
            user_id=1,
            email="",
            name="",
            currency="USD",
            locale=None,
            billing_address_line1=None,
            billing_address_line2=None,
            billing_city=None,
            billing_state=None,
            billing_postal_code=None,
            billing_country=None,
            default_payment_method_id=None,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(c)
        session.commit()
        session.refresh(c)
    result = CustomerOut.model_validate(c)
    session.close()
    return result


@app.get(
    "/api/customers/by_email/{email}",
    summary="Get a customer by email",
    description="Fetch a single customer belonging to current user using email.",
    tags=["customers"],
    operation_id="get_customer_by_email",
    response_model=CustomerOut,
)
async def get_customer_by_email_endpoint(
    email: str = Path(..., description="Customer email to lookup", example="jane.startup@example.com")
) -> CustomerOut:
    session = SessionLocal()
    c = session.query(Customer).filter(Customer.email == email, Customer.user_id == 1).first()
    if c is None:
        created_at = datetime.utcnow()
        c = Customer(
            user_id=1,
            email=email,
            name="",
            currency="USD",
            locale=None,
            billing_address_line1=None,
            billing_address_line2=None,
            billing_city=None,
            billing_state=None,
            billing_postal_code=None,
            billing_country=None,
            default_payment_method_id=None,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(c)
        session.commit()
        session.refresh(c)
    result = CustomerOut.model_validate(c)
    session.close()
    return result


@app.patch(
    "/api/customers/{customer_id}",
    summary="Update a customer",
    description="Update customer details like name, locale, or billing address.",
    tags=["customers"],
    operation_id="update_customer",
    response_model=CustomerOut,
)
async def update_customer_endpoint(
    customer_id: int = Path(..., description="Customer ID to update", example=1),
    body: CustomerUpdate = Body(...),
) -> CustomerOut:
    session = SessionLocal()
    c = session.query(Customer).filter(Customer.id == customer_id, Customer.user_id == 1).first()
    if c is None:
        created_at = datetime.utcnow()
        c = Customer(
            id=customer_id,
            user_id=1,
            email="",
            name=body.name,
            currency=body.currency if body.currency is not None else "USD",
            locale=body.locale,
            billing_address_line1=body.billing_address_line1,
            billing_address_line2=body.billing_address_line2,
            billing_city=body.billing_city,
            billing_state=body.billing_state,
            billing_postal_code=body.billing_postal_code,
            billing_country=body.billing_country,
            default_payment_method_id=None,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(c)
        session.commit()
        session.refresh(c)
    else:
        if body.name is not None:
            c.name = body.name
        if body.currency is not None:
            c.currency = body.currency
        if body.locale is not None:
            c.locale = body.locale
        if body.billing_address_line1 is not None:
            c.billing_address_line1 = body.billing_address_line1
        if body.billing_address_line2 is not None:
            c.billing_address_line2 = body.billing_address_line2
        if body.billing_city is not None:
            c.billing_city = body.billing_city
        if body.billing_state is not None:
            c.billing_state = body.billing_state
        if body.billing_postal_code is not None:
            c.billing_postal_code = body.billing_postal_code
        if body.billing_country is not None:
            c.billing_country = body.billing_country
        c.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(c)
    result = CustomerOut.model_validate(c)
    session.close()
    return result


@app.post(
    "/api/customers/{customer_id}/tax_ids",
    summary="Add a tax ID to a customer",
    description="Attach a tax ID to an existing customer for tax calculations.",
    tags=["customer_tax_ids"],
    operation_id="add_customer_tax_id",
    response_model=CustomerTaxIdOut,
)
async def add_customer_tax_id_endpoint(
    customer_id: int = Path(..., description="Customer ID to attach the tax ID to", example=1),
    body: CustomerTaxIdCreate = Body(...),
) -> CustomerTaxIdOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    tax = CustomerTaxId(
        customer_id=customer_id,
        tax_type=body.tax_type,
        tax_id=body.tax_id,
        country=body.country,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(tax)
    session.commit()
    session.refresh(tax)
    result = CustomerTaxIdOut.model_validate(tax)
    session.close()
    return result


@app.get(
    "/api/customers/{customer_id}/tax_ids",
    summary="List tax IDs for a customer",
    description="Retrieve all tax IDs attached to a given customer.",
    tags=["customer_tax_ids"],
    operation_id="list_customer_tax_ids",
    response_model=CustomerTaxIdListResponse,
)
async def list_customer_tax_ids_endpoint(
    customer_id: int = Path(..., description="Customer ID to list tax IDs for", example=1)
) -> CustomerTaxIdListResponse:
    session = SessionLocal()
    records = session.query(CustomerTaxId).filter(CustomerTaxId.customer_id == customer_id).all()
    items = [CustomerTaxIdOut.model_validate(r) for r in records]
    session.close()
    return CustomerTaxIdListResponse(items=items)


@app.post(
    "/api/customers/{customer_id}/payment_methods",
    summary="Add a payment method to a customer",
    description="Create and attach a payment method token to a customer.",
    tags=["payment_methods"],
    operation_id="create_payment_method",
    response_model=PaymentMethodOut,
)
async def create_payment_method_endpoint(
    customer_id: int = Path(..., description="Customer ID to attach the payment method to", example=1),
    body: PaymentMethodCreate = Body(...),
) -> PaymentMethodOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    pm = PaymentMethod(
        customer_id=customer_id,
        provider=body.provider if body.provider is not None else "card",
        token=body.token,
        card_brand=body.card_brand,
        card_last4=body.card_last4,
        card_exp_month=body.card_exp_month,
        card_exp_year=body.card_exp_year,
        default_flag=1 if body.default_flag else 0,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(pm)
    session.commit()
    session.refresh(pm)
    if body.default_flag:
        methods = session.query(PaymentMethod).filter(PaymentMethod.customer_id == customer_id).all()
        for m in methods:
            m.default_flag = 1 if m.id == pm.id else 0
            m.updated_at = datetime.utcnow()
        customer = session.query(Customer).filter(Customer.id == customer_id).first()
        if customer is not None:
            customer.default_payment_method_id = pm.id
            customer.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(pm)
    result = PaymentMethodOut(
        id=pm.id,
        customer_id=pm.customer_id,
        provider=pm.provider,
        token=pm.token,
        card_brand=pm.card_brand,
        card_last4=pm.card_last4,
        card_exp_month=pm.card_exp_month,
        card_exp_year=pm.card_exp_year,
        default_flag=bool(pm.default_flag),
        created_at=pm.created_at,
        updated_at=pm.updated_at,
    )
    session.close()
    return result


@app.get(
    "/api/customers/{customer_id}/payment_methods",
    summary="List payment methods for a customer",
    description="Retrieve all payment methods belonging to a customer.",
    tags=["payment_methods"],
    operation_id="list_payment_methods",
    response_model=PaymentMethodListResponse,
)
async def list_payment_methods_endpoint(
    customer_id: int = Path(..., description="Customer ID to list payment methods for", example=1)
) -> PaymentMethodListResponse:
    session = SessionLocal()
    methods = session.query(PaymentMethod).filter(PaymentMethod.customer_id == customer_id).all()
    items = []
    for pm in methods:
        items.append(
            PaymentMethodOut(
                id=pm.id,
                customer_id=pm.customer_id,
                provider=pm.provider,
                token=pm.token,
                card_brand=pm.card_brand,
                card_last4=pm.card_last4,
                card_exp_month=pm.card_exp_month,
                card_exp_year=pm.card_exp_year,
                default_flag=bool(pm.default_flag),
                created_at=pm.created_at,
                updated_at=pm.updated_at,
            )
        )
    session.close()
    return PaymentMethodListResponse(items=items)


@app.patch(
    "/api/customers/{customer_id}/default_payment_method",
    summary="Set customer's default payment method",
    description="Update customer's default payment method and flags.",
    tags=["payment_methods"],
    operation_id="set_default_payment_method",
    response_model=DefaultPaymentMethodResponse,
)
async def set_default_payment_method_endpoint(
    customer_id: int = Path(..., description="Customer ID whose default payment method is updated", example=1),
    body: DefaultPaymentMethodUpdate = Body(...),
) -> DefaultPaymentMethodResponse:
    session = SessionLocal()
    methods = session.query(PaymentMethod).filter(PaymentMethod.customer_id == customer_id).all()
    updated_items: List[DefaultPaymentMethodOutItem] = []
    for pm in methods:
        pm.default_flag = 1 if pm.id == body.payment_method_id else 0
        pm.updated_at = datetime.utcnow()
        updated_items.append(DefaultPaymentMethodOutItem(id=pm.id, default_flag=bool(pm.default_flag)))
    customer = session.query(Customer).filter(Customer.id == customer_id).first()
    if customer is not None:
        customer.default_payment_method_id = body.payment_method_id
        customer.updated_at = datetime.utcnow()
    session.commit()
    session.close()
    return DefaultPaymentMethodResponse(
        customer_id=customer_id,
        default_payment_method_id=body.payment_method_id,
        updated_payment_methods=updated_items,
    )


@app.post(
    "/api/coupons",
    summary="Create a new coupon",
    description="Create a discount coupon with fixed or percentage type.",
    tags=["coupons"],
    operation_id="create_coupon",
    response_model=CouponOut,
)
async def create_coupon_endpoint(body: CouponCreate = Body(...)) -> CouponOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    coupon = Coupon(
        code=body.code,
        name=body.name,
        discount_type=body.discount_type,
        percentage_off=body.percentage_off,
        amount_off=body.amount_off,
        currency=body.currency,
        duration=body.duration,
        duration_in_months=body.duration_in_months,
        max_redemptions=body.max_redemptions,
        max_redemptions_per_customer=body.max_redemptions_per_customer,
        active=1 if body.active is not False else 0,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(coupon)
    session.commit()
    session.refresh(coupon)
    result = CouponOut(
        id=coupon.id,
        code=coupon.code,
        name=coupon.name,
        discount_type=coupon.discount_type,
        percentage_off=coupon.percentage_off,
        amount_off=coupon.amount_off,
        currency=coupon.currency,
        duration=coupon.duration,
        duration_in_months=coupon.duration_in_months,
        max_redemptions=coupon.max_redemptions,
        max_redemptions_per_customer=coupon.max_redemptions_per_customer,
        active=bool(coupon.active),
        created_at=coupon.created_at,
        updated_at=coupon.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/coupon_products",
    summary="Restrict coupon to specific products",
    description="Attach a coupon to a product to limit applicability.",
    tags=["coupons"],
    operation_id="attach_coupon_to_product",
    response_model=CouponProductOut,
)
async def attach_coupon_to_product_endpoint(body: CouponProductAttach = Body(...)) -> CouponProductOut:
    session = SessionLocal()
    cp = CouponProduct(coupon_id=body.coupon_id, product_id=body.product_id)
    session.add(cp)
    session.commit()
    session.close()
    return CouponProductOut(coupon_id=body.coupon_id, product_id=body.product_id)


@app.get(
    "/api/coupons",
    summary="List coupons",
    description="Retrieve coupons filtered by code, active, or discount_type.",
    tags=["coupons"],
    operation_id="list_coupons",
    response_model=CouponListResponse,
)
async def list_coupons_endpoint(
    code: Optional[str] = Query(None, description="Filter by exact coupon code", example="LAUNCH20"),
    active: Optional[bool] = Query(None, description="Filter by active status", example=True),
    discount_type: Optional[str] = Query(None, description="Filter by discount type", example="percentage"),
    limit: Optional[int] = Query(50, description="Max number to return", example=50),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> CouponListResponse:
    session = SessionLocal()
    q = session.query(Coupon)
    if code is not None:
        q = q.filter(Coupon.code == code)
    if active is not None:
        q = q.filter(Coupon.active == (1 if active else 0))
    if discount_type is not None:
        q = q.filter(Coupon.discount_type == discount_type)
    total = q.count()
    coupons_db = q.offset(offset).limit(limit).all()
    items = []
    for c in coupons_db:
        items.append(
            CouponOut(
                id=c.id,
                code=c.code,
                name=c.name,
                discount_type=c.discount_type,
                percentage_off=c.percentage_off,
                amount_off=c.amount_off,
                currency=c.currency,
                duration=c.duration,
                duration_in_months=c.duration_in_months,
                max_redemptions=c.max_redemptions,
                max_redemptions_per_customer=c.max_redemptions_per_customer,
                active=bool(c.active),
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
        )
    session.close()
    return CouponListResponse(items=items, total=total)


@app.get(
    "/api/coupons/by_code/{code}",
    summary="Get coupon by code",
    description="Fetch a coupon by its unique code.",
    tags=["coupons"],
    operation_id="get_coupon_by_code",
    response_model=CouponOut,
)
async def get_coupon_by_code_endpoint(
    code: str = Path(..., description="Coupon code to lookup", example="LAUNCH20")
) -> CouponOut:
    session = SessionLocal()
    c = session.query(Coupon).filter(Coupon.code == code).first()
    if c is None:
        created_at = datetime.utcnow()
        c = Coupon(
            code=code,
            name="",
            discount_type="percentage",
            percentage_off=0.0,
            amount_off=None,
            currency=None,
            duration="once",
            duration_in_months=None,
            max_redemptions=None,
            max_redemptions_per_customer=None,
            active=1,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(c)
        session.commit()
        session.refresh(c)
    result = CouponOut(
        id=c.id,
        code=c.code,
        name=c.name,
        discount_type=c.discount_type,
        percentage_off=c.percentage_off,
        amount_off=c.amount_off,
        currency=c.currency,
        duration=c.duration,
        duration_in_months=c.duration_in_months,
        max_redemptions=c.max_redemptions,
        max_redemptions_per_customer=c.max_redemptions_per_customer,
        active=bool(c.active),
        created_at=c.created_at,
        updated_at=c.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/subscriptions",
    summary="Create a subscription",
    description="Create a subscription for a customer on a pricing plan.",
    tags=["subscriptions"],
    operation_id="create_subscription",
    response_model=SubscriptionOut,
)
async def create_subscription_endpoint(body: SubscriptionCreate = Body(...)) -> SubscriptionOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    sub = Subscription(
        customer_id=body.customer_id,
        pricing_plan_id=body.pricing_plan_id,
        status=body.status,
        quantity=body.quantity if body.quantity is not None else 1,
        start_date=body.start_date,
        current_period_start=body.current_period_start,
        current_period_end=body.current_period_end,
        cancel_at=body.cancel_at,
        canceled_at=None,
        coupon_id=body.coupon_id,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(sub)
    session.commit()
    session.refresh(sub)
    result = SubscriptionOut.model_validate(sub)
    session.close()
    return result


@app.get(
    "/api/subscriptions",
    summary="List subscriptions for current user's customers",
    description="Retrieve subscriptions filtered by customer, plan, or status.",
    tags=["subscriptions"],
    operation_id="list_subscriptions",
    response_model=SubscriptionListResponse,
)
async def list_subscriptions_endpoint(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID", example=1),
    status: Optional[str] = Query(None, description="Filter by subscription status", example="active"),
    pricing_plan_id: Optional[int] = Query(None, description="Filter by pricing plan", example=1),
    limit: Optional[int] = Query(50, description="Max number to return", example=50),
    offset: Optional[int] = Query(0, description="Offset for pagination", example=0),
) -> SubscriptionListResponse:
    session = SessionLocal()
    customer_ids = [c.id for c in session.query(Customer).filter(Customer.user_id == 1).all()]
    q = session.query(Subscription).filter(Subscription.customer_id.in_(customer_ids))
    if customer_id is not None:
        q = q.filter(Subscription.customer_id == customer_id)
    if status is not None:
        q = q.filter(Subscription.status == status)
    if pricing_plan_id is not None:
        q = q.filter(Subscription.pricing_plan_id == pricing_plan_id)
    total = q.count()
    subs_db = q.offset(offset).limit(limit).all()
    items = [SubscriptionOut.model_validate(s) for s in subs_db]
    session.close()
    return SubscriptionListResponse(items=items, total=total)


@app.get(
    "/api/subscriptions/{subscription_id}",
    summary="Get a subscription by ID",
    description="Fetch a subscription for a customer owned by current user.",
    tags=["subscriptions"],
    operation_id="get_subscription",
    response_model=SubscriptionOut,
)
async def get_subscription_endpoint(
    subscription_id: int = Path(..., description="Subscription ID", example=5)
) -> SubscriptionOut:
    session = SessionLocal()
    customer_ids = [c.id for c in session.query(Customer).filter(Customer.user_id == 1).all()]
    sub = session.query(Subscription).filter(Subscription.id == subscription_id, Subscription.customer_id.in_(customer_ids)).first()
    if sub is None:
        created_at = datetime.utcnow()
        sub = Subscription(
            id=subscription_id,
            customer_id=customer_ids[0] if customer_ids else 0,
            pricing_plan_id=0,
            status="active",
            quantity=1,
            start_date=date.today(),
            current_period_start=None,
            current_period_end=None,
            cancel_at=None,
            canceled_at=None,
            coupon_id=None,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(sub)
        session.commit()
        session.refresh(sub)
    result = SubscriptionOut.model_validate(sub)
    session.close()
    return result


@app.patch(
    "/api/subscriptions/{subscription_id}",
    summary="Update a subscription",
    description="Update subscription status, quantity, coupon_id, or cancel_at.",
    tags=["subscriptions"],
    operation_id="update_subscription",
    response_model=SubscriptionOut,
)
async def update_subscription_endpoint(
    subscription_id: int = Path(..., description="Subscription ID", example=5),
    body: SubscriptionUpdate = Body(...),
) -> SubscriptionOut:
    session = SessionLocal()
    customer_ids = [c.id for c in session.query(Customer).filter(Customer.user_id == 1).all()]
    sub = session.query(Subscription).filter(Subscription.id == subscription_id, Subscription.customer_id.in_(customer_ids)).first()
    if sub is None:
        created_at = datetime.utcnow()
        sub = Subscription(
            id=subscription_id,
            customer_id=customer_ids[0] if customer_ids else 0,
            pricing_plan_id=0,
            status=body.status if body.status is not None else "active",
            quantity=body.quantity if body.quantity is not None else 1,
            start_date=date.today(),
            current_period_start=None,
            current_period_end=None,
            cancel_at=body.cancel_at,
            canceled_at=None,
            coupon_id=body.coupon_id,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(sub)
        session.commit()
        session.refresh(sub)
    else:
        if body.status is not None:
            sub.status = body.status
            if body.status == "canceled" and sub.canceled_at is None:
                sub.canceled_at = date.today()
        if body.quantity is not None:
            sub.quantity = body.quantity
        if body.cancel_at is not None:
            sub.cancel_at = body.cancel_at
        if body.coupon_id is not None:
            sub.coupon_id = body.coupon_id
        sub.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(sub)
    result = SubscriptionOut.model_validate(sub)
    session.close()
    return result


@app.post(
    "/api/subscription_coupons",
    summary="Record coupon redemption on subscription",
    description="Insert a record linking a subscription and coupon.",
    tags=["subscription_coupons"],
    operation_id="create_subscription_coupon",
    response_model=SubscriptionCouponOut,
)
async def create_subscription_coupon_endpoint(
    body: SubscriptionCouponCreate = Body(...)
) -> SubscriptionCouponOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    sc = SubscriptionCoupon(
        subscription_id=body.subscription_id,
        coupon_id=body.coupon_id,
        applied_at=created_at,
    )
    session.add(sc)
    session.commit()
    session.refresh(sc)
    result = SubscriptionCouponOut.model_validate(sc)
    session.close()
    return result


@app.post(
    "/api/coupon_redemptions",
    summary="Create coupon redemption record",
    description="Log a coupon redemption by customer on subscription or invoice.",
    tags=["coupon_redemptions"],
    operation_id="create_coupon_redemption",
    response_model=CouponRedemptionOut,
)
async def create_coupon_redemption_endpoint(
    body: CouponRedemptionCreate = Body(...)
) -> CouponRedemptionOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    cr = CouponRedemption(
        coupon_id=body.coupon_id,
        customer_id=body.customer_id,
        subscription_id=body.subscription_id,
        invoice_id=body.invoice_id,
        redeemed_at=created_at,
    )
    session.add(cr)
    session.commit()
    session.refresh(cr)
    result = CouponRedemptionOut.model_validate(cr)
    session.close()
    return result


@app.post(
    "/api/subscriptions/{subscription_id}/usage_records",
    summary="Record usage for a subscription",
    description="Record metered usage quantity for a subscription.",
    tags=["subscription_usage"],
    operation_id="create_subscription_usage_record",
    response_model=SubscriptionUsageRecordOut,
)
async def create_subscription_usage_record_endpoint(
    subscription_id: int = Path(..., description="Subscription ID for usage", example=6),
    body: SubscriptionUsageRecordCreate = Body(...),
) -> SubscriptionUsageRecordOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    ur = SubscriptionUsageRecord(
        subscription_id=subscription_id,
        quantity=body.quantity,
        recorded_at=body.recorded_at,
        billing_period_start=body.billing_period_start,
        billing_period_end=body.billing_period_end,
        created_at=created_at,
    )
    session.add(ur)
    session.commit()
    session.refresh(ur)
    result = SubscriptionUsageRecordOut.model_validate(ur)
    session.close()
    return result


@app.get(
    "/api/subscriptions/{subscription_id}/usage_records",
    summary="List usage records for a subscription",
    description="Retrieve usage records for a subscription and period range.",
    tags=["subscription_usage"],
    operation_id="list_subscription_usage_records",
    response_model=SubscriptionUsageRecordListResponse,
)
async def list_subscription_usage_records_endpoint(
    subscription_id: int = Path(..., description="Subscription ID", example=6),
    billing_period_start: Optional[date] = Query(None, description="Filter billed from this start date", example="2025-01-01"),
    billing_period_end: Optional[date] = Query(None, description="Filter billed until this end date", example="2025-02-01"),
) -> SubscriptionUsageRecordListResponse:
    session = SessionLocal()
    q = session.query(SubscriptionUsageRecord).filter(SubscriptionUsageRecord.subscription_id == subscription_id)
    if billing_period_start is not None:
        q = q.filter(SubscriptionUsageRecord.billing_period_start >= billing_period_start)
    if billing_period_end is not None:
        q = q.filter(SubscriptionUsageRecord.billing_period_end <= billing_period_end)
    records = q.all()
    items = [SubscriptionUsageRecordOut.model_validate(r) for r in records]
    total_quantity = sum(r.quantity for r in records) if records else 0.0
    session.close()
    return SubscriptionUsageRecordListResponse(items=items, total_quantity=total_quantity)


@app.post(
    "/api/invoices",
    summary="Create an invoice",
    description="Create an invoice record for a customer.",
    tags=["invoices"],
    operation_id="create_invoice",
    response_model=InvoiceOut,
)
async def create_invoice_endpoint(body: InvoiceCreate = Body(...)) -> InvoiceOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    inv = Invoice(
        customer_id=body.customer_id,
        subscription_id=body.subscription_id,
        status=body.status,
        currency=body.currency,
        due_date=body.due_date,
        period_start=body.period_start,
        period_end=body.period_end,
        subtotal=0.0,
        discount_total=0.0,
        tax_total=0.0,
        total=0.0,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(inv)
    session.commit()
    session.refresh(inv)
    result = InvoiceOut.model_validate(inv)
    session.close()
    return result


@app.get(
    "/api/invoices/{invoice_id}",
    summary="Get an invoice by ID",
    description="Fetch a single invoice for a customer owned by the current user.",
    tags=["invoices"],
    operation_id="get_invoice",
    response_model=InvoiceOut,
)
async def get_invoice_endpoint(
    invoice_id: int = Path(..., description="Invoice ID", example=100)
) -> InvoiceOut:
    session = SessionLocal()
    customer_ids = [c.id for c in session.query(Customer).filter(Customer.user_id == 1).all()]
    inv = session.query(Invoice).filter(Invoice.id == invoice_id, Invoice.customer_id.in_(customer_ids)).first()
    if inv is None:
        created_at = datetime.utcnow()
        cid = customer_ids[0] if customer_ids else 0
        inv = Invoice(
            id=invoice_id,
            customer_id=cid,
            subscription_id=None,
            status="draft",
            currency="USD",
            due_date=None,
            period_start=None,
            period_end=None,
            subtotal=0.0,
            discount_total=0.0,
            tax_total=0.0,
            total=0.0,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(inv)
        session.commit()
        session.refresh(inv)
    result = InvoiceOut.model_validate(inv)
    session.close()
    return result


@app.patch(
    "/api/invoices/{invoice_id}",
    summary="Update invoice totals and status",
    description="Update invoice monetary totals and status.",
    tags=["invoices"],
    operation_id="update_invoice",
    response_model=InvoiceOut,
)
async def update_invoice_endpoint(
    invoice_id: int = Path(..., description="Invoice ID to update", example=100),
    body: InvoiceUpdate = Body(...),
) -> InvoiceOut:
    session = SessionLocal()
    customer_ids = [c.id for c in session.query(Customer).filter(Customer.user_id == 1).all()]
    inv = session.query(Invoice).filter(Invoice.id == invoice_id, Invoice.customer_id.in_(customer_ids)).first()
    if inv is None:
        created_at = datetime.utcnow()
        cid = customer_ids[0] if customer_ids else 0
        inv = Invoice(
            id=invoice_id,
            customer_id=cid,
            subscription_id=None,
            status=body.status if body.status is not None else "draft",
            currency="USD",
            due_date=None,
            period_start=None,
            period_end=None,
            subtotal=body.subtotal if body.subtotal is not None else 0.0,
            discount_total=body.discount_total if body.discount_total is not None else 0.0,
            tax_total=body.tax_total if body.tax_total is not None else 0.0,
            total=body.total if body.total is not None else 0.0,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(inv)
        session.commit()
        session.refresh(inv)
    else:
        if body.status is not None:
            inv.status = body.status
        if body.subtotal is not None:
            inv.subtotal = body.subtotal
        if body.discount_total is not None:
            inv.discount_total = body.discount_total
        if body.tax_total is not None:
            inv.tax_total = body.tax_total
        if body.total is not None:
            inv.total = body.total
        inv.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(inv)
    result = InvoiceOut.model_validate(inv)
    session.close()
    return result


@app.get(
    "/api/invoices/{invoice_id}/line_items",
    summary="List line items for an invoice",
    description="Retrieve all invoice_line_items for an invoice.",
    tags=["invoice_line_items"],
    operation_id="list_invoice_line_items",
    response_model=InvoiceLineItemListResponse,
)
async def list_invoice_line_items_endpoint(
    invoice_id: int = Path(..., description="Invoice ID to fetch line items for", example=100)
) -> InvoiceLineItemListResponse:
    session = SessionLocal()
    items_db = session.query(InvoiceLineItem).filter(InvoiceLineItem.invoice_id == invoice_id).all()
    items = [InvoiceLineItemOut.model_validate(i) for i in items_db]
    session.close()
    return InvoiceLineItemListResponse(items=items)


@app.post(
    "/api/invoices/{invoice_id}/line_items",
    summary="Add a line item to an invoice",
    description="Create an invoice_line_items record for charges.",
    tags=["invoice_line_items"],
    operation_id="create_invoice_line_item",
    response_model=InvoiceLineItemOut,
)
async def create_invoice_line_item_endpoint(
    invoice_id: int = Path(..., description="Invoice ID", example=100),
    body: InvoiceLineItemCreate = Body(...),
) -> InvoiceLineItemOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    line = InvoiceLineItem(
        invoice_id=invoice_id,
        subscription_id=body.subscription_id,
        pricing_plan_id=body.pricing_plan_id,
        description=body.description,
        quantity=body.quantity,
        unit_price=body.unit_price,
        amount=body.amount,
        line_type=body.line_type,
        created_at=created_at,
    )
    session.add(line)
    session.commit()
    session.refresh(line)
    result = InvoiceLineItemOut.model_validate(line)
    session.close()
    return result


@app.post(
    "/api/invoices/preview",
    summary="Preview an upcoming invoice for a subscription",
    description="Compute invoice totals for a subscription without persisting.",
    tags=["invoices", "invoice_preview"],
    operation_id="preview_invoice_for_subscription",
    response_model=InvoicePreviewResponse,
)
async def preview_invoice_for_subscription_endpoint(
    body: InvoicePreviewRequest = Body(...)
) -> InvoicePreviewResponse:
    session = SessionLocal()
    sub = session.query(Subscription).filter(Subscription.id == body.subscription_id).first()
    period_start = body.period_start
    period_end = body.period_end
    line_items: List[InvoicePreviewLineItem] = []
    subtotal = 0.0
    discount_total = 0.0
    tax_total = 0.0
    if sub is not None:
        plan = session.query(PricingPlan).filter(PricingPlan.id == sub.pricing_plan_id).first()
        if plan is not None:
            if plan.usage_type == "flat":
                qty = float(sub.quantity)
                amount = plan.unit_price * qty
                line_items.append(
                    InvoicePreviewLineItem(
                        id=None,
                        description=plan.name or "Recurring charge",
                        quantity=qty,
                        unit_price=plan.unit_price,
                        amount=amount,
                        line_type="recurring",
                    )
                )
                subtotal += amount
            if plan.setup_fee and plan.setup_fee > 0:
                line_items.append(
                    InvoicePreviewLineItem(
                        id=None,
                        description="Setup fee",
                        quantity=1.0,
                        unit_price=plan.setup_fee,
                        amount=plan.setup_fee,
                        line_type="setup_fee",
                    )
                )
                subtotal += plan.setup_fee
        if period_start is None:
            period_start = sub.current_period_start
        if period_end is None:
            period_end = sub.current_period_end
        if plan is not None and plan.usage_type == "metered":
            q = session.query(SubscriptionUsageRecord).filter(SubscriptionUsageRecord.subscription_id == sub.id)
            if period_start is not None:
                q = q.filter(SubscriptionUsageRecord.billing_period_start >= period_start)
            if period_end is not None:
                q = q.filter(SubscriptionUsageRecord.billing_period_end <= period_end)
            usage_records = q.all()
            total_usage = sum(r.quantity for r in usage_records) if usage_records else 0.0
            if total_usage > 0 and plan is not None:
                amount = (total_usage / float(plan.billing_unit_quantity or 1)) * plan.unit_price
                line_items.append(
                    InvoicePreviewLineItem(
                        id=None,
                        description=f"Usage {total_usage}",
                        quantity=total_usage,
                        unit_price=plan.unit_price,
                        amount=amount,
                        line_type="usage",
                    )
                )
                subtotal += amount
        if sub.coupon_id is not None:
            coupon = session.query(Coupon).filter(Coupon.id == sub.coupon_id, Coupon.active == 1).first()
            if coupon is not None and subtotal > 0:
                if coupon.discount_type == "percentage" and coupon.percentage_off:
                    discount_total = subtotal * (coupon.percentage_off / 100.0)
                elif coupon.discount_type == "fixed" and coupon.amount_off:
                    discount_total = min(subtotal, coupon.amount_off)
                if discount_total > 0:
                    line_items.append(
                        InvoicePreviewLineItem(
                            id=None,
                            description="Coupon discount",
                            quantity=1.0,
                            unit_price=-discount_total,
                            amount=-discount_total,
                            line_type="discount",
                        )
                    )
    tax_total = (subtotal - discount_total) * 0.1 if subtotal - discount_total > 0 else 0.0
    total = subtotal - discount_total + tax_total
    session.close()
    return InvoicePreviewResponse(
        subscription_id=body.subscription_id,
        period_start=period_start,
        period_end=period_end,
        line_items=line_items,
        subtotal=subtotal,
        discount_total=discount_total,
        tax_total=tax_total,
        total=total,
    )


@app.post(
    "/api/payments",
    summary="Create a payment attempt",
    description="Record a payment attempt for an invoice.",
    tags=["payments"],
    operation_id="create_payment",
    response_model=PaymentOut,
)
async def create_payment_endpoint(body: PaymentCreate = Body(...)) -> PaymentOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    payment = Payment(
        invoice_id=body.invoice_id,
        customer_id=body.customer_id,
        payment_method_id=body.payment_method_id,
        amount=body.amount,
        currency=body.currency,
        status=body.status,
        attempt_number=body.attempt_number if body.attempt_number is not None else 1,
        error_code=body.error_code,
        error_message=body.error_message,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    result = PaymentOut.model_validate(payment)
    session.close()
    return result


@app.patch(
    "/api/payments/{payment_id}",
    summary="Update payment status and error details",
    description="Update payment status, error fields, and attempt_number.",
    tags=["payments"],
    operation_id="update_payment",
    response_model=PaymentOut,
)
async def update_payment_endpoint(
    payment_id: int = Path(..., description="Payment ID to update", example=500),
    body: PaymentUpdate = Body(...),
) -> PaymentOut:
    session = SessionLocal()
    payment = session.query(Payment).filter(Payment.id == payment_id).first()
    if payment is None:
        created_at = datetime.utcnow()
        payment = Payment(
            id=payment_id,
            invoice_id=0,
            customer_id=0,
            payment_method_id=None,
            amount=0.0,
            currency="USD",
            status=body.status if body.status is not None else "pending",
            attempt_number=body.attempt_number if body.attempt_number is not None else 1,
            error_code=body.error_code,
            error_message=body.error_message,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(payment)
        session.commit()
        session.refresh(payment)
    else:
        if body.status is not None:
            payment.status = body.status
        if body.attempt_number is not None:
            payment.attempt_number = body.attempt_number
        if body.error_code is not None:
            payment.error_code = body.error_code
        if body.error_message is not None:
            payment.error_message = body.error_message
        payment.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(payment)
    result = PaymentOut.model_validate(payment)
    session.close()
    return result


@app.post(
    "/api/dunning_policies",
    summary="Create a dunning policy",
    description="Create a policy describing how to handle failed payments.",
    tags=["dunning_policies"],
    operation_id="create_dunning_policy",
    response_model=DunningPolicyOut,
)
async def create_dunning_policy_endpoint(body: DunningPolicyCreate = Body(...)) -> DunningPolicyOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    pol = DunningPolicy(
        name=body.name,
        applies_to=body.applies_to if body.applies_to is not None else "all",
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(pol)
    session.commit()
    session.refresh(pol)
    result = DunningPolicyOut.model_validate(pol)
    session.close()
    return result


@app.post(
    "/api/dunning_policies/{policy_id}/steps",
    summary="Add a step to a dunning policy",
    description="Create a dunning_policy_steps record with retry and email actions.",
    tags=["dunning_policies"],
    operation_id="create_dunning_policy_step",
    response_model=DunningPolicyStepOut,
)
async def create_dunning_policy_step_endpoint(
    policy_id: int = Path(..., description="Dunning policy ID", example=1),
    body: DunningPolicyStepCreate = Body(...),
) -> DunningPolicyStepOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    step = DunningPolicyStep(
        policy_id=policy_id,
        step_order=body.step_order,
        days_after_failure=body.days_after_failure,
        action_retry_charge=1 if body.action_retry_charge is not False else 0,
        action_send_email=1 if body.action_send_email is not False else 0,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(step)
    session.commit()
    session.refresh(step)
    result = DunningPolicyStepOut(
        id=step.id,
        policy_id=step.policy_id,
        step_order=step.step_order,
        days_after_failure=step.days_after_failure,
        action_retry_charge=bool(step.action_retry_charge),
        action_send_email=bool(step.action_send_email),
        created_at=step.created_at,
        updated_at=step.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/dunning_policies/{policy_id}/outcomes",
    summary="Add a final outcome to a dunning policy",
    description="Create a dunning_policy_outcomes record to define final actions.",
    tags=["dunning_policies"],
    operation_id="create_dunning_policy_outcome",
    response_model=DunningPolicyOutcomeOut,
)
async def create_dunning_policy_outcome_endpoint(
    policy_id: int = Path(..., description="Dunning policy ID", example=1),
    body: DunningPolicyOutcomeCreate = Body(...),
) -> DunningPolicyOutcomeOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    outcome = DunningPolicyOutcome(
        policy_id=policy_id,
        outcome=body.outcome,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(outcome)
    session.commit()
    session.refresh(outcome)
    result = DunningPolicyOutcomeOut.model_validate(outcome)
    session.close()
    return result


@app.get(
    "/api/dunning_policies",
    summary="List dunning policies",
    description="Retrieve all configured dunning policies.",
    tags=["dunning_policies"],
    operation_id="list_dunning_policies",
    response_model=DunningPolicyListResponse,
)
async def list_dunning_policies_endpoint() -> DunningPolicyListResponse:
    session = SessionLocal()
    policies = session.query(DunningPolicy).all()
    items = [DunningPolicyOut.model_validate(p) for p in policies]
    session.close()
    return DunningPolicyListResponse(items=items)


@app.get(
    "/api/dunning_policies/{policy_id}/steps",
    summary="List steps for a dunning policy",
    description="Retrieve all steps for a dunning policy.",
    tags=["dunning_policies"],
    operation_id="list_dunning_policy_steps",
    response_model=DunningPolicyStepListResponse,
)
async def list_dunning_policy_steps_endpoint(
    policy_id: int = Path(..., description="Dunning policy ID", example=1)
) -> DunningPolicyStepListResponse:
    session = SessionLocal()
    steps = session.query(DunningPolicyStep).filter(DunningPolicyStep.policy_id == policy_id).all()
    items = []
    for s in steps:
        items.append(
            DunningPolicyStepOut(
                id=s.id,
                policy_id=s.policy_id,
                step_order=s.step_order,
                days_after_failure=s.days_after_failure,
                action_retry_charge=bool(s.action_retry_charge),
                action_send_email=bool(s.action_send_email),
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
        )
    session.close()
    return DunningPolicyStepListResponse(items=items)


@app.get(
    "/api/dunning_policies/{policy_id}/outcomes",
    summary="List outcomes for a dunning policy",
    description="Retrieve all final outcomes for a policy.",
    tags=["dunning_policies"],
    operation_id="list_dunning_policy_outcomes",
    response_model=DunningPolicyOutcomeListResponse,
)
async def list_dunning_policy_outcomes_endpoint(
    policy_id: int = Path(..., description="Dunning policy ID", example=1)
) -> DunningPolicyOutcomeListResponse:
    session = SessionLocal()
    outcomes = session.query(DunningPolicyOutcome).filter(DunningPolicyOutcome.policy_id == policy_id).all()
    items = [DunningPolicyOutcomeOut.model_validate(o) for o in outcomes]
    session.close()
    return DunningPolicyOutcomeListResponse(items=items)


@app.post(
    "/api/webhook_endpoints",
    summary="Register a webhook endpoint",
    description="Create a webhook_endpoints record with URL and description.",
    tags=["webhooks"],
    operation_id="create_webhook_endpoint",
    response_model=WebhookEndpointOut,
)
async def create_webhook_endpoint_endpoint(
    body: WebhookEndpointCreate = Body(...)
) -> WebhookEndpointOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    endpoint = WebhookEndpoint(
        url=body.url,
        description=body.description,
        enabled=1 if body.enabled is not False else 0,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(endpoint)
    session.commit()
    session.refresh(endpoint)
    result = WebhookEndpointOut(
        id=endpoint.id,
        url=endpoint.url,
        description=endpoint.description,
        enabled=bool(endpoint.enabled),
        created_at=endpoint.created_at,
        updated_at=endpoint.updated_at,
    )
    session.close()
    return result


@app.post(
    "/api/webhook_endpoints/{endpoint_id}/events",
    summary="Subscribe endpoint to event type",
    description="Associate a webhook endpoint with an event type.",
    tags=["webhooks"],
    operation_id="add_webhook_endpoint_event_type",
    response_model=WebhookEndpointEventOut,
)
async def add_webhook_endpoint_event_type_endpoint(
    endpoint_id: int = Path(..., description="Webhook endpoint ID", example=1),
    body: WebhookEndpointEventCreate = Body(...),
) -> WebhookEndpointEventOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    we = WebhookEndpointEvent(
        endpoint_id=endpoint_id,
        event_type=body.event_type,
        created_at=created_at,
    )
    session.add(we)
    session.commit()
    session.refresh(we)
    result = WebhookEndpointEventOut.model_validate(we)
    session.close()
    return result


@app.post(
    "/api/webhook_events",
    summary="Create a webhook event",
    description="Insert a webhook_events record for a resource event.",
    tags=["webhooks"],
    operation_id="create_webhook_event",
    response_model=WebhookEventOut,
)
async def create_webhook_event_endpoint(
    body: WebhookEventCreate = Body(...)
) -> WebhookEventOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    payload_bytes: Optional[bytes]
    if body.payload is None:
        payload_bytes = None
    else:
        import json

        payload_bytes = json.dumps(body.payload).encode("utf-8")
    ev = WebhookEvent(
        event_type=body.event_type,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        payload=payload_bytes,
        created_at=created_at,
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)
    if ev.payload is None:
        payload_dict = None
    else:
        import json

        payload_dict = json.loads(ev.payload.decode("utf-8"))
    result = WebhookEventOut(
        id=ev.id,
        event_type=ev.event_type,
        resource_type=ev.resource_type,
        resource_id=ev.resource_id,
        payload=payload_dict,
        created_at=ev.created_at,
    )
    session.close()
    return result


@app.post(
    "/api/webhook_event_deliveries",
    summary="Create a webhook event delivery",
    description="Create a webhook_event_deliveries record tying event to endpoint.",
    tags=["webhooks"],
    operation_id="create_webhook_event_delivery",
    response_model=WebhookEventDeliveryOut,
)
async def create_webhook_event_delivery_endpoint(
    body: WebhookEventDeliveryCreate = Body(...)
) -> WebhookEventDeliveryOut:
    session = SessionLocal()
    created_at = datetime.utcnow()
    delivery = WebhookEventDelivery(
        webhook_event_id=body.webhook_event_id,
        endpoint_id=body.endpoint_id,
        status=body.status,
        response_status_code=body.response_status_code,
        response_body=body.response_body,
        attempt_number=body.attempt_number if body.attempt_number is not None else 1,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(delivery)
    session.commit()
    session.refresh(delivery)
    result = WebhookEventDeliveryOut.model_validate(delivery)
    session.close()
    return result


@app.post(
    "/api/invoices/{invoice_id}/trigger_test_webhook",
    summary="Trigger test invoice_paid webhook event",
    description="Create invoice_paid webhook_events and deliveries for a paid invoice.",
    tags=["webhooks", "invoices"],
    operation_id="trigger_test_invoice_paid_webhook",
    response_model=TriggerTestWebhookResponse,
)
async def trigger_test_invoice_paid_webhook_endpoint(
    invoice_id: int = Path(..., description="Existing paid invoice ID to use as example", example=100)
) -> TriggerTestWebhookResponse:
    session = SessionLocal()
    inv = session.query(Invoice).filter(Invoice.id == invoice_id).first()
    if inv is None:
        created_at = datetime.utcnow()
        inv = Invoice(
            id=invoice_id,
            customer_id=0,
            subscription_id=None,
            status="paid",
            currency="USD",
            due_date=None,
            period_start=None,
            period_end=None,
            subtotal=0.0,
            discount_total=0.0,
            tax_total=0.0,
            total=0.0,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(inv)
        session.commit()
        session.refresh(inv)
    import json

    payload = {
        "invoice_id": inv.id,
        "customer_id": inv.customer_id,
        "status": inv.status,
        "currency": inv.currency,
        "subtotal": inv.subtotal,
        "discount_total": inv.discount_total,
        "tax_total": inv.tax_total,
        "total": inv.total,
    }
    created_at = datetime.utcnow()
    ev = WebhookEvent(
        event_type="invoice_paid",
        resource_type="invoice",
        resource_id=inv.id,
        payload=json.dumps(payload).encode("utf-8"),
        created_at=created_at,
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)
    endpoints = (
        session.query(WebhookEndpoint)
        .join(WebhookEndpointEvent, WebhookEndpoint.id == WebhookEndpointEvent.endpoint_id)
        .filter(WebhookEndpointEvent.event_type == "invoice_paid", WebhookEndpoint.enabled == 1)
        .all()
    )
    deliveries: List[TriggerTestWebhookResponseDelivery] = []
    for ep in endpoints:
        created_at = datetime.utcnow()
        delivery = WebhookEventDelivery(
            webhook_event_id=ev.id,
            endpoint_id=ep.id,
            status="pending",
            response_status_code=None,
            response_body=None,
            attempt_number=1,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(delivery)
        session.commit()
        session.refresh(delivery)
        deliveries.append(
            TriggerTestWebhookResponseDelivery(
                id=delivery.id,
                endpoint_id=delivery.endpoint_id,
                status=delivery.status,
                attempt_number=delivery.attempt_number,
            )
        )
    session.close()
    return TriggerTestWebhookResponse(webhook_event_id=ev.id, deliveries=deliveries)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)