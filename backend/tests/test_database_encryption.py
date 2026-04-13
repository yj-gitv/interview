from app.database import is_encrypted


class TestEncryption:
    def test_is_encrypted_returns_bool(self):
        result = is_encrypted()
        assert isinstance(result, bool)

    def test_default_is_not_encrypted(self):
        assert is_encrypted() is False
