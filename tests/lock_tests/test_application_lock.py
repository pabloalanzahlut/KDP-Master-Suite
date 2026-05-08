#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests unitarios para el sistema de lock de instancias múltiples.
"""

import os
import sys
import tempfile
import time
import signal
import subprocess
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.lock_manager import ApplicationLock, check_and_initialize_lock


def test_lock_acquire_release():
    """Test básico de adquisición y liberación de lock."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = os.path.join(tmpdir, "test.lock")
        
        lock = ApplicationLock(lock_name="test.lock", base_dir=tmpdir)
        
        # Debe poder adquirir el lock
        assert lock.acquire(), "Debe poder adquirir el lock inicialmente"
        assert lock._acquired, "El lock debería estar marcado como adquirido"
        
        # Debe poder liberar el lock
        lock.release()
        assert not lock._acquired, "El lock debería estar marcado como liberado"
        assert not os.path.exists(lock_path), "El archivo de lock debería haberse eliminado"


def test_lock_prevents_duplicate():
    """Test que evita adquisición duplicada del lock."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = os.path.join(tmpdir, "test.lock")
        
        lock1 = ApplicationLock(lock_name="test.lock", base_dir=tmpdir)
        lock2 = ApplicationLock(lock_name="test.lock", base_dir=tmpdir)
        
        # Primer lock debe adquirir exitosamente
        assert lock1.acquire(), "Primer lock debe adquirir exitosamente"
        
        # Segundo lock debe fallar
        assert not lock2.acquire(), "Segundo lock debe fallar (ya está tomado)"
        
        # Liberar primer lock
        lock1.release()
        
        # Ahora el segundo debería poder adquirir
        assert lock2.acquire(), "Segundo lock debe poder adquirir después de liberar el primero"


def test_orphaned_lock_detection():
    """Test de detección de locks huérfanos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = os.path.join(tmpdir, "test.lock")
        
        # Crear archivo de lock huérfano (con PID inexistente)
        with open(lock_path, 'w') as f:
            f.write("999999")  # PID muy alto que probablemente no exista
        
        lock = ApplicationLock(lock_name="test.lock", base_dir=tmpdir)
        
        # Debe detectar que es huérfano
        assert lock.is_orphaned_lock(), "Debe detectar lock huérfano"
        
        # Al intentar adquirir, debería fallar (porque dejamos que el usuario decida)
        # Pero internamente reconoce que es huérfano
        assert not lock.acquire(), "No debe adquirir lock huérfano sin intervención del usuario"


def test_lock_info():
    """Test de obtención de información de lock."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = os.path.join(tmpdir, "test.lock")
        
        lock = ApplicationLock(lock_name="test.lock", base_dir=tmpdir)
        
        # Info antes de adquirir
        info = lock.get_lock_info()
        assert info["lock_path"] == lock_path
        assert info["exists"] == False
        assert info["acquired"] == False
        
        # Adquirir lock
        assert lock.acquire()
        
        # Info después de adquirir
        info = lock.get_lock_info()
        assert info["exists"] == True
        assert info["acquired"] == True
        assert info["stored_pid"] == str(os.getpid())
        assert info["is_orphaned"] == False
        
        # Liberar
        lock.release()
        
        # Info después de liberar
        info = lock.get_lock_info()
        assert info["exists"] == False
        assert info["acquired"] == False


def test_force_cleanup():
    """Test de fuerza de limpieza de lock."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = os.path.join(tmpdir, "test.lock")
        
        lock = ApplicationLock(lock_name="test.lock", base_dir=tmpdir)
        
        # Adquirir lock
        assert lock.acquire()
        assert os.path.exists(lock_path)
        
        # Forzar limpieza
        result = lock.force_cleanup()
        assert result == True
        assert not os.path.exists(lock_path)
        assert not lock._acquired


def test_check_and_initialize_lock():
    """Test de la función helper de inicialización."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = os.path.join(tmpdir, "test.lock")
        
        # Primera llamada debe devolver lock y True para continuar
        lock_instance, should_continue = check_and_initialize_lock(
            lock_name="test.lock", 
            base_dir=tmpdir
        )
        
        assert lock_instance is not None
        assert should_continue == True
        assert lock_instance._acquired == True
        assert os.path.exists(lock_path)
        
        # Segunda llamada debe devolver lock y False (ya está tomado)
        lock_instance2, should_continue2 = check_and_initialize_lock(
            lock_name="test.lock", 
            base_dir=tmpdir
        )
        
        assert lock_instance2 is not None
        assert should_continue2 == False  # No debe continuar
        assert lock_instance2._acquired == False  # No debería haber adquirido
        
        # Limpiar
        lock_instance.release()


if __name__ == "__main__":
    print("Ejecutando tests de ApplicationLock...")
    
    try:
        test_lock_acquire_release()
        print("✅ test_lock_acquire_release passed")
    except Exception as e:
        print(f"❌ test_lock_acquire_release failed: {e}")
        sys.exit(1)
    
    try:
        test_lock_prevents_duplicate()
        print("✅ test_lock_prevents_duplicate passed")
    except Exception as e:
        print(f"❌ test_lock_prevents_duplicate failed: {e}")
        sys.exit(1)
    
    try:
        test_orphaned_lock_detection()
        print("✅ test_orphaned_lock_detection passed")
    except Exception as e:
        print(f"❌ test_orphaned_lock_detection failed: {e}")
        sys.exit(1)
    
    try:
        test_lock_info()
        print("✅ test_lock_info passed")
    except Exception as e:
        print(f"❌ test_lock_info failed: {e}")
        sys.exit(1)
    
    try:
        test_force_cleanup()
        print("✅ test_force_cleanup passed")
    except Exception as e:
        print(f"❌ test_force_cleanup failed: {e}")
        sys.exit(1)
    
    try:
        test_check_and_initialize_lock()
        print("✅ test_check_and_initialize_lock passed")
    except Exception as e:
        print(f"❌ test_check_and_initialize_lock failed: {e}")
        sys.exit(1)
    
    print("\n🎉 Todos los tests pasaron correctamente!")