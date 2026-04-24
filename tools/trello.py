import os
import requests
from dotenv import load_dotenv

load_dotenv()

TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
BOARD_ID = os.getenv("TRELLO_BOARD_ID")

BASE_URL = "https://api.trello.com/1"


def get_list_id(list_name="Failed Test"):
    url = f"{BASE_URL}/boards/{BOARD_ID}/lists"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    lists = resp.json()
    for lst in lists:
        if lst["name"].lower() == list_name.lower():
            return lst["id"]
    return lists[0]["id"] if lists else None


def create_failure_card(test_id, error_details, screenshot_path=None):
    if not TRELLO_API_KEY or TRELLO_API_KEY == "votre_api_key":
        print("[TRELLO] API keys non configurées, utilisation du mode mock")
        return _mock_card(test_id, error_details, screenshot_path)

    try:
        list_id = get_list_id()
        card_url = f"{BASE_URL}/cards"
        params = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN,
            "idList": list_id,
            "name": f"Failed: {test_id}",
            "desc": f"**Error:** {error_details}\n\n**Test ID:** {test_id}"
        }
        resp = requests.post(card_url, params=params)
        resp.raise_for_status()
        card = resp.json()
        card_id = card["id"]
        print(f"[TRELLO] Carte créée: {card['url']}")

        if screenshot_path and os.path.exists(screenshot_path):
            attach_url = f"{BASE_URL}/cards/{card_id}/attachments"
            with open(screenshot_path, "rb") as f:
                files = {"file": f}
                data = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
                resp = requests.post(attach_url, files=files, data=data)
                resp.raise_for_status()
                print(f"[TRELLO] Screenshot attaché: {screenshot_path}")

        return {"card_id": card_id, "status": "created", "url": card["url"]}
    except Exception as e:
        print(f"[TRELLO ERROR] {e}")
        return _mock_card(test_id, error_details, screenshot_path)


def _mock_card(test_id, error_details, screenshot_path=None):
    print(f"[TRELLO MOCK] Creating card for {test_id}")
    print(f"  - Error: {error_details}")
    if screenshot_path:
        print(f"  - Attached image: {screenshot_path}")
    return {"card_id": "mock_id_123", "status": "created"}