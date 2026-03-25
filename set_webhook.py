#!/usr/bin/env python3
"""
Запустите этот скрипт ОДИН РАЗ после деплоя на Vercel,
чтобы зарегистрировать webhook у Telegram.

Замените YOUR_VERCEL_URL на ваш реальный URL, например:
https://bot-mu-khaki.vercel.app
"""

import urllib.request
import json

TOKEN = "8329966485:AAE-MIlK3wT704TOfKpCkify-2U4qUshI1o"
VERCEL_URL = "https://bot-mu-khaki.vercel.app"  # <-- ваш реальный URL

webhook_url = f"{VERCEL_URL}/api/webhook"
api_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"

print(f"Устанавливаю webhook: {webhook_url}")
with urllib.request.urlopen(api_url) as response:
    result = json.loads(response.read())
    print("Ответ:", json.dumps(result, ensure_ascii=False, indent=2))
