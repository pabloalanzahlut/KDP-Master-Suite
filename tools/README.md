# KDP Master Suite - CI/CD & Automation Tools

## Overview

This directory contains enterprise-grade automation tools for the KDP Master Suite project.

## Structure

```
tools/
├── ci_cd/              # Continuous Integration
│   ├── run_tests.py    # Test runner with coverage
│   ├── run_build.py    # Centralized build pipeline
│   └── smoke_test.py   # Post-build validation
├── backup/             # Backup & Recovery
│   ├── backup_manager.py  # Incremental backup with rotation
│   ├── integrity_check.py # State validation
│   └── restore.py         # Restore from backups
├── packaging/          # Enterprise Packaging
│   ├── silent_install.py  # Silent installer
│   ├── portable_check.py  # Portable mode detection
│   └── checksum.py        # SHA256 checksums
├── scripts/            # Utilities
│   ├── health_check.py    # HTTP health endpoint
│   ├── service_guard.py   # Monitor service safety monitors
│   └── version.py         # Semantic versioning
└── pipeline.py         # Master orchestrator
```

## Quick Start

### Full Pipeline (tests + build + backup)
```bash
python tools/pipeline.py --full
```

### Quick Build (no tests)
```bash
python tools/pipeline.py --quick
```

### Health Check
```bash
python tools/pipeline.py --health

# Or start HTTP server
python tools/scripts/health_check.py --server
```

### Backup
```bash
# Create backup
python tools/backup/backup_manager.py --backup

# List backups
python tools/backup/backup_manager.py --list

# Restore
python tools/backup/backup_manager.py --restore
```

### Version Management
```bash
# View current version
python tools/scripts/version.py --current

# Bump version
python tools/scripts/version.py --bump patch   # 2.5.6 -> 2.5.7
python tools/scripts/version.py --bump minor   # 2.5.6 -> 2.6.0
python tools/scripts/version.py --bump major   # 2.5.6 -> 3.0.0
```

### Checksums
```bash
# Generate checksums
python tools/packaging/checksum.py --generate

# Verify checksums
python tools/packaging/checksum.py --verify
```

## Service Resiliency

As of v2.6.1, the "Service Availability Guard" is active. 
- UI components now perform pre-flight checks before interacting with the Monitor Service.
- Automated recovery logging is triggered if a "SERVICE UNAVAILABLE" state is detected.

### Bug Fixes (v2.9.1)
- **Initialization**: Resolved `NameError: BackupManager` during application startup.
- **Resilience**: Improved import logic to handle internal service renaming (`BackupService` / `BackupManager`).
- **Monitor Safety**: Injected safety guards in `toggle_monitor_service` to prevent state lockups.

## Health Check Endpoints

When running the health check server:
- `http://localhost:8765/health` - Full status
- `http://localhost:8765/health/ready` - Readiness probe

## Configuration

- Max backups: 10 (configurable in `tools/backup/backup_config.json`)
- Version file: `VERSION.txt`
- Health check port: 8765 (configurable)

## Status

All tools tested and operational as of v2.5.7