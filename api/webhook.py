import json
import os
import re
import sys
import asyncio
from functools import partial
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))

import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

from transcribe import transcribe_bytes, score_lead, format_tg_reply
from amo import get_recording_url

TOKEN = os.environ.get("BOT_TOKEN", "8329966485:AAE-MIlK3wT704TOfKpCkify-2U4qUshI1o")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5732894871"))
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

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
            "Настрой AMO_DOMAIN и AMO_TOKEN в Vercel env"
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


@dp.message(Command("score"), F.from_user.id == ADMIN_ID)
async def cmd_score(message: types.Message):
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


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.bot.send_message(message.from_user.id, f"Канал запущен, ваш id: {message.from_user.id}")
    await message.bot.send_message(ADMIN_ID, f"Канал запущен, ваш id: {message.from_user.id}")


@dp.message(Command("kayer"))
async def cmd_kayer(message: types.Message):
    await message.bot.send_message(1238147392, "В таблицу добавлен новый лид ✅")
    await message.bot.send_message(ADMIN_ID, "В таблицу добавлен новый лид ✅")


@dp.message(Command("wb"))
async def cmd_wb(message: types.Message):
    await message.bot.send_message(1016265544, "В таблицу добавлен новый лид ✅")
    await message.bot.send_message(ADMIN_ID, "В таблицу добавлен новый лид ✅")


@dp.message(Command("inc_tan"))
async def cmd_inc_tan(message: types.Message):
    await message.bot.send_message(215933351, " Добавлен новый лид ✅")
    await message.bot.send_message(342343624, " Добавлен новый лид ✅")
    await message.bot.send_message(ADMIN_ID, "Добавлен новый лид ✅")


@dp.message(Command("inc_vik"))
async def cmd_inc_vik(message: types.Message):
    await message.bot.send_message(215933351, " Добавлен новый лид ✅")
    await message.bot.send_message(5043021562, " Добавлен новый лид ✅")
    await message.bot.send_message(ADMIN_ID, "Добавлен новый лид ✅")


@dp.message(Command("arzumanov"))
async def cmd_arzumanov(message: types.Message):
    await message.bot.send_message(280572695, " Добавлен новый лид ✅")
    await message.bot.send_message(ADMIN_ID, "Добавлен новый лид ✅")


@dp.message(Command("keep"))
async def cmd_keep(message: types.Message):
    await message.bot.send_message(126445299, " Добавлен новый лид ✅")
    await message.bot.send_message(259980067, " Добавлен новый лид ✅")
    await message.bot.send_message(158200687, " Добавлен новый лид ✅")
    await message.bot.send_message(ADMIN_ID, "Добавлен новый лид ✅")


async def process_update(update_data: dict):
    # Создаём Bot внутри async-функции, чтобы сессия открывалась в нужном loop
    bot = Bot(token=TOKEN)
    try:
        update = types.Update(**update_data)
        await dp.feed_update(bot, update)
    finally:
        await bot.session.close()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            update_data = json.loads(body.decode("utf-8"))

            # Создаём новый event loop для каждого serverless-запроса Vercel
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_update(update_data))
            finally:
                loop.close()

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
