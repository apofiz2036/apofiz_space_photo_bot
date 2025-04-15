import os
import time
import requests
import telegram
from dotenv import load_dotenv


def get_nasa_photo(NASA_API_URL, NASA_TOKEN):
    params = {'api_key': NASA_TOKEN, 'count': 1}
    response = requests.get(NASA_API_URL, params=params)
    response.raise_for_status()

    return response.json()[0]['url']


def download_and_send_photo(bot, nasa_api_url, nasa_token, error_chat_id):
    try:
        photo_url = get_nasa_photo(nasa_api_url, nasa_token)
        photo_data = requests.get(photo_url).content

        updates = bot.get_updates()
        chat_ids = {update.message.chat.id for update in updates if update.message}
        for chat_id in chat_ids:
            bot.send_photo(chat_id=chat_id, photo=photo_data)
    except Exception as e:
        bot.send_message(chat_id=error_chat_id, text=f"Произошла ошибка: {e}")


def main():
    load_dotenv()

    NASA_API_URL = 'https://api.nasa.gov/planetary/apod'
    TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
    NASA_TOKEN = os.environ['NASA_TOKEN']
    ERROR_CHAT_ID = os.environ['TELEGRAM_ERROR_CHAT_ID']
    SLEEP_TIME = 30  # 6 * 60 * 60

    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    while True:
        download_and_send_photo(
            bot=bot,
            nasa_api_url=NASA_API_URL,
            nasa_token=NASA_TOKEN,
            error_chat_id=ERROR_CHAT_ID)
        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()
