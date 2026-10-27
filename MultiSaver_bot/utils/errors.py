"""Application errors."""


class MultiSaverError(Exception):
    """Base error with i18n key."""

    def __init__(self, message: str = "", error_key: str = "download.failed") -> None:
        super().__init__(message)
        self.error_key = error_key


class InvalidURLError(MultiSaverError):
    def __init__(self, message: str = "Invalid URL") -> None:
        super().__init__(message, error_key="download.invalid_url")


class UnsupportedPlatformError(MultiSaverError):
    def __init__(self, message: str = "Unsupported") -> None:
        super().__init__(message, error_key="download.unsupported")


class PrivateContentError(MultiSaverError):
    def __init__(self, message: str = "Private") -> None:
        super().__init__(message, error_key="download.private")


class NetworkError(MultiSaverError):
    def __init__(self, message: str = "Network") -> None:
        super().__init__(message, error_key="download.failed")


class DownloadTimeoutError(MultiSaverError):
    def __init__(self, message: str = "Timeout") -> None:
        super().__init__(message, error_key="download.timeout")


class FileTooLargeError(MultiSaverError):
    def __init__(self, message: str = "Too large") -> None:
        super().__init__(message, error_key="download.too_large")


class RateLimitError(MultiSaverError):
    def __init__(self, seconds: int = 60, message: str = "Rate limit") -> None:
        super().__init__(message, error_key="download.rate_limit")
        self.seconds = seconds


class AudioExtractionError(MultiSaverError):
    def __init__(self, message: str = "Audio failed") -> None:
        super().__init__(message, error_key="media.audio_failed")


class MediaExpiredError(MultiSaverError):
    def __init__(self, message: str = "Expired") -> None:
        super().__init__(message, error_key="media.expired")