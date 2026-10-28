"""
OptiGrid - Quiet KPI Strip.

Renders ONE continuous white panel divided into six equal columns by thin vertical dividers.
Displays: Grid cost, Grid import, Peak demand, Carbon, Essential load, and Comfort relaxation.
"""

import streamlit as st
from src.services.baseline import ScheduleResult


def render_kpi_strip(
    baseline: ScheduleResult,
    optimized: ScheduleResult,
    import_cap_kw: float,
):
    """Render 6 equal columns in a single continuous white panel with hairline dividers."""
    # 1. Grid Cost
    cost_base = baseline.total_grid_cost_inr
    cost_opt = optimized.total_grid_cost_inr
    if cost_opt < cost_base:
        pct = ((cost_base - cost_opt) / max(1.0, cost_base)) * 100.0
        cost_sub = f'<span style="color: #0F766E;">{pct:.1f}% below baseline (₹{cost_base:,.0f})</span>'
    elif cost_opt > cost_base:
        pct = ((cost_opt - cost_base) / max(1.0, cost_base)) * 100.0
        cost_sub = f'<span style="color: #B91C1C;">{pct:.1f}% above baseline (₹{cost_base:,.0f})</span>'
    else:
        cost_sub = f'<span style="color: #78716C;">Matches baseline (₹{cost_base:,.0f})</span>'

    # 2. Grid Import
    imp_base = baseline.total_grid_import_kwh
    imp_opt = optimized.total_grid_import_kwh
    if imp_opt < imp_base:
        pct = ((imp_base - imp_opt) / max(1.0, imp_base)) * 100.0
        imp_sub = f'<span style="color: #0F766E;">{pct:.1f}% below baseline ({imp_base:,.0f} kWh)</span>'
    elif imp_opt > imp_base:
        pct = ((imp_opt - imp_base) / max(1.0, imp_base)) * 100.0
        imp_sub = f'<span style="color: #B91C1C;">{pct:.1f}% above baseline ({imp_base:,.0f} kWh)</span>'
    else:
        imp_sub = '<span style="color: #78716C;">Matches baseline</span>'

    # 3. Peak Demand
    peak_base = baseline.peak_import_kw
    peak_opt = optimized.peak_import_kw
    margin_pct = max(0.0, (import_cap_kw - peak_opt) / max(1.0, import_cap_kw)) * 100.0
    if peak_opt < peak_base:
        diff_pct = ((peak_base - peak_opt) / max(1.0, peak_base)) * 100.0
        peak_sub = f'<span style="color: #0F766E;">{diff_pct:.1f}% below baseline · {margin_pct:.0f}% under cap</span>'
    else:
        peak_sub = f'<span style="color: #78716C;">{margin_pct:.0f}% under cap ({import_cap_kw:,.0f} kW)</span>'

    # 4. Carbon
    carb_base = baseline.total_carbon_kg
    carb_opt = optimized.total_carbon_kg
    if carb_opt < carb_base:
        pct = ((carb_base - carb_opt) / max(1.0, carb_base)) * 100.0
        carb_sub = f'<span style="color: #0F766E;">{pct:.1f}% below baseline ({carb_base:,.0f} kg)</span>'
    elif carb_opt > carb_base:
        pct = ((carb_opt - carb_base) / max(1.0, carb_base)) * 100.0
        carb_sub = f'<span style="color: #B91C1C;">{pct:.1f}% above baseline</span>'
    else:
        carb_sub = '<span style="color: #78716C;">Matches baseline</span>'

    # 5. Essential Load
    uptime = optimized.essential_uptime_pct
    uptime_sub = '<span style="color: #78716C;">Always on, never shed</span>'

    # 6. Comfort Relaxation
    v_hours = optimized.comfort_violation_hours
    shed_kwh = optimized.total_ac_shed_kwh
    if shed_kwh > 0.5:
        comfort_sub = f'<span style="color: #B45309;">{shed_kwh:,.1f} kWh cooling shifted</span>'
    else:
        comfort_sub = '<span style="color: #78716C;">Full comfort maintained</span>'

    st.markdown(
        f"""
        <div style="background-color: #FFFFFF; border: 1px solid #E7E5E4; border-radius: 6px; display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); margin-bottom: 22px;">
            <div style="padding: 14px 16px; border-right: 1px solid #E7E5E4; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 13px; color: #78716C; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Grid cost</div>
                    <div style="font-size: 28px; font-weight: 600; color: #1C1917; font-variant-numeric: tabular-nums; line-height: 1.15; margin-bottom: 6px;">₹{cost_opt:,.0f}</div>
                </div>
                <div style="font-size: 12px; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{cost_sub}</div>
            </div>
            <div style="padding: 14px 16px; border-right: 1px solid #E7E5E4; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 13px; color: #78716C; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Grid import</div>
                    <div style="font-size: 28px; font-weight: 600; color: #1C1917; font-variant-numeric: tabular-nums; line-height: 1.15; margin-bottom: 6px;">
                        {imp_opt:,.0f} <span style="font-size: 13px; font-weight: 400; color: #78716C;">kWh</span>
                    </div>
                </div>
                <div style="font-size: 12px; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{imp_sub}</div>
            </div>
            <div style="padding: 14px 16px; border-right: 1px solid #E7E5E4; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 13px; color: #78716C; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Peak demand</div>
                    <div style="font-size: 28px; font-weight: 600; color: #1C1917; font-variant-numeric: tabular-nums; line-height: 1.15; margin-bottom: 6px;">
                        {peak_opt:,.1f} <span style="font-size: 13px; font-weight: 400; color: #78716C;">kW</span>
                    </div>
                </div>
                <div style="font-size: 12px; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{peak_sub}</div>
            </div>
            <div style="padding: 14px 16px; border-right: 1px solid #E7E5E4; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 13px; color: #78716C; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Carbon</div>
                    <div style="font-size: 28px; font-weight: 600; color: #1C1917; font-variant-numeric: tabular-nums; line-height: 1.15; margin-bottom: 6px;">
                        {carb_opt:,.0f} <span style="font-size: 13px; font-weight: 400; color: #78716C;">kg</span>
                    </div>
                </div>
                <div style="font-size: 12px; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{carb_sub}</div>
            </div>
            <div style="padding: 14px 16px; border-right: 1px solid #E7E5E4; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 13px; color: #78716C; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Essential load</div>
                    <div style="font-size: 28px; font-weight: 600; color: #1C1917; font-variant-numeric: tabular-nums; line-height: 1.15; margin-bottom: 6px;">{uptime:.1f}%</div>
                </div>
                <div style="font-size: 12px; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{uptime_sub}</div>
            </div>
            <div style="padding: 14px 16px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 13px; color: #78716C; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Comfort relaxation</div>
                    <div style="font-size: 28px; font-weight: 600; color: #1C1917; font-variant-numeric: tabular-nums; line-height: 1.15; margin-bottom: 6px;">
                        {v_hours} <span style="font-size: 13px; font-weight: 400; color: #78716C;">hrs</span>
                    </div>
                </div>
                <div style="font-size: 12px; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{comfort_sub}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
