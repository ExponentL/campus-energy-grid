"""
OptiGrid - Multi-Building Energy Optimization System.

Production Streamlit application for real-time microgrid telemetry,
cross-building dispatch coordination, rolling-horizon re-optimization, and what-if exploration.
"""

import streamlit as st

# Configure page metadata must be first Streamlit command
st.set_page_config(
    page_title="OptiGrid",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

import importlib
import sys
import src.components.charts as _charts_mod
import src.components.kpi_strip as _kpi_mod
import src.components.shed_panel as _shed_mod
import src.components.theme as _theme_mod

# Explicitly reload UI component modules so active Streamlit sessions immediately reflect changes
importlib.reload(_theme_mod)
importlib.reload(_kpi_mod)
importlib.reload(_shed_mod)
importlib.reload(_charts_mod)

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
from src.services.ai_distributor import (
    predict_and_distribute_energy,
    run_ai_guided_optimization,
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

SCENARIO_FRIENDLY_NAMES = {
    "cloud_cover": "Cloud cover",
    "price_spike": "Tariff spike",
    "equipment_failure": "Substation derate",
    "occupancy_surge": "Occupancy surge",
    "ai_custom": "AI predictive dispatch",
}


def init_session():
    """Initialize Streamlit session state variables."""
    if "active_disruption" not in st.session_state:
        st.session_state.active_disruption = None
    if "trigger_hour" not in st.session_state:
        st.session_state.trigger_hour = 13
    if "ai_result" not in st.session_state:
        st.session_state.ai_result = None
    if "ai_api_key" not in st.session_state:
        st.session_state.ai_api_key = ""
    if "ai_situation" not in st.session_state:
        st.session_state.ai_situation = ""
    if "ai_custom_result" not in st.session_state:
        st.session_state.ai_custom_result = None


def trigger_cloud_cover():
    st.session_state.active_disruption = "cloud_cover"
    st.session_state.ai_custom_result = None
    st.session_state.ai_result = None


def trigger_price_spike():
    st.session_state.active_disruption = "price_spike"
    st.session_state.ai_custom_result = None
    st.session_state.ai_result = None


def trigger_equipment_failure():
    st.session_state.active_disruption = "equipment_failure"
    st.session_state.ai_custom_result = None
    st.session_state.ai_result = None


def trigger_occupancy_surge():
    st.session_state.active_disruption = "occupancy_surge"
    st.session_state.ai_custom_result = None
    st.session_state.ai_result = None


def trigger_nominal():
    st.session_state.active_disruption = None
    st.session_state.ai_custom_result = None
    st.session_state.ai_result = None
    st.session_state.ai_situation = ""


def main():
    init_session()
    apply_industrial_theme()

    # -------------------------------------------------------------------------
    # Sidebar: Clean Controls & Disruption Simulation
    # -------------------------------------------------------------------------
    # Placeholder for Mode label so it updates immediately after button triggers
    mode_placeholder = st.sidebar.empty()

    # Group 1: AI Assistant
    st.sidebar.subheader("AI assistant")

    ai_key_input = st.sidebar.text_input(
        "AI API key",
        type="password",
        value=st.session_state.ai_api_key,
        help="Optional AI API key (OpenAI / Gemini). If omitted or disconnected, automatically falls back to local calculation.",
    )
    st.session_state.ai_api_key = ai_key_input

    ai_situation_input = st.sidebar.text_area(
        "Campus situation or live event",
        value=st.session_state.ai_situation,
        placeholder="e.g. Cloud cover at 14:00 and high evening demand in Hostel",
        help="Describe upcoming weather shifts, occupancy changes, or tariff surges. The AI layer parses the event and instructs the MILP solver.",
    )
    st.session_state.ai_situation = ai_situation_input

    ai_predict_btn = st.sidebar.button(
        "Predict and distribute energy",
        type="primary",
        use_container_width=True,
    )

    # Group 2: Simulate a Disruption
    st.sidebar.subheader("Simulate a disruption")

    trigger_hour_val = st.sidebar.slider(
        "Disruption trigger hour",
        min_value=1,
        max_value=23,
        value=13 if "trigger_hour" not in st.session_state else st.session_state.trigger_hour,
        format="%02d:00",
        help="Freezes all solved decision variables for t < Trigger Hour and re-solves remaining hours.",
    )
    st.session_state.trigger_hour = trigger_hour_val

    st.sidebar.button(
        "Cloud cover",
        help="Cloud cover (−75% solar, 13:00–16:00)",
        on_click=trigger_cloud_cover,
        use_container_width=True,
    )

    st.sidebar.button(
        "Tariff spike",
        help="Tariff spike (₹22/kWh, 14:00–18:00)",
        on_click=trigger_price_spike,
        use_container_width=True,
    )

    st.sidebar.button(
        "Substation derate",
        help="Lab chiller and substation derate (−25% cap)",
        on_click=trigger_equipment_failure,
        use_container_width=True,
    )

    st.sidebar.button(
        "Occupancy surge",
        help="Academic seminar occupancy surge (+85 kW HVAC)",
        on_click=trigger_occupancy_surge,
        use_container_width=True,
    )

    st.sidebar.button(
        "Back to normal forecast",
        help="Restore nominal 24-hour campus forecast",
        on_click=trigger_nominal,
        use_container_width=True,
    )

    # Group 3: Campus Assets
    st.sidebar.subheader("Campus assets")

    import_cap = st.sidebar.slider(
        "Grid import cap (kW)",
        min_value=250.0,
        max_value=700.0,
        value=float(DEFAULT_CAMPUS_IMPORT_CAP_KW),
        step=10.0,
        help="Hard ceiling on instantaneous campus power import from the utility grid.",
    )

    battery_cap = st.sidebar.slider(
        "Battery storage capacity (kWh)",
        min_value=50.0,
        max_value=500.0,
        value=float(DEFAULT_BATTERY_CAPACITY_KWH),
        step=25.0,
        help="Capacity of the central battery system. C-rate bounds automatically scale.",
    )

    solar_cap = st.sidebar.slider(
        "Rooftop solar capacity (kWp)",
        min_value=0.0,
        max_value=350.0,
        value=float(DEFAULT_SOLAR_CAPACITY_KWP),
        step=25.0,
        help="Total rated capacity of campus solar installations.",
    )

    campus_cfg = CampusConfig(
        import_cap_kw=import_cap,
        solar_capacity_kwp=solar_cap,
    ).scale_battery(battery_cap)

    # About the data expander
    with st.sidebar.expander("About the data"):
        st.caption(
            "**Solver:** PuLP CBC mathematical solver re-optimizing on each state change.\n\n"
            "**AI assistant:** Demand prediction coupled directly to solver inputs.\n\n"
            "**Load profiles:** Building Data Genome Project 2 calibrated curves.\n\n"
            "**Solar irradiance:** Physical cache derived from Open-Meteo."
        )

    # -------------------------------------------------------------------------
    # Optimization Engine Execution
    # -------------------------------------------------------------------------
    nominal_scenario = get_scenario_data(
        disruption_type=None,
        trigger_hour=st.session_state.trigger_hour,
        campus_config=campus_cfg,
    )

    baseline_result = compute_baseline_schedule(nominal_scenario)
    initial_optimal_plan = solve_campus_milp(nominal_scenario)

    if ai_predict_btn:
        opt_res = run_ai_guided_optimization(
            api_key=ai_key_input,
            situation_text=ai_situation_input,
            trigger_hour=st.session_state.trigger_hour,
            initial_plan=initial_optimal_plan,
            campus_config=campus_cfg,
            baseline_plan=baseline_result,
        )
        st.session_state.active_disruption = "ai_custom"
        st.session_state.ai_custom_result = (
            opt_res.plan,
            opt_res.ai_explanation,
            opt_res.raw_ai_json,
            opt_res.building_allocation_df,
        )
        st.session_state.ai_opt_res = opt_res

    # Fill sidebar Mode placeholder now that all triggers have been processed
    mode_name = (
        "AI predictive dispatch"
        if st.session_state.active_disruption == "ai_custom"
        else (SCENARIO_FRIENDLY_NAMES.get(st.session_state.active_disruption) or "Nominal forecast")
    )
    mode_placeholder.markdown(
        f"""
        <div style="font-size: 13px; color: #78716C; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #E7E5E4;">
            Mode: <span style="font-weight: 600; color: #1C1917;">{mode_name}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Highlight the currently active disruption button with a teal border
    active_btn_labels = {
        "cloud_cover": "Cloud cover",
        "price_spike": "Tariff spike",
        "equipment_failure": "Substation derate",
        "occupancy_surge": "Occupancy surge",
        None: "Back to normal forecast",
    }
    highlight_lbl = active_btn_labels.get(st.session_state.active_disruption)
    if highlight_lbl:
        st.sidebar.markdown(
            f"""
            <style>
            section[data-testid="stSidebar"] button[aria-label="{highlight_lbl}"] {{
                border: 1.5px solid #0F766E !important;
                color: #0F766E !important;
                font-weight: 600 !important;
                background-color: #F0FDFA !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    active_disruption = st.session_state.active_disruption
    is_disrupted = active_disruption is not None

    if st.session_state.active_disruption == "ai_custom" and st.session_state.ai_custom_result is not None:
        ai_solved_plan, ai_explanation, raw_ai_json, building_allocation_df = st.session_state.ai_custom_result
        active_plan = ai_solved_plan
        technical_explanation = ai_explanation
        if hasattr(st.session_state, "ai_opt_res") and st.session_state.ai_opt_res is not None:
            active_scenario = getattr(st.session_state.ai_opt_res, "scenario", None) or nominal_scenario
            ai_telemetry = st.session_state.ai_opt_res
        else:
            active_scenario = nominal_scenario
            ai_telemetry = None
        alloc_matrix_df = building_allocation_df
        raw_json_to_display = raw_ai_json
        model_name_disp = ai_telemetry.model_name if ai_telemetry else "Live AI Model"
        latency_ms_disp = ai_telemetry.latency_ms if ai_telemetry else 0.0
        api_err_disp = ai_telemetry.api_error if ai_telemetry else None
        api_status_disp = (
            "200 OK (Live Cloud Model)"
            if (ai_telemetry and ai_telemetry.is_live_call)
            else ("Local Fallback Active" if api_err_disp else "Local Calculation")
        )
        status_chip_text = f"AI scenario ({latency_ms_disp:.0f} ms)"

    elif is_disrupted:
        active_plan, technical_explanation = reoptimize(
            current_hour=st.session_state.trigger_hour,
            disruption_type=active_disruption,
            initial_plan=initial_optimal_plan,
            campus_config=campus_cfg,
            baseline_plan=baseline_result,
        )
        active_scenario = get_scenario_data(
            disruption_type=active_disruption,
            trigger_hour=st.session_state.trigger_hour,
            campus_config=campus_cfg,
        )
        nom_ai_res = predict_and_distribute_energy(
            operator_input=None,
            trigger_hour=st.session_state.trigger_hour,
            campus_config=campus_cfg,
            initial_plan=active_plan,
            baseline_plan=baseline_result,
        )
        alloc_matrix_df = nom_ai_res.building_allocation_df
        raw_json_to_display = nom_ai_res.raw_json
        ai_telemetry = nom_ai_res
        model_name_disp = "Preset Disruption Engine"
        latency_ms_disp = 14.5
        api_err_disp = None
        api_status_disp = f"Preset Disruption: {active_disruption}"
        friendly_label = SCENARIO_FRIENDLY_NAMES.get(active_disruption, active_disruption)
        status_chip_text = f"Scenario: {friendly_label}"

    else:
        active_plan = initial_optimal_plan
        active_scenario = nominal_scenario
        technical_explanation = generate_explanation(
            initial_plan=initial_optimal_plan,
            reoptimized_plan=initial_optimal_plan,
            trigger_hour=st.session_state.trigger_hour,
            disrupted_scenario=nominal_scenario,
            baseline_plan=baseline_result,
        )
        nom_ai_res = predict_and_distribute_energy(
            operator_input=None,
            trigger_hour=st.session_state.trigger_hour,
            campus_config=campus_cfg,
            initial_plan=initial_optimal_plan,
            baseline_plan=baseline_result,
        )
        alloc_matrix_df = nom_ai_res.building_allocation_df
        raw_json_to_display = nom_ai_res.raw_json
        ai_telemetry = nom_ai_res
        model_name_disp = "Local Deterministic Engine"
        latency_ms_disp = 2.4
        api_err_disp = None
        api_status_disp = "Nominal Microgrid Dispatch"
        status_chip_text = "Scenario: Nominal forecast"

    # -------------------------------------------------------------------------
    # Main Dashboard Layout
    # -------------------------------------------------------------------------
    # 1. Slim Header
    render_header(
        solver_status=active_plan.solver_status,
        trigger_hour=st.session_state.trigger_hour,
        solve_time_sec=active_plan.solve_time_sec,
        essential_uptime_pct=active_plan.essential_uptime_pct,
        is_disrupted=is_disrupted,
    )

    # 2. What Changed / Today's Plan Explanation
    render_why_changed_banner(
        explanation=technical_explanation,
        solve_time_sec=active_plan.solve_time_sec,
        is_disrupted=is_disrupted,
    )

    # 3. Continuous KPI Row
    render_kpi_strip(
        baseline=baseline_result,
        optimized=active_plan,
        import_cap_kw=campus_cfg.import_cap_kw,
    )

    # 4. Hero Chart: Cross-Building Coordinated Load Stack
    st.markdown(
        """
        <div style="margin-top: 4px; margin-bottom: 8px;">
            <div style="font-size: 15px; font-weight: 600; color: #1C1917;">Cross-building load and uncoordinated baseline</div>
            <div style="font-size: 13px; color: #78716C;">Stacked 24-hour demand by building compared against uncoordinated campus baseline and substation import limit.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if active_scenario is None:
        active_scenario = nominal_scenario

    fig_stack = create_load_stack_chart(
        baseline=baseline_result,
        optimized=active_plan,
        scenario=active_scenario,
        trigger_hour=st.session_state.trigger_hour,
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    # 5. Load-Shedding Hierarchy List
    render_shed_panel(
        optimized=active_plan,
        trigger_hour=st.session_state.trigger_hour,
        disruption_type=active_disruption,
    )

    # 6. Secondary Charts (Side by Side)
    col_chart_left, col_chart_right = st.columns(2)

    with col_chart_left:
        st.markdown(
            """
            <div style="margin-top: 10px; margin-bottom: 8px;">
                <div style="font-size: 15px; font-weight: 600; color: #1C1917;">Solar generation and battery storage dispatch</div>
                <div style="font-size: 13px; color: #78716C;">Rooftop PV output, battery charge and discharge cycles, and state of charge across tariff bands.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fig_dispatch = create_dispatch_solar_battery_chart(
            optimized=active_plan,
            scenario=active_scenario,
        )
        st.plotly_chart(fig_dispatch, use_container_width=True)

    with col_chart_right:
        st.markdown(
            """
            <div style="margin-top: 10px; margin-bottom: 8px;">
                <div style="font-size: 15px; font-weight: 600; color: #1C1917;">Cooling comfort and flexible load schedules</div>
                <div style="font-size: 13px; color: #78716C;">Building-level AC power against nominal demand, with shifted EV and water heating loads.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fig_flex = create_comfort_and_flex_breakdown_chart(
            optimized=active_plan,
            scenario=active_scenario,
        )
        st.plotly_chart(fig_flex, use_container_width=True)

    # 7. Building Electricity Allocation Matrix
    st.markdown(
        f"""
        <div style="margin-top: 24px; margin-bottom: 12px; display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
            <div>
                <div style="font-size: 15px; font-weight: 600; color: #1C1917;">Building electricity allocation</div>
                <div style="font-size: 13px; color: #78716C;">Planned distribution across buildings, prioritized energy sources, and cooling comfort targets.</div>
            </div>
            <div style="font-size: 12px; color: #78716C; font-variant-numeric: tabular-nums;">
                {status_chip_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Format allocation matrix DataFrame cleanly at display time only
    disp_df = alloc_matrix_df.copy()
    col_rename = {
        "Building": "Building",
        "Predicted Peak Window": "Peak window",
        "Essential Power (kWh)": "Essential kWh",
        "Flexible/Cooling Power (kWh)": "Flexible and cooling kWh",
        "Primary Energy Source (Solar + Battery vs. Grid)": "Main source",
        "Primary Energy Source": "Main source",
        "Distribution Priority": "Priority",
    }
    disp_df = disp_df.rename(columns=col_rename)

    if "Building" in disp_df.columns:
        disp_df["Building"] = disp_df["Building"].replace({"Library_Admin": "Library & Admin"})

    def clean_priority_text(val):
        if not isinstance(val, str):
            return val
        s = val.strip()
        if "TIER 4 HARD LOCK" in s or "100% Essential" in s:
            return "Always on (never shed)"
        if "AI HIGH PRIORITY" in s or "Surge" in s:
            return "High priority surge"
        if "OPTIMAL SHIFTED" in s:
            return "Shifted, on plan"
        if "HARD LOCK" in s:
            return "Always on"
        return s.capitalize() if s.isupper() else s

    def clean_source_text(val):
        if not isinstance(val, str):
            return val
        s = val.strip()
        if "Grid + BESS Priority Bus" in s:
            return "Grid and battery buffer"
        if "Shared Solar + BESS Buffer" in s:
            return "Rooftop solar and battery"
        if "Solar Pool + Off-Peak Grid" in s:
            return "Rooftop solar and off-peak grid"
        return s

    if "Priority" in disp_df.columns:
        disp_df["Priority"] = disp_df["Priority"].apply(clean_priority_text)
    if "Main source" in disp_df.columns:
        disp_df["Main source"] = disp_df["Main source"].apply(clean_source_text)

    st.dataframe(
        disp_df,
        use_container_width=True,
        hide_index=True,
    )

    # 8. AI Response Details Expander
    with st.expander("AI response details", expanded=(st.session_state.active_disruption == "ai_custom")):
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            st.markdown(f"**Model:** `{model_name_disp}`")
        with col_t2:
            st.markdown(f"**Response time:** `{latency_ms_disp:.1f} ms`")
        with col_t3:
            st.markdown(f"**Status:** `{api_status_disp}`")

        if api_err_disp:
            st.warning(f"**Notice:** {api_err_disp}")

        st.json(raw_json_to_display)


if __name__ == "__main__":
    main()
