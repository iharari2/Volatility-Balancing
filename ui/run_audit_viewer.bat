@echo off
REM Run Streamlit audit viewer accessible from Windows
REM Usage: ui\run_audit_viewer.bat

echo 🔍 Starting Audit Trail Viewer...
echo    Accessible at: http://localhost:8501
echo    (Also accessible from Windows via localhost:8501)
echo.

REM Run Streamlit with host 0.0.0.0 to allow access from Windows
streamlit run ui/audit_viewer.py --server.port 8501 --server.address 0.0.0.0 --server.headless true

pause

















