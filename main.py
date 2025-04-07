import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "7204847095:AAEIAmuJV8vqC8J5XepRVPQRmdmTUePVuYU"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

class UserState(StatesGroup):
    waiting_for_full_name = State()
    editing_full_name = State()
    meeting_title = State()
    meeting_datetime = State()
    effectiveness = State()
    satisfaction = State()

def get_db_connection():
    return sqlite3.connect('fback.db')

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            t_id INTEGER UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date_time TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fback (
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

def m_menu():
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Оценить встречу")]],
        resize_keyboard=True
    )
    return markup

def editconfirm():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подтвердить"), KeyboardButton(text="Редактировать")]
        ],
        resize_keyboard=True
    )
    return markup

def ratemenu():
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=str(i)) for i in range(1, 6)]],
        resize_keyboard=True
    )
    return markup

@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM employees WHERE t_id = ?", (user_id,))
    employee = cursor.fetchone()
    conn.close()

    if employee:
        await message.answer("Добро пожаловать!", reply_markup=m_menu())
    else:
        await message.answer("Пожалуйста, введите свои ФИО:")
        await state.set_state(UserState.waiting_for_full_name)

@dp.message(StateFilter(UserState.waiting_for_full_name))
async def process_full_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()
    user_id = message.from_user.id

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM employees WHERE full_name = ?", (full_name,))
    employee = cursor.fetchone()

    if employee:
        cursor.execute("UPDATE employees SET t_id = ? WHERE id = ?", (user_id, employee[0]))
        conn.commit()
        conn.close()
        await message.answer("Добро пожаловать!", reply_markup=m_menu())
        await state.clear()
    else:
        conn.close()
        await message.answer("Сотрудник не найден")
        await state.set_state(UserState.waiting_for_full_name)

@dp.message(lambda message: message.text == "Оценить встречу")
async def handle_menu(message: types.Message, state: FSMContext):
    await start_meeting_feedback(message, state)

async def start_meeting_feedback(message: types.Message, state: FSMContext):
    await message.answer("введите название встречи:")
    await state.set_state(UserState.meeting_title)

@dp.message(StateFilter(UserState.meeting_title))
async def process_meeting_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer(f"Название встречи: {message.text}", reply_markup=editconfirm())
    await state.set_state(UserState.meeting_datetime)

@dp.message(StateFilter(UserState.meeting_datetime))
async def process_meeting_datetime_or_confirm(message: types.Message, state: FSMContext):
    if message.text == "Подтвердить":
        await message.answer("Введите дату и время начала:")
    elif message.text == "Редактировать":
        await message.answer("Введите название встречи:")
        await state.set_state(UserState.meeting_title)
    else:
        await state.update_data(datetime=message.text.strip())
        await message.answer(f"Дата и время: {message.text}", reply_markup=editconfirm())
        await state.set_state(UserState.effectiveness)

@dp.message(StateFilter(UserState.effectiveness))
async def process_effectiveness_or_confirm(message: types.Message, state: FSMContext):
    if message.text == "Подтвердить":
        await message.answer("Пожалуйста, оцените результативность встречи (от 1 до 5):", reply_markup=ratemenu())
    elif message.text == "Редактировать":
        await message.answer("Введите дату:")
        await state.set_state(UserState.meeting_datetime)
    else:
        await state.update_data(effectiveness=int(message.text))
        await message.answer("Дайте оценку вашей эмоциональной удовлетворённости (от 1 до 5):", reply_markup=ratemenu())
        await state.set_state(UserState.satisfaction)

@dp.message(StateFilter(UserState.satisfaction))
async def process_satisfaction(message: types.Message, state: FSMContext):
    await state.update_data(satisfaction=int(message.text))
    await save_fbavk(message, state)
    await message.answer("Благодарю, ваши ответы сохранены :3", reply_markup=m_menu())
    await state.clear()

async def save_fbavk(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO meets (title, date_time) VALUES (?, ?)", (data['title'], data['datetime']))
    meeting_id = cursor.lastrowid
    
    cursor.execute("SELECT id FROM employees WHERE t_id = ?", (user_id,))
    employee_id = cursor.fetchone()[0]
    
    cursor.execute("INSERT INTO fback (employee_id, meeting_id, effectiveness, satisfaction) VALUES (?, ?, ?, ?)",
                (employee_id, meeting_id, data['effectiveness'], data['satisfaction']))
    
    conn.commit()
    conn.close()

async def main():
    try:
        print("Бот запущен!")
        await dp.start_polling(bot)
    except Exception as oshibka:
        print(f"Произошла ошибка: {oshibka}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())