"""Media type detection tests."""

from services.media_detector import detect_media_type, is_audio, is_image, is_video


def test_video():
    assert detect_media_type("clip.mp4") == "video"
    assert is_video("a.webm")


def test_image():
    assert detect_media_type("photo.jpg") == "image"
    assert is_image("x.png")


def test_audio():
    assert detect_media_type("song.mp3") == "audio"
    assert is_audio("t.m4a")


def test_unknown():
    assert detect_media_type("file.xyz") == "unknown"
