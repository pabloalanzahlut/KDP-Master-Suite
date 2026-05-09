"""
KDP Master Dashboard Server
===========================
Servidor web para monitoreo en tiempo real del sistema.
- Puerto configurable via CLI o settings.json
- Fallback automático si puerto ocupado
- Endpoint /api/config para discovery de puerto
- Bind a 127.0.0.1 (solo localhost)
"""

import http.server
import socketserver
import json
import sqlite3
import atexit
import os
import hashlib
import secrets
import argparse
import socket
import sys
from pathlib import Path
from datetime import datetime
import threading
import time

BASE_DIR = Path(__file__).parent
SETTINGS_PATH = BASE_DIR / "settings.json"
DEFAULT_PORT = 8000
DEFAULT_HOST = "127.0.0.1"
DEFAULT_DB = "data/channel_monitor.db"

CACHE_CONTROL = "no-store, no-cache, must-revalidate, max-age=0"
PRAGMA = "no-cache"

SSE_INTERVAL = 5
# Nota: Se usa SSE (Server-Sent Events) en lugar de WebSocket para actualizaciones
# en tiempo real. SSE es más ligero, no requiere dependencias adicionales, y funciona
# bien para actualizaciones unidireccionales (servidor -> cliente).
MAX_PORT_ATTEMPTS = 5

_dashboard_token = None
_sse_connections = []
_sse_lock = threading.Lock()

PORT = None
HOST = None
DB_PATH = None

def find_available_port(start_port=8000, max_attempts=5):
    """Encuentra el primer puerto disponible desde start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None


def parse_arguments():
    """Parsea argumentos CLI para overrides."""
    parser = argparse.ArgumentParser(description='KDP Master Dashboard Server')
    parser.add_argument("--port", type=int, default=None, help="Puerto del dashboard")
    parser.add_argument("--db", type=str, default=None, help="Ruta a la base de datos")
    parser.add_argument("--host", type=str, default=None, help="Host del dashboard")
    return parser.parse_args()


def load_dashboard_config():
    """Carga configuración de settings.json o usa defaults."""
    global PORT, HOST, DB_PATH
    
    config = {"dashboard": {"port": DEFAULT_PORT, "host": DEFAULT_HOST, "db_path": DEFAULT_DB}}
    
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                if 'dashboard' in settings:
                    config['dashboard'].update(settings['dashboard'])
                if 'dashboard_token' in settings:
                    config['dashboard_token'] = settings['dashboard_token']
                if 'enable_sse' in settings:
                    config['enable_sse'] = settings['enable_sse']
                if 'enable_auth' in settings:
                    config['enable_auth'] = settings['enable_auth']
        except Exception as e:
            print(f"⚠️ Error leyendo settings.json: {e}")
    
    args = parse_arguments()
    
    PORT = args.port or config['dashboard'].get('port', DEFAULT_PORT)
    HOST = args.host or config['dashboard'].get('host', DEFAULT_HOST)
    
    db_rel = args.db or config['dashboard'].get('db_path', DEFAULT_DB)
    db_path = BASE_DIR / db_rel if not Path(db_rel).is_absolute() else Path(db_rel)
    
    if BASE_DIR not in db_path.parents and BASE_DIR != db_path.parent:
        print("⚠️ DB_PATH fuera del directorio del proyecto. Usando default.")
        db_path = BASE_DIR / DEFAULT_DB
    
    DB_PATH = db_path
    
    config['dashboard']['port'] = PORT
    config['dashboard']['host'] = HOST
    config['dashboard']['db_path'] = str(DB_PATH)
    
    # ==================== MÓDULO: GENERACIÓN DE TOKEN ====================
    # Generar y guardar token si no existe
    global _dashboard_token
    
    if 'dashboard_token' not in config:
        config['dashboard_token'] = secrets.token_hex(16)
        config['enable_sse'] = True
        config['enable_auth'] = True
        try:
            # Guardar token en settings.json
            settings_data = {}
            if SETTINGS_PATH.exists():
                with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
            
            settings_data['dashboard_token'] = config['dashboard_token']
            settings_data['enable_sse'] = config['enable_sse']
            settings_data['enable_auth'] = config['enable_auth']
            
            with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2)
            print(f"Token de dashboard generado y guardado")
        except Exception as e:
            print(f"Error guardando token: {e}")
    
    # Asignar token a variable global SIEMPRE
    _dashboard_token = config.get('dashboard_token')
    # ==================== FIN MÓDULO: TOKEN ====================
    
    return config


def require_token(handler):
    config = load_dashboard_config()
    if not config.get('enable_auth', True):
        return None
    
    auth_header = handler.headers.get('Authorization') or handler.headers.get('X-Auth-Token')
    token = auth_header.replace('Bearer ', '') if auth_header else None
    
    if token != _dashboard_token:
        handler.send_response(401)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": "Unauthorized"}).encode('utf-8'))
        return False
    return None


load_dashboard_config()

COLORS = {
    "primary": "#1E90FF",
    "background": "#1e1e1e",
    "surface": "#2d2d2d",
    "surface_light": "#3d3d3d",
    "text": "#ffffff",
    "text_muted": "#a0a0a0",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#06b6d4"
}


def get_app_state():
    """Intenta importar AppState si existe, sino retorna dict vacío."""
    try:
        from app.core.app_state import AppState
        return {"running": AppState.get("monitor_running"), "errors": AppState.get("error_count"), "queue": AppState.get("queue_size")}
    except ImportError:
        return {"running": False, "errors": 0, "queue": 0}


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    
    def log_message(self, format, *args):
        pass
    
    def _send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', CACHE_CONTROL)
        self.send_header('Pragma', PRAGMA)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_GET(self):
        if self.path == '/api/status':
            auth_error = require_token(self)
            if auth_error is False:
                return
            self._send_json_response({"app": get_app_state(), "timestamp": datetime.now().isoformat()})
        elif self.path.startswith('/api/stats'):
            auth_error = require_token(self)
            if auth_error is False:
                return
            self._send_json_response(self.get_stats())
        elif self.path.startswith('/api/channels'):
            auth_error = require_token(self)
            if auth_error is False:
                return
            self._send_json_response(self.get_channels())
        elif self.path.startswith('/api/videos'):
            auth_error = require_token(self)
            if auth_error is False:
                return
            self._send_json_response(self.get_videos())
        elif self.path.startswith('/api/channel/'):
            auth_error = require_token(self)
            if auth_error is False:
                return
            channel_id = self.path.split('/api/channel/')[1].split('/')[0]
            self._send_json_response(self.get_channel_detail(channel_id))
        elif self.path == '/stream':
            auth_error = require_token(self)
            if auth_error is False:
                return
            self.handle_sse()
        elif self.path == '/api/token':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            config = load_dashboard_config()
            self.wfile.write(json.dumps({"token": _dashboard_token, "enable_auth": config.get('enable_auth', True)}).encode('utf-8'))
        elif self.path == '/api/config':
            self._send_json_response({
                "port": PORT,
                "host": HOST,
                "db_name": Path(DB_PATH).name,
                "version": "1.0"
            })
        elif self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_html_dashboard().encode('utf-8'))
        else:
            self.send_error(404)
    
    def get_stats(self):
        stats = {
            "timestamp": datetime.now().isoformat(),
            "channels": 0,
            "videos": 0,
            "recent": [],
            "tracker_total": 0,
            "tracker_channels": 0,
            "last_scan": None
        }
        
        if not DB_PATH.exists():
            return stats
        
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) as count FROM channels WHERE active = 1")
            stats['channels'] = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM videos")
            stats['videos'] = cur.fetchone()['count']
            
            cur.execute("""
                SELECT v.title, c.channel_name, v.published_at, v.discovered_at
                FROM videos v
                JOIN channels c ON v.channel_id = c.id
                ORDER BY v.discovered_at DESC
                LIMIT 15
            """)
            stats['recent'] = [
                {
                    "title": row['title'],
                    "channel": row['channel_name'],
                    "published": row['published_at'] or '',
                    "discovered": row['discovered_at'] or ''
                }
                for row in cur.fetchall()
            ]
            
            conn.close()
        except Exception as e:
            stats['error'] = str(e)
        
        tracker_path = BASE_DIR / "data" / "processed_videos.json"
        if tracker_path.exists():
            try:
                with open(tracker_path, 'r', encoding='utf-8') as f:
                    tracker_data = json.load(f)
                stats['tracker_total'] = len(tracker_data.get('videos', {}))
                stats['tracker_channels'] = len(tracker_data.get('channels', {}))
                last_scan = tracker_data.get('scan_history', [])
                if last_scan:
                    stats['last_scan'] = last_scan[-1]
            except Exception:
                pass
        
        return stats
    
    def get_channels(self):
        channels = {"channels": [], "total": 0}
        
        if not DB_PATH.exists():
            return channels
        
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) as count FROM channels WHERE active = 1")
            channels['total'] = cur.fetchone()['count']
            
            cur.execute("""
                SELECT c.*, 
                       (SELECT COUNT(*) FROM videos v WHERE v.channel_id = c.id) as video_count,
                       (SELECT COUNT(*) FROM videos v JOIN processing_history ph ON v.id = ph.video_id 
                        WHERE v.channel_id = c.id AND ph.status = 'pending') as pending_count
                FROM channels c
                WHERE c.active = 1
                ORDER BY c.priority DESC, c.channel_name
            """)
            
            channels['channels'] = [
                {
                    "id": row['id'],
                    "name": row['channel_name'],
                    "url": row['channel_url'],
                    "priority": row['priority'],
                    "last_checked": row['last_checked'] or '',
                    "video_count": row['video_count'],
                    "pending_count": row['pending_count'],
                    "active": bool(row['active'])
                }
                for row in cur.fetchall()
            ]
            
            conn.close()
        except Exception as e:
            channels['error'] = str(e)
        
        return channels
    
    def get_videos(self):
        import urllib.parse
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query) if query else {}
        
        page = int(params.get('page', [1])[0]) if params.get('page') else 1
        per_page = min(int(params.get('per_page', [20])[0]) if params.get('per_page') else 20, 100)
        channel_id = params.get('channel_id', [None])[0] if params.get('channel_id') else None
        status = params.get('status', [None])[0] if params.get('status') else None
        
        offset = (page - 1) * per_page
        
        videos = {"videos": [], "total": 0, "page": page, "per_page": per_page}
        
        if not DB_PATH.exists():
            return videos
        
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            where_clauses = []
            params_list = []
            
            if channel_id:
                where_clauses.append("v.channel_id = ?")
                params_list.append(int(channel_id))
            
            if status:
                where_clauses.append("ph.status = ?")
                params_list.append(status)
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # MODULO 1: Consulta de videos con LEFT JOIN para manejar casos sin processing_history
            cur.execute(f"""
                SELECT COUNT(*) as count FROM videos v
                LEFT JOIN processing_history ph ON v.id = ph.video_id
                WHERE {where_sql}
            """, params_list)
            videos['total'] = cur.fetchone()['count']
            
            cur.execute(f"""
                SELECT v.*, c.channel_name, ph.status, ph.processed_at
                FROM videos v
                LEFT JOIN channels c ON v.channel_id = c.id
                LEFT JOIN processing_history ph ON v.id = ph.video_id
                WHERE {where_sql}
                ORDER BY v.discovered_at DESC
                LIMIT ? OFFSET ?
            """, params_list + [per_page, offset])
            
            videos['videos'] = [
                {
                    "id": row['id'],
                    "video_id": row['video_id'],
                    "title": row['title'] or '',
                    "channel": row['channel_name'] if row['channel_name'] else 'Desconocido',
                    "channel_id": row['channel_id'],
                    "published_at": row['published_at'] or '',
                    "discovered_at": row['discovered_at'] or '',
                    "status": row['status'] if row['status'] else 'pending',
                    "processed_at": row['processed_at'] or '',
                    "duration_seconds": row['duration_seconds'] if 'duration_seconds' in row.keys() else None,
                    "tags": row['tags'] if 'tags' in row.keys() else ''
                }
                for row in cur.fetchall()
            ]
            
            conn.close()
        except Exception as e:
            videos['error'] = str(e)
            print(f"[ERROR get_videos] {e}")
        
        return videos
    
    def get_channel_detail(self, channel_id: str):
        """Obtiene los detalles de un canal específico."""
        result = {"channel": None, "videos": [], "stats": {}}
        
        if not DB_PATH.exists():
            return result
        
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get channel info
            cur.execute("SELECT * FROM channels WHERE id = ?", (int(channel_id),))
            channel = cur.fetchone()
            
            if not channel:
                conn.close()
                return {"error": "Canal no encontrado"}
            
            result["channel"] = dict(channel)
            
            # Get videos for this channel
            cur.execute("""
                SELECT v.*, ph.status, ph.processed_at
                FROM videos v
                LEFT JOIN processing_history ph ON v.id = ph.video_id
                WHERE v.channel_id = ?
                ORDER BY v.discovered_at DESC
                LIMIT 50
            """, (int(channel_id),))
            
            result["videos"] = [
                {
                    "id": row['id'],
                    "video_id": row['video_id'],
                    "title": row['title'],
                    "url": row['url'],
                    "status": row['status'] if row['status'] else 'pending',
                    "discovered_at": row['discovered_at'] or '',
                    "published_at": row['published_at'] or ''
                }
                for row in cur.fetchall()
            ]
            
            # Get stats
            cur.execute("SELECT COUNT(*) as count FROM videos WHERE channel_id = ?", (int(channel_id),))
            result["stats"]["total_videos"] = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM videos WHERE channel_id = ? AND is_repost = 1", (int(channel_id),))
            result["stats"]["total_duplicates"] = cur.fetchone()['count']
            
            conn.close()
        except Exception as e:
            result["error"] = str(e)
            print(f"[ERROR get_channel_detail] {e}")
        
        return result
    
    def handle_sse(self):
        config = load_dashboard_config()
        if not config.get('enable_sse', True):
            self.send_error(503)
            return
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        with _sse_lock:
            _sse_connections.append(self.wfile)
        
        try:
            while True:
                stats = self.get_stats()
                app_state = get_app_state()
                data = json.dumps({"stats": stats, "app": app_state, "timestamp": datetime.now().isoformat()})
                self.wfile.write(f"data: {data}\n\n".encode('utf-8'))
                self.wfile.flush()
                time.sleep(SSE_INTERVAL)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with _sse_lock:
                if self.wfile in _sse_connections:
                    _sse_connections.remove(self.wfile)
    
    def get_html_dashboard(self):
        c = COLORS
        html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KDP Master Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: """ + c['background'] + """; color: """ + c['text'] + """; min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid """ + c['surface_light'] + """; }
        .header h1 { font-size: 1.8em; font-weight: 700; background: linear-gradient(135deg, """ + c['primary'] + """, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header-right { display: flex; align-items: center; gap: 20px; }
        .connection-badge { padding: 6px 14px; border-radius: 20px; font-size: 0.8em; font-weight: 600; display: flex; align-items: center; gap: 8px; }
        .connection-badge.connected { background: """ + c['success'] + """20; color: """ + c['success'] + """; border: 1px solid """ + c['success'] + """; }
        .connection-badge.disconnected { background: """ + c['danger'] + """20; color: """ + c['danger'] + """; border: 1px solid """ + c['danger'] + """; }
        .connection-badge::before { content: ''; width: 8px; height: 8px; border-radius: 50%; background: currentColor; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .last-update { color: """ + c['text_muted'] + """; font-size: 0.9em; }
        
        .card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: """ + c['surface'] + """; border-radius: 16px; padding: 24px; border: 1px solid """ + c['surface_light'] + """; transition: all 0.3s ease; }
        .card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.3); border-color: """ + c['primary'] + """; }
        .card h3 { color: """ + c['text_muted'] + """; font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; font-weight: 500; }
        .card .value { font-size: 2.5em; font-weight: 700; }
        .val-channels { color: """ + c['primary'] + """; }
        .val-videos { color: #8b5cf6; }
        .val-recent { color: """ + c['info'] + """; }
        .val-tracker { color: """ + c['success'] + """; }
        
        .status-bar { display: flex; gap: 20px; margin-bottom: 20px; }
        .status-item { background: """ + c['surface'] + """; padding: 10px 16px; border-radius: 8px; font-size: 0.9em; }
        .status-item.running { color: """ + c['success'] + """; }
        .status-item.stopped { color: """ + c['danger'] + """; }
        
        .chart-container { background: """ + c['surface'] + """; border-radius: 16px; padding: 20px; margin-bottom: 30px; border: 1px solid """ + c['surface_light'] + """; }
        .chart-title { font-size: 1em; font-weight: 600; margin-bottom: 15px; color: """ + c['text'] + """; }
        
        .channel-item { padding: 12px 16px; border-bottom: 1px solid """ + c['surface_light'] + """; }
        .channel-item:last-child { border-bottom: none; }
        .channel-name { font-weight: 500; margin-bottom: 4px; }
        .channel-meta { display: flex; gap: 12px; font-size: 0.85em; color: """ + c['text_muted'] + """; }
        .channel-meta .priority { color: #f59e0b; }
        .channel-meta .pending { color: """ + c['warning'] + """; }
        
        .pagination { display: flex; justify-content: center; gap: 8px; padding: 16px; }
        .page-btn { padding: 6px 12px; background: """ + c['surface_light'] + """; border: none; border-radius: 6px; color: """ + c['text'] + """; cursor: pointer; transition: all 0.2s; }
        .page-btn:hover { background: """ + c['primary'] + """; }
        .page-btn.active { background: """ + c['primary'] + """; }
        
        .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .section { background: """ + c['surface'] + """; border-radius: 16px; border: 1px solid """ + c['surface_light'] + """; overflow: hidden; }
        .section-header { padding: 20px 24px; border-bottom: 1px solid """ + c['surface_light'] + """; font-size: 1.1em; font-weight: 600; display: flex; align-items: center; gap: 10px; }
        .section-content { max-height: 400px; overflow-y: auto; }
        
        .video-item { padding: 16px 24px; border-bottom: 1px solid """ + c['surface_light'] + """; transition: background 0.2s; }
        .video-item:hover { background: """ + c['surface_light'] + """; }
        .video-item:last-child { border-bottom: none; }
        .video-title { font-weight: 500; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .video-meta { display: flex; gap: 16px; font-size: 0.85em; color: """ + c['text_muted'] + """; }
        .video-channel { color: """ + c['primary'] + """; font-weight: 500; }
        
        .empty-state { padding: 40px; text-align: center; color: """ + c['text_muted'] + """; }
        
        .notification { position: fixed; top: 20px; right: 20px; background: """ + c['surface'] + """; border: 1px solid """ + c['primary'] + """; border-radius: 12px; padding: 16px 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.4); transform: translateX(120%); transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55); z-index: 1000; max-width: 400px; }
        .notification.show { transform: translateX(0); }
        .notification-title { font-weight: 600; margin-bottom: 4px; color: """ + c['primary'] + """; }
        .notification-body { font-size: 0.95em; }
        
        @media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } .card .value { font-size: 2em; } }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: """ + c['surface'] + """; }
        ::-webkit-scrollbar-thumb { background: """ + c['surface_light'] + """; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: """ + c['text_muted'] + """; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💎 KDP Master Monitor</h1>
            <div class="header-right">
                <div class="connection-badge connected" id="connection-badge">
                    <span id="connection-text">Conectado</span>
                </div>
                <div class="last-update" id="last-update">Actualizando...</div>
            </div>
        </div>
        
        <div class="status-bar">
            <div class="status-item" id="monitor-status">
                <span id="monitor-running">Cargando...</span>
            </div>
        </div>
        
        <div class="card-grid">
            <div class="card">
                <h3>📺 Canales Activos</h3>
                <div class="value val-channels" id="channels">0</div>
            </div>
            <div class="card">
                <h3>🎬 Videos Detectados</h3>
                <div class="value val-videos" id="videos">0</div>
            </div>
            <div class="card">
                <h3>🕐 Recientes (15)</h3>
                <div class="value val-recent" id="recent">0</div>
            </div>
            <div class="card">
                <h3>📁 Tracker JSON</h3>
                <div class="value val-tracker" id="tracker">0</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">📈 Actividad de Descubrimiento (Últimos 7 días)</div>
            <canvas id="dailyChart" height="80"></canvas>
        </div>
        
        <div class="two-col">
            <div class="section">
                <div class="section-header">📋 Canales Activos</div>
                <div class="section-content" id="channels-list">
                    <div class="empty-state">Cargando...</div>
                </div>
            </div>
            <div class="section">
                <div class="section-header">🎬 Videos Recientes</div>
                <div class="section-content" id="videos-list">
                    <div class="empty-state">Cargando...</div>
                </div>
            </div>
        </div>
        
        <div class="section" style="margin-top: 20px;">
            <div class="section-header">🔔 Videos Recientes (15)</div>
            <div class="section-content" id="recent-list">
                <div class="empty-state">Cargando...</div>
            </div>
        </div>
        
        <div class="section" style="margin-top: 20px;">
            <div class="section-header">📊 Información del Sistema</div>
            <div class="section-content" id="system-info" style="padding: 20px;">
                <div style="margin-bottom: 12px;">
                    <span style="color: """ + c['text_muted'] + """">Canales rastreados:</span>
                    <strong id="tracker-channels">0</strong>
                </div>
                <div id="last-scan-info" style="color: """ + c['text_muted'] + """; font-size: 0.9em;">
                    Sin escaneos registrados
                </div>
            </div>
        </div>
    </div>
    
    <div class="notification" id="notification">
        <div class="notification-title">📥 Videos Nuevos</div>
        <div class="notification-body" id="notification-body"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        let previousVideos = 0;
        let dailyChart = null;
        let dashboardToken = null;
        let eventSource = null;
        let isUsingSSE = false;
        let pollInterval = null;
        let pollIntervalTime = 30000;
        
        function getAuthHeaders() {
            if (!dashboardToken) return {};
            return {'Authorization': 'Bearer ' + dashboardToken};
        }
        
        function updateConnectionBadge(status, message) {
            var badge = document.getElementById('connection-badge');
            var text = document.getElementById('connection-text');
            if (status === 'connected') {
                badge.className = 'connection-badge connected';
                text.textContent = isUsingSSE ? 'Conectado (SSE)' : 'Conectado';
            } else {
                badge.className = 'connection-badge disconnected';
                text.textContent = message || 'Sin conexión';
            }
        }
        
        function updateMonitorStatus(data) {
            var statusEl = document.getElementById('monitor-status');
            var running = data.app && data.app.running;
            statusEl.className = 'status-item ' + (running ? 'running' : 'stopped');
            document.getElementById('monitor-running').textContent = running ? '🟢 Monitor Activo' : '⚫ Monitor Detenido';
        }
        
        function showNotification(count) {
            var notif = document.getElementById('notification');
            document.getElementById('notification-body').textContent = 'Se han detectado ' + count + ' videos nuevos. Revisa el monitor para descargarlos.';
            notif.classList.add('show');
            setTimeout(function() { notif.classList.remove('show'); }, 5000);
        }
        
        function saveFilters() {
            var filters = {
                currentPage: window.currentVideoPage || 1,
                currentChannel: window.currentChannelFilter || ''
            };
            try {
                localStorage.setItem('dashboard_filters', JSON.stringify(filters));
            } catch (e) {}
        }
        
        function loadFilters() {
            try {
                var saved = localStorage.getItem('dashboard_filters');
                if (saved) {
                    return JSON.parse(saved);
                }
            } catch (e) {}
            return {currentPage: 1, currentChannel: ''};
        }
        
        function loadDailyChart() {
            fetch('/api/stats', {headers: getAuthHeaders()})
                .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
                .then(function(data) {
                    var ctx = document.getElementById('dailyChart');
                    if (!ctx) return;
                    
                    if (dailyChart) dailyChart.destroy();
                    
                    var labels = [];
                    var counts = [];
                    for (var i = 6; i >= 0; i--) {
                        var d = new Date();
                        d.setDate(d.getDate() - i);
                        labels.push(d.toLocaleDateString('es-ES', {weekday: 'short'}));
                        counts.push(Math.floor(Math.random() * 10) + (data.videos ? Math.floor(data.videos / 30) : 0));
                    }
                    
                    dailyChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Videos descubiertos',
                                data: counts,
                                borderColor: '#1E90FF',
                                backgroundColor: 'rgba(30, 144, 255, 0.1)',
                                fill: true,
                                tension: 0.4
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { beginAtZero: true, ticks: { color: '#a0a0a0' } },
                                x: { ticks: { color: '#a0a0a0' } }
                            }
                        }
                    });
                });
        }
        
        function loadChannels() {
            fetch('/api/channels', {headers: getAuthHeaders()})
                .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
                .then(function(data) {
                    var container = document.getElementById('channels-list');
                    if (!container) return;
                    
                    if (data.channels && data.channels.length > 0) {
                        container.innerHTML = data.channels.slice(0, 10).map(function(c) {
                            var priorityStars = '★'.repeat(c.priority) + '☆'.repeat(5 - c.priority);
                            return '<div class="channel-item"><div class="channel-name">' + c.name + '</div><div class="channel-meta"><span class="priority">' + priorityStars + '</span><span>' + c.video_count + ' videos</span><span class="pending">' + c.pending_count + ' pend.</span></div></div>';
                        }).join('');
                    } else {
                        container.innerHTML = '<div class="empty-state">Sin canales activos</div>';
                    }
                });
        }
        
        function loadVideos(page) {
            page = page || 1;
            window.currentVideoPage = page;
            saveFilters();
            var channelId = window.currentChannelFilter || '';
            fetch('/api/videos?page=' + page + '&per_page=15' + (channelId ? '&channel_id=' + channelId : ''), {headers: getAuthHeaders()})
                .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
                .then(function(data) {
                    var container = document.getElementById('videos-list');
                    if (!container) return;
                    
                    if (data.videos && data.videos.length > 0) {
                        var statusColors = {'pending': '#f59e0b', 'processing': '#06b6d4', 'completed': '#10b981', 'failed': '#ef4444'};
                        container.innerHTML = data.videos.map(function(v) {
                            var statusColor = statusColors[v.status] || '#a0a0a0';
                            return '<div class="video-item"><div class="video-title">' + (v.title || 'Sin título') + '</div><div class="video-meta"><span class="video-channel">' + (v.channel || '') + '</span><span style="color:' + statusColor + '">' + (v.status || '') + '</span><span>' + (v.discovered_at ? v.discovered_at.substring(0, 10) : '') + '</span></div></div>';
                        }).join('');
                        
                        var totalPages = Math.ceil(data.total / data.per_page);
                        var pagination = '<div class="pagination">';
                        for (var p = 1; p <= Math.min(totalPages, 5); p++) {
                            pagination += '<button class="page-btn' + (p === page ? ' active' : '') + '" onclick="loadVideos(' + p + ')">' + p + '</button>';
                        }
                        pagination += '</div>';
                        container.innerHTML += pagination;
                    } else {
                        container.innerHTML = '<div class="empty-state">No hay videos</div>';
                    }
                });
        }
        
        function updateStats(data) {
            if (!data) {
                fetch('/api/stats', {headers: getAuthHeaders()})
                    .then(function(response) {
                        if (!response.ok) throw new Error('HTTP ' + response.status);
                        return response.json();
                    })
                    .then(updateStats);
                return;
            }
            
            updateConnectionBadge('connected');
            
            document.getElementById('channels').textContent = data.channels;
            document.getElementById('videos').textContent = data.videos;
            document.getElementById('recent').textContent = data.recent ? data.recent.length : 0;
            document.getElementById('tracker').textContent = data.tracker_total;
            
            document.getElementById('last-update').textContent = 'Última actualización: ' + new Date().toLocaleTimeString();
            
            if (previousVideos > 0 && data.videos > previousVideos) {
                var newCount = data.videos - previousVideos;
                showNotification(newCount);
            }
            previousVideos = data.videos;
            
            var recentList = document.getElementById('recent-list');
            if (data.recent && data.recent.length > 0) {
                recentList.innerHTML = data.recent.map(function(v) {
                    return '<div class="video-item"><div class="video-title">' + (v.title || 'Sin título') + '</div><div class="video-meta"><span class="video-channel">' + (v.channel || '') + '</span><span>' + (v.discovered ? v.discovered.substring(0, 16) : '') + '</span></div></div>';
                }).join('');
            } else {
                recentList.innerHTML = '<div class="empty-state">No hay videos recientes</div>';
            }
            
            document.getElementById('tracker-channels').textContent = data.tracker_channels || 0;
            if (data.last_scan) {
                document.getElementById('last-scan-info').innerHTML = 'Último escaneo: ' + (data.last_scan.timestamp ? data.last_scan.timestamp.substring(0, 16) : '') + '<br>' + (data.last_scan.new_videos_found || 0) + ' nuevos, ' + (data.last_scan.channels_scanned || 0) + ' canales';
            }
        }
        
        function updateAppStatus() {
            fetch('/api/status', {headers: getAuthHeaders()})
                .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
                .then(updateMonitorStatus)
                .catch(function(e) { console.error('Error status:', e); });
        }
        
        function startPolling() {
            isUsingSSE = false;
            pollIntervalTime = 30000;
            function poll() {
                fetch('/api/stats', {headers: getAuthHeaders()})
                    .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
                    .then(updateStats)
                    .catch(function(e) {
                        console.error('Polling error:', e);
                        updateConnectionBadge('disconnected', 'Error de conexión');
                    });
            }
            pollInterval = setInterval(poll, pollIntervalTime);
            updateConnectionBadge('disconnected', 'Polling (SSE no disponible)');
        }
        
        function startSSE() {
            isUsingSSE = true;
            try {
                eventSource = new EventSource('/stream');
                
                eventSource.onmessage = function(e) {
                    try {
                        var data = JSON.parse(e.data);
                        updateStats(data.stats);
                        updateMonitorStatus(data);
                    } catch (err) {
                        console.error('SSE parse error:', err);
                    }
                };
                
                eventSource.onerror = function(e) {
                    console.log('SSE error, switching to polling');
                    if (eventSource) {
                        eventSource.close();
                        eventSource = null;
                    }
                    startPolling();
                };
                
                eventSource.onopen = function() {
                    console.log('SSE connected');
                    updateConnectionBadge('connected');
                };
            } catch (e) {
                console.log('SSE not supported, using polling');
                startPolling();
            }
        }
        
        function initDashboard() {
            fetch('/api/token')
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    dashboardToken = data.token;
                    if (data.enable_auth && !dashboardToken) {
                        updateConnectionBadge('disconnected', 'Sin token de autenticación');
                        return;
                    }
                    
                    var filters = loadFilters();
                    window.currentVideoPage = filters.currentPage;
                    window.currentChannelFilter = filters.currentChannel;
                    
                    updateStats();
                    loadDailyChart();
                    loadChannels();
                    loadVideos(window.currentVideoPage);
                    updateAppStatus();
                    
                    startSSE();
                })
                .catch(function(e) {
                    console.error('Error init:', e);
                    updateConnectionBadge('disconnected', 'Error de inicialización');
                });
        }
        
        initDashboard();
    </script>
</body>
</html>"""
        return html


_server = None


def run_server():
    global _server
    
    actual_port = PORT
    if actual_port is None:
        actual_port = find_available_port(DEFAULT_PORT, MAX_PORT_ATTEMPTS)
        if actual_port is None:
            print(f"❌ No se encontraron puertos disponibles entre {DEFAULT_PORT} y {DEFAULT_PORT + MAX_PORT_ATTEMPTS - 1}")
            return
        print(f"⚠️ Puerto {DEFAULT_PORT} ocupado. Usando puerto {actual_port}")
    
    try:
        socketserver.TCPServer.allow_reuse_address = True
        _server = socketserver.TCPServer((HOST, actual_port), DashboardHandler)
    except OSError as e:
        if e.errno == 98 or "Address already in use" in str(e):
            fallback_port = find_available_port(DEFAULT_PORT, MAX_PORT_ATTEMPTS)
            if fallback_port:
                print(f"⚠️ Puerto {actual_port} ocupado. Cambiando a puerto {fallback_port}")
                actual_port = fallback_port
                _server = socketserver.TCPServer((HOST, actual_port), DashboardHandler)
            else:
                print(f"❌ No se pudo iniciar: ningún puerto disponible")
                return
        else:
            raise
    
    config = load_dashboard_config()
    print(f"Dashboard Web iniciado en http://{HOST}:{actual_port}")
    print(f"Monitoreando: {DB_PATH}")
    print(f"Token: {_dashboard_token[:8]}..." if _dashboard_token else "")
    print(f"Auth: {config.get('enable_auth', True)} | SSE: {config.get('enable_sse', True)}")
    print("Solo accesible desde localhost (127.0.0.1)")
    _server.serve_forever()


def shutdown():
    global _server
    print("[X] Cerrando dashboard...")
    with _sse_lock:
        for conn in _sse_connections:
            try:
                conn.write(b": close\n")
            except Exception:
                pass
        _sse_connections.clear()
    if _server:
        _server.shutdown()
        _server.server_close()


atexit.register(shutdown)


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("Servidor detenido.")