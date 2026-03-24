from __future__ import annotations

import logging
from typing import Any


class _LoggerProxy:
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    @staticmethod
    def _render(message: str, args: tuple[Any, ...], bind: dict[str, Any] | None) -> str:
        if args:
            try:
                message = message.format(*args)
            except Exception:
                message = " ".join([message, *[str(arg) for arg in args]])
        if bind:
            return f"{message} | {bind}"
        return message

    def debug(self, message: str, *args: Any, bind: dict[str, Any] | None = None, exc_info: Any = False) -> None:
        self._logger.debug(self._render(message, args, bind), exc_info=exc_info)

    def info(self, message: str, *args: Any, bind: dict[str, Any] | None = None, exc_info: Any = False) -> None:
        self._logger.info(self._render(message, args, bind), exc_info=exc_info)

    def warning(self, message: str, *args: Any, bind: dict[str, Any] | None = None, exc_info: Any = False) -> None:
        self._logger.warning(self._render(message, args, bind), exc_info=exc_info)

    def error(self, message: str, *args: Any, bind: dict[str, Any] | None = None, exc_info: Any = False) -> None:
        self._logger.error(self._render(message, args, bind), exc_info=exc_info)


def get_logger(name: str) -> _LoggerProxy:
    return _LoggerProxy(name)
