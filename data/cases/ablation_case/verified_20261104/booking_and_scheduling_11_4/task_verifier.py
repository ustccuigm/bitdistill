def verify_task_completion(initial_db_path: str, final_db_path: str, final_answer: str | None = None) -> dict:
    import sqlite3
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

    # Step 1: Verify appointment slots configuration
    slots_query = """
        SELECT id, provider_id, clinic_id, visit_type_id, start_datetime, end_datetime,
               capacity_per_slot, base_capacity_per_slot, is_overbook_capable
        FROM appointment_slots
        WHERE provider_id = 'PROV-3344'
          AND clinic_id = 'CLIN-01'
          AND date(start_datetime) = '2026-02-03'
          AND time(start_datetime) >= '08:00:00'
          AND time(end_datetime) <= '09:00:00'
        ORDER BY start_datetime
    """
    
    final_slots = safe_query(final_db_path, slots_query)
    
    # Should have exactly 4 slots (08:00-08:15, 08:15-08:30, 08:30-08:45, 08:45-09:00)
    if len(final_slots) != 4:
        return {"result": "others"}
    
    # Verify each slot has correct configuration
    expected_times = [
        ('2026-02-03 08:00:00', '2026-02-03 08:15:00'),
        ('2026-02-03 08:15:00', '2026-02-03 08:30:00'),
        ('2026-02-03 08:30:00', '2026-02-03 08:45:00'),
        ('2026-02-03 08:45:00', '2026-02-03 09:00:00')
    ]
    
    slot_ids = []
    for i, slot in enumerate(final_slots):
        slot_id, provider_id, clinic_id, visit_type_id, start_dt, end_dt, capacity, base_capacity, is_overbook = slot
        
        # Verify basic attributes
        if provider_id != 'PROV-3344' or clinic_id != 'CLIN-01':
            return {"result": "others"}
        
        # Verify visit_type_id is 4 (Same-day Sick Visit)
        if visit_type_id != 4:
            return {"result": "others"}
        
        # Verify times match expected 15-minute intervals
        if (start_dt, end_dt) != expected_times[i]:
            return {"result": "others"}
        
        # Verify capacity configuration for overbooked slots
        if capacity != 3 or base_capacity != 2 or is_overbook != 1:
            return {"result": "others"}
        
        slot_ids.append(slot_id)
    
    # Step 2: Verify patient Maria Lopez exists with correct DOB
    patient_query = """
        SELECT id, full_name, date_of_birth
        FROM patients
        WHERE full_name = 'Maria Lopez' AND date_of_birth = '2012-09-03'
    """
    
    final_patient = safe_query(final_db_path, patient_query)
    if len(final_patient) != 1:
        return {"result": "others"}
    
    patient_id = final_patient[0][0]
    if patient_id != 2:
        return {"result": "others"}
    
    # Step 3: Get bookings for Maria Lopez in initial and final databases
    booking_query = """
        SELECT id, appointment_slot_id, patient_id, visit_type_id, status, is_same_day_booking
        FROM bookings
        WHERE patient_id = 2
    """
    
    initial_bookings = safe_query(initial_db_path, booking_query)
    final_bookings = safe_query(final_db_path, booking_query)
    
    # Should have exactly one more booking in final than initial
    if len(final_bookings) != len(initial_bookings) + 1:
        return {"result": "others"}
    
    # Find the new booking (not in initial)
    initial_booking_ids = {b[0] for b in initial_bookings}
    new_bookings = [b for b in final_bookings if b[0] not in initial_booking_ids]
    
    if len(new_bookings) != 1:
        return {"result": "others"}
    
    new_booking = new_bookings[0]
    booking_id, slot_id, pat_id, visit_type, status, is_same_day = new_booking
    
    # Verify the new booking attributes
    if pat_id != 2:
        return {"result": "others"}
    
    if visit_type != 4:
        return {"result": "others"}
    
    if status != 'scheduled':
        return {"result": "others"}
    
    if is_same_day != 1:
        return {"result": "others"}
    
    # Verify the booking is linked to one of the PROV-3344 slots on 2026-02-03 08:00-09:00
    if slot_id not in slot_ids:
        return {"result": "others"}
    
    # All checks passed
    return {"result": "complete"}