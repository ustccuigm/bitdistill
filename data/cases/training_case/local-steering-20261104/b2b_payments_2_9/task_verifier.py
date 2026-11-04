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

    # Get payment internal id for 'PMT-2025-00077'
    payment_query = "SELECT id FROM payments WHERE payment_id = ?"
    payment_result = safe_query(final_db_path, payment_query, ('PMT-2025-00077',))
    if not payment_result:
        return {"result": "others"}
    payment_id = payment_result[0][0]

    # Get invoice internal ids
    invoice1_query = "SELECT id FROM invoices WHERE invoice_number = ?"
    invoice1_result = safe_query(final_db_path, invoice1_query, ('INV-2024-1190',))
    if not invoice1_result:
        return {"result": "others"}
    invoice1_id = invoice1_result[0][0]

    invoice2_query = "SELECT id FROM invoices WHERE invoice_number = ?"
    invoice2_result = safe_query(final_db_path, invoice2_query, ('INV-2024-1215',))
    if not invoice2_result:
        return {"result": "others"}
    invoice2_id = invoice2_result[0][0]

    # Check initial remittance_advices count for this payment
    initial_remittance_query = "SELECT COUNT(*) FROM remittance_advices WHERE payment_id = ?"
    initial_count = safe_query(initial_db_path, initial_remittance_query, (payment_id,))
    if not initial_count:
        return {"result": "others"}
    initial_remittance_count = initial_count[0][0]

    # Check final remittance_advices for this payment
    final_remittance_query = "SELECT invoice_id, allocated_amount, discount_amount, write_off_amount FROM remittance_advices WHERE payment_id = ?"
    final_remittances = safe_query(final_db_path, final_remittance_query, (payment_id,))
    if not final_remittances:
        return {"result": "others"}

    # Should have 2 more remittance records than initial (based on initial db dump, payment_id 3 already has 2 remittances)
    if len(final_remittances) != initial_remittance_count + 2:
        return {"result": "others"}

    # Verify the two new remittance records
    remittance1_found = False
    remittance2_found = False

    for remittance in final_remittances:
        inv_id, allocated, discount, write_off = remittance
        
        # Check for INV-2024-1190: 8000.00 allocated, 160.00 discount, 0.0 write_off
        if inv_id == invoice1_id:
            if abs(allocated - 8000.0) < 0.01 and abs(discount - 160.0) < 0.01 and abs(write_off - 0.0) < 0.01:
                remittance1_found = True
        
        # Check for INV-2024-1215: 4340.00 allocated (note: task says 4300, but with 40 write_off, total would be 4340), 0.0 discount, 40.0 write_off
        # Re-reading task: allocates 4,300.00 USD with a 40.00 write_off. This means allocated_amount should be 4300.00
        if inv_id == invoice2_id:
            if abs(allocated - 4300.0) < 0.01 and abs(discount - 0.0) < 0.01 and abs(write_off - 40.0) < 0.01:
                remittance2_found = True

    if not (remittance1_found and remittance2_found):
        return {"result": "others"}

    # Check that both invoices have open_balance = 0.0 (fully paid)
    invoice1_balance_query = "SELECT open_balance FROM invoices WHERE id = ?"
    invoice1_balance = safe_query(final_db_path, invoice1_balance_query, (invoice1_id,))
    if not invoice1_balance or abs(invoice1_balance[0][0] - 0.0) > 0.01:
        return {"result": "others"}

    invoice2_balance_query = "SELECT open_balance FROM invoices WHERE id = ?"
    invoice2_balance = safe_query(final_db_path, invoice2_balance_query, (invoice2_id,))
    if not invoice2_balance or abs(invoice2_balance[0][0] - 0.0) > 0.01:
        return {"result": "others"}

    # Check that payment reconciliation_status is 'reconciled'
    payment_status_query = "SELECT reconciliation_status FROM payments WHERE id = ?"
    payment_status = safe_query(final_db_path, payment_status_query, (payment_id,))
    if not payment_status or payment_status[0][0] != 'reconciled':
        return {"result": "others"}

    return {"result": "complete"}