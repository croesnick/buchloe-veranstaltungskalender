"""Tests for iCal formatting functionality

This module tests the custom iCal formatting functions to ensure they improve
readability while maintaining RFC 5545 compliance.
"""

import pytest
from buchloe_veranstaltungskalender.ical_formatter import (
    smart_fold_line,
    optimize_escaping,
    preprocess_description,
    format_ical_content,
    format_property_value,
    _find_best_break_point,
)


class TestSmartFoldLine:
    """Tests for smart line folding functionality."""

    def test_short_line_unchanged(self):
        """Test that short lines are not folded."""
        line = "SUMMARY:Short event title"
        result = smart_fold_line(line)
        assert result == [line]

    def test_long_line_folded_at_word_boundary(self):
        """Test that long lines are folded at word boundaries when possible."""
        line = "DESCRIPTION:This is a very long description that should be folded at word boundaries to maintain readability while staying RFC compliant"
        result = smart_fold_line(line, max_length=75)

        # Should have multiple lines
        assert len(result) > 1

        # First line should not exceed max length
        assert len(result[0]) <= 75

        # Continuation lines should start with space
        for continuation_line in result[1:]:
            assert continuation_line.startswith(" ")
            assert len(continuation_line) <= 75

    def test_fold_at_comma(self):
        """Test folding at comma boundaries."""
        line = "LOCATION:Very Long Location Name, Street Address, City, State, ZIP Code"
        result = smart_fold_line(line, max_length=50)

        assert len(result) > 1
        # Should break after comma when possible
        assert any("," in line for line in result[:-1])

    def test_very_long_word_character_breaking(self):
        """Test that very long words are broken at character level."""
        line = "URL:https://www.example.com/very/long/path/that/cannot/be/broken/at/word/boundaries/and/exceeds/maximum/length"
        result = smart_fold_line(line, max_length=75)

        assert len(result) > 1
        for line in result:
            assert len(line) <= 75

    def test_escape_sequence_preservation(self):
        """Test that escape sequences are not broken."""
        line = "DESCRIPTION:Text with \\n newline and \\, comma escapes that should not be broken"
        result = smart_fold_line(line, max_length=50)

        # Check that no line ends with a single backslash
        for line in result:
            if line.endswith("\\"):
                # Should be a double backslash or part of a valid escape
                assert (
                    line.endswith("\\\\")
                    or line.endswith("\\n")
                    or line.endswith("\\,")
                )


class TestFindBestBreakPoint:
    """Tests for the break point finding algorithm."""

    def test_word_boundary_preferred(self):
        """Test that word boundaries are preferred for breaking."""
        line = "This is a test line with multiple words"
        break_point = _find_best_break_point(line, 20)

        # Should break at a space
        assert line[break_point - 1] == " " or break_point == 20

    def test_punctuation_break_points(self):
        """Test breaking at punctuation marks."""
        line = "Event: Location, Date; Time"
        break_point = _find_best_break_point(line, 15)

        # Should break at punctuation when possible
        if break_point < len(line):
            assert line[break_point - 1] in [" ", ",", ";", ":"]

    def test_no_break_after_property_colon(self):
        """Test that we don't break immediately after property name colon."""
        line = "DESCRIPTION:This is the content"
        break_point = _find_best_break_point(line, 15)

        # Should not break right after DESCRIPTION:
        assert break_point > 12  # Length of "DESCRIPTION:"


class TestOptimizeEscaping:
    """Tests for escaping optimization."""

    def test_remove_unnecessary_escaping(self):
        """Test removal of unnecessary escape characters."""
        text = "Text with \\, comma and \\; semicolon"
        result = optimize_escaping(text)

        # Should remove unnecessary escaping in regular text
        assert "," in result
        assert ";" in result

    def test_preserve_necessary_escaping(self):
        """Test that necessary escaping is preserved."""
        text = "Path\\\\with\\\\backslashes"
        result = optimize_escaping(text)

        # Should preserve backslash escaping
        assert "\\\\" in result

    def test_empty_string(self):
        """Test handling of empty strings."""
        result = optimize_escaping("")
        assert result == ""

    def test_none_input(self):
        """Test handling of None input."""
        result = optimize_escaping(None)
        assert result is None


class TestPreprocessDescription:
    """Tests for description preprocessing."""

    def test_normalize_whitespace(self):
        """Test normalization of excessive whitespace."""
        description = "Text  with   multiple    spaces"
        result = preprocess_description(description)
        assert result == "Text with multiple spaces"

    def test_paragraph_breaks(self):
        """Test handling of paragraph breaks."""
        description = "First paragraph.\n\n\nSecond paragraph."
        result = preprocess_description(description)
        assert result == "First paragraph.\n\nSecond paragraph."

    def test_punctuation_spacing(self):
        """Test cleanup of spacing around punctuation."""
        description = "Text with spaces  ,  and  ;  punctuation  ."
        result = preprocess_description(description)
        assert result == "Text with spaces, and; punctuation."

    def test_trailing_whitespace_removal(self):
        """Test removal of trailing whitespace from lines."""
        description = "Line with trailing spaces   \nAnother line   "
        result = preprocess_description(description)
        assert not any(line.endswith(" ") for line in result.split("\n"))

    def test_empty_description(self):
        """Test handling of empty descriptions."""
        result = preprocess_description("")
        assert result == ""

    def test_none_description(self):
        """Test handling of None descriptions."""
        result = preprocess_description(None)
        assert result == ""


class TestFormatPropertyValue:
    """Tests for property-specific formatting."""

    def test_description_formatting(self):
        """Test that descriptions are preprocessed."""
        value = "Description  with   extra   spaces"
        result = format_property_value("DESCRIPTION", value)
        assert result == "Description with extra spaces"

    def test_summary_formatting(self):
        """Test that summaries are normalized."""
        value = "  Event   Title  "
        result = format_property_value("SUMMARY", value)
        assert result == "Event Title"

    def test_location_formatting(self):
        """Test that locations are normalized."""
        value = "  Location   Name  "
        result = format_property_value("LOCATION", value)
        assert result == "Location Name"

    def test_other_property_minimal_processing(self):
        """Test that other properties get minimal processing."""
        value = "  Some Value  "
        result = format_property_value("OTHER", value)
        assert result == "Some Value"

    def test_empty_value(self):
        """Test handling of empty values."""
        result = format_property_value("DESCRIPTION", "")
        assert result == ""


class TestFormatIcalContent:
    """Tests for complete iCal content formatting."""

    def test_basic_formatting(self):
        """Test basic iCal content formatting."""
        ical_content = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Very long event title that should be folded at word boundaries for better readability
DESCRIPTION:Long description with multiple sentences that should be properly formatted and folded.
END:VEVENT
END:VCALENDAR"""

        result = format_ical_content(ical_content)
        result_str = result.decode("utf-8")

        # Should still be valid iCal structure
        assert "BEGIN:VCALENDAR" in result_str
        assert "END:VCALENDAR" in result_str
        assert "BEGIN:VEVENT" in result_str
        assert "END:VEVENT" in result_str

    def test_line_folding_applied(self):
        """Test that line folding is applied to long lines."""
        long_line = "DESCRIPTION:" + "x" * 100
        ical_content = f"""BEGIN:VCALENDAR
{long_line}
END:VCALENDAR""".encode("utf-8")

        result = format_ical_content(ical_content)
        result_str = result.decode("utf-8")

        # Should have folded the long line
        lines = result_str.split("\n")
        long_lines = [line for line in lines if len(line) > 75]
        assert len(long_lines) == 0  # No lines should exceed 75 characters

    def test_unicode_handling(self):
        """Test proper handling of Unicode characters."""
        ical_content = "BEGIN:VCALENDAR\nSUMMARY:Event with ümlaut and émoji 🎉\nEND:VCALENDAR".encode(
            "utf-8"
        )

        result = format_ical_content(ical_content)
        result_str = result.decode("utf-8")

        # Should preserve Unicode characters
        assert "ümlaut" in result_str
        assert "émoji" in result_str
        assert "🎉" in result_str

    def test_empty_lines_preserved(self):
        """Test that empty lines are preserved appropriately."""
        ical_content = b"""BEGIN:VCALENDAR

VERSION:2.0

END:VCALENDAR"""

        result = format_ical_content(ical_content)
        result_str = result.decode("utf-8")

        # Should not have excessive blank lines
        assert "\n\n\n" not in result_str

    def test_proper_line_endings(self):
        """Test that line endings are normalized."""
        ical_content = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"

        result = format_ical_content(ical_content)
        result_str = result.decode("utf-8")

        # Should use Unix line endings
        assert "\r\n" not in result_str
        assert result_str.endswith("\n")


class TestRFC5545Compliance:
    """Tests to ensure RFC 5545 compliance is maintained."""

    def test_line_length_compliance(self):
        """Test that all lines comply with RFC 5545 length limits."""
        long_text = "x" * 200
        lines = smart_fold_line(f"DESCRIPTION:{long_text}")

        for line in lines:
            assert len(line) <= 75

    def test_continuation_line_format(self):
        """Test that continuation lines are properly formatted."""
        long_text = "This is a very long line that needs to be folded"
        lines = smart_fold_line(f"DESCRIPTION:{long_text}", max_length=30)

        if len(lines) > 1:
            # First line should not start with space
            assert not lines[0].startswith(" ")

            # Continuation lines should start with space
            for line in lines[1:]:
                assert line.startswith(" ")

    def test_property_structure_preserved(self):
        """Test that property structure is preserved."""
        ical_content = b"""BEGIN:VEVENT
SUMMARY:Test Event
DESCRIPTION:Test Description
DTSTART:20250101T120000Z
END:VEVENT"""

        result = format_ical_content(ical_content)
        result_str = result.decode("utf-8")

        # Should preserve all properties
        assert "SUMMARY:" in result_str
        assert "DESCRIPTION:" in result_str
        assert "DTSTART:" in result_str
        assert "BEGIN:VEVENT" in result_str
        assert "END:VEVENT" in result_str


@pytest.fixture
def sample_event_data():
    """Fixture providing sample event data for testing."""
    return {
        "title": "Sample Event with a Very Long Title That Should Be Formatted Properly",
        "description": """This is a long description with multiple paragraphs.

It contains various punctuation marks, commas, semicolons; and other characters that might need special handling.

The description should be formatted nicely while maintaining RFC compliance.""",
        "location": "Very Long Location Name, Street Address, City, State, ZIP Code",
        "url": "https://www.example.com/very/long/url/path/that/might/need/folding",
    }


def test_integration_with_sample_data(sample_event_data):
    """Integration test with realistic event data."""
    # Test description preprocessing
    processed_desc = preprocess_description(sample_event_data["description"])
    assert "  " not in processed_desc  # No double spaces

    # Test property formatting
    formatted_title = format_property_value("SUMMARY", sample_event_data["title"])
    assert formatted_title == sample_event_data["title"].strip()

    # Test line folding on long properties
    long_line = f"DESCRIPTION:{processed_desc}"
    folded_lines = smart_fold_line(long_line)

    # Should be folded and compliant
    assert len(folded_lines) > 1
    for line in folded_lines:
        assert len(line) <= 75
