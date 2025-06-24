import requests
from django.conf import settings

def send_telegram_message(message):
    """📩 Adminlarga Telegram orqali xabar yuborish"""
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    response = requests.post(url, data=data)
    return response.json()
