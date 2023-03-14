import logging
import os
import requests
import telegram


from logging import StreamHandler
from http import HTTPStatus
import time

from dotenv import load_dotenv 

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)
handler = StreamHandler()
logger.addHandler(handler)

def check_tokens():
    """docstring"""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])




def send_message(bot, message):
    """docstring"""
    try:
        message_info = f'Сообщение готово к отправке: {message}'
        logger.debug(message_info)
        bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message,
        )
        logger.debug(f'Сообщение отправлено: {message}')
    except telegram.TelegramError:
        logger.error(f'Сообщение не отправлено: {message}')


def get_api_answer(timestamp):
    """Запрос API"""
    try:
        response = requests.get(ENDPOINT, 
                            headers=HEADERS, 
                            params={'from_date':timestamp})
        status_code = response.status_code
        if status_code != HTTPStatus.OK:
            raise Exception(f' {ENDPOINT} не доступен'
                            f'код {status_code}')
        response = response.json()
        return response
        
    except requests.exceptions.RequestException as error_request:
        raise (f'Ошибка в запросе {error_request}')


def check_response(response):
    """Проверка респонса"""
    if not response:
        message = 'Ответ от API пуст.'
        logger.error(message)
        raise Exception(message)
    if not isinstance(response, dict):
        message = 'Структура данных не соответсвует ожиданиям.'
        logger.error(message)
        raise TypeError(message)
    if 'homeworks' not in response:
        raise Exception('Отсутсвует ключ homeworks')
    if not isinstance(response["homeworks"], list):
        raise TypeError('Неверный тип данных у homeworks')
    return response.get('homeworks')
    


def parse_status(homework):
    """docstring"""
    verdict =  homework.get('status')
    homework_name = homework.get('homework_name')
    if verdict not in HOMEWORK_VERDICTS:
        message = f'Неизвестный статус работы {verdict}'
        raise Exception(message)
    if verdict is None:
        raise Exception('Пустой статус')
    if homework_name is None:
        raise Exception('Отсутсвует имя работы')

    verdict = HOMEWORK_VERDICTS[verdict]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствует токен')
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    send_message(bot, 'Бот включен')
    timestamp = int(time.time())
    messages = []
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date')
            homework = check_response(response)[0]
            message = parse_status(homework)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой: {error}'
            logger.error(message)
        finally:
            time.sleep(RETRY_PERIOD)
    




if __name__ == '__main__':
    main()
