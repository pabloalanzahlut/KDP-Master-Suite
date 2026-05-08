import re
import logging
from .yt_dlp_errors import YTDLPBaseError, VideoUnavailableError, RateLimitError, AuthRequiredError, NetworkError, SubtitleMissingError, UnknownYTDLPError

logger = logging.getLogger("kdp.yt_dlp")

YT_DLP_PATTERNS = {
    r"(?i)(http error 403|sign in required|login|cookies)": AuthRequiredError,
    r"(?i)(http error 410|unavailable|private|deleted|removed|video not found|channel.*not found|playlist.*not found)": VideoUnavailableError,
    r"(?i)(http error 429|too many requests|rate limit)": RateLimitError,
    r"(?i)(http error 50[0-9]|connection refused|timed out|network|dns)": NetworkError,
    r"(?i)(no subtitles|subtitles not available|no subtitle tracks found)": SubtitleMissingError,
}

def map_yt_dlp_error(raw_exc: Exception, context: dict) -> YTDLPBaseError:
    """Convierte excepción cruda en error tipado con contexto."""
    error_msg = str(raw_exc)
    exc_class = UnknownYTDLPError
    
    for pattern, cls in YT_DLP_PATTERNS.items():
        if re.search(pattern, error_msg):
            exc_class = cls
            break
            
    return exc_class(
        message=f"{exc_class.__name__}: {error_msg}",
        url=context.get("url"),
        raw_error=raw_exc
    )