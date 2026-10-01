import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
import aiohttp

# --- ПОЛУЧЕНИЕ ТОКЕНОВ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not TELEGRAM_TOKEN or not DISCORD_WEBHOOK_URL:
    raise ValueError(
        "КРИТИЧЕСКАЯ ОШИБКА: Переменные окружения TELEGRAM_TOKEN или DISCORD_WEBHOOK_URL не настроены!"
    )
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

async def send_to_discord(full_text: str):
    """Отправляет готовый текст в Discord через Webhook"""
    payload = {
        "content": full_text  # Discord примет сообщение в формате "Имя: текст"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(DISCORD_WEBHOOK_URL, json=payload) as response:
                if response.status in:
                    logging.info("Сообщение успешно доставлено в Discord.")
                else:
                    logging.error(f"Ошибка Discord API: {response.status}")
        except Exception as e:
            logging.error(f"Не удалось связаться с Discord: {e}")

@dp.message()
async def handle_tg_message(message: types.Message):
    # Проверяем, что сообщение из группы/супергруппы и не от бота
    if message.chat.type not in ["group", "supergroup"] or message.from_user.is_bot:
        return

    # Получаем имя и текст
    user_name = message.from_user.full_name
    text_content = message.text or message.caption
    
    # Если текста нет (например, просто стикер или файл), ничего не делаем
    if not text_content:
        return

    # Формируем итоговую строку для Дискорда
    formatted_message = f"{user_name}: {text_content}"

    # Отправляем в Discord
    await send_to_discord(formatted_message)

async def main():
    logging.info("Бот запущен и ожидает сообщений в Telegram-группе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
