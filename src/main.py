import os
import json
import sys
import glob
from datetime import datetime, timezone
import requests

def load_all_curricula():
    """Scans the data directory and aggregates all JSON curriculum modules."""
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    json_files = glob.glob(os.path.join(data_dir, "*.json"))
    
    if not json_files:
        print(f"Error: No JSON curriculum files found in {data_dir}")
        sys.exit(1)

    all_modules = []
    
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                modules = data.get("modules", [])
                all_modules.extend(modules)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse JSON in {file_path}. Skipping.")
        except Exception as e:
            print(f"Warning: Could not read {file_path}. Error: {e}")
            
    return all_modules

def fetch_friday_quote():
    """Fetches a random motivational quote from the Internet via ZenQuotes API."""
    try:
        # Utilizing a robust, free public API for inspirational quotes
        response = requests.get("https://zenquotes.io/api/random", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                return {
                    "quote": data[0].get("q", "Discipline is the bridge between goals and accomplishment."),
                    "author": data[0].get("a", "Jim Rohn")
                }
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching quote: {e}")
    
    # Fallback to ensure the app generates an outcome even if the network fails
    return {
        "quote": "The elements of good trading are: 1. Cutting losses, 2. Cutting losses, and 3. Cutting losses. If you can follow these three rules, you may have a chance.",
        "author": "Ed Seykota"
    }

def send_quote_to_discord(webhook_url, quote_data):
    """Dispatches the Friday motivational quote as a clean Discord Embed."""
    payload = {
        "embeds": [
            {
                "title": "🧠 Friday Market Psychology & Motivation",
                "description": f"**\"{quote_data['quote']}\"**\n\n— *{quote_data['author']}*",
                "color": 15844367, # Gold color for high contrast and distinction
                "footer": {
                    "text": "Forex Engine | End of Week Reflection"
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code in [200, 204]:
            print("Successfully delivered Friday quote.")
        else:
            print(f"Failed to deliver payload. HTTP Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Network error trying to dispatch webhook: {e}")

def send_to_discord(webhook_url, module):
    """Dispatches the structured curriculum module as a clean Discord Embed."""
    payload = {
        "embeds": [
            {
                "title": module["title"],
                "description": module["description"],
                "color": 3447003,
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

    # Friday Intercept: Send motivational quote instead of curriculum
    if current_day == "Friday":
        print("Friday detected. Fetching motivational quote from the Internet...")
        quote_data = fetch_friday_quote()
        send_quote_to_discord(webhook_url, quote_data)
        return

    all_modules = load_all_curricula()
    
    # Filter modules that are scheduled for today
    modules_to_send = [mod for mod in all_modules if mod.get("delivery_day") == current_day]

    if not modules_to_send:
        print(f"No course content scheduled for delivery on {current_day}. Standing down.")
        return

    for module in modules_to_send:
        send_to_discord(webhook_url, module)

if __name__ == "__main__":
    main()
