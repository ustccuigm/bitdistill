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

    # Get Luna's pet_id
    luna_query = "SELECT id FROM pets WHERE name = 'Luna'"
    luna_results = safe_query(final_db_path, luna_query)
    if not luna_results:
        return {"result": "others"}
    luna_pet_id = luna_results[0][0]

    # Get initial vaccination count for Luna
    initial_vacc_query = "SELECT COUNT(*) FROM vaccinations WHERE pet_id = ?"
    initial_count = safe_query(initial_db_path, initial_vacc_query, (luna_pet_id,))
    if not initial_count:
        return {"result": "others"}
    initial_vacc_count = initial_count[0][0]

    # Get final vaccination count for Luna
    final_count = safe_query(final_db_path, initial_vacc_query, (luna_pet_id,))
    if not final_count:
        return {"result": "others"}
    final_vacc_count = final_count[0][0]

    # Check if a new vaccination was added
    if final_vacc_count <= initial_vacc_count:
        return {"result": "others"}

    # Get medical_record_id for appointment 'APT-98342'
    medical_record_query = "SELECT id FROM medical_records WHERE appointment_id = 'APT-98342'"
    medical_record_results = safe_query(final_db_path, medical_record_query)
    if not medical_record_results:
        return {"result": "others"}
    
    valid_medical_record_ids = [row[0] for row in medical_record_results]

    # Query for the new vaccination with exact specifications
    vaccination_query = """
        SELECT id, pet_id, medical_record_id, vaccine_type, dose, administration_date, next_due_date
        FROM vaccinations
        WHERE pet_id = ?
        AND vaccine_type = 'Rabies 1-year'
        AND dose = '1.0 mL subcutaneous'
        AND administration_date = '2025-01-12'
        AND next_due_date = '2026-01-12'
    """
    
    new_vaccinations = safe_query(final_db_path, vaccination_query, (luna_pet_id,))
    
    if not new_vaccinations:
        return {"result": "others"}

    # Check if any of the matching vaccinations are linked to the correct medical_record
    for vacc in new_vaccinations:
        vacc_id, pet_id, medical_record_id, vaccine_type, dose, admin_date, next_due = vacc
        
        # Verify medical_record_id is not None and is in the valid list
        if medical_record_id is not None and medical_record_id in valid_medical_record_ids:
            # Verify all fields match exactly
            if (pet_id == luna_pet_id and
                vaccine_type == 'Rabies 1-year' and
                dose == '1.0 mL subcutaneous' and
                admin_date == '2025-01-12' and
                next_due == '2026-01-12'):
                
                # Verify this vaccination didn't exist in initial database
                check_initial = safe_query(initial_db_path, "SELECT id FROM vaccinations WHERE id = ?", (vacc_id,))
                if not check_initial:
                    return {"result": "complete"}

    return {"result": "others"}