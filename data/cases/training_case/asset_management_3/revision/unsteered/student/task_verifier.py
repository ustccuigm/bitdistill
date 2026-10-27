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
    
    # Get asset_id for PRJ-DRN-003
    asset_query = "SELECT id, location_id FROM assets WHERE asset_tag = ?"
    initial_asset = safe_query(initial_db_path, asset_query, ('PRJ-DRN-003',))
    final_asset = safe_query(final_db_path, asset_query, ('PRJ-DRN-003',))
    
    if not initial_asset or not final_asset:
        return {"result": "others"}
    
    asset_id = final_asset[0][0]
    initial_location_id = initial_asset[0][1]
    final_location_id = final_asset[0][1]
    
    # Get custodian_id for Maria Lopez (Engineering)
    custodian_query = "SELECT id FROM custodians WHERE name = ?"
    custodian_result = safe_query(final_db_path, custodian_query, ('Maria Lopez (Engineering)',))
    
    if not custodian_result:
        return {"result": "others"}
    
    custodian_id = custodian_result[0][0]
    
    # Get location_id for Prototype Lab
    location_query = "SELECT id FROM locations WHERE full_path = ?"
    location_result = safe_query(final_db_path, location_query, ('HQ > 4th Floor > Prototype Lab',))
    
    if not location_result:
        return {"result": "others"}
    
    expected_location_id = location_result[0][0]
    
    # Check 1: Verify location was updated to Prototype Lab (location_id=8)
    if final_location_id != expected_location_id:
        return {"result": "others"}
    
    # Check 2: Get checkout records for this asset in initial state
    initial_checkouts_query = "SELECT id, custodian_id, checkout_date, expected_return_date, actual_return_date FROM asset_checkouts WHERE asset_id = ?"
    initial_checkouts = safe_query(initial_db_path, initial_checkouts_query, (asset_id,))
    final_checkouts = safe_query(final_db_path, initial_checkouts_query, (asset_id,))
    
    # Check 3: Verify a new checkout record was created
    if len(final_checkouts) <= len(initial_checkouts):
        return {"result": "others"}
    
    # Check 4: Find the new checkout record with the specific criteria
    new_checkout_found = False
    for checkout in final_checkouts:
        checkout_id, cust_id, checkout_date, expected_return, actual_return = checkout
        
        # Check if this checkout matches our requirements
        if (cust_id == custodian_id and 
            checkout_date == '2025-01-02' and 
            expected_return == '2025-03-31' and 
            actual_return is None):
            new_checkout_found = True
            break
    
    if not new_checkout_found:
        return {"result": "others"}
    
    # All checks passed
    return {"result": "complete"}
