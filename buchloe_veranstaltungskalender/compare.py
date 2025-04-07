import os
import json
from datetime import datetime


def read_last_two_json_files(directory):
    """
    Reads the last two JSON files from the specified directory.
    """
    # Get list of all JSON files in the directory
    files = [f for f in os.listdir(directory) if f.endswith(".json")]
    if len(files) < 2:
        raise Exception("Not enough JSON files in the directory to compare.")
    # Sort files by modification time
    files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)))
    # Get the last two files
    last_file = files[-1]
    second_last_file = files[-2]
    # Read the files
    with open(os.path.join(directory, second_last_file), "r", encoding="utf-8") as f:
        previous_events = json.load(f)
    with open(os.path.join(directory, last_file), "r", encoding="utf-8") as f:
        current_events = json.load(f)
    return previous_events, current_events


def event_key(event):
    """
    Creates a unique identifier for an event based on its key attributes.
    """
    return (
        event.get("title"),
        event.get("date"),
        event.get("start_time"),
        event.get("end_time"),
        event.get("location"),
    )


def is_event_in_past(event):
    """
    Checks if the event date is in the past.
    """
    event_date_str = event.get("date")
    if not event_date_str:
        return False  # If no date is provided, consider it not in the past
    try:
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        return event_date < today
    except ValueError:
        return False  # If date parsing fails, consider it not in the past


def compare_events(previous_events, current_events):
    """
    Compares previous and current events to find new and removed events.
    """
    # Build sets of event keys
    previous_event_keys = set(event_key(event) for event in previous_events)
    current_event_keys = set(event_key(event) for event in current_events)
    # New events are in current but not in previous
    new_events_keys = current_event_keys - previous_event_keys
    new_events = [
        event for event in current_events if event_key(event) in new_events_keys
    ]
    # Removed events are in previous but not in current
    removed_events_keys = previous_event_keys - current_event_keys
    removed_events = [
        event for event in previous_events if event_key(event) in removed_events_keys
    ]
    # Filter removed events to those not in the past
    removed_events_future = [
        event for event in removed_events if not is_event_in_past(event)
    ]
    return new_events, removed_events_future


def main():
    directory = "data"  # Adjust the directory path if needed
    try:
        previous_events, current_events = read_last_two_json_files(directory)
    except Exception as e:
        print(str(e))
        return
    new_events, removed_events = compare_events(previous_events, current_events)
    if new_events:
        print("New events added since last scrape:")
        for event in new_events:
            print(json.dumps(event, ensure_ascii=False, indent=4))
    else:
        print("No new events since last scrape.")
    if removed_events:
        print("\nEvents removed since last scrape (that are not in the past):")
        for event in removed_events:
            print(json.dumps(event, ensure_ascii=False, indent=4))
    else:
        print("\nNo events removed since last scrape (that are not in the past).")


if __name__ == "__main__":
    main()
