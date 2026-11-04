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

    # Get asset_id for CAM-NYC-0007
    asset_query = "SELECT id FROM assets WHERE asset_tag = ?"
    asset_result = safe_query(final_db_path, asset_query, ('CAM-NYC-0007',))
    if not asset_result:
        return {"result": "others"}
    asset_id = asset_result[0][0]

    # Get user_id for jane.smith@company.com
    user_query = "SELECT id FROM users WHERE email = ?"
    user_result = safe_query(final_db_path, user_query, ('jane.smith@company.com',))
    if not user_result:
        return {"result": "others"}
    user_id = user_result[0][0]

    # Get location_id for NYC Office > Media Closet
    location_query = "SELECT id FROM locations WHERE full_path = ?"
    location_result = safe_query(final_db_path, location_query, ('NYC Office > Media Closet',))
    if not location_result:
        return {"result": "others"}
    location_id = location_result[0][0]

    # Get initial checkouts for this asset/user combination
    initial_checkouts_query = """SELECT id, asset_id, user_id, project_name, checkout_location_id, 
                                         due_date, checked_in_at, note 
                                  FROM asset_checkouts 
                                  WHERE asset_id = ? AND user_id = ? AND checked_in_at IS NULL"""
    initial_checkouts = safe_query(initial_db_path, initial_checkouts_query, (asset_id, user_id))
    initial_checkout_ids = {row[0] for row in initial_checkouts}

    # Get final checkouts for this asset/user combination
    final_checkouts = safe_query(final_db_path, initial_checkouts_query, (asset_id, user_id))

    # Find new checkouts (present in final but not in initial)
    new_checkouts = [row for row in final_checkouts if row[0] not in initial_checkout_ids]

    if not new_checkouts:
        return {"result": "others"}

    # Check each new checkout to see if it matches all criteria
    for checkout in new_checkouts:
        checkout_id, chk_asset_id, chk_user_id, project_name, chk_location_id, due_date, checked_in_at, note = checkout

        # Verify all required fields
        if chk_asset_id != asset_id:
            continue
        if chk_user_id != user_id:
            continue
        if project_name != 'Q3 Brand Shoot':
            continue
        if due_date != '2025-08-15':
            continue
        if chk_location_id != location_id:
            continue
        if checked_in_at is not None:
            continue

        # Verify note contains required text about batteries and SD card
        if not note:
            continue
        note_lower = note.lower()
        has_batteries = 'batter' in note_lower
        has_sd_card = 'sd' in note_lower and 'card' in note_lower
        has_return = 'return' in note_lower

        if not (has_batteries and has_sd_card and has_return):
            continue

        # All criteria met
        return {"result": "complete"}

    return {"result": "others"}