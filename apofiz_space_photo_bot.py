import os
import time
import requests
import telegram
from dotenv import load_dotenv


def translate(text, yandex_translate_key):
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


def get_nasa_apod_data(nasa_api_url, nasa_token):
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


def download_and_send_photo(bot, nasa_api_url, nasa_token, error_chat_id, yandex_translate_key):
    try:
        apod_data = get_nasa_apod_data(nasa_api_url, nasa_token)
        photo_url = apod_data['url']
        title = apod_data['title']
        explanation = apod_data['explanation']
        date = apod_data['date']

        photo_data = requests.get(photo_url).content

        updates = bot.get_updates()
        chat_ids = {update.message.chat.id for update in updates if update.message}
        text = f'📅 {date}\n\n🔭 {title}\n\nℹ️ {explanation}'
        translated_text = translate(text, yandex_translate_key)
        for chat_id in chat_ids:
            bot.send_photo(chat_id=chat_id, photo=photo_data)
            bot.send_message(chat_id=chat_id, text=translated_text)
    except Exception as e:
        bot.send_message(chat_id=error_chat_id, text=f"Произошла ошибка: {e}")


def main():
    load_dotenv()

    NASA_API_URL = 'https://api.nasa.gov/planetary/apod'
    TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
    NASA_TOKEN = os.environ['NASA_TOKEN']
    ERROR_CHAT_ID = os.environ['TELEGRAM_ERROR_CHAT_ID']
    YANDEX_TRANSLATE_KEY = os.environ['YANDEX_TRANSLATE_KEY']
    SLEEP_TIME = 30  # 6 * 60 * 60

    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    while True:
        download_and_send_photo(
            bot=bot,
            nasa_api_url=NASA_API_URL,
            nasa_token=NASA_TOKEN,
            error_chat_id=ERROR_CHAT_ID,
            yandex_translate_key=YANDEX_TRANSLATE_KEY
        )
        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()
