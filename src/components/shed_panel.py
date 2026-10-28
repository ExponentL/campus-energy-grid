"""
OptiGrid - Load Flexibility & Shedding Hierarchy Panel.

Renders a single clean table-like list with four rows (priority 1 to 4):
1. EV charging
2. Hostel water heaters
3. Air conditioning
4. Labs and servers (Always on)
"""

from typing import Optional
import streamlit as st
from src.services.baseline import ScheduleResult


def render_shed_panel(
    optimized: ScheduleResult,
    trigger_hour: int,
    disruption_type: Optional[str] = None,
):
    """Render a 4-row priority table with small status dots and key metric numbers."""
    # Priority 1: EV Charging
    ev_active_hours = [t for t, kw in enumerate(optimized.ev_kw) if kw > 0.5]
    ev_peak_kw = max(optimized.ev_kw) if optimized.ev_kw else 0.0
    if disruption_type in ["price_spike", "equipment_failure", "cloud_cover"]:
        ev_dot = "#B45309"
        ev_status = "Deferred from peak"
    else:
        ev_dot = "#0F766E"
        ev_status = "Shifted to solar hours"
    ev_detail = (
        f"{optimized.ev_total_kwh:.1f} / 120.0 kWh delivered · {ev_peak_kw:.1f} kW peak · "
        f"active {min(ev_active_hours, default=8):02d}:00–{max(ev_active_hours, default=20):02d}:00"
    )

    # Priority 2: Hostel Water Heaters
    morn_kwh = sum(optimized.wh_morn_kw)
    eve_kwh = sum(optimized.wh_eve_kw)
    wh_dot = "#0F766E"
    wh_status = "Pre-heated off-peak"
    wh_detail = f"{optimized.wh_total_kwh:.1f} kWh total · morning {morn_kwh:.1f} kWh · evening {eve_kwh:.1f} kWh"

    # Priority 3: Air Conditioning
    total_shed = optimized.total_ac_shed_kwh
    v_hours = optimized.comfort_violation_hours
    if total_shed > 1.0:
        approx_temp = 24.0 + min(2.0, (total_shed / 250.0) * 2.0)
        ac_dot = "#B45309"
        ac_status = f"Relaxed (~{approx_temp:.1f}°C)"
        ac_detail = f"{v_hours} building-hours with >10% shedding · {total_shed:.1f} kWh cooling shifted"
    else:
        ac_dot = "#0F766E"
        ac_status = "Nominal setpoint (24.0°C)"
        ac_detail = "0 building-hours with >10% shedding · full comfort maintained"

    # Priority 4: Labs and Servers
    lab_dot = "#0F766E"
    lab_status = "Always on"
    lab_detail = "100.0% essential uptime · 0% shed"

    st.markdown(
        f"""
        <div style="margin-top: 6px; margin-bottom: 22px;">
            <div style="margin-bottom: 8px;">
                <div style="font-size: 15px; font-weight: 600; color: #1C1917;">Load flexibility and shedding order</div>
                <div style="font-size: 13px; color: #78716C;">Asset dispatch priority during tariff spikes, equipment derating, or cloud disruptions.</div>
            </div>
            <div style="background-color: #FFFFFF; border: 1px solid #E7E5E4; border-radius: 6px;">
                <!-- Row 1: EV charging -->
                <div style="padding: 11px 16px; border-bottom: 1px solid #E7E5E4; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 13px; font-weight: 600; color: #78716C; width: 14px;">1</span>
                        <span style="font-size: 13.5px; font-weight: 500; color: #1C1917;">EV charging</span>
                        <span style="font-size: 13px; color: #78716C;">· Library plaza</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <div style="display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500; color: #1C1917;">
                            <span style="width: 7px; height: 7px; border-radius: 50%; background-color: {ev_dot}; display: inline-block;"></span>
                            {ev_status}
                        </div>
                        <div style="font-size: 13px; color: #78716C; font-variant-numeric: tabular-nums;">
                            {ev_detail}
                        </div>
                    </div>
                </div>

                <!-- Row 2: Hostel water heaters -->
                <div style="padding: 11px 16px; border-bottom: 1px solid #E7E5E4; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 13px; font-weight: 600; color: #78716C; width: 14px;">2</span>
                        <span style="font-size: 13.5px; font-weight: 500; color: #1C1917;">Hostel water heaters</span>
                        <span style="font-size: 13px; color: #78716C;">· Hostel blocks</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <div style="display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500; color: #1C1917;">
                            <span style="width: 7px; height: 7px; border-radius: 50%; background-color: {wh_dot}; display: inline-block;"></span>
                            {wh_status}
                        </div>
                        <div style="font-size: 13px; color: #78716C; font-variant-numeric: tabular-nums;">
                            {wh_detail}
                        </div>
                    </div>
                </div>

                <!-- Row 3: Air conditioning -->
                <div style="padding: 11px 16px; border-bottom: 1px solid #E7E5E4; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 13px; font-weight: 600; color: #78716C; width: 14px;">3</span>
                        <span style="font-size: 13.5px; font-weight: 500; color: #1C1917;">Air conditioning</span>
                        <span style="font-size: 13px; color: #78716C;">· Campus-wide</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <div style="display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500; color: #1C1917;">
                            <span style="width: 7px; height: 7px; border-radius: 50%; background-color: {ac_dot}; display: inline-block;"></span>
                            {ac_status}
                        </div>
                        <div style="font-size: 13px; color: #78716C; font-variant-numeric: tabular-nums;">
                            {ac_detail}
                        </div>
                    </div>
                </div>

                <!-- Row 4: Labs and servers -->
                <div style="padding: 11px 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 13px; font-weight: 600; color: #78716C; width: 14px;">4</span>
                        <span style="font-size: 13.5px; font-weight: 500; color: #1C1917;">Labs and servers</span>
                        <span style="font-size: 13px; color: #78716C;">· Critical research</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <div style="display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500; color: #1C1917;">
                            <span style="width: 7px; height: 7px; border-radius: 50%; background-color: {lab_dot}; display: inline-block;"></span>
                            {lab_status}
                        </div>
                        <div style="font-size: 13px; color: #78716C; font-variant-numeric: tabular-nums;">
                            {lab_detail}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
