import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import sqlite3

TOKEN = "7204847095:AAEIAmuJV8vqC8J5XepRVPQRmdmTUePVuYU"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def get_db_connection():
    return sqlite3.connect('feedback_bot.db')

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            telegram_id INTEGER UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date_time TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            meeting_id INTEGER,
            effectiveness INTEGER,
            satisfaction INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()


@dp.message(Command("start"))
async def start_handler(message: Message) -> None:
    await bot.send_message("Привет!")

async def main():
    try:
        print("Бот запущен!")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())