"""
Módulo P1-7: Filtro de Fecha Rápida (Slider)
Permite filtrar videos por rango de fechas con slider visual.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import Optional, Callable, Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)


class DateFilterSlider(ttk.Frame):
    """Widget de filtro de fecha con slider para filtrado rápido."""

    DEFAULT_PRESETS = {
        "Hoy": 0,
        "Ayer": 1,
        "Últimos 3 días": 3,
        "Última semana": 7,
        "Últimas 2 semanas": 14,
        "Último mes": 30,
        "Últimos 3 meses": 90,
        "Últimos 6 meses": 180,
        "Último año": 365,
        "Todo": None
    }

    def __init__(
        self,
        parent,
        on_change: Optional[Callable[[Optional[Tuple[datetime, datetime]]], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.on_change_callback = on_change
        self._selected_days = None
        self._selected_preset = None

        self._create_widgets()

    def _create_widgets(self):
        """Crea los widgets del filtro de fecha."""
        label_frame = ttk.LabelFrame(self, text="📅 Filtrar por Fecha", padding=5)
        label_frame.pack(fill=tk.X, padx=5, pady=5)

        self.preset_var = tk.StringVar(value="Último mes")

        preset_frame = ttk.Frame(label_frame)
        preset_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(preset_frame, text="Preset:").pack(side=tk.LEFT, padx=2)

        preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_var,
            values=list(self.DEFAULT_PRESETS.keys()),
            state="readonly",
            width=20
        )
        preset_combo.pack(side=tk.LEFT, padx=2)
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        self.custom_frame = ttk.Frame(label_frame)
        self.custom_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.custom_frame, text="Rango personalizado:").pack(anchor=tk.W)

        range_frame = ttk.Frame(self.custom_frame)
        range_frame.pack(fill=tk.X, pady=2)

        self.from_date_var = tk.StringVar()
        self.to_date_var = tk.StringVar()

        ttk.Label(range_frame, text="Desde:").pack(side=tk.LEFT, padx=2)
        from_entry = ttk.Entry(range_frame, textvariable=self.from_date_var, width=12)
        from_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(range_frame, text="Hasta:").pack(side=tk.LEFT, padx=2)
        to_entry = ttk.Entry(range_frame, textvariable=self.to_date_var, width=12)
        to_entry.pack(side=tk.LEFT, padx=2)

        self.apply_custom_btn = ttk.Button(
            self.custom_frame,
            text="Aplicar Rango",
            command=self._apply_custom_range
        )
        self.apply_custom_btn.pack(pady=2)

        self.slider_frame = ttk.Frame(label_frame)
        self.slider_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.slider_frame, text="Días hacia atrás:").pack(anchor=tk.W)

        self.days_var = tk.IntVar(value=30)

        self.days_slider = ttk.Scale(
            self.slider_frame,
            from_=0,
            to=365,
            variable=self.days_var,
            orient=tk.HORIZONTAL,
            command=self._on_slider_change
        )
        self.days_slider.pack(fill=tk.X, padx=5, pady=2)

        self.days_label = ttk.Label(
            self.slider_frame,
            text=f"Seleccionado: {self.days_var.get()} días",
            font=("Segoe UI", 9)
        )
        self.days_label.pack()

        self.info_label = ttk.Label(
            label_frame,
            text="💡 Los filtros de fecha reducen el procesamiento de videos antiguos",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        self.info_label.pack(pady=(5, 0))

    def _on_slider_change(self, value):
        """Maneja el cambio del slider."""
        days = int(float(value))
        self.days_label.config(text=f"Seleccionado: {days} días")
        self.preset_var.set("Personalizado")
        self._selected_days = days
        if self.on_change_callback:
            date_range = self._calculate_date_range(days)
            self.on_change_callback(date_range)

    def _on_preset_change(self, event):
        """Maneja la selección de un preset."""
        preset_name = self.preset_var.get()
        days = self.DEFAULT_PRESETS.get(preset_name)
        self._selected_preset = preset_name
        self._selected_days = days

        if days is None:
            if self.on_change_callback:
                self.on_change_callback(None)
            self.days_label.config(text="Seleccionado: Todo")
        else:
            self.days_var.set(days)
            self.days_label.config(text=f"Seleccionado: {days} días")
            if self.on_change_callback:
                date_range = self._calculate_date_range(days)
                self.on_change_callback(date_range)

    def _apply_custom_range(self):
        """Aplica un rango de fechas personalizado."""
        try:
            from_date_str = self.from_date_var.get()
            to_date_str = self.to_date_var.get()

            if from_date_str and to_date_str:
                from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
                to_date = datetime.strptime(to_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

                if self.on_change_callback:
                    self.on_change_callback((from_date, to_date))

                self.preset_var.set("Personalizado")
                logger.info(f"Rango personalizado aplicado: {from_date_str} - {to_date_str}")
        except ValueError as e:
            logger.warning(f"Formato de fecha inválido: {e}")

    def _calculate_date_range(self, days: int) -> Optional[Tuple[datetime, datetime]]:
        """Calcula el rango de fechas para los últimos N días."""
        if days is None:
            return None
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        return (from_date, to_date)

    def get_date_range(self) -> Optional[Tuple[datetime, datetime]]:
        """Retorna el rango de fecha actual seleccionado."""
        if self._selected_days is None:
            return None
        return self._calculate_date_range(self._selected_days)

    def set_date_range(self, from_date: datetime, to_date: datetime):
        """Establece un rango de fecha específico."""
        delta = (to_date - from_date).days
        self.days_var.set(delta)
        self.days_label.config(text=f"Seleccionado: {delta} días")
        self.preset_var.set("Personalizado")
        self._selected_days = delta

    def reset(self):
        """Reinicia el filtro a valores por defecto."""
        self.preset_var.set("Último mes")
        self.days_var.set(30)
        self.days_label.config(text="Seleccionado: 30 días")
        self.from_date_var.set("")
        self.to_date_var.set("")
        self._selected_days = 30
        self._selected_preset = None
        if self.on_change_callback:
            self.on_change_callback(self._calculate_date_range(30))


def filter_videos_by_date(
    videos: List[Dict],
    date_range: Optional[Tuple[datetime, datetime]]
) -> List[Dict]:
    """
    Filtra una lista de videos por rango de fecha.
    Args:
        videos: Lista de diccionarios con ключ 'discovered_at' o 'upload_date'
        date_range: Tupla (from_date, to_date) o None para返回 todos
    Returns:
        Lista filtrada de videos
    """
    if date_range is None:
        return videos

    from_date, to_date = date_range
    filtered = []

    for video in videos:
        discovered = video.get('discovered_at') or video.get('upload_date')
        if discovered:
            try:
                if isinstance(discovered, str):
                    video_date = datetime.fromisoformat(discovered.replace('Z', '+00:00'))
                else:
                    video_date = discovered

                if from_date <= video_date <= to_date:
                    filtered.append(video)
            except Exception:
                filtered.append(video)

    return filtered


def create_date_filter_dialog(parent, on_apply: Callable) -> Optional[Tuple[datetime, datetime]]:
    """
    Crea un diálogo de filtro de fecha y retorna el rango seleccionado.
    """
    dialog = tk.Toplevel(parent)
    dialog.title("Filtrar Videos por Fecha")
    dialog.geometry("400x300")
    dialog.transient(parent)

    filter_widget = DateFilterSlider(
        dialog,
        on_change=lambda dr: setattr(dialog, '_date_range', dr)
    )
    filter_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    dialog._date_range = None

    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(fill=tk.X, padx=10, pady=10)

    def on_apply():
        dialog._date_range = filter_widget.get_date_range()
        dialog.destroy()

    ttk.Button(btn_frame, text="Aplicar", command=on_apply).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="Limpiar Filtro", command=filter_widget.reset).pack(side=tk.LEFT, padx=2)

    dialog.wait_window()
    return dialog._date_range