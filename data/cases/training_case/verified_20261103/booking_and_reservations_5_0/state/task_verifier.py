def verify_task_completion(initial_db_path: str, final_db_path: str, final_answer: str | None = None) -> dict:
    import sqlite3
    import re
    from datetime import datetime, timedelta

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

    # Get all appointment IDs from initial database
    initial_appointments = safe_query(initial_db_path, "SELECT id FROM appointments")
    initial_apt_ids = {row[0] for row in initial_appointments}

    # Get the latest timestamp from initial database to determine the "current time"
    latest_timestamps = safe_query(initial_db_path, 
        "SELECT MAX(created_at) FROM appointments UNION SELECT MAX(updated_at) FROM appointments")
    if not latest_timestamps or not latest_timestamps[0][0]:
        return {"result": "others"}
    
    try:
        current_time = datetime.fromisoformat(latest_timestamps[0][0])
    except Exception:
        return {"result": "others"}
    
    seven_days_later = current_time + timedelta(days=7)

    # Get all appointments from final database with required fields
    final_appointments = safe_query(final_db_path, 
        """SELECT a.id, a.provider_id, a.specialty_id, a.appointment_type_id, 
                  a.visit_mode, a.reason_for_visit, a.start_datetime, a.end_datetime, 
                  a.status, at.default_duration_minutes
           FROM appointments a
           JOIN appointment_types at ON a.appointment_type_id = at.id""")

    # Find new appointments (not in initial database)
    new_appointments = [apt for apt in final_appointments if apt[0] not in initial_apt_ids]

    if not new_appointments:
        return {"result": "others"}

    # Check each new appointment for matching criteria
    for apt in new_appointments:
        apt_id, provider_id, specialty_id, apt_type_id, visit_mode, reason, start_dt, end_dt, status, duration = apt

        # Check provider (Dr. Anita Rao has id=1)
        if provider_id != 1:
            continue

        # Check specialty (Cardiology has id=1)
        if specialty_id != 1:
            continue

        # Check appointment type (Standard consultation has id=1)
        if apt_type_id != 1:
            continue

        # Check visit mode (in-person)
        if visit_mode != 'in_person':
            continue

        # Check duration is 30 minutes
        if duration != 30:
            continue

        # Parse start and end datetime to verify 30-minute duration
        try:
            start_time = datetime.fromisoformat(start_dt)
            end_time = datetime.fromisoformat(end_dt)
            actual_duration = (end_time - start_time).total_seconds() / 60
            if abs(actual_duration - 30) > 1:  # Allow 1 minute tolerance
                continue
        except Exception:
            continue

        # Check start datetime is within 7 days from current time
        if start_time < current_time or start_time > seven_days_later:
            continue

        # Check reason for visit matches (case-insensitive, flexible matching)
        if not reason:
            continue
        
        reason_lower = reason.lower()
        # Check for key phrases: chest pain, intermittent, 2 weeks
        has_chest_pain = 'chest pain' in reason_lower or 'chest-pain' in reason_lower
        has_intermittent = 'intermittent' in reason_lower
        has_duration = '2 week' in reason_lower or 'two week' in reason_lower
        
        if not (has_chest_pain and has_intermittent and has_duration):
            continue

        # Check status is booked or confirmed
        if status not in ['booked', 'confirmed']:
            continue

        # Check reminder settings: both email and SMS enabled
        reminder_settings = safe_query(final_db_path,
            "SELECT send_email, send_sms FROM appointment_reminder_settings WHERE appointment_id = ?",
            (apt_id,))
        
        if not reminder_settings:
            continue
        
        send_email, send_sms = reminder_settings[0]
        if send_email != 1 or send_sms != 1:
            continue

        # All checks passed!
        return {"result": "complete"}

    # No appointment met all criteria
    return {"result": "others"}