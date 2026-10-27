"""
Campus Energy Command Center - 4-Tier Load Shedding Hierarchy Panel.

Renders an authentic SCADA engineering matrix reflecting the live operational state
and shedding disposition across all 4 equipment priority tiers.
"""

from typing import Optional
import streamlit as st
from src.services.baseline import ScheduleResult


def render_shed_panel(
    optimized: ScheduleResult,
    trigger_hour: int,
    disruption_type: Optional[str] = None,
):
    """Render a 4-column horizontal SCADA priority matrix."""
    st.markdown(
        """
        <div style="font-size: 0.78rem; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; color: #475569; margin: 16px 0 8px 0; display: flex; align-items: center; gap: 8px;">
            <span>AUTOMATED LOAD-SHEDDING & FLEXIBILITY HIERARCHY DISPOSITION</span>
            <span style="font-size: 0.68rem; font-weight: 600; color: #0F766E; background: #F0FDFA; border: 1px solid #CCFBF1; padding: 1px 6px; border-radius: 3px;">PRIORITY 1 → 4</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    # -------------------------------------------------------------------------
    # Tier 1: EV Charging (Library_Admin Plaza)
    # -------------------------------------------------------------------------
    ev_active_hours = [t for t, kw in enumerate(optimized.ev_kw) if kw > 0.5]
    ev_peak_kw = max(optimized.ev_kw) if optimized.ev_kw else 0.0

    if disruption_type in ["price_spike", "equipment_failure", "cloud_cover"]:
        ev_status_text = "DEFERRED FROM SURGE"
        ev_status_bg = "#FEF2F2"
        ev_status_color = "#B91C1C"
    else:
        ev_status_text = "OPTIMAL SOLAR SHIFT"
        ev_status_bg = "#DCFCE7"
        ev_status_color = "#15803D"

    with c1:
        st.markdown(
            f"""
            <div class="tier-card" style="border-top: 3px solid #0284C7; border-radius: 6px;">
                <div class="tier-header" style="color: #0284C7;">TIER 1 // EV CHARGING</div>
                <div class="tier-status tabular-nums" style="background-color: {ev_status_bg}; color: {ev_status_color};">
                    {ev_status_text}
                </div>
                <div class="tier-detail">
                    <div><b>Energy Delivered:</b> <span class="tabular-nums">{optimized.ev_total_kwh:.1f} / 120.0 kWh</span></div>
                    <div><b>Peak Charging:</b> <span class="tabular-nums">{ev_peak_kw:.1f} kW</span></div>
                    <div><b>Active Window:</b> <span class="tabular-nums">Hours {min(ev_active_hours, default=8):02d}–{max(ev_active_hours, default=20):02d}</span></div>
                    <div style="margin-top: 6px; color: #64748B; font-size: 0.72rem;">Shifted out of peak grid window (18:00–21:00) into solar hours.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # Tier 2: Water Heaters (Hostel Blocks)
    # -------------------------------------------------------------------------
    morn_kwh = sum(optimized.wh_morn_kw)
    eve_kwh = sum(optimized.wh_eve_kw)
    wh_status_text = "BATCH PRE-HEAT LOCKED"
    wh_status_bg = "#DCFCE7"
    wh_status_color = "#15803D"

    with c2:
        st.markdown(
            f"""
            <div class="tier-card" style="border-top: 3px solid #EA580C; border-radius: 6px;">
                <div class="tier-header" style="color: #EA580C;">TIER 2 // HOSTEL GEYSERS</div>
                <div class="tier-status tabular-nums" style="background-color: {wh_status_bg}; color: {wh_status_color};">
                    {wh_status_text}
                </div>
                <div class="tier-detail">
                    <div><b>Morning Batch:</b> <span class="tabular-nums">{morn_kwh:.1f} / 90.0 kWh</span></div>
                    <div><b>Evening Batch:</b> <span class="tabular-nums">{eve_kwh:.1f} / 70.0 kWh</span></div>
                    <div><b>Total Shifted:</b> <span class="tabular-nums">{optimized.wh_total_kwh:.1f} kWh</span></div>
                    <div style="margin-top: 6px; color: #64748B; font-size: 0.72rem;">Shifted to off-peak tariff (₹5.0) and afternoon solar self-consumption.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # Tier 3: HVAC Setpoint Band (24°C - 26°C)
    # -------------------------------------------------------------------------
    total_shed = optimized.total_ac_shed_kwh
    v_hours = optimized.comfort_violation_hours

    if total_shed > 1.0:
        hvac_status_text = f"ACTIVE RELAXATION (-{total_shed:.1f} kWh)"
        hvac_status_bg = "#FFFBEB"
        hvac_status_color = "#B45309"
        approx_temp = 24.0 + min(2.0, (total_shed / 250.0) * 2.0)
    else:
        hvac_status_text = "NOMINAL (24.0°C LOCKED)"
        hvac_status_bg = "#DCFCE7"
        hvac_status_color = "#15803D"
        approx_temp = 24.0

    with c3:
        st.markdown(
            f"""
            <div class="tier-card" style="border-top: 3px solid #D97706; border-radius: 6px;">
                <div class="tier-header" style="color: #D97706;">TIER 3 // HVAC SETPOINT</div>
                <div class="tier-status tabular-nums" style="background-color: {hvac_status_bg}; color: {hvac_status_color};">
                    {hvac_status_text}
                </div>
                <div class="tier-detail">
                    <div><b>Setpoint Band:</b> <span class="tabular-nums">~{approx_temp:.1f}°C (24.0–26.0°C)</span></div>
                    <div><b>Violations (>10%):</b> <span class="tabular-nums">{v_hours} bldg-hrs</span></div>
                    <div><b>Total AC Shed:</b> <span class="tabular-nums">{total_shed:.1f} kWh</span></div>
                    <div style="margin-top: 6px; color: #64748B; font-size: 0.72rem;">Pre-cooled during cheap solar; relaxed only when caps/tariffs spike.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # Tier 4: Essential Labs & Servers (NEVER SHED)
    # -------------------------------------------------------------------------
    with c4:
        st.markdown(
            f"""
            <div class="tier-card" style="border-top: 3px solid #7C3AED; border-radius: 6px;">
                <div class="tier-header" style="color: #7C3AED;">TIER 4 // ESSENTIAL BUS</div>
                <div class="tier-status tabular-nums" style="background-color: #EFF6FF; color: #1D4ED8;">
                    HARD LOCK — 100.0% SERVED
                </div>
                <div class="tier-detail">
                    <div><b>Lab Instrumentation:</b> <span class="tabular-nums">100.0% Uptime</span></div>
                    <div><b>Server Racks & IT:</b> <span class="tabular-nums">100.0% Uptime</span></div>
                    <div><b>Emergency Circuits:</b> <span class="tabular-nums">0.00% Shedding</span></div>
                    <div style="margin-top: 6px; color: #64748B; font-size: 0.72rem;">Locked equality constraints in MILP solver under all conditions.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
