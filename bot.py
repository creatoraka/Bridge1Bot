import os
import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp

# --- ПОЛУЧЕНИЕ ТОКЕНА ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError(
        "КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения TELEGRAM_TOKEN не настроена!"
    )
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Инициализация базы данных для хранения URL вебхука
DB_FILE = "config.db"

def init_db():
    """Создает таблицу для настроек, если её нет"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()

def get_webhook_url():
    """Получает сохраненный вебхук из базы данных"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'discord_webhook'")
        row = cursor.fetchone()
        return row[0] if row else None

def save_webhook_url(url: str):
    """Сохраняет или обновляет вебхук в базе данных"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO settings (key, value) 
            VALUES ('discord_webhook', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (url,))
        conn.commit()

async def send_to_discord(full_text: str):
    """Отправляет готовый текст в Discord через сохраненный Webhook"""
    webhook_url = get_webhook_url()
    if not webhook_url:
        logging.warning("Сообщение не отправлено: Discord Webhook еще не настроен с помощью команды /webhook")
        return

    payload = {"content": full_text}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(webhook_url, json=payload) as response:
                # Исправлена ошибка синтаксиса: проверяем успешные коды (200-299)
                if 200 <= response.status < 300:
                    logging.info("Сообщение успешно доставлено в Discord.")
                else:
                    logging.error(f"Ошибка Discord API. Статус-код: {response.status}")
        except Exception as e:
            logging.error(f"Не удалось связаться с Discord: {e}")

@dp.message(Command("webhook"))
async def cmd_set_webhook(message: types.Message):
    """Обработчик команды /webhook <ссылка>"""
    # Выделяем текст после команды
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.reply("Использование команды: `/webhook https://discord.com...`", parse_mode="Markdown")
        return

    new_url = args[1].strip()
    
    if not new_url.startswith("https://discord.com"):
        await message.reply("❌ Это не похоже на правильную ссылку на вебхук Discord.")
        return

    # Сохраняем вебхук в базу данных
    save_webhook_url(new_url)
    await message.reply("✅ Ссылка на Discord Webhook успешно обновлена!")

@dp.message()
async def handle_tg_message(message: types.Message):
    # Игнорируем команды (они начинаются с /)
    if message.text and message.text.startswith("/"):
        return

    # Проверяем, что сообщение из группы/супергруппы и не от бота
    if message.chat.type not in ["group", "supergroup"] or message.from_user.is_bot:
        return

    user_name = message.from_user.full_name
    text_content = message.text or message.caption
    
    if not text_content:
        return

    formatted_message = f"{user_name}: {text_content}"
    await send_to_discord(formatted_message)

async def main():
    init_db()  # Запуск базы данных при старте
    logging.info("Бот запущен и ожидает сообщений в Telegram-группе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
