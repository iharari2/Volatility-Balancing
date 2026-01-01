#!/usr/bin/env python3
"""Execute the cleanup plan - move files and organize repository"""

import shutil
from pathlib import Path


def main():
    root_dir = Path(".")
    target_test_dir = Path("backend/tests/root")
    target_test_dir.mkdir(parents=True, exist_ok=True)

    # Files to move from root to backend/tests/root/
    test_files = [
        "test_aapl_simulation.py",
        "test_market_data.py",
        "test_simulation_fix.py",
        "test_simulation_export_debug.py",
        "test_export_regression_simple.py",
        "test_ticker_parameter_fix.py",
        "test_dynamic_ticker_support.py",
        "test_real_market_data_exports.py",
        "test_all_exports.py",
        "test_comprehensive_export.py",
        "test_simulation_export_fix.py",
        "test_backend_endpoints.py",
        "test_backend_simple.py",
        "test_position_api.py",
        "test_excel_simple.py",
        "test_excel_export_fix.py",
        "test_excel_export_simple.py",
        "test_enhanced_excel_export.py",
        "test_simulation_debug.py",
        "test_positions_export.py",
        "test_excel_export_demo.py",
        "test_position_creation.py",
    ]

    check_verify_files = [
        "check_price_comparison.py",
        "verify_phase1.py",
        "verify_simulation_export.py",
        "run_export_tests.py",
    ]

    # HTML test files to delete
    html_files = [
        "test_exports.html",
        "test_simulation_simple.html",
        "integrate_excel_export.html",
        "excel_export_gui.html",
        "test_market_data.html",
    ]

    # Start scripts to keep
    keep_scripts = ["start_dev_environment.bat", "start_dev_environment.ps1"]

    # Start scripts to remove
    start_bat_files = [
        "start_app_fixed.bat",
        "start_app.bat",
        "start_backend_fixed.bat",
        "start_backend_python.bat",
        "start_backend_simple.bat",
        "start_backend.bat",
        "start_frontend.bat",
        "start_servers.bat",
    ]

    start_ps1_files = ["start_app.ps1"]

    moved = []
    not_found = []
    deleted = []

    print("=" * 60)
    print("CLEANUP PLAN EXECUTION")
    print("=" * 60)

    # Move test files
    print("\n1. Moving test files to backend/tests/root/...")
    for file in test_files + check_verify_files:
        src = root_dir / file
        if src.exists():
            dst = target_test_dir / file
            shutil.move(str(src), str(dst))
            moved.append(file)
            print(f"   ✓ Moved: {file}")
        else:
            not_found.append(file)
            print(f"   ✗ Not found: {file}")

    # Delete HTML test files
    print("\n2. Deleting HTML test files...")
    for file in html_files:
        src = root_dir / file
        if src.exists():
            src.unlink()
            deleted.append(file)
            print(f"   ✓ Deleted: {file}")
        else:
            print(f"   ✗ Not found: {file}")

    # Delete old start scripts
    print("\n3. Removing old start scripts...")
    for file in start_bat_files + start_ps1_files:
        src = root_dir / file
        if src.exists():
            src.unlink()
            deleted.append(file)
            print(f"   ✓ Deleted: {file}")
        else:
            print(f"   ✗ Not found: {file}")

    # Update .gitignore
    print("\n4. Updating .gitignore...")
    gitignore_path = root_dir / ".gitignore"
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if "build/" not in content:
            content += "\nbuild/\n"
            gitignore_path.write_text(content)
            print("   ✓ Added build/ to .gitignore")
        else:
            print("   ✓ build/ already in .gitignore")
    else:
        gitignore_path.write_text("build/\n")
        print("   ✓ Created .gitignore with build/")

    # Archive documentation
    print("\n5. Archiving outdated documentation...")
    docs_archive = Path("docs/archive")
    docs_archive.mkdir(parents=True, exist_ok=True)

    outdated_doc = root_dir / "volatility_balancing_prd_gui_lockup_v_1.md"
    if outdated_doc.exists():
        dst = docs_archive / outdated_doc.name
        shutil.move(str(outdated_doc), str(dst))
        moved.append(outdated_doc.name)
        print(f"   ✓ Archived: {outdated_doc.name}")
    else:
        print(f"   ✗ Not found: {outdated_doc.name}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files moved: {len(moved)}")
    print(f"Files deleted: {len(deleted)}")
    print(f"Files not found: {len(not_found)}")

    if not_found:
        print("\nFiles not found (may have been moved already):")
        for f in not_found:
            print(f"  - {f}")

    print("\n✅ Cleanup phase 1 complete!")
    print("\n⚠️  NOTE: src/ and build/ directories need manual removal")
    print("   (These are large directories that require confirmation)")


if __name__ == "__main__":
    main()
