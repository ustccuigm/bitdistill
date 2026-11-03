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
    
    # First, get the lessee_id for invoice 2033 from initial database
    invoice_query = "SELECT i.id, i.payment_status, i.total_amount, i.lease_id, l.lessee_id FROM invoices i JOIN leases l ON i.lease_id = l.id WHERE i.id = 2033"
    initial_invoice = safe_query(initial_db_path, invoice_query)
    final_invoice = safe_query(final_db_path, invoice_query)
    
    if not initial_invoice or not final_invoice:
        return {"result": "others"}
    
    initial_status = initial_invoice[0][1]
    final_status = final_invoice[0][1]
    total_amount = initial_invoice[0][2]
    lessee_id = initial_invoice[0][4]
    
    # Check 1: Invoice 2033 payment_status must change from 'unpaid' to 'paid'
    if initial_status != 'unpaid' or final_status != 'paid':
        return {"result": "others"}
    
    # Check 2: Get all payment IDs from initial database
    initial_payment_ids = safe_query(initial_db_path, "SELECT id FROM payments")
    initial_payment_id_set = set(row[0] for row in initial_payment_ids)
    
    # Check 3: Find NEW payments in final database with correct specifications
    new_payments_query = """SELECT id, lessee_id, payment_date, amount, currency, method 
                            FROM payments 
                            WHERE payment_date = '2026-03-10' 
                            AND amount = 1070.0 
                            AND currency = 'USD' 
                            AND method = 'bank_transfer'"""
    final_payments = safe_query(final_db_path, new_payments_query)
    
    if not final_payments:
        return {"result": "others"}
    
    # Find which payment is NEW (not in initial database)
    new_payment_id = None
    new_payment_lessee_id = None
    for payment in final_payments:
        payment_id = payment[0]
        payment_lessee_id = payment[1]
        if payment_id not in initial_payment_id_set:
            new_payment_id = payment_id
            new_payment_lessee_id = payment_lessee_id
            break
    
    if new_payment_id is None:
        return {"result": "others"}
    
    # Check 4: Verify the payment is associated with the correct lessee
    if new_payment_lessee_id != lessee_id:
        return {"result": "others"}
    
    # Check 5: Get all payment allocation IDs from initial database
    initial_allocation_ids = safe_query(initial_db_path, "SELECT id FROM payment_allocations")
    initial_allocation_id_set = set(row[0] for row in initial_allocation_ids)
    
    # Check 6: Verify NEW payment_allocation exists linking the new payment to invoice 2033
    allocation_query = """SELECT id, payment_id, invoice_id, allocated_amount 
                          FROM payment_allocations 
                          WHERE payment_id = ? AND invoice_id = 2033"""
    allocations = safe_query(final_db_path, allocation_query, (new_payment_id,))
    
    if not allocations:
        return {"result": "others"}
    
    # Find NEW allocation
    new_allocation_found = False
    correct_amount = False
    for allocation in allocations:
        allocation_id = allocation[0]
        allocated_amount = allocation[3]
        if allocation_id not in initial_allocation_id_set:
            new_allocation_found = True
            if abs(allocated_amount - 1070.0) < 0.01:
                correct_amount = True
                break
    
    if not new_allocation_found or not correct_amount:
        return {"result": "others"}
    
    # All checks passed
    return {"result": "complete"}