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


def check_tokens():
    """Проверка токенов."""
    TOKEN_LIST = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    for token_name in TOKEN_LIST:
        if globals()[token_name]:
            return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))
        else:
            logging.critical('Токен недоступен')
            sys.exit('Работа бота не осуществляется')


def send_message(bot, message):
    """Бот отправляет сообщение в чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Попытка отправки сообщения', exc_info=True)
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
            f'Формат ответа не json: {error}'
        )


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        message = 'Ответ API не соответствует формату'
        logging.error(message)
        raise TypeError(message)
    if 'homeworks' not in response:
        message = 'Осутствуют ожидаемые ключи'
        raise TypeError(message)
    if 'current_date' not in response:
        message = 'Осутствуют ожидаемые ключи'
        raise TypeError(message)
    if not isinstance(response.get('homeworks'), list):
        message = 'Формат ответа не соответствует'
        raise TypeError(message)
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус."""
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует имя домашней работы.')
    if 'status' not in homework:
        raise KeyError('Отсутствует статус проверки.')
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
    logging.info('Бот работает')
    try:
        if check_tokens():
            bot = telegram.Bot(token=TELEGRAM_TOKEN)
    except Exception:
        logging.critical('Переменные окружения отсутствуют')
        sys.exit('Программа остановлена')
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
                logging.debug('Нет заданий для проверки')
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
