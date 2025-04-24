import urllib.parse


def build_google_map_link(location: str) -> str:
    query = urllib.parse.quote(location)
    return f"https://www.google.com/maps/search/?api=1&query={query}"
