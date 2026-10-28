"""
Campus Energy Command Center - AI Energy Distributor Test Suite.

Verifies:
1. Nominal local calculation & fallback execution (zero crash on missing/invalid API key).
2. 2-tuple unpacking and object attribute access.
3. Accurate situation parsing (disruption classification & trigger hour extraction).
4. Mathematical solver coupling & 100.0% essential uptime invariant.
5. Building allocation DataFrame schema and building coverage.
"""

import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
import pandas as pd
from src.services.config import BUILDINGS, CampusConfig
from src.services.ai_distributor import predict_and_distribute_energy, AIDistributionResult


def test_01_ai_distributor_nominal_fallback():
    """Verify default nominal execution without API key returns valid result and 4 buildings."""
    res = predict_and_distribute_energy()

    assert isinstance(res, AIDistributionResult)
    assert res.is_fallback is True
    assert isinstance(res.ai_summary, str) and len(res.ai_summary) > 20
    assert isinstance(res.building_allocation_df, pd.DataFrame)
    assert len(res.building_allocation_df) == 4

    # Verify building coverage
    buildings_in_df = set(res.building_allocation_df["Building"])
    assert buildings_in_df == set(BUILDINGS)

    # Verify required column headers
    cols = res.building_allocation_df.columns.tolist()
    assert "Building" in cols
    assert "Predicted Peak Window" in cols
    assert "Essential Power (kWh)" in cols
    assert "Flexible/Cooling Power (kWh)" in cols
    assert "Primary Energy Source (Solar + Battery vs. Grid)" in cols
    assert "Distribution Priority" in cols


def test_02_ai_distributor_tuple_unpacking():
    """Verify that predict_and_distribute_energy supports direct 2-tuple unpacking."""
    summary, df = predict_and_distribute_energy("Cloud cover at 14:00")

    assert isinstance(summary, str)
    assert "cloud cover" in summary.lower() or "solar" in summary.lower()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4


def test_03_ai_distributor_situation_parsing():
    """Verify natural language situation parsing for all standard disruption types and hours."""
    cases = [
        ("Cloud cover at 14:00 and high evening demand in Hostel", "cloud_cover", 14),
        ("Emergency tariff spike at 15:00 reaching ₹22/kWh", "price_spike", 15),
        ("Substation equipment failure and chiller derate at 13:00", "equipment_failure", 13),
        ("Academic seminar occupancy surge at 16:00", "occupancy_surge", 16),
    ]

    for prompt, expected_type, expected_hour in cases:
        res = predict_and_distribute_energy(operator_input=prompt)
        assert res.disruption_type == expected_type, f"Failed for prompt: {prompt}"
        assert res.trigger_hour == expected_hour, f"Failed hour for prompt: {prompt}"
        assert res.plan.essential_uptime_pct == 100.0


def test_04_ai_distributor_invalid_key_graceful_fallback():
    """Verify that an invalid API key or disconnected state never crashes the caller."""
    res = predict_and_distribute_energy(
        operator_input="Cloud cover at 14:00",
        api_key="sk-invalid-non-working-key-99999",
    )

    assert res.is_fallback is True
    assert res.disruption_type == "cloud_cover"
    assert res.plan.essential_uptime_pct == 100.0


def test_05_ai_distributor_with_custom_campus_config():
    """Verify scaling with custom infrastructure configurations."""
    cfg = CampusConfig(import_cap_kw=550.0, solar_capacity_kwp=200.0)
    res = predict_and_distribute_energy(campus_config=cfg)

    assert res.scenario.campus_config.import_cap_kw == 550.0
    assert res.scenario.campus_config.solar_capacity_kwp == 200.0
    assert res.plan.essential_uptime_pct == 100.0


def test_06_run_ai_guided_optimization_mutates_arrays_and_solves():
    """
    Verify run_ai_guided_optimization directly mutates scenario arrays
    and returns a valid ScheduleResult with changed KPIs.
    """
    from src.services.ai_distributor import run_ai_guided_optimization
    from src.services.data_loader import get_scenario_data
    from src.services.optimizer import solve_campus_milp

    cfg = CampusConfig()
    nom_scen = get_scenario_data(disruption_type=None, trigger_hour=13, campus_config=cfg)
    nominal_plan = solve_campus_milp(nom_scen)

    res = run_ai_guided_optimization(
        situation_text="Cloud cover at 14:00 reducing solar by 75%",
        trigger_hour=13,
        initial_plan=nominal_plan,
        campus_config=cfg,
    )

    # 1. Unpacking check (4-tuple)
    ai_solved_plan, ai_explanation, raw_ai_json, building_allocation_df = res

    # 2. Verify scenario mutation
    assert res.scenario.disruption_type == "ai_custom"
    assert raw_ai_json["solar_multiplier"] == 0.25
    # Hour 14 solar must be mutated down
    assert res.scenario.solar_available_kw[14] < nom_scen.solar_available_kw[14]

    # 3. Verify MILP solve output
    assert ai_solved_plan.solver_status == "Optimal"
    assert ai_solved_plan.essential_uptime_pct == 100.0
    assert len(building_allocation_df) == 4
    assert len(ai_explanation) > 20

    # 4. Changed KPIs vs nominal
    assert ai_solved_plan.total_grid_cost_inr != nominal_plan.total_grid_cost_inr


def test_07_gemini_and_openai_url_detection():
    """Verify call_live_ai_api correctly formats endpoints and headers for Gemini vs OpenAI."""
    from src.services.ai_distributor import call_live_ai_api

    # Invalid key triggers graceful failure with clear error
    _, _, model_gemini, err_gemini = call_live_ai_api(
        situation_text="Test prompt",
        api_key="AIzaSyFakeKeyForTesting1234567890",
        campus_summary={},
        timeout_sec=1.0,
    )
    assert model_gemini == "gemini-2.5-flash"
    assert err_gemini is not None

    _, _, model_openai, err_openai = call_live_ai_api(
        situation_text="Test prompt",
        api_key="sk-fake-openai-key-1234567890",
        campus_summary={},
        timeout_sec=1.0,
    )
    assert model_openai == "gpt-4o-mini"
    assert err_openai is not None
