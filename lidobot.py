import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Твои данные
TOKEN = "8329966485:AAE-MIlK3wT704TOfKpCkify-2U4qUshI1o"
ADMIN_ID = 5732894871

bot = Bot(token=TOKEN)
dp = Dispatcher()


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
