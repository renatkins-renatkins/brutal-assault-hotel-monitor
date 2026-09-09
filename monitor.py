import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HOTELS_URL = "https://brutalassault.cz/en/ac-71/hotels"
AVAILABLE_URL = HOTELS_URL + "?show=ao"
STATE_FILE = Path("state.json")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
TEST_NOTIFICATION = os.environ.get("TEST_NOTIFICATION", "").lower() == "true"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BrutalAssaultHotelMonitor/1.0; "
        "+personal accommodation availability monitor)"
    )
}

HOTEL_PATTERN = re.compile(r"\bBA\s+2027\s+Hotel\b", re.IGNORECASE)


def fetch(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def extract_2027_hotels(html, base_url):
    """Return {hotel_title: product_url} for BA 2027 hotel products."""
    soup = BeautifulSoup(html, "html.parser")
    hotels = {}

    for link in soup.find_all("a", href=True):
        title = " ".join(link.stripped_strings)
        if HOTEL_PATTERN.search(title):
            hotels[title] = urljoin(base_url, link["href"])

    return hotels


def load_state():
    if not STATE_FILE.exists():
        return {"known_hotels": {}, "available_hotels": {}}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(known_hotels, available_hotels):
    STATE_FILE.write_text(
        json.dumps(
            {
                "known_hotels": known_hotels,
                "available_hotels": available_hotels,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )


def send_notification(title, message, click_url):
    if not NTFY_TOPIC:
        raise RuntimeError(
            "NTFY_TOPIC is not set. Add it as a GitHub Actions repository secret."
        )

    response = requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": "urgent",
            "Tags": "rotating_light,hotel",
            "Click": click_url,
        },
        timeout=30,
    )
    response.raise_for_status()


def main():
    if TEST_NOTIFICATION:
        send_notification(
            "Brutal Assault monitor test",
            "Success — your BA 2027 hotel monitor can send notifications.",
            HOTELS_URL,
        )
        print("Test notification sent.")

    full_html = fetch(HOTELS_URL)
    available_html = fetch(AVAILABLE_URL)

    current_hotels = extract_2027_hotels(full_html, HOTELS_URL)
    available_hotels = extract_2027_hotels(available_html, AVAILABLE_URL)

    state = load_state()
    old_known = state.get("known_hotels", {})
    old_available = state.get("available_hotels", {})

    new_listings = {
        name: url
        for name, url in current_hotels.items()
        if name not in old_known
    }

    newly_available = {
        name: url
        for name, url in available_hotels.items()
        if name not in old_available
    }

    messages = []

    if newly_available:
        lines = ["🚨 HOTEL ROOM AVAILABLE", ""]
        for name, url in newly_available.items():
            lines.extend([name, url, ""])
        messages.append(
            (
                "BRUTAL ASSAULT HOTEL AVAILABLE",
                "\n".join(lines).strip(),
                next(iter(newly_available.values())),
            )
        )

    # A new hotel listing is useful even if it initially appears sold out.
    # Don't duplicate the alert if the same listing is already in newly_available.
    listing_only = {
        name: url
        for name, url in new_listings.items()
        if name not in newly_available
    }

    if listing_only:
        lines = ["New BA 2027 hotel listing detected:", ""]
        for name, url in listing_only.items():
            lines.extend([name, url, ""])
        messages.append(
            (
                "New Brutal Assault hotel listing",
                "\n".join(lines).strip(),
                next(iter(listing_only.values())),
            )
        )

    # Send before saving state. If notification delivery fails, the next run retries.
    for title, message, click_url in messages:
        send_notification(title, message, click_url)

    save_state(current_hotels, available_hotels)

    print(f"Found {len(current_hotels)} BA 2027 hotel listings.")
    print(f"Currently available: {len(available_hotels)}.")
    if not messages:
        print("No alert-worthy changes.")
    else:
        print(f"Sent {len(messages)} notification(s).")


if __name__ == "__main__":
    main()
