"""A tiny HTTP header container."""


class Headers:
    def __init__(self, items=None):
        self._items = dict(items or {})

    def get(self, name, default=None):
        return self._items.get(name, default)

    def __contains__(self, name):
        return name in self._items

    def set(self, name, value):
        self._items[name] = value
