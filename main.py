# -*- coding: utf-8 -*-
"""
KDP Master Suite - Entry Point
Redirige a gui_app.py (versión principal con todas las funcionalidades)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import gui_app
    import tkinter as tk
    root = tk.Tk()
    root.geometry("1400x900")
    app = gui_app.TranscriptionProcessorApp(root)
    root.mainloop()
