import pytest
from pathlib import Path
from datetime import datetime, timedelta
import json
from buchloe_veranstaltungskalender.io import load_events, save_events
from buchloe_veranstaltungskalender.models import Event


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
            start=now + timedelta(days=1),
            end=now + timedelta(days=1, hours=2),
            location="Town Hall",
            description="Music event",
            url="http://example.com/1",
        ),
        Event(
            title="Exhibition",
            start=now + timedelta(days=2),
            end=now + timedelta(days=5),
            location="Museum",
            description="Art show",
            url="http://example.com/2",
        ),
    ]


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
async def test_save_events(temp_data_dir, sample_events):
    processed_dir = Path(temp_data_dir) / "processed"
    await save_events(sample_events, str(processed_dir))

    files = list(processed_dir.glob("*.json"))
    assert len(files) == 1

    with files[0].open() as f:
        saved_events = json.load(f)
    assert len(saved_events) == 2
    assert saved_events[0]["title"] == "Concert"
