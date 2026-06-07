"""Test signal store functionality."""
import pytest
from app.db.signal_store import SignalStore
from app.models.signal import SignalFrame


@pytest.fixture
def store():
    """Create a fresh signal store."""
    return SignalStore()


def test_signal_store_initialization(store):
    """Test signal store initializes correctly."""
    assert store is not None
    assert store.signals == {}
    assert store.stats == {}


def test_add_signal(store):
    """Test adding a signal to the store."""
    signal = SignalFrame(
        timestamp=1000,
        pgn=0xF004,
        spn=190,
        spn_name="EngineSpeed",
        value=1500.0,
        unit="rpm",
        raw_value=0x0F,
    )

    store.add_signal(signal)
    assert "EngineSpeed" in store.signals
    assert len(store.signals["EngineSpeed"]) == 1


def test_signal_stats_calculation(store):
    """Test that stats (min, max, avg) are calculated."""
    signals = [
        SignalFrame(timestamp=i*1000, pgn=0xF004, spn=190, spn_name="EngineSpeed",
                   value=float(1000 + i*100), unit="rpm", raw_value=i),
        SignalFrame(timestamp=i*1000, pgn=0xF004, spn=190, spn_name="EngineSpeed",
                   value=float(1100 + i*100), unit="rpm", raw_value=i),
        SignalFrame(timestamp=i*1000, pgn=0xF004, spn=190, spn_name="EngineSpeed",
                   value=float(1200 + i*100), unit="rpm", raw_value=i),
    ]

    for signal in signals:
        store.add_signal(signal)

    # Check stats exist
    assert "EngineSpeed" in store.stats
    stats = store.stats["EngineSpeed"]
    assert "min" in stats
    assert "max" in stats
    assert "avg" in stats


def test_multiple_signals(store):
    """Test adding multiple different signals."""
    signals_data = [
        ("EngineSpeed", 0xF004, 190, 1500.0, "rpm"),
        ("EngineCoolantTemp", 0xFECA, 110, 85.0, "°C"),
        ("VehicleSpeed", 0xFEC1, 84, 60.0, "km/h"),
    ]

    for name, pgn, spn, value, unit in signals_data:
        signal = SignalFrame(
            timestamp=1000,
            pgn=pgn,
            spn=spn,
            spn_name=name,
            value=value,
            unit=unit,
            raw_value=0,
        )
        store.add_signal(signal)

    assert len(store.signals) == 3
    assert "EngineSpeed" in store.signals
    assert "EngineCoolantTemp" in store.signals
    assert "VehicleSpeed" in store.signals


def test_get_all_signals(store):
    """Test retrieving all signals."""
    for i in range(5):
        signal = SignalFrame(
            timestamp=i*1000,
            pgn=0xF004,
            spn=190,
            spn_name="EngineSpeed",
            value=float(1000 + i*100),
            unit="rpm",
            raw_value=i,
        )
        store.add_signal(signal)

    all_signals = store.get_all_signals()
    assert all_signals is not None
    assert len(all_signals) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
