import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import sys
from typing import List
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)


class Event(BaseModel):
    title: str
    start_date: datetime
    end_date: datetime
    location: str
    description: str
    url: str

    class Config:
        frozen = True


async def load_events(directory: Path) -> List[Event]:
    """Load events from the latest JSON file in the data directory"""
    files = list(directory.glob("*.json"))
    if not files:
        raise ValueError("No JSON files found in directory")

    # Get most recent file by parsing YYYYMMDD from filename
    def get_file_date(f: Path):
        try:
            # Extract date from filename like "events_20240101.json"
            date_str = f.stem.split("_")[-1]
            return datetime.strptime(date_str, "%Y%m%d").date()
        except (ValueError, IndexError):
            return datetime.min.date()

    latest_file = max(files, key=get_file_date)

    with latest_file.open("r", encoding="utf-8") as f:
        events_data = json.load(f)

    return [Event(**event) for event in events_data]


async def deduplicate_events(events: List[Event]) -> List[Event]:
    """Remove duplicate events based on key attributes"""
    seen = set()
    unique_events = []

    for event in events:
        # Create a unique key for each event
        event_key = (
            event.title,
            event.start_date.date(),
            event.end_date.date(),
            event.location,
        )

        if event_key not in seen:
            seen.add(event_key)
            unique_events.append(event)

    return unique_events


async def compare_with_previous(
    new_events: List[Event], previous_events: List[Event]
) -> tuple[List[Event], List[Event]]:
    """Compare new events with previous events to find differences"""

    # Create lookup keys for both sets of events
    def get_event_key(event: Event) -> tuple:
        return (
            event.title,
            event.start_date.date(),
            event.end_date.date(),
            event.location,
        )

    new_keys = {get_event_key(e): e for e in new_events}
    previous_keys = {get_event_key(e): e for e in previous_events}

    # Find new events (keys in new but not in previous)
    new_events_list = [e for k, e in new_keys.items() if k not in previous_keys]
    # Find removed events (keys in previous but not in new)
    removed_events_list = [e for k, e in previous_keys.items() if k not in new_keys]

    return new_events_list, removed_events_list


async def save_events(events: List[Event], directory: str):
    """Save events to a new JSON file"""
    if not events:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"processed_events_{timestamp}.json"
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)

    with (dir_path / filename).open("w", encoding="utf-8") as f:
        json.dump(
            [event.model_dump(mode="json") for event in events],
            f,
            ensure_ascii=False,
            indent=4,
        )


async def main():
    data_dir = Path("data")
    processed_dir = str(Path(data_dir) / "processed")

    try:
        # Load and process events
        current_events = await load_events(data_dir)
        unique_events = await deduplicate_events(current_events)

        # Load previous processed events
        previous_events = await load_events(Path(processed_dir))
        new_events, removed_events = await compare_with_previous(
            unique_events, previous_events
        )

        # Save and display results
        await save_events(new_events, processed_dir)

        if new_events:
            logger.info(f"Found {len(new_events)} new events:")
            for event in new_events:
                logger.info(
                    f"- {event.title} at {event.location} on {event.start_date}"
                )
        else:
            logger.info("No new events found since last scrape.")

        if removed_events:
            logger.info(f"Found {len(removed_events)} removed events:")
            for event in removed_events:
                logger.info(
                    f"- {event.title} at {event.location} was removed (previously scheduled for {event.start_date})"
                )

    except Exception as e:
        logger.error(f"Error processing events: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
