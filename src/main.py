import os
import json
import sys
from datetime import datetime, timezone
import requests

def load_curriculum():
    """Loads the course curriculum database safely."""
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "curriculum.json")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Curriculum file not found at {data_path}")
        sys.exit(1)

def send_to_discord(webhook_url, module):
    """Dispatches the structured curriculum module as a clean Discord Embed."""
    payload = {
        "embeds": [
            {
                "title": module["title"],
                "description": module["description"],
                "color": 3447003,  # Tech blue accent color
                "fields": module.get("fields", []),
                "image": {"url": module["image_url"]} if module.get("image_url") else None,
                "footer": {
                    "text": f"Forex Engine | Auto-delivered on {module['delivery_day']}"
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code in [200, 204]:
            print(f"Successfully delivered module: {module['id']}")
        else:
            print(f"Failed to deliver payload. HTTP Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Network error trying to dispatch webhook: {e}")

def main():
    # Retrieve webhook URL from environment secret
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL environment variable is missing.")
        sys.exit(1)

    # Determine current day of the week using modern timezone-aware UTC datetime
    current_day = datetime.now(timezone.utc).strftime("%A")
    print(f"Initiating automation check for day: {current_day}")

    curriculum = load_curriculum()
    modules_to_send = [mod for mod in curriculum.get("modules", []) if mod["delivery_day"] == current_day]

    if not modules_to_send:
        print(f"No course content scheduled for delivery on {current_day}. Standing down.")
        return

    for module in modules_to_send:
        send_to_discord(webhook_url, module)

if __name__ == "__main__":
    main()
