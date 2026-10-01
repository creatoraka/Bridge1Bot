import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
import aiohttp

# --- ПОЛУЧЕНИЕ ТОКЕНОВ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Проверка: если переменные не заданы, бот сразу сообщит об ошибке и не упадет скрытно
if not TELEGRAM_TOKEN or not DISCORD_WEBHOOK_URL:
    raise ValueError(
        "КРИТИЧЕСКАЯ ОШИБКА: Переменные окружения TELEGRAM_TOKEN или DISCORD_WEBHOOK_URL не настроены!"
    )
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

async def send_to_discord(username: str, text: str, avatar_url: str = None):
    payload = {
        "username": username,
        "content": text
    }
    if avatar_url:
        payload["avatar_url"] = avatar_url

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(DISCORD_WEBHOOK_URL, json=payload) as response:
                if response.status not in:
                    logging.error(f"Ошибка Discord API: {response.status}")
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение в Discord: {e}")

@dp.message()
async def handle_tg_message(message: types.Message):
    if message.chat.type not in ["group", "supergroup"] or message.from_user.is_bot:
        return

    user_name = message.from_user.full_name
    text_content = message.text or message.caption
    
    if not text_content:
        return

    avatar_url = None
    try:
        user_photos = await bot.get_user_profile_photos(message.from_user.id, limit=1)
        if user_photos.total_count > 0:
            file_id = user_photos.photos[0][0].file_id  # Исправлено обращение к фото в aiogram 3.x
            file = await bot.get_file(file_id)
            avatar_url = f"https://telegram.org{TELEGRAM_TOKEN}/{file.file_path}"
    except Exception:
        pass

    await send_to_discord(username=user_name, text=text_content, avatar_url=avatar_url)

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
