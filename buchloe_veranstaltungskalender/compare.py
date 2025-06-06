import logging

from .logging_config import get_logger, setup_logging
from .models import Event

# Initialize logging configuration
setup_logging(level=logging.INFO)
logger = get_logger(__name__)


async def deduplicate_events(events: list[Event]) -> list[Event]:
    """Remove duplicate events based on key attributes"""
    seen = set()
    unique_events = []

    for event in events:
        event_key = get_event_key(event)
        if event_key not in seen:
            seen.add(event_key)
            unique_events.append(event)

    return unique_events


async def compare_events(
    new_events: list[Event], previous_events: list[Event]
) -> tuple[list[Event], list[Event]]:
    """Compare new events with previous events to find differences"""

    new_keys = {get_event_key(e): e for e in new_events}
    previous_keys = {get_event_key(e): e for e in previous_events}

    # Find new events (keys in new but not in previous)
    new_events_list = [e for k, e in new_keys.items() if k not in previous_keys]
    # Find removed events (keys in previous but not in new)
    removed_events_list = [e for k, e in previous_keys.items() if k not in new_keys]

    return new_events_list, removed_events_list


def get_event_key(event: Event) -> tuple:
    return (
        event.title,
        event.start.isoformat(),
        event.end.isoformat(),
        event.location,
    )
