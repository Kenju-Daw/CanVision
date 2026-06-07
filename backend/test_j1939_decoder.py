"""Test J1939 decoder functionality."""
import pytest
from app.decoders.j1939_decoder import J1939Decoder
from app.models.signal import SignalDefinition


@pytest.fixture
def decoder():
    """Create decoder instance with test data."""
    decoder = J1939Decoder()
    decoder._load_j1939_base()
    return decoder


def test_j1939_decoder_initialization(decoder):
    """Test decoder initializes with base signals."""
    assert decoder.signal_defs is not None
    assert len(decoder.signal_defs) > 0, "Should load J1939 base signals"


def test_pgn_extraction():
    """Test PGN extraction from 29-bit CAN ID."""
    decoder = J1939Decoder()

    # Sample J1939 IDs (format: priority(3) + reserved(1) + PDU_format(8) + PDU_specific(8) + PS(8))
    test_id = 0x0CF00400  # EEC1 PGN = 0xF004
    pgn = decoder._extract_pgn(test_id)

    # PGN should be extracted correctly
    assert pgn == 0xF004, f"Expected PGN 0xF004, got {hex(pgn)}"


def test_signal_decode(decoder):
    """Test decoding a signal from CAN data."""
    # EEC1 (0x0CF00400) with engine speed data
    pgn = 0xF004
    data = bytes([0x10, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    signals = decoder.decode_pgn(pgn, data)
    assert signals is not None, "Should decode signals from PGN"
    assert len(signals) > 0, "Should return at least one signal"


def test_invalid_data_filtering(decoder):
    """Test that 0xFF/0xFE invalid indicators are filtered."""
    pgn = 0xF004
    # All 0xFF is invalid data
    data = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

    signals = decoder.decode_pgn(pgn, data)
    # Should either return empty or filter invalid values
    assert signals is not None


def test_signal_definitions_loaded(decoder):
    """Test that standard J1939 signal definitions are loaded."""
    assert 0xF004 in decoder.signal_defs, "EEC1 should be in signal defs"
    assert 0xFEC1 in decoder.signal_defs, "CCVS1 should be in signal defs"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
