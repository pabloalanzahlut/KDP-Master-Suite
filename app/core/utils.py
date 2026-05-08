import re
from urllib.parse import urlparse, parse_qs

def normalize_youtube_url(url: str) -> str:
    """
    Normaliza una URL de YouTube o un handle de canal a un formato canónico.
    
    Formatos soportados:
    - @handle
    - https://www.youtube.com/@handle
    - https://youtube.com/@handle
    - https://youtube.com/user/username
    - https://youtube.com/c/channelname
    - https://youtube.com/channel/CHANNEL_ID
    - https://youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    
    Retorna el handle con @ (ej: @almoney11) o la URL original si es un video.
    
    NOTA: Los handles de YouTube son case-insensitive (se lowercasing),
    pero los video IDs son case-sensitive (se preservan tal cual).
    """
    if not url:
        return ""
    
    url = url.strip()
    
    # Si ya es un handle puro, retornarlo limpio (lowercase: los handles son case-insensitive)
    if url.startswith('@'):
        return '@' + re.sub(r'[^a-z0-9._-]', '', url[1:].lower())
    
    # Detectar URLs de video — NO normalizar (los video IDs son case-sensitive)
    if 'watch?' in url or 'youtu.be/' in url:
        return url
    
    # Parsear URL
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        path = parsed.path.rstrip('/')
    except Exception:
        # Si no es una URL válida, tratar como texto plano
        hostname = ''
        path = url
    
    # Eliminar www. del hostname
    hostname = hostname.replace('www.', '')
    
    # Solo procesar URLs de YouTube
    is_youtube = hostname in ('youtube.com', 'm.youtube.com', 'youtube.googleapis.com')
    
    if is_youtube:
        # Caso 1: /@handle
        handle_match = re.match(r'^/@([\w.-]+)$', path)
        if handle_match:
            return '@' + handle_match.group(1).lower()
        
        # Caso 2: /user/username (legacy)
        user_match = re.match(r'^/user/([\w.-]+)$', path)
        if user_match:
            return '@' + user_match.group(1).lower()
        
        # Caso 3: /c/channelname (legacy custom URL)
        custom_match = re.match(r'^/c/([\w.-]+)$', path)
        if custom_match:
            return '@' + custom_match.group(1).lower()
        
        # Caso 4: /channel/CHANNEL_ID (no convertir a handle, retornar URL original)
        channel_match = re.match(r'^/channel/([\w-]+)$', path)
        if channel_match:
            return url
    
    # Caso 5: Texto sin formato de URL = posible nombre de canal
    if not hostname and '/' not in url and '.' not in url:
        cleaned = re.sub(r'\s+', '', url).lower()
        if cleaned and not cleaned.startswith('@'):
            return '@' + cleaned
    
    # Retornar URL original si no se reconoce el formato
    return url
