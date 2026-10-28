"""
OptiGrid - Quiet, Editorial Plotly Visualizations.

Generates 3 production-grade charts with calm styling, muted building palette,
no vertical gridlines, faint horizontal gridlines, and clean IBM Plex Sans typography:
1. Cross-Building Load Stack vs Baseline & Substation Limit (Hero Chart)
2. Solar Generation, Battery Storage Dispatch & Tariff Bands
3. Cooling Comfort & Flexible Load Breakdown
"""

from typing import Dict, List, Optional
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.services.baseline import ScheduleResult
from src.services.config import BUILDINGS
from src.services.data_loader import ScenarioData

# Muted palette for the 4 buildings and flexible loads
COLOR_ACADEMIC = "#4C6A92"        # Slate blue
COLOR_LAB = "#7A5C8E"             # Plum
COLOR_HOSTEL = "#B08A3E"          # Ochre
COLOR_LIBRARY = "#6B8F71"         # Sage
COLOR_EV = "#9DB4D3"              # Light slate blue
COLOR_WH = "#D8C08A"              # Light ochre
COLOR_BASELINE = "#44403C"        # Thin dark grey dashed line
COLOR_IMPORT_CAP = "#B91C1C"      # Thin red dotted line

# Storage and generation colors
COLOR_SOLAR = "#D97706"           # Warm amber
COLOR_BATT_DIS = "#0F766E"        # Teal discharge
COLOR_BATT_CHG = "#14B8A6"        # Muted teal charge
COLOR_SOC = "#0F766E"             # Teal SOC line

# Axis configuration: every 3 hours
TICK_VALS = [0, 3, 6, 9, 12, 15, 18, 21]
TICK_TEXT = ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]


def _base_chart_layout() -> dict:
    """Standardized quiet layout dictionary for all Plotly charts."""
    return dict(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(
            family="IBM Plex Sans, -apple-system, sans-serif",
            size=12,
            color="#78716C",
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#E7E5E4",
            font=dict(
                family="IBM Plex Sans, sans-serif",
                size=12,
                color="#1C1917",
            ),
        ),
        hovermode="x unified",
    )


def create_load_stack_chart(
    baseline: ScheduleResult,
    optimized: ScheduleResult,
    scenario: ScenarioData,
    trigger_hour: int = 13,
) -> go.Figure:
    """
    Chart 1: Primary Full-Width Hero Visual.
    Cross-Building Load Stack vs. Uncoordinated Baseline and Substation Limit.
    """
    if scenario is None or not hasattr(scenario, "hours"):
        from src.services.data_loader import get_scenario_data
        scenario = get_scenario_data()

    hours = scenario.hours
    fig = go.Figure()

    # Stacked components of coordinated dispatch
    # 1. Academic Building
    fig.add_trace(
        go.Bar(
            name="Academic",
            x=hours,
            y=optimized.building_total_kw["Academic"],
            marker_color=COLOR_ACADEMIC,
            opacity=0.92,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Academic: %{y:.1f} kW<extra></extra>",
        )
    )

    # 2. Lab Building (100% Essential)
    fig.add_trace(
        go.Bar(
            name="Lab",
            x=hours,
            y=optimized.building_total_kw["Lab"],
            marker_color=COLOR_LAB,
            opacity=0.92,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Lab: %{y:.1f} kW<extra></extra>",
        )
    )

    # 3. Hostel Building
    fig.add_trace(
        go.Bar(
            name="Hostel",
            x=hours,
            y=optimized.building_total_kw["Hostel"],
            marker_color=COLOR_HOSTEL,
            opacity=0.92,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Hostel: %{y:.1f} kW<extra></extra>",
        )
    )

    # 4. Library & Admin
    fig.add_trace(
        go.Bar(
            name="Library & Admin",
            x=hours,
            y=optimized.building_total_kw["Library_Admin"],
            marker_color=COLOR_LIBRARY,
            opacity=0.92,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Library & Admin: %{y:.1f} kW<extra></extra>",
        )
    )

    # 5. EV Charging (Flexible Load)
    fig.add_trace(
        go.Bar(
            name="EV charging",
            x=hours,
            y=optimized.ev_kw,
            marker_color=COLOR_EV,
            opacity=0.95,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | EV charging: %{y:.1f} kW<extra></extra>",
        )
    )

    # 6. Hostel Geysers / Water Heaters (Flexible Load)
    fig.add_trace(
        go.Bar(
            name="Hostel geysers",
            x=hours,
            y=optimized.wh_total_kw,
            marker_color=COLOR_WH,
            opacity=0.95,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Hostel geysers: %{y:.1f} kW<extra></extra>",
        )
    )

    # 7. Uncoordinated Baseline (Thin dark grey dashed line)
    fig.add_trace(
        go.Scatter(
            name="Baseline",
            x=hours,
            y=baseline.campus_net_demand_kw,
            mode="lines",
            line=dict(color=COLOR_BASELINE, width=1.8, dash="dash"),
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Baseline: %{y:.1f} kW<extra></extra>",
        )
    )

    # 8. Campus Grid Import Cap (Thin red dotted line)
    cap_values = [scenario.import_cap_kw[h] for h in hours]
    fig.add_trace(
        go.Scatter(
            name="Import cap",
            x=hours,
            y=cap_values,
            mode="lines",
            line=dict(color=COLOR_IMPORT_CAP, width=1.6, dash="dot"),
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Import cap: %{y:.1f} kW<extra></extra>",
        )
    )

    # Direct label at right end of import cap line
    fig.add_annotation(
        x=23.3,
        y=cap_values[-1],
        text="Import cap",
        showarrow=False,
        xanchor="left",
        font=dict(family="IBM Plex Sans, sans-serif", size=10.5, color=COLOR_IMPORT_CAP),
    )

    # 9. Horizon Lock Vertical Line & Plain Label
    th = int(trigger_hour)
    fig.add_shape(
        type="line",
        x0=th,
        x1=th,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="#A8A29E", width=1.4, dash="dash"),
    )
    fig.add_annotation(
        x=th,
        y=1.03,
        yref="paper",
        text=f"Plan locked before {th:02d}:00",
        showarrow=False,
        xanchor="center",
        font=dict(family="IBM Plex Sans, sans-serif", size=11, color="#78716C"),
    )

    layout_dict = _base_chart_layout()
    layout_dict.update(
        barmode="stack",
        height=420,
        margin=dict(l=46, r=46, t=32, b=36),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="left",
            x=0.0,
            font=dict(size=11.5, color="#78716C"),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            tickmode="array",
            tickvals=TICK_VALS,
            ticktext=TICK_TEXT,
            tickangle=0,
            range=[-0.5, 24.2],
            showgrid=False,
            linecolor="#E7E5E4",
            tickfont=dict(family="IBM Plex Sans, sans-serif", size=11, color="#78716C"),
        ),
        yaxis=dict(
            title=dict(text="kW", font=dict(size=11, color="#78716C")),
            showgrid=True,
            gridcolor="#F1F0EE",
            gridwidth=1,
            linecolor="#E7E5E4",
            tickfont=dict(family="IBM Plex Sans, sans-serif", size=11, color="#78716C"),
            rangemode="tozero",
        ),
    )
    fig.update_layout(**layout_dict)
    return fig


def create_dispatch_solar_battery_chart(
    optimized: ScheduleResult,
    scenario: ScenarioData,
) -> go.Figure:
    """
    Chart 2: Solar Generation, Battery Storage Dispatch & Tariff Bands.
    Dual-axis visual with short y-axis labels and tariff labels placed at top edge outside the plot area.
    """
    if scenario is None or not hasattr(scenario, "hours"):
        from src.services.data_loader import get_scenario_data
        scenario = get_scenario_data()

    hours = scenario.hours
    bess_cap = scenario.campus_config.battery_capacity_kwh
    solar_vals = [scenario.solar_available_kw[h] for h in hours]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Subtle Background Bands for ToU Tariff (very faint fills)
    # Off-Peak: 0..5 (₹5.0)
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=5.5, y0=0, y1=1, yref="paper",
        fillcolor="#F5F5F4", opacity=0.35, layer="below", line_width=0,
    )
    fig.add_annotation(
        x=2.5, y=1.02, yref="paper", text="Off-peak ₹5", showarrow=False,
        font=dict(size=10.5, family="IBM Plex Sans", color="#78716C"),
    )

    # Standard: 6..17 (₹7.5)
    fig.add_shape(
        type="rect",
        x0=5.5, x1=17.5, y0=0, y1=1, yref="paper",
        fillcolor="#FAFAF9", opacity=0.25, layer="below", line_width=0,
    )
    fig.add_annotation(
        x=11.5, y=1.02, yref="paper", text="Standard ₹7.5", showarrow=False,
        font=dict(size=10.5, family="IBM Plex Sans", color="#78716C"),
    )

    # Peak: 18..21 (₹10.0)
    fig.add_shape(
        type="rect",
        x0=17.5, x1=21.5, y0=0, y1=1, yref="paper",
        fillcolor="#FEF2F2", opacity=0.35, layer="below", line_width=0,
    )
    fig.add_annotation(
        x=19.5, y=1.02, yref="paper", text="Peak ₹10", showarrow=False,
        font=dict(size=10.5, family="IBM Plex Sans", color="#B91C1C"),
    )

    # Late Off-Peak: 22..23 (₹5.0)
    fig.add_shape(
        type="rect",
        x0=21.5, x1=23.5, y0=0, y1=1, yref="paper",
        fillcolor="#F5F5F4", opacity=0.35, layer="below", line_width=0,
    )

    # 2. Solar Generation (kW)
    fig.add_trace(
        go.Scatter(
            name="Solar generation",
            x=hours,
            y=solar_vals,
            mode="lines",
            line=dict(color=COLOR_SOLAR, width=1.8),
            fill="tozeroy",
            fillcolor="rgba(217, 119, 6, 0.08)",
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Solar: %{y:.1f} kW<extra></extra>",
        ),
        secondary_y=False,
    )

    # 3. Battery Discharge (kW) - Positive teal bars
    fig.add_trace(
        go.Bar(
            name="Battery discharge",
            x=hours,
            y=optimized.batt_discharge,
            marker_color=COLOR_BATT_DIS,
            opacity=0.85,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Discharge: %{y:.1f} kW<extra></extra>",
        ),
        secondary_y=False,
    )

    # 4. Battery Charge (kW) - Negative muted teal bars
    fig.add_trace(
        go.Bar(
            name="Battery charge",
            x=hours,
            y=[-v for v in optimized.batt_charge],
            marker_color=COLOR_BATT_CHG,
            opacity=0.85,
            customdata=[(f"{h:02d}:00", v) for h, v in zip(hours, optimized.batt_charge)],
            hovertemplate="%{customdata[0]} | Charge: %{customdata[1]:.1f} kW<extra></extra>",
        ),
        secondary_y=False,
    )

    # 5. Battery State of Charge (%) on Secondary Axis
    soc_pct = [(soc / max(1.0, bess_cap)) * 100.0 for soc in optimized.batt_soc]
    fig.add_trace(
        go.Scatter(
            name="State of charge %",
            x=hours,
            y=soc_pct,
            mode="lines",
            line=dict(color=COLOR_SOC, width=1.8),
            customdata=[(f"{h:02d}:00", soc) for h, soc in zip(hours, optimized.batt_soc)],
            hovertemplate="%{customdata[0]} | SOC: %{y:.1f}%% (%{customdata[1]:.1f} kWh)<extra></extra>",
        ),
        secondary_y=True,
    )

    layout_dict = _base_chart_layout()
    layout_dict.update(
        height=340,
        margin=dict(l=48, r=54, t=32, b=36),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.09,
            xanchor="left",
            x=0.0,
            font=dict(size=11, color="#78716C"),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            tickmode="array",
            tickvals=TICK_VALS,
            ticktext=TICK_TEXT,
            tickangle=0,
            range=[-0.5, 23.5],
            showgrid=False,
            linecolor="#E7E5E4",
            tickfont=dict(family="IBM Plex Sans, sans-serif", size=11, color="#78716C"),
        ),
    )
    fig.update_layout(**layout_dict)

    fig.update_yaxes(
        title_text="kW",
        title_font=dict(size=11, color="#78716C"),
        secondary_y=False,
        showgrid=True,
        gridcolor="#F1F0EE",
        gridwidth=1,
        linecolor="#E7E5E4",
        tickfont=dict(family="IBM Plex Sans, sans-serif", size=11, color="#78716C"),
    )
    fig.update_yaxes(
        title_text="State of charge %",
        title_font=dict(size=11, color="#78716C"),
        secondary_y=True,
        range=[0, 105],
        showgrid=False,
        linecolor="#E7E5E4",
        tickfont=dict(family="IBM Plex Sans, sans-serif", size=11, color="#78716C"),
    )

    return fig


def create_comfort_and_flex_breakdown_chart(
    optimized: ScheduleResult,
    scenario: ScenarioData,
) -> go.Figure:
    """
    Chart 3: Cooling Comfort & Flexible Load Breakdown.
    Shows nominal vs actual cooling power by building and shifted EV/WH loads.
    Height: 480px, clean subplot headings, short y-axis labels ('kW'), single row legend.
    """
    if scenario is None or not hasattr(scenario, "hours"):
        from src.services.data_loader import get_scenario_data
        scenario = get_scenario_data()

    hours = scenario.hours
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.15,
        subplot_titles=[
            "Cooling power: baseline vs. dispatch",
            "Flexible load schedule",
        ],
    )

    # Subplot 1: Building AC used vs nominal
    bldg_colors = {
        "Academic": COLOR_ACADEMIC,
        "Lab": COLOR_LAB,
        "Hostel": COLOR_HOSTEL,
        "Library_Admin": COLOR_LIBRARY,
    }
    bldg_labels = {
        "Academic": "Academic",
        "Lab": "Lab",
        "Hostel": "Hostel",
        "Library_Admin": "Library & Admin",
    }

    for b in BUILDINGS:
        nom_vals = [scenario.ac_nominal_kw[(b, h)] for h in hours]
        used_vals = optimized.ac_used_kw_by_bldg[b]
        col = bldg_colors.get(b, "#78716C")
        label = bldg_labels.get(b, b)

        # Nominal (thin light dotted in same hue)
        fig.add_trace(
            go.Scatter(
                name=f"{label} nominal",
                x=hours,
                y=nom_vals,
                mode="lines",
                line=dict(color=col, width=1.1, dash="dot"),
                showlegend=False,
                customdata=[f"{h:02d}:00" for h in hours],
                hovertemplate=f"%{{customdata}} | {label} nominal: %{{y:.1f}} kW<extra></extra>",
            ),
            row=1, col=1,
        )
        # Actual served (thin solid)
        fig.add_trace(
            go.Scatter(
                name=label,
                x=hours,
                y=used_vals,
                mode="lines",
                line=dict(color=col, width=1.6),
                customdata=[f"{h:02d}:00" for h in hours],
                hovertemplate=f"%{{customdata}} | {label}: %{{y:.1f}} kW<extra></extra>",
            ),
            row=1, col=1,
        )

    # Subplot 2: Flexible Loads (EV and Water Heaters)
    fig.add_trace(
        go.Bar(
            name="EV charging",
            x=hours,
            y=optimized.ev_kw,
            marker_color=COLOR_EV,
            opacity=0.9,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | EV: %{y:.1f} kW<extra></extra>",
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Bar(
            name="Hostel geysers (morn)",
            x=hours,
            y=optimized.wh_morn_kw,
            marker_color=COLOR_WH,
            opacity=0.9,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Geysers morning: %{y:.1f} kW<extra></extra>",
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Bar(
            name="Hostel geysers (eve)",
            x=hours,
            y=optimized.wh_eve_kw,
            marker_color="#C4A86C",
            opacity=0.9,
            customdata=[f"{h:02d}:00" for h in hours],
            hovertemplate="%{customdata} | Geysers evening: %{y:.1f} kW<extra></extra>",
        ),
        row=2, col=1,
    )

    layout_dict = _base_chart_layout()
    layout_dict.update(
        height=480,
        margin=dict(l=46, r=36, t=32, b=36),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="left",
            x=0.0,
            font=dict(size=11, color="#78716C"),
            bgcolor="rgba(0,0,0,0)",
        ),
        barmode="group",
    )
    fig.update_layout(**layout_dict)

    fig.update_yaxes(
        title_text="kW",
        title_font=dict(size=10.5, color="#78716C"),
        row=1, col=1,
        showgrid=True,
        gridcolor="#F1F0EE",
        linecolor="#E7E5E4",
        tickfont=dict(family="IBM Plex Sans, sans-serif", size=10.5, color="#78716C"),
    )
    fig.update_yaxes(
        title_text="kW",
        title_font=dict(size=10.5, color="#78716C"),
        row=2, col=1,
        showgrid=True,
        gridcolor="#F1F0EE",
        linecolor="#E7E5E4",
        tickfont=dict(family="IBM Plex Sans, sans-serif", size=10.5, color="#78716C"),
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=TICK_VALS,
        ticktext=TICK_TEXT,
        tickangle=0,
        range=[-0.5, 23.5],
        showgrid=False,
        linecolor="#E7E5E4",
        tickfont=dict(family="IBM Plex Sans, sans-serif", size=10.5, color="#78716C"),
        row=2, col=1,
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=TICK_VALS,
        ticktext=TICK_TEXT,
        tickangle=0,
        range=[-0.5, 23.5],
        showgrid=False,
        linecolor="#E7E5E4",
        row=1, col=1,
    )

    # Style subplot title annotations cleanly in normal-case font
    for ann in fig.layout.annotations:
        ann.font.size = 12
        ann.font.family = "IBM Plex Sans, sans-serif"
        ann.font.color = "#1C1917"

    return fig
