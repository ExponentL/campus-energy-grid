"""
Campus Energy Command Center - Data Loader and Disruption Scenario Engine.

Loads cached timetable and solar weather datasets, and mutates forecast feeds
for real-time rolling-horizon re-optimization under grid and operational disruptions.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.services.config import (
    BUILDINGS,
    DEFAULT_CAMPUS_IMPORT_CAP_KW,
    DEFAULT_SOLAR_CAPACITY_KWP,
    DEFAULT_TARIFF_INR,
    EV_DEADLINE_HOUR,
    EV_MAX_KW,
    EV_START_HOUR,
    EV_TOTAL_KWH,
    MAX_AC_SHED_PCT_EMERGENCY,
    MAX_AC_SHED_PCT_NORMAL,
    WH_EVE_END_HOUR,
    WH_EVE_MAX_KW,
    WH_EVE_START_HOUR,
    WH_EVE_TOTAL_KWH,
    WH_MORN_END_HOUR,
    WH_MORN_MAX_KW,
    WH_MORN_START_HOUR,
    WH_MORN_TOTAL_KWH,
    CampusConfig,
)

# Friendly display names for scenarios
SCENARIO_NAMES: Dict[Optional[str], str] = {
    None: "Nominal Forecast",
    "cloud_cover": "Sudden Cloud Cover (-75% Solar)",
    "price_spike": "Grid Tariff Surge (₹22/kWh)",
    "equipment_failure": "Lab Chiller / Transformer Derate (-25% Cap)",
    "occupancy_surge": "Auditorium & Seminar Surge (+85 kW AC)",
}


@dataclass
class ScenarioData:
    """Complete 24-hour operational and environmental inputs for microgrid solvers."""
    disruption_type: Optional[str]
    trigger_hour: int
    hours: List[int]
    buildings: List[str]
    tariff_inr: Dict[int, float]
    import_cap_kw: Dict[int, float]
    solar_available_kw: Dict[int, float]
    ambient_temp_c: Dict[int, float]
    cloud_cover_pct: Dict[int, float]
    occupancy: Dict[Tuple[str, int], int]
    essential_kw: Dict[Tuple[str, int], float]
    ac_nominal_kw: Dict[Tuple[str, int], float]
    max_ac_shed_pct: float
    campus_config: CampusConfig
    timetable_df: pd.DataFrame
    solar_df: pd.DataFrame


def load_raw_data(data_dir: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load cached timetable and solar-weather dataframes from disk."""
    if data_dir is None:
        data_dir = Path(__file__).resolve().parent.parent.parent / "data"

    timetable_path = data_dir / "timetable.csv"
    solar_path = data_dir / "solar_weather_cache.csv"

    if not timetable_path.exists() or not solar_path.exists():
        # Auto-generate if missing
        from scripts.generate_data import generate_solar_weather_cache, generate_timetable
        data_dir.mkdir(parents=True, exist_ok=True)
        generate_timetable(data_dir)
        generate_solar_weather_cache(data_dir)

    df_timetable = pd.read_csv(timetable_path)
    df_solar = pd.read_csv(solar_path)
    return df_timetable, df_solar


def get_scenario_data(
    disruption_type: Optional[str] = None,
    trigger_hour: int = 13,
    campus_config: Optional[CampusConfig] = None,
    data_dir: Optional[Path] = None,
) -> ScenarioData:
    """
    Construct 24-hour scenario inputs, applying disruption mutations if active.

    Supported disruptions:
    - None: Nominal forecast
    - 'cloud_cover': Cloud cover jumps to 92%, solar drops by 75% (hours 13:00 to 16:00)
    - 'price_spike': Grid tariff spikes to ₹22.0/kWh (hours 14:00 to 18:00)
    - 'equipment_failure': Campus import cap drops 25% (480 -> 360 kW) and Lab AC cooling
      requires +25 kW auxiliary fan power (hours 13:00 to 19:00)
    - 'occupancy_surge': Academic & Library occupancy surges +180%, increasing AC by +85 kW
      (hours 14:00 to 18:00)
    """
    if campus_config is None:
        campus_config = CampusConfig()

    df_timetable, df_solar = load_raw_data(data_dir)
    hours = list(range(24))

    # Base arrays
    solar_ratio = campus_config.solar_capacity_kwp / DEFAULT_SOLAR_CAPACITY_KWP
    tariff_inr: Dict[int, float] = {h: float(DEFAULT_TARIFF_INR[h]) for h in hours}
    import_cap_kw: Dict[int, float] = {h: float(campus_config.import_cap_kw) for h in hours}
    solar_available_kw: Dict[int, float] = {
        int(row["hour"]): float(row["solar_kw_available"]) * solar_ratio
        for _, row in df_solar.iterrows()
    }
    ambient_temp_c: Dict[int, float] = {
        int(row["hour"]): float(row["ambient_temp_c"]) for _, row in df_solar.iterrows()
    }
    cloud_cover_pct: Dict[int, float] = {
        int(row["hour"]): float(row["cloud_cover_pct"]) for _, row in df_solar.iterrows()
    }

    occupancy: Dict[Tuple[str, int], int] = {}
    essential_kw: Dict[Tuple[str, int], float] = {}
    ac_nominal_kw: Dict[Tuple[str, int], float] = {}

    for _, row in df_timetable.iterrows():
        h = int(row["hour"])
        for b in BUILDINGS:
            occ_col = f"{b}_occ"
            ess_col = f"{b}_essential_kw"
            ac_col = f"{b}_ac_nominal_kw"
            occupancy[(b, h)] = int(row[occ_col])
            essential_kw[(b, h)] = float(row[ess_col])
            ac_nominal_kw[(b, h)] = float(row[ac_col])

    max_ac_shed_pct = MAX_AC_SHED_PCT_NORMAL

    # Apply Disruption Mutations
    if disruption_type == "cloud_cover":
        # Between hours 13:00 and 16:00, cloud cover jumps to 92%, solar drops by 75%
        for h in range(13, 17):
            cloud_cover_pct[h] = 92.0
            solar_available_kw[h] = round(solar_available_kw[h] * 0.25, 2)

    elif disruption_type == "price_spike":
        # Between hours 14:00 and 18:00, grid emergency tariff spikes to ₹22.0 / kWh
        for h in range(14, 19):
            tariff_inr[h] = 22.0

    elif disruption_type == "equipment_failure":
        # Between hours 13:00 and 19:00, Campus Grid Import Cap drops by 25%
        # AND Lab cooling requires an extra 25 kW backup fan power
        for h in range(13, 20):
            import_cap_kw[h] = round(campus_config.import_cap_kw * 0.75, 2)
            ac_nominal_kw[("Lab", h)] = round(ac_nominal_kw[("Lab", h)] + 25.0, 2)
        max_ac_shed_pct = MAX_AC_SHED_PCT_EMERGENCY

    elif disruption_type == "occupancy_surge":
        # Between hours 14:00 and 18:00, Academic and Library_Admin occupancy surges +180%
        # increasing AC nominal demand by +85 kW total (+55 kW Academic, +30 kW Library)
        for h in range(14, 19):
            occupancy[("Academic", h)] = int(occupancy[("Academic", h)] * 2.8)
            occupancy[("Library_Admin", h)] = int(occupancy[("Library_Admin", h)] * 2.8)
            ac_nominal_kw[("Academic", h)] = round(ac_nominal_kw[("Academic", h)] + 55.0, 2)
            ac_nominal_kw[("Library_Admin", h)] = round(ac_nominal_kw[("Library_Admin", h)] + 30.0, 2)

    return ScenarioData(
        disruption_type=disruption_type,
        trigger_hour=trigger_hour,
        hours=hours,
        buildings=BUILDINGS,
        tariff_inr=tariff_inr,
        import_cap_kw=import_cap_kw,
        solar_available_kw=solar_available_kw,
        ambient_temp_c=ambient_temp_c,
        cloud_cover_pct=cloud_cover_pct,
        occupancy=occupancy,
        essential_kw=essential_kw,
        ac_nominal_kw=ac_nominal_kw,
        max_ac_shed_pct=max_ac_shed_pct,
        campus_config=campus_config,
        timetable_df=df_timetable,
        solar_df=df_solar,
    )

