# Development Guide

Development guidelines and technical documentation for the Objekterkennung.yolo11 project.

> **For AI Assistants**: This file contains important context information for working on this project.

## 🐍 Python Environment

### Micromamba Setup
The project uses **Micromamba** as package manager:
```bash
# Initialize shell (first time setup)
micromamba shell init --shell zsh --root-prefix=~/micromamba

# Activate environment (if not automatically active)
micromamba activate yolo11

# Execute Python scripts
python3 script_name.py
```
Add needed packages to yolo11.condaenv.yml, then execute 1_create-conda-env.sh to update the Micromamba environment, followed by 2_setup_jupyter.sh, in case you do some work with Jupyter.


### Python Execution
- **Always use `python3`**, not `python`
- Execute scripts from project root: `/Users/andreas/Documents/Projekte/Objekterkennung.yolo11`
- For import issues: Add `sys.path.append()` for libs directory

## 🧪 Test System

### Test Structure
```
tests/
├── test_lookup_utils.py           # Unit Tests (Mock-based)
├── test_lookup_utils_integration.py # Integration Tests (real APIs)
└── test_clean_ocr_text.py         # Additional component tests
```

### Test Execution
```bash
# Unit Tests
python3 tests/test_lookup_utils.py

# Integration Tests  
python3 tests/test_lookup_utils_integration.py

# Individual test classes
python3 -m unittest tests.test_lookup_utils.TestLookupUtils
```

### Test Writing Guidelines
1. **Mock-based Unit Tests** for fast, offline validation
2. **Integration Tests** for real API calls (slower)
3. **Import fix** often needed:
   ```python
   import sys, os
   sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
   ```

### Test Updates
- For API changes: If feasible, update tests first, then code. There are many missing tests still, however.
- Base mock responses on real API responses
- Use integration tests for API compatibility


## 📝 Logging Conventions

```python
# Successful search
logger.info(f"🔎 Searching with {service} for: {query}")
logger.info(f"✅ Best match: {title} (from {count} results)")

# Failures
logger.info(f"⚠️ No book found for query: {query}")
logger.error(f"❌ {service} Error: {error}")

# Fallbacks
logger.info(f"🔄 Fallback: Searching with {fallback_service}...")
```

