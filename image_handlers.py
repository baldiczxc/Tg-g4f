import asyncio
import logging
from aiogram.types import Message
from g4f.client import Client

logger = logging.getLogger(__name__)
g4f_client = Client()

def create_prompt(user_text: str) -> str:
    """
    Создаёт промт для генерации изображения с помощью g4f.
    """
    try:
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Create a detailed image generation prompt based on: {user_text}"}],
            web_search=False
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ Ошибка генерации промта с помощью g4f: {str(e)}")
        return f"Generate an image based on the following description: {user_text}"


async def generate_image_with_flux_and_send(message: Message, translated_prompt: str, model: str):
    """
    Генерация изображения с помощью Flux и отправка пользователю по URL.
    """
    generating_message = None
    
    try:
        generating_message = await message.answer("⏳ Создание изображения...")
        # Создание финального промта
        final_prompt = create_prompt(translated_prompt)
        # Генерация изображения
        response = g4f_client.images.generate(
            model=model,
            prompt=final_prompt,
            response_format="url"
        )
        image_url = response.data[0].url  # Получаем URL изображения
        if generating_message:
            await generating_message.delete()
        # Отправляем изображение пользователю
        await message.answer_photo(image_url)
    except Exception as e:
        logger.error(f"❌ Ошибка генерации изображения Flux: {str(e)}")
        await message.answer("⚠️ Произошла ошибка при генерации изображения. Попробуйте снова.")

