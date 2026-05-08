#!/usr/bin/env python3
"""
KDP Master - Build Executable
Wrapper para crear ejecutables con PyInstaller
Soporta: --clean (full rebuild) | --incremental (fast build)
"""
import sys
import os
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build KDP Transcriptions')
    parser.add_argument('--clean', action='store_true', help='Full clean build')
    parser.add_argument('--incremental', action='store_true', help='Fast incremental build')
    parser.add_argument('--pyinstaller-args', type=str, default='', help='Additional arguments to pass directly to PyInstaller (e.g., "--debug all --hidden-import=tkinter")')
    args = parser.parse_args()
    
    # Default: incremental (fast), --clean for full rebuild
    clean_first = args.clean if args.clean else False
    
    from app.modules.monitoring.run_build import BuildPipeline
    
    # Pass additional PyInstaller arguments to the BuildPipeline
    pipeline = BuildPipeline(clean_first=clean_first, extra_pyinstaller_args=args.pyinstaller_args)
    sys.exit(pipeline.run())