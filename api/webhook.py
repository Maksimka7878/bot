import json
import os
import asyncio
from http.server import BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Токен и ID администратора (рекомендуется хранить в переменных окружения Vercel)
TOKEN = os.environ.get("BOT_TOKEN", "8329966485:AAE-MIlK3wT704TOfKpCkify-2U4qUshI1o")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5732894871"))

dp = Dispatcher()


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
