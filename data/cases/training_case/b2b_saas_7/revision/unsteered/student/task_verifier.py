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
    
    # First verify the entities exist
    location_check = safe_query(final_db_path, "SELECT id FROM locations WHERE name = ?", ("Midtown Cloud Kitchen",))
    if not location_check or location_check[0][0] != 3:
        return {"result": "others"}
    
    menu_check = safe_query(final_db_path, "SELECT id FROM menus WHERE name = ?", ("Ghost Kitchen Late Night",))
    if not menu_check or menu_check[0][0] != 4:
        return {"result": "others"}
    
    kimchi_check = safe_query(final_db_path, "SELECT id FROM menu_items WHERE internal_name = ?", ("loaded_kimchi_fries",))
    if not kimchi_check or kimchi_check[0][0] != 6:
        return {"result": "others"}
    
    nachos_check = safe_query(final_db_path, "SELECT id FROM menu_items WHERE internal_name = ?", ("classic_nachos",))
    if not nachos_check or nachos_check[0][0] != 7:
        return {"result": "others"}
    
    # Check if version 3 existed in initial database
    initial_version = safe_query(initial_db_path, 
        "SELECT id, version_number, is_published, audit_note FROM location_menu_versions WHERE location_id = ? AND menu_id = ? AND version_number = ?",
        (3, 4, 3))
    
    if initial_version:
        # Version 3 already existed, task was not completed by the agent
        return {"result": "others"}
    
    # Check if version 3 exists in final database with correct attributes
    final_version = safe_query(final_db_path,
        "SELECT id, version_number, is_published, audit_note FROM location_menu_versions WHERE location_id = ? AND menu_id = ? AND version_number = ?",
        (3, 4, 3))
    
    if not final_version:
        return {"result": "others"}
    
    version_id, version_number, is_published, audit_note = final_version[0]
    
    # Verify version is published
    if is_published != 1:
        return {"result": "others"}
    
    # Verify exact audit note
    expected_audit_note = "Shifted to Korean-inspired snacks based on sales data"
    if audit_note != expected_audit_note:
        return {"result": "others"}
    
    # Check that Loaded Kimchi Fries was NOT in version 3 initially
    initial_kimchi = safe_query(initial_db_path,
        "SELECT id, is_published FROM location_menu_items WHERE location_id = ? AND menu_item_id = ? AND menu_version_id = ?",
        (3, 6, version_id))
    
    if initial_kimchi:
        # Already existed, not added by agent
        return {"result": "others"}
    
    # Check that Loaded Kimchi Fries is now in version 3 and published
    final_kimchi = safe_query(final_db_path,
        "SELECT id, is_published FROM location_menu_items WHERE location_id = ? AND menu_item_id = ? AND menu_version_id = ?",
        (3, 6, version_id))
    
    if not final_kimchi or final_kimchi[0][1] != 1:
        return {"result": "others"}
    
    # Check Classic Nachos state in version 3
    # First check if it existed in initial database
    initial_nachos = safe_query(initial_db_path,
        "SELECT id, is_published FROM location_menu_items WHERE location_id = ? AND menu_item_id = ? AND menu_version_id = ?",
        (3, 7, version_id))
    
    # Check Classic Nachos in final database - should be unpublished
    final_nachos = safe_query(final_db_path,
        "SELECT id, is_published FROM location_menu_items WHERE location_id = ? AND menu_item_id = ? AND menu_version_id = ?",
        (3, 7, version_id))
    
    if not final_nachos or final_nachos[0][1] != 0:
        return {"result": "others"}
    
    # If we reached here, all checks passed
    return {"result": "complete"}
