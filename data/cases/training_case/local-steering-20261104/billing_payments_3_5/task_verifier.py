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
    
    # First, get the product_id for 'API Usage Add-on'
    product_query = "SELECT id FROM products WHERE name = ?"
    product_result = safe_query(final_db_path, product_query, ('API Usage Add-on',))
    
    if not product_result:
        return {"result": "others"}
    
    product_id = product_result[0][0]
    
    # Get all pricing_plan IDs from initial database
    initial_plan_ids_query = "SELECT id FROM pricing_plans"
    initial_plan_ids = safe_query(initial_db_path, initial_plan_ids_query)
    initial_ids_set = {row[0] for row in initial_plan_ids}
    
    # Get pricing_plans from final database that match our criteria
    final_plans_query = """
        SELECT id, product_id, billing_interval, currency, unit_price, 
               billing_unit_quantity, usage_type, trial_period_days, active
        FROM pricing_plans
        WHERE product_id = ?
          AND billing_interval = ?
          AND currency = ?
          AND unit_price = ?
          AND billing_unit_quantity = ?
          AND usage_type = ?
          AND active = ?
    """
    
    final_plans = safe_query(
        final_db_path, 
        final_plans_query, 
        (product_id, 'month', 'USD', 0.02, 1000, 'metered', 1)
    )
    
    if not final_plans:
        return {"result": "others"}
    
    # Check if any of the matching plans is new (not in initial database)
    for plan in final_plans:
        plan_id = plan[0]
        trial_period_days = plan[7]
        
        # Verify this is a new plan (not in initial database)
        if plan_id not in initial_ids_set:
            # Verify trial_period_days is NULL or 0 (no trial)
            if trial_period_days is None or trial_period_days == 0:
                return {"result": "complete"}
    
    return {"result": "others"}