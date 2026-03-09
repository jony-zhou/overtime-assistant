<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TECO SSP Overtime Calculator (加班時數計算器) — a Windows desktop GUI app (CustomTkinter) that automates login to the TECO SSP system, calculates overtime hours from attendance records, and submits overtime reports. Written in Python, packaged as a single `.exe` via PyInstaller.

## Common Commands

```bash
# Run the application
python app.py

# Run all tests
python -m pytest

# Run a single test file
python -m pytest tests/test_calculator.py

# Run a specific test
python -m pytest tests/test_calculator.py::test_function_name

# Run tests with coverage
python -m pytest --cov=src --cov-report=html

# Lint
pylint src/

# Build executable (version auto-injected from src/core/version.py)
python -m PyInstaller overtime_calculator.spec --clean --noconfirm
```

If using a venv, prefix with `.\.venv\Scripts\python.exe -m`.

## Architecture

**Layered MVC pattern** with four layers:

```
UI Layer (ui/)                    CustomTkinter GUI
    └─ MainWindow                 3-tab interface (Attendance / Overtime Report / Personal Records)
       ├─ LoginFrame              Login with credential storage
       ├─ AttendanceTab           Attendance anomaly list
       ├─ OvertimeReportTab       Form filling & submission
       ├─ PersonalRecordTab       Historical records
       └─ StatisticsCard          Dashboard cards (shared across tabs)

Service Layer (src/services/)     Business logic
    ├─ AuthService                SSP login, ASP.NET ViewState handling
    ├─ DataSyncService ★          Unified data sync with 5-min cache (replaces legacy services)
    ├─ OvertimeReportService      ASP.NET form auto-fill & submission
    ├─ ExportService              Excel report generation
    ├─ CredentialManager          Windows Credential Manager + Fernet encryption
    ├─ TemplateManager            Overtime description templates (JSON persistence)
    └─ UpdateService              GitHub release version checking

Core Layer (src/core/)
    ├─ OvertimeCalculator         Overtime = total - 70min lunch - 480min work - 30min rest
    └─ Version                    Semantic versioning (SSOT for all version references)

Data Layer (src/models/)          Dataclass models
    ├─ AttendanceRecord, PunchRecord, LeaveRecord
    ├─ UnifiedOvertimeRecord      Merged punch + submission status (v1.3.0)
    ├─ AttendanceSnapshot         Complete data package with TTL cache
    ├─ OvertimeStatistics         Aggregated metrics
    └─ OvertimeSubmissionRecord, PersonalRecord
```

### Key Data Flow

```
SSP HTTP → DataSyncService (parallel fetch, 3 concurrent) →
  AttendanceParser / PersonalRecordParser (HTML→models) →
  OvertimeCalculator →
  AttendanceSnapshot (cached 5 min) →
  UI tabs read from snapshot
```

### Important Patterns

- **Single Source of Truth (SSOT)**: Version in `src/core/version.py`, config in `src/config/settings.py`
- **DataSyncService** is the recommended data layer (legacy `DataService`, `OvertimeStatusService`, `PersonalRecordService` are deprecated, removal planned for v2.0.0)
- **Background threads** for login and data fetching — UI updates happen on the main thread
- **Stale-on-Error caching**: network failures return cached data instead of crashing
- **ASP.NET compatibility**: services handle ViewState, EventValidation, and PostBack mechanisms

## Configuration

All tunable constants are in `src/config/settings.py` (Settings dataclass). Key values:

- `LUNCH_BREAK=70`, `WORK_HOURS=480`, `REST_TIME=30` (minutes)
- `CACHE_DURATION_SECONDS=300` (5-minute sync cache TTL)
- `VERIFY_SSL=False` (internal certificate)
- `MAX_PAGES=10` (attendance pagination limit)

## Design System

UI tokens (colors, typography, spacing) are centralized in `ui/config/design_system.py`. All UI components reference these tokens instead of hardcoded values.

## OpenSpec Change Management

This project uses OpenSpec for spec-driven development. For new features, breaking changes, or architecture shifts, create a change proposal under `openspec/changes/` before implementing. See `openspec/AGENTS.md` for the full workflow.

## Language

Code comments and documentation are in Traditional Chinese (繁體中文). Commit messages follow the same convention.
