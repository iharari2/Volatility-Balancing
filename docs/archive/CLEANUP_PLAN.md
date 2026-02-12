# Repository Cleanup Plan

**Date**: January 2025  
**Purpose**: Clean up unrelated files and organize repository structure

## Files to Clean Up

### Test Files in Root (Move to backend/tests/)

- `test_*.py` files (move to `backend/tests/root/` or delete if obsolete)
- `check_*.py` files
- `verify_*.py` files
- `run_*_tests.py` files

### Duplicate/Old Structure

- `src/` directory (appears to be old structure, duplicate of backend/)
- `build/` directory (should be in .gitignore)

### Temporary/Debug Files

- `*.html` test files in root
- `*.xlsx` test files in root
- `tatus` (typo file?)
- `volatility_balancing_prd_gui_lockup_v_1.md` (outdated?)

### Multiple Start Scripts (Consolidate)

- Multiple `start_*.bat` files (keep `start_dev_environment.bat`, remove others)
- Multiple `start_*.ps1` files

### Documentation Cleanup

- Consolidate duplicate documentation
- Move completion reports to docs/archive/
- Update cross-references

## Action Plan

1. Move test files to appropriate locations
2. Remove duplicate src/ directory
3. Consolidate start scripts
4. Update .gitignore
5. Archive old documentation
6. Sync all documentation

## Progress Status

### ✅ Completed

- **HTML test files deleted**: Removed 5 temporary HTML test files from root
- **Start scripts consolidated**: Removed 9 old .bat files and 1 .ps1 file (kept only `start_dev_environment.bat` and `start_dev_environment.ps1`)
- **.gitignore updated**: Added `build/` directory to .gitignore
- **Documentation archived**: Moved `volatility_balancing_prd_gui_lockup_v_1.md` to `docs/archive/`
- **Test files started**: Created `backend/tests/root/` directory and moved initial test files

### ⚠️ In Progress

- **Test files migration**: Many `test_*.py`, `check_*.py`, `verify_*.py`, and `run_*_tests.py` files still in root need to be moved to `backend/tests/root/`
  - Use the `execute_cleanup.py` script to complete this task
  - Or manually move remaining files

### ❌ Pending

- **Remove `src/` directory**: Large duplicate directory (contains old structure)
- **Remove `build/` directory**: Build artifacts (now in .gitignore, but directory still exists)
- **Complete test file migration**: ~20+ test files still need to be moved

### 📝 Notes

- The `src/` and `build/` directories are large and should be removed manually after verification
- Remaining test files can be moved using: `python execute_cleanup.py`
- Some test files may be obsolete and can be deleted instead of moved
