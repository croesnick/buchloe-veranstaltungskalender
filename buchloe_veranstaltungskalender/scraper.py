import sys
import aiohttp
from bs4 import BeautifulSoup, Tag
import asyncio
import json
from datetime import datetime, time
import locale
import logging
from typing import Optional, Dict, List, Tuple
from .models import Event
from .logging_config import setup_logging, get_logger

# Initialize logging configuration
setup_logging(level=logging.INFO)
logger = get_logger("buchloe-scraper")


async def fetch_page(session: aiohttp.ClientSession, url: str) -> Optional[bytes]:
    """
    Fetches the HTML content of the given URL using aiohttp.
    """
    async with session.get(url) as response:
        if response.status == 200:
            return await response.read()
        return None


async def parse_events_from_page(
    content: bytes,
    session: Optional[aiohttp.ClientSession] = None,
    fetch_full_descriptions: bool = True,
) -> List[Event]:
    """
    Parses the HTML content of a page and returns a list of events.
    Enhanced to support full description fetching from detail pages.
    """
    soup = BeautifulSoup(content, "html.parser")

    # Look for <a class="article"> wrappers that contain the articles
    article_wrappers = soup.find_all("a", class_="article")

    if not article_wrappers:
        # Fallback to direct article elements for backward compatibility
        articles = soup.find_all("article")
        article_wrappers = [(None, article) for article in articles]
    else:
        # Extract (wrapper, article) pairs
        article_wrappers = [
            (wrapper, wrapper.find("article")) for wrapper in article_wrappers
        ]

    events = []
    tasks = []

    for wrapper, article in article_wrappers:
        if not article:
            continue

        # Extract event URL if wrapper is available
        event_url = extract_event_url(wrapper) if wrapper else None

        # Create task for async event parsing
        task = parse_event(
            article,
            event_url=event_url,
            session=session if fetch_full_descriptions else None,
        )
        tasks.append(task)

    # Execute all parsing tasks concurrently
    if tasks:
        events = await asyncio.gather(*tasks, return_exceptions=True)
        # Filter out None results and exceptions
        events = [event for event in events if isinstance(event, Event)]

        for event in events:
            logger.info(f"Found event: {event}")

    return events


async def parse_event(
    article: Tag,
    event_url: Optional[str] = None,
    session: Optional[aiohttp.ClientSession] = None,
) -> Optional[Event]:
    """
    Parses a single event article and extracts event data.
    Enhanced to handle 'Noch bis' date patterns, description extraction,
    and full description fetching from detail pages.
    """
    logger.debug("Parsing article", extra={"article": str(article)})

    # Extract date components using enhanced logic
    date_components = extract_date_components(article)
    event_date = parse_date_with_pattern(date_components)

    # Extract title
    title_element = article.find("h2")
    title = title_element.get_text(strip=True) if title_element else None

    # Extract and parse time
    time_div = article.find("div", class_="time")
    time_ranges = parse_time(time_div.get_text(strip=True)) if time_div else {}

    # Extract location
    location_div = article.find("div", class_="location")
    location_text = (
        parse_location(location_div.get_text(strip=True)) if location_div else None
    )

    # Extract description - try full description first, fallback to short
    description = parse_description(article)  # Short description as fallback

    if event_url and session:
        try:
            full_description = await fetch_full_description(session, event_url)
            if full_description:
                description = full_description
        except Exception as e:
            logger.warning(
                f"Failed to fetch full description, using short description",
                extra={"url": event_url, "error": str(e)},
            )

    if not title or not event_date:
        logger.warning(
            "Missing essential information for event parsing.",
            extra={
                "title": title,
                "date": event_date,
                "pattern": date_components.get("pattern", "unknown"),
                "url": event_url,
            },
        )
        return None  # Essential information is missing

    start_time = time_ranges.get("start_time")
    end_time = time_ranges.get("end_time")

    start_datetime = (
        datetime.combine(event_date, start_time) if start_time else event_date
    )
    end_datetime = datetime.combine(event_date, end_time) if end_time else event_date

    return Event(
        title=title,
        start=start_datetime,
        end=end_datetime,
        location=location_text or "",
        description=description,
        url=event_url or "",
    )


def parse_event_sync(article: Tag) -> Optional[Event]:
    """
    Synchronous wrapper for parse_event for backward compatibility.
    This version does not fetch full descriptions from detail pages.
    """
    import asyncio

    # Create a new event loop if none exists
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Run the async function without session (no full description fetching)
    return loop.run_until_complete(parse_event(article, event_url=None, session=None))


def detect_date_pattern(article: Tag) -> str:
    """
    Detects the date pattern in the article element.

    Returns:
        "noch_bis" if the event has "Noch bis" pattern
        "normal" for standard date patterns
        "unknown" if pattern cannot be determined
    """
    still_element = article.find("div", class_="still")
    if still_element and "noch bis" in still_element.get_text(strip=True).lower():
        return "noch_bis"

    # Check if we have the basic date structure
    dayname = article.find("div", class_="dayname")
    day = article.find("div", class_="day")
    month = article.find("div", class_="month")
    year = article.find("div", class_="year")

    if dayname and day and month and year:
        return "normal"

    return "unknown"


def extract_date_components(article: Tag) -> Dict[str, str]:
    """
    Extracts date components from the article element.

    Returns:
        Dictionary with dayname, day, month, year, and pattern
    """
    pattern = detect_date_pattern(article)

    return {
        "dayname": get_text_from_element(article, "div", "dayname"),
        "day": get_text_from_element(article, "div", "day"),
        "month": get_text_from_element(article, "div", "month").strip("."),
        "year": get_text_from_element(article, "div", "year"),
        "pattern": pattern,
    }


def parse_date_with_pattern(components: Dict[str, str]) -> Optional[datetime]:
    """
    Parses date components considering the detected pattern.

    Args:
        components: Dictionary with date components and pattern

    Returns:
        Parsed datetime object or None if parsing fails
    """
    dayname = components.get("dayname", "")
    day = components.get("day", "")
    month = components.get("month", "")
    year = components.get("year", "")
    pattern = components.get("pattern", "normal")

    if not all([dayname, day, month, year]):
        logger.warning(
            "Missing date components",
            extra={
                "dayname": dayname,
                "day": day,
                "month": month,
                "year": year,
                "pattern": pattern,
            },
        )
        return None

    # Map German month names to numbers for more robust parsing
    german_months = {
        "jan": 1,
        "januar": 1,
        "feb": 2,
        "februar": 2,
        "mär": 3,
        "märz": 3,
        "mar": 3,
        "apr": 4,
        "april": 4,
        "mai": 5,
        "may": 5,
        "jun": 6,
        "juni": 6,
        "jul": 7,
        "juli": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "okt": 10,
        "oktober": 10,
        "nov": 11,
        "november": 11,
        "dez": 12,
        "dezember": 12,
    }

    # Try to parse using month mapping first
    month_lower = month.lower().strip(".")
    month_num = german_months.get(month_lower)

    if month_num:
        try:
            parsed_date = datetime(int(year), month_num, int(day))

            if pattern == "noch_bis":
                logger.info(f"Parsed 'Noch bis' date: {parsed_date}")

            return parsed_date
        except ValueError as e:
            logger.warning(
                f"Failed to parse date with month mapping: {day}/{month_num}/{year}",
                extra={"error": str(e), "pattern": pattern},
            )

    # Fallback to original locale-based parsing
    date_str = f"{dayname} {day} {month} {year}"
    try:
        set_german_locale()
        parsed_date = datetime.strptime(date_str, "%A %d %b %Y")

        if pattern == "noch_bis":
            logger.info(f"Parsed 'Noch bis' date: {parsed_date}")

        return parsed_date
    except ValueError as e:
        logger.warning(
            f"Failed to parse date: {date_str}",
            extra={"error": str(e), "pattern": pattern},
        )
        return None


def parse_description(article: Tag) -> str:
    """
    Extracts and cleans description text from the article element.

    Args:
        article: BeautifulSoup Tag element containing the event article

    Returns:
        Cleaned description text or empty string if not found
    """
    description_div = article.find("div", class_="description")
    if not description_div:
        return ""

    text = description_div.get_text(strip=True)
    # Remove "Beschreibung:" label
    cleaned_text = text.replace("Beschreibung:", "").strip()

    logger.debug(f"Extracted description: {cleaned_text[:100]}...")
    return cleaned_text


def extract_event_url(article_wrapper: Tag) -> Optional[str]:
    """
    Extrahiert die Event-URL aus dem <a> Wrapper-Element.

    Args:
        article_wrapper: BeautifulSoup Tag für <a class="article">

    Returns:
        Absolute URL zur Event-Detail-Seite oder None
    """
    if not article_wrapper or article_wrapper.name != "a":
        return None

    href = article_wrapper.get("href")
    if not href:
        return None

    # Convert relative URL to absolute URL
    base_url = "https://www.buchloe.de"
    if href.startswith("/"):
        return f"{base_url}{href}"
    elif href.startswith("http"):
        return href
    else:
        return f"{base_url}/{href}"


def parse_contenttable(soup: BeautifulSoup) -> str:
    """
    Extrahiert den Text aus der contenttable.

    Args:
        soup: BeautifulSoup-Objekt der Detail-Seite

    Returns:
        Bereinigter Beschreibungstext
    """
    contenttable = soup.find("table", class_="contenttable")
    if not contenttable:
        return ""

    # Extract all text from spans within the table
    spans = contenttable.find_all("span")
    if not spans:
        # Fallback: get all text from the table
        return contenttable.get_text(strip=True)

    # Combine text from all spans, preserving paragraph breaks
    description_parts = []
    for span in spans:
        text = span.get_text(strip=True)
        if text:
            description_parts.append(text)

    # Join with double newlines to preserve paragraph structure
    full_description = "\n\n".join(description_parts)

    logger.debug(f"Extracted full description: {full_description[:100]}...")
    return full_description


async def fetch_full_description(
    session: aiohttp.ClientSession, event_url: str
) -> Optional[str]:
    """
    Ruft die vollständige Beschreibung von der Event-Detail-Seite ab.

    Args:
        session: aiohttp ClientSession für HTTP-Requests
        event_url: URL zur Event-Detail-Seite

    Returns:
        Vollständige Beschreibung oder None bei Fehlern
    """
    try:
        async with session.get(event_url, timeout=10.0) as response:
            if response.status != 200:
                logger.warning(
                    f"Failed to fetch event detail page: HTTP {response.status}",
                    extra={"url": event_url},
                )
                return None

            content = await response.read()
            soup = BeautifulSoup(content, "html.parser")

            full_description = parse_contenttable(soup)
            if full_description:
                logger.info(f"Successfully fetched full description from {event_url}")
                return full_description
            else:
                logger.warning(
                    f"No contenttable found on detail page", extra={"url": event_url}
                )
                return None

    except asyncio.TimeoutError:
        logger.warning(
            f"Timeout while fetching event detail page", extra={"url": event_url}
        )
        return None
    except Exception as e:
        logger.warning(
            f"Error fetching event detail page: {str(e)}",
            extra={"url": event_url, "error": str(e)},
        )
        return None


def get_text_from_element(parent: Tag, tag: str, class_name: str) -> str:
    """
    Helper function to get text from an HTML element.
    """
    element = parent.find(tag, class_=class_name)
    return element.get_text(strip=True) if element else ""


def parse_date(
    dayname: str, day: str, month: str, year: str, pattern: str = "normal"
) -> Optional[datetime]:
    """
    Parses date components and returns a datetime object.
    Maintained for backward compatibility.

    Args:
        dayname: Day name (e.g., "Sonntag")
        day: Day number (e.g., "14")
        month: Month name (e.g., "Sept")
        year: Year (e.g., "2025")
        pattern: Date pattern type ("normal" or "noch_bis")
    """
    components = {
        "dayname": dayname,
        "day": day,
        "month": month.strip("."),
        "year": year,
        "pattern": pattern,
    }
    return parse_date_with_pattern(components)


def set_german_locale() -> None:
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


def parse_time(time_text: str) -> Optional[Dict[str, time]]:
    """
    Parses the time text and returns a dictionary with start and end times as time objects.
    """
    time_text = time_text.replace("Uhrzeit:", "").strip()
    if "bis" in time_text:
        start_time_str, end_time_str = [t.strip() for t in time_text.split("bis")]
    else:
        start_time_str = time_text.strip()
        end_time_str = None

    start_time_obj = parse_time_string(start_time_str)
    end_time_obj = parse_time_string(end_time_str) if end_time_str else None

    time_data = {}
    if start_time_obj:
        time_data["start_time"] = start_time_obj
    if end_time_obj:
        time_data["end_time"] = end_time_obj

    return time_data if time_data else None


def parse_time_string(time_str: Optional[str]) -> Optional[time]:
    """
    Parses a time string and returns a time object.
    """
    if not time_str:
        return None

    time_str = time_str.replace("Uhr", "").strip()
    time_formats = ["%H:%M", "%H"]

    for time_format in time_formats:
        try:
            time_obj = datetime.strptime(time_str, time_format).time()
            return time_obj
        except ValueError:
            continue
    return None


def parse_location(location_text: str) -> str:
    """
    Cleans up the location text by removing unnecessary labels.
    """
    return location_text.replace("Veranstaltungsort:", "").strip()


async def scrape_events(fetch_full_descriptions: bool = True) -> List[Event]:
    """
    Orchestrates the scraping process and returns all events.
    Enhanced to support full description fetching from detail pages.

    Args:
        fetch_full_descriptions: Whether to fetch full descriptions from detail pages
    """
    base_url = "https://www.buchloe.de/freizeit-tourismus/veranstaltungen/seite/"
    page_num = 1
    all_events = []
    previous_events = None

    async with aiohttp.ClientSession() as session:
        while True:
            logger.info(f"Scraping page {page_num}...")
            url = f"{base_url}{page_num}/"
            content = await fetch_page(session, url)

            if not content:
                break

            events = await parse_events_from_page(
                content,
                session=session,
                fetch_full_descriptions=fetch_full_descriptions,
            )
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

    async def main():
        events = await scrape_events()
        print(json.dumps(events, ensure_ascii=False, indent=4))

    asyncio.run(main())
