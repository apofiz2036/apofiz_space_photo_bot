import os
import time
import requests
import logging
import telegram
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler


class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def save_chat_id(chat_id):
    with open('chat_ids.txt', 'a+') as f:
        f.seek(0)
        saved_ids = f.read()
        if str(chat_id) not in saved_ids:
            f.write(f"{chat_id}\n")


def load_chat_ids():
    try:
        with open('chat_ids.txt', 'r') as f:
            return [int(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        return []


def translate(text, yandex_translate_key):
    try:
        url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
        headers = {
            "Authorization": f"Api-Key {yandex_translate_key}",
            "Content-Type": "application/json"
        }
        data = {
            "targetLanguageCode": "ru",
            "texts": [text]
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        return response.json()["translations"][0]["text"]
    except Exception:
        return text


def get_nasa_apod_data(nasa_api_url, nasa_token, error_chat_id, bot, logger):
    try:
        params = {'api_key': nasa_token, 'count': 1}
        response = requests.get(nasa_api_url, params=params)
        response.raise_for_status()

        data = response.json()[0]

        return {
            'url': data['url'],
            'title': data['title'],
            'explanation': data['explanation'],
            'date': data['date']
        }
    except Exception as e:
        bot.send_message(chat_id=error_chat_id, text=f"Ошибка NASA API: {e}")
        logger.error(f"Ошибка: {str(e)}")
        return None


def download_and_send_photo(bot, nasa_api_url, nasa_token, error_chat_id, yandex_translate_key, logger):
    try:
        apod_data = get_nasa_apod_data(nasa_api_url, nasa_token, error_chat_id, bot, logger)
        photo_url = apod_data['url']
        title = apod_data['title']
        explanation = apod_data['explanation']
        date = apod_data['date']

        photo_data = requests.get(photo_url).content

        saved_chat_ids = load_chat_ids()
        updates = bot.get_updates()
        new_chat_ids = {update.message.chat.id for update in updates if update.message}
        chat_ids = set(saved_chat_ids).union(new_chat_ids)

        for chat_id in new_chat_ids:
            save_chat_id(chat_id)

        text = f'📅 {date}\n\n🔭 {title}\n\nℹ️ {explanation}'
        translated_text = translate(text, yandex_translate_key)
        for chat_id in chat_ids:
            bot.send_photo(chat_id=chat_id, photo=photo_data)
            bot.send_message(chat_id=chat_id, text=translated_text)
    except Exception as e:
        bot.send_message(chat_id=error_chat_id, text=f"Произошла ошибка: {e}")
        logger.error(f"Ошибка: {str(e)}")
        return


def main():
    load_dotenv()

    NASA_API_URL = 'https://api.nasa.gov/planetary/apod'
    TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
    NASA_TOKEN = os.environ['NASA_TOKEN']
    ERROR_CHAT_ID = os.environ['TELEGRAM_ERROR_CHAT_ID']
    YANDEX_TRANSLATE_KEY = os.environ['YANDEX_TRANSLATE_KEY']
    TIMER = os.environ['TIMER']
    SLEEP_TIME = int(TIMER) * 60 * 60

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler = RotatingFileHandler(
        'nasa_bot.log',
        maxBytes=1024 * 1024,
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("Бот запущен")

    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    telegram_handler = TelegramLogsHandler(bot, ERROR_CHAT_ID)
    telegram_handler.setFormatter(formatter)
    logger.addHandler(telegram_handler)

    while True:
        download_and_send_photo(
            bot=bot,
            nasa_api_url=NASA_API_URL,
            nasa_token=NASA_TOKEN,
            error_chat_id=ERROR_CHAT_ID,
            yandex_translate_key=YANDEX_TRANSLATE_KEY,
            logger=logger
        )
        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()
