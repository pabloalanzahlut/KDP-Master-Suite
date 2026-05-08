import tkinter as tk
from tkinter import ttk
import time
from collections import deque


class ETACalculator:
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.times = deque(maxlen=window_size)
        self.start_time = None
    
    def start(self):
        self.start_time = time.time()
    
    def add_sample(self, duration_seconds):
        self.times.append(duration_seconds)
    
    def estimate_remaining(self, remaining_files):
        if not self.times or self.start_time is None:
            return None
        avg = sum(self.times) / len(self.times)
        return avg * remaining_files
    
    def get_elapsed(self):
        if self.start_time is None:
            return 0
        return time.time() - self.start_time


class FileProgressItem(ttk.Frame):
    STATES = {
        'queued': ('⏳', 'Pendiente', 'gray'),
        'processing': ('⚙️', 'Procesando...', 'blue'),
        'completed': ('✅', 'Completado', 'green'),
        'error': ('❌', 'Error', 'red'),
        'duplicate': ('⏭️', 'Duplicado', 'orange'),
        'retry': ('🔄', 'Reintentando...', 'yellow')
    }
    
    def __init__(self, parent, filename, on_retry=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.filename = filename
        self.on_retry = on_retry
        self._last_update_time = 0
        self._last_percent = -1
        self._last_state = None
        self._file_start_time = None
        self._file_size = 0
        
        self._build_ui()
    
    def _build_ui(self):
        container = ttk.Frame(self, padding=5)
        container.pack(fill=tk.X, expand=True)
        
        header = ttk.Frame(container)
        header.pack(fill=tk.X)
        
        self.icon_label = ttk.Label(header, text='⏳', font=('Segoe UI', 10))
        self.icon_label.pack(side=tk.LEFT)
        
        self.filename_label = ttk.Label(
            header, text=self._truncate_filename(self.filename),
            font=('Inter', 9, 'bold'), wraplength=150
        )
        self.filename_label.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        self.progress_bar = ttk.Progressbar(
            container, orient=tk.HORIZONTAL, length=100, mode='determinate', maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        info_frame = ttk.Frame(container)
        info_frame.pack(fill=tk.X, pady=(3, 0))
        
        self.status_label = ttk.Label(info_frame, text='Pendiente', font=('Inter', 8), foreground='gray')
        self.status_label.pack(side=tk.LEFT)
        
        self.details_label = ttk.Label(info_frame, text='', font=('Consolas', 8), foreground='#888')
        self.details_label.pack(side=tk.RIGHT)
        
        self.retry_btn = ttk.Button(
            container, text='🔄 Reintentar', command=self._handle_retry,
            style='Small.TButton'
        )
    
    def _truncate_filename(self, name, max_len=25):
        if len(name) <= max_len:
            return name
        return name[:max_len-3] + '...'
    
    def _handle_retry(self):
        if self.on_retry and hasattr(self, '_current_state') and self._current_state == 'error':
            self.on_retry(self.filename)
    
    def update(self, percent, state, eta_seconds=None, speed=None):
        current_time = time.time()
        
        if state in ('completed', 'error', 'duplicate'):
            should_update = True
        elif state != self._last_state:
            should_update = True
        elif current_time - self._last_update_time >= 0.1:
            should_update = percent != self._last_percent
        else:
            should_update = False
        
        if not should_update:
            return
        
        self._last_update_time = current_time
        self._last_percent = percent
        self._last_state = state
        self._current_state = state
        
        icon, status_text, color = self.STATES.get(state, ('❓', 'Desconocido', 'gray'))
        
        self.icon_label.config(text=icon)
        self.progress_bar['value'] = percent
        self.status_label.config(text=status_text, foreground=color)
        
        if state == 'processing' and self._file_start_time is None:
            self._file_start_time = time.time()
        
        details_parts = []
        if state == 'processing':
            details_parts.append(f'{percent:.0f}%')
            if eta_seconds is not None:
                details_parts.append(f'ETA: {self._format_time(eta_seconds)}')
            if speed:
                details_parts.append(f'{speed}/s')
        elif state == 'completed':
            if self._file_start_time:
                elapsed = time.time() - self._file_start_time
                details_parts.append(f'{self._format_time(elapsed)}')
            details_parts.append('100%')
        elif state == 'error':
            details_parts.append('FALLO')
        
        self.details_label.config(text=' '.join(details_parts))
        
        if state == 'error':
            self.retry_btn.pack(fill=tk.X, pady=(5, 0))
        else:
            self.retry_btn.pack_forget()
    
    def _format_time(self, seconds):
        if seconds is None or seconds < 0:
            return '--'
        if seconds < 1:
            return f'{seconds*1000:.0f}ms'
        if seconds < 60:
            return f'{seconds:.1f}s'
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f'{minutes}m {secs}s'
    
    def reset(self):
        self.progress_bar['value'] = 0
        self.icon_label.config(text='⏳')
        self.status_label.config(text='Pendiente', foreground='gray')
        self.details_label.config(text='')
        self.retry_btn.pack_forget()
        self._last_update_time = 0
        self._last_percent = -1
        self._last_state = None
        self._file_start_time = None


class ProgressPanel(ttk.Frame):
    def __init__(self, parent, max_visible=10, on_retry=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.max_visible = max_visible
        self.on_retry = on_retry
        self.widget_pool = []
        self.active_items = {}
        self.queued_files = []
        self.eta_calculator = ETACalculator(window_size=10)
        
        self._build_ui()
    
    def _build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(header, text='📊 Progreso por Archivo', font=('Inter', 10, 'bold')).pack(side=tk.LEFT)
        
        self.count_label = ttk.Label(header, text='', font=('Inter', 9), foreground='#888')
        self.count_label.pack(side=tk.RIGHT)
        
        canvas = tk.Canvas(self, highlightthickness=0, bg='#2b2b2b')
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind(
            '<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        for _ in range(self.max_visible):
            item = FileProgressItem(
                self.scrollable_frame, '',
                on_retry=self.on_retry,
                style='ProgressItem.TFrame'
            )
            item.pack(fill=tk.X, pady=2)
            item.pack_forget()
            self.widget_pool.append(item)
    
    def set_files(self, filenames):
        self.active_items.clear()
        self.queued_files = list(filenames)
        self.eta_calculator.start()
        
        for widget in self.widget_pool:
            widget.pack_forget()
            widget.reset()
        
        visible_count = min(len(filenames), self.max_visible)
        
        for i in range(visible_count):
            fname = filenames[i]
            widget = self.widget_pool[i]
            widget.filename = fname
            widget.filename_label.config(text=widget._truncate_filename(fname))
            widget.pack(fill=tk.X, pady=2)
            self.active_items[fname] = widget
        
        if len(filenames) > self.max_visible:
            self.queued_files = filenames[self.max_visible:]
        else:
            self.queued_files = []
        
        self._update_count()
    
    def update_file(self, filename, percent, state, eta_seconds=None, speed=None):
        if filename in self.active_items:
            self.active_items[filename].update(percent, state, eta_seconds, speed)
            
            if state == 'completed':
                self.eta_calculator.add_sample(
                    getattr(self.active_items[filename], '_file_start_time', None) and 
                    (time.time() - self.active_items[filename]._file_start_time) or 0
                )
                self._promote_next()
        
        self._update_global_progress()
    
    def _promote_next(self):
        if not self.queued_files:
            return
        
        if len(self.active_items) >= self.max_visible:
            return
        
        next_file = self.queued_files.pop(0)
        
        for widget in self.widget_pool:
            if not widget.winfo_ismapped():
                widget.filename = next_file
                widget.filename_label.config(text=widget._truncate_filename(next_file))
                widget.reset()
                widget.pack(fill=tk.X, pady=2)
                self.active_items[next_file] = widget
                break
        
        self._update_count()
    
    def _update_count(self):
        active = len(self.active_items)
        queued = len(self.queued_files)
        self.count_label.config(text=f'{active}/{active + queued}')
    
    def _update_global_progress(self):
        pass


class BatchProgressManager:
    def __init__(self, progress_panel, global_progress_callback=None):
        self.panel = progress_panel
        self.global_progress_callback = global_progress_callback
        self.file_states = {}
        self.file_percentages = {}
        self.file_weights = {}
        self.total_weight = 0
        self.completed_count = 0
    
    def set_files(self, filenames, weights=None):
        if weights is None:
            weights = {f: 1 for f in filenames}
        
        self.file_weights = weights
        self.total_weight = sum(weights.values())
        self.file_states = {f: 'queued' for f in filenames}
        self.file_percentages = {f: 0 for f in filenames}
        self.completed_count = 0
        
        self.panel.set_files(filenames)
    
    def update_file(self, filename, percent, state, eta_seconds=None, speed=None):
        self.file_states[filename] = state
        self.file_percentages[filename] = percent
        
        if state == 'completed':
            self.completed_count += 1
        
        self.panel.update_file(filename, percent, state, eta_seconds, speed)
        
        if self.global_progress_callback:
            global_pct = self._calculate_global_progress()
            self.global_progress_callback(global_pct)
    
    def _calculate_global_progress(self):
        if not self.file_states:
            return 0
        
        if self.total_weight == 0:
            return (self.completed_count / len(self.file_states)) * 100
        
        completed_weight = 0
        in_progress_weight = 0
        
        for fname, state in self.file_states.items():
            weight = self.file_weights.get(fname, 1)
            
            if state == 'completed':
                completed_weight += weight * 100
            elif state == 'duplicate':
                completed_weight += weight * 100
            elif state in ('processing', 'retry'):
                in_progress_weight += weight * self.file_percentages.get(fname, 0)
            elif state == 'error':
                pass
        
        return (completed_weight + in_progress_weight) / self.total_weight
    
    def get_eta(self):
        remaining = len(self.file_states) - self.completed_count
        return self.panel.eta_calculator.estimate_remaining(remaining)
    
    def get_completed_count(self):
        return self.completed_count
    
    def get_total_count(self):
        return len(self.file_states)
    
    def get_failed_files(self):
        return [f for f, s in self.file_states.items() if s == 'error']
    
    def retry_failed(self):
        failed = self.get_failed_files()
        for fname in failed:
            self.file_states[fname] = 'queued'
            self.file_percentages[fname] = 0
            if fname in self.panel.active_items:
                self.panel.active_items[fname].reset()
        return failed
