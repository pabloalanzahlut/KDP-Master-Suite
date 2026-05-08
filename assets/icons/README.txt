═══════════════════════════════════════════════════════════════════════════════
                    KDP MASTER SUITE - CARPETA DE ICONOS
═══════════════════════════════════════════════════════════════════════════════

Este directorio contiene los iconos personalizados de la aplicación.
Los iconos se cargan automáticamente mediante el IconManager de ttkbootstrap.

───────────────────────────────────────────────────────────────────────────────
                           ESTRUCTURA DE CARPETAS
───────────────────────────────────────────────────────────────────────────────

assets/icons/
├── 32x32/      ← Iconos pequeños (botones de toolbar, notificaciones)
├── 64x64/      ← Iconos medianos (tabs, paneles)
├── 128x128/    ← Iconos grandes (headers, splash screens)
└── README.txt   ← Este archivo

───────────────────────────────────────────────────────────────────────────────
                         CÓMO AGREGAR ICONOS
───────────────────────────────────────────────────────────────────────────────

1. Coloca tus archivos PNG en la carpeta correspondiente:
   - 32x32/ para iconos pequeños
   - 64x64/ para iconos medianos
   - 128x128 para iconos grandes

2. Formato recomendado:
   - PNG con transparencia (fondos .png)
   - SVG convertido a PNG (recomendado para mejor calidad)
   - Nombres en minúsculas con guiones: download.png, settings.png

3. Uso en el código:

   # Importar el módulo de iconos
   from app.core.ui_framework import IconManager

   # En tu clase app, agregar:
   self.icon_manager = IconManager(self.root)

   # Cargar un icono:
   icon = self.icon_manager.load_icon("nombre_del_archivo", size=32)

   # Usar con widgets:
   ttk.Button(root, image=icon, text="Descargar")

───────────────────────────────────────────────────────────────────────────────
                         NOMBRES RECOMENDADOS
───────────────────────────────────────────────────────────────────────────────

Iconos sugeridos para la aplicación:
- download.png / download.svg
- upload.png / upload.svg
- settings.png / settings.svg
- search.png / search.svg
- folder.png / folder.svg
- file.png / file.svg
- delete.png / delete.svg
- edit.png / edit.svg
- play.png / play.svg
- pause.png / pause.svg
- stop.png / stop.svg
- refresh.png / refresh.svg
- export.png / export.svg
- import.png / import.svg
- info.png / info.svg
- warning.png / warning.svg
- error.png / error.svg
- success.png / success.svg
- user.png / user.svg
- lock.png / lock.svg

───────────────────────────────────────────────────────────────────────────────
                         NOTAS IMPORTANTES
───────────────────────────────────────────────────────────────────────────────

✓ Los iconos se cargan lazily (solo cuando se necesitan)
✓ Puedes usar ttkbootstrap.icons para iconos integrados
✓ PIL/Pillow debe estar instalado para manejar imágenes
✓ Los iconos se adaptan automáticamente al tema (oscuro/claro)

═══════════════════════════════════════════════════════════════════════════════