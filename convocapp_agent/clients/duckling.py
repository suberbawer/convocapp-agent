import os
import requests


def parse_date_duckling(text: str, locale: str = "en_EN", tz: str = "America/Montevideo") -> str:
    url = os.getenv("DUCKLING_URL")
    print("Calling Duckling...", url)
    payload = {"text": text, "locale": locale, "tz": tz, "dims": '["time"]'}

    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        return __extract_duckling_datetime(response.json())
    except requests.RequestException as e:
        raise RuntimeError(f"Error parsing date using Duckling: {e}")


def __extract_duckling_datetime(response: list[dict]) -> str | None:
    day = None
    for item in response:
        if item.get("dim") == "time" and "value" in item:
            value: dict = item["value"]
            values: list[dict] = value.get("values", [])
            for val in values:
                if val.get("grain") == "day" and not day:
                    entire_date: str = val["value"]
                    day = entire_date.split("T")[0]  # keeping the first hit
                if val.get("grain") == "hour":
                    entire_hour: str = val["value"]
                    hour = entire_hour.split("T")[1]
                    return f"{day}T{hour}" if day else entire_hour

    return entire_date or response[0]["value"]
