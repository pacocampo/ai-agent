"""Tests for FileStorage adapters."""

import pytest
from pathlib import Path

from src.adapters.files import LocalFileStorageAdapter
from src.core.interfaces import FileStorage


def test_local_file_storage_read_text(tmp_path):
    """Test reading text file with LocalFileStorageAdapter."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!", encoding="utf-8")
    
    adapter = LocalFileStorageAdapter(base_path=tmp_path)
    content = adapter.read_text("test.txt")
    
    assert content == "Hello, World!"


def test_local_file_storage_read_bytes(tmp_path):
    """Test reading binary file with LocalFileStorageAdapter."""
    # Create a test file
    test_file = tmp_path / "test.csv"
    test_file.write_bytes(b"col1,col2\nval1,val2")
    
    adapter = LocalFileStorageAdapter(base_path=tmp_path)
    content = adapter.read_bytes("test.csv")
    
    assert content == b"col1,col2\nval1,val2"


def test_local_file_storage_exists(tmp_path):
    """Test exists() method with LocalFileStorageAdapter."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")
    
    adapter = LocalFileStorageAdapter(base_path=tmp_path)
    
    assert adapter.exists("test.txt") is True
    assert adapter.exists("nonexistent.txt") is False


def test_local_file_storage_read_text_file_not_found(tmp_path):
    """Test read_text() raises FileNotFoundError for missing file."""
    adapter = LocalFileStorageAdapter(base_path=tmp_path)
    
    with pytest.raises(FileNotFoundError):
        adapter.read_text("nonexistent.txt")


def test_local_file_storage_read_bytes_file_not_found(tmp_path):
    """Test read_bytes() raises FileNotFoundError for missing file."""
    adapter = LocalFileStorageAdapter(base_path=tmp_path)
    
    with pytest.raises(FileNotFoundError):
        adapter.read_bytes("nonexistent.csv")


def test_local_file_storage_absolute_path():
    """Test LocalFileStorageAdapter with absolute paths."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("absolute path test", encoding="utf-8")
        
        # No base_path, use absolute path
        adapter = LocalFileStorageAdapter()
        content = adapter.read_text(str(test_file))
        
        assert content == "absolute path test"


def test_local_file_storage_relative_path_with_base():
    """Test LocalFileStorageAdapter resolves relative paths correctly."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir) / "base"
        base.mkdir()
        subdir = base / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("relative path test", encoding="utf-8")
        
        adapter = LocalFileStorageAdapter(base_path=base)
        # Relative path from base
        content = adapter.read_text("subdir/test.txt")
        
        assert content == "relative path test"


def test_file_storage_integration_with_catalog():
    """Test that FileStorage works with catalog loading."""
    from src.factories import get_container
    from src.tools.catalog.inventory import _load_catalog_data, clear_catalog_cache
    
    # Clear cache to ensure fresh load
    clear_catalog_cache()
    _load_catalog_data.cache_clear()
    
    container = get_container()
    file_storage = container.file_storage()
    
    # Verify file storage is configured
    assert file_storage is not None
    assert isinstance(file_storage, LocalFileStorageAdapter)
    
    # Verify catalog file exists
    catalog_path = "resources/sample_caso_ai_engineer.csv"
    assert file_storage.exists(catalog_path), f"Catalog file not found at {catalog_path}"
    
    # Verify we can load the catalog
    vehicles = _load_catalog_data()
    assert vehicles is not None
    assert len(vehicles) > 0


def test_file_storage_integration_with_kavak_info():
    """Test that FileStorage works with Kavak info loading."""
    from src.factories import get_container
    from src.tools.catalog.kavak_info import get_kavak_info, clear_info_cache, _load_kavak_info
    
    # Clear cache to ensure fresh load
    clear_info_cache()
    _load_kavak_info.cache_clear()
    
    container = get_container()
    file_storage = container.file_storage()
    
    # Verify file storage is configured
    assert file_storage is not None
    
    # Verify info file exists
    info_path = "resources/info.txt"
    assert file_storage.exists(info_path), f"Info file not found at {info_path}"
    
    # Verify we can load the info
    info = get_kavak_info()
    assert info is not None
    assert len(info) > 0

