#!/usr/bin/env python3
"""
Streamlit-based Audit Trail Viewer for Volatility Balancing.

Usage:
    streamlit run ui/audit_viewer.py
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import pandas as pd
import requests


# Configuration
DEFAULT_LOG_FILE = Path("backend/logs/audit_trail.jsonl")  # Relative to project root
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def load_events(log_file: Path) -> List[Dict[str, Any]]:
    """Load events from JSONL file."""
    events = []
    if not log_file.exists():
        return events

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                continue

    return events


def _normalize_datetime(dt_str: str) -> datetime:
    """Parse datetime string and normalize to timezone-aware (UTC)."""
    from datetime import timezone

    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    # If timezone-naive, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Convert to UTC if timezone-aware
    elif dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt


def filter_events(
    events: List[Dict[str, Any]],
    tenant_id: Optional[str] = None,
    portfolio_id: Optional[str] = None,
    asset_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Filter events based on criteria."""
    filtered = events

    if tenant_id:
        filtered = [e for e in filtered if e.get("tenant_id") == tenant_id]
    if portfolio_id:
        filtered = [e for e in filtered if e.get("portfolio_id") == portfolio_id]
    if asset_id:
        filtered = [e for e in filtered if e.get("asset_id") == asset_id]
    if trace_id:
        filtered = [e for e in filtered if e.get("trace_id") == trace_id]
    if start_date:
        # Normalize datetimes to timezone-aware (UTC) for comparison
        start_dt = start_date
        if start_dt.tzinfo is None:
            # Make naive datetime timezone-aware (assume UTC)
            from datetime import timezone

            start_dt = start_dt.replace(tzinfo=timezone.utc)
        filtered = [e for e in filtered if _normalize_datetime(e["created_at"]) >= start_dt]
    if end_date:
        # Normalize datetimes to timezone-aware (UTC) for comparison
        end_dt = end_date
        if end_dt.tzinfo is None:
            # Make naive datetime timezone-aware (assume UTC)
            from datetime import timezone

            end_dt = end_dt.replace(tzinfo=timezone.utc)
        filtered = [e for e in filtered if _normalize_datetime(e["created_at"]) <= end_dt]

    return filtered


def group_by_trace(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group events by trace_id."""
    grouped = defaultdict(list)
    for event in events:
        trace_id = event.get("trace_id", "unknown")
        grouped[trace_id].append(event)

    # Sort events within each trace by created_at
    for trace_id in grouped:
        grouped[trace_id].sort(key=lambda e: e["created_at"])

    return dict(grouped)


def build_event_tree(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a tree structure from events based on parent_event_id."""
    event_map = {e["event_id"]: e for e in events}
    roots = []

    for event in events:
        parent_id = event.get("parent_event_id")
        if not parent_id or parent_id not in event_map:
            roots.append(event)
        else:
            parent = event_map[parent_id]
            if "children" not in parent:
                parent["children"] = []
            parent["children"].append(event)

    return {"roots": roots, "map": event_map}


def format_event_time(event: Dict[str, Any]) -> str:
    """Format event timestamp for display."""
    try:
        dt = datetime.fromisoformat(event["created_at"])
        return dt.strftime(DATE_FORMAT)
    except (ValueError, KeyError, TypeError):
        return event["created_at"]


def highlight_event_type(event_type: str) -> str:
    """Return color for event type."""
    colors = {
        "PriceEvent": "🔵",
        "TriggerEvaluated": "🟡",
        "GuardrailEvaluated": "🟠",
        "OrderCreated": "🟢",
        "ExecutionRecorded": "✅",
        "PositionUpdated": "📊",
        "DividendPaid": "💰",
    }
    return colors.get(event_type, "⚪")


# Streamlit UI
st.set_page_config(page_title="Audit Trail Viewer", layout="wide")

st.title("🔍 Volatility Balancing - Audit Trail Viewer")

# Sidebar filters
st.sidebar.header("Filters")

log_file_path = st.sidebar.text_input(
    "Log File Path",
    value=str(DEFAULT_LOG_FILE),
    help="Path to the JSONL audit log file",
)

# Load events
log_file = Path(log_file_path)
events = load_events(log_file)

if not events:
    st.warning(f"No events found in {log_file_path}.")

    # Provide helpful guidance
    st.info(
        """
    **To generate audit events:**
    
    1. **Start the backend** and trigger trading cycles:
       ```bash
       cd backend
       python -m uvicorn app.main:app --reload
       ```
    
    2. **Generate test events** (for testing):
       ```bash
       python tools/generate_test_audit_event.py
       ```
    
    3. **Trigger a trading cycle** via API:
       - POST to `/api/positions/{position_id}/evaluate`
       - Or run a simulation
    
    The log file will be created automatically when the first event is logged.
    """
    )

    # Check if file exists
    if log_file.exists():
        st.info(f"✅ Log file exists at: `{log_file.absolute()}` but is empty.")
    else:
        st.info(f"ℹ️ Log file does not exist yet: `{log_file.absolute()}`")
        st.info("It will be created automatically when the first event is logged.")

    st.stop()

# Extract unique values for filters
tenants = sorted(set(e.get("tenant_id") for e in events if e.get("tenant_id")))
portfolios = sorted(set(e.get("portfolio_id") for e in events if e.get("portfolio_id")))
assets = sorted(set(e.get("asset_id") for e in events if e.get("asset_id")))

# Filter inputs
selected_tenant = st.sidebar.selectbox("Tenant", [None] + tenants)
selected_portfolio = st.sidebar.selectbox("Portfolio", [None] + portfolios)
selected_asset = st.sidebar.selectbox("Asset", [None] + assets)
selected_trace_id = st.sidebar.text_input("Trace ID (optional)")

# Date range
st.sidebar.subheader("Date Range")
use_date_filter = st.sidebar.checkbox("Filter by date range")
if use_date_filter:
    start_date = st.sidebar.date_input(
        "Start Date", value=datetime.now().date() - timedelta(days=7)
    )
    end_date = st.sidebar.date_input("End Date", value=datetime.now().date())
    # Make datetimes timezone-aware (UTC) to match event timestamps
    from datetime import timezone

    start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
else:
    start_datetime = None
    end_datetime = None

# Apply filters
filtered_events = filter_events(
    events,
    tenant_id=selected_tenant,
    portfolio_id=selected_portfolio,
    asset_id=selected_asset,
    trace_id=selected_trace_id if selected_trace_id else None,
    start_date=start_datetime,
    end_date=end_datetime,
)

st.sidebar.metric("Total Events", len(filtered_events))

# Main content
if not filtered_events:
    st.info("No events match the selected filters.")
    st.stop()

# View mode selection
view_mode = st.radio("View Mode", ["Timeline", "By Trace", "Tree"], horizontal=True)

if view_mode == "Timeline":
    st.subheader("Event Timeline")

    # Sort by time
    filtered_events.sort(key=lambda e: e["created_at"])

    for event in filtered_events:
        with st.expander(
            f"{highlight_event_type(event['event_type'])} {event['event_type']} - {format_event_time(event)}",
            expanded=False,
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Event ID:**", event["event_id"])
                st.write("**Trace ID:**", event.get("trace_id", "N/A"))
                st.write("**Parent Event ID:**", event.get("parent_event_id", "N/A"))
                st.write("**Source:**", event.get("source", "N/A"))
            with col2:
                st.write("**Tenant:**", event.get("tenant_id", "N/A"))
                st.write("**Portfolio:**", event.get("portfolio_id", "N/A"))
                st.write("**Asset:**", event.get("asset_id", "N/A"))

            st.json(event["payload"])

elif view_mode == "By Trace":
    st.subheader("Events Grouped by Trace")

    grouped = group_by_trace(filtered_events)

    for trace_id, trace_events in sorted(
        grouped.items(), key=lambda x: x[1][0]["created_at"], reverse=True
    ):
        with st.expander(f"Trace: {trace_id} ({len(trace_events)} events)", expanded=False):
            for event in trace_events:
                st.write(
                    f"**{highlight_event_type(event['event_type'])} {event['event_type']}** - {format_event_time(event)}"
                )
                with st.expander("Details", expanded=False):
                    st.json(event)

            # Export trace button
            trace_json = json.dumps(trace_events, indent=2)
            st.download_button(
                f"Download Trace {trace_id}",
                trace_json,
                file_name=f"trace_{trace_id}.json",
                mime="application/json",
            )

elif view_mode == "Tree":
    st.subheader("Event Tree (Parent-Child Relationships)")

    tree = build_event_tree(filtered_events)

    def render_event_node(event: Dict[str, Any], level: int = 0):
        """Recursively render event tree."""
        indent = "  " * level
        children = event.get("children", [])

        with st.expander(
            f"{indent}{highlight_event_type(event['event_type'])} {event['event_type']} - {format_event_time(event)}",
            expanded=level == 0,
        ):
            st.json(event)
            for child in sorted(children, key=lambda e: e["created_at"]):
                render_event_node(child, level + 1)

    for root in sorted(tree["roots"], key=lambda e: e["created_at"], reverse=True):
        render_event_node(root)

# Simulation section
st.sidebar.divider()
st.sidebar.subheader("🔬 Run Simulation")

position_id_for_sim = st.sidebar.text_input(
    "Position ID",
    value="",
    help="Enter the position ID to run a simulation for",
    key="sim_position_id",
)

if position_id_for_sim:
    # Simulation configuration
    col1, col2 = st.sidebar.columns(2)
    with col1:
        sim_start_date = st.date_input(
            "Start Date", value=datetime.now().date() - timedelta(days=30), key="sim_start_date"
        )
    with col2:
        sim_end_date = st.date_input("End Date", value=datetime.now().date(), key="sim_end_date")

    # Validate date range
    if sim_start_date >= sim_end_date:
        st.sidebar.error("⚠️ Start date must be before end date")
        st.stop()

    # Calculate time window
    time_window_days = (sim_end_date - sim_start_date).days
    time_window_hours = time_window_days * 24

    # Interval options with descriptions
    interval_options = {
        1: "1 minute (very granular - max 7 days)",
        5: "5 minutes (granular - recommended for < 30 days)",
        15: "15 minutes (balanced - recommended for < 90 days)",
        30: "30 minutes (default - recommended for < 180 days)",
        60: "60 minutes (hourly - recommended for < 365 days)",
    }

    # Calculate estimated data points
    def calculate_data_points(days: int, interval_minutes: int, include_after_hours: bool) -> int:
        """Calculate estimated number of data points."""
        # Market hours: 9:30 AM - 4:00 PM = 6.5 hours per day
        market_hours_per_day = 6.5
        if include_after_hours:
            # Extended hours: 4:00 AM - 8:00 PM = 16 hours per day
            trading_hours_per_day = 16
        else:
            trading_hours_per_day = market_hours_per_day

        bars_per_day = (trading_hours_per_day * 60) / interval_minutes
        return int(days * bars_per_day)

    # Show current selection info
    st.sidebar.info(f"📅 Time Window: **{time_window_days} days** ({time_window_hours} hours)")

    sim_include_after_hours = st.sidebar.checkbox(
        "Include After Hours", value=False, key="sim_after_hours"
    )

    # Interval selection with validation
    sim_interval = st.sidebar.selectbox(
        "Intraday Interval",
        options=list(interval_options.keys()),
        format_func=lambda x: f"{x} min - {interval_options[x]}",
        index=3,  # Default to 30 minutes
        key="sim_interval",
    )

    # Calculate and validate data points
    estimated_points = calculate_data_points(
        time_window_days, sim_interval, sim_include_after_hours
    )

    # Validation thresholds
    MAX_RECOMMENDED_POINTS = 50000  # Reasonable limit for most systems
    MAX_SAFE_POINTS = 100000  # Hard limit - will likely timeout
    WARNING_THRESHOLD = 20000  # Show warning above this

    # Display validation info
    st.sidebar.metric("Estimated Data Points", f"{estimated_points:,}")

    # Validation logic
    validation_passed = True
    validation_message = None
    suggestion = None

    if estimated_points > MAX_SAFE_POINTS:
        validation_passed = False
        validation_message = (
            f"❌ **Too granular!** {estimated_points:,} data points will likely timeout."
        )
        # Suggest better options
        if sim_interval == 1:
            if time_window_days > 7:
                suggestion = f"⚠️ **1-minute data is only available for up to 7 days.**\n\n**Options:**\n1. Reduce time window to ≤ 7 days\n2. Use 5-minute intervals (≈{calculate_data_points(time_window_days, 5, sim_include_after_hours):,} points)"
            else:
                suggestion = f"⚠️ **Too many data points for 1-minute intervals.**\n\n**Options:**\n1. Use 5-minute intervals (≈{calculate_data_points(time_window_days, 5, sim_include_after_hours):,} points)\n2. Reduce time window to {int(time_window_days * 0.5)} days"
        elif sim_interval == 5:
            suggestion = f"⚠️ **Too many data points for 5-minute intervals.**\n\n**Options:**\n1. Use 15-minute intervals (≈{calculate_data_points(time_window_days, 15, sim_include_after_hours):,} points)\n2. Reduce time window to {int(time_window_days * 0.6)} days"
        elif sim_interval == 15:
            suggestion = f"⚠️ **Too many data points for 15-minute intervals.**\n\n**Options:**\n1. Use 30-minute intervals (≈{calculate_data_points(time_window_days, 30, sim_include_after_hours):,} points)\n2. Reduce time window to {int(time_window_days * 0.7)} days"
        elif sim_interval == 30:
            suggestion = f"⚠️ **Too many data points for 30-minute intervals.**\n\n**Options:**\n1. Use 60-minute intervals (≈{calculate_data_points(time_window_days, 60, sim_include_after_hours):,} points)\n2. Reduce time window to {int(time_window_days * 0.7)} days"
        else:
            suggestion = f"⚠️ **Time window too large for hourly intervals.**\n\n**Option:** Reduce time window to {int(time_window_days * 0.7)} days"
    elif estimated_points > MAX_RECOMMENDED_POINTS:
        validation_passed = False
        validation_message = (
            f"⚠️ **High data point count:** {estimated_points:,} points may be slow."
        )
        # Suggest better options
        if sim_interval <= 15:
            next_interval = sim_interval * 2
            if next_interval <= 60:
                suggestion = f"💡 **Suggestion:** Use {next_interval}-minute intervals (≈{calculate_data_points(time_window_days, next_interval, sim_include_after_hours):,} points) for faster execution."
        else:
            suggestion = f"💡 **Suggestion:** Consider reducing time window to {int(time_window_days * 0.8)} days for faster execution."
    elif estimated_points > WARNING_THRESHOLD:
        validation_message = f"ℹ️ **Moderate data point count:** {estimated_points:,} points. Execution may take a few minutes."
    else:
        validation_message = (
            f"✅ **Good configuration:** {estimated_points:,} data points. Should execute quickly."
        )

    # Display validation message
    if validation_message:
        if not validation_passed:
            st.sidebar.error(validation_message)
        elif estimated_points > WARNING_THRESHOLD:
            st.sidebar.warning(validation_message)
        else:
            st.sidebar.success(validation_message)

    # Display suggestion if provided
    if suggestion:
        st.sidebar.markdown(suggestion)

    sim_initial_cash = st.sidebar.number_input(
        "Initial Cash (optional, uses position value if not set)",
        min_value=0.0,
        value=0.0,
        step=1000.0,
        key="sim_initial_cash",
    )

    # Disable button if validation fails
    button_disabled = not validation_passed

    if st.sidebar.button(
        "🚀 Run Simulation",
        key="run_sim_btn",
        disabled=button_disabled,
        help="Fix validation errors above before running simulation" if button_disabled else None,
    ):
        try:
            # Format dates as ISO strings with Z suffix (matching frontend format)
            # This format is compatible with backend's fromisoformat parser
            start_date_str = f"{sim_start_date.isoformat()}T00:00:00.000Z"
            end_date_str = f"{sim_end_date.isoformat()}T23:59:59.999Z"

            # Prepare request
            sim_request = {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "include_after_hours": sim_include_after_hours,
                "intraday_interval_minutes": sim_interval,
            }

            if sim_initial_cash > 0:
                sim_request["initial_cash"] = sim_initial_cash

            # Call the API endpoint for position-based simulation
            api_url = "http://localhost:8000/v1/positions/{}/simulation/run".format(
                position_id_for_sim
            )

            st.sidebar.info("Running simulation... This may take a minute.")

            response = requests.post(api_url, json=sim_request, timeout=300)

            if response.status_code == 200:
                result = response.json()
                st.session_state["simulation_result"] = result
                st.sidebar.success("Simulation completed!")
            else:
                # Try to parse error details
                try:
                    error_detail = response.json()
                    error_msg = error_detail.get(
                        "detail", error_detail.get("message", str(error_detail))
                    )
                    st.sidebar.error(f"Simulation Error\n{error_msg}")
                except (ValueError, json.JSONDecodeError):
                    st.sidebar.error(f"Simulation Error\n{response.text}")
        except requests.exceptions.Timeout:
            st.sidebar.error("Simulation timed out. Please try a shorter time period.")
        except requests.exceptions.ConnectionError:
            st.sidebar.error(
                "Cannot connect to backend. Make sure the backend is running on http://localhost:8000"
            )
        except Exception as e:
            st.sidebar.error(f"Error running simulation: {str(e)}")
            import traceback

            st.sidebar.code(traceback.format_exc())

# Display simulation results if available
if "simulation_result" in st.session_state and st.session_state["simulation_result"]:
    st.sidebar.divider()
    st.sidebar.subheader("📊 Simulation Results")
    result = st.session_state["simulation_result"]

    st.sidebar.metric("Algorithm Return", f"{result.get('algorithm_return_pct', 0):.2f}%")
    st.sidebar.metric("Buy & Hold Return", f"{result.get('buy_hold_return_pct', 0):.2f}%")
    st.sidebar.metric("Excess Return", f"{result.get('excess_return', 0):.2f}%")
    st.sidebar.metric("Total Trades", result.get("algorithm_trades", 0))
    st.sidebar.metric("Sharpe Ratio", f"{result.get('sharpe_ratio', 0):.2f}")

    if st.sidebar.button("Clear Results", key="clear_sim_results"):
        del st.session_state["simulation_result"]

# Display simulation results in main area if available
if "simulation_result" in st.session_state and st.session_state["simulation_result"]:
    st.divider()
    st.subheader("📊 Simulation Results")
    result = st.session_state["simulation_result"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Algorithm Return", f"{result.get('algorithm_return_pct', 0):.2f}%")
    with col2:
        st.metric("Buy & Hold Return", f"{result.get('buy_hold_return_pct', 0):.2f}%")
    with col3:
        st.metric("Excess Return", f"{result.get('excess_return', 0):.2f}%")
    with col4:
        st.metric("Total Trades", result.get("algorithm_trades", 0))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Algorithm P&L", f"${result.get('algorithm_pnl', 0):.2f}")
    with col2:
        st.metric("Buy & Hold P&L", f"${result.get('buy_hold_pnl', 0):.2f}")
    with col3:
        st.metric("Sharpe Ratio", f"{result.get('sharpe_ratio', 0):.2f}")
    with col4:
        st.metric("Max Drawdown", f"{result.get('max_drawdown', 0):.2f}%")

    st.json(result)

# Export options
st.sidebar.subheader("Export")
if st.sidebar.button("Export to CSV"):
    df = pd.DataFrame(filtered_events)
    csv = df.to_csv(index=False)
    st.sidebar.download_button(
        "Download CSV",
        csv,
        file_name=f"audit_trail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

if st.sidebar.button("Export to JSON"):
    json_data = json.dumps(filtered_events, indent=2)
    st.sidebar.download_button(
        "Download JSON",
        json_data,
        file_name=f"audit_trail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )
