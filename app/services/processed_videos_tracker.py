"""
KDP_MASTER - Video Processed Tracker (Indestructible JSON Cache)
================================================================
Respaldo paralelo e indestructible de todos los videos escaneados/procesados.
Complementa a SQLite: si la DB se corrompe, este JSON sobrevive.
NUNCA borra registros, solo añade.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ProcessedVideosTracker:
    """Registro indestructible de videos procesados en formato JSON."""
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            import sys
            if getattr(sys, 'frozen', False):
                self.base_dir = Path(sys.executable).parent
            else:
                self.base_dir = Path(__file__).parent.parent.parent
        else:
            self.base_dir = Path(base_dir)
        
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tracker_file = self.data_dir / "processed_videos.json"
        self.data = self._load()
    
    def _load(self) -> Dict:
        """Carga el registro existente o crea uno nuevo."""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Asegurar estructura completa
                data.setdefault('videos', {})
                data.setdefault('channels', {})
                data.setdefault('scan_history', [])
                data.setdefault('statistics', {
                    'total_scanned': 0,
                    'total_new': 0,
                    'total_duplicates': 0,
                    'total_downloaded': 0,
                    'total_failed': 0
                })
                # Recalcular stats desde datos reales para evitar inconsistencias
                stats = data['statistics']
                actual_new = len(data['videos'])
                actual_downloaded = sum(1 for v in data['videos'].values() if v.get('status') == 'downloaded')
                actual_failed = sum(1 for v in data['videos'].values() if v.get('status') == 'failed')
                if stats['total_new'] != actual_new:
                    stats['total_new'] = actual_new
                if stats['total_downloaded'] != actual_downloaded:
                    stats['total_downloaded'] = actual_downloaded
                if stats['total_failed'] != actual_failed:
                    stats['total_failed'] = actual_failed
                return data
            except (json.JSONDecodeError, KeyError):
                pass
        
        return {
            'videos': {},
            'channels': {},
            'scan_history': [],
            'statistics': {
                'total_scanned': 0,
                'total_new': 0,
                'total_duplicates': 0,
                'total_downloaded': 0,
                'total_failed': 0
            },
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    
    def _save(self):
        """Guarda el registro completo. NUNCA borra, solo sobrescribe con todo."""
        self.data['last_updated'] = datetime.now().isoformat()
        tmp_file = self.tracker_file.with_suffix('.tmp')
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        tmp_file.replace(self.tracker_file)
    
    def _make_video_hash(self, video_id: str, channel_id: str) -> str:
        return hashlib.sha256(f"{video_id}::{channel_id}".encode()).hexdigest()
    
    def is_video_processed(self, video_id: str, channel_id: str) -> bool:
        h = self._make_video_hash(video_id, channel_id)
        return h in self.data['videos']
    
    def register_video(self, video_id: str, channel_id: str, channel_name: str,
                       title: str = "", video_url: str = "", published_at: str = "",
                       status: str = "detected") -> bool:
        """
        Registra un video. Si ya existe, retorna False (duplicado).
        Si es nuevo, lo registra y retorna True.
        NUNCA borra nada previo.
        """
        h = self._make_video_hash(video_id, channel_id)
        
        if h in self.data['videos']:
            self.data['statistics']['total_duplicates'] += 1
            return False
        
        self.data['videos'][h] = {
            'video_id': video_id,
            'channel_id': channel_id,
            'channel_name': channel_name,
            'title': title,
            'video_url': video_url,
            'published_at': published_at,
            'status': status,
            'registered_at': datetime.now().isoformat()
        }
        
        if channel_id not in self.data['channels']:
            self.data['channels'][channel_id] = {
                'name': channel_name,
                'video_hashes': []
            }
        
        self.data['channels'][channel_id]['video_hashes'].append(h)
        self.data['statistics']['total_new'] += 1
        self._save()
        return True
    
    def update_video_status(self, video_id: str, channel_id: str, new_status: str):
        h = self._make_video_hash(video_id, channel_id)
        if h in self.data['videos']:
            self.data['videos'][h]['status'] = new_status
            if new_status == 'downloaded':
                self.data['statistics']['total_downloaded'] += 1
            elif new_status == 'failed':
                self.data['statistics']['total_failed'] += 1
            self._save()
    
    def record_scan(self, channels_scanned: int, new_found: int, duplicates: int,
                    duration_seconds: float = 0):
        """Registra un escaneo en el historial."""
        scan_record = {
            'timestamp': datetime.now().isoformat(),
            'channels_scanned': channels_scanned,
            'new_videos_found': new_found,
            'duplicates_found': duplicates,
            'duration_seconds': round(duration_seconds, 2)
        }
        self.data['scan_history'].append(scan_record)
        self.data['statistics']['total_scanned'] += new_found + duplicates
        self._save()
        return scan_record
    
    def get_stats(self) -> Dict:
        return {
            'total_videos_tracked': len(self.data['videos']),
            'total_channels_tracked': len(self.data['channels']),
            'total_scans': len(self.data.get('scan_history', [])),
            'statistics': self.data['statistics'],
            'last_scan': self.data['scan_history'][-1] if self.data.get('scan_history') else None,
            'file_size_kb': round(self.tracker_file.stat().st_size / 1024, 1) if self.tracker_file.exists() else 0
        }
    
    def get_videos_by_channel(self, channel_id: str) -> List[Dict]:
        if channel_id not in self.data['channels']:
            return []
        result = []
        for h in self.data['channels'][channel_id]['video_hashes']:
            if h in self.data['videos']:
                result.append(self.data['videos'][h])
        return result
    
    def get_recent_videos(self, limit: int = 50) -> List[Dict]:
        videos = sorted(
            self.data['videos'].values(),
            key=lambda v: v.get('registered_at', ''),
            reverse=True
        )
        return videos[:limit]
