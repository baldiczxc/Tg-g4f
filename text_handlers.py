import asyncio
import logging
from aiogram.types import Message
from aiogram.exceptions import TelegramRetryAfter
import g4f
from g4f import Provider
import time

logger = logging.getLogger(__name__)

BLACKBOX_LIMIT_MSG = "You have reached your request limit for the hour."

async def generate_gpt_stream(messages: list, model: str, queue: asyncio.Queue, providers: list):
    """Генерация ответа в потоке с использованием g4f."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'Origin': 'https://www.google.com/'
        }

        for provider in providers:
            try:
                full_response = ""
                async for chunk in g4f.ChatCompletion.create_async(
                        model=model,
                        messages=messages,
                        headers=headers,
                        timeout=10,
                        stream=True
                ):
                    logger.debug(f"📦 Получен chunk: {chunk} (тип: {type(chunk)})")
                    
                    # Обработка текстовых чанков
                    if isinstance(chunk, str):
                        # Проверка лимита Blackbox
                        if BLACKBOX_LIMIT_MSG in chunk:
                            await queue.put(Exception("⚠️ Произошла ошибка при генерации ответа, попробуйте позже\nИли выберите другую модель"))
                            return
                        full_response += chunk
                        await queue.put(chunk)
                    
                    # Обработка объектов с атрибутом content
                    elif hasattr(chunk, 'content') and chunk.content:
                        content = chunk.content
                        # Проверка лимита Blackbox
                        if BLACKBOX_LIMIT_MSG in content:
                            await queue.put(Exception("⚠️ Произошла ошибка при генерации ответа, попробуйте позже\nИли выберите другую модель"))
                            return
                        full_response += content
                        await queue.put(content)
                    
                
                # Финальная проверка лимита
                if BLACKBOX_LIMIT_MSG in full_response:
                    await queue.put(Exception("⚠️ Произошла ошибка при генерации ответа, попробуйте позже\nИли выберите другую модель"))
                    return
                
                if full_response.strip():
                    await queue.put(None)
                return
                
            except Exception as e:
                logger.error(f"❌ Ошибка в {provider.__name__}: {str(e)}")
                continue
        
        await queue.put(Exception("⚠️ Все провайдеры недоступны. Попробуйте позже."))
    
    except Exception as e:
        logger.error(f"❌ Общая ошибка генерации: {str(e)}")
        await queue.put(e)

async def process_user_message(message: Message, model: str, history: list, save_message_func):
    """
    Обработка пользовательского сообщения с учетом истории диалога.
    """
    user_message = message.text
    await save_message_func(message.from_user.id, "user", user_message)

    messages = [{"role": "system", "content": "Ты отвечаешь в телеграмме, используй форматирование как в телеграмме"}]
    for msg_type, content in history:
        role = "user" if msg_type == "user" else "assistant"
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    response_message = await message.answer(f"⏳ Обработка запроса... (Модель: {model})")
    response_text = ""
    last_update_time = 0
    update_interval = 0.3

    async def safe_edit(text: str):
        nonlocal last_update_time
        try:
            await response_message.edit_text(text[:4096], parse_mode='Markdown')
            last_update_time = time.time()
        except TelegramRetryAfter as e:
            logger.warning(f"⏳ Превышен лимит Telegram, ждем {e.retry_after} сек.")
            await asyncio.sleep(e.retry_after)
            await safe_edit(text)
        except Exception as e:
            logger.error(f"❌ Ошибка редактирования: {str(e)}")

    try:
        queue = asyncio.Queue()
        asyncio.create_task(generate_gpt_stream(messages, model, queue, [Provider.Blackbox]))

        while True:
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=35.0)
            except asyncio.TimeoutError:
                logger.error("⚠️ Таймаут ожидания ответа")
                await safe_edit("⌛ Превышено время ожидания ответа")
                return

            if chunk is None:
                break
            if isinstance(chunk, Exception):
                raise chunk

            response_text += str(chunk)
            if (time.time() - last_update_time) > update_interval:
                await safe_edit(response_text[:4096])

        if response_text:
            await safe_edit(response_text[:4096])
            await save_message_func(message.from_user.id, "bot", response_text)
    except Exception as e:
        logger.error(f"❌ Ошибка генерации: {str(e)}")
        await safe_edit("⚠️ Произошла ошибка при генерации ответа, попробуйте позже\nИли выберите другую модель")
