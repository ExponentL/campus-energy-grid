"""
Campus Energy Command Center - SCADA Telemetry Plotly Visualizations.

Generates 3 production-grade industrial charts with 100% crash-free numeric axes:
1. Full-Width Primary Visual: Cross-Building Coordinated Load Stack vs Baseline & Import Cap
2. Secondary Left: Shared Solar Pool, Battery Storage Dispatch & ToU Tariff Bands
3. Secondary Right: Building-Level Comfort (AC Relaxation) & Flexible Load Schedules
"""

from typing import Dict, List, Optional
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.services.baseline import ScheduleResult
from src.services.config import BUILDINGS
from src.services.data_loader import ScenarioData


# Color configuration matching SCADA theme
COLOR_ACADEMIC = "#2563EB"
COLOR_LAB = "#7C3AED"
COLOR_HOSTEL = "#D97706"
COLOR_LIBRARY = "#059669"
COLOR_EV = "#0284C7"
COLOR_WH = "#EA580C"
COLOR_BASELINE_LINE = "#1E293B"
COLOR_CAP_LINE = "#DC2626"
COLOR_SOLAR = "#EAB308"
COLOR_BATT_CHG = "#0D9488"
COLOR_BATT_DIS = "#10B981"
COLOR_SOC = "#0284C7"

TICK_HOURS = list(range(24))
TICK_LABELS = [f"{h:02d}:00" for h in range(24)]


def create_load_stack_chart(
    baseline: ScheduleResult,
    optimized: ScheduleResult,
    scenario: ScenarioData,
    trigger_hour: int = 13,
) -> go.Figure:
    """
    Chart 1: Primary Full-Width Headline Visual.
    Cross-Building Coordinated Load Stack vs. Uncoordinated Baseline & Substation Import Cap.
    Uses numeric integer hours 0..23 on X-axis with custom string ticktext to prevent Plotly crashes.
    """
    hours = scenario.hours
    fig = go.Figure()

    # Stacked components of optimized dispatch
    # 1. Academic Building
    fig.add_trace(
        go.Bar(
            name="Academic Building",
            x=hours,
            y=optimized.building_total_kw["Academic"],
            marker_color=COLOR_ACADEMIC,
            opacity=0.90,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Academic: %{y:.1f} kW<extra></extra>",
        )
    )

    # 2. Lab Building (100% hard locked)
    fig.add_trace(
        go.Bar(
            name="Lab Building (Critical)",
            x=hours,
            y=optimized.building_total_kw["Lab"],
            marker_color=COLOR_LAB,
            opacity=0.90,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Lab: %{y:.1f} kW<extra></extra>",
        )
    )

    # 3. Hostel Building
    fig.add_trace(
        go.Bar(
            name="Hostel Building",
            x=hours,
            y=optimized.building_total_kw["Hostel"],
            marker_color=COLOR_HOSTEL,
            opacity=0.90,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Hostel: %{y:.1f} kW<extra></extra>",
        )
    )

    # 4. Library & Administration
    fig.add_trace(
        go.Bar(
            name="Library & Admin",
            x=hours,
            y=optimized.building_total_kw["Library_Admin"],
            marker_color=COLOR_LIBRARY,
            opacity=0.90,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Library/Admin: %{y:.1f} kW<extra></extra>",
        )
    )

    # 5. EV Charging Plaza (Tier 1 Flex)
    fig.add_trace(
        go.Bar(
            name="EV Charging Station",
            x=hours,
            y=optimized.ev_kw,
            marker_color=COLOR_EV,
            opacity=0.95,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | EV Charging: %{y:.1f} kW<extra></extra>",
        )
    )

    # 6. Hostel Water Heaters (Tier 2 Flex)
    fig.add_trace(
        go.Bar(
            name="Hostel Geysers (WH)",
            x=hours,
            y=optimized.wh_total_kw,
            marker_color=COLOR_WH,
            opacity=0.95,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Hostel Geysers: %{y:.1f} kW<extra></extra>",
        )
    )

    # 7. Baseline Uncoordinated Demand Curve (Dashed line)
    fig.add_trace(
        go.Scatter(
            name="Uncoordinated Baseline",
            x=hours,
            y=baseline.campus_net_demand_kw,
            mode="lines",
            line=dict(color=COLOR_BASELINE_LINE, width=2.8, dash="dash"),
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Baseline Total: %{y:.1f} kW<extra></extra>",
        )
    )

    # 8. Campus Grid Import Cap (Horizontal Line / Array)
    cap_values = [scenario.import_cap_kw[h] for h in hours]
    fig.add_trace(
        go.Scatter(
            name="Substation Import Cap",
            x=hours,
            y=cap_values,
            mode="lines",
            line=dict(color=COLOR_CAP_LINE, width=2.0, dash="dot"),
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Import Cap: %{y:.1f} kW<extra></extra>",
        )
    )

    # 9. Rolling Horizon Lock Vertical Line using explicit add_shape and add_annotation
    th = int(trigger_hour)
    fig.add_shape(
        type="line",
        x0=th,
        x1=th,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="#DC2626", width=2, dash="dash"),
    )
    fig.add_annotation(
        x=th,
        y=1.03,
        yref="paper",
        text=f"T={th:02d}:00 HORIZON LOCK",
        showarrow=False,
        font=dict(family="JetBrains Mono", size=10, color="#DC2626"),
        bgcolor="#FEF2F2",
        bordercolor="#FECACA",
        borderwidth=1,
        borderpad=3,
    )

    fig.update_layout(
        barmode="stack",
        height=390,
        margin=dict(l=45, r=25, t=35, b=40),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, sans-serif", size=11, color="#1E293B"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="left",
            x=0.0,
            font=dict(size=10),
        ),
        xaxis=dict(
            title="",
            tickmode="array",
            tickvals=TICK_HOURS,
            ticktext=TICK_LABELS,
            range=[-0.5, 23.5],
            gridcolor="#F1F5F9",
            linecolor="#CBD5E1",
            tickfont=dict(family="JetBrains Mono", size=10),
        ),
        yaxis=dict(
            title="Total Campus Power (kW)",
            gridcolor="#E2E8F0",
            linecolor="#CBD5E1",
            tickfont=dict(family="JetBrains Mono", size=10),
            rangemode="tozero",
        ),
        hovermode="x unified",
    )

    for ann in fig.layout.annotations:
        ann.font.size = 11
    return fig


def create_dispatch_solar_battery_chart(
    optimized: ScheduleResult,
    scenario: ScenarioData,
) -> go.Figure:
    """
    Chart 2: Shared Solar Pool, Battery SOC & ToU Tariff Dispatch.
    Dual-axis 24-hour visual with ToU background color bands.
    Uses numeric integer hours 0..23 to avoid any Plotly crash.
    """
    hours = scenario.hours
    bess_cap = scenario.campus_config.battery_capacity_kwh
    solar_vals = [scenario.solar_available_kw[h] for h in hours]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Background Shaded Bands for Indian ToU Tariff (Numeric x0 and x1 bounds)
    # Off-Peak: 0..5 (₹5.0)
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=5.5, y0=0, y1=1, yref="paper",
        fillcolor="#F0FDF4", opacity=0.60, layer="below", line_width=0,
    )
    fig.add_annotation(
        x=2.5, y=0.96, yref="paper", text="Off-Peak ₹5.0", showarrow=False,
        font=dict(size=9, family="JetBrains Mono", color="#15803D"),
    )

    # Normal: 6..17 (₹7.5)
    fig.add_shape(
        type="rect",
        x0=5.5, x1=17.5, y0=0, y1=1, yref="paper",
        fillcolor="#F8FAFC", opacity=0.50, layer="below", line_width=0,
    )
    fig.add_annotation(
        x=11.5, y=0.96, yref="paper", text="Normal ₹7.5", showarrow=False,
        font=dict(size=9, family="JetBrains Mono", color="#475569"),
    )

    # Peak: 18..21 (₹10.0)
    fig.add_shape(
        type="rect",
        x0=17.5, x1=21.5, y0=0, y1=1, yref="paper",
        fillcolor="#FEF2F2", opacity=0.60, layer="below", line_width=0,
    )
    fig.add_annotation(
        x=19.5, y=0.96, yref="paper", text="Peak ₹10.0", showarrow=False,
        font=dict(size=9, family="JetBrains Mono", color="#B91C1C"),
    )

    # Late Off-Peak: 22..23 (₹5.0)
    fig.add_shape(
        type="rect",
        x0=21.5, x1=23.5, y0=0, y1=1, yref="paper",
        fillcolor="#F0FDF4", opacity=0.60, layer="below", line_width=0,
    )

    # 2. Solar Available & Solar Used (kW)
    fig.add_trace(
        go.Scatter(
            name="Solar Generation",
            x=hours,
            y=solar_vals,
            mode="lines",
            line=dict(color=COLOR_SOLAR, width=2.0),
            fill="tozeroy",
            fillcolor="rgba(234, 179, 8, 0.18)",
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Solar PV: %{y:.1f} kW<extra></extra>",
        ),
        secondary_y=False,
    )

    # 3. Battery Discharge (kW) - Positive green bars
    fig.add_trace(
        go.Bar(
            name="BESS Discharge",
            x=hours,
            y=optimized.batt_discharge,
            marker_color=COLOR_BATT_DIS,
            opacity=0.85,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | BESS Discharge: %{y:.1f} kW<extra></extra>",
        ),
        secondary_y=False,
    )

    # 4. Battery Charge (kW) - Rendered as negative teal bars
    fig.add_trace(
        go.Bar(
            name="BESS Charge",
            x=hours,
            y=[-v for v in optimized.batt_charge],
            marker_color=COLOR_BATT_CHG,
            opacity=0.85,
            customdata=[(f"{h:02d}:00", v) for h, v in zip(hours, optimized.batt_charge)],
            hovertemplate="%{customdata[0]} | BESS Charge: %{customdata[1]:.1f} kW<extra></extra>",
        ),
        secondary_y=False,
    )

    # 5. Battery State of Charge (SOC %) on Secondary Axis
    soc_pct = [(soc / max(1.0, bess_cap)) * 100.0 for soc in optimized.batt_soc]
    fig.add_trace(
        go.Scatter(
            name="BESS SOC (%)",
            x=hours,
            y=soc_pct,
            mode="lines+markers",
            line=dict(color=COLOR_SOC, width=2.2),
            marker=dict(size=4),
            customdata=[(f"{h:02d}:00", soc) for h, soc in zip(hours, optimized.batt_soc)],
            hovertemplate="%{customdata[0]} | BESS SOC: %{y:.1f}%% (%{customdata[1]:.1f} kWh)<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        height=340,
        margin=dict(l=45, r=45, t=35, b=40),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, sans-serif", size=11, color="#1E293B"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="left",
            x=0.0,
            font=dict(size=10),
        ),
        xaxis=dict(
            tickmode="array",
            tickvals=TICK_HOURS,
            ticktext=TICK_LABELS,
            range=[-0.5, 23.5],
            gridcolor="#F1F5F9",
            linecolor="#CBD5E1",
            tickfont=dict(family="JetBrains Mono", size=10),
        ),
        hovermode="x unified",
    )

    fig.update_yaxes(
        title_text="Power Flow (kW) [Chg - / Dis +]",
        secondary_y=False,
        gridcolor="#E2E8F0",
        linecolor="#CBD5E1",
        tickfont=dict(family="JetBrains Mono", size=10),
    )
    fig.update_yaxes(
        title_text="BESS State of Charge (%)",
        secondary_y=True,
        range=[0, 105],
        gridcolor="rgba(0,0,0,0)",
        linecolor="#CBD5E1",
        tickfont=dict(family="JetBrains Mono", size=10),
    )

    for ann in fig.layout.annotations:
        ann.font.size = 11
    return fig


def create_comfort_and_flex_breakdown_chart(
    optimized: ScheduleResult,
    scenario: ScenarioData,
) -> go.Figure:
    """
    Chart 3: Building-Level AC Comfort & Flexible Load Breakdown.
    Shows nominal vs actual AC load per building and scheduled EV/WH profiles.
    Uses numeric integer hours 0..23 on X-axis.
    """
    hours = scenario.hours
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=[
            "HVAC COOLING: NOMINAL DEMAND VS SOLVER DISPATCH (AC RELAXATION)",
            "Flexible Loads: EV Charging & Hostel Geysers (kW)",
        ],
    )

    # Subplot 1: Building AC used vs nominal
    for b in BUILDINGS:
        nom_vals = [scenario.ac_nominal_kw[(b, h)] for h in hours]
        used_vals = optimized.ac_used_kw_by_bldg[b]

        # Nominal dashed
        fig.add_trace(
            go.Scatter(
                name=f"{b} AC Nom",
                x=hours,
                y=nom_vals,
                mode="lines",
                line=dict(color=COLOR_ACADEMIC if b == "Academic" else (COLOR_LAB if b == "Lab" else (COLOR_HOSTEL if b == "Hostel" else COLOR_LIBRARY)), width=1.2, dash="dot"),
                showlegend=False,
                customdata=[f"{h:02d}:00" for h in hours],
                hovertemplate=f"%{{customdata}} | {b} Nom: %{{y:.1f}} kW<extra></extra>",
            ),
            row=1, col=1,
        )
        # Actual served solid
        fig.add_trace(
            go.Scatter(
                name=f"{b} AC Served",
                x=hours,
                y=used_vals,
                mode="lines",
                line=dict(color=COLOR_ACADEMIC if b == "Academic" else (COLOR_LAB if b == "Lab" else (COLOR_HOSTEL if b == "Hostel" else COLOR_LIBRARY)), width=2.0),
                customdata=[f"{h:02d}:00" for h in hours],
                hovertemplate=f"%{{customdata}} | {b} Served: %{{y:.1f}} kW<extra></extra>",
            ),
            row=1, col=1,
        )

    # Subplot 2: Flexible Loads (EV and WH)
    fig.add_trace(
        go.Bar(
            name="EV Charging Plaza",
            x=hours,
            y=optimized.ev_kw,
            marker_color=COLOR_EV,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | EV: %{y:.1f} kW<extra></extra>",
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Bar(
            name="Hostel Geysers (Morn)",
            x=hours,
            y=optimized.wh_morn_kw,
            marker_color=COLOR_WH,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | WH Morn: %{y:.1f} kW<extra></extra>",
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Bar(
            name="Hostel Geysers (Eve)",
            x=hours,
            y=optimized.wh_eve_kw,
            marker_color="#C2410C",
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | WH Eve: %{y:.1f} kW<extra></extra>",
        ),
        row=2, col=1,
    )

    fig.update_layout(
        height=340,
        margin=dict(l=45, r=25, t=35, b=40),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, sans-serif", size=10, color="#1E293B"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="left",
            x=0.0,
            font=dict(size=10),
        ),
        hovermode="x unified",
        barmode="group",
    )

    fig.update_yaxes(title_text="AC Power (kW)", row=1, col=1, gridcolor="#E2E8F0")
    fig.update_yaxes(title_text="Flex Power (kW)", row=2, col=1, gridcolor="#E2E8F0")
    fig.update_xaxes(
        tickmode="array",
        tickvals=TICK_HOURS,
        ticktext=TICK_LABELS,
        range=[-0.5, 23.5],
        gridcolor="#F1F5F9",
        tickfont=dict(family="JetBrains Mono", size=10),
        row=2, col=1,
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=TICK_HOURS,
        ticktext=TICK_LABELS,
        range=[-0.5, 23.5],
        gridcolor="#F1F5F9",
        row=1, col=1,
    )

    for ann in fig.layout.annotations:
        ann.font.size = 11
    return fig
