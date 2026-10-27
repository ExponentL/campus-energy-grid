"""
Campus Energy Command Center - SCADA Industrial Theme Engine.

Implements clean, modern ABB / Siemens / Grid-OS industrial SCADA aesthetic:
- Neutral background (#F4F6F8), crisp borders (#CBD5E1 / #E2E8F0), 6px border-radius, subtle elevation
- Monospace tabular numerals for technical metrics (kW, kWh, INR, timing)
- Spacious typography, clear visual hierarchy, and high contrast status indicators
"""

import streamlit as st

# Color Palette Constants
COLOR_BG = "#F4F6F8"
COLOR_CARD = "#FFFFFF"
COLOR_BORDER = "#CBD5E1"
COLOR_BORDER_LIGHT = "#E2E8F0"
COLOR_TEXT_MAIN = "#0F172A"
COLOR_TEXT_MUTED = "#64748B"
COLOR_TEAL = "#0F766E"
COLOR_AMBER = "#D97706"
COLOR_CRIMSON = "#DC2626"
COLOR_BLUE = "#2563EB"
COLOR_PURPLE = "#7C3AED"
COLOR_GREEN = "#16A34A"


def apply_industrial_theme():
    """Inject global modern SCADA industrial CSS into the Streamlit session."""
    st.markdown(
        """
        <style>
        /* Import clean monospace and sans typography */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

        /* Root styling overrides */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #0F172A;
            background-color: #F4F6F8;
        }

        .stApp {
            background-color: #F4F6F8;
        }

        /* Monospace tabular numerals for technical metrics */
        .tabular-nums {
            font-family: 'JetBrains Mono', monospace;
            font-variant-numeric: tabular-nums;
        }

        /* Top header container */
        .scada-header {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 14px 22px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        }

        .scada-title {
            font-size: 1.18rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            color: #0F172A;
            text-transform: uppercase;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .scada-title-tag {
            background-color: #0F766E;
            color: #FFFFFF;
            font-size: 0.68rem;
            padding: 2px 7px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            letter-spacing: 0.06em;
        }

        .scada-badges {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .scada-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            padding: 5px 10px;
            border-radius: 4px;
            border: 1px solid #CBD5E1;
            background-color: #F8FAFC;
            color: #334155;
            text-transform: uppercase;
        }

        .badge-active {
            border-color: #99F6E4;
            color: #0F766E;
            background-color: #F0FDFA;
        }

        .badge-locked {
            border-color: #BFDBFE;
            color: #1D4ED8;
            background-color: #EFF6FF;
        }

        .badge-alert {
            border-color: #FECACA;
            color: #B91C1C;
            background-color: #FEF2F2;
        }

        /* Why The Plan Changed Industrial Callout */
        .plan-changed-banner {
            background-color: #FFFFFF;
            padding: 14px 20px;
            border-radius: 6px;
            border: 1px solid #E2E8F0;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        }

        .banner-normal {
            border-left: 5px solid #0F766E;
        }

        .banner-disruption {
            border-left: 5px solid #DC2626;
            background-color: #FFFDFD;
        }

        .banner-label {
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }

        .banner-text {
            font-size: 0.90rem;
            line-height: 1.50;
            color: #1E293B;
            margin: 0;
            font-weight: 450;
        }

        /* KPI Cards */
        .kpi-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 16px 16px;
            height: 100%;
            min-height: 120px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .kpi-label {
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #64748B;
            margin-bottom: 6px;
        }

        .kpi-value-row {
            display: flex;
            align-items: baseline;
            gap: 6px;
            margin-bottom: 6px;
        }

        .kpi-main-val {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.65rem;
            font-weight: 700;
            color: #0F172A;
            line-height: 1.1;
        }

        .kpi-unit {
            font-family: 'Inter', sans-serif;
            font-size: 0.82rem;
            color: #64748B;
            font-weight: 500;
        }

        .kpi-footer-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.76rem;
        }

        .kpi-sub-val {
            font-family: 'JetBrains Mono', monospace;
            color: #64748B;
            font-size: 0.74rem;
        }

        .kpi-pill-good {
            background-color: #DCFCE7;
            color: #15803D;
            padding: 2px 8px;
            border-radius: 9999px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            font-weight: 600;
        }

        .kpi-pill-alert {
            background-color: #FEE2E2;
            color: #991B1B;
            padding: 2px 8px;
            border-radius: 9999px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            font-weight: 600;
        }

        .kpi-pill-neutral {
            background-color: #F1F5F9;
            color: #475569;
            padding: 2px 8px;
            border-radius: 9999px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            font-weight: 600;
        }

        /* 4-Tier Automated Load Shedding Matrix */
        .tier-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 14px 15px;
            height: 100%;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        }

        .tier-header {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.70rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .tier-status {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            display: inline-block;
            margin-bottom: 8px;
        }

        .tier-detail {
            font-size: 0.78rem;
            color: #334155;
            line-height: 1.45;
        }

        /* Plotly chart container crisp borders */
        .chart-box {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        }

        .chart-title {
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #1E293B;
            margin-bottom: 10px;
            border-bottom: 1px solid #F1F5F9;
            padding-bottom: 6px;
        }

        /* Sidebar industrial styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
        }

        section[data-testid="stSidebar"] .stButton > button {
            border-radius: 4px;
            border: 1px solid #CBD5E1;
            font-family: 'Inter', sans-serif;
            font-size: 0.76rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            padding: 8px 10px;
            width: 100%;
            transition: all 0.15s ease;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            border-color: #0F766E;
            color: #0F766E;
        }
        
        .stDeployButton, [data-testid="stDeployButton"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu {
            display: none !important;
            visibility: hidden !important;
        }
    
        
        [data-testid="stTickBar"] {
            display: none !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(
    solver_status: str,
    trigger_hour: int,
    solve_time_sec: float,
    essential_uptime_pct: float,
    is_disrupted: bool,
):
    """Render top SCADA telemetry header bar with live status badges."""
    badge_disrupt = "badge-alert" if is_disrupted else "badge-active"
    status_label = "DISRUPTED HORIZON" if is_disrupted else "NOMINAL FORECAST"

    st.markdown(
        f"""
        <div class="scada-header">
            <div class="scada-title">
                CAMPUS MICROGRID EMS // MULTI-BUILDING MILP CONTROLLER
                <span class="scada-title-tag">LIVE TELEMETRY</span>
            </div>
            <div class="scada-badges">
                <span class="scada-badge badge-active">SOLVER: CBC-MILP [{solver_status}]</span>
                <span class="scada-badge {badge_disrupt}">HORIZON: T={trigger_hour:02d}:00 [{status_label}]</span>
                <span class="scada-badge badge-active">LATENCY: {solve_time_sec * 1000:.1f} ms</span>
                <span class="scada-badge badge-locked">ESSENTIAL BUS: {essential_uptime_pct:.1f}% LOCKED</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_why_changed_banner(explanation: str, solve_time_sec: float, is_disrupted: bool):
    """Render high-contrast explanation callout bar directly beneath top header."""
    cls_border = "banner-disruption" if is_disrupted else "banner-normal"
    tag_color = "#DC2626" if is_disrupted else "#0F766E"
    tag_text = "REAL-TIME DISRUPTION TELEMETRY & ADAPTIVE DISPATCH" if is_disrupted else "OPTIMAL COORDINATED DISPATCH ADVISORY"

    st.markdown(
        f"""
        <div class="plan-changed-banner {cls_border}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span class="banner-label" style="color: {tag_color};">{tag_text}</span>
                <span class="tabular-nums" style="font-size: 0.74rem; color: #64748B; background: #F8FAFC; padding: 2px 8px; border-radius: 4px; border: 1px solid #E2E8F0;">
                    Re-solve Latency: {solve_time_sec * 1000:.1f} ms
                </span>
            </div>
            <p class="banner-text">{explanation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
