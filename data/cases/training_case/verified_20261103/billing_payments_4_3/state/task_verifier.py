def verify_task_completion(initial_db_path: str, final_db_path: str, final_answer: str | None = None) -> dict:
    import sqlite3
    import re

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

    # Check if final_answer exists and is not empty
    if not final_answer or len(final_answer.strip()) < 20:
        return {"result": "others"}

    final_answer_lower = final_answer.lower()

    # Key check 1: Verify customer ID 'cus_123' is mentioned
    if 'cus_123' not in final_answer_lower and 'cus 123' not in final_answer_lower:
        return {"result": "others"}

    # Key check 2: Verify mention of the old plan (basic)
    has_old_plan = bool(re.search(r'plan_basic_monthly_001|basic.*monthly|current.*plan.*basic', final_answer_lower))
    if not has_old_plan:
        return {"result": "others"}

    # Key check 3: Verify mention of the new plan (pro)
    has_new_plan = bool(re.search(r'plan_pro_monthly_002|pro.*monthly|upgrade.*pro|new.*plan.*pro', final_answer_lower))
    if not has_new_plan:
        return {"result": "others"}

    # Key check 4: Check for proration-related terms
    has_proration = bool(re.search(r'prorat|always_invoice|immediate|credit|prorate', final_answer_lower))
    if not has_proration:
        return {"result": "others"}

    # Key check 5: Verify presence of monetary amounts (dollar signs, cents, or numeric amounts)
    has_amounts = bool(re.search(r'\$[\d,]+\.?\d*|\d+\s*(cents|usd)|amount.*\d+|total.*\d+|subtotal.*\d+', final_answer_lower))
    if not has_amounts:
        return {"result": "others"}

    # Key check 6: Check for invoice/preview terminology
    has_invoice_preview = bool(re.search(r'invoice|preview|upcoming|estimate|bill', final_answer_lower))
    if not has_invoice_preview:
        return {"result": "others"}

    # Key check 7: Ensure no new invoices were created (this is a preview, not actual invoice creation)
    initial_invoices = safe_query(initial_db_path, "SELECT id FROM invoices WHERE customer_id = ?", ('cus_123',))
    final_invoices = safe_query(final_db_path, "SELECT id FROM invoices WHERE customer_id = ?", ('cus_123',))
    
    # Allow for preview invoices marked with upcoming_preview=1, but no new finalized invoices
    initial_finalized = safe_query(initial_db_path, "SELECT id FROM invoices WHERE customer_id = ? AND (finalized_at IS NOT NULL OR upcoming_preview = 0)", ('cus_123',))
    final_finalized = safe_query(final_db_path, "SELECT id FROM invoices WHERE customer_id = ? AND (finalized_at IS NOT NULL OR upcoming_preview = 0)", ('cus_123',))
    
    if len(final_finalized) > len(initial_finalized):
        # New finalized invoice was created, this is not just a preview
        return {"result": "others"}

    # Key check 8: Verify subscription remains unchanged (no actual upgrade was applied)
    initial_sub = safe_query(initial_db_path, "SELECT si.pricing_plan_id FROM subscriptions s JOIN subscription_items si ON s.id = si.subscription_id WHERE s.customer_id = ? AND s.id = 'sub_basic_123'", ('cus_123',))
    final_sub = safe_query(final_db_path, "SELECT si.pricing_plan_id FROM subscriptions s JOIN subscription_items si ON s.id = si.subscription_id WHERE s.customer_id = ? AND s.id = 'sub_basic_123'", ('cus_123',))
    
    if initial_sub and final_sub:
        if initial_sub[0][0] != final_sub[0][0]:
            # Subscription plan changed, this was an actual upgrade not just a preview
            return {"result": "others"}

    # All checks passed - the agent successfully previewed the upgrade invoice
    return {"result": "complete"}