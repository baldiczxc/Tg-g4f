import aiohttp
import asyncio
import base64
import json


class Text2ImageAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }
        self.STYLES = ["KANDINSKY", "UHD", "ANIME", "DEFAULT"]

    async def _get_model_id(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS) as response:
                data = await response.json()
                return data[0]['id']

    async def _generate(self, prompt, model, style, dimensions):
        style_name = self.STYLES[style]
        width, height = map(int, dimensions.split('x'))
        doptext = "None"

        mod_options = {
            "1920x1080": (1920, 1080, "Изображение в UHD стиле."),
            "1080x1080": (1080, 1080, "Изображение в квадратном формате."),
            "1080x1920": (1080, 1920, "Изображение в вертикальном формате."),
            "1024x1024": (1024, 1024, "Изображение в формате 1024x1024.")
        }

        if dimensions in mod_options:
            width, height, doptext = mod_options[dimensions]

        print(width, height, doptext, prompt)
        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": width,
            "height": height,
            "request_id": None,
            "generateParams": {
                "query": prompt + doptext,
                "style": style_name
            }
        }
        data = aiohttp.FormData()
        data.add_field('model_id', str(model))
        data.add_field('params', json.dumps(params), content_type='application/json')

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    self.URL + 'key/api/v1/text2image/run',
                    headers=self.AUTH_HEADERS,
                    data=data
            ) as response:
                result = await response.json()
                print("Response from _generate:", result)
                return result.get('uuid')

    async def _check_generation(self, request_id):
        if request_id is None:
            print("Ошибка: request_id отсутствует")
            return None

        attempts = 10
        delay = 10
        async with aiohttp.ClientSession() as session:
            while attempts > 0:
                async with session.get(self.URL + 'key/api/v1/text2image/status/' + request_id,
                                    headers=self.AUTH_HEADERS) as response:
                    data = await response.json()
                    if data['status'] == 'DONE':
                        return data['images']
                    attempts -= 1
                    await asyncio.sleep(delay)
        return None

    async def _save_image(self, image_base64, file_path):
        image_data = base64.b64decode(image_base64)
        with open(file_path, 'wb') as f:
            f.write(image_data)

    async def generate_image(self, prompt, style, dimensions, file_path):
        model_id = await self._get_model_id()
        uuid = await self._generate(prompt, model_id, style, dimensions)
        images = await self._check_generation(uuid)
        if images:
            await self._save_image(images[0], file_path)
        else:
            print("Ошибка при генерации изображения.")
            return None


async def main():
    TEXT2IMAGE_API_URL = "https://api-key.fusionbrain.ai/"
    TEXT2IMAGE_API_KEY = "FF937D741D2A949547451AF874BAC4F5"
    TEXT2IMAGE_SECRET_KEY = "EC234CAFE1250C7BEFBF7AFADA8C8C1C"

    text2image_api = Text2ImageAPI(TEXT2IMAGE_API_URL, TEXT2IMAGE_API_KEY, TEXT2IMAGE_SECRET_KEY)

    prompt = "Лиса"
    style = 2 # 1 = UHD | 2 = Anime
    dimensions = "1080x1920" # любое не прившающие 3к пикселей в сумме
    file_path = "output_image.png"

    await text2image_api.generate_image(prompt, style, dimensions, file_path)
    print("ok")
