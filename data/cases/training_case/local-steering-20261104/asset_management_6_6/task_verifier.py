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

    # Step 1: Find the asset_id for VIN '1HGCM82633A004352'
    asset_query = "SELECT id FROM assets WHERE vin = ?"
    asset_results = safe_query(final_db_path, asset_query, ('1HGCM82633A004352',))
    if not asset_results:
        return {"result": "others"}
    asset_id = asset_results[0][0]

    # Step 2: Find the checklist_id for 'DOT Pre-Trip'
    checklist_query = "SELECT id FROM inspection_checklists WHERE name = ?"
    checklist_results = safe_query(final_db_path, checklist_query, ('DOT Pre-Trip',))
    if not checklist_results:
        return {"result": "others"}
    checklist_id = checklist_results[0][0]

    # Step 3: Find the newly created inspection for this asset on 2025-01-07
    inspection_query = """SELECT id, overall_status, checklist_id 
                          FROM inspections 
                          WHERE asset_id = ? AND inspection_date = ? AND checklist_id = ?"""
    inspection_results = safe_query(final_db_path, inspection_query, (asset_id, '2025-01-07', checklist_id))
    
    initial_inspections = safe_query(initial_db_path, inspection_query, (asset_id, '2025-01-07', checklist_id))
    
    # Check if a new inspection was created
    if len(inspection_results) <= len(initial_inspections):
        return {"result": "others"}
    
    # Get the inspection that should be new (could be multiple, need to find the right one)
    new_inspection = None
    initial_inspection_ids = {insp[0] for insp in initial_inspections}
    for insp in inspection_results:
        if insp[0] not in initial_inspection_ids:
            new_inspection = insp
            break
    
    if not new_inspection:
        return {"result": "others"}
    
    inspection_id = new_inspection[0]
    overall_status = new_inspection[1]
    
    # Step 4: Verify overall_status is 'fail'
    if overall_status != 'fail':
        return {"result": "others"}

    # Step 5: Get all checklist items for 'DOT Pre-Trip'
    checklist_items_query = "SELECT id, name FROM inspection_checklist_items WHERE checklist_id = ?"
    checklist_items = safe_query(final_db_path, checklist_items_query, (checklist_id,))
    if len(checklist_items) != 4:
        return {"result": "others"}
    
    # Map item names to IDs
    item_id_map = {item[1]: item[0] for item in checklist_items}
    left_rear_tire_item_id = item_id_map.get('Left rear tire tread')
    if not left_rear_tire_item_id:
        return {"result": "others"}

    # Step 6: Verify all inspection item results exist for this inspection
    results_query = """SELECT checklist_item_id, status, photo_ref 
                       FROM inspection_items_results 
                       WHERE inspection_id = ?"""
    item_results = safe_query(final_db_path, results_query, (inspection_id,))
    
    if len(item_results) != 4:
        return {"result": "others"}
    
    # Step 7: Verify the 'Left rear tire tread' item failed with correct photo reference
    left_tire_result = None
    other_results = []
    for result in item_results:
        item_id, status, photo_ref = result
        if item_id == left_rear_tire_item_id:
            left_tire_result = result
        else:
            other_results.append(result)
    
    if not left_tire_result:
        return {"result": "others"}
    
    if left_tire_result[1] != 'fail':
        return {"result": "others"}
    
    if left_tire_result[2] != 'photo_2025-01-07_0935.jpg':
        return {"result": "others"}
    
    # Step 8: Verify all other items passed
    for result in other_results:
        if result[1] != 'pass':
            return {"result": "others"}

    # Step 9: Find the inspection_items_results id for the failed tire item
    failed_result_query = """SELECT id FROM inspection_items_results 
                             WHERE inspection_id = ? AND checklist_item_id = ? AND status = 'fail'"""
    failed_result_id_results = safe_query(final_db_path, failed_result_query, (inspection_id, left_rear_tire_item_id))
    if not failed_result_id_results:
        return {"result": "others"}
    failed_result_id = failed_result_id_results[0][0]

    # Step 10: Verify an issue was created for this failed inspection item
    issue_query = """SELECT id, severity, due_date, source, source_inspection_item_result_id, title
                     FROM issues 
                     WHERE asset_id = ? AND source = 'inspection' AND source_inspection_item_result_id = ?"""
    issue_results = safe_query(final_db_path, issue_query, (asset_id, failed_result_id))
    
    initial_issues = safe_query(initial_db_path, issue_query, (asset_id, failed_result_id))
    
    # Check if a new issue was created
    if len(issue_results) <= len(initial_issues):
        return {"result": "others"}
    
    # Find the new issue
    new_issue = None
    initial_issue_ids = {issue[0] for issue in initial_issues}
    for issue in issue_results:
        if issue[0] not in initial_issue_ids:
            new_issue = issue
            break
    
    if not new_issue:
        return {"result": "others"}
    
    issue_id, severity, due_date, source, source_insp_item_id, title = new_issue
    
    # Step 11: Verify issue attributes
    if severity != 'high':
        return {"result": "others"}
    
    if due_date != '2025-01-10':
        return {"result": "others"}
    
    if source != 'inspection':
        return {"result": "others"}
    
    if source_insp_item_id != failed_result_id:
        return {"result": "others"}
    
    # Step 12: Verify issue title/description relates to tire tread
    if not title:
        return {"result": "others"}
    
    # Check if title contains relevant keywords (case insensitive)
    title_lower = title.lower()
    if not (('tire' in title_lower or 'tread' in title_lower) and ('left' in title_lower or 'rear' in title_lower)):
        return {"result": "others"}
    
    # All checks passed
    return {"result": "complete"}