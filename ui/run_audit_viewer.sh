#!/bin/bash
# Run Streamlit audit viewer accessible from Windows
# Usage: ./ui/run_audit_viewer.sh

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🔍 Starting Audit Trail Viewer..."
echo "   Accessible at: http://localhost:8501"
echo "   (Also accessible from Windows via localhost:8501)"
echo ""

# Run Streamlit with host 0.0.0.0 to allow access from Windows
streamlit run ui/audit_viewer.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true
















