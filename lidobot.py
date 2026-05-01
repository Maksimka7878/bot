import asyncio
import re
import os
from functools import partial

import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

from transcribe import transcribe_bytes, score_lead, format_tg_reply
from amo import get_recording_url

TOKEN = os.environ.get("BOT_TOKEN", "8329966485:AAE-MIlK3wT704TOfKpCkify-2U4qUshI1o")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5732894871"))
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

PHONE_RE = re.compile(r"[\+7|8][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}")


def _extract_phone(text: str) -> str | None:
    match = PHONE_RE.search(text or "")
    return match.group(0) if match else None


async def _download_mp3(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()


async def _analyze_and_reply(message: types.Message, phone: str):
    status = await message.reply("🔄 Ищу запись звонка...")

    mp3_url = await get_recording_url(phone)
    if not mp3_url:
        await status.edit_text(
            "⚠️ Запись не найдена в AmoCRM.\n"
            "Настрой AMO_DOMAIN и AMO_TOKEN в .env"
        )
        return

    await status.edit_text("⬇️ Скачиваю MP3...")
    try:
        audio_bytes = await _download_mp3(mp3_url)
    except Exception as e:
        await status.edit_text(f"❌ Ошибка скачивания: {e}")
        return

    await status.edit_text("🎙 Транскрибирую разговор... (~60 сек)")

    loop = asyncio.get_event_loop()
    try:
        transcription = await loop.run_in_executor(
            None, partial(transcribe_bytes, audio_bytes, GEMINI_API_KEY)
        )
        score = await loop.run_in_executor(
            None, partial(score_lead, transcription, GEMINI_API_KEY)
        )
    except Exception as e:
        await status.edit_text(f"❌ Ошибка анализа: {e}")
        return

    reply_text = format_tg_reply(transcription, score)
    await status.edit_text(reply_text)


# ── Команда /score — ответом на сообщение о лиде ──────────────────────────
@dp.message(Command("score"), F.from_user.id == ADMIN_ID)
async def cmd_score(message: types.Message):
    # Пробуем достать телефон: из аргумента команды или из replied сообщения
    args = message.text.split(maxsplit=1)
    phone = args[1].strip() if len(args) > 1 else None

    if not phone and message.reply_to_message:
        phone = _extract_phone(message.reply_to_message.text or "")

    if not phone:
        await message.reply(
            "Укажи телефон:\n"
            "• <code>/score +79991234567</code>\n"
            "• или ответь на сообщение с номером командой /score"
        )
        return

    await _analyze_and_reply(message.reply_to_message or message, phone)


# ── Существующие команды ───────────────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await bot.send_message(message.from_user.id, f"Канал запущен, ваш id: {message.from_user.id}")
    await bot.send_message(ADMIN_ID, f"Канал запущен, ваш id: {message.from_user.id}")


@dp.message(Command("kayer"))
async def cmd_kayer(message: types.Message):
    await bot.send_message(1238147392, "В таблицу добавлен новый лид ✅")
    await bot.send_message(ADMIN_ID, "В таблицу добавлен новый лид ✅")


@dp.message(Command("wb"))
async def cmd_wb(message: types.Message):
    await bot.send_message(1016265544, "В таблицу добавлен новый лид ✅")
    await bot.send_message(ADMIN_ID, "В таблицу добавлен новый лид ✅")


@dp.message(Command("inc_tan"))
async def cmd_inc_tan(message: types.Message):
    await bot.send_message(215933351, " Добавлен новый лид ✅")
    await bot.send_message(342343624, " Добавлен новый лид ✅")
    await bot.send_message(ADMIN_ID, "Добавлен новый лид ✅")


@dp.message(Command("inc_vik"))
async def cmd_inc_vik(message: types.Message):
    await bot.send_message(215933351, " Добавлен новый лид ✅")
    await bot.send_message(5043021562, " Добавлен новый лид ✅")
    await bot.send_message(ADMIN_ID, "Добавлен новый лид ✅")


@dp.message(Command("arzumanov"))
async def cmd_arzumanov(message: types.Message):
    await bot.send_message(280572695, " Добавлен новый лид ✅")
    await bot.send_message(ADMIN_ID, "Добавлен новый лид ✅")


async def main():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("Бот запущен...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
