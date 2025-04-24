from typing import Optional
from dateutil import parser
from datetime import timezone

from clients.duckling import parse_date_duckling


def parse_nlp_datetime(text: str, locale: str = "en_EN", tz: str = "America/Montevideo") -> Optional[str]:
    date_string = parse_date_duckling(text, locale, tz)
    return convert_utc(date_string)


def convert_utc(date_str: str):
    dt = parser.isoparse(date_str)
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.isoformat()
