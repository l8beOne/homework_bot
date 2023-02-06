class HtppError(Exception):
    """Ошибка: соединения."""

    pass


class EndpointError(Exception):
    """Ошибка: эндпойнт не корректен."""

    pass


class IncorrectFormatError(Exception):
    """Ошибка: некорректный формат ответа."""

    pass
