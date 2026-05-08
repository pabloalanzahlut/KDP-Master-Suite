import pytest
import tempfile
import os
from app.database.db_manager import DatabaseManager

@pytest.fixture
def db(tmp_path):
    """DB temporal para tests"""
    db_file = tmp_path / "test.db"
    db_manager = DatabaseManager(str(db_file))
    yield db_manager
    if os.path.exists(db_file):
        os.remove(db_file)

def test_add_channel_returns_id(db):
    """add_channel debe retornar ID válido"""
    channel_id = db.add_channel("https://youtube.com/@test", "Test Channel", "UCtest")
    assert channel_id > 0

def test_add_channel_duplicates_returns_zero(db):
    """Duplicado debe retornar 0"""
    db.add_channel("https://youtube.com/@dup", "Duplicado")
    result = db.add_channel("https://youtube.com/@dup", "Duplicado")
    assert result == 0

def test_get_all_channels(db):
    """get_all_channels retorna lista de canales"""
    db.add_channel("https://youtube.com/@ch1", "Canal 1")
    db.add_channel("https://youtube.com/@ch2", "Canal 2")
    channels = db.get_all_channels(active_only=False)
    assert len(channels) == 2

def test_get_all_channels_active_only(db):
    """Filtro active_only funciona"""
    db.add_channel("https://youtube.com/@active", "Activo")
    ch_id = db.add_channel("https://youtube.com/@inactive", "Inactivo")
    db.toggle_channel_active(ch_id, False)
    active = db.get_all_channels(active_only=True)
    assert len(active) == 1
    assert active[0]['channel_name'] == "Activo"

def test_toggle_channel_active(db):
    """toggle_channel_active cambia estado"""
    ch_id = db.add_channel("https://youtube.com/@toggle", "Toggle Test")
    assert db.toggle_channel_active(ch_id, False) is True
    channels = db.get_all_channels(active_only=True)
    assert len(channels) == 0

def test_remove_channel(db):
    """remove_channel elimina canal"""
    ch_id = db.add_channel("https://youtube.com/@remove", "Remove Test")
    assert db.remove_channel(ch_id) is True
    channels = db.get_all_channels(active_only=False)
    assert len(channels) == 0

def test_video_exists_false_for_new(db):
    """video_exists retorna False para video nuevo"""
    assert db.video_exists("new_video_xyz") is False

def test_add_video_returns_id(db):
    """add_video retorna ID de video"""
    ch_id = db.add_channel("https://youtube.com/@ch", "Canal")
    video_id = db.add_video(ch_id, "vid_123", "https://youtube.com/watch?v=vid_123", "Test Video")
    assert video_id is not None

def test_add_video_batch(db):
    """add_videos_batch inserta múltiples videos"""
    ch_id = db.add_channel("https://youtube.com/@batch", "Batch")
    videos = [
        (ch_id, f"vid_{i}", f"url_{i}", f"Title {i}", "2024-01-01")
        for i in range(10)
    ]
    result = db.add_videos_batch(videos)
    assert len(result) == 10

def test_content_hash_deduplication(db):
    """content_hash permite deduplicación"""
    ch_id = db.add_channel("https://youtube.com/@hash", "Hash Test")
    vid_id = db.add_video(ch_id, "vid_hash", "url", "Title", "2024-01-01")
    db.update_video_content_hash("vid_hash", "abc123")
    assert db.check_content_hash_exists("abc123") is True
    assert db.check_content_hash_exists("other") is False