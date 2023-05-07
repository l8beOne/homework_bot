# Python Telegram Bot
<h1 align="center"><img src="https://tophallclub.ru/wp-content/uploads/6/b/7/6b7ab28479760e3a47c318ae0a6af25f.gif" height="300" width="400"/></h1>

## Описание проекта:
Написал Telegram-бота, который обращается к API сервиса Практикум.Домашка и узнаёт статус домашней работы. В случае изменений статуса, уведомляет об этом личным сообщением в телеграм.
## Стек и Технологии:
* Python 3.9.10
* Telegram
## Как запустить проект:
Склонируйте репозиторий:

```
git clone git@github.com:l8beOne/homework_bot.git
```

Переходим в папку с ботом.

```
cd homework_bot
```

Установите и активируйте виртуальное окружение:

```
python -m venv venv
source venv/Scripts/activate
```

Установите зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

В консоле импортируем токены для ЯндексюПрактикум и для Телеграмм:

```
export PRACTICUM_TOKEN=<PRACTICUM_TOKEN>
export TELEGRAM_TOKEN=<TELEGRAM_TOKEN>
export CHAT_ID=<CHAT_ID>
```

Запустите проект:

```
python homework.py
```
