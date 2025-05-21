# Telegram AI Bot (g4f, Flux, Kandinsky)

Телеграм-бот для генерации текста и изображений с использованием нейросетей (g4f, Flux, Kandinsky) и поддержкой прокси.

---

## Возможности

- Генерация текста с помощью различных моделей (GPT-4o, DeepSeek, Llama и др.)
- Генерация изображений через Flux и Kandinsky
- Перевод промта для генерации изображений
- История диалога и выбор модели для пользователя
- Поддержка работы через HTTP-прокси (автоматическая смена при лимитах)
- SQLite база для хранения истории и настроек

---

## Установка

1. **Клонируйте репозиторий:**
   ```
   git clone <repo-url>
   cd Tg-g4f-main
   ```

2. **Установите зависимости:**
   ```
   pip install aiogram g4f googletrans aiohttp 
   ```
   Основные библиотеки:  
   - aiogram
   - g4f
   - googletrans
   - aiohttp
   - sqlite3 (стандартная)

3. **Настройте переменные:**
   - В файле `main.py` укажите токен Telegram-бота (`TOKEN`)
   - Для генерации изображений через Kandinsky укажите ключи API и URL в `main.py` и `image_gen_kandinsky.py`


## Запуск

```bash
python main.py
```

---

## Структура проекта

- `main.py` — основной файл, запуск бота, роутинг, обработка команд, интеграция прокси
- `text_handlers.py` — обработка текстовых сообщений, генерация ответов через g4f
- `image_handlers.py` — генерация изображений через Flux (g4f)
- `bot.db` — база данных SQLite (создаётся автоматически)
- `README.md` — документация

---


## Основные функции

- **/start** — запуск и регистрация пользователя
- **/menu** — главное меню
- **/help** — справка по командам
- **/delete_history** — очистка истории диалога
- **/history** — просмотр истории диалога
- **Выбрать модель 🤖** — выбор модели для текста или изображений

---

## Пример использования

- Отправьте текст — получите ответ от выбранной модели
- Выберите модель Flux — отправьте описание, получите сгенерированное изображение

---

## Авторы

- baldiczxc

---

## Лицензия

MIT (или ваша лицензия)

---

# Telegram AI Bot (g4f, Flux, Kandinsky) [EN]

Telegram bot for text and image generation using neural networks (g4f, Flux, Kandinsky) with proxy support.

---

## Features

- Text generation with various models (GPT-4o, DeepSeek, Llama, etc.)
- Image generation via Flux and Kandinsky
- Prompt translation for image generation
- Dialog history and per-user model selection
- HTTP proxy support (automatic switching on limits)
- SQLite database for history and settings

---

## Installation

1. **Clone the repository:**
   ```
   git clone <repo-url>
   cd Tg-g4f-main
   ```

2. **Install dependencies:**
   ```
   pip install aiogram g4f googletrans aiohttp 
   ```
   Main libraries:  
   - aiogram
   - g4f
   - googletrans
   - aiohttp
   - sqlite3 (builtin)

3. **Configure variables:**
   - Set your Telegram bot token (`TOKEN`) in `main.py`
   - For Kandinsky image generation, set API keys and URL in `main.py` and `image_gen_kandinsky.py`


## Run

```bash
python main.py
```

---

## Project structure

- `main.py` — main file, bot startup, routing, command handling, proxy integration
- `text_handlers.py` — text message handling, g4f response generation
- `image_handlers.py` — image generation via Flux (g4f)
- `bot.db` — SQLite database (auto-created)
- `README.md` — documentation

---


## Main commands

- **/start** — start and register user
- **/menu** — main menu
- **/help** — command help
- **/delete_history** — clear dialog history
- **/history** — view dialog history
- **Выбрать модель 🤖** — choose model for text or images

---



## Usage example

- Send text — get a response from the selected model
- Select Flux model — send a description, get a generated image

---

## Authors

- baldiczxc

---

## License

MIT (or your license)

