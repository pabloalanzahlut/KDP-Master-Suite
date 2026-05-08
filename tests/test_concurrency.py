import unittest
import os
import shutil
import tempfile
from pathlib import Path
import sys

# Añadir el path base para poder importar los servicios
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.processing_service import ProcessingService

class TestProcessingConcurrency(unittest.TestCase):
    """
    Suite de pruebas para validar la seguridad de hilos (thread-safety)
    en la deduplicación por hash MD5 del motor de procesamiento.
    """
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.input_dir)
        os.makedirs(self.output_dir)
        self.service = ProcessingService()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_duplicate_hash_concurrency(self):
        """
        Verifica que ante múltiples archivos idénticos procesados en paralelo,
        el sistema solo registre uno y marque el resto como duplicados.
        """
        # Crear 50 archivos con contenido idéntico
        content = "Contenido de prueba para validación de concurrencia v2.5.10."
        filenames = [f"archivo_duplicado_{i}.txt" for i in range(50)]
        
        for name in filenames:
            with open(os.path.join(self.input_dir, name), "w", encoding="utf-8") as f:
                f.write(content)

        # Ejecutar procesamiento con alta concurrencia (20 hilos simultáneos)
        processed_count = self.service.process_files(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            files_to_process=filenames,
            max_workers=20
        )

        # Validaciones de integridad atómica
        self.assertEqual(processed_count, 1, "Solo un archivo único debería haber sido procesado")
        self.assertEqual(len(os.listdir(self.output_dir)), 1, "La carpeta de salida debe contener solo un archivo")
        self.assertEqual(len(self.service._processed_hashes), 1, "El set interno de hashes debe tener una única entrada")

if __name__ == "__main__":
    unittest.main()