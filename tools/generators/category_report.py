import sqlite3
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def generate_report():
    """
    Analiza la base de datos SQLite y genera un reporte de frecuencia de categorías.
    """
    base_dir = Path(os.getcwd())
    if base_dir.name == "dist":
        base_dir = base_dir.parent

    db_path = base_dir / "knowledge" / "knowledge_base.db"
    output_path = base_dir / "outputs" / "reports"

    if not db_path.exists():
        return False, f"No se encontró la base de datos: {db_path}"

    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT category FROM knowledge_entries", conn)
        conn.close()

        if df.empty:
            return False, "La base de datos está vacía. No se puede generar el reporte."

        category_counts = df['category'].value_counts()

        # --- Generar Gráfico ---
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(10, 6))
        category_counts.plot(kind='barh', ax=ax, color='skyblue')
        ax.set_title('Frecuencia de Categorías en la Base de Conocimiento', fontsize=16)
        ax.set_xlabel('Número de Entradas')
        ax.invert_yaxis() # La categoría más frecuente arriba
        plt.tight_layout()
        
        chart_path = output_path / "category_frequency_chart.png"
        plt.savefig(chart_path)
        plt.close(fig)

        # --- Generar Reporte HTML ---
        html_report = f"""
        <h1>Reporte de Frecuencia de Categorías</h1>
        <p>Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <h2>Distribución de Contenido</h2>
        <img src='category_frequency_chart.png' alt='Gráfico de Frecuencia de Categorías' style='max-width:100%;'>
        <h2>Datos en Bruto</h2>
        {category_counts.to_frame().to_html()}
        """

        report_file_path = output_path / "category_report.html"
        report_file_path.write_text(html_report, encoding='utf-8')

        return True, f"Reporte guardado en: {report_file_path}"

    except Exception as e:
        return False, f"Error generando el reporte: {e}"

if __name__ == "__main__":
    success, msg = generate_report()
    print(msg)