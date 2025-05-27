import pytest
from bs4 import BeautifulSoup
import aiohttp
from unittest.mock import AsyncMock, MagicMock
from buchloe_veranstaltungskalender.scraper import (
    extract_event_url,
    parse_contenttable,
    fetch_full_description,
    parse_events_from_page,
)


class TestEventUrlExtraction:
    """Tests for event URL extraction functionality."""

    def test_extract_event_url_valid(self):
        """Test extraction of valid event URL from wrapper."""
        html = '<a class="article" href="/freizeit-tourismus/veranstaltungen/detail/test-event/">content</a>'
        soup = BeautifulSoup(html, "html.parser")
        wrapper = soup.find("a")

        url = extract_event_url(wrapper)

        assert (
            url
            == "https://www.buchloe.de/freizeit-tourismus/veranstaltungen/detail/test-event/"
        )

    def test_extract_event_url_absolute(self):
        """Test extraction when URL is already absolute."""
        html = '<a class="article" href="https://www.buchloe.de/test/">content</a>'
        soup = BeautifulSoup(html, "html.parser")
        wrapper = soup.find("a")

        url = extract_event_url(wrapper)

        assert url == "https://www.buchloe.de/test/"

    def test_extract_event_url_no_href(self):
        """Test extraction when no href attribute."""
        html = '<a class="article">content</a>'
        soup = BeautifulSoup(html, "html.parser")
        wrapper = soup.find("a")

        url = extract_event_url(wrapper)

        assert url is None

    def test_extract_event_url_not_a_tag(self):
        """Test extraction when element is not an <a> tag."""
        html = '<div class="article">content</div>'
        soup = BeautifulSoup(html, "html.parser")
        wrapper = soup.find("div")

        url = extract_event_url(wrapper)

        assert url is None


class TestContenttableParsing:
    """Tests for contenttable parsing functionality."""

    def test_parse_contenttable_with_spans(self):
        """Test parsing contenttable with span elements."""
        html = """
        <table class="contenttable">
            <tbody>
                <tr>
                    <td>
                        <span>First paragraph text.</span>
                        <br><br>
                        <span>Second paragraph text.</span>
                    </td>
                </tr>
            </tbody>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")

        description = parse_contenttable(soup)

        assert "First paragraph text." in description
        assert "Second paragraph text." in description
        assert "\n\n" in description  # Should preserve paragraph breaks

    def test_parse_contenttable_no_spans(self):
        """Test parsing contenttable without span elements."""
        html = """
        <table class="contenttable">
            <tbody>
                <tr>
                    <td>Direct text content without spans.</td>
                </tr>
            </tbody>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")

        description = parse_contenttable(soup)

        assert description == "Direct text content without spans."

    def test_parse_contenttable_missing(self):
        """Test parsing when contenttable is missing."""
        html = "<div>No contenttable here</div>"
        soup = BeautifulSoup(html, "html.parser")

        description = parse_contenttable(soup)

        assert description == ""


class TestFullDescriptionFetching:
    """Tests for full description fetching functionality."""

    @pytest.mark.asyncio
    async def test_fetch_full_description_success(self):
        """Test successful full description fetching."""
        # Mock response content
        mock_content = """
        <html>
            <body>
                <table class="contenttable">
                    <tbody>
                        <tr>
                            <td>
                                <span>Full description content here.</span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </body>
        </html>
        """

        # Create mock session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read.return_value = mock_content.encode("utf-8")

        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        # Test the function
        result = await fetch_full_description(mock_session, "https://example.com/event")

        assert result == "Full description content here."
        mock_session.get.assert_called_once_with(
            "https://example.com/event", timeout=10.0
        )

    @pytest.mark.asyncio
    async def test_fetch_full_description_http_error(self):
        """Test handling of HTTP errors."""
        mock_response = AsyncMock()
        mock_response.status = 404

        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        result = await fetch_full_description(mock_session, "https://example.com/event")

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_full_description_no_contenttable(self):
        """Test handling when contenttable is not found."""
        mock_content = "<html><body><div>No contenttable here</div></body></html>"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read.return_value = mock_content.encode("utf-8")

        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        result = await fetch_full_description(mock_session, "https://example.com/event")

        assert result is None


class TestEnhancedEventParsing:
    """Tests for enhanced event parsing with full descriptions."""

    @pytest.mark.asyncio
    async def test_parse_events_from_page_with_wrappers(self):
        """Test parsing events from page with <a> wrappers."""
        html = """
        <html>
            <body>
                <a class="article" href="/event1/">
                    <article>
                        <div class="col date eventdates">
                            <div class="dayname">Dienstag</div>
                            <div class="table">
                                <div class="col">
                                    <div class="day">17</div>
                                </div>
                                <div class="col">
                                    <div class="month">Juni</div>
                                    <div class="year">2025</div>
                                </div>
                            </div>
                        </div>
                        <div class="col infos">
                            <div class="text">
                                <div class="title">
                                    <h2>Test Event</h2>
                                </div>
                                <div class="description">
                                    <strong>Beschreibung:</strong>
                                    Short description
                                </div>
                            </div>
                        </div>
                    </article>
                </a>
            </body>
        </html>
        """

        # Mock session for full description fetching
        mock_session = AsyncMock()

        events = await parse_events_from_page(
            html.encode("utf-8"),
            session=mock_session,
            fetch_full_descriptions=False,  # Disable for this test
        )

        assert len(events) == 1
        assert events[0].title == "Test Event"
        assert events[0].url == "https://www.buchloe.de/event1/"
        assert "Short description" in events[0].description

    @pytest.mark.asyncio
    async def test_parse_events_from_page_fallback_to_articles(self):
        """Test fallback to direct article elements when no wrappers found."""
        html = """
        <html>
            <body>
                <article>
                    <div class="col date eventdates">
                        <div class="dayname">Dienstag</div>
                        <div class="table">
                            <div class="col">
                                <div class="day">17</div>
                            </div>
                            <div class="col">
                                <div class="month">Juni</div>
                                <div class="year">2025</div>
                            </div>
                        </div>
                    </div>
                    <div class="col infos">
                        <div class="text">
                            <div class="title">
                                <h2>Test Event</h2>
                            </div>
                        </div>
                    </div>
                </article>
            </body>
        </html>
        """

        events = await parse_events_from_page(
            html.encode("utf-8"), session=None, fetch_full_descriptions=False
        )

        assert len(events) == 1
        assert events[0].title == "Test Event"
        assert events[0].url == ""  # No URL when no wrapper
