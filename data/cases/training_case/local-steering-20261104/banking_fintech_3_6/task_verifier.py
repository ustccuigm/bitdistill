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

    # Step 1: Verify the card exists and identify it
    card_query = "SELECT id, user_id, status FROM debit_cards WHERE last4 = ? AND physical_card = 1"
    
    initial_cards = safe_query(initial_db_path, card_query, ('4321',))
    final_cards = safe_query(final_db_path, card_query, ('4321',))
    
    if not initial_cards or not final_cards:
        return {"result": "others"}
    
    initial_card = initial_cards[0]
    final_card = final_cards[0]
    
    card_id = initial_card[0]
    user_id = initial_card[1]
    initial_status = initial_card[2]
    final_status = final_card[2]
    
    # Step 2: Verify card was locked (status changed from active to locked)
    if initial_status != 'active' or final_status != 'locked':
        return {"result": "others"}
    
    # Step 3: Check for new replacement request
    replacement_query = "SELECT id, user_id, original_card_id, reason, status, mail_to_address_id FROM card_replacement_requests WHERE original_card_id = ?"
    
    initial_requests = safe_query(initial_db_path, replacement_query, (card_id,))
    final_requests = safe_query(final_db_path, replacement_query, (card_id,))
    
    # Count new requests (should have at least one more in final than initial)
    if len(final_requests) <= len(initial_requests):
        return {"result": "others"}
    
    # Step 4: Find the new request(s) by comparing
    initial_request_ids = {req[0] for req in initial_requests}
    new_requests = [req for req in final_requests if req[0] not in initial_request_ids]
    
    if not new_requests:
        return {"result": "others"}
    
    # Step 5: Verify at least one new request meets criteria
    for request in new_requests:
        req_user_id = request[1]
        req_card_id = request[2]
        req_reason = request[3]
        req_status = request[4]
        req_mail_address = request[5]
        
        # Verify the request is for the correct user and card
        if req_user_id != user_id or req_card_id != card_id:
            continue
        
        # Verify reason mentions loss
        if not req_reason:
            continue
        
        reason_lower = req_reason.lower()
        if 'loss' not in reason_lower and 'lost' not in reason_lower:
            continue
        
        # Verify status is pending or processed
        if req_status not in ('pending', 'processed'):
            continue
        
        # Verify mail_to_address_id is NULL (using existing address)
        # The task says "to my existing home address on file" which means NULL
        if req_mail_address is not None:
            continue
        
        # All checks passed for this request
        return {"result": "complete"}
    
    # No request met all criteria
    return {"result": "others"}