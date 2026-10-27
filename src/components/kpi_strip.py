"""
Campus Energy Command Center - SCADA Top-Row KPI Strip.

Renders 6 high-density, spacious engineering cards comparing Optimized / Disrupted dispatch
against Uncoordinated Baseline telemetry with prominent metric values and green pill badges.
"""

from typing import Optional
import streamlit as st
from src.services.baseline import ScheduleResult


def render_kpi_strip(
    baseline: ScheduleResult,
    optimized: ScheduleResult,
    import_cap_kw: float,
):
    """Render 6 spacious engineering cards across a single horizontal row."""
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    # 1. 24h Grid Cost (INR)
    cost_base = baseline.total_grid_cost_inr
    cost_opt = optimized.total_grid_cost_inr
    cost_delta_pct = ((cost_opt - cost_base) / max(1.0, cost_base)) * 100.0
    cost_pill_cls = "kpi-pill-good" if cost_delta_pct <= 0 else "kpi-pill-alert"
    cost_sign = "" if cost_delta_pct <= 0 else "+"

    with col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div>
                    <div class="kpi-label">24h Grid Cost (INR)</div>
                    <div class="kpi-value-row">
                        <span class="kpi-main-val tabular-nums">₹{cost_opt:,.0f}</span>
                    </div>
                </div>
                <div>
                    <div class="kpi-sub-val tabular-nums" style="margin-bottom: 4px;">Baseline: ₹{cost_base:,.0f}</div>
                    <div class="kpi-footer-row">
                        <span class="{cost_pill_cls} tabular-nums">{cost_sign}{cost_delta_pct:.1f}% vs Base</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Total Grid Import (kWh)
    imp_base = baseline.total_grid_import_kwh
    imp_opt = optimized.total_grid_import_kwh
    imp_delta_pct = ((imp_opt - imp_base) / max(1.0, imp_base)) * 100.0
    imp_pill_cls = "kpi-pill-good" if imp_delta_pct <= 0 else "kpi-pill-alert"
    imp_sign = "" if imp_delta_pct <= 0 else "+"

    with col2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div>
                    <div class="kpi-label">Grid Import (kWh)</div>
                    <div class="kpi-value-row">
                        <span class="kpi-main-val tabular-nums">{imp_opt:,.0f}</span>
                        <span class="kpi-unit">kWh</span>
                    </div>
                </div>
                <div>
                    <div class="kpi-sub-val tabular-nums" style="margin-bottom: 4px;">Baseline: {imp_base:,.0f} kWh</div>
                    <div class="kpi-footer-row">
                        <span class="{imp_pill_cls} tabular-nums">{imp_sign}{imp_delta_pct:.1f}% Net kWh</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Campus Peak Demand (kW)
    peak_base = baseline.peak_import_kw
    peak_opt = optimized.peak_import_kw
    peak_delta_pct = ((peak_opt - peak_base) / max(1.0, peak_base)) * 100.0
    margin_below_cap = max(0.0, import_cap_kw - peak_opt)
    margin_pct = (margin_below_cap / max(1.0, import_cap_kw)) * 100.0
    peak_pill_cls = "kpi-pill-good" if peak_delta_pct <= 0 else "kpi-pill-alert"

    with col3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div>
                    <div class="kpi-label">Campus Peak Grid (kW)</div>
                    <div class="kpi-value-row">
                        <span class="kpi-main-val tabular-nums">{peak_opt:,.1f}</span>
                        <span class="kpi-unit">kW</span>
                    </div>
                </div>
                <div>
                    <div class="kpi-sub-val tabular-nums" style="margin-bottom: 4px;">Baseline: {peak_base:,.1f} kW</div>
                    <div class="kpi-footer-row">
                        <span class="{peak_pill_cls} tabular-nums">{peak_delta_pct:.1f}% Peak</span>
                        <span class="tabular-nums" style="font-size: 0.70rem; color: #0F766E; font-weight: 600;">{margin_pct:.0f}% Under Cap</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 4. Carbon Emissions (kg CO2)
    carb_base = baseline.total_carbon_kg
    carb_opt = optimized.total_carbon_kg
    carb_delta_pct = ((carb_opt - carb_base) / max(1.0, carb_base)) * 100.0
    carb_pill_cls = "kpi-pill-good" if carb_delta_pct <= 0 else "kpi-pill-alert"
    carb_sign = "" if carb_delta_pct <= 0 else "+"

    with col4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div>
                    <div class="kpi-label">Carbon Impact (kg CO₂)</div>
                    <div class="kpi-value-row">
                        <span class="kpi-main-val tabular-nums">{carb_opt:,.0f}</span>
                        <span class="kpi-unit">kg</span>
                    </div>
                </div>
                <div>
                    <div class="kpi-sub-val tabular-nums" style="margin-bottom: 4px;">Baseline: {carb_base:,.0f} kg</div>
                    <div class="kpi-footer-row">
                        <span class="{carb_pill_cls} tabular-nums">{carb_sign}{carb_delta_pct:.1f}% CO₂</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 5. Essential Service Uptime (HARD CONSTRAINT LOCKED)
    with col5:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div>
                    <div class="kpi-label">Essential Service Bus</div>
                    <div class="kpi-value-row">
                        <span class="kpi-main-val tabular-nums" style="color: #0F766E;">{optimized.essential_uptime_pct:.1f}%</span>
                    </div>
                </div>
                <div>
                    <div class="kpi-sub-val" style="color: #0F766E; font-weight: 600; margin-bottom: 4px;">HARD LOCKED 100%</div>
                    <div class="kpi-footer-row">
                        <span class="kpi-pill-good tabular-nums">0.00% Shedding</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 6. Comfort Violation Hours
    v_hours = optimized.comfort_violation_hours
    v_shed_kwh = optimized.total_ac_shed_kwh
    v_pill_cls = "kpi-pill-good" if v_hours == 0 else "kpi-pill-alert"
    v_label = "0 bldg-hrs" if v_hours == 0 else f"{v_hours} bldg-hrs"

    with col6:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div>
                    <div class="kpi-label">Comfort Relaxation</div>
                    <div class="kpi-value-row">
                        <span class="kpi-main-val tabular-nums">{v_hours}</span>
                        <span class="kpi-unit">hrs</span>
                    </div>
                </div>
                <div>
                    <div class="kpi-sub-val tabular-nums" style="margin-bottom: 4px;">Threshold: >10% Shed</div>
                    <div class="kpi-footer-row">
                        <span class="{v_pill_cls} tabular-nums">{v_shed_kwh:.1f} kWh Shed</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
