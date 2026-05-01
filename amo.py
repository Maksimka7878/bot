"""
AmoCRM интеграция — получение ссылки на запись звонка по номеру телефона.
TODO: заполнить после получения API-данных.
"""

import os
import aiohttp

AMO_DOMAIN = os.environ.get("AMO_DOMAIN", "")          # example.amocrm.ru
AMO_TOKEN = os.environ.get("AMO_TOKEN", "")             # long-lived access token


async def get_recording_url(phone: str) -> str | None:
    """
    Возвращает прямую ссылку на MP3-запись последнего звонка клиента.
    phone — номер в любом формате, очищаем до цифр.

    Возвращает None если запись не найдена или API не настроен.
    """
    if not AMO_DOMAIN or not AMO_TOKEN:
        return None

    # Нормализуем номер: оставляем только цифры
    digits = "".join(c for c in phone if c.isdigit())

    headers = {
        "Authorization": f"Bearer {AMO_TOKEN}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Ищем контакт по телефону
        url = f"https://{AMO_DOMAIN}/api/v4/contacts"
        params = {"query": digits, "limit": 1}
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

        contacts = data.get("_embedded", {}).get("contacts", [])
        if not contacts:
            return None
        contact_id = contacts[0]["id"]

        # 2. Получаем звонки контакта (последний)
        url = f"https://{AMO_DOMAIN}/api/v4/calls"
        params = {"filter[contact_id]": contact_id, "limit": 1, "order[created_at]": "desc"}
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

        calls = data.get("_embedded", {}).get("calls", [])
        if not calls:
            return None

        # 3. Возвращаем ссылку на запись
        return calls[0].get("record_url") or calls[0].get("link")
