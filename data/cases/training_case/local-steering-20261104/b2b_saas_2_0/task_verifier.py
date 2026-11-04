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
    
    # Get initial max property ID to identify new properties
    initial_properties = safe_query(initial_db_path, "SELECT id FROM properties ORDER BY id DESC LIMIT 1")
    if not initial_properties:
        max_initial_property_id = 0
    else:
        max_initial_property_id = initial_properties[0][0]
    
    # Find new property at 120 Market Street, Sydney NSW 2000
    new_properties = safe_query(
        final_db_path,
        "SELECT id, property_type FROM properties WHERE id > ? AND address_line = ? AND city = ? AND state = ? AND postal_code = ?",
        (max_initial_property_id, '120 Market Street', 'Sydney', 'NSW', '2000')
    )
    
    if not new_properties or len(new_properties) != 1:
        return {"result": "others"}
    
    new_property_id, property_type = new_properties[0]
    
    # Verify property type is office
    if property_type != 'office':
        return {"result": "others"}
    
    # Verify the new property has exactly 3 key features
    features = safe_query(
        final_db_path,
        "SELECT feature FROM property_features WHERE property_id = ? ORDER BY feature",
        (new_property_id,)
    )
    
    if len(features) != 3:
        return {"result": "others"}
    
    # Extract feature strings and check they match required features
    feature_list = [f[0] for f in features]
    required_features = ['A-grade office tower', 'End-of-trip facilities', 'On-site parking']
    required_features_sorted = sorted(required_features)
    feature_list_sorted = sorted(feature_list)
    
    if feature_list_sorted != required_features_sorted:
        return {"result": "others"}
    
    # Verify 3 units were added for the new property
    units = safe_query(
        final_db_path,
        "SELECT unit_name, floor_number, floor_area_sqm, fitout_type, occupancy_status FROM units WHERE property_id = ? ORDER BY unit_name",
        (new_property_id,)
    )
    
    if len(units) != 3:
        return {"result": "others"}
    
    # Define expected units (sorted by unit_name)
    expected_units = [
        ('Unit 501', 5, 750.0, 'open plan', 'vacant'),
        ('Unit 502', 5, 600.0, 'spec fitout', 'occupied'),
        ('Unit 601', 6, 800.0, 'shell', 'vacant')
    ]
    
    # Verify each unit matches expectations
    for i, (unit_name, floor_number, floor_area, fitout_type, occupancy_status) in enumerate(units):
        expected = expected_units[i]
        
        if unit_name != expected[0]:
            return {"result": "others"}
        
        if floor_number != expected[1]:
            return {"result": "others"}
        
        # Check floor area with tolerance for floating point comparison
        if abs(floor_area - expected[2]) > 0.01:
            return {"result": "others"}
        
        if fitout_type != expected[3]:
            return {"result": "others"}
        
        if occupancy_status != expected[4]:
            return {"result": "others"}
    
    # All checks passed
    return {"result": "complete"}