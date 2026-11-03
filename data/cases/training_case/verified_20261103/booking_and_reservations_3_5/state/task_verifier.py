def verify_task_completion(initial_db_path: str, final_db_path: str, final_answer: str | None = None) -> dict:
    import sqlite3
    import re
    from datetime import datetime

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

    # If no final_answer provided, cannot verify
    if not final_answer:
        return {"result": "others"}

    # Step 1: Determine the current active shift
    # We need to check which shift is currently active based on timestamp
    # From the database dump, the shifts are:
    # Shift 1: Brunch 2025-12-30 10:00-14:00
    # Shift 2: Dinner 2025-12-31 17:00-22:00 (this appears to be active based on snapshots)
    # Shift 3: Dinner 2025-12-30 18:00-23:00
    # Shift 4: Brunch 2025-12-29 10:00-14:00
    
    # Query all shifts to find which one is active
    shifts_query = """
        SELECT id, name, business_date, start_time, end_time 
        FROM shifts 
        ORDER BY start_time DESC
    """
    shifts = safe_query(final_db_path, shifts_query)
    
    if not shifts:
        return {"result": "others"}
    
    # Since we don't have actual current time in the verification context,
    # we need to infer the active shift based on the most recent snapshot
    # or the shift with the most recent activity
    
    # Query for the most recent snapshot to determine active shift
    recent_snapshot_query = """
        SELECT shift_id, dining_area_id, snapshot_time
        FROM table_status_snapshots
        ORDER BY snapshot_time DESC
        LIMIT 1
    """
    recent_snapshot = safe_query(final_db_path, recent_snapshot_query)
    
    if not recent_snapshot:
        return {"result": "others"}
    
    active_shift_id = recent_snapshot[0][0]
    
    # Step 2: Get the Bar dining area ID
    bar_area_query = "SELECT id FROM dining_areas WHERE name = 'Bar'"
    bar_area = safe_query(final_db_path, bar_area_query)
    
    if not bar_area:
        return {"result": "others"}
    
    bar_area_id = bar_area[0][0]
    
    # Step 3: Get the snapshot for the active shift and Bar area
    snapshot_query = """
        SELECT id 
        FROM table_status_snapshots 
        WHERE shift_id = ? AND dining_area_id = ?
        ORDER BY snapshot_time DESC
        LIMIT 1
    """
    snapshot = safe_query(final_db_path, snapshot_query, (active_shift_id, bar_area_id))
    
    if not snapshot:
        return {"result": "others"}
    
    snapshot_id = snapshot[0][0]
    
    # Step 4: Query for vacant tables in Bar with capacity >= 2 and mergeable_flag = true
    expected_tables_query = """
        SELECT t.table_code, t.capacity, t.mergeable_flag
        FROM table_status_snapshot_items tssi
        JOIN tables t ON tssi.table_id = t.id
        WHERE tssi.snapshot_id = ?
        AND tssi.status = 'vacant'
        AND t.dining_area_id = ?
        AND t.capacity >= 2
        AND t.mergeable_flag = 1
        ORDER BY t.table_code
    """
    expected_tables = safe_query(final_db_path, expected_tables_query, (snapshot_id, bar_area_id))
    
    if not expected_tables:
        # No tables match criteria - check if answer reflects this
        if re.search(r'(no tables|empty|none|0 tables)', final_answer, re.IGNORECASE):
            return {"result": "complete"}
        return {"result": "others"}
    
    # Extract expected table codes
    expected_codes = [table[0] for table in expected_tables]
    
    # Step 5: Extract table codes from final_answer
    # Look for patterns like B-01, B-02, etc.
    found_codes = re.findall(r'B-\d+', final_answer)
    
    # Also try to find table codes in various formats
    if not found_codes:
        found_codes = re.findall(r'["\']?([A-Z]-\d+)["\']?', final_answer)
    
    # Normalize found codes
    found_codes = list(set(found_codes))
    found_codes.sort()
    expected_codes.sort()
    
    # Step 6: Verify that found codes match expected codes exactly
    if found_codes == expected_codes and len(expected_codes) > 0:
        # Additional check: ensure the answer mentions key criteria
        has_criteria = (
            re.search(r'vacant', final_answer, re.IGNORECASE) and
            re.search(r'bar', final_answer, re.IGNORECASE) and
            (re.search(r'capacity.*2|2.*capacity', final_answer, re.IGNORECASE) or 
             re.search(r'>=\s*2|≥\s*2', final_answer)) and
            re.search(r'mergeable', final_answer, re.IGNORECASE)
        )
        
        if has_criteria:
            return {"result": "complete"}
    
    # Alternative check: verify all expected codes are mentioned
    all_found = all(code in final_answer for code in expected_codes)
    no_extra = all(code in expected_codes for code in found_codes) if found_codes else True
    
    if all_found and no_extra and len(expected_codes) > 0:
        return {"result": "complete"}
    
    return {"result": "others"}