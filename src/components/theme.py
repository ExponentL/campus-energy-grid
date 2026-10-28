"""
OptiGrid - Quiet, Editorial UI Theme Engine.

Implements a calm, professional design system:
- Palette: #FAFAF9 page background, #FFFFFF surface, #1C1917 text, #78716C secondary, #E7E5E4 hairlines
- Single accent teal #0F766E, alert #B91C1C, warning #B45309
- Single font: IBM Plex Sans with tabular-nums; zero monospace fonts
- Sentence case everywhere, no uppercase transforms, no letter-spacing tricks, 6px radius, no box-shadows
- Reduced top whitespace for a compact, editorial layout
"""

from typing import Optional
import re
import streamlit as st

# Design System Colors
COLOR_BG = "#FAFAF9"
COLOR_SURFACE = "#FFFFFF"
COLOR_TEXT = "#1C1917"
COLOR_TEXT_SECONDARY = "#78716C"
COLOR_BORDER = "#E7E5E4"
COLOR_ACCENT = "#0F766E"
COLOR_ALERT = "#B91C1C"
COLOR_WARNING = "#B45309"

# Backwards-compatibility aliases
COLOR_CARD = COLOR_SURFACE
COLOR_BORDER_LIGHT = COLOR_BORDER
COLOR_TEXT_MAIN = COLOR_TEXT
COLOR_TEXT_MUTED = COLOR_TEXT_SECONDARY
COLOR_TEAL = COLOR_ACCENT
COLOR_AMBER = COLOR_WARNING
COLOR_CRIMSON = COLOR_ALERT
COLOR_BLUE = "#4C6A92"
COLOR_PURPLE = "#7A5C8E"
COLOR_GREEN = COLOR_ACCENT


def apply_industrial_theme():
    """Inject global editorial CSS overrides into the Streamlit session."""
    st.markdown(
        """
        <style>
        /* Import IBM Plex Sans */
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        /* Root & global typography */
        html, body, [class*="css"], .stApp {
            font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            color: #1C1917;
            background-color: #FAFAF9;
        }

        /* Reduce top empty gap in main view */
        .main .block-container {
            max-width: 1280px;
            padding-top: 1.25rem !important;
            padding-bottom: 2.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            margin: 0 auto;
        }

        /* Reduce top empty gap in sidebar */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E7E5E4 !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.25rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1.15rem !important;
            padding-right: 1.15rem !important;
        }

        header[data-testid="stHeader"] {
            height: 1.25rem !important;
            background: transparent !important;
        }

        /* Tabular numerals for numbers */
        .tabular-nums, [data-testid="stMetricValue"], [data-testid="stDataFrame"] {
            font-variant-numeric: tabular-nums;
        }

        /* Sidebar subheaders in clean sentence case */
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] [data-testid="stHeadingWithActionElements"] {
            font-size: 13.5px !important;
            font-weight: 600 !important;
            color: #1C1917 !important;
            text-transform: none !important;
            letter-spacing: normal !important;
            margin-top: 16px !important;
            margin-bottom: 6px !important;
        }

        /* Button styling: 34px high, 6px radius, no uppercase */
        .stButton > button {
            height: 34px !important;
            min-height: 34px !important;
            border-radius: 6px !important;
            font-family: 'IBM Plex Sans', sans-serif !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            text-transform: none !important;
            letter-spacing: normal !important;
            border: 1px solid #E7E5E4 !important;
            background-color: #FFFFFF !important;
            color: #1C1917 !important;
            box-shadow: none !important;
            padding: 0 12px !important;
            transition: all 0.15s ease !important;
            white-space: nowrap !important;
        }

        .stButton > button:hover {
            border-color: #0F766E !important;
            color: #0F766E !important;
            background-color: #FAFAF9 !important;
        }

        /* Primary button: filled teal #0F766E */
        .stButton > button[kind="primary"],
        button[data-testid="baseButton-primary"] {
            background-color: #0F766E !important;
            border: 1px solid #0F766E !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        .stButton > button[kind="primary"]:hover,
        button[data-testid="baseButton-primary"]:hover {
            background-color: #115E59 !important;
            border-color: #115E59 !important;
            color: #FFFFFF !important;
        }

        /* Text Input & Text Area styling */
        .stTextInput input, .stTextArea textarea {
            border: 1px solid #E7E5E4 !important;
            border-radius: 6px !important;
            font-family: 'IBM Plex Sans', sans-serif !important;
            font-size: 13px !important;
            background-color: #FFFFFF !important;
            color: #1C1917 !important;
            box-shadow: none !important;
        }

        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #0F766E !important;
            box-shadow: 0 0 0 1px #0F766E !important;
        }

        /* Slider tick labels */
        div[data-testid="stSliderTickBarMin"], div[data-testid="stSliderTickBarMax"] {
            font-family: 'IBM Plex Sans', sans-serif !important;
            font-size: 11px !important;
            color: #78716C !important;
        }

        /* Streamlit Expander styling */
        div[data-testid="stExpander"] {
            border: 1px solid #E7E5E4 !important;
            border-radius: 6px !important;
            background-color: #FFFFFF !important;
            box-shadow: none !important;
        }

        div[data-testid="stExpander"] details summary {
            font-family: 'IBM Plex Sans', sans-serif !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            color: #1C1917 !important;
            padding: 9px 13px !important;
        }

        /* Dataframe styling */
        div[data-testid="stDataFrame"] {
            border: 1px solid #E7E5E4 !important;
            border-radius: 6px !important;
            background-color: #FFFFFF !important;
        }

        /* Hide Streamlit chrome / decoration */
        .stDeployButton, [data-testid="stDeployButton"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {
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
    """
    Render a single slim row.
    Left: "OptiGrid" (24px, 600, one line, never wraps) + subtitle.
    Right: 8px dot (teal for nominal, red for disruption) + "Plan optimal" / "Disruption at 13:00"
    and "Solved in 22.9 ms" in secondary text.
    """
    dot_color = COLOR_ALERT if is_disrupted else COLOR_ACCENT
    status_label = f"Disruption at {trigger_hour:02d}:00" if is_disrupted else "Plan optimal"
    solve_ms = solve_time_sec * 1000.0

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: baseline; padding-bottom: 10px; margin-bottom: 14px; border-bottom: 1px solid #E7E5E4; flex-wrap: nowrap; gap: 16px;">
            <div style="min-width: 0;">
                <h1 style="font-size: 24px; font-weight: 600; color: #1C1917; margin: 0; line-height: 1.2; letter-spacing: -0.02em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    OptiGrid
                </h1>
                <div style="font-size: 13px; color: #78716C; margin-top: 2px; font-weight: 400; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    Multi-building 24-hour microgrid optimization and storage dispatch
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 13px; flex-shrink: 0; white-space: nowrap;">
                <span style="width: 8px; height: 8px; border-radius: 50%; background-color: {dot_color}; display: inline-block;"></span>
                <span style="font-weight: 500; color: #1C1917;">{status_label}</span>
                <span style="color: #78716C; font-variant-numeric: tabular-nums;">· Solved in {solve_ms:.1f} ms</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_why_changed_banner(explanation: str, solve_time_sec: float, is_disrupted: bool):
    """
    Parse backend explanation caps prefix safely at display time.
    Show short normal-case heading ('Plan changed from 13:00 to 23:00' or 'Today's plan')
    and body split into sentences, max-width ~70 characters, 14px, no boxes or borders.
    Latency is removed from banner (shown only in header).
    """
    # Safe regex parsing of backend prefix like "DISRUPTION RESPONSE [13:00–23:00]:"
    match = re.match(r"^[A-Z\s_/-]+\[(\d{1,2}:\d{2})[–-](\d{1,2}:\d{2})\]:\s*(.*)", explanation, re.DOTALL)
    if match:
        start_t = match.group(1)
        end_t = match.group(2)
        body = match.group(3).strip()
        heading = f"Plan changed from {start_t} to {end_t}" if is_disrupted else "Today's plan"
    else:
        heading = "What changed" if is_disrupted else "Today's plan"
        body = explanation.strip()

    # Split into short sentences
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    sentences_html = "".join(f"<div style='margin-bottom: 3px;'>{s}</div>" for s in sentences)

    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <div style="font-size: 15px; font-weight: 600; color: #1C1917; margin-bottom: 5px;">
                {heading}
            </div>
            <div style="font-size: 14px; line-height: 1.55; color: #1C1917; max-width: 70ch;">
                {sentences_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
