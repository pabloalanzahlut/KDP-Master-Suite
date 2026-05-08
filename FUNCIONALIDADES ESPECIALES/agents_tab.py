# --- INICIO FUNCIONALIDAD US-030: UI DE AGENTES ---
import tkinter as tk
from tkinter import ttk, scrolledtext

class AgentsTab(ttk.Frame):
    """
    Interfaz de usuario para la ejecución de prompts de agentes.
    """
    def __init__(self, parent, agent_manager):
        super().__init__(parent)
        self.agent_manager = agent_manager
        self._setup_ui()

    def _setup_ui(self):
        # --- INICIO FUNCIONALIDAD US-032: GESTOR DE PLANTILLAS ---
        template_frame = ttk.Frame(self)
        template_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(template_frame, text="Plantilla:").pack(side='left')
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, state='readonly')
        self.template_combo['values'] = ["Análisis de Nicho", "Optimización SEO", "Legal Compliance", "Estructura de Libro"]
        self.template_combo.pack(side='left', padx=5, fill='x', expand=True)
        self.template_combo.bind("<<ComboboxSelected>>", self._on_template_select)
        # --- FIN FUNCIONALIDAD US-032 ---

        # Área de Entrada
        ttk.Label(self, text="Prompt del Agente:", font=('Segoe UI', 10, 'bold')).pack(pady=5, padx=10, anchor='w')
        self.prompt_input = scrolledtext.ScrolledText(self, height=5)
        self.prompt_input.pack(fill='x', padx=10, pady=5)

        # Botón de Ejecución
        self.btn_run = ttk.Button(self, text="🚀 Ejecutar Agente", command=self._on_execute)
        self.btn_run.pack(pady=10)

        # Área de Respuesta
        ttk.Label(self, text="Respuesta de la IA:", font=('Segoe UI', 10, 'bold')).pack(padx=10, anchor='w')
        self.response_output = scrolledtext.ScrolledText(self, height=15, state='disabled', background='#f0f0f0')
        self.response_output.pack(fill='both', expand=True, padx=10, pady=5)

    # --- INICIO FUNCIONALIDAD US-032: LÓGICA DE PLANTILLAS ---
    def _on_template_select(self, event):
        templates = {
            "Análisis de Nicho": "Analiza el potencial de ventas para el nicho: {INPUT}\nConsidera competencia y estacionalidad.",
            "Optimización SEO": "Genera 7 tags optimizados y un subtítulo persuasivo para: {INPUT}",
            "Legal Compliance": "Verifica si el siguiente contenido infringe marcas registradas de Amazon: {INPUT}",
            "Estructura de Libro": "Propón una tabla de contenidos de 10 capítulos para un libro sobre: {INPUT}"
        }
        selected = self.template_var.get()
        if selected in templates:
            self.prompt_input.delete("1.0", tk.END)
            self.prompt_input.insert("1.0", templates[selected])
    # --- FIN FUNCIONALIDAD US-032 ---

    def _on_execute(self):
        prompt = self.prompt_input.get("1.0", tk.END).strip()
        if not prompt: return

        self.btn_run.config(state='disabled')
        # Aquí se llamaría al manager (idealmente en un thread para no congelar la UI)
        result = self.agent_manager.execute_agent_prompt("General Agent", prompt)
        
        self.response_output.config(state='normal')
        self.response_output.delete("1.0", tk.END)
        if result["status"] == "success":
            self.response_output.insert(tk.END, result["response"])
        else:
            self.response_output.insert(tk.END, f"Error: {result['message']}")
        self.response_output.config(state='disabled')
        self.btn_run.config(state='normal')
# --- FIN FUNCIONALIDAD US-030 ---