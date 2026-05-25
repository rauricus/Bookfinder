# Development guide

Development guidelines and technical documentation for the Bookfinder project.

> **For AI assistants**: This file contains important context information for working on this project.

## Python environment

### Micromamba setup
The project uses **Micromamba** as package manager:
```bash
# Initialize shell dynamically (required before first activation in session)
eval "$(micromamba shell hook --shell zsh)"

# Initialize shell permanently (first time setup only)
micromamba shell init --shell zsh --root-prefix=~/micromamba

# Activate environment (if not automatically active)
micromamba activate bookfinder

# Execute Python scripts
python3 script_name.py
```

The shell must be initialized for Micromamba before environment activation works. Use the dynamic initialization `eval "$(micromamba shell hook --shell zsh)"` in each new terminal session, or run the permanent setup once with `micromamba shell init`.

Add needed packages to bookfinder.condaenv.yml, then execute 1_create-conda-env.sh to update the Micromamba environment, followed by 2_setup_jupyter.sh, in case you do some work with Jupyter.

### Python execution
- In the "bookfinder" environment, use `python3`, not `python`
- Execute scripts from project root


## Test system

There are only very few and very basic tests currently.

### Test structure
```
tests/
├── test_lookup_utils.py           # Unit Tests (Mock-based)
├── test_lookup_utils_integration.py # Integration Tests (real APIs)
└── test_clean_ocr_text.py         # Additional component tests
```

### Test execution
```bash
# Initialize shell for Micromamba (if not done permanently)
eval "$(micromamba shell hook --shell zsh)"
micromamba activate bookfinder

# Unit Tests
python3 tests/test_lookup_utils.py

# Integration Tests  
python3 tests/test_lookup_utils_integration.py

# Individual test classes
python3 -m unittest tests.test_lookup_utils.TestLookupUtils
```

### Test writing guidelines
1. **Mock-based Unit Tests** for fast, offline validation
2. **Integration Tests** for real API calls (slower)
3. **Import fix** often needed:
   ```python
   import sys, os
   sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
   ```

### Test updates
- For API changes: If feasible, update tests first, then code. There are many missing tests still, however.
- Base mock responses on real API responses
- Use integration tests for API compatibility


## Logging conventions

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

