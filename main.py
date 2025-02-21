import json
import re
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configuration
SETTINGS_FILE = 'settings.json'
BOT_STATE = {"enabled": False}  # Bot status
AUTHORIZED_PHONE = '996507118299'  # Authorized phone number
RESPOND_PHONE = '79216312691'    # Bot phone number
BOT_USER = {"fio": "Смирнов КВ", "tab_number": "475"}  # Authorized user details

# WhatsApp API URL and token
TOKEN = 'nIx0p3JeG4NP4gBOrgWUfPIDRmESrxgF'
API_URL = 'https://gate.whapi.cloud/messages/text'

def normalize_phone(phone):
    """Normalize phone number by removing non-digit characters."""
    return re.sub(r'\D', '', phone)

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

load_settings()

def send_message(to, body):
    if not isinstance(to, str) or not re.match(r'^[\d-]{10,31}(@[\w\.]{1,})?$', to):
        raise ValueError(f"Invalid 'to' parameter: {to}")
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
    }
    payload = {"to": to, "body": body}
    response = requests.post(API_URL, json=payload, headers=headers)
    print(f"Send message response: {response.status_code}, {response.text}")
    return response.json()

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = json.loads(request.get_data(as_text=True))
        if data.get("event", {}).get("type") == "messages":
            for message in data.get('messages', []):
                chat_id = message.get('chat_id')
                from_phone = message.get('from')
                text_body = message.get('text', {}).get('body', '')
                text_lower = text_body.lower()

                # Normalize phone numbers
                phone_part = from_phone.split('@')[0] if from_phone else ''
                from_norm = normalize_phone(phone_part)
                respond_norm = normalize_phone(RESPOND_PHONE)
                auth_norm = normalize_phone(AUTHORIZED_PHONE)

                # Handle commands from respond_phone
                if from_norm == respond_norm:
                    if text_lower == 'botoff':
                        BOT_STATE['enabled'] = False
                        save_settings()
                        send_message(chat_id, "Бот выключен.")
                        continue
                    elif text_lower == 'boton':
                        BOT_STATE['enabled'] = True
                        save_settings()
                        send_message(chat_id, "Бот включен.")
                        continue

                # Handle messages from authorized phone when bot is enabled
                if BOT_STATE['enabled'] and from_norm == auth_norm:
                    if any(kw in text_lower for kw in ['сегодня', 'завтра', 'в день', 'в ночь']):
                        response_text = f"{BOT_USER['fio']}, таб.номер {BOT_USER['tab_number']}"
                        send_message(chat_id, response_text)

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)