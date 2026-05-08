import time
import functools
import logging
import threading
from .yt_dlp_errors import (
    YTDLPBaseError, RateLimitError, NetworkError, 
    SubtitleMissingError, VideoUnavailableError, AuthRequiredError
)
from .error_mapper import map_yt_dlp_error

logger = logging.getLogger("kdp.yt_dlp")
_retry_lock = threading.Lock()

def retry_yt_dlp(max_attempts: int = 3, base_delay: float = 2.0, get_context: callable = None):
    """
    Decorador thread-safe para reintentos inteligentes.
    - Reintenta: RateLimit, Network
    - Fail-fast: Auth, Unavailable, SubtitleMissing
    - get_context: lambda para extraer URL de args/kwargs
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = get_context(*args, **kwargs) if get_context else {"url": "unknown"}
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                
                except Exception as e:
                    mapped = map_yt_dlp_error(e, context)
                    
                    # Fail-fast inmediato
                    if isinstance(mapped, (SubtitleMissingError, VideoUnavailableError, AuthRequiredError)):
                        logger.info(f"Fail-fast: {mapped.__class__.__name__} en {context.get('url')}")
                        raise mapped
                    
                    # Reintento con backoff exponencial
                    if isinstance(mapped, (RateLimitError, NetworkError)) and attempt < max_attempts:
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.warning(f"{mapped.__class__.__name__}. Reintentando en {delay}s ({attempt}/{max_attempts})")
                        with _retry_lock:
                            time.sleep(delay)
                    else:
                        raise mapped
        return wrapper
    return decorator