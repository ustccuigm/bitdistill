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
    
    order_id = 'PO-2025-000981'
    budget_limit = 15000.0
    
    # Check initial state - order should be 'draft'
    initial_order = safe_query(initial_db_path, "SELECT status, total_amount FROM orders WHERE id = ?", (order_id,))
    if not initial_order or len(initial_order) == 0:
        return {"result": "others"}
    
    initial_status = initial_order[0][0]
    if initial_status != 'draft':
        return {"result": "others"}
    
    # Check final state - order should be 'submitted'
    final_order = safe_query(final_db_path, "SELECT status, total_amount, budget_limit FROM orders WHERE id = ?", (order_id,))
    if not final_order or len(final_order) == 0:
        return {"result": "others"}
    
    final_status = final_order[0][0]
    final_total = final_order[0][1]
    final_budget = final_order[0][2]
    
    # Verify status changed to 'submitted'
    if final_status != 'submitted':
        return {"result": "others"}
    
    # Verify all order_lines have non-null negotiated_price
    order_lines = safe_query(final_db_path, "SELECT id, negotiated_price, line_total FROM order_lines WHERE order_id = ?", (order_id,))
    if not order_lines or len(order_lines) == 0:
        return {"result": "others"}
    
    for line in order_lines:
        negotiated_price = line[1]
        if negotiated_price is None:
            return {"result": "others"}
    
    # Verify total_amount does not exceed budget_limit
    if final_total is None or final_total > budget_limit:
        return {"result": "others"}
    
    # Verify total_amount matches sum of line_total
    calculated_total = sum(line[2] if line[2] is not None else 0 for line in order_lines)
    # Allow small floating point difference
    if abs(calculated_total - final_total) > 0.01:
        return {"result": "others"}
    
    # All checks passed
    return {"result": "complete"}