"""Tests for shared utilities and critical functions.

Run with: python -m pytest tests\test_utils.py -v
"""

import os
import pytest

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from features.utils import (
    parse_page_range,
    parse_page_range_groups,
    safe_filename,
    readable_size,
)


class TestParsePageRange:
    def test_empty_string_returns_all(self):
        result = parse_page_range("", 10)
        assert result == list(range(10))

    def test_single_page(self):
        result = parse_page_range("3", 10)
        assert result == [2]  # zero-based

    def test_range(self):
        result = parse_page_range("1-5", 10)
        assert result == [0, 1, 2, 3, 4]

    def test_comma_separated(self):
        result = parse_page_range("1, 3, 5-7", 10)
        assert result == [0, 2, 4, 5, 6]

    def test_duplicates_removed(self):
        result = parse_page_range("1-3, 2-4", 10)
        assert result == [0, 1, 2, 3]

    def test_whitespace_handled(self):
        result = parse_page_range("  1 ,  3-5  ", 10)
        assert result == [0, 2, 3, 4]

    def test_zero_based_false(self):
        result = parse_page_range("1, 3", 10, zero_based=False)
        assert result == [1, 3]

    def test_out_of_bounds_raises(self):
        with pytest.raises(ValueError):
            parse_page_range("1, 11", 10)

    def test_reversed_range_raises(self):
        with pytest.raises(ValueError):
            parse_page_range("5-1", 10)


class TestParsePageRangeGroups:
    def test_single_group(self):
        result = parse_page_range_groups("1-3", 10)
        assert result == [[0, 1, 2]]

    def test_multiple_groups(self):
        result = parse_page_range_groups("1-3, 5, 7-9", 10)
        assert result == [[0, 1, 2], [4], [6, 7, 8]]

    def test_single_page_group(self):
        result = parse_page_range_groups("4", 10)
        assert result == [[3]]

    def test_out_of_bounds_raises(self):
        with pytest.raises(ValueError):
            parse_page_range_groups("1-20", 10)


class TestSafeFilename:
    def test_replaces_invalid_chars(self):
        result = safe_filename('test:file"name*here?')
        assert result == 'test_file_name_here_'

    def test_handles_empty_string(self):
        result = safe_filename('')
        assert result == 'video'

    def test_strips_invalid_only(self):
        result = safe_filename('<>:"/\\|?*')
        assert result == '_________'

    def test_preserves_valid_chars(self):
        result = safe_filename('Hello World - 2024')
        assert result == 'Hello World - 2024'

    def test_replaces_null_byte(self):
        result = safe_filename('test\x00file')
        assert result == 'test_file'


class TestReadableSize:
    def test_bytes(self):
        assert readable_size(500) == "500.0 B"

    def test_kilobytes(self):
        assert readable_size(2048) == "2.0 KB"

    def test_megabytes(self):
        assert readable_size(1048576) == "1.0 MB"

    def test_gigabytes(self):
        assert readable_size(1073741824) == "1.0 GB"

    def test_terabytes(self):
        assert readable_size(1099511627776) == "1.0 TB"

    def test_zero(self):
        assert readable_size(0) == "0.0 B"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
