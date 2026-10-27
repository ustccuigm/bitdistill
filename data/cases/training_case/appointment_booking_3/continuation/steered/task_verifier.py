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
    
    # Step 1: Find 'Deep Tissue Massage' service in Massage category with correct specs
    service_query = """
        SELECT s.id, s.name, s.service_category_id, s.default_duration_minutes, s.base_price
        FROM services s
        JOIN service_categories sc ON s.service_category_id = sc.id
        WHERE s.name = 'Deep Tissue Massage' 
        AND sc.name = 'Massage'
        AND s.default_duration_minutes = 60
        AND s.base_price = 120.0
    """
    
    final_services = safe_query(final_db_path, service_query)
    if not final_services:
        return {"result": "others"}
    
    service_id = final_services[0][0]
    
    # Step 2: Verify service is associated with Downtown Spa (location_id=1)
    location_service_query = """
        SELECT ls.id
        FROM location_services ls
        JOIN locations l ON ls.location_id = l.id
        WHERE ls.service_id = ?
        AND l.name = 'Downtown Spa'
        AND ls.is_active = 1
    """
    
    final_location_services = safe_query(final_db_path, location_service_query, (service_id,))
    initial_location_services = safe_query(initial_db_path, location_service_query, (service_id,))
    
    if not final_location_services:
        return {"result": "others"}
    
    # Step 3: Verify service requires 'Massage Room' resource
    required_resource_query = """
        SELECT srr.id
        FROM service_required_resources srr
        JOIN resource_types rt ON srr.resource_type_id = rt.id
        WHERE srr.service_id = ?
        AND rt.name = 'Massage Room'
        AND srr.quantity = 1
    """
    
    final_required_resources = safe_query(final_db_path, required_resource_query, (service_id,))
    initial_required_resources = safe_query(initial_db_path, required_resource_query, (service_id,))
    
    if not final_required_resources:
        return {"result": "others"}
    
    # Step 4: Verify 'Aromatherapy Upgrade' add-on (id=1, price=20)
    aromatherapy_query = """
        SELECT sao.id
        FROM service_add_on_options sao
        JOIN add_on_options ao ON sao.add_on_option_id = ao.id
        WHERE sao.service_id = ?
        AND ao.name = 'Aromatherapy Upgrade'
        AND ao.price = 20.0
        AND sao.is_active = 1
    """
    
    final_aromatherapy = safe_query(final_db_path, aromatherapy_query, (service_id,))
    initial_aromatherapy = safe_query(initial_db_path, aromatherapy_query, (service_id,))
    
    if not final_aromatherapy:
        return {"result": "others"}
    
    # Step 5: Verify 'Extended 15 Minutes' add-on (id=2, price=30)
    extended_query = """
        SELECT sao.id
        FROM service_add_on_options sao
        JOIN add_on_options ao ON sao.add_on_option_id = ao.id
        WHERE sao.service_id = ?
        AND ao.name = 'Extended 15 Minutes'
        AND ao.price = 30.0
        AND sao.is_active = 1
    """
    
    final_extended = safe_query(final_db_path, extended_query, (service_id,))
    initial_extended = safe_query(initial_db_path, extended_query, (service_id,))
    
    if not final_extended:
        return {"result": "others"}
    
    # Step 6: Verify at least one of these relationships was newly created
    # (This ensures the agent actually did something, not just that the data already existed)
    changes_made = (
        len(final_location_services) > len(initial_location_services) or
        len(final_required_resources) > len(initial_required_resources) or
        len(final_aromatherapy) > len(initial_aromatherapy) or
        len(final_extended) > len(initial_extended)
    )
    
    if not changes_made:
        # Check if service itself is new
        initial_services = safe_query(initial_db_path, service_query)
        if len(final_services) <= len(initial_services):
            # No new service and no new relationships - nothing was done
            return {"result": "others"}
    
    # All conditions met
    return {"result": "complete"}
