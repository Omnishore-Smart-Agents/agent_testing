def create_failure_card(test_id, error_details, screenshot_path=None):
    """
    Mock implementation of Trello API.
    """
    print(f"[TRELLO MOCK] Creating card for {test_id}")
    print(f"  - Error: {error_details}")
    if screenshot_path:
        print(f"  - Attached image: {screenshot_path}")
    return {"card_id": "mock_id_123", "status": "created"}
