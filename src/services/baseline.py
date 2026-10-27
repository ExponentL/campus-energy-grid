"""
Campus Energy Command Center - Uncoordinated Baseline Simulation.

Calculates the business-as-usual baseline schedule reflecting typical uncoordinated campus operations:
- EVs plug in immediately during evening peak hours (18:00–21:00 at ₹10/kWh) upon commuter return.
- Hostel water heaters fire during morning peak hours (06:00–09:00) and evening peak hours (18:00–21:00 at ₹10/kWh).
- Uncoordinated HVAC runs ~25% higher due to constant low setpoints (over-cooling at 21°C) and lack of pre-cooling.
- Rooftop solar is trapped on individual building roofs and cannot be shared or stored (self-consumption capped at 55%).
- Zero battery storage buffering (BESS remains idle at initial 80 kWh).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

from src.services.config import (
    BUILDINGS,
    GRID_CO2_FACTOR_KG_PER_KWH,
    COMFORT_VIOLATION_THRESHOLD_PCT,
)
from src.services.data_loader import ScenarioData


@dataclass
class ScheduleResult:
    """Unified container for 24-hour campus microgrid dispatch schedules and SCADA KPIs."""
    hours: List[int]
    grid_import: List[float]
    solar_used: List[float]
    solar_curtailed: List[float]
    batt_charge: List[float]
    batt_discharge: List[float]
    batt_soc: List[float]
    ev_kw: List[float]
    wh_morn_kw: List[float]
    wh_eve_kw: List[float]
    wh_total_kw: List[float]
    essential_kw_by_bldg: Dict[str, List[float]]
    ac_used_kw_by_bldg: Dict[str, List[float]]
    ac_shed_kw_by_bldg: Dict[str, List[float]]
    ac_nominal_kw_by_bldg: Dict[str, List[float]]
    building_total_kw: Dict[str, List[float]]
    campus_net_demand_kw: List[float]
    total_grid_cost_inr: float
    total_grid_import_kwh: float
    peak_import_kw: float
    peak_campus_demand_kw: float
    total_carbon_kg: float
    essential_uptime_pct: float
    comfort_violation_hours: int
    total_ac_shed_kwh: float
    ev_total_kwh: float
    wh_total_kwh: float
    solve_time_sec: float
    solver_status: str
    disruption_type: Optional[str] = None


def compute_baseline_schedule(scenario: ScenarioData) -> ScheduleResult:
    """
    Simulate uncoordinated campus operations under the provided scenario.

    Returns a ScheduleResult with identical schema to the MILP optimizer
    for direct apples-to-apples SCADA comparison.
    """
    hours = scenario.hours
    n_hours = len(hours)

    # 1. Uncoordinated Flexible Loads
    # Water Heaters: Fired right before usage peaks
    # Morning batch (90 kWh): hours 6, 7, 8 @ 30 kW each (normal daytime tariff ₹7.50)
    wh_morn = [0.0] * n_hours
    wh_morn[6] = 30.0
    wh_morn[7] = 30.0
    wh_morn[8] = 30.0

    # Evening batch (70 kWh): fired directly during peak tariff hours (18:00–21:00 at ₹10/kWh)
    # Hours 18, 19 @ 25 kW, hour 20 @ 20 kW -> 70 kWh total
    wh_eve = [0.0] * n_hours
    wh_eve[18] = 25.0
    wh_eve[19] = 25.0
    wh_eve[20] = 20.0

    wh_total = [round(wh_morn[t] + wh_eve[t], 2) for t in hours]

    # EV Charging: Commuters return in evening and plug in simultaneously during peak hours (18:00–21:00)
    # Total 120 kWh: hour 18: 35 kW, hour 19: 35 kW, hour 20: 30 kW, hour 21: 20 kW -> 120 kWh
    ev_kw = [0.0] * n_hours
    ev_kw[18] = 35.0
    ev_kw[19] = 35.0
    ev_kw[20] = 30.0
    ev_kw[21] = 20.0

    # 2. Building Loads
    # Uncoordinated HVAC runs ~25% higher due to constant low setpoints and zero pre-cooling
    essential_by_bldg: Dict[str, List[float]] = {b: [] for b in BUILDINGS}
    ac_used_by_bldg: Dict[str, List[float]] = {b: [] for b in BUILDINGS}
    ac_shed_by_bldg: Dict[str, List[float]] = {b: [] for b in BUILDINGS}
    ac_nominal_by_bldg: Dict[str, List[float]] = {b: [] for b in BUILDINGS}
    building_total: Dict[str, List[float]] = {b: [] for b in BUILDINGS}

    for b in BUILDINGS:
        for t in hours:
            ess = float(scenario.essential_kw[(b, t)])
            ac_nom = float(scenario.ac_nominal_kw[(b, t)])
            ac_used_uncoord = round(ac_nom * 1.25, 2)  # 25% cooling penalty from lack of coordination

            essential_by_bldg[b].append(round(ess, 2))
            ac_nominal_by_bldg[b].append(round(ac_nom, 2))
            ac_used_by_bldg[b].append(ac_used_uncoord)
            ac_shed_by_bldg[b].append(0.0)  # Baseline never sheds AC
            building_total[b].append(round(ess + ac_used_uncoord, 2))

    # 3. Microgrid Power Balance without Battery (Battery idle at 80 kWh)
    batt_charge = [0.0] * n_hours
    batt_discharge = [0.0] * n_hours
    batt_soc = [scenario.campus_config.battery_initial_soc_kwh] * n_hours

    grid_import: List[float] = []
    solar_used: List[float] = []
    solar_curtailed: List[float] = []
    campus_net_demand_kw: List[float] = []

    for t in hours:
        # Sum of all demands at hour t
        total_demand = sum(building_total[b][t] for b in BUILDINGS) + ev_kw[t] + wh_total[t]
        campus_net_demand_kw.append(round(total_demand, 2))

        # In an uncoordinated campus, rooftop solar cannot be shared across building feeds or stored.
        # Self-consumption is physically capped at 55% of available solar generation; rest is curtailed.
        pv_avail = scenario.solar_available_kw[t]
        pv_consumed = round(min(0.55 * pv_avail, total_demand), 2)
        pv_curtailed = round(max(0.0, pv_avail - pv_consumed), 2)

        net_import = round(max(0.0, total_demand - pv_consumed), 2)
        grid_import.append(net_import)
        solar_used.append(pv_consumed)
        solar_curtailed.append(pv_curtailed)

    # 4. SCADA Performance Metrics
    total_cost = sum(grid_import[t] * scenario.tariff_inr[t] for t in hours)
    total_import = sum(grid_import)
    peak_import = max(grid_import)
    peak_demand = max(campus_net_demand_kw)
    total_carbon = total_import * scenario.campus_config.grid_co2_factor

    # Essential uptime verification
    total_essential_demanded = sum(
        scenario.essential_kw[(b, t)] for b in BUILDINGS for t in hours
    )
    total_essential_served = sum(
        sum(essential_by_bldg[b]) for b in BUILDINGS
    )
    essential_uptime_pct = (
        100.0 if total_essential_demanded == 0
        else round((total_essential_served / total_essential_demanded) * 100.0, 2)
    )

    return ScheduleResult(
        hours=hours,
        grid_import=grid_import,
        solar_used=solar_used,
        solar_curtailed=solar_curtailed,
        batt_charge=batt_charge,
        batt_discharge=batt_discharge,
        batt_soc=batt_soc,
        ev_kw=ev_kw,
        wh_morn_kw=wh_morn,
        wh_eve_kw=wh_eve,
        wh_total_kw=wh_total,
        essential_kw_by_bldg=essential_by_bldg,
        ac_used_kw_by_bldg=ac_used_by_bldg,
        ac_shed_kw_by_bldg=ac_shed_by_bldg,
        ac_nominal_kw_by_bldg=ac_nominal_by_bldg,
        building_total_kw=building_total,
        campus_net_demand_kw=campus_net_demand_kw,
        total_grid_cost_inr=round(total_cost, 2),
        total_grid_import_kwh=round(total_import, 2),
        peak_import_kw=round(peak_import, 2),
        peak_campus_demand_kw=round(peak_demand, 2),
        total_carbon_kg=round(total_carbon, 2),
        essential_uptime_pct=essential_uptime_pct,
        comfort_violation_hours=0,
        total_ac_shed_kwh=0.0,
        ev_total_kwh=sum(ev_kw),
        wh_total_kwh=sum(wh_total),
        solve_time_sec=0.001,
        solver_status="BASELINE_HEURISTIC",
        disruption_type=scenario.disruption_type,
    )
