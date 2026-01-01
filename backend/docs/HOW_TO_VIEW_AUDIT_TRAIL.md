# How to View Audit Trail

## Quick Start

### Prerequisites

Install Streamlit (if not already installed):

```bash
# Activate your virtual environment first
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows

# Install Streamlit
pip install streamlit==1.39.0

# Or install all requirements
pip install -r backend/requirements.txt
```

### Option 1: Streamlit GUI (Recommended)

Launch the interactive audit viewer:

**From WSL (Linux):**

```bash
# From project root - accessible from Windows
streamlit run ui/audit_viewer.py --server.address 0.0.0.0 --server.port 8501

# Or use the helper script
bash ui/run_audit_viewer.sh
```

**From Windows:**

```cmd
ui\run_audit_viewer.bat
```

**Access from Windows Browser:**

- Open `http://localhost:8501` in your Windows browser
- WSL2 automatically forwards ports to Windows localhost

The GUI will open in your browser (usually at `http://localhost:8501`).

**Features:**

- Filter by tenant, portfolio, asset, trace_id, or date range
- View events in three modes:
  - **Timeline**: Chronological list of all events
  - **By Trace**: Events grouped by trace_id
  - **Tree**: Parent-child relationships visualized
- Export to CSV or JSON
- Collapsible JSON payloads for detailed inspection

### Option 2: CLI Tool

Print a specific trace to the console:

```bash
# From project root
python tools/print_audit_trail.py --trace-id <your-trace-id>
```

**Options:**

- `--trace-id`: Required - The trace ID to view
- `--log-file`: Optional - Path to log file (default: `backend/logs/audit_trail.jsonl`)
- `--json`: Optional - Output as JSON instead of formatted text

**Example:**

```bash
python tools/print_audit_trail.py --trace-id abc-123-def-456
```

Output format:

```
[09:00:00] PriceEvent price=96.9 anchor=100
[09:00:00] TriggerEvaluated BUY trigger fired: BELOW_THRESHOLD
[09:00:00] GuardrailEvaluated Guardrail allowed BUY 20: within limits
[09:00:01] OrderCreated Order abc123 BUY 20 @ 96.9 commission_est 1.94
```

### Option 3: Direct File Access

The audit log is a JSONL (JSON Lines) file:

```bash
# View raw log file
cat backend/logs/audit_trail.jsonl

# Or with line numbers
cat -n backend/logs/audit_trail.jsonl

# Filter for specific trace_id
grep "trace_id.*abc-123" backend/logs/audit_trail.jsonl
```

Each line is a JSON object representing one event.

## Finding Trace IDs

### From the Log File

```bash
# Extract all unique trace IDs
grep -o '"trace_id":"[^"]*"' backend/logs/audit_trail.jsonl | sort -u
```

### From the Streamlit GUI

1. Open the GUI
2. Look at the "By Trace" view mode
3. All trace IDs are listed in the expandable sections

### From Application Logs

When orchestrators run, they generate trace_ids. Check application logs or use the GUI to see recent traces.

## Understanding Event Types

- 🔵 **PriceEvent**: Market price data received
- 🟡 **TriggerEvaluated**: Price trigger evaluation result
- 🟠 **GuardrailEvaluated**: Guardrail check result
- 🟢 **OrderCreated**: Order submitted to broker
- ✅ **ExecutionRecorded**: Trade execution recorded
- 📊 **PositionUpdated**: Position state changed
- 💰 **DividendPaid**: Dividend payment processed

## Filtering in Streamlit GUI

1. **By Tenant**: Select from dropdown (if multi-tenant)
2. **By Portfolio**: Select from dropdown
3. **By Asset**: Select ticker symbol (e.g., AAPL, MSFT)
4. **By Trace ID**: Enter specific trace ID
5. **By Date Range**: Enable date filter and select start/end dates

## Troubleshooting

### "No events found"

The audit log file is created automatically when the first event is logged. If you see "No events found", it means:

1. **No events have been generated yet** - Events are only created when:

   - The backend runs trading cycles (via orchestrators)
   - You trigger position evaluations via API
   - You run simulations

2. **To generate test events** (for testing the viewer):

   ```bash
   # From project root
   python tools/generate_test_audit_event.py
   ```

3. **To generate real events**:

   ```bash
   # Start the backend
   cd backend
   python -m uvicorn app.main:app --reload

   # Then trigger a trading cycle via API:
   # POST to /api/positions/{position_id}/evaluate
   # Or run a simulation
   ```

4. **Check log file location**:
   ```bash
   ls -la backend/logs/audit_trail.jsonl
   ```
   The file is created at `backend/logs/audit_trail.jsonl` (relative to project root) when the first event is logged.

### "Log file not found"

- The log file is created automatically when first event is logged
- Make sure the backend has write permissions to `backend/logs/`
- Check that orchestrators are running and generating events

### Empty log file

- Events are only logged when orchestrators run trading cycles
- Try triggering a position evaluation or simulation
- Check that the unified logger is properly configured in DI container

## Example Workflow

1. **Start Backend**: `python -m uvicorn app.main:app --reload`
2. **Trigger Trading Cycle**: Make API calls that trigger orchestrators
3. **View Events**:
   ```bash
   streamlit run ui/audit_viewer.py
   ```
4. **Filter by Asset**: Select "AAPL" in the Asset dropdown
5. **View Trace**: Click on a trace in "By Trace" mode to see full chain

## Advanced Usage

### Export Specific Trace

In Streamlit GUI:

1. Switch to "By Trace" view mode
2. Find the trace you want
3. Click "Download Trace {trace_id}" button

### Command Line JSON Output

```bash
python tools/print_audit_trail.py --trace-id abc-123 --json > trace.json
```

### Parse with jq

```bash
# Pretty print all events
cat backend/logs/audit_trail.jsonl | jq '.'

# Filter by event type
cat backend/logs/audit_trail.jsonl | jq 'select(.event_type == "OrderCreated")'

# Get all trace IDs
cat backend/logs/audit_trail.jsonl | jq -r '.trace_id' | sort -u
```
















