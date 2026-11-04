from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import os
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, ForeignKey, UniqueConstraint, Index, Float
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

database_url = os.getenv("DATABASE_PATH", "sqlite:///outputs/databases/partsrack_wholesale_inventory.db")
engine = create_engine("sqlite:////mnt/genming/case-rerun-20261103/cases/b2b_commerce_1_1/unsteered/student/final.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

class Warehouse(Base):
    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    code = Column(String)
    address_line1 = Column(String)
    address_line2 = Column(String)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    country = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

class Part(Base):
    __tablename__ = "parts"
    id = Column(Integer, primary_key=True)
    sku = Column(String, nullable=False, unique=True)
    manufacturer = Column(String)
    part_number = Column(String)
    description = Column(String)
    category = Column(String, nullable=False)
    default_cost_price = Column(Float, nullable=False)
    default_list_price = Column(Float, nullable=False)
    default_core_charge = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

class PartCompatibility(Base):
    __tablename__ = "part_compatibility"
    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year_start = Column(Integer, nullable=False)
    year_end = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class WarehouseBin(Base):
    __tablename__ = "warehouse_bins"
    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    bin_code = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    __table_args__ = (UniqueConstraint("warehouse_id", "bin_code", name="uix_warehouse_bin_code"),)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    bin_id = Column(Integer, ForeignKey("warehouse_bins.id"), nullable=False)
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    __table_args__ = (UniqueConstraint("part_id", "warehouse_id", "bin_id", name="uix_inventory_part_wh_bin"),)

class InventoryLot(Base):
    __tablename__ = "inventory_lots"
    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    bin_id = Column(Integer, ForeignKey("warehouse_bins.id"), nullable=False)
    lot_number = Column(String)
    received_date = Column(Date, nullable=False)
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    from_bin_id = Column(Integer, ForeignKey("warehouse_bins.id"))
    to_bin_id = Column(Integer, ForeignKey("warehouse_bins.id"))
    quantity = Column(Integer, nullable=False)
    movement_type = Column(String, nullable=False)
    reference_type = Column(String)
    reference_id = Column(Integer)
    movement_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    contact_name = Column(String)
    email = Column(String)
    phone = Column(String)
    address_line1 = Column(String)
    address_line2 = Column(String)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    country = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

class CustomerAccount(Base):
    __tablename__ = "customer_accounts"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    price_tier = Column(String, nullable=False)
    customer_group = Column(String)
    email = Column(String)
    phone = Column(String)
    billing_address_line1 = Column(String)
    billing_address_line2 = Column(String)
    billing_city = Column(String)
    billing_state = Column(String)
    billing_postal_code = Column(String)
    billing_country = Column(String)
    shipping_address_line1 = Column(String)
    shipping_address_line2 = Column(String)
    shipping_city = Column(String)
    shipping_state = Column(String)
    shipping_postal_code = Column(String)
    shipping_country = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

class PriceTierRule(Base):
    __tablename__ = "price_tier_rules"
    id = Column(Integer, primary_key=True)
    price_tier = Column(String)
    customer_group = Column(String)
    category = Column(String)
    min_quantity = Column(Integer, default=1)
    discount_percent = Column(Float, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True)
    order_number = Column(String, nullable=False, unique=True)
    customer_account_id = Column(Integer, ForeignKey("customer_accounts.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    status = Column(String, nullable=False)
    requested_ship_date = Column(Date, nullable=False)
    order_date = Column(Date, nullable=False)
    ship_to_name = Column(String)
    ship_to_address_line1 = Column(String)
    ship_to_address_line2 = Column(String)
    ship_to_city = Column(String)
    ship_to_state = Column(String)
    ship_to_postal_code = Column(String)
    ship_to_country = Column(String)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

class SalesOrderLine(Base):
    __tablename__ = "sales_order_lines"
    id = Column(Integer, primary_key=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    sku = Column(String, nullable=False)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_allocated = Column(Integer, nullable=False, default=0)
    quantity_shipped = Column(Integer, nullable=False, default=0)
    backorder_status = Column(String, nullable=False)
    unit_list_price = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_percent = Column(Float, nullable=False, default=0.0)
    category = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    __table_args__ = (UniqueConstraint("sales_order_id", "line_number", name="uix_sales_order_line_number"),)

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True)
    po_number = Column(String, nullable=False, unique=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    status = Column(String, nullable=False)
    order_date = Column(Date, nullable=False)
    expected_receipt_date = Column(Date)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    id = Column(Integer, primary_key=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    sku = Column(String, nullable=False)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, nullable=False, default=0)
    unit_cost = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    __table_args__ = (UniqueConstraint("purchase_order_id", "line_number", name="uix_po_line_number"),)

class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True)
    shipment_number = Column(String, nullable=False, unique=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    carrier = Column(String, nullable=False)
    service_level = Column(String)
    tracking_number = Column(String)
    ship_date = Column(Date, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

class ShipmentLine(Base):
    __tablename__ = "shipment_lines"
    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    sales_order_line_id = Column(Integer, ForeignKey("sales_order_lines.id"), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    sku = Column(String, nullable=False)
    quantity_shipped = Column(Integer, nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    bin_id = Column(Integer, ForeignKey("warehouse_bins.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

class WarehouseServiceZone(Base):
    __tablename__ = "warehouse_service_zones"
    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    postal_code_prefix = Column(String, nullable=False)
    transit_days = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)

Base.metadata.create_all(engine)

app = FastAPI(title="PartsRack Wholesale Inventory API", version="1.0.0")

class PartCreateRequest(BaseModel):
    sku: str = Field(..., description="Unique stock-keeping unit for the part", example="BRK-TOY-001")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name", example="Bosch")
    part_number: Optional[str] = Field(None, description="Manufacturer part number", example="0986ABC123")
    description: Optional[str] = Field(None, description="Human-readable part description", example="Front brake pad set")
    category: str = Field(..., description="Part category for pricing and reporting", example="Brakes")
    default_cost_price: float = Field(..., description="Default cost price in USD", example=45.0)
    default_list_price: float = Field(..., description="Default list price in USD", example=89.99)
    default_core_charge: Optional[float] = Field(0.0, description="Default core charge in USD", example=10.0)

class PartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Generated part ID", example=101)
    sku: str = Field(..., description="Unique SKU", example="BRK-TOY-001")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name", example="Bosch")
    part_number: Optional[str] = Field(None, description="Manufacturer part number", example="0986ABC123")
    description: Optional[str] = Field(None, description="Part description", example="Front brake pad set")
    category: str = Field(..., description="Part category", example="Brakes")
    default_cost_price: float = Field(..., description="Default cost price", example=45.0)
    default_list_price: float = Field(..., description="Default list price", example=89.99)
    default_core_charge: float = Field(..., description="Default core charge", example=10.0)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-12-31T10:15:00Z")
    updated_at: Optional[datetime] = Field(None, description="Last updated timestamp", example="2025-12-31T11:00:00Z")

class PartUpdateRequest(BaseModel):
    manufacturer: Optional[str] = Field(None, description="New manufacturer name", example="Bosch")
    part_number: Optional[str] = Field(None, description="New part number", example="0986ABC123")
    description: Optional[str] = Field(None, description="New description", example="Updated front brake pad set")
    category: Optional[str] = Field(None, description="New category", example="Brakes")
    default_cost_price: Optional[float] = Field(None, description="New default cost", example=47.5)
    default_list_price: Optional[float] = Field(None, description="New default list price", example=92.0)
    default_core_charge: Optional[float] = Field(None, description="New default core charge", example=12.0)

class PartCompatibilityCreateRequest(BaseModel):
    make: str = Field(..., description="Vehicle make", example="Toyota")
    model: str = Field(..., description="Vehicle model", example="Corolla")
    year_start: int = Field(..., description="First compatible model year", example=2015)
    year_end: int = Field(..., description="Last compatible model year", example=2019)

class PartCompatibilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Compatibility row ID", example=501)
    part_id: int = Field(..., description="Part ID", example=101)
    make: str = Field(..., description="Vehicle make", example="Toyota")
    model: str = Field(..., description="Vehicle model", example="Corolla")
    year_start: int = Field(..., description="Start year", example=2015)
    year_end: int = Field(..., description="End year", example=2019)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", example="2025-12-31T10:20:00Z")

class PartCompatibilityBulkItem(BaseModel):
    make: str = Field(..., description="Vehicle make", example="Toyota")
    model: str = Field(..., description="Vehicle model", example="Corolla")
    year_start: int = Field(..., description="Start year", example=2015)
    year_end: int = Field(..., description="End year", example=2019)

class PartCompatibilityBulkRequest(BaseModel):
    items: List[PartCompatibilityBulkItem] = Field(..., description="List of compatibility definitions", example=[{"make": "Toyota", "model": "Corolla", "year_start": 2015, "year_end": 2019}])

class PartCompatibilityListResponse(BaseModel):
    compatibility: List[PartCompatibilityResponse] = Field(..., description="Compatibility records for the part", example=[])

class WarehouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Warehouse ID", example=1)
    name: str = Field(..., description="Warehouse name", example="Downtown Warehouse")
    code: Optional[str] = Field(None, description="Short warehouse code", example="DTW")
    city: Optional[str] = Field(None, description="City", example="San Francisco")
    state: Optional[str] = Field(None, description="State or region", example="CA")
    postal_code: Optional[str] = Field(None, description="Postal code", example="94107")
    country: Optional[str] = Field(None, description="Country", example="US")

class WarehouseListResponse(BaseModel):
    warehouses: List[WarehouseResponse] = Field(..., description="List of warehouses", example=[])

class WarehouseCreateRequest(BaseModel):
    name: str = Field(..., description="Unique warehouse name", example="Downtown Warehouse")
    code: Optional[str] = Field(None, description="Short code identifier", example="DTW")
    address_line1: Optional[str] = Field(None, description="Street address line 1", example="123 Market St")
    city: Optional[str] = Field(None, description="City", example="San Francisco")
    state: Optional[str] = Field(None, description="State", example="CA")
    postal_code: Optional[str] = Field(None, description="Postal code", example="94107")
    country: Optional[str] = Field(None, description="Country", example="US")
    latitude: Optional[float] = Field(None, description="Latitude coordinate", example=37.776)
    longitude: Optional[float] = Field(None, description="Longitude coordinate", example=-122.394)

class WarehouseBinCreateRequest(BaseModel):
    bin_code: str = Field(..., description="Unique bin code within warehouse", example="A-03-05")
    description: Optional[str] = Field(None, description="Bin description", example="Aisle A, Row 3, Shelf 5")

class WarehouseBinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Bin ID", example=10)
    warehouse_id: int = Field(..., description="Warehouse ID", example=1)
    bin_code: str = Field(..., description="Bin code", example="A-03-05")
    description: Optional[str] = Field(None, description="Bin description", example="Aisle A, Row 3, Shelf 5")

class WarehouseBinListResponse(BaseModel):
    bins: List[WarehouseBinResponse] = Field(..., description="Bins in the warehouse", example=[])

class InventoryCreateRequest(BaseModel):
    part_id: int = Field(..., description="Part ID for this inventory row", example=101)
    warehouse_id: int = Field(..., description="Warehouse where inventory is stored", example=1)
    bin_id: int = Field(..., description="Bin ID within the warehouse", example=10)
    quantity_on_hand: int = Field(..., description="Initial on-hand quantity", example=120)
    quantity_reserved: Optional[int] = Field(0, description="Initial reserved quantity", example=0)
    reorder_point: Optional[int] = Field(0, description="Reorder point threshold", example=30)

class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Inventory row ID", example=1001)
    part_id: int = Field(..., description="Part ID", example=101)
    warehouse_id: int = Field(..., description="Warehouse ID", example=1)
    bin_id: int = Field(..., description="Bin ID", example=10)
    quantity_on_hand: int = Field(..., description="On-hand quantity", example=120)
    quantity_reserved: int = Field(..., description="Reserved quantity", example=0)
    reorder_point: int = Field(..., description="Reorder point", example=30)

class InventoryUpdateRequest(BaseModel):
    quantity_on_hand: Optional[int] = Field(None, description="New on-hand quantity", example=115)
    quantity_reserved: Optional[int] = Field(None, description="New reserved quantity", example=5)
    reorder_point: Optional[int] = Field(None, description="New reorder point", example=25)

class InventorySearchResponse(BaseModel):
    inventory: List[InventoryResponse] = Field(..., description="Matching inventory rows", example=[])

class InventoryBySkuWarehouseItem(BaseModel):
    warehouse_id: int = Field(..., description="Warehouse ID", example=1)
    warehouse_name: str = Field(..., description="Warehouse name", example="Downtown Warehouse")
    total_on_hand: int = Field(..., description="Total on-hand in this warehouse", example=120)
    total_reserved: int = Field(..., description="Total reserved in this warehouse", example=0)

class InventoryBySkuResponse(BaseModel):
    sku: str = Field(..., description="Requested SKU", example="BRK-TOY-001")
    part_id: Optional[int] = Field(None, description="Part ID", example=101)
    warehouses: List[InventoryBySkuWarehouseItem] = Field(..., description="Per-warehouse inventory summary", example=[])

class InventoryMovementCreateRequest(BaseModel):
    part_id: int = Field(..., description="Part being moved", example=201)
    warehouse_id: int = Field(..., description="Warehouse where movement occurs", example=2)
    from_bin_id: Optional[int] = Field(None, description="Source bin ID (nullable for adjustments)", example=22)
    to_bin_id: Optional[int] = Field(None, description="Destination bin ID (nullable for adjustments)", example=23)
    quantity: int = Field(..., description="Quantity moved (positive integer)", example=25)
    movement_type: str = Field(..., description="Movement type e.g. TRANSFER, SHIPMENT, RECEIPT, ADJUSTMENT", example="TRANSFER")
    reference_type: Optional[str] = Field(None, description="Related document type e.g. SALES_ORDER, SHIPMENT", example="SALES_ORDER")
    reference_id: Optional[int] = Field(None, description="ID of related document", example=450)

class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Movement ID", example=9001)
    part_id: int = Field(..., description="Part ID", example=201)
    warehouse_id: int = Field(..., description="Warehouse ID", example=2)
    from_bin_id: Optional[int] = Field(None, description="Source bin ID", example=22)
    to_bin_id: Optional[int] = Field(None, description="Destination bin ID", example=23)
    quantity: int = Field(..., description="Quantity moved", example=25)
    movement_type: str = Field(..., description="Movement type", example="TRANSFER")
    reference_type: Optional[str] = Field(None, description="Reference type", example="SALES_ORDER")
    reference_id: Optional[int] = Field(None, description="Reference ID", example=450)
    movement_date: datetime = Field(..., description="Movement timestamp", example="2026-01-01T10:00:00Z")

class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Customer ID", example=5)
    name: str = Field(..., description="Customer name", example="Joe's Auto Repair")
    price_tier: str = Field(..., description="Price tier code", example="silver")
    customer_group: Optional[str] = Field(None, description="Customer group", example="independent_shop")
    email: Optional[str] = Field(None, description="Primary email", example="joe@example.com")
    phone: Optional[str] = Field(None, description="Phone number", example="+1-555-0100")

class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse] = Field(..., description="Matching customer accounts", example=[])

class PriceTierRuleCreateRequest(BaseModel):
    price_tier: Optional[str] = Field(None, description="Price tier code or null", example=None)
    customer_group: Optional[str] = Field(None, description="Customer group this rule applies to", example="gold")
    category: Optional[str] = Field(None, description="Part category this rule applies to", example="Batteries")
    min_quantity: Optional[int] = Field(1, description="Minimum quantity on line to apply discount", example=3)
    discount_percent: float = Field(..., description="Discount percentage e.g. 12 for 12%", example=12.0)
    start_date: Optional[str] = Field(None, description="Start date YYYY-MM-DD when rule becomes active", example="2026-01-01")
    end_date: Optional[str] = Field(None, description="End date YYYY-MM-DD when rule expires", example=None)
    is_active: Optional[int] = Field(1, description="1 for active, 0 for inactive", example=1)

class PriceTierRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Rule ID", example=300)
    price_tier: Optional[str] = Field(None, description="Price tier", example=None)
    customer_group: Optional[str] = Field(None, description="Customer group", example="gold")
    category: Optional[str] = Field(None, description="Category", example="Batteries")
    min_quantity: int = Field(..., description="Minimum quantity", example=3)
    discount_percent: float = Field(..., description="Discount percent", example=12.0)
    start_date: Optional[date] = Field(None, description="Start date", example="2026-01-01")
    end_date: Optional[date] = Field(None, description="End date or null", example=None)
    is_active: int = Field(..., description="Active flag", example=1)

class PriceTierRuleListResponse(BaseModel):
    rules: List[PriceTierRuleResponse] = Field(..., description="Matching pricing rules", example=[])

class ApplyPricingRequest(BaseModel):
    customer_account_id: int = Field(..., description="Customer placing the order", example=5)
    part_id: int = Field(..., description="Part being ordered", example=301)
    category: str = Field(..., description="Part category for this line", example="Batteries")
    quantity_ordered: int = Field(..., description="Ordered quantity", example=4)
    order_date: str = Field(..., description="Order date YYYY-MM-DD for rule validity", example="2026-01-01")

class ApplyPricingResponse(BaseModel):
    unit_list_price: float = Field(..., description="Base unit list price from parts", example=150.0)
    unit_price: float = Field(..., description="Calculated unit price after discount", example=132.0)
    discount_percent: float = Field(..., description="Total discount percent applied", example=12.0)
    applied_rule_ids: List[int] = Field(..., description="IDs of rules that affected pricing", example=[300])

class RecalculateOpenLinesRequest(BaseModel):
    customer_group: str = Field(..., description="Customer group to target", example="gold")
    category: str = Field(..., description="Part category filter", example="Batteries")
    min_quantity: int = Field(..., description="Minimum quantity on line to recalc", example=3)
    order_date: str = Field(..., description="Order date YYYY-MM-DD to filter sales orders", example="2026-01-01")

class RecalculatedLineItem(BaseModel):
    sales_order_line_id: int = Field(..., description="Line ID", example=8001)
    sales_order_id: int = Field(..., description="Order ID", example=700)
    old_unit_price: float = Field(..., description="Previous unit price", example=150.0)
    new_unit_price: float = Field(..., description="New unit price", example=132.0)
    old_discount_percent: float = Field(..., description="Previous discount percent", example=0.0)
    new_discount_percent: float = Field(..., description="New discount percent", example=12.0)

class RecalculateOpenLinesResponse(BaseModel):
    recalculated_lines: List[RecalculatedLineItem] = Field(..., description="Lines that were recalculated", example=[])

class SupplierListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Supplier ID", example=20)
    name: str = Field(..., description="Supplier name", example="ACME Brake Parts")
    email: Optional[str] = Field(None, description="Contact email", example="sales@acmebrakes.com")
    phone: Optional[str] = Field(None, description="Contact phone", example="+1-555-0200")

class SupplierListResponse(BaseModel):
    suppliers: List[SupplierListItem] = Field(..., description="Matching suppliers", example=[])

class PurchaseOrderCreateRequest(BaseModel):
    po_number: str = Field(..., description="Unique purchase order number", example="PO-2026-00010")
    supplier_id: int = Field(..., description="Supplier placing the PO with", example=20)
    warehouse_id: int = Field(..., description="Destination warehouse for the PO", example=4)
    status: str = Field(..., description="Initial PO status such as draft or sent", example="draft")
    order_date: str = Field(..., description="PO order date YYYY-MM-DD", example="2026-01-02")
    expected_receipt_date: Optional[str] = Field(None, description="Expected receipt date YYYY-MM-DD", example="2026-01-10")

class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Purchase order ID", example=600)
    po_number: str = Field(..., description="PO number", example="PO-2026-00010")
    supplier_id: int = Field(..., description="Supplier ID", example=20)
    warehouse_id: int = Field(..., description="Warehouse ID", example=4)
    status: str = Field(..., description="Current PO status", example="draft")
    order_date: date = Field(..., description="Order date", example="2026-01-02")
    expected_receipt_date: Optional[date] = Field(None, description="Expected receipt date", example="2026-01-10")

class PurchaseOrderUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="New status such as sent, received, closed", example="sent")
    expected_receipt_date: Optional[str] = Field(None, description="New expected receipt date", example="2026-01-12")

class PurchaseOrderUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="PO ID", example=600)
    po_number: str = Field(..., description="PO number", example="PO-2026-00010")
    status: str = Field(..., description="Updated status", example="sent")
    expected_receipt_date: Optional[date] = Field(None, description="Updated expected receipt date", example="2026-01-12")

class PurchaseOrderLineCreateRequest(BaseModel):
    line_number: int = Field(..., description="Line number within the PO", example=1)
    part_id: int = Field(..., description="Part being ordered", example=101)
    sku: str = Field(..., description="SKU of the part", example="BRK-TOY-001")
    quantity_ordered: int = Field(..., description="Quantity ordered from supplier", example=200)
    unit_cost: float = Field(..., description="Agreed unit cost", example=40.0)

class PurchaseOrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="PO line ID", example=610)
    purchase_order_id: int = Field(..., description="PO ID", example=600)
    line_number: int = Field(..., description="Line number", example=1)
    part_id: int = Field(..., description="Part ID", example=101)
    sku: str = Field(..., description="SKU", example="BRK-TOY-001")
    quantity_ordered: int = Field(..., description="Ordered quantity", example=200)
    quantity_received: int = Field(..., description="Received quantity", example=0)
    unit_cost: float = Field(..., description="Unit cost", example=40.0)

class SalesOrderCreateRequest(BaseModel):
    order_number: str = Field(..., description="Unique sales order number", example="SO-2026-00045")
    customer_account_id: int = Field(..., description="Customer placing the order", example=5)
    warehouse_id: int = Field(..., description="Shipping warehouse for the order", example=2)
    status: str = Field(..., description="Order status such as open, closed, cancelled", example="open")
    requested_ship_date: str = Field(..., description="Requested ship date YYYY-MM-DD", example="2026-01-05")
    order_date: str = Field(..., description="Order creation date YYYY-MM-DD", example="2026-01-02")
    ship_to_name: Optional[str] = Field(None, description="Ship-to contact name override", example="Joe's Auto Repair")
    ship_to_address_line1: Optional[str] = Field(None, description="Ship-to address line 1", example="456 Service Rd")
    ship_to_city: Optional[str] = Field(None, description="Ship-to city", example="San Francisco")
    ship_to_state: Optional[str] = Field(None, description="Ship-to state", example="CA")
    ship_to_postal_code: Optional[str] = Field(None, description="Ship-to postal code", example="94107")
    ship_to_country: Optional[str] = Field(None, description="Ship-to country", example="US")

class SalesOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Sales order ID", example=700)
    order_number: str = Field(..., description="Order number", example="SO-2026-00045")
    customer_account_id: int = Field(..., description="Customer ID", example=5)
    warehouse_id: int = Field(..., description="Warehouse ID", example=2)
    status: str = Field(..., description="Status", example="open")
    requested_ship_date: date = Field(..., description="Requested ship date", example="2026-01-05")
    order_date: date = Field(..., description="Order date", example="2026-01-02")

class SalesOrderLineCreateRequest(BaseModel):
    line_number: int = Field(..., description="Line number within the order", example=1)
    part_id: int = Field(..., description="Part being sold", example=101)
    sku: str = Field(..., description="SKU of the part", example="OIL-FLTR-001")
    quantity_ordered: int = Field(..., description="Quantity ordered", example=10)
    backorder_status: str = Field(..., description="Backorder status e.g. allow, no_backorder, shipped", example="allow")
    unit_list_price: float = Field(..., description="Base unit list price", example=9.99)
    unit_price: float = Field(..., description="Final unit price after discount", example=8.49)
    discount_percent: float = Field(..., description="Discount percent applied", example=15.0)
    category: str = Field(..., description="Part category at order time", example="Oil Filters")

class SalesOrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Order line ID", example=8001)
    sales_order_id: int = Field(..., description="Sales order ID", example=700)
    line_number: int = Field(..., description="Line number", example=1)
    part_id: int = Field(..., description="Part ID", example=101)
    sku: str = Field(..., description="SKU", example="OIL-FLTR-001")
    quantity_ordered: int = Field(..., description="Ordered quantity", example=10)
    quantity_allocated: int = Field(..., description="Allocated quantity", example=10)
    quantity_shipped: int = Field(..., description="Shipped quantity", example=0)
    backorder_status: str = Field(..., description="Backorder status", example="allow")
    unit_list_price: float = Field(..., description="List price", example=9.99)
    unit_price: float = Field(..., description="Net unit price", example=8.49)
    discount_percent: float = Field(..., description="Discount percent", example=15.0)
    category: str = Field(..., description="Category", example="Oil Filters")

class SalesOrderLineListResponse(BaseModel):
    lines: List[SalesOrderLineResponse] = Field(..., description="Lines belonging to the order", example=[])

class AllocateInventoryRequest(BaseModel):
    sales_order_line_id: int = Field(..., description="Line to allocate inventory to", example=8001)
    inventory_id: int = Field(..., description="Inventory row used for allocation", example=1001)
    quantity_to_allocate: int = Field(..., description="Quantity being allocated", example=10)

class AllocateInventoryResponse(BaseModel):
    sales_order_line_id: int = Field(..., description="Line ID", example=8001)
    new_quantity_allocated: int = Field(..., description="Updated allocated quantity on line", example=10)
    inventory_id: int = Field(..., description="Inventory ID used", example=1001)
    new_inventory_reserved: int = Field(..., description="Updated reserved quantity in inventory row", example=10)

class SalesOrderUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="New order status", example="closed")
    requested_ship_date: Optional[str] = Field(None, description="New requested ship date", example="2026-01-06")

class SalesOrderUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Sales order ID", example=700)
    order_number: str = Field(..., description="Order number", example="SO-2026-00045")
    status: str = Field(..., description="Updated status", example="closed")
    requested_ship_date: date = Field(..., description="Updated requested ship date", example="2026-01-06")

class SalesOrderLineUpdateRequest(BaseModel):
    quantity_shipped: Optional[int] = Field(None, description="New shipped quantity", example=10)
    backorder_status: Optional[str] = Field(None, description="New backorder status such as shipped or backordered", example="shipped")
    unit_price: Optional[float] = Field(None, description="Updated unit price when repricing", example=132.0)
    discount_percent: Optional[float] = Field(None, description="Updated discount percent", example=12.0)

class SalesOrderLineUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Line ID", example=8001)
    sales_order_id: int = Field(..., description="Order ID", example=700)
    quantity_shipped: int = Field(..., description="Updated shipped quantity", example=10)
    backorder_status: str = Field(..., description="Updated backorder status", example="shipped")
    unit_price: float = Field(..., description="Unit price", example=132.0)
    discount_percent: float = Field(..., description="Discount percent", example=12.0)

class WarehouseServiceZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Zone ID", example=10)
    warehouse_id: int = Field(..., description="Warehouse ID", example=2)
    postal_code_prefix: str = Field(..., description="Postal code prefix", example="941")
    transit_days: int = Field(..., description="Estimated transit days", example=2)

class WarehouseServiceZoneListResponse(BaseModel):
    zones: List[WarehouseServiceZoneResponse] = Field(..., description="Service zones", example=[])

class AvailabilityAlternativeItem(BaseModel):
    warehouse_id: int = Field(..., description="Warehouse ID", example=3)
    warehouse_name: str = Field(..., description="Warehouse name", example="West Coast DC")
    available_quantity: int = Field(..., description="Available quantity", example=8)
    estimated_delivery_date: str = Field(..., description="ETA date", example="2026-01-06")

class AvailabilityBestWarehouse(BaseModel):
    warehouse_id: int = Field(..., description="Warehouse ID", example=2)
    warehouse_name: str = Field(..., description="Warehouse name", example="Central DC")
    available_quantity: int = Field(..., description="Total available quantity (on_hand - reserved)", example=15)
    estimated_delivery_date: str = Field(..., description="Estimated delivery date YYYY-MM-DD", example="2026-01-05")

class AvailabilityResponse(BaseModel):
    sku: str = Field(..., description="Requested SKU", example="ALT-HON-2.4L")
    part_id: Optional[int] = Field(None, description="Part ID", example=350)
    best_warehouse: Optional[AvailabilityBestWarehouse] = Field(None, description="Selected warehouse offering soonest delivery")
    alternatives: List[AvailabilityAlternativeItem] = Field(..., description="Other warehouses with availability and ETA", example=[])

class ShipmentCreateRequest(BaseModel):
    shipment_number: str = Field(..., description="Unique shipment number", example="SH-2026-00090")
    sales_order_id: int = Field(..., description="Sales order being shipped", example=700)
    warehouse_id: int = Field(..., description="Warehouse shipping the order", example=2)
    carrier: str = Field(..., description="Carrier name", example="UPS Ground")
    service_level: Optional[str] = Field(None, description="Carrier service level", example="Ground")
    tracking_number: Optional[str] = Field(None, description="Tracking number string", example="1Z999AA10123456784")
    ship_date: str = Field(..., description="Shipment date YYYY-MM-DD", example="2026-01-02")

class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Shipment ID", example=900)
    shipment_number: str = Field(..., description="Shipment number", example="SH-2026-00090")
    sales_order_id: int = Field(..., description="Sales order ID", example=700)
    warehouse_id: int = Field(..., description="Warehouse ID", example=2)
    carrier: str = Field(..., description="Carrier", example="UPS Ground")
    tracking_number: Optional[str] = Field(None, description="Tracking number", example="1Z999AA10123456784")
    ship_date: date = Field(..., description="Ship date", example="2026-01-02")

class ShipmentLineCreateRequest(BaseModel):
    sales_order_line_id: int = Field(..., description="Sales order line being shipped", example=8001)
    part_id: int = Field(..., description="Part ID", example=101)
    sku: str = Field(..., description="SKU", example="OIL-FLTR-001")
    quantity_shipped: int = Field(..., description="Quantity shipped on this shipment line", example=10)
    warehouse_id: int = Field(..., description="Warehouse fulfilling this line", example=2)
    bin_id: Optional[int] = Field(None, description="Bin from which the item was picked", example=22)

class ShipmentLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Shipment line ID", example=910)
    shipment_id: int = Field(..., description="Shipment ID", example=900)
    sales_order_line_id: int = Field(..., description="Sales order line ID", example=8001)
    part_id: int = Field(..., description="Part ID", example=101)
    sku: str = Field(..., description="SKU", example="OIL-FLTR-001")
    quantity_shipped: int = Field(..., description="Quantity shipped", example=10)
    warehouse_id: int = Field(..., description="Warehouse ID", example=2)
    bin_id: Optional[int] = Field(None, description="Bin ID", example=22)

class ShipmentListResponse(BaseModel):
    shipments: List[ShipmentResponse] = Field(..., description="Shipments associated with the order", example=[])

class ShipmentLineListResponse(BaseModel):
    lines: List[ShipmentLineResponse] = Field(..., description="Lines in the shipment", example=[])

class PickListItem(BaseModel):
    bin_code: Optional[str] = Field(None, description="Pick bin code", example="B-01-02")
    warehouse_bin_id: Optional[int] = Field(None, description="Bin ID", example=22)
    order_number: str = Field(..., description="Sales order number", example="SO-2026-00040")
    sales_order_id: int = Field(..., description="Sales order ID", example=695)
    sales_order_line_id: int = Field(..., description="Sales order line ID", example=7990)
    customer_name: Optional[str] = Field(None, description="Customer name", example="Joe's Auto Repair")
    sku: str = Field(..., description="SKU to pick", example="OIL-FLTR-001")
    quantity_to_pick: int = Field(..., description="Quantity to pick from this bin", example=10)

class PickListResponse(BaseModel):
    warehouse_id: int = Field(..., description="Warehouse ID", example=2)
    ship_date: str = Field(..., description="Ship date", example="2026-01-03")
    items: List[PickListItem] = Field(..., description="Pick list items grouped by bin", example=[])

class StockAgingItem(BaseModel):
    part_id: int = Field(..., description="Part ID", example=420)
    sku: str = Field(..., description="SKU", example="SUS-TRK-001")
    description: Optional[str] = Field(None, description="Part description", example="Truck rear shock absorber")
    quantity_on_hand: int = Field(..., description="Total on-hand quantity at warehouse", example=120)
    average_age_in_days: float = Field(..., description="Weighted average age of on-hand stock", example=134.5)

class StockAgingResponse(BaseModel):
    warehouse_id: int = Field(..., description="Warehouse ID", example=5)
    category: str = Field(..., description="Category filter", example="Suspension")
    items: List[StockAgingItem] = Field(..., description="Aging stock items sorted by quantity_on_hand desc", example=[])

class FillRateTopPartItem(BaseModel):
    part_id: int = Field(..., description="Part ID", example=101)
    sku: str = Field(..., description="SKU", example="OIL-FLTR-001")
    total_quantity_shipped: int = Field(..., description="Total shipped quantity", example=750)

class FillRateReportResponse(BaseModel):
    start_date: str = Field(..., description="Start date of window", example="2026-01-01")
    end_date: str = Field(..., description="End date of window", example="2026-01-30")
    total_orders: int = Field(..., description="Number of sales orders in window", example=250)
    orders_filled_on_time: int = Field(..., description="Orders fully shipped on their requested_ship_date", example=210)
    fill_rate_percent: float = Field(..., description="Percentage of orders filled on time", example=84.0)
    top_moving_parts: List[FillRateTopPartItem] = Field(..., description="Top 10 parts by shipped quantity in window", example=[])

@app.post("/api/parts", response_model=PartResponse, summary="Create a new part with pricing", description="Create a parts row using SKU, manufacturer, part_number, category, and default prices.", tags=["parts"], operation_id="create_part")
async def create_part(body: PartCreateRequest = Body(...)) -> PartResponse:
    session = SessionLocal()
    part = Part(
        sku=body.sku,
        manufacturer=body.manufacturer,
        part_number=body.part_number,
        description=body.description,
        category=body.category,
        default_cost_price=body.default_cost_price,
        default_list_price=body.default_list_price,
        default_core_charge=body.default_core_charge if body.default_core_charge is not None else 0.0,
        created_at=datetime.utcnow()
    )
    session.add(part)
    session.commit()
    session.refresh(part)
    response = PartResponse.model_validate(part)
    session.close()
    return response

@app.get("/api/parts/{part_id}", response_model=PartResponse, summary="Get part details by ID", description="Retrieve a single part row by its ID including core attributes.", tags=["parts"], operation_id="get_part_by_id")
async def get_part_by_id(part_id: int = Path(..., description="Part ID to retrieve", example=101)) -> PartResponse:
    session = SessionLocal()
    part = session.query(Part).filter(Part.id == part_id).first()
    if part is None:
        part = Part(
            id=0,
            sku="",
            manufacturer=None,
            part_number=None,
            description=None,
            category="",
            default_cost_price=0.0,
            default_list_price=0.0,
            default_core_charge=0.0,
            created_at=None,
            updated_at=None
        )
    response = PartResponse.model_validate(part)
    session.close()
    return response

@app.get("/api/parts/by-sku/{sku}", response_model=PartResponse, summary="Get part details by SKU", description="Retrieve a single part row by its SKU for use when only SKU is known.", tags=["parts"], operation_id="get_part_by_sku")
async def get_part_by_sku(sku: str = Path(..., description="SKU to look up", example="BRK-TOY-001")) -> PartResponse:
    session = SessionLocal()
    part = session.query(Part).filter(Part.sku == sku).first()
    if part is None:
        part = Part(
            id=0,
            sku="",
            manufacturer=None,
            part_number=None,
            description=None,
            category="",
            default_cost_price=0.0,
            default_list_price=0.0,
            default_core_charge=0.0,
            created_at=None,
            updated_at=None
        )
    response = PartResponse.model_validate(part)
    session.close()
    return response

@app.patch("/api/parts/{part_id}", response_model=PartResponse, summary="Update part core fields", description="Partially update manufacturer, part_number, category, or prices for a part.", tags=["parts"], operation_id="update_part")
async def update_part(part_id: int = Path(..., description="ID of the part to update", example=101), body: PartUpdateRequest = Body(...)) -> PartResponse:
    session = SessionLocal()
    part = session.query(Part).filter(Part.id == part_id).first()
    if part is None:
        part = Part(
            id=part_id,
            sku="",
            manufacturer=None,
            part_number=None,
            description=None,
            category="",
            default_cost_price=0.0,
            default_list_price=0.0,
            default_core_charge=0.0,
            created_at=datetime.utcnow()
        )
        session.add(part)
        session.commit()
        session.refresh(part)
    if body.manufacturer is not None:
        part.manufacturer = body.manufacturer
    if body.part_number is not None:
        part.part_number = body.part_number
    if body.description is not None:
        part.description = body.description
    if body.category is not None:
        part.category = body.category
    if body.default_cost_price is not None:
        part.default_cost_price = body.default_cost_price
    if body.default_list_price is not None:
        part.default_list_price = body.default_list_price
    if body.default_core_charge is not None:
        part.default_core_charge = body.default_core_charge
    part.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(part)
    response = PartResponse.model_validate(part)
    session.close()
    return response

@app.post("/api/parts/{part_id}/compatibility", response_model=PartCompatibilityResponse, summary="Add a compatibility record for a part", description="Create a single part_compatibility row for a given part and vehicle range.", tags=["part_compatibility"], operation_id="add_part_compatibility")
async def add_part_compatibility(part_id: int = Path(..., description="Part ID owning the compatibility", example=101), body: PartCompatibilityCreateRequest = Body(...)) -> PartCompatibilityResponse:
    session = SessionLocal()
    compat = PartCompatibility(
        part_id=part_id,
        make=body.make,
        model=body.model,
        year_start=body.year_start,
        year_end=body.year_end,
        created_at=datetime.utcnow()
    )
    session.add(compat)
    session.commit()
    session.refresh(compat)
    response = PartCompatibilityResponse.model_validate(compat)
    session.close()
    return response

@app.post("/api/parts/{part_id}/compatibility/bulk", response_model=PartCompatibilityListResponse, summary="Bulk add compatibility rows for a part", description="Create multiple part_compatibility rows in one request for a given part.", tags=["part_compatibility"], operation_id="bulk_add_part_compatibility")
async def bulk_add_part_compatibility(part_id: int = Path(..., description="Part ID owning the compatibility rows", example=101), body: PartCompatibilityBulkRequest = Body(...)) -> PartCompatibilityListResponse:
    session = SessionLocal()
    created_items: List[PartCompatibility] = []
    for item in body.items:
        compat = PartCompatibility(
            part_id=part_id,
            make=item.make,
            model=item.model,
            year_start=item.year_start,
            year_end=item.year_end,
            created_at=datetime.utcnow()
        )
        session.add(compat)
        session.commit()
        session.refresh(compat)
        created_items.append(compat)
    response_items = [PartCompatibilityResponse.model_validate(c) for c in created_items]
    response = PartCompatibilityListResponse(compatibility=response_items)
    session.close()
    return response

@app.get("/api/parts/{part_id}/compatibility", response_model=PartCompatibilityListResponse, summary="List compatibility entries for a part", description="Retrieve all part_compatibility rows for a specific part ID.", tags=["part_compatibility"], operation_id="list_part_compatibility")
async def list_part_compatibility(part_id: int = Path(..., description="Part ID to list compatibilities", example=101)) -> PartCompatibilityListResponse:
    session = SessionLocal()
    compat = session.query(PartCompatibility).filter(PartCompatibility.part_id == part_id).all()
    response_items = [PartCompatibilityResponse.model_validate(c) for c in compat]
    response = PartCompatibilityListResponse(compatibility=response_items)
    session.close()
    return response

@app.get("/api/warehouses", response_model=WarehouseListResponse, summary="List warehouses with optional filters", description="Retrieve warehouses filtered by name or postal_code for routing and allocation.", tags=["warehouses"], operation_id="list_warehouses")
async def list_warehouses(name: Optional[str] = Query(None, description="Filter by warehouse name (partial match)", example="Downtown"), postal_code: Optional[str] = Query(None, description="Filter by postal_code", example="94107")) -> WarehouseListResponse:
    session = SessionLocal()
    query = session.query(Warehouse)
    if name is not None:
        query = query.filter(Warehouse.name.contains(name))
    if postal_code is not None:
        query = query.filter(Warehouse.postal_code == postal_code)
    warehouses = query.all()
    items = [WarehouseResponse.model_validate(w) for w in warehouses]
    response = WarehouseListResponse(warehouses=items)
    session.close()
    return response

@app.post("/api/warehouses", response_model=WarehouseResponse, summary="Create a new warehouse", description="Insert a new warehouses row for storing and shipping inventory.", tags=["warehouses"], operation_id="create_warehouse")
async def create_warehouse(body: WarehouseCreateRequest = Body(...)) -> WarehouseResponse:
    session = SessionLocal()
    wh = Warehouse(
        name=body.name,
        code=body.code,
        address_line1=body.address_line1,
        city=body.city,
        state=body.state,
        postal_code=body.postal_code,
        country=body.country,
        latitude=body.latitude,
        longitude=body.longitude,
        created_at=datetime.utcnow()
    )
    session.add(wh)
    session.commit()
    session.refresh(wh)
    response = WarehouseResponse.model_validate(wh)
    session.close()
    return response

@app.post("/api/warehouses/{warehouse_id}/bins", response_model=WarehouseBinResponse, summary="Create a bin in a warehouse", description="Insert a new warehouse_bins row for a specific warehouse.", tags=["warehouse_bins"], operation_id="create_warehouse_bin")
async def create_warehouse_bin(warehouse_id: int = Path(..., description="Owning warehouse ID", example=1), body: WarehouseBinCreateRequest = Body(...)) -> WarehouseBinResponse:
    session = SessionLocal()
    bin_obj = WarehouseBin(
        warehouse_id=warehouse_id,
        bin_code=body.bin_code,
        description=body.description,
        created_at=datetime.utcnow()
    )
    session.add(bin_obj)
    session.commit()
    session.refresh(bin_obj)
    response = WarehouseBinResponse.model_validate(bin_obj)
    session.close()
    return response

@app.get("/api/warehouses/{warehouse_id}/bins", response_model=WarehouseBinListResponse, summary="List bins in a warehouse", description="Retrieve all warehouse_bins for a given warehouse_id.", tags=["warehouse_bins"], operation_id="list_warehouse_bins")
async def list_warehouse_bins(warehouse_id: int = Path(..., description="Warehouse whose bins to list", example=1)) -> WarehouseBinListResponse:
    session = SessionLocal()
    bins = session.query(WarehouseBin).filter(WarehouseBin.warehouse_id == warehouse_id).all()
    items = [WarehouseBinResponse.model_validate(b) for b in bins]
    response = WarehouseBinListResponse(bins=items)
    session.close()
    return response

@app.get("/api/warehouses/{warehouse_id}/bins/by-code/{bin_code}", response_model=WarehouseBinResponse, summary="Get bin by warehouse and code", description="Find a single bin in a warehouse using its bin_code.", tags=["warehouse_bins"], operation_id="get_bin_by_code")
async def get_bin_by_code(warehouse_id: int = Path(..., description="Warehouse ID", example=2), bin_code: str = Path(..., description="Bin code to locate", example="B-01-02")) -> WarehouseBinResponse:
    session = SessionLocal()
    bin_obj = session.query(WarehouseBin).filter(WarehouseBin.warehouse_id == warehouse_id, WarehouseBin.bin_code == bin_code).first()
    if bin_obj is None:
        bin_obj = WarehouseBin(
            id=0,
            warehouse_id=warehouse_id,
            bin_code="",
            description=None,
            created_at=None,
            updated_at=None
        )
    response = WarehouseBinResponse.model_validate(bin_obj)
    session.close()
    return response

@app.post("/api/inventory", response_model=InventoryResponse, summary="Create or set an inventory record", description="Create an inventory row for a part, warehouse, and bin with explicit quantities.", tags=["inventory"], operation_id="create_inventory_record")
async def create_inventory_record(body: InventoryCreateRequest = Body(...)) -> InventoryResponse:
    session = SessionLocal()
    inv = session.query(Inventory).filter(Inventory.part_id == body.part_id, Inventory.warehouse_id == body.warehouse_id, Inventory.bin_id == body.bin_id).first()
    if inv is None:
        inv = Inventory(
            part_id=body.part_id,
            warehouse_id=body.warehouse_id,
            bin_id=body.bin_id,
            quantity_on_hand=body.quantity_on_hand,
            quantity_reserved=body.quantity_reserved if body.quantity_reserved is not None else 0,
            reorder_point=body.reorder_point if body.reorder_point is not None else 0,
            created_at=datetime.utcnow()
        )
        session.add(inv)
    else:
        inv.quantity_on_hand = body.quantity_on_hand
        inv.quantity_reserved = body.quantity_reserved if body.quantity_reserved is not None else inv.quantity_reserved
        inv.reorder_point = body.reorder_point if body.reorder_point is not None else inv.reorder_point
        inv.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(inv)
    response = InventoryResponse.model_validate(inv)
    session.close()
    return response

@app.get("/api/inventory/by-sku", response_model=InventoryBySkuResponse, summary="Get inventory summary by SKU", description="Summarize quantities by warehouse for a part referenced by SKU.", tags=["inventory"], operation_id="get_inventory_by_sku")
async def get_inventory_by_sku(sku: str = Query(..., description="Part SKU to summarize", example="BRK-TOY-001")) -> InventoryBySkuResponse:
    session = SessionLocal()
    part = session.query(Part).filter(Part.sku == sku).first()
    if part is None:
        response = InventoryBySkuResponse(sku=sku, part_id=None, warehouses=[])
        session.close()
        return response
    inv_rows = session.query(Inventory).filter(Inventory.part_id == part.id).all()
    warehouse_totals: Dict[int, Dict[str, int]] = {}
    for inv in inv_rows:
        if inv.warehouse_id not in warehouse_totals:
            warehouse_totals[inv.warehouse_id] = {"on_hand": 0, "reserved": 0}
        warehouse_totals[inv.warehouse_id]["on_hand"] += inv.quantity_on_hand
        warehouse_totals[inv.warehouse_id]["reserved"] += inv.quantity_reserved
    items: List[InventoryBySkuWarehouseItem] = []
    for wh_id, totals in warehouse_totals.items():
        wh = session.query(Warehouse).filter(Warehouse.id == wh_id).first()
        wh_name = wh.name if wh is not None else ""
        items.append(InventoryBySkuWarehouseItem(warehouse_id=wh_id, warehouse_name=wh_name, total_on_hand=totals["on_hand"], total_reserved=totals["reserved"]))
    response = InventoryBySkuResponse(sku=sku, part_id=part.id, warehouses=items)
    session.close()
    return response

@app.patch("/api/inventory/{inventory_id}", response_model=InventoryResponse, summary="Update inventory quantities for a row", description="Adjust quantity_on_hand, quantity_reserved, or reorder_point on a single inventory row.", tags=["inventory"], operation_id="update_inventory_row")
async def update_inventory_row(inventory_id: int = Path(..., description="Inventory row ID", example=1001), body: InventoryUpdateRequest = Body(...)) -> InventoryResponse:
    session = SessionLocal()
    inv = session.query(Inventory).filter(Inventory.id == inventory_id).first()
    if inv is None:
        inv = Inventory(
            id=inventory_id,
            part_id=0,
            warehouse_id=0,
            bin_id=0,
            quantity_on_hand=0,
            quantity_reserved=0,
            reorder_point=0,
            created_at=datetime.utcnow()
        )
        session.add(inv)
        session.commit()
    if body.quantity_on_hand is not None:
        inv.quantity_on_hand = body.quantity_on_hand
    if body.quantity_reserved is not None:
        inv.quantity_reserved = body.quantity_reserved
    if body.reorder_point is not None:
        inv.reorder_point = body.reorder_point
    inv.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(inv)
    response = InventoryResponse.model_validate(inv)
    session.close()
    return response

@app.get("/api/inventory/search", response_model=InventorySearchResponse, summary="Find inventory rows by part and warehouse", description="List inventory rows filtered by part_id or warehouse_id or bin_id.", tags=["inventory"], operation_id="search_inventory")
async def search_inventory(part_id: Optional[int] = Query(None, description="Filter by part ID", example=101), warehouse_id: Optional[int] = Query(None, description="Filter by warehouse ID", example=1), bin_id: Optional[int] = Query(None, description="Filter by bin ID", example=10)) -> InventorySearchResponse:
    session = SessionLocal()
    query = session.query(Inventory)
    if part_id is not None:
        query = query.filter(Inventory.part_id == part_id)
    if warehouse_id is not None:
        query = query.filter(Inventory.warehouse_id == warehouse_id)
    if bin_id is not None:
        query = query.filter(Inventory.bin_id == bin_id)
    rows = query.all()
    items = [InventoryResponse.model_validate(r) for r in rows]
    response = InventorySearchResponse(inventory=items)
    session.close()
    return response

@app.post("/api/inventory/movements", response_model=InventoryMovementResponse, summary="Record an inventory movement between bins", description="Insert an inventory_movements row and adjust inventory rows for a bin transfer.", tags=["inventory_movements"], operation_id="create_inventory_movement")
async def create_inventory_movement(body: InventoryMovementCreateRequest = Body(...)) -> InventoryMovementResponse:
    session = SessionLocal()
    if body.from_bin_id is not None:
        from_inv = session.query(Inventory).filter(Inventory.part_id == body.part_id, Inventory.warehouse_id == body.warehouse_id, Inventory.bin_id == body.from_bin_id).first()
        if from_inv is None:
            from_inv = Inventory(
                part_id=body.part_id,
                warehouse_id=body.warehouse_id,
                bin_id=body.from_bin_id,
                quantity_on_hand=0,
                quantity_reserved=0,
                reorder_point=0,
                created_at=datetime.utcnow()
            )
            session.add(from_inv)
            session.commit()
        from_inv.quantity_on_hand = from_inv.quantity_on_hand - body.quantity
        from_inv.updated_at = datetime.utcnow()
        session.commit()
    if body.to_bin_id is not None:
        to_inv = session.query(Inventory).filter(Inventory.part_id == body.part_id, Inventory.warehouse_id == body.warehouse_id, Inventory.bin_id == body.to_bin_id).first()
        if to_inv is None:
            to_inv = Inventory(
                part_id=body.part_id,
                warehouse_id=body.warehouse_id,
                bin_id=body.to_bin_id,
                quantity_on_hand=0,
                quantity_reserved=0,
                reorder_point=0,
                created_at=datetime.utcnow()
            )
            session.add(to_inv)
            session.commit()
        to_inv.quantity_on_hand = to_inv.quantity_on_hand + body.quantity
        to_inv.updated_at = datetime.utcnow()
        session.commit()
    movement_date_value = datetime.utcnow()
    movement = InventoryMovement(
        part_id=body.part_id,
        warehouse_id=body.warehouse_id,
        from_bin_id=body.from_bin_id,
        to_bin_id=body.to_bin_id,
        quantity=body.quantity,
        movement_type=body.movement_type,
        reference_type=body.reference_type,
        reference_id=body.reference_id,
        movement_date=movement_date_value,
        created_by_user_id=1,
        created_at=datetime.utcnow()
    )
    session.add(movement)
    session.commit()
    session.refresh(movement)
    response = InventoryMovementResponse.model_validate(movement)
    session.close()
    return response

@app.get("/api/customers", response_model=CustomerListResponse, summary="List customer accounts", description="Retrieve customer_accounts filtered by name, price_tier, or customer_group.", tags=["customers"], operation_id="list_customer_accounts")
async def list_customer_accounts(name: Optional[str] = Query(None, description="Filter customers by name (partial match)", example="Joe's Auto"), price_tier: Optional[str] = Query(None, description="Filter by price tier", example="silver"), customer_group: Optional[str] = Query(None, description="Filter by customer group", example="gold")) -> CustomerListResponse:
    session = SessionLocal()
    query = session.query(CustomerAccount)
    if name is not None:
        query = query.filter(CustomerAccount.name.contains(name))
    if price_tier is not None:
        query = query.filter(CustomerAccount.price_tier == price_tier)
    if customer_group is not None:
        query = query.filter(CustomerAccount.customer_group == customer_group)
    customers = query.all()
    items = [CustomerResponse.model_validate(c) for c in customers]
    response = CustomerListResponse(customers=items)
    session.close()
    return response

@app.post("/api/price-tier-rules", response_model=PriceTierRuleResponse, summary="Create a price tier rule", description="Insert a price_tier_rules row defining discount for tier, group, and category.", tags=["pricing"], operation_id="create_price_tier_rule")
async def create_price_tier_rule(body: PriceTierRuleCreateRequest = Body(...)) -> PriceTierRuleResponse:
    session = SessionLocal()
    start_date_value = None
    end_date_value = None
    if body.start_date is not None and body.start_date != "":
        start_date_value = datetime.strptime(body.start_date, "%Y-%m-%d").date()
    if body.end_date is not None and body.end_date != "":
        end_date_value = datetime.strptime(body.end_date, "%Y-%m-%d").date()
    rule = PriceTierRule(
        price_tier=body.price_tier,
        customer_group=body.customer_group,
        category=body.category,
        min_quantity=body.min_quantity if body.min_quantity is not None else 1,
        discount_percent=body.discount_percent,
        start_date=start_date_value,
        end_date=end_date_value,
        is_active=body.is_active if body.is_active is not None else 1,
        created_at=datetime.utcnow()
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    response = PriceTierRuleResponse.model_validate(rule)
    session.close()
    return response

@app.get("/api/price-tier-rules", response_model=PriceTierRuleListResponse, summary="List price tier rules", description="Retrieve price_tier_rules optionally filtered by tier, group, or category.", tags=["pricing"], operation_id="list_price_tier_rules")
async def list_price_tier_rules(price_tier: Optional[str] = Query(None, description="Filter by price tier", example="silver"), customer_group: Optional[str] = Query(None, description="Filter by customer group", example="gold"), category: Optional[str] = Query(None, description="Filter by category", example="Batteries"), is_active: Optional[int] = Query(None, description="Filter by active flag 1/0", example=1)) -> PriceTierRuleListResponse:
    session = SessionLocal()
    query = session.query(PriceTierRule)
    if price_tier is not None:
        query = query.filter(PriceTierRule.price_tier == price_tier)
    if customer_group is not None:
        query = query.filter(PriceTierRule.customer_group == customer_group)
    if category is not None:
        query = query.filter(PriceTierRule.category == category)
    if is_active is not None:
        query = query.filter(PriceTierRule.is_active == is_active)
    rules = query.all()
    items = [PriceTierRuleResponse.model_validate(r) for r in rules]
    response = PriceTierRuleListResponse(rules=items)
    session.close()
    return response

@app.post("/api/pricing/apply-rules", response_model=ApplyPricingResponse, summary="Apply pricing rules to a sales order line", description="Calculate unit_price and discount_percent for a line using price_tier_rules and part defaults.", tags=["pricing"], operation_id="apply_pricing_rules_to_line")
async def apply_pricing_rules_to_line(body: ApplyPricingRequest = Body(...)) -> ApplyPricingResponse:
    session = SessionLocal()
    customer = session.query(CustomerAccount).filter(CustomerAccount.id == body.customer_account_id).first()
    part = session.query(Part).filter(Part.id == body.part_id).first()
    base_price = part.default_list_price if part is not None else 0.0
    discount_total = 0.0
    applied_ids: List[int] = []
    if customer is not None and part is not None:
        order_date_value = datetime.strptime(body.order_date, "%Y-%m-%d").date()
        rules_query = session.query(PriceTierRule).filter(PriceTierRule.is_active == 1)
        rules_query = rules_query.filter((PriceTierRule.price_tier == None) | (PriceTierRule.price_tier == customer.price_tier))
        rules_query = rules_query.filter((PriceTierRule.customer_group == None) | (PriceTierRule.customer_group == customer.customer_group))
        rules_query = rules_query.filter((PriceTierRule.category == None) | (PriceTierRule.category == body.category))
        rules = rules_query.all()
        for rule in rules:
            if body.quantity_ordered >= (rule.min_quantity if rule.min_quantity is not None else 1):
                if rule.start_date is not None and order_date_value < rule.start_date:
                    continue
                if rule.end_date is not None and order_date_value > rule.end_date:
                    continue
                discount_total += rule.discount_percent
                applied_ids.append(rule.id)
    if discount_total < 0.0:
        discount_total = 0.0
    if discount_total > 100.0:
        discount_total = 100.0
    unit_price_value = base_price * (1.0 - discount_total / 100.0)
    response = ApplyPricingResponse(unit_list_price=base_price, unit_price=unit_price_value, discount_percent=discount_total, applied_rule_ids=applied_ids)
    session.close()
    return response

@app.post("/api/pricing/recalculate-open-lines", response_model=RecalculateOpenLinesResponse, summary="Recalculate prices for open order lines by rule", description="Recompute unit_price and discount_percent for matching open sales_order_lines created on a date.", tags=["pricing", "sales_orders"], operation_id="recalculate_open_sales_order_lines")
async def recalculate_open_sales_order_lines(body: RecalculateOpenLinesRequest = Body(...)) -> RecalculateOpenLinesResponse:
    session = SessionLocal()
    order_date_value = datetime.strptime(body.order_date, "%Y-%m-%d").date()
    rules = session.query(PriceTierRule).filter(PriceTierRule.is_active == 1, PriceTierRule.customer_group == body.customer_group, PriceTierRule.category == body.category).all()
    customer_ids_subquery = session.query(CustomerAccount.id).filter(CustomerAccount.customer_group == body.customer_group).subquery()
    orders = session.query(SalesOrder).filter(SalesOrder.customer_account_id.in_(customer_ids_subquery), SalesOrder.order_date == order_date_value, SalesOrder.status == "open").all()
    order_ids = [o.id for o in orders]
    lines = session.query(SalesOrderLine).filter(SalesOrderLine.sales_order_id.in_(order_ids), SalesOrderLine.category == body.category, SalesOrderLine.quantity_ordered >= body.min_quantity).all()
    recalculated_items: List[RecalculatedLineItem] = []
    for line in lines:
        customer = session.query(SalesOrder, CustomerAccount).join(CustomerAccount, SalesOrder.customer_account_id == CustomerAccount.id).filter(SalesOrder.id == line.sales_order_id).first()
        if customer is None:
            continue
        order_obj = customer[0]
        cust_obj = customer[1]
        applicable_discount = 0.0
        applied_rule_ids_local: List[int] = []
        for rule in rules:
            if rule.price_tier is not None and rule.price_tier != cust_obj.price_tier:
                continue
            if rule.min_quantity is not None and line.quantity_ordered < rule.min_quantity:
                continue
            if rule.start_date is not None and order_obj.order_date < rule.start_date:
                continue
            if rule.end_date is not None and order_obj.order_date > rule.end_date:
                continue
            applicable_discount += rule.discount_percent
            applied_rule_ids_local.append(rule.id)
        if applicable_discount < 0.0:
            applicable_discount = 0.0
        if applicable_discount > 100.0:
            applicable_discount = 100.0
        old_unit_price_value = line.unit_price
        old_discount_value = line.discount_percent
        new_unit_price_value = line.unit_list_price * (1.0 - applicable_discount / 100.0)
        line.unit_price = new_unit_price_value
        line.discount_percent = applicable_discount
        line.updated_at = datetime.utcnow()
        session.commit()
        recalculated_items.append(RecalculatedLineItem(sales_order_line_id=line.id, sales_order_id=line.sales_order_id, old_unit_price=old_unit_price_value, new_unit_price=new_unit_price_value, old_discount_percent=old_discount_value, new_discount_percent=applicable_discount))
    response = RecalculateOpenLinesResponse(recalculated_lines=recalculated_items)
    session.close()
    return response

@app.get("/api/suppliers", response_model=SupplierListResponse, summary="List suppliers with optional name filter", description="Retrieve suppliers filtered by name for PO creation.", tags=["suppliers"], operation_id="list_suppliers")
async def list_suppliers(name: Optional[str] = Query(None, description="Filter suppliers by name (partial match)", example="ACME")) -> SupplierListResponse:
    session = SessionLocal()
    query = session.query(Supplier)
    if name is not None:
        query = query.filter(Supplier.name.contains(name))
    suppliers = query.all()
    items = [SupplierListItem.model_validate(s) for s in suppliers]
    response = SupplierListResponse(suppliers=items)
    session.close()
    return response

@app.post("/api/purchase-orders", response_model=PurchaseOrderResponse, summary="Create a purchase order header", description="Insert a purchase_orders row with draft status for a supplier and warehouse.", tags=["purchase_orders"], operation_id="create_purchase_order")
async def create_purchase_order(body: PurchaseOrderCreateRequest = Body(...)) -> PurchaseOrderResponse:
    session = SessionLocal()
    order_date_value = datetime.strptime(body.order_date, "%Y-%m-%d").date()
    expected_receipt_date_value = None
    if body.expected_receipt_date is not None and body.expected_receipt_date != "":
        expected_receipt_date_value = datetime.strptime(body.expected_receipt_date, "%Y-%m-%d").date()
    po = PurchaseOrder(
        po_number=body.po_number,
        supplier_id=body.supplier_id,
        warehouse_id=body.warehouse_id,
        status=body.status,
        order_date=order_date_value,
        expected_receipt_date=expected_receipt_date_value,
        created_by_user_id=1,
        created_at=datetime.utcnow()
    )
    session.add(po)
    session.commit()
    session.refresh(po)
    response = PurchaseOrderResponse.model_validate(po)
    session.close()
    return response

@app.patch("/api/purchase-orders/{purchase_order_id}", response_model=PurchaseOrderUpdateResponse, summary="Update purchase order header fields", description="Update status or expected_receipt_date of a purchase_orders row.", tags=["purchase_orders"], operation_id="update_purchase_order")
async def update_purchase_order(purchase_order_id: int = Path(..., description="PO ID", example=600), body: PurchaseOrderUpdateRequest = Body(...)) -> PurchaseOrderUpdateResponse:
    session = SessionLocal()
    po = session.query(PurchaseOrder).filter(PurchaseOrder.id == purchase_order_id).first()
    if po is None:
        po = PurchaseOrder(
            id=purchase_order_id,
            po_number="",
            supplier_id=0,
            warehouse_id=0,
            status="",
            order_date=date.today(),
            expected_receipt_date=None,
            created_by_user_id=1,
            created_at=datetime.utcnow()
        )
        session.add(po)
        session.commit()
    if body.status is not None:
        po.status = body.status
    if body.expected_receipt_date is not None and body.expected_receipt_date != "":
        po.expected_receipt_date = datetime.strptime(body.expected_receipt_date, "%Y-%m-%d").date()
    po.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(po)
    response = PurchaseOrderUpdateResponse.model_validate(po)
    session.close()
    return response

@app.post("/api/purchase-orders/{purchase_order_id}/lines", response_model=PurchaseOrderLineResponse, summary="Add a line to a purchase order", description="Insert a purchase_order_lines row for a part on a purchase order.", tags=["purchase_order_lines"], operation_id="create_purchase_order_line")
async def create_purchase_order_line(purchase_order_id: int = Path(..., description="Parent purchase order ID", example=600), body: PurchaseOrderLineCreateRequest = Body(...)) -> PurchaseOrderLineResponse:
    session = SessionLocal()
    line = PurchaseOrderLine(
        purchase_order_id=purchase_order_id,
        line_number=body.line_number,
        part_id=body.part_id,
        sku=body.sku,
        quantity_ordered=body.quantity_ordered,
        quantity_received=0,
        unit_cost=body.unit_cost,
        created_at=datetime.utcnow()
    )
    session.add(line)
    session.commit()
    session.refresh(line)
    response = PurchaseOrderLineResponse.model_validate(line)
    session.close()
    return response

@app.post("/api/sales-orders", response_model=SalesOrderResponse, summary="Create a sales order header", description="Insert a sales_orders row for a customer, warehouse, and requested_ship_date.", tags=["sales_orders"], operation_id="create_sales_order")
async def create_sales_order(body: SalesOrderCreateRequest = Body(...)) -> SalesOrderResponse:
    session = SessionLocal()
    requested_ship_date_value = datetime.strptime(body.requested_ship_date, "%Y-%m-%d").date()
    order_date_value = datetime.strptime(body.order_date, "%Y-%m-%d").date()
    so = SalesOrder(
        order_number=body.order_number,
        customer_account_id=body.customer_account_id,
        warehouse_id=body.warehouse_id,
        status=body.status,
        requested_ship_date=requested_ship_date_value,
        order_date=order_date_value,
        ship_to_name=body.ship_to_name,
        ship_to_address_line1=body.ship_to_address_line1,
        ship_to_city=body.ship_to_city,
        ship_to_state=body.ship_to_state,
        ship_to_postal_code=body.ship_to_postal_code,
        ship_to_country=body.ship_to_country,
        created_by_user_id=1,
        created_at=datetime.utcnow()
    )
    session.add(so)
    session.commit()
    session.refresh(so)
    response = SalesOrderResponse.model_validate(so)
    session.close()
    return response

@app.get("/api/sales-orders/by-number/{order_number}", response_model=SalesOrderResponse, summary="Get sales order by order_number", description="Retrieve a sales_orders row using its order_number string.", tags=["sales_orders"], operation_id="get_sales_order_by_number")
async def get_sales_order_by_number(order_number: str = Path(..., description="Order number to look up", example="SO-2026-00045")) -> SalesOrderResponse:
    session = SessionLocal()
    so = session.query(SalesOrder).filter(SalesOrder.order_number == order_number).first()
    if so is None:
        so = SalesOrder(
            id=0,
            order_number=order_number,
            customer_account_id=0,
            warehouse_id=0,
            status="",
            requested_ship_date=date.today(),
            order_date=date.today(),
            created_by_user_id=1,
            created_at=datetime.utcnow()
        )
    response = SalesOrderResponse.model_validate(so)
    session.close()
    return response

@app.post("/api/sales-orders/{sales_order_id}/lines", response_model=SalesOrderLineResponse, summary="Add a line to a sales order", description="Insert a sales_order_lines row with pricing and backorder_status.", tags=["sales_order_lines"], operation_id="create_sales_order_line")
async def create_sales_order_line(sales_order_id: int = Path(..., description="Parent sales order ID", example=700), body: SalesOrderLineCreateRequest = Body(...)) -> SalesOrderLineResponse:
    session = SessionLocal()
    line = SalesOrderLine(
        sales_order_id=sales_order_id,
        line_number=body.line_number,
        part_id=body.part_id,
        sku=body.sku,
        quantity_ordered=body.quantity_ordered,
        quantity_allocated=body.quantity_ordered,
        quantity_shipped=0,
        backorder_status=body.backorder_status,
        unit_list_price=body.unit_list_price,
        unit_price=body.unit_price,
        discount_percent=body.discount_percent,
        category=body.category,
        created_at=datetime.utcnow()
    )
    session.add(line)
    session.commit()
    session.refresh(line)
    response = SalesOrderLineResponse.model_validate(line)
    session.close()
    return response

@app.get("/api/sales-orders/{sales_order_id}/lines", response_model=SalesOrderLineListResponse, summary="List lines for a sales order", description="Retrieve all sales_order_lines for a given sales order ID.", tags=["sales_order_lines"], operation_id="list_sales_order_lines")
async def list_sales_order_lines(sales_order_id: int = Path(..., description="Sales order ID", example=700)) -> SalesOrderLineListResponse:
    session = SessionLocal()
    lines = session.query(SalesOrderLine).filter(SalesOrderLine.sales_order_id == sales_order_id).all()
    items = [SalesOrderLineResponse.model_validate(l) for l in lines]
    response = SalesOrderLineListResponse(lines=items)
    session.close()
    return response

@app.post("/api/sales-orders/allocate-line", response_model=AllocateInventoryResponse, summary="Allocate inventory to a sales order line", description="Increase quantity_allocated for a line and increase quantity_reserved in inventory.", tags=["sales_orders", "inventory"], operation_id="allocate_inventory_to_sales_order_line")
async def allocate_inventory_to_sales_order_line(body: AllocateInventoryRequest = Body(...)) -> AllocateInventoryResponse:
    session = SessionLocal()
    line = session.query(SalesOrderLine).filter(SalesOrderLine.id == body.sales_order_line_id).first()
    inv = session.query(Inventory).filter(Inventory.id == body.inventory_id).first()
    if line is None or inv is None:
        response = AllocateInventoryResponse(sales_order_line_id=body.sales_order_line_id, new_quantity_allocated=0, inventory_id=body.inventory_id, new_inventory_reserved=0)
        session.close()
        return response
    line.quantity_allocated = line.quantity_allocated + body.quantity_to_allocate
    line.updated_at = datetime.utcnow()
    inv.quantity_reserved = inv.quantity_reserved + body.quantity_to_allocate
    inv.updated_at = datetime.utcnow()
    session.commit()
    new_alloc = line.quantity_allocated
    new_reserved = inv.quantity_reserved
    response = AllocateInventoryResponse(sales_order_line_id=line.id, new_quantity_allocated=new_alloc, inventory_id=inv.id, new_inventory_reserved=new_reserved)
    session.close()
    return response

@app.patch("/api/sales-orders/{sales_order_id}", response_model=SalesOrderUpdateResponse, summary="Update sales order header status or dates", description="Change status or requested_ship_date fields on a sales_orders row.", tags=["sales_orders"], operation_id="update_sales_order")
async def update_sales_order(sales_order_id: int = Path(..., description="Sales order ID", example=700), body: SalesOrderUpdateRequest = Body(...)) -> SalesOrderUpdateResponse:
    session = SessionLocal()
    so = session.query(SalesOrder).filter(SalesOrder.id == sales_order_id).first()
    if so is None:
        so = SalesOrder(
            id=sales_order_id,
            order_number="",
            customer_account_id=0,
            warehouse_id=0,
            status="",
            requested_ship_date=date.today(),
            order_date=date.today(),
            created_by_user_id=1,
            created_at=datetime.utcnow()
        )
        session.add(so)
        session.commit()
    if body.status is not None:
        so.status = body.status
    if body.requested_ship_date is not None and body.requested_ship_date != "":
        so.requested_ship_date = datetime.strptime(body.requested_ship_date, "%Y-%m-%d").date()
    so.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(so)
    response = SalesOrderUpdateResponse.model_validate(so)
    session.close()
    return response

@app.patch("/api/sales-order-lines/{sales_order_line_id}", response_model=SalesOrderLineUpdateResponse, summary="Update sales order line quantities or backorder status", description="Update quantity_shipped or backorder_status on a sales_order_lines row.", tags=["sales_order_lines"], operation_id="update_sales_order_line")
async def update_sales_order_line(sales_order_line_id: int = Path(..., description="Line ID to update", example=8001), body: SalesOrderLineUpdateRequest = Body(...)) -> SalesOrderLineUpdateResponse:
    session = SessionLocal()
    line = session.query(SalesOrderLine).filter(SalesOrderLine.id == sales_order_line_id).first()
    if line is None:
        line = SalesOrderLine(
            id=sales_order_line_id,
            sales_order_id=0,
            line_number=0,
            part_id=0,
            sku="",
            quantity_ordered=0,
            quantity_allocated=0,
            quantity_shipped=0,
            backorder_status="",
            unit_list_price=0.0,
            unit_price=0.0,
            discount_percent=0.0,
            category="",
            created_at=datetime.utcnow()
        )
        session.add(line)
        session.commit()
    if body.quantity_shipped is not None:
        line.quantity_shipped = body.quantity_shipped
    if body.backorder_status is not None:
        line.backorder_status = body.backorder_status
    if body.unit_price is not None:
        line.unit_price = body.unit_price
    if body.discount_percent is not None:
        line.discount_percent = body.discount_percent
    line.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(line)
    response = SalesOrderLineUpdateResponse.model_validate(line)
    session.close()
    return response

@app.get("/api/warehouse-service-zones", response_model=WarehouseServiceZoneListResponse, summary="List warehouse service zones", description="Retrieve warehouse_service_zones to see transit_days by postal_code_prefix.", tags=["service_zones"], operation_id="list_warehouse_service_zones")
async def list_warehouse_service_zones(warehouse_id: Optional[int] = Query(None, description="Filter by warehouse ID", example=2)) -> WarehouseServiceZoneListResponse:
    session = SessionLocal()
    query = session.query(WarehouseServiceZone)
    if warehouse_id is not None:
        query = query.filter(WarehouseServiceZone.warehouse_id == warehouse_id)
    zones = query.all()
    items = [WarehouseServiceZoneResponse.model_validate(z) for z in zones]
    response = WarehouseServiceZoneListResponse(zones=items)
    session.close()
    return response

@app.get("/api/availability", response_model=AvailabilityResponse, summary="Check availability and ETA for a SKU and destination ZIP", description="Find best warehouse with available quantity and estimated_delivery_date using transit_days.", tags=["availability"], operation_id="check_availability_by_sku_and_zip")
async def check_availability_by_sku_and_zip(sku: str = Query(..., description="Part SKU to check availability", example="ALT-HON-2.4L"), destination_zip: str = Query(..., description="Destination ZIP/postal code", example="94107"), ship_date: Optional[str] = Query(None, description="Planned ship date YYYY-MM-DD for ETA calc; defaults to today", example="2026-01-02")) -> AvailabilityResponse:
    session = SessionLocal()
    part = session.query(Part).filter(Part.sku == sku).first()
    if ship_date is not None and ship_date != "":
        ship_date_value = datetime.strptime(ship_date, "%Y-%m-%d").date()
    else:
        ship_date_value = date.today()
    if part is None:
        response = AvailabilityResponse(sku=sku, part_id=None, best_warehouse=None, alternatives=[])
        session.close()
        return response
    inv_rows = session.query(Inventory).filter(Inventory.part_id == part.id).all()
    availability_by_wh: Dict[int, int] = {}
    for inv in inv_rows:
        available = inv.quantity_on_hand - inv.quantity_reserved
        if available < 0:
            available = 0
        if inv.warehouse_id not in availability_by_wh:
            availability_by_wh[inv.warehouse_id] = 0
        availability_by_wh[inv.warehouse_id] += available
    alternatives: List[AvailabilityAlternativeItem] = []
    best: Optional[AvailabilityBestWarehouse] = None
    for wh_id, qty in availability_by_wh.items():
        if qty <= 0:
            continue
        wh = session.query(Warehouse).filter(Warehouse.id == wh_id).first()
        wh_name = wh.name if wh is not None else ""
        prefix = destination_zip[:3]
        zone = session.query(WarehouseServiceZone).filter(WarehouseServiceZone.warehouse_id == wh_id, WarehouseServiceZone.postal_code_prefix == prefix).first()
        transit_days_value = zone.transit_days if zone is not None else 5
        eta = ship_date_value + timedelta(days=transit_days_value)
        eta_str = eta.strftime("%Y-%m-%d")
        item = AvailabilityAlternativeItem(warehouse_id=wh_id, warehouse_name=wh_name, available_quantity=qty, estimated_delivery_date=eta_str)
        alternatives.append(item)
    alternatives_sorted = sorted(alternatives, key=lambda x: x.estimated_delivery_date)
    if len(alternatives_sorted) > 0:
        first = alternatives_sorted[0]
        best = AvailabilityBestWarehouse(warehouse_id=first.warehouse_id, warehouse_name=first.warehouse_name, available_quantity=first.available_quantity, estimated_delivery_date=first.estimated_delivery_date)
        remaining = alternatives_sorted[1:]
    else:
        remaining = []
    response = AvailabilityResponse(sku=sku, part_id=part.id, best_warehouse=best, alternatives=remaining)
    session.close()
    return response

@app.post("/api/shipments", response_model=ShipmentResponse, summary="Create a shipment for a sales order", description="Insert a shipments row with carrier, tracking_number, ship_date, and warehouse.", tags=["shipments"], operation_id="create_shipment")
async def create_shipment(body: ShipmentCreateRequest = Body(...)) -> ShipmentResponse:
    session = SessionLocal()
    ship_date_value = datetime.strptime(body.ship_date, "%Y-%m-%d").date()
    shipment = Shipment(
        shipment_number=body.shipment_number,
        sales_order_id=body.sales_order_id,
        warehouse_id=body.warehouse_id,
        carrier=body.carrier,
        service_level=body.service_level,
        tracking_number=body.tracking_number,
        ship_date=ship_date_value,
        created_by_user_id=1,
        created_at=datetime.utcnow()
    )
    session.add(shipment)
    session.commit()
    session.refresh(shipment)
    response = ShipmentResponse.model_validate(shipment)
    session.close()
    return response

@app.post("/api/shipments/{shipment_id}/lines", response_model=ShipmentLineResponse, summary="Add a line to a shipment", description="Insert a shipment_lines row, linking to a sales_order_line and optional bin.", tags=["shipment_lines"], operation_id="create_shipment_line")
async def create_shipment_line(shipment_id: int = Path(..., description="Parent shipment ID", example=900), body: ShipmentLineCreateRequest = Body(...)) -> ShipmentLineResponse:
    session = SessionLocal()
    line = ShipmentLine(
        shipment_id=shipment_id,
        sales_order_line_id=body.sales_order_line_id,
        part_id=body.part_id,
        sku=body.sku,
        quantity_shipped=body.quantity_shipped,
        warehouse_id=body.warehouse_id,
        bin_id=body.bin_id,
        created_at=datetime.utcnow()
    )
    session.add(line)
    session.commit()
    session.refresh(line)
    response = ShipmentLineResponse.model_validate(line)
    session.close()
    return response

@app.get("/api/shipments/by-order/{sales_order_id}", response_model=ShipmentListResponse, summary="List shipments for a sales order", description="Retrieve shipments rows for a specific sales_order_id.", tags=["shipments"], operation_id="list_shipments_for_order")
async def list_shipments_for_order(sales_order_id: int = Path(..., description="Sales order ID", example=700)) -> ShipmentListResponse:
    session = SessionLocal()
    shipments = session.query(Shipment).filter(Shipment.sales_order_id == sales_order_id).all()
    items = [ShipmentResponse.model_validate(s) for s in shipments]
    response = ShipmentListResponse(shipments=items)
    session.close()
    return response

@app.get("/api/shipments/{shipment_id}/lines", response_model=ShipmentLineListResponse, summary="List lines for a shipment", description="Retrieve shipment_lines for a given shipment_id including quantities and bins.", tags=["shipment_lines"], operation_id="list_shipment_lines")
async def list_shipment_lines(shipment_id: int = Path(..., description="Shipment ID", example=900)) -> ShipmentLineListResponse:
    session = SessionLocal()
    lines = session.query(ShipmentLine).filter(ShipmentLine.shipment_id == shipment_id).all()
    items = [ShipmentLineResponse.model_validate(l) for l in lines]
    response = ShipmentLineListResponse(lines=items)
    session.close()
    return response

@app.get("/api/reports/pick-list", response_model=PickListResponse, summary="Generate pick list for a warehouse and ship date", description="Return pick_list lines for open orders shipping on a date from a warehouse grouped by bin.", tags=["reports", "warehouse_operations"], operation_id="generate_pick_list")
async def generate_pick_list(warehouse_id: int = Query(..., description="Warehouse preparing the picks", example=2), ship_date: str = Query(..., description="Requested ship date YYYY-MM-DD to pick for", example="2026-01-03")) -> PickListResponse:
    session = SessionLocal()
    ship_date_value = datetime.strptime(ship_date, "%Y-%m-%d").date()
    orders = session.query(SalesOrder).filter(SalesOrder.warehouse_id == warehouse_id, SalesOrder.requested_ship_date == ship_date_value, SalesOrder.status == "open").all()
    items: List[PickListItem] = []
    for order in orders:
        lines = session.query(SalesOrderLine).filter(SalesOrderLine.sales_order_id == order.id).all()
        customer = session.query(CustomerAccount).filter(CustomerAccount.id == order.customer_account_id).first()
        customer_name = customer.name if customer is not None else None
        for line in lines:
            quantity_to_pick = line.quantity_allocated - line.quantity_shipped
            if quantity_to_pick <= 0:
                continue
            inv_rows = session.query(Inventory, WarehouseBin).join(WarehouseBin, Inventory.bin_id == WarehouseBin.id).filter(Inventory.part_id == line.part_id, Inventory.warehouse_id == warehouse_id).all()
            remaining = quantity_to_pick
            for inv_row, bin_obj in inv_rows:
                available = inv_row.quantity_on_hand - inv_row.quantity_reserved
                if available <= 0:
                    continue
                qty_from_bin = remaining if remaining <= available else available
                items.append(PickListItem(bin_code=bin_obj.bin_code, warehouse_bin_id=bin_obj.id, order_number=order.order_number, sales_order_id=order.id, sales_order_line_id=line.id, customer_name=customer_name, sku=line.sku, quantity_to_pick=qty_from_bin))
                remaining = remaining - qty_from_bin
                if remaining <= 0:
                    break
            if remaining > 0 and len(inv_rows) == 0:
                items.append(PickListItem(bin_code=None, warehouse_bin_id=None, order_number=order.order_number, sales_order_id=order.id, sales_order_line_id=line.id, customer_name=customer_name, sku=line.sku, quantity_to_pick=remaining))
    response = PickListResponse(warehouse_id=warehouse_id, ship_date=ship_date, items=items)
    session.close()
    return response

@app.get("/api/reports/stock-aging", response_model=StockAgingResponse, summary="Run stock aging report for a warehouse and category", description="Return parts with quantity_on_hand and average age in days exceeding threshold, sorted by quantity.", tags=["reports", "inventory"], operation_id="stock_aging_report")
async def stock_aging_report(warehouse_id: int = Query(..., description="Warehouse to analyze", example=5), category: str = Query(..., description="Part category filter", example="Suspension"), min_quantity_on_hand: int = Query(..., description="Minimum on-hand quantity threshold", example=50), min_average_age_days: int = Query(..., description="Minimum average age in days", example=90)) -> StockAgingResponse:
    session = SessionLocal()
    parts_in_category = session.query(Part).filter(Part.category == category).all()
    items: List[StockAgingItem] = []
    today_value = date.today()
    for part in parts_in_category:
        inv_rows = session.query(Inventory).filter(Inventory.part_id == part.id, Inventory.warehouse_id == warehouse_id).all()
        total_on_hand = sum(r.quantity_on_hand for r in inv_rows)
        if total_on_hand < min_quantity_on_hand or total_on_hand <= 0:
            continue
        lots = session.query(InventoryLot).filter(InventoryLot.part_id == part.id, InventoryLot.warehouse_id == warehouse_id).all()
        if len(lots) == 0:
            average_age = 0.0
        else:
            total_qty = 0
            weighted_age_sum = 0.0
            for lot in lots:
                qty = lot.quantity_on_hand
                total_qty += qty
                age_days = (today_value - lot.received_date).days
                weighted_age_sum += age_days * qty
            if total_qty > 0:
                average_age = weighted_age_sum / float(total_qty)
            else:
                average_age = 0.0
        if average_age < float(min_average_age_days):
            continue
        items.append(StockAgingItem(part_id=part.id, sku=part.sku, description=part.description, quantity_on_hand=total_on_hand, average_age_in_days=average_age))
    items_sorted = sorted(items, key=lambda x: x.quantity_on_hand, reverse=True)
    response = StockAgingResponse(warehouse_id=warehouse_id, category=category, items=items_sorted)
    session.close()
    return response

@app.get("/api/reports/fill-rate", response_model=FillRateReportResponse, summary="Calculate fill rate and top moving parts for a period", description="Compute percent of orders fully filled on requested_ship_date plus top 10 parts by shipped qty.", tags=["reports", "sales_orders"], operation_id="fill_rate_report")
async def fill_rate_report(start_date: str = Query(..., description="Start date YYYY-MM-DD of analysis window", example="2026-01-01"), end_date: str = Query(..., description="End date YYYY-MM-DD of analysis window", example="2026-01-30")) -> FillRateReportResponse:
    session = SessionLocal()
    start_date_value = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_value = datetime.strptime(end_date, "%Y-%m-%d").date()
    orders = session.query(SalesOrder).filter(SalesOrder.requested_ship_date >= start_date_value, SalesOrder.requested_ship_date <= end_date_value).all()
    total_orders = len(orders)
    orders_filled_on_time = 0
    for order in orders:
        lines = session.query(SalesOrderLine).filter(SalesOrderLine.sales_order_id == order.id).all()
        if len(lines) == 0:
            continue
        total_ordered = sum(l.quantity_ordered for l in lines)
        total_shipped = sum(l.quantity_shipped for l in lines)
        if total_ordered > 0 and total_shipped >= total_ordered:
            shipments_for_order = session.query(Shipment).filter(Shipment.sales_order_id == order.id).all()
            if len(shipments_for_order) == 0:
                continue
            latest_ship_date = max(s.ship_date for s in shipments_for_order)
            if latest_ship_date <= order.requested_ship_date:
                orders_filled_on_time += 1
    fill_rate_percent_value = 0.0
    if total_orders > 0:
        fill_rate_percent_value = (orders_filled_on_time / float(total_orders)) * 100.0
    shipments_in_window = session.query(Shipment).filter(Shipment.ship_date >= start_date_value, Shipment.ship_date <= end_date_value).all()
    shipment_ids = [s.id for s in shipments_in_window]
    shipment_lines = session.query(ShipmentLine).filter(ShipmentLine.shipment_id.in_(shipment_ids)).all()
    qty_by_part: Dict[int, int] = {}
    for line in shipment_lines:
        if line.part_id not in qty_by_part:
            qty_by_part[line.part_id] = 0
        qty_by_part[line.part_id] += line.quantity_shipped
    top_items: List[FillRateTopPartItem] = []
    for part_id_key, qty in qty_by_part.items():
        part = session.query(Part).filter(Part.id == part_id_key).first()
        sku_value = part.sku if part is not None else ""
        top_items.append(FillRateTopPartItem(part_id=part_id_key, sku=sku_value, total_quantity_shipped=qty))
    top_items_sorted = sorted(top_items, key=lambda x: x.total_quantity_shipped, reverse=True)[:10]
    response = FillRateReportResponse(start_date=start_date, end_date=end_date, total_orders=total_orders, orders_filled_on_time=orders_filled_on_time, fill_rate_percent=fill_rate_percent_value, top_moving_parts=top_items_sorted)
    session.close()
    return response

if __name__ == "__main__":
    import uvicorn, os
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)