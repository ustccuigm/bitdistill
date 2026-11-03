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

    # Step 1: Get the resource_type_id for 'Company Pool Car'
    resource_type_query = "SELECT id FROM resource_types WHERE name = ?"
    resource_type_result = safe_query(final_db_path, resource_type_query, ('Company Pool Car',))
    
    if not resource_type_result:
        return {"result": "others"}
    
    resource_type_id = resource_type_result[0][0]

    # Step 2: Get the booking_policy_id for this resource_type
    # Check if there's a policy that applies_to='resource_type' for Company Pool Car
    policy_query = """
        SELECT bp.id, bp.max_duration_minutes, bp.cancellation_window_minutes, bp.applies_to
        FROM booking_policies bp
        WHERE bp.applies_to = 'resource_type'
        AND bp.id IN (
            SELECT DISTINCT booking_policy_id 
            FROM resources 
            WHERE resource_type_id = ? AND booking_policy_id IS NOT NULL
        )
    """
    policy_result = safe_query(final_db_path, policy_query, (resource_type_id,))
    
    # If no policy found via resources, check if there's a general policy for this resource type
    # by checking resource_type_permissions
    if not policy_result:
        # Try to find policy that is linked to resource_type through resource_type_permissions
        alt_policy_query = """
            SELECT DISTINCT bp.id, bp.max_duration_minutes, bp.cancellation_window_minutes, bp.applies_to
            FROM booking_policies bp
            JOIN booking_policy_permissions bpp ON bp.id = bpp.booking_policy_id
            JOIN resource_type_permissions rtp ON bpp.permission_id = rtp.permission_id
            WHERE rtp.resource_type_id = ? AND bp.applies_to = 'resource_type'
        """
        policy_result = safe_query(final_db_path, alt_policy_query, (resource_type_id,))
    
    if not policy_result:
        return {"result": "others"}
    
    # We should have exactly one policy for this resource type
    policy_id, max_duration, cancellation_window, applies_to = policy_result[0]
    
    # Step 3: Verify max_duration_minutes = 480 (8 hours)
    if max_duration != 480:
        return {"result": "others"}
    
    # Step 4: Verify cancellation_window_minutes = 120 (2 hours)
    if cancellation_window != 120:
        return {"result": "others"}
    
    # Step 5: Verify booking_policy_permissions has ONLY field_sales permission
    permission_query = """
        SELECT p.code 
        FROM booking_policy_permissions bpp
        JOIN permissions p ON bpp.permission_id = p.id
        WHERE bpp.booking_policy_id = ?
    """
    permission_result = safe_query(final_db_path, permission_query, (policy_id,))
    
    if not permission_result:
        return {"result": "others"}
    
    # Extract permission codes
    permission_codes = [row[0] for row in permission_result]
    
    # Must have exactly 'field_sales' permission and no others
    if len(permission_codes) != 1 or permission_codes[0] != 'field_sales':
        return {"result": "others"}
    
    # All checks passed
    return {"result": "complete"}