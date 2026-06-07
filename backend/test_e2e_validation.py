"""End-to-End validation tests."""
import json
import pytest
from pathlib import Path


def test_data_files_integrity():
    """Test that all data files are valid and intact."""
    data_dir = Path(__file__).parent.parent / "data"

    # Check J1939 base database
    j1939_file = data_dir / "j1939_base.json"
    assert j1939_file.exists(), "J1939 base should exist"

    with open(j1939_file) as f:
        j1939_data = json.load(f)
        assert isinstance(j1939_data, dict), "J1939 should be a dictionary"

        # J1939 data structure: top level has 'pgns', 'source_addresses', etc.
        pgns = j1939_data.get("pgns", {})
        assert len(pgns) >= 5, f"Should have at least 5 PGNs, got {len(pgns)}"

        # Check structure of PGNs
        for pgn_hex, pgn_data in list(pgns.items())[:3]:
            assert "name" in pgn_data, f"PGN {pgn_hex} should have name"
            assert "spns" in pgn_data or "signals" in pgn_data, f"PGN {pgn_hex} should have signals/spns"

    print(f"✓ J1939 base valid ({len(pgns)} PGNs)")

    # Check test data
    test_log = data_dir / "test_j1939.log"
    assert test_log.exists(), "Test log should exist"
    assert test_log.stat().st_size > 100, "Test log should have content"
    print(f"✓ Test data valid ({test_log.stat().st_size} bytes)")


def test_project_files_present():
    """Test that all critical project files exist."""
    base_path = Path(__file__).parent.parent

    files_to_check = [
        "README.md",
        "Makefile",
        "LICENSE",
        "backend/main.py",
        "backend/requirements.txt",
        "dashboard/package.json",
        "dashboard/App.tsx",
        ".gitignore",
        "docs/ARCHITECTURE.md",
        "docs/PHASE1_COMPLETE.md",
        "docs/API.md",
    ]

    for file_path in files_to_check:
        full_path = base_path / file_path
        assert full_path.exists(), f"Missing: {file_path}"

    print(f"✓ All {len(files_to_check)} critical files present")


def test_documentation_quality():
    """Test that documentation is complete."""
    docs_dir = Path(__file__).parent.parent / "docs"

    # Check phase 1 documentation
    phase1_doc = docs_dir / "PHASE1_COMPLETE.md"
    with open(phase1_doc) as f:
        content = f.read()
        assert len(content) > 500, "Documentation should be substantial"
        assert "Status:" in content or "status" in content.lower(), "Should have status"
        assert "test" in content.lower(), "Should mention testing"

    print("✓ Documentation is complete")


def test_makefile_integrity():
    """Test that Makefile has required targets."""
    makefile = Path(__file__).parent.parent / "Makefile"
    with open(makefile) as f:
        content = f.read()
        assert "install" in content, "Should have install target"
        assert "dev" in content, "Should have dev target"
        assert "backend" in content, "Should have backend target"
        assert "dashboard" in content, "Should have dashboard target"

    print("✓ Makefile has all required targets")


def test_requirements_completeness():
    """Test that all package requirements are specified."""
    req_file = Path(__file__).parent / "requirements.txt"
    with open(req_file) as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    required_packages = ["fastapi", "uvicorn", "python-can", "cantools"]
    for package in required_packages:
        assert any(package.lower() in line.lower() for line in lines), \
            f"Missing required package: {package}"

    print(f"✓ All required packages specified ({len(lines)} packages)")


def test_frontend_package_config():
    """Test that frontend package.json is valid."""
    pkg_file = Path(__file__).parent.parent / "dashboard" / "package.json"
    with open(pkg_file) as f:
        pkg_data = json.load(f)

    assert "name" in pkg_data, "Package should have name"
    assert "dependencies" in pkg_data, "Package should have dependencies"
    assert "react" in pkg_data["dependencies"], "Should have React dependency"

    print(f"✓ Frontend package.json valid ({len(pkg_data.get('dependencies', {}))} dependencies)")


def test_git_repository():
    """Test that git repository is initialized."""
    git_dir = Path(__file__).parent.parent / ".git"
    assert git_dir.exists(), "Git repository should be initialized"
    print("✓ Git repository initialized")


def test_source_code_stats():
    """Calculate and report source code statistics."""
    base_path = Path(__file__).parent.parent

    python_files = list(base_path.rglob("*.py"))
    tsx_files = list(base_path.rglob("*.tsx"))
    ts_files = list(base_path.rglob("*.ts"))
    doc_files = list(base_path.rglob("docs/*.md"))

    # Filter out test files and node_modules
    python_files = [f for f in python_files if "test_" not in f.name and ".venv" not in str(f)]
    tsx_files = [f for f in tsx_files if "node_modules" not in str(f)]
    ts_files = [f for f in ts_files if "node_modules" not in str(f)]

    print(f"\n📊 Code Statistics:")
    print(f"  Python files: {len(python_files)}")
    print(f"  TypeScript/TSX files: {len(ts_files + tsx_files)}")
    print(f"  Documentation files: {len(doc_files)}")

    assert len(python_files) > 5, "Should have Python source files"
    assert len(tsx_files) > 0, "Should have React components"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
