from bs4 import BeautifulSoup

from buchloe_veranstaltungskalender.scraper import (
    detect_date_pattern,
    extract_date_components,
    parse_date_with_pattern,
    parse_description,
)
from buchloe_veranstaltungskalender.scraper import (
    parse_event_sync as parse_event,
)


class TestDatePatternDetection:
    """Tests for date pattern detection functionality."""

    def test_detect_noch_bis_pattern(self):
        """Test detection of 'Noch bis' date pattern."""
        html = """
        <article>
            <div class="col date eventdates">
                <div class="still">Noch bis</div>
                <div class="dayname">Sonntag</div>
                <div class="table">
                    <div class="col">
                        <div class="day">14</div>
                    </div>
                    <div class="col">
                        <div class="month">Sept.</div>
                        <div class="year">2025</div>
                    </div>
                </div>
            </div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        pattern = detect_date_pattern(article)
        assert pattern == "noch_bis"

    def test_detect_normal_pattern(self):
        """Test detection of normal date pattern."""
        html = """
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
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        pattern = detect_date_pattern(article)
        assert pattern == "normal"

    def test_detect_unknown_pattern(self):
        """Test detection when date pattern is unknown."""
        html = """
        <article>
            <div class="col date eventdates">
                <div class="dayname">Dienstag</div>
                <!-- Missing day, month, year elements -->
            </div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        pattern = detect_date_pattern(article)
        assert pattern == "unknown"


class TestDateComponentExtraction:
    """Tests for date component extraction functionality."""

    def test_extract_noch_bis_components(self):
        """Test extraction of date components from 'Noch bis' pattern."""
        html = """
        <article>
            <div class="col date eventdates">
                <div class="still">Noch bis</div>
                <div class="dayname">Sonntag</div>
                <div class="table">
                    <div class="col">
                        <div class="day">14</div>
                    </div>
                    <div class="col">
                        <div class="month">Sept.</div>
                        <div class="year">2025</div>
                    </div>
                </div>
            </div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        components = extract_date_components(article)

        assert components["dayname"] == "Sonntag"
        assert components["day"] == "14"
        assert components["month"] == "Sept"  # Should strip the dot
        assert components["year"] == "2025"
        assert components["pattern"] == "noch_bis"

    def test_extract_normal_components(self):
        """Test extraction of date components from normal pattern."""
        html = """
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
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        components = extract_date_components(article)

        assert components["dayname"] == "Dienstag"
        assert components["day"] == "17"
        assert components["month"] == "Juni"
        assert components["year"] == "2025"
        assert components["pattern"] == "normal"


class TestDateParsing:
    """Tests for enhanced date parsing functionality."""

    def test_parse_noch_bis_date(self):
        """Test parsing of 'Noch bis' date pattern."""
        components = {
            "dayname": "Sonntag",
            "day": "14",
            "month": "Sept",
            "year": "2025",
            "pattern": "noch_bis",
        }

        result = parse_date_with_pattern(components)

        assert result is not None
        assert result.year == 2025
        assert result.month == 9  # September
        assert result.day == 14

    def test_parse_normal_date(self):
        """Test parsing of normal date pattern."""
        components = {
            "dayname": "Dienstag",
            "day": "17",
            "month": "Juni",
            "year": "2025",
            "pattern": "normal",
        }

        result = parse_date_with_pattern(components)

        assert result is not None
        assert result.year == 2025
        assert result.month == 6  # June
        assert result.day == 17

    def test_parse_date_missing_components(self):
        """Test parsing with missing date components."""
        components = {
            "dayname": "",
            "day": "17",
            "month": "Juni",
            "year": "2025",
            "pattern": "normal",
        }

        result = parse_date_with_pattern(components)

        assert result is None


class TestDescriptionExtraction:
    """Tests for description extraction functionality."""

    def test_extract_description_with_label(self):
        """Test extraction of description with 'Beschreibung:' label."""
        html = """
        <article>
            <div class="description">
                <strong>Beschreibung:</strong>
                Im Jahr 2015 gründeten wir gemeinsam mit unserer Chorleiterin Kerstin Klotz den Kinderchor picCHORo.
            </div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        description = parse_description(article)

        assert "Beschreibung:" not in description
        assert "Im Jahr 2015 gründeten wir" in description
        assert "picCHORo" in description

    def test_extract_description_without_label(self):
        """Test extraction of description without 'Beschreibung:' label."""
        html = """
        <article>
            <div class="description">
                Mittagstisch „Gemeinsam schmeckts besser"Der monatliche Mittagstisch für Seniorinnen und Senioren
            </div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        description = parse_description(article)

        assert "Mittagstisch" in description
        assert "Gemeinsam schmeckts besser" in description

    def test_extract_description_missing(self):
        """Test extraction when description element is missing."""
        html = """
        <article>
            <div class="title">
                <h2>Some Event</h2>
            </div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        description = parse_description(article)

        assert description == ""


class TestFullEventParsing:
    """Tests for complete event parsing with enhancements."""

    def test_parse_noch_bis_event_complete(self):
        """Test parsing of complete 'Noch bis' event."""
        html = """
        <article>
            <div class="col date eventdates">
                <div class="still">Noch bis</div>
                <div class="dayname">Sonntag</div>
                <div class="table">
                    <div class="col">
                        <div class="day">14</div>
                    </div>
                    <div class="col">
                        <div class="month">Sept.</div>
                        <div class="year">2025</div>
                    </div>
                </div>
            </div>
            <div class="col infos">
                <div class="text">
                    <div class="title">
                        <h2>Emil und die Detektive das Musical</h2>
                    </div>
                    <div class="time">
                        <strong>Uhrzeit:</strong>
                        19:00 bis 22:00 Uhr
                    </div>
                    <div class="location">
                        <strong>Veranstaltungsort:</strong>
                        Vereinsheim Honsolgen
                    </div>
                    <div class="description">
                        <strong>Beschreibung:</strong>
                        Im Jahr 2015 gründeten wir gemeinsam mit unserer Chorleiterin Kerstin Klotz den Kinderchor picCHORo.
                    </div>
                </div>
            </div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        event = parse_event(article)

        assert event is not None
        assert event.title == "Emil und die Detektive das Musical"
        assert event.start.year == 2025
        assert event.start.month == 9
        assert event.start.day == 14
        assert event.start.hour == 19
        assert event.start.minute == 0
        assert event.end.hour == 22
        assert event.end.minute == 0
        assert "Vereinsheim Honsolgen" in event.location
        assert "picCHORo" in event.description
        assert "Beschreibung:" not in event.description

    def test_parse_normal_event_complete(self):
        """Test parsing of complete normal event."""
        html = """
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
                        <h2>Mittagstisch „Gemeinsam schmeckts besser"</h2>
                    </div>
                    <div class="time">
                        <strong>Uhrzeit:</strong>
                        12:00 bis 13:30 Uhr
                    </div>
                    <div class="location">
                        <strong>Veranstaltungsort:</strong>
                        Gasthaus Eichel, Rathausplatz 4, 86807 Buchloe
                    </div>
                    <div class="description">
                        <strong>Beschreibung:</strong>
                        Mittagstisch „Gemeinsam schmeckts besser"Der monatliche Mittagstisch für Seniorinnen und Senioren
                    </div>
                </div>
            </div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        event = parse_event(article)

        assert event is not None
        assert event.title == 'Mittagstisch „Gemeinsam schmeckts besser"'
        assert event.start.year == 2025
        assert event.start.month == 6
        assert event.start.day == 17
        assert event.start.hour == 12
        assert event.start.minute == 0
        assert event.end.hour == 13
        assert event.end.minute == 30
        assert "Gasthaus Eichel" in event.location
        assert "Rathausplatz 4" in event.location
        assert "monatliche Mittagstisch" in event.description
        assert "Beschreibung:" not in event.description


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_event_missing_title(self):
        """Test parsing event with missing title."""
        html = """
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
                    <!-- Missing title element -->
                </div>
            </div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        event = parse_event(article)

        assert event is None

    def test_parse_event_missing_date(self):
        """Test parsing event with missing date components."""
        html = """
        <article>
            <div class="col date eventdates">
                <!-- Missing date elements -->
            </div>
            <div class="col infos">
                <div class="text">
                    <div class="title">
                        <h2>Some Event</h2>
                    </div>
                </div>
            </div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        event = parse_event(article)

        assert event is None

    def test_parse_event_missing_optional_elements(self):
        """Test parsing event with missing optional elements (time, location, description)."""
        html = """
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
                        <h2>Minimal Event</h2>
                    </div>
                    <!-- Missing time, location, description -->
                </div>
            </div>
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        event = parse_event(article)

        assert event is not None
        assert event.title == "Minimal Event"
        assert event.location == ""
        assert event.description == ""
        # Should have date but no specific time
        assert event.start.year == 2025
        assert event.start.month == 6
        assert event.start.day == 17
