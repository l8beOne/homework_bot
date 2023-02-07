import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from telegram import TelegramError

from exceptions import HtppError, IncorrectFormatError

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
STATUS_OF_MESSAGE = 'Сообщение: "{message}", {my_key}'
TRY_MESSAGE = 'Попытка отправки сообщения'
UNAVAILABLE_TOKEN = 'Токен недоступен'
WORK_WAS_ENDED = 'Работа бота не осуществляется'
NOT_JSON = 'Формат ответа не json: {error}'
NOT_API_FORMAT = 'Ответ API не соответствует формату'
INAPPROPRIATE_FORMAT = 'Формат ответа не соответствует'
KEY_MISSED = 'Осутствуют ожидаемые ключи'
NAME_IS_NOT_EXIST = 'Отсутствует имя домашней работы.'
STATUS_IS_NOT_EXIST = 'Отсутствует статус проверки.'
BOT_IS_WORKING = 'Бот работает'
NO_TOKENS = 'Переменные окружения отсутствуют: {missed_tokens}'
NOTHING_TO_CHECK = 'Нет заданий для проверки'
PRACTICUM_TOKEN_ERROR = 'Токен Практикума недоступен'
TELEGRAM_TOKEN_ERROR = 'Токен телеграм бота недоступен'
TELEGRAM_CHAT_ID_ERROR = 'ID чата недоступно'


def check_tokens():
    """Проверка токенов."""
    TOKEN_LIST = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    for token_name in TOKEN_LIST:
        if globals()[token_name]:
            return token_name
        elif token_name == 'PRACTICUM_TOKEN':
            logging.critical(PRACTICUM_TOKEN_ERROR)
        elif token_name == 'TELEGRAM_TOKEN':
            logging.critical(TELEGRAM_TOKEN_ERROR)
        elif token_name == 'TELEGRAM_CHAT_ID':
            logging.critical(TELEGRAM_CHAT_ID_ERROR)


def send_message(bot, message):
    """Бот отправляет сообщение в чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(TRY_MESSAGE, exc_info=True)
    except TelegramError as error:
        logging.exception(f'Сообщение: "{message}", не отправлено.'
                          f'"{error}"', exc_info=True)
    else:
        logging.info(
            f'Сообщение: "{message}", отправлено.'
        )


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    current_timestamp = timestamp or int(time.time())
    payload = {'from_date': current_timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload
        )
    except requests.exceptions.RequestException as error:
        raise ConnectionError(
            'Ошибка соединения {error} с параметрами: '
            '{url}, {headers}, {params}'.format(
                error=error,
                url=ENDPOINT,
                headers=HEADERS,
                params=payload
            )
        )
    if response.status_code != HTTPStatus.OK:
        raise HtppError('Ошибка соединения: {status}, {text}'.format(
            status=response.status_code,
            text=response.text))
    try:
        return response.json()
    except TypeError as error:
        raise IncorrectFormatError(
            NOT_JSON.format(error=error)
        )


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        logging.error(NOT_API_FORMAT)
        raise TypeError(NOT_API_FORMAT)
    if 'homeworks' not in response:
        raise KeyError(KEY_MISSED)
    if 'current_date' not in response:
        raise KeyError(KEY_MISSED)
    if not isinstance(response.get('homeworks'), list):
        raise TypeError(INAPPROPRIATE_FORMAT)
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус."""
    if 'homework_name' not in homework:
        raise KeyError(NAME_IS_NOT_EXIST)
    if 'status' not in homework:
        raise KeyError(STATUS_IS_NOT_EXIST)
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(
            f'Неожиданный статус работы: "{status}"'
        )
    verdict = HOMEWORK_VERDICTS[status]
    homework_name = homework.get('homework_name')
    return (f'Изменился статус проверки работы "{homework_name}".'
            f'{verdict}')


def main():
    """Основная логика работы бота."""
    logging.info(BOT_IS_WORKING)
    if not check_tokens():
        logging.critical(NO_TOKENS)
        sys.exit(WORK_WAS_ENDED)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date')
            homeworks_list = check_response(response)
            if len(homeworks_list) > 0:
                homework = homeworks_list[0]
                message = parse_status(homework)
                send_message(bot, message)
            else:
                logging.debug(NOTHING_TO_CHECK)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.error(message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='program.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    main()
