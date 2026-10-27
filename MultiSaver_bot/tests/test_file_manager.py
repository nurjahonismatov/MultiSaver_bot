
import pytest

from services.file_manager import FileManager


@pytest.mark.asyncio
async def test_generate_and_cleanup(tmp_path, monkeypatch):
    monkeypatch.setenv("TEMP_DIR", str(tmp_path))
    # Force new instance
    from services import file_manager as fm_mod
    fm_mod._file_manager = None

    fm = FileManager()
    path = fm.generate_path(suffix=".txt")
    path.write_text("hello")
    assert path.exists()
    await fm.cleanup(path)
    assert not path.exists()
