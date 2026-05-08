class YTDLPBaseError(Exception):
    """Base para errores de yt-dlp. Preserva el error original y contexto."""
    def __init__(self, message: str, url: str = None, raw_error: Exception = None):
        super().__init__(message)
        self.url = url
        self.raw_error = raw_error

class VideoUnavailableError(YTDLPBaseError): pass
class RateLimitError(YTDLPBaseError): pass
class AuthRequiredError(YTDLPBaseError): pass
class NetworkError(YTDLPBaseError): pass
class SubtitleMissingError(YTDLPBaseError): pass
class UnknownYTDLPError(YTDLPBaseError): pass