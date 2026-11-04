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

    # Get Maria Gonzalez traveler_id
    traveler_check = safe_query(final_db_path, "SELECT id FROM travelers WHERE first_name = 'Maria' AND last_name = 'Gonzalez'", ())
    if not traveler_check:
        return {"result": "others"}
    maria_id = traveler_check[0][0]

    # Get all trip IDs from initial database
    initial_trip_ids = set([row[0] for row in safe_query(initial_db_path, "SELECT id FROM trips", ())])
    
    # Get all trip IDs from final database
    final_trip_ids = set([row[0] for row in safe_query(final_db_path, "SELECT id FROM trips", ())])
    
    # Find NEW trip IDs
    new_trip_ids = final_trip_ids - initial_trip_ids
    
    if not new_trip_ids:
        return {"result": "others"}
    
    # Check each new trip to see if it matches the requirements
    for trip_id in new_trip_ids:
        # Check trip details
        trip_query = "SELECT status, purpose, cost_center, primary_traveler_id FROM trips WHERE id = ?"
        trip_data = safe_query(final_db_path, trip_query, (trip_id,))
        
        if not trip_data:
            continue
            
        status, purpose, cost_center, primary_traveler_id = trip_data[0]
        
        # Verify trip attributes
        if status != 'draft':
            continue
        if not purpose or 'Client meeting at Seattle HQ' not in purpose:
            continue
        if cost_center != 'SALES-NW':
            continue
        if primary_traveler_id != maria_id:
            continue
        
        # Check flight segments
        flight_query = "SELECT from_airport, to_airport, departure_date, departure_time_from, return_segment, cabin_class FROM flight_segments WHERE trip_id = ?"
        flights = safe_query(final_db_path, flight_query, (trip_id,))
        
        if len(flights) != 2:
            continue
        
        # Validate outbound flight: SFO->SEA on 2025-02-10 after 08:00, Economy
        outbound = [f for f in flights if f[4] == 0]  # return_segment = 0
        inbound = [f for f in flights if f[4] == 1]   # return_segment = 1
        
        if len(outbound) != 1 or len(inbound) != 1:
            continue
        
        out_from, out_to, out_date, out_time, _, out_cabin = outbound[0]
        in_from, in_to, in_date, in_time, _, in_cabin = inbound[0]
        
        # Check outbound: SFO->SEA on 2025-02-10 after 08:00
        if out_from != 'SFO' or out_to != 'SEA':
            continue
        if out_date != '2025-02-10':
            continue
        if not out_time or out_time < '08:00':
            continue
        if out_cabin != 'Economy':
            continue
        
        # Check inbound: SEA->SFO on 2025-02-12 after 17:00
        if in_from != 'SEA' or in_to != 'SFO':
            continue
        if in_date != '2025-02-12':
            continue
        if not in_time or in_time < '17:00':
            continue
        if in_cabin != 'Economy':
            continue
        
        # Check hotel booking
        hotel_query = "SELECT city, check_in_date, check_out_date, nightly_rate FROM hotel_bookings WHERE trip_id = ?"
        hotels = safe_query(final_db_path, hotel_query, (trip_id,))
        
        if len(hotels) != 1:
            continue
        
        city, check_in, check_out, nightly_rate = hotels[0]
        
        # Verify hotel is in Seattle (case insensitive)
        if not city or 'seattle' not in city.lower():
            continue
        if check_in != '2025-02-10':
            continue
        if check_out != '2025-02-12':
            continue
        # Verify nightly rate is under 220 USD (or None for planned)
        if nightly_rate is not None and nightly_rate >= 220.0:
            continue
        
        # All checks passed for this trip
        return {"result": "complete"}
    
    # No new trip matched all requirements
    return {"result": "others"}