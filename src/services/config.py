"""
Campus Energy Command Center - System Configuration and Domain Parameters.

Defines all operational limits, Time-of-Use (ToU) tariffs, campus microgrid assets,
equipment tiers, and objective weights for multi-building MILP optimization.
"""

from dataclasses import dataclass, field
from typing import Dict, List

# -----------------------------------------------------------------------------
# 1. Campus Buildings
# -----------------------------------------------------------------------------
BUILDINGS: List[str] = ["Academic", "Lab", "Hostel", "Library_Admin"]

BUILDING_DESCRIPTIONS: Dict[str, str] = {
    "Academic": "Base networking & lighting + daytime class occupancy + variable AC comfort load",
    "Lab": "24/7 mission-critical servers, fume hoods, precision instrumentation (100% hard lock) + chiller cooling",
    "Hostel": "Morning & night occupancy peaks + batch domestic water geysers + night AC load",
    "Library_Admin": "Steady 08:00–22:00 occupancy + campus EV charging plaza + administrative AC load",
}

# -----------------------------------------------------------------------------
# 2. Time-of-Use (ToU) Electricity Tariffs (INR / kWh)
# -----------------------------------------------------------------------------
# Off-Peak: 22:00 to 05:59 (Hours 0, 1, 2, 3, 4, 5, 22, 23) -> ₹5.00 / kWh
# Normal:   06:00 to 17:59 (Hours 6 through 17)             -> ₹7.50 / kWh
# Peak:     18:00 to 21:59 (Hours 18 through 21)            -> ₹10.00 / kWh

DEFAULT_TARIFF_INR: Dict[int, float] = {
    t: (5.0 if t in [0, 1, 2, 3, 4, 5, 22, 23] else (10.0 if t in [18, 19, 20, 21] else 7.5))
    for t in range(24)
}

# -----------------------------------------------------------------------------
# 3. Shared Campus Microgrid Resources
# -----------------------------------------------------------------------------
DEFAULT_CAMPUS_IMPORT_CAP_KW: float = 480.0
DEFAULT_SOLAR_CAPACITY_KWP: float = 150.0

# Shared Battery Energy Storage System (BESS)
DEFAULT_BATTERY_CAPACITY_KWH: float = 200.0
DEFAULT_BATTERY_MIN_SOC_KWH: float = 20.0       # 10% minimum reserve (depth-of-discharge limit)
DEFAULT_BATTERY_MAX_SOC_KWH: float = 190.0      # 95% maximum charge ceiling
DEFAULT_BATTERY_INITIAL_SOC_KWH: float = 80.0   # 40% state of charge at t=0
DEFAULT_BATTERY_FINAL_SOC_KWH: float = 80.0     # Final boundary condition at t=24 to avoid free-draining
DEFAULT_BATTERY_MAX_CHARGE_KW: float = 60.0
DEFAULT_BATTERY_MAX_DISCHARGE_KW: float = 60.0
DEFAULT_BATTERY_CHARGE_EFF: float = 0.95
DEFAULT_BATTERY_DISCHARGE_EFF: float = 0.95

# Environmental & Carbon Accounting
GRID_CO2_FACTOR_KG_PER_KWH: float = 0.82  # Central Electricity Authority / Grid average

# -----------------------------------------------------------------------------
# 4. Equipment Categories & Strict Shedding Hierarchy
# -----------------------------------------------------------------------------
# TIER 1 (First to shift/shed): Campus EV Charging Station (Library_Admin)
EV_TOTAL_KWH: float = 120.0
EV_START_HOUR: int = 8
EV_DEADLINE_HOUR: int = 20  # Delivered between 08:00 and 21:00 inclusive (hours 8..20)
EV_MAX_KW: float = 35.0

# TIER 2 (Second to shift): Hostel Domestic Hot Water Geysers
# Morning batch: needed before 08:00 AM (window: hours 0..6)
WH_MORN_TOTAL_KWH: float = 90.0
WH_MORN_START_HOUR: int = 0
WH_MORN_END_HOUR: int = 6
WH_MORN_MAX_KW: float = 30.0

# Evening batch: needed before 21:00 PM (window: hours 13..19)
WH_EVE_TOTAL_KWH: float = 70.0
WH_EVE_START_HOUR: int = 13
WH_EVE_END_HOUR: int = 19
WH_EVE_MAX_KW: float = 25.0

# TIER 3 (Third to relax): HVAC / AC Comfort Loads (All 4 Buildings)
# Pre-cooling or setpoint relaxation (24°C -> 26°C) sheds up to 35% of nominal load.
MAX_AC_SHED_PCT_NORMAL: float = 0.35
MAX_AC_SHED_PCT_EMERGENCY: float = 0.45  # Permitted under severe equipment derating
COMFORT_VIOLATION_THRESHOLD_PCT: float = 0.10  # >10% AC shed counts as building comfort violation hour

# TIER 4 (NEVER SHED - HARD CONSTRAINT LOCKED): Essential Services
# Lab equipment, server racks, emergency lighting, base campus communications.
# Must be satisfied 100.0% in every single hour under all conditions.

# -----------------------------------------------------------------------------
# 5. Objective Function Weights
# -----------------------------------------------------------------------------
# Minimizing:
#   sum(tariff[t] * grid_import[t])
#   + CO2_WEIGHT * sum(0.82 * grid_import[t])
#   + BATTERY_CYCLE_COST * sum(batt_charge[t] + batt_discharge[t])
#   + PEAK_DEMAND_WEIGHT * peak_import_kw
#   + COMFORT_PENALTY_WEIGHT * sum(ac_shed_kw[b, t])

CO2_WEIGHT: float = 0.50             # INR per kg CO2 equivalent
BATTERY_CYCLE_COST: float = 0.05     # INR per kWh throughput (prevents micro-cycling & simultaneous charge/discharge)
PEAK_DEMAND_WEIGHT: float = 25.0     # INR per peak kW imported (strong incentive to flatten load)
COMFORT_PENALTY_WEIGHT: float = 22.0 # INR per kWh of AC comfort shed (AC relaxed only when necessary)


@dataclass
class CampusConfig:
    """Configurable system parameters for simulation and what-if exploration."""
    import_cap_kw: float = DEFAULT_CAMPUS_IMPORT_CAP_KW
    solar_capacity_kwp: float = DEFAULT_SOLAR_CAPACITY_KWP
    battery_capacity_kwh: float = DEFAULT_BATTERY_CAPACITY_KWH
    battery_min_soc_kwh: float = DEFAULT_BATTERY_MIN_SOC_KWH
    battery_max_soc_kwh: float = DEFAULT_BATTERY_MAX_SOC_KWH
    battery_initial_soc_kwh: float = DEFAULT_BATTERY_INITIAL_SOC_KWH
    battery_final_soc_kwh: float = DEFAULT_BATTERY_FINAL_SOC_KWH
    battery_max_charge_kw: float = DEFAULT_BATTERY_MAX_CHARGE_KW
    battery_max_discharge_kw: float = DEFAULT_BATTERY_MAX_DISCHARGE_KW
    battery_charge_eff: float = DEFAULT_BATTERY_CHARGE_EFF
    battery_discharge_eff: float = DEFAULT_BATTERY_DISCHARGE_EFF
    grid_co2_factor: float = GRID_CO2_FACTOR_KG_PER_KWH
    max_ac_shed_pct: float = MAX_AC_SHED_PCT_NORMAL
    co2_weight: float = CO2_WEIGHT
    battery_cycle_cost: float = BATTERY_CYCLE_COST
    peak_demand_weight: float = PEAK_DEMAND_WEIGHT
    comfort_penalty_weight: float = COMFORT_PENALTY_WEIGHT

    def scale_battery(self, new_capacity_kwh: float) -> "CampusConfig":
        """Scale battery operational bounds proportionally with capacity."""
        ratio = new_capacity_kwh / max(1.0, DEFAULT_BATTERY_CAPACITY_KWH)
        self.battery_capacity_kwh = float(new_capacity_kwh)
        self.battery_min_soc_kwh = round(0.10 * new_capacity_kwh, 2)
        self.battery_max_soc_kwh = round(0.95 * new_capacity_kwh, 2)
        self.battery_initial_soc_kwh = round(0.40 * new_capacity_kwh, 2)
        self.battery_final_soc_kwh = round(0.40 * new_capacity_kwh, 2)
        self.battery_max_charge_kw = round(min(60.0 * ratio, new_capacity_kwh * 0.5), 2)
        self.battery_max_discharge_kw = round(min(60.0 * ratio, new_capacity_kwh * 0.5), 2)
        return self
