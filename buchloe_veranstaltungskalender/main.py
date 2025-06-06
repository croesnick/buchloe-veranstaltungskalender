"""Main module for Buchloe Event Calendar

This module implements the core processing pipeline:
1. Scrape events from the website
2. Remove duplicates
3. Compare with previous events
4. Log new and removed events
5. Save results

The pipeline is started via the main() function which:
- Invokes the scraper
- Performs deduplication
- Compares with previous data
- Saves and logs results
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from . import compare, ical, io, scraper
from .logging_config import get_logger, setup_logging

# Initialize logging configuration
setup_logging(level=logging.INFO)
logger = get_logger(__name__)


async def main() -> None:
    data_dir = Path("data")
    processed_dir = data_dir / "processed"

    try:
        # Scrape new events
        current_events = await scraper.scrape_events()

        # Deduplicate
        unique_events = await compare.deduplicate_events(current_events)

        # Load previous processed events
        previous_events = await io.load_events(processed_dir)

        # Compare with previous
        new_events, removed_events = await compare.compare_events(
            unique_events, previous_events
        )

        # Save new events
        await io.save_events(new_events, processed_dir)

        # Generate and save iCal files
        if unique_events:
            # Save timestamped iCal for archival
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ical_filename = f"events_{timestamp}.ics"
            await ical.save_ical_file(unique_events, processed_dir / ical_filename)

            # Save public iCal for GitHub Pages
            public_ical_path = await ical.save_public_ical(unique_events, data_dir)
            logger.info(f"Generated iCal files with {len(unique_events)} events")
            logger.info(f"Public iCal available at: {public_ical_path}")

        # Log results
        if new_events:
            logger.info(f"Found {len(new_events)} new events:")
            for event in new_events:
                logger.info(f"- {event.title} at {event.location} on {event.start}")
        else:
            logger.info("No new events found since last scrape.")

        if removed_events:
            logger.info(f"Found {len(removed_events)} removed events:")
            for event in removed_events:
                logger.info(
                    f"- {event.title} at {event.location} was removed (previously scheduled for {event.start})"
                )

    except Exception as e:
        logger.error(f"Error processing events: {str(e)}", exc_info=True)


def start() -> None:
    asyncio.run(main())
