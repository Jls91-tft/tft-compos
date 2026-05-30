"""Caché simple en memoria con TTL.

Las partidas terminadas son inmutables → se cachean mucho tiempo. El historial
cambia poco → TTL corto. En producción esto podría ir a Redis/SQLite; para
empezar, un diccionario en memoria es suficiente.
"""
import time


class TTLCache:
    def __init__(self) -> None:
        self._store: dict = {}

    def get(self, key):
        item = self._store.get(key)
        if not item:
            return None
        value, expires = item
        if expires is not None and time.time() > expires:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key, value, ttl: float | None = None) -> None:
        expires = time.time() + ttl if ttl else None
        self._store[key] = (value, expires)
