import json
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Конфигурация
SETTINGS_FILE = 'settings.json'
BOT_STATE = {"enabled": False}  # Состояние бота
AUTHORIZED_PHONE = '89219181589'  # Абонент-2
RESPOND_PHONE = '89052352883'  # Абонент-1 (сам бот)
BOT_USER = {"fio": "Смирнов Константин", "tab_number": "475"}  # Данные абонента-2

# URL API для отправки сообщений
TOKEN = 'nIx0p3JeG4NP4gBOrgWUfPIDRmESrxgF'
API_URL = 'https://gate.whapi.cloud/messages/text'

# Функции для работы с файлом настроек
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


# Загружаем настройки при старте
load_settings()


# Функция для отправки сообщения
def send_message(to, body):
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
    }
    payload = {
        "to": f"{to}@s.whatsapp.net",
        "body": body,
    }
    response = requests.post(API_URL, json=payload, headers=headers)
    print(f"Send message response: {response.status_code}, {response.text}")
    return response.json()


# Маршрут для обработки сообщений
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        raw_data = request.get_data(as_text=True)
        data = json.loads(raw_data)
        print(f"Incoming data: {data}")

        # Обрабатываем только события типа "messages"
        if data.get("event", {}).get("type") == "messages":
            for message in data.get('messages', []):
                user_phone = message['from']
                text = message['text']['body'].lower()

                # Если сообщение от самого RESPOND_PHONE (сам бот)
                if user_phone == RESPOND_PHONE:
                    # Обработка команд управления ботом
                    if text == "turnon":
                        if not BOT_STATE["enabled"]:
                            BOT_STATE["enabled"] = True
                            save_settings()
                            send_message(RESPOND_PHONE, "Бот включен.")
                            print("Bot enabled.")
                        else:
                            send_message(RESPOND_PHONE, "Бот уже включен.")
                    elif text == "turnoff":
                        if BOT_STATE["enabled"]:
                            BOT_STATE["enabled"] = False
                            save_settings()
                            send_message(RESPOND_PHONE, "Бот отключен.")
                            print("Bot disabled.")
                        else:
                            send_message(RESPOND_PHONE, "Бот уже отключен.")


# Если сообщение от AUTHORIZED_PHONE и бот включён
                elif user_phone == AUTHORIZED_PHONE and BOT_STATE["enabled"]:
                    # Проверяем ключевые слова
                    if any(keyword in text for keyword in ['сегодня', 'завтра', 'в день', 'в ночь']):
                        response_text = f"{BOT_USER['fio']}, таб.номер {BOT_USER['tab_number']}"
                        send_message(AUTHORIZED_PHONE, response_text)
                        print(f"Message sent to {AUTHORIZED_PHONE}: {response_text}")
                    else:
                        print("No relevant keywords found. Ignoring.")
                else:
                    print(f"Message from unauthorized or irrelevant phone: {user_phone}")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == 'main':
    app.run(debug=True, host='0.0.0.0', port=3000)