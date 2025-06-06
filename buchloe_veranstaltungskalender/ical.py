"""iCal generation module for Buchloe events

This module handles the conversion of Event objects to iCal format
for calendar subscription and import functionality.
"""

import logging
from datetime import date, datetime
from pathlib import Path

import pytz  # type: ignore
from icalendar import Calendar  # type: ignore
from icalendar import Event as ICalEvent

from .ical_formatter import (
    format_ical_content,
    format_property_value,
    preprocess_description,
)
from .logging_config import get_logger, setup_logging
from .models import Event

# Initialize logging configuration
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

# Timezone for Buchloe, Germany
BUCHLOE_TZ = pytz.timezone("Europe/Berlin")


async def generate_ical(events: list[Event]) -> bytes:
    """Generate iCal calendar from events

    Args:
        events: List of Event objects to convert

    Returns:
        iCal calendar data as bytes
    """
    cal = Calendar()

    # Calendar metadata
    cal.add("prodid", "-//Buchloe//Veranstaltungskalender//DE")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", "Buchloe Veranstaltungskalender")
    cal.add("x-wr-caldesc", "Veranstaltungen der Stadt Buchloe")
    cal.add("x-wr-timezone", "Europe/Berlin")

    for event in events:
        # Preprocess event data for better formatting
        processed_event = Event(
            title=format_property_value("SUMMARY", event.title),
            start=event.start,
            end=event.end,
            location=format_property_value("LOCATION", event.location),
            description=preprocess_description(event.description or ""),
            url=event.url,
        )
        ical_event = await _convert_event_to_ical(processed_event)
        cal.add_component(ical_event)

    # Generate raw iCal and apply custom formatting
    raw_ical = cal.to_ical()
    formatted_ical = format_ical_content(raw_ical)

    logger.info(f"Generated formatted iCal with {len(events)} events")
    return formatted_ical


async def _convert_event_to_ical(event: Event) -> ICalEvent:
    """Convert a single Event to iCal format

    Args:
        event: Event object to convert

    Returns:
        iCal Event component
    """
    ical_event = ICalEvent()

    # Generate unique ID for the event
    event_id = f"{hash(f'{event.title}{event.start}{event.location}')}@buchloe.de"
    ical_event.add("uid", event_id)

    # Basic event information
    ical_event.add("summary", event.title)
    ical_event.add("description", event.description or "")
    ical_event.add("location", event.location)

    # Handle datetime vs date objects
    start_dt = _ensure_timezone_aware(event.start)
    end_dt = _ensure_timezone_aware(event.end)

    ical_event.add("dtstart", start_dt)
    ical_event.add("dtend", end_dt)

    # Metadata
    ical_event.add("dtstamp", datetime.now(BUCHLOE_TZ))
    ical_event.add("created", datetime.now(BUCHLOE_TZ))
    ical_event.add("last-modified", datetime.now(BUCHLOE_TZ))

    # Add URL if available
    if event.url:
        ical_event.add("url", event.url)

    # Classification
    ical_event.add("class", "PUBLIC")
    ical_event.add("status", "CONFIRMED")

    return ical_event


def _ensure_timezone_aware(dt: date | datetime) -> datetime:
    """Ensure datetime object is timezone-aware

    Args:
        dt: datetime or date object

    Returns:
        Timezone-aware datetime object
    """
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            # Assume local timezone (Buchloe)
            return BUCHLOE_TZ.localize(dt)  # type: ignore
        return dt
    else:  # It's a date
        # Convert to datetime at midnight in local timezone
        dt_obj = datetime.combine(dt, datetime.min.time())
        return BUCHLOE_TZ.localize(dt_obj)  # type: ignore


async def save_ical_file(events: list[Event], output_path: Path) -> None:
    """Save events as iCal file

    Args:
        events: List of Event objects to save
        output_path: Path where to save the iCal file
    """
    if not events:
        logger.warning("No events to save to iCal file")
        return

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate iCal data
    ical_data = await generate_ical(events)

    # Write to file
    with output_path.open("wb") as f:
        f.write(ical_data)

    logger.info(f"Saved {len(events)} events to {output_path}")


async def save_public_ical(events: list[Event], data_dir: Path) -> Path:
    """Save iCal file for public access (GitHub Pages)

    Args:
        events: List of Event objects to save
        data_dir: Base data directory

    Returns:
        Path to the saved public iCal file
    """
    public_dir = data_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)

    # Use a consistent filename for public access
    public_ical_path = public_dir / "events.ics"

    await save_ical_file(events, public_ical_path)

    return public_ical_path
