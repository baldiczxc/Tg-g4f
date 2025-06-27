import logging
import time
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InputFile, FSInputFile
from aiogram.exceptions import TelegramForbiddenError
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from g4f.client import Client  # Добавлен импорт клиента для генерации изображений
from image_gen_kandinsky import Text2ImageAPI
from image_handlers import generate_image_with_flux_and_send
from text_handlers import process_user_message

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Исправлено levellevel на levelname
)
logger = logging.getLogger(__name__)

# Инициализация базы данных SQLite
conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()

# Таблица для настроек пользователя
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        model TEXT NOT NULL DEFAULT 'gpt-4'
    )
''')

# Таблица для истории диалога
cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message_type TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
''')
conn.commit()

# Инициализация бота и диспетчера
TOKEN = "7836340941:AAEbWid0dlRGb2LMsBUc3CLL72JXTJ5vzUA"
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Список доступных моделей
TEXT_MODELS = ["llama-3.3-70b", "deepseek-v3", "deepseek-r1", "gpt-4o", "gpt-4o-mini", "gpt-4.1"]
IMAGE_MODELS = ["flux","flux-pro", "flux-dev", "flux-schnell", "dall-e", "gpt-image"]

def get_model_keyboard_paginated(page: int = 1):
    """Создает инлайн-клавиатуру для выбора моделей с пагинацией."""
    keyboard = InlineKeyboardBuilder()
    if page == 1:
        for model in TEXT_MODELS:
            keyboard.button(text=model.capitalize(), callback_data=f"model_{model}")
        keyboard.button(text="➡️ Модели для изображений", callback_data="page_2")
    elif page == 2:
        for model in IMAGE_MODELS:
            keyboard.button(text=model.capitalize(), callback_data=f"model_{model}")
        keyboard.button(text="⬅️ Модели для текста", callback_data="page_1")
    keyboard.adjust(2)
    return keyboard.as_markup()

# Настройки для Text2ImageAPI
TEXT2IMAGE_API_URL = ""
TEXT2IMAGE_API_KEY = ""
TEXT2IMAGE_SECRET_KEY = ""
text2image_api = Text2ImageAPI(TEXT2IMAGE_API_URL, TEXT2IMAGE_API_KEY, TEXT2IMAGE_SECRET_KEY)

# Инициализация клиента для генерации изображений
g4f_client = Client()

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Выбрать модель 🤖")],
    ],
    resize_keyboard=True
)

async def get_user_model(user_id: int) -> str:
    """Получает выбранную модель пользователя из базы данных."""
    cursor.execute("SELECT model FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else "gpt-4"

async def set_user_model(user_id: int, model: str):
    """Устанавливает выбранную модель пользователя в базу данных."""
    cursor.execute("INSERT OR REPLACE INTO users (user_id, model) VALUES (?, ?)", (user_id, model))  # Исправлено
    conn.commit()

async def save_message(user_id: int, message_type: str, content: str):
    """Сохраняет сообщение в историю диалога."""
    cursor.execute(
        "INSERT INTO chat_history (user_id, message_type, content) VALUES (?, ?, ?)",
        (user_id, message_type, content)
    )
    conn.commit()

async def get_chat_history(user_id: int, limit: int = 10) -> list:
    """Получает последние сообщения из истории диалога."""
    cursor.execute(
        "SELECT message_type, content FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    )
    return cursor.fetchall()[::-1]

async def clear_chat_history(user_id: int):
    """Очищает историю диалога пользователя."""
    cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()


@router.message(Command("menu"))
async def show_menu(message: Message):
    """Обработка команды /menu."""
    await message.answer("Выберите действие:", reply_markup=main_menu)

@router.message(Command("help"))
async def show_menu(message: Message):
    """Обработка команды /help."""
    await message.answer(
        "/start - перезапуск бота\n"
        "/delete_history - удаление истории диалога\n"
        "/history - история диолога\n"
        "/menu - вывод клавиатуры\n"
    )

@router.message(F.text == "Выбрать модель 🤖")
async def choose_model(message: Message):
    """Обработка выбора модели."""
    await message.answer("Выберите модель для работы:", reply_markup=get_model_keyboard_paginated(page=1))

@router.callback_query(F.data.startswith("page_"))
async def paginate_models(callback: CallbackQuery):
    """Обработка переключения страниц выбора моделей."""
    page = int(callback.data.split("_")[1])
    if page == 1:
        await callback.message.edit_text("Выберите модель для текста:", reply_markup=get_model_keyboard_paginated(page=1))
    elif page == 2:
        await callback.message.edit_text("Выберите модель для изображений:", reply_markup=get_model_keyboard_paginated(page=2))
    await callback.answer()

@router.callback_query(F.data.startswith("model_"))
async def select_model(callback: CallbackQuery):
    """Обработка выбора модели через инлайн-кнопку."""
    model_name = callback.data.split("_", 1)[1]
    await set_user_model(callback.from_user.id, model_name)
    await callback.message.edit_text(f"✅ Вы выбрали модель: {model_name}")
    await callback.answer("Модель изменена!")
    # Не спрашиваем про промт сразу!

def get_prompt_choice_keyboard():
    """Инлайн-клавиатура для выбора способа генерации промта."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сделать промт", callback_data="prompt_auto"),
             InlineKeyboardButton(text="Использовать мой текст", callback_data="prompt_user")]
        ]
    )
    return keyboard

# --- Простая память для хранения состояния пользователя (user_id: 'wait_prompt_choice' или None) ---
user_states = {}
user_texts = {}

@router.callback_query(F.data.in_(["prompt_auto", "prompt_user"]))
async def prompt_choice_handler(callback: CallbackQuery):
    """Обработка выбора способа генерации промта для изображения."""
    user_id = callback.from_user.id
    model = await get_user_model(user_id)
    # Получаем текст, который пользователь до этого отправил
    user_text = user_texts.pop(user_id, None)
    # Сначала отвечаем на callback, чтобы не было ошибки TelegramBadRequest
    await callback.answer()
    # Затем удаляем сообщение с выбором
    try:
        await callback.message.delete()
    except Exception:
        pass
    if not user_text:
        await callback.message.answer("Пожалуйста, сначала отправьте описание для изображения.")
        return
    if callback.data == "prompt_auto":
        # Генерируем промт автоматически
        await generate_image_with_flux_and_send(callback.message, user_text, model)
    else:
        # Используем текст пользователя как промт
        await generate_image_with_flux_and_send(callback.message, user_text, model)
    user_states[user_id] = None

@router.message(Command("delete_history"))
async def clear_history(message: Message):
    """Очистка истории диалога."""
    await clear_chat_history(message.from_user.id)
    await message.answer("✅ История диалога очищена!")

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start."""
    await set_user_model(message.from_user.id, "GPT-4o")
    await message.answer(
        "Привет! Я бот, использующий нейросети для ответов.\nИспользуйте кнопку ниже ⬇️",
        reply_markup=main_menu
    )

@router.message(Command("history"))
async def check_history(message: Message):
    """Проверка истории диалога."""
    user_id = message.from_user.id
    history = await get_chat_history(user_id)
    if not history:
        await message.answer("История пуста.")
    else:
        history_text = "\n".join([f"{msg_type}: {content}" for msg_type, content in history])
        await message.answer(f"Ваша история диалога:\n{history_text}")


@router.message(F.text)
async def handle_user_message(message: Message):
    """
    Обработка текстового сообщения.
    """
    try:
        user_id = message.from_user.id
        model = await get_user_model(user_id)
        # Если выбрана модель для изображений
        if model.lower() in IMAGE_MODELS:
            # Если пользователь только что выбрал модель или еще не выбрал способ генерации промта
            if user_states.get(user_id) != 'wait_prompt_choice':
                user_states[user_id] = 'wait_prompt_choice'
                user_texts[user_id] = message.text
                await message.answer(
                    "Как сгенерировать промт для изображения?",
                    reply_markup=get_prompt_choice_keyboard()
                )
                return
        # Для остальных моделей обрабатываем текстовое сообщение
        history = await get_chat_history(user_id, limit=10)
        await process_user_message(message, model, history, save_message)
    except TelegramForbiddenError:
        logger.warning(f"Пользователь {message.from_user.id} заблокировал бота.")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
