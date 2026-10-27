def verify_task_completion(initial_db_path: str, final_db_path: str, final_answer: str | None = None) -> dict:
    import sqlite3
    import re

    def safe_query(db_path: str, query: str, params: tuple = ()) -> list:
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception:
            return []

    # Get all sales_order IDs from initial_db
    initial_orders = safe_query(initial_db_path, "SELECT id FROM sales_orders")
    initial_order_ids = {row['id'] for row in initial_orders}

    # Get all sales_order IDs from final_db
    final_orders = safe_query(final_db_path, "SELECT id FROM sales_orders")
    final_order_ids = {row['id'] for row in final_orders}

    # Find new order IDs
    new_order_ids = final_order_ids - initial_order_ids

    if not new_order_ids:
        return {"result": "others"}

    # Check each new order to see if it matches requirements
    for order_id in new_order_ids:
        # Get the sales_order details
        order_query = """SELECT so.*, ca.name as customer_name, ca.price_tier 
                         FROM sales_orders so 
                         JOIN customer_accounts ca ON so.customer_account_id = ca.id 
                         WHERE so.id = ?"""
        order_results = safe_query(final_db_path, order_query, (order_id,))
        
        if not order_results:
            continue
        
        order = order_results[0]
        
        # Check customer_account is 'Joe's Auto Repair' with price_tier 'silver'
        if order.get('customer_name') != "Joe's Auto Repair":
            continue
        if order.get('price_tier') != 'silver':
            continue
        
        # Check requested_ship_date is '2026-01-05'
        if order.get('requested_ship_date') != '2026-01-05':
            continue
        
        # Get order_lines for this order
        lines_query = """SELECT sol.*, p.sku, p.category, p.default_list_price
                         FROM sales_order_lines sol
                         JOIN parts p ON sol.part_id = p.id
                         WHERE sol.sales_order_id = ?
                         ORDER BY sol.line_number"""
        lines = safe_query(final_db_path, lines_query, (order_id,))
        
        # Must have exactly 3 lines
        if len(lines) != 3:
            continue
        
        # Check each line matches specifications
        expected_lines = [
            {'sku': 'OIL-FLTR-001', 'quantity': 10, 'category': 'Oil & Filters', 'list_price': 9.99, 'discount': 8.0},
            {'sku': 'BRK-TOY-001', 'quantity': 4, 'category': 'Brakes', 'list_price': 89.99, 'discount': 5.0},
            {'sku': 'BAT-12V-600CCA', 'quantity': 2, 'category': 'Batteries', 'list_price': 129.99, 'discount': 0.0}
        ]
        
        all_lines_match = True
        for i, expected in enumerate(expected_lines):
            if i >= len(lines):
                all_lines_match = False
                break
            
            line = lines[i]
            
            # Check SKU
            if line.get('sku') != expected['sku']:
                all_lines_match = False
                break
            
            # Check quantity_ordered
            if line.get('quantity_ordered') != expected['quantity']:
                all_lines_match = False
                break
            
            # Check category
            if line.get('category') != expected['category']:
                all_lines_match = False
                break
            
            # Check unit_list_price
            list_price = line.get('unit_list_price')
            if list_price is None or abs(list_price - expected['list_price']) > 0.01:
                all_lines_match = False
                break
            
            # Check discount_percent
            discount = line.get('discount_percent', 0.0)
            if abs(discount - expected['discount']) > 0.01:
                all_lines_match = False
                break
            
            # Calculate expected unit_price
            expected_unit_price = expected['list_price'] * (1 - expected['discount'] / 100.0)
            actual_unit_price = line.get('unit_price')
            if actual_unit_price is None or abs(actual_unit_price - expected_unit_price) > 0.01:
                all_lines_match = False
                break
            
            # Check backorder_status is 'allow'
            backorder_status = line.get('backorder_status')
            if backorder_status != 'allow':
                all_lines_match = False
                break
        
        if all_lines_match:
            return {"result": "complete"}
    
    return {"result": "others"}
