from utils.i18n import get_text


def test_welcome_uz_contains_name():
    text = get_text("start.welcome", "uz", first_name="Ali")
    assert "Ali" in text
    assert "MultiSaver" in text


def test_welcome_en():
    text = get_text("start.welcome", "en", first_name="Bob")
    assert "Bob" in text
    assert "Welcome" in text


def test_welcome_ru():
    text = get_text("start.welcome", "ru", first_name="Иван")
    assert "Иван" in text
