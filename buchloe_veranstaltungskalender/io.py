import json
from datetime import datetime
from pathlib import Path

from .models import Event


async def load_events(directory: Path) -> list[Event]:
    """Load events from the latest JSON file in the data directory"""
    files = list(directory.glob("*.json"))
    if not files:
        # Return empty list if no previous events exist
        return []

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


async def save_events(events: list[Event], directory: Path):
    """Save events to a new JSON file"""
    if not events:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"processed_events_{timestamp}.json"
    directory.mkdir(parents=True, exist_ok=True)

    with (directory / filename).open("w", encoding="utf-8") as f:
        json.dump(
            [event.model_dump(mode="json") for event in events],
            f,
            ensure_ascii=False,
            indent=4,
        )
