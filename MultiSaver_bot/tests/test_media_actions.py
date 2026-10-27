from keyboards.media_actions import media_actions_kb


def test_video_keyboard_has_audio():
    kb = media_actions_kb("abc123", lang="en", media_type="video", can_extract_audio=True)
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert any("Audio" in t or "аудио" in t.lower() or "Musiqa" in t or "Download Audio" in t for t in texts)


def test_image_keyboard_no_audio():
    kb = media_actions_kb("xyz", lang="en", media_type="image", can_extract_audio=False)
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert not any("Audio" in t for t in texts)
