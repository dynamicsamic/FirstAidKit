from datetime import datetime

from settings import settings


def now():
    return datetime.now(tz=settings.TZ)
