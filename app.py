"""
Campus Energy Command Center - Multi-Building MILP Optimization System.

Production Streamlit SCADA application for real-time microgrid telemetry,
cross-building dispatch coordination, rolling-horizon re-optimization, and what-if exploration.
"""

import streamlit as st

# Configure page metadata must be first Streamlit command
st.set_page_config(
    page_title="Campus Microgrid EMS // MILP Controller",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.components.charts import (
    create_comfort_and_flex_breakdown_chart,
    create_dispatch_solar_battery_chart,
    create_load_stack_chart,
)
from src.components.kpi_strip import render_kpi_strip
from src.components.shed_panel import render_shed_panel
from src.components.theme import (
    apply_industrial_theme,
    render_header,
    render_why_changed_banner,
)
from src.services.baseline import compute_baseline_schedule
from src.services.config import (
    DEFAULT_BATTERY_CAPACITY_KWH,
    DEFAULT_CAMPUS_IMPORT_CAP_KW,
    DEFAULT_SOLAR_CAPACITY_KWP,
    CampusConfig,
)
from src.services.data_loader import SCENARIO_NAMES, get_scenario_data
from src.services.optimizer import (
    generate_explanation,
    reoptimize,
    solve_campus_milp,
)


def init_session():
    """Initialize Streamlit session state variables."""
    if "active_disruption" not in st.session_state:
        st.session_state.active_disruption = None
    if "trigger_hour" not in st.session_state:
        st.session_state.trigger_hour = 13


def main():
    init_session()
    apply_industrial_theme()

    # -------------------------------------------------------------------------
    # Sidebar: Engineering Console & What-If Controls
    # -------------------------------------------------------------------------
    st.sidebar.markdown(
        """
        <div style="font-size: 0.88rem; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; color: #0F172A; margin-bottom: 12px; border-bottom: 2px solid #E2E8F0; padding-bottom: 8px;">
            MICROGRID DISPATCH CONSOLE
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Active Scenario Status Box
    active_disp_name = (
        SCENARIO_NAMES.get(st.session_state.active_disruption)
        or "NOMINAL 24H FORECAST"
    )
    is_active_disrupted = st.session_state.active_disruption is not None
    border_accent = "#DC2626" if is_active_disrupted else "#0F766E"
    badge_bg = "#FEF2F2" if is_active_disrupted else "#F0FDFA"
    badge_color = "#DC2626" if is_active_disrupted else "#0F766E"

    st.sidebar.markdown(
        f"""
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid {border_accent}; padding: 10px 14px; border-radius: 6px; margin-bottom: 14px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
            <div style="font-size: 0.68rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.06em;">CURRENT ACTIVE DISPATCH MODE</div>
            <div style="font-size: 0.86rem; font-weight: 700; color: #0F172A; margin-top: 3px;">{active_disp_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Section 1: Live Disruption Trigger (Rolling Re-Optimization)
    st.sidebar.markdown(
        """
        <div style="font-size: 0.74rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #64748B; margin-bottom: 6px;">
            SECTION 1 // ROLLING-HORIZON DISRUPTION INJECTION
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Disruption Trigger Hour Slider (Default locked to 13:00)
    trigger_hour_val = st.sidebar.slider(
        "Disruption Trigger Hour (Lock Past T < Hour)",
        min_value=1, max_value=23,
        value=13 if "trigger_hour" not in st.session_state else st.session_state.trigger_hour,
        format="%02d:00",
        help="Freezes all solved decision variables for t < Trigger Hour and re-solves remaining hours.",
    )
    st.session_state.trigger_hour = trigger_hour_val

    st.sidebar.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    if st.sidebar.button(
        "[TRIGGER] CLOUD COVER (-75% SOLAR, 13:00-16:00)",
        use_container_width=True,
    ):
        st.session_state.active_disruption = "cloud_cover"

    if st.sidebar.button(
        "[TRIGGER] TARIFF SPIKE (₹22/kWh, 14:00-18:00)",
        use_container_width=True,
    ):
        st.session_state.active_disruption = "price_spike"

    if st.sidebar.button(
        "[TRIGGER] LAB CHILLER / CAP DERATE (-25% CAP)",
        use_container_width=True,
    ):
        st.session_state.active_disruption = "equipment_failure"

    if st.sidebar.button(
        "[TRIGGER] OCCUPANCY SURGE (+85 kW HVAC)",
        use_container_width=True,
    ):
        st.session_state.active_disruption = "occupancy_surge"

    if st.sidebar.button(
        "[RESET] RESTORE NOMINAL 24H FORECAST",
        use_container_width=True,
    ):
        st.session_state.active_disruption = None

    # Section 2: Editable Campus Parameters (Live What-If Controls)
    st.sidebar.markdown(
        """
        <div style="font-size: 0.74rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #64748B; margin: 18px 0 6px 0;">
            SECTION 2 // CAMPUS MICROGRID INFRASTRUCTURE ASSETS
        </div>
        """,
        unsafe_allow_html=True,
    )

    import_cap = st.sidebar.slider(
        "Substation Grid Import Cap (kW)",
        min_value=250.0,
        max_value=700.0,
        value=float(DEFAULT_CAMPUS_IMPORT_CAP_KW),
        step=10.0,
        help="Hard ceiling on instantaneous campus power import from the utility grid.",
    )

    battery_cap = st.sidebar.slider(
        "Shared BESS Storage Capacity (kWh)",
        min_value=50.0,
        max_value=500.0,
        value=float(DEFAULT_BATTERY_CAPACITY_KWH),
        step=25.0,
        help="Capacity of the central battery system. C-rate bounds automatically scale.",
    )

    solar_cap = st.sidebar.slider(
        "Rooftop Solar PV Capacity (kWp)",
        min_value=0.0,
        max_value=350.0,
        value=float(DEFAULT_SOLAR_CAPACITY_KWP),
        step=25.0,
        help="Total rated capacity of campus solar installations.",
    )

    # Build campus config instance
    campus_cfg = CampusConfig(
        import_cap_kw=import_cap,
        solar_capacity_kwp=solar_cap,
    ).scale_battery(battery_cap)

    # Section 3: Simulation Transparency & Honesty Note
    st.sidebar.markdown(
        """
        <div style="font-size: 0.74rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #64748B; margin: 18px 0 6px 0;">
            SECTION 3 // SIMULATION TRANSPARENCY & DATA PROVENANCE
        </div>
        <div style="font-size: 0.72rem; color: #475569; background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 10px 12px; border-radius: 6px; line-height: 1.45; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
            <b>Live Solver:</b> PuLP / COIN-OR CBC MILP solver running in real-time on every state mutation.<br><br>
            <b>Load Profiles:</b> Scaled from Building Data Genome Project 2 (BDG2) university load curves.<br><br>
            <b>Solar & Weather:</b> Deterministic Open-Meteo physical model (data/solar_weather_cache.csv).<br><br>
            <b>Zero Hardcoded Numbers:</b> All deltas, costs, peak margins, and explanations computed live.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------------------
    # Optimization Engine Execution
    # -------------------------------------------------------------------------
    # 1. Base nominal forecast inputs
    nominal_scenario = get_scenario_data(
        disruption_type=None,
        trigger_hour=st.session_state.trigger_hour,
        campus_config=campus_cfg,
    )

    # 2. Uncoordinated baseline schedule (for KPI and chart comparison)
    baseline_result = compute_baseline_schedule(nominal_scenario)

    # 3. Initial optimal nominal dispatch plan
    initial_optimal_plan = solve_campus_milp(nominal_scenario)

    # 4. Handle active disruption via rolling re-optimization
    active_disruption = st.session_state.active_disruption
    is_disrupted = active_disruption is not None

    if is_disrupted:
        active_plan, technical_explanation = reoptimize(
            current_hour=st.session_state.trigger_hour,
            disruption_type=active_disruption,
            initial_plan=initial_optimal_plan,
            campus_config=campus_cfg,
        )
        # Fetch mutated scenario for plotting cap line and solar availability
        active_scenario = get_scenario_data(
            disruption_type=active_disruption,
            trigger_hour=st.session_state.trigger_hour,
            campus_config=campus_cfg,
        )
    else:
        active_plan = initial_optimal_plan
        active_scenario = nominal_scenario
        technical_explanation = generate_explanation(
            initial_plan=initial_optimal_plan,
            reoptimized_plan=initial_optimal_plan,
            trigger_hour=st.session_state.trigger_hour,
            disrupted_scenario=nominal_scenario,
        )

    # -------------------------------------------------------------------------
    # Main SCADA Telemetry Layout
    # -------------------------------------------------------------------------
    # Top Header Bar with Live Badges
    render_header(
        solver_status=active_plan.solver_status,
        trigger_hour=st.session_state.trigger_hour,
        solve_time_sec=active_plan.solve_time_sec,
        essential_uptime_pct=active_plan.essential_uptime_pct,
        is_disrupted=is_disrupted,
    )

    # Why The Plan Changed Industrial Callout
    render_why_changed_banner(
        explanation=technical_explanation,
        solve_time_sec=active_plan.solve_time_sec,
        is_disrupted=is_disrupted,
    )

    # Top Row KPI Strip (6 Cards)
    render_kpi_strip(
        baseline=baseline_result,
        optimized=active_plan,
        import_cap_kw=campus_cfg.import_cap_kw,
    )

    # 4-Tier Automated Load-Shedding Matrix
    render_shed_panel(
        optimized=active_plan,
        trigger_hour=st.session_state.trigger_hour,
        disruption_type=active_disruption,
    )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Main Interactive Charts
    # -------------------------------------------------------------------------
    # Chart 1 (Primary Full-Width Visual): Cross-Building Coordinated Load Stack
    st.markdown(
        """
        <div class="chart-box">
            <div class="chart-title">TELEMETRY 01 // 24-HOUR CROSS-BUILDING COORDINATED LOAD STACK VS. UNCOORDINATED BASELINE</div>
        """,
        unsafe_allow_html=True,
    )
    fig_stack = create_load_stack_chart(
        baseline=baseline_result,
        optimized=active_plan,
        scenario=active_scenario,
        trigger_hour=st.session_state.trigger_hour,
    )
    st.plotly_chart(fig_stack, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Charts 2 & 3 in two side-by-side columns
    col_chart_left, col_chart_right = st.columns(2)

    with col_chart_left:
        st.markdown(
            """
            <div class="chart-box">
                <div class="chart-title">TELEMETRY 02 // SHARED ROOFTOP SOLAR POOL & BESS STORAGE DISPATCH (kW & SOC %)</div>
            """,
            unsafe_allow_html=True,
        )
        fig_dispatch = create_dispatch_solar_battery_chart(
            optimized=active_plan,
            scenario=active_scenario,
        )
        st.plotly_chart(fig_dispatch, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_chart_right:
        st.markdown(
            """
            <div class="chart-box">
                <div class="chart-title">TELEMETRY 03 // BUILDING-LEVEL HVAC COMFORT (AC RELAXATION) & FLEXIBLE SCHEDULES</div>
            """,
            unsafe_allow_html=True,
        )
        fig_flex = create_comfort_and_flex_breakdown_chart(
            optimized=active_plan,
            scenario=active_scenario,
        )
        st.plotly_chart(fig_flex, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
