import sys
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import locale
import logging

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("buchloe-scraper")


def fetch_page(url):
    """
    Fetches the HTML content of the given URL.
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    return None


def parse_events_from_page(content):
    """
    Parses the HTML content of a page and returns a list of events.
    """
    soup = BeautifulSoup(content, "html.parser")
    articles = soup.find_all("article")
    events = []

    for article in articles:
        event = parse_event(article)
        if event:
            logger.info(f"Found event: {event}")
            events.append(event)
    return events


def parse_event(article):
    """
    Parses a single event article and extracts event data.
    """
    # Extract date components
    dayname = get_text_from_element(article, "div", "dayname")
    day = get_text_from_element(article, "div", "day")
    month = get_text_from_element(article, "div", "month").strip(".")
    year = get_text_from_element(article, "div", "year")

    event_date_iso = parse_date(dayname, day, month, year)

    # Extract title
    title_element = article.find("h2")
    title = title_element.get_text(strip=True) if title_element else None

    # Extract and parse time
    time_div = article.find("div", class_="time")
    time_ranges = parse_time(time_div.get_text(strip=True)) if time_div else None

    # Extract location
    location_div = article.find("div", class_="location")
    location_text = (
        parse_location(location_div.get_text(strip=True)) if location_div else None
    )

    if not title or not event_date_iso:
        return None  # Essential information is missing

    event = {
        "title": title,
        "date": event_date_iso,
    }

    if time_ranges:
        event.update(time_ranges)

    if location_text:
        event["location"] = location_text

    return event


def get_text_from_element(parent, tag, class_name):
    """
    Helper function to get text from an HTML element.
    """
    element = parent.find(tag, class_=class_name)
    return element.get_text(strip=True) if element else ""


def parse_date(dayname, day, month, year):
    """
    Parses date components and returns a date string in ISO format.
    """
    date_str = f"{dayname} {day} {month} {year}"
    try:
        # Set locale for German month names
        set_german_locale()
        event_date = datetime.strptime(date_str, "%A %d %b %Y")
        return event_date.strftime("%Y-%m-%d")
    except ValueError:
        return None


def set_german_locale():
    """
    Sets the locale to German for date parsing.
    """
    try:
        locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, "deu")
        except locale.Error:
            locale.setlocale(locale.LC_TIME, "German_Germany")


def parse_time(time_text):
    """
    Parses the time text and returns a dictionary with start and end times in ISO 8601 format.
    """
    time_text = time_text.replace("Uhrzeit:", "").strip()
    if "bis" in time_text:
        start_time_str, end_time_str = [t.strip() for t in time_text.split("bis")]
    else:
        start_time_str = time_text.strip()
        end_time_str = None

    start_time_iso = parse_time_string(start_time_str)
    end_time_iso = parse_time_string(end_time_str) if end_time_str else None

    time_data = {}
    if start_time_iso:
        time_data["start_time"] = start_time_iso
    if end_time_iso:
        time_data["end_time"] = end_time_iso

    return time_data if time_data else None


def parse_time_string(time_str):
    """
    Parses a time string and returns time in ISO 8601 format.
    """
    if not time_str:
        return None

    time_str = time_str.replace("Uhr", "").strip()
    time_formats = ["%H:%M", "%H"]

    for time_format in time_formats:
        try:
            time_obj = datetime.strptime(time_str, time_format).time()
            return time_obj.strftime("%H:%M:%S")
        except ValueError:
            continue
    return None


def parse_location(location_text):
    """
    Cleans up the location text by removing unnecessary labels.
    """
    return location_text.replace("Veranstaltungsort:", "").strip()


def scrape_events():
    """
    Orchestrates the scraping process and returns all events.
    """
    base_url = "https://www.buchloe.de/freizeit-tourismus/veranstaltungen/seite/"
    page_num = 1
    all_events = []
    previous_events = None

    while True:
        logger.info(f"Scraping page {page_num}...")
        url = f"{base_url}{page_num}/"
        content = fetch_page(url)

        if not content:
            break

        events = parse_events_from_page(content)
        if not events:
            break  # No more events found

        if events == previous_events:
            logger.info(
                "Buchloe's pagination is trolling us 🤡 by repeating the same page. Let's stop here."
            )
            break

        previous_events = events

        all_events.extend(events)
        page_num += 1

    return all_events


if __name__ == "__main__":
    events = scrape_events()
    print(json.dumps(events, ensure_ascii=False, indent=4))
