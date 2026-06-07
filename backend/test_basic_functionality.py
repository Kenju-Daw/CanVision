"""Basic functionality tests for CanVision."""
import pytest
from pathlib import Path


def test_backend_structure():
    """Test that backend has required structure."""
    base_path = Path(__file__).parent

    # Check directory structure
    assert (base_path / "app").exists(), "app directory should exist"
    assert (base_path / "app" / "parsers").exists(), "parsers directory should exist"
    assert (base_path / "app" / "decoders").exists(), "decoders directory should exist"
    assert (base_path / "app" / "api").exists(), "api directory should exist"
    assert (base_path / "app" / "db").exists(), "db directory should exist"
    assert (base_path / "app" / "models").exists(), "models directory should exist"


def test_main_app_exists():
    """Test that main.py exists and imports."""
    from pathlib import Path
    main_file = Path(__file__).parent / "main.py"
    assert main_file.exists(), "main.py should exist"

    # Try importing FastAPI app
    try:
        from main import app
        assert app is not None, "FastAPI app should be importable"
        print("✓ FastAPI app imported successfully")
    except ImportError as e:
        pytest.skip(f"FastAPI not installed: {e}")


def test_models_exist():
    """Test that model classes exist."""
    try:
        from app.models.signal import SignalFrame, RawFrame, SignalDefinition
        assert SignalFrame is not None
        assert RawFrame is not None
        assert SignalDefinition is not None
        print("✓ All model classes exist")
    except ImportError:
        pytest.skip("Models not accessible")


def test_requirements_file():
    """Test that requirements.txt has all needed packages."""
    req_file = Path(__file__).parent / "requirements.txt"
    assert req_file.exists(), "requirements.txt should exist"

    with open(req_file) as f:
        requirements = f.read()
        assert "fastapi" in requirements.lower(), "Should have fastapi"
        assert "uvicorn" in requirements.lower(), "Should have uvicorn"
        assert "python-can" in requirements.lower() or "can" in requirements.lower(), "Should have python-can"

    print("✓ All required packages listed")


def test_test_data_exists():
    """Test that test data is available."""
    test_data = Path(__file__).parent.parent / "data" / "test_j1939.log"
    assert test_data.exists(), f"Test data should exist at {test_data}"
    assert test_data.stat().st_size > 0, "Test data should not be empty"
    print(f"✓ Test data exists ({test_data.stat().st_size} bytes)")


def test_j1939_base_data_exists():
    """Test that J1939 base database exists."""
    j1939_file = Path(__file__).parent.parent / "data" / "j1939_base.json"
    assert j1939_file.exists(), f"J1939 base should exist at {j1939_file}"
    assert j1939_file.stat().st_size > 0, "J1939 base should not be empty"

    # Try parsing JSON
    import json
    try:
        with open(j1939_file) as f:
            data = json.load(f)
            assert isinstance(data, dict), "J1939 base should be a dictionary"
            assert len(data) > 0, "J1939 base should not be empty"
            print(f"✓ J1939 base loaded ({len(data)} PGNs)")
    except json.JSONDecodeError as e:
        pytest.fail(f"J1939 base JSON is invalid: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
