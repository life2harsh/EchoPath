from __future__ import annotations

from functools import lru_cache

from .config import get_settings
from .repository import Repository


@lru_cache(maxsize=1)
def get_repository() -> Repository:
    return Repository(get_settings())
