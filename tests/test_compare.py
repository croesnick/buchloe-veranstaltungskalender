import pytest
from pathlib import Path
from datetime import datetime, timedelta
import json
from buchloe_veranstaltungskalender.compare import (
    Event,
    load_events,
    deduplicate_events,
    compare_with_previous,
    save_events,
)


@pytest.fixture
def temp_data_dir(tmp_path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_events():
    now = datetime.now()
    return [
        Event(
            title="Concert",
            start_date=now + timedelta(days=1),
            end_date=now + timedelta(days=1, hours=2),
            location="Town Hall",
            description="Music event",
            url="http://example.com/1",
        ),
        Event(
            title="Exhibition",
            start_date=now + timedelta(days=2),
            end_date=now + timedelta(days=5),
            location="Museum",
            description="Art show",
            url="http://example.com/2",
        ),
    ]


@pytest.fixture
def duplicate_events(sample_events) -> list[Event]:
    duplicate = sample_events[0].copy()
    return sample_events + [duplicate]


@pytest.mark.asyncio
async def test_load_events(temp_data_dir, sample_events):
    # Create test JSON file
    test_file = Path(temp_data_dir) / "events_20250101.json"
    with test_file.open("w") as f:
        json.dump([e.model_dump(mode="json") for e in sample_events], f)

    loaded_events = await load_events(temp_data_dir)
    assert len(loaded_events) == 2
    assert loaded_events[0].title == "Concert"


@pytest.mark.asyncio
async def test_deduplicate_events(duplicate_events):
    unique_events = await deduplicate_events(duplicate_events)
    assert len(unique_events) == 2
    titles = [e.title for e in unique_events]
    assert titles.count("Concert") == 1


@pytest.mark.asyncio
async def test_compare_with_previous(temp_data_dir, sample_events):
    # Create two test files
    old_file = Path(temp_data_dir) / "events_20240101.json"
    new_file = Path(temp_data_dir) / "events_20250101.json"

    with old_file.open("w") as f:
        json.dump([sample_events[0].model_dump(mode="json")], f)
    with new_file.open("w") as f:
        json.dump([e.model_dump(mode="json") for e in sample_events], f)

    # Load previous events from old_file
    with old_file.open("r") as f:
        previous_events = [Event(**e) for e in json.load(f)]

    new_events, removed_events = await compare_with_previous(
        sample_events, previous_events
    )
    new_list = list(new_events)
    removed_list = list(removed_events)
    assert len(new_list) == 1
    assert new_list[0].title == "Exhibition"
    assert len(removed_list) == 0


@pytest.mark.asyncio
async def test_save_events(temp_data_dir, sample_events):
    processed_dir = Path(temp_data_dir) / "processed"
    await save_events(sample_events, str(processed_dir))

    files = list(processed_dir.glob("*.json"))
    assert len(files) == 1

    with files[0].open() as f:
        saved_events = json.load(f)
    assert len(saved_events) == 2
    assert saved_events[0]["title"] == "Concert"


@pytest.mark.asyncio
async def test_compare_with_previous_removed_events(temp_data_dir, sample_events):
    # Create two test files with one event removed
    old_file = Path(temp_data_dir) / "events_20240101.json"
    new_file = Path(temp_data_dir) / "events_20250101.json"

    with old_file.open("w") as f:
        json.dump([e.model_dump(mode="json") for e in sample_events], f)
    with new_file.open("w") as f:
        json.dump([sample_events[0].model_dump(mode="json")], f)

    # Load previous events from old_file
    with old_file.open("r") as f:
        previous_events = [Event(**e) for e in json.load(f)]

    new_events, removed_events = await compare_with_previous(
        [sample_events[0]], previous_events
    )
    new_list = list(new_events)
    removed_list = list(removed_events)
    assert len(new_list) == 0
    assert len(removed_list) == 1
    assert removed_list[0].title == "Exhibition"
