import json
import re
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configuration
SETTINGS_FILE = 'settings.json'
BOT_STATE = {"enabled": False}  # Bot status
AUTHORIZED_PHONE = '89119877112'  # Authorized phone number
RESPOND_PHONE = '89052352883'    # Bot phone number
BOT_USER = {"fio": "Смирнов КВ", "tab_number": "475"}  # Authorized user details

# WhatsApp API URL and token
TOKEN = 'nIx0p3JeG4NP4gBOrgWUfPIDRmESrxgF'
API_URL = 'https://gate.whapi.cloud/messages/text'

# Load settings

def load_settings():
    global BOT_STATE, BOT_USER, RESPOND_PHONE
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as file:
            settings = json.load(file)
            BOT_STATE['enabled'] = settings.get('bot_state', False)
            BOT_USER['fio'] = settings.get('fio', "Иванов Иван")
            BOT_USER['tab_number'] = settings.get('tab_number', "1234")
            RESPOND_PHONE = settings.get('respond_phone', '996709450197')
    except FileNotFoundError:
        print("Settings file not found. Using default values.")


def save_settings():
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as file:
            settings = {
                'bot_state': BOT_STATE['enabled'],
                'fio': BOT_USER['fio'],
                'tab_number': BOT_USER['tab_number'],
                'respond_phone': RESPOND_PHONE
            }
            json.dump(settings, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")


# Load settings on startup
load_settings()

# Function to send a message
def send_message(to, body):
    """
    :param to: Full WhatsApp ID, e.g., '120363381745770655@g.us' or '996507118299@s.whatsapp.net'
    :param body: Text message to send
    """
    # Validate "to" parameter
    if not isinstance(to, str) or not re.match(r'^[\d-]{10,31}(@[\w\.]{1,})?$', to):
        raise ValueError(f"Invalid 'to' parameter: {to}")

    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
    }
    payload = {
        "to": to,
        "body": body,
    }
    response = requests.post(API_URL, json=payload, headers=headers)
    print(f"Send message response: {response.status_code}, {response.text}")
    return response.json()


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        raw_data = request.get_data(as_text=True)
        data = json.loads(raw_data)
        print(f"Incoming data: {data}")

        # We only care if event type is 'messages'
        if data.get("event", {}).get("type") == "messages":
            for message in data.get('messages', []):
                chat_id = message.get('chat_id')      # e.g. '120363381745770655@g.us'
                from_phone = message.get('from')      # e.g. '996507118299'
                text_body = message['text']['body']   # e.g. 'сегодня'
                text_lower = text_body.lower()

                # Validate chat_id
                if not chat_id or not re.match(r'^[\d-]{10,31}(@[\w\.]{1,})?$', chat_id):
                    print(f"Invalid chat_id: {chat_id}")
                    continue

                # If the bot is enabled and the sender is our authorized phone
                if BOT_STATE["enabled"] and from_phone == AUTHORIZED_PHONE:
                    # Check if the user said certain keywords
                    if any(keyword in text_lower for keyword in ['сегодня', 'завтра', 'в день', 'в ночь']):
                        response_text = f"{BOT_USER['fio']}, таб.номер {BOT_USER['tab_number']}"

                        # Reply back to the same chat_id (group or private)
                        send_message(chat_id, response_text)
                        print(f"Sent reply to {chat_id}")
                    else:
                        print("No relevant keywords found in message. Ignoring.")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(3000)  # Использует PORT из окружения, иначе 3000
    app.run(host='0.0.0.0', port=port, debug=True)