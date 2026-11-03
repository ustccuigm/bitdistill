def verify_task_completion(initial_db_path: str, final_db_path: str, final_answer: str | None = None) -> dict:
    import sqlite3
    
    def safe_query(db_path: str, query: str, params: tuple = ()) -> list:
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception:
            return []
    
    # Step 1: Get PO-10457's ID from initial database
    po_query = "SELECT id FROM purchase_orders WHERE po_number = ?"
    po_initial = safe_query(initial_db_path, po_query, ('PO-10457',))
    po_final = safe_query(final_db_path, po_query, ('PO-10457',))
    
    if not po_initial or not po_final:
        return {"result": "others"}
    
    po_id = po_initial[0][0]
    
    # Step 2: Get all purchase_order_items for PO-10457 from initial database
    po_items_query = "SELECT id, quantity_case_packs FROM purchase_order_items WHERE purchase_order_id = ?"
    po_items_initial = safe_query(initial_db_path, po_items_query, (po_id,))
    
    if not po_items_initial:
        return {"result": "others"}
    
    expected_item_count = len(po_items_initial)
    expected_items = {item[0]: item[1] for item in po_items_initial}
    
    # Step 3: Verify no shipment existed for PO-10457 in initial database
    initial_shipments = safe_query(initial_db_path, "SELECT id FROM shipments WHERE purchase_order_id = ?", (po_id,))
    if initial_shipments:
        return {"result": "others"}
    
    # Step 4: Find the new shipment in final database
    shipment_query = """SELECT id, carrier, tracking_number, ship_date, expected_delivery_date 
                        FROM shipments 
                        WHERE purchase_order_id = ?"""
    final_shipments = safe_query(final_db_path, shipment_query, (po_id,))
    
    if len(final_shipments) != 1:
        return {"result": "others"}
    
    shipment_id, carrier, tracking_number, ship_date, expected_delivery_date = final_shipments[0]
    
    # Step 5: Verify shipment details match requirements
    if carrier != 'UPS':
        return {"result": "others"}
    if tracking_number != '1Z999AA10123456784':
        return {"result": "others"}
    if ship_date != '2026-01-11':
        return {"result": "others"}
    if expected_delivery_date != '2026-01-15':
        return {"result": "others"}
    
    # Step 6: Verify shipment_items link to all PO items
    shipment_items_query = "SELECT po_item_id, quantity_case_packs FROM shipment_items WHERE shipment_id = ?"
    shipment_items = safe_query(final_db_path, shipment_items_query, (shipment_id,))
    
    if len(shipment_items) != expected_item_count:
        return {"result": "others"}
    
    # Verify each shipment_item matches the correct PO item with correct quantity
    for po_item_id, quantity in shipment_items:
        if po_item_id not in expected_items:
            return {"result": "others"}
        if quantity != expected_items[po_item_id]:
            return {"result": "others"}
    
    # Step 7: Verify purchase order status and expected_delivery_date
    po_status_query = "SELECT status, expected_delivery_date FROM purchase_orders WHERE id = ?"
    po_status = safe_query(final_db_path, po_status_query, (po_id,))
    
    if not po_status:
        return {"result": "others"}
    
    status, po_expected_delivery = po_status[0]
    
    # The task says to keep status as 'shipped', but initial status is 'pending'
    # Check if status was updated to 'shipped' (as the task implies it should be)
    if status != 'shipped':
        return {"result": "others"}
    
    if po_expected_delivery != '2026-01-15':
        return {"result": "others"}
    
    # All checks passed
    return {"result": "complete"}