"""Test log file parsers."""
import pytest
from pathlib import Path
from app.parsers.base_parser import BaseParser
from app.parsers.log_parser import LogParser
from app.parsers.trc_parser import TrcParser


@pytest.fixture
def test_log_path():
    """Get path to test data."""
    return Path(__file__).parent.parent / "data" / "test_j1939.log"


def test_base_parser_exists():
    """Test base parser class exists."""
    parser = BaseParser()
    assert parser is not None


def test_log_parser_initialization():
    """Test log parser can be initialized."""
    parser = LogParser()
    assert parser is not None


def test_trc_parser_initialization():
    """Test TRC parser can be initialized."""
    parser = TrcParser()
    assert parser is not None


def test_test_data_exists(test_log_path):
    """Test that test data file exists."""
    assert test_log_path.exists(), f"Test data not found at {test_log_path}"


def test_log_parser_can_read(test_log_path):
    """Test log parser can read test data."""
    parser = LogParser()
    try:
        frames = parser.parse(str(test_log_path))
        assert frames is not None, "Parser should return frames"
        assert len(frames) > 0, "Should parse at least one frame"
        print(f"✓ Parsed {len(frames)} frames from test data")
    except Exception as e:
        pytest.fail(f"Parser failed: {e}")


def test_parsed_frames_have_required_fields(test_log_path):
    """Test that parsed frames have required fields."""
    parser = LogParser()
    frames = parser.parse(str(test_log_path))

    for frame in frames[:3]:  # Test first 3 frames
        assert hasattr(frame, 'timestamp') or hasattr(frame, 'ts'), "Frame should have timestamp"
        assert hasattr(frame, 'arbitration_id') or hasattr(frame, 'can_id'), "Frame should have CAN ID"
        assert hasattr(frame, 'data'), "Frame should have data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
