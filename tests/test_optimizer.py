"""
Campus Energy Command Center - Automated Optimization Verification Test Suite.

Verifies:
1. Nominal economic and peak reduction (Optimized cost & peak strictly lower than Baseline).
2. Essential uptime invariant (100.0% locked uptime across all disruption scenarios).
3. Rolling-horizon state locking (Hours 0..12 strictly identical after re-optimization).
4. Re-optimization performance latency (< 2.0s solve time across all disruptions).
5. Battery operational boundaries (SOC strictly within [20.0, 190.0] kWh at all hours).
"""

import sys
import time
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pytest

from src.services.baseline import compute_baseline_schedule
from src.services.config import CampusConfig
from src.services.data_loader import get_scenario_data
from src.services.optimizer import reoptimize, solve_campus_milp


@pytest.fixture
def default_config():
    """Default campus microgrid configuration."""
    return CampusConfig()


@pytest.fixture
def nominal_scenario(default_config):
    """Clean 24-hour nominal scenario without disruptions."""
    return get_scenario_data(
        disruption_type=None,
        trigger_hour=13,
        campus_config=default_config,
    )


@pytest.fixture
def initial_nominal_plan(nominal_scenario):
    """Initial solved optimal dispatch schedule under nominal forecast."""
    return solve_campus_milp(nominal_scenario)


def test_01_baseline_vs_optimized_cost_and_peak(nominal_scenario, initial_nominal_plan):
    """
    Test 1: Verify that the MILP optimizer achieves strictly lower 24h electricity cost (INR)
    and strictly lower peak grid import (kW) than the uncoordinated baseline under nominal forecast.
    """
    baseline = compute_baseline_schedule(nominal_scenario)

    # 1. Cost verification: Optimized must be strictly lower than baseline
    cost_saving_inr = baseline.total_grid_cost_inr - initial_nominal_plan.total_grid_cost_inr
    cost_saving_pct = (cost_saving_inr / baseline.total_grid_cost_inr) * 100.0

    assert initial_nominal_plan.total_grid_cost_inr < baseline.total_grid_cost_inr, (
        f"Optimized cost (₹{initial_nominal_plan.total_grid_cost_inr}) is not strictly lower "
        f"than baseline (₹{baseline.total_grid_cost_inr})"
    )
    assert cost_saving_pct >= 14.0, (
        f"Cost saving percentage ({cost_saving_pct:.2f}%) should be >= 14.0%"
    )

    # 2. Peak demand verification: Optimized peak kW must be strictly lower than baseline peak kW
    assert initial_nominal_plan.peak_import_kw < baseline.peak_import_kw, (
        f"Optimized peak import ({initial_nominal_plan.peak_import_kw} kW) must be lower "
        f"than baseline peak ({baseline.peak_import_kw} kW)"
    )

    # 3. Solver status must be OPTIMAL
    assert initial_nominal_plan.solver_status == "Optimal" or "Optimal" in initial_nominal_plan.solver_status


def test_02_essential_uptime_invariant_across_all_scenarios(default_config):
    """
    Test 2: Verify that essential service uptime (Tier 4) is mathematically locked
    at exactly 100.0% under nominal operations and all 4 disruption scenarios.
    """
    scenarios_to_test = [
        None,
        "cloud_cover",
        "price_spike",
        "equipment_failure",
        "occupancy_surge",
    ]

    for dtype in scenarios_to_test:
        scen = get_scenario_data(disruption_type=dtype, trigger_hour=13, campus_config=default_config)
        plan = solve_campus_milp(scen)

        assert plan.essential_uptime_pct == 100.0, (
            f"Essential uptime breached under scenario '{dtype}': {plan.essential_uptime_pct}%"
        )

        # Confirm each building essential load matches 100% demanded
        for b in scen.buildings:
            for t in scen.hours:
                demanded = scen.essential_kw[(b, t)]
                served = plan.essential_kw_by_bldg[b][t]
                assert abs(demanded - served) < 1e-4, (
                    f"Essential load mismatch for {b} at hour {t}: demanded={demanded}, served={served}"
                )


def test_03_rolling_horizon_past_hours_frozen(nominal_scenario, initial_nominal_plan, default_config):
    """
    Test 3: Verify rolling-horizon re-optimization at trigger_hour = 13.
    Hours 0..12 must remain strictly identical to initial_nominal_plan (np.allclose).
    """
    trigger_hour = 13
    disruptions = ["cloud_cover", "price_spike", "equipment_failure", "occupancy_surge"]

    for dtype in disruptions:
        reopt_plan, explanation = reoptimize(
            current_hour=trigger_hour,
            disruption_type=dtype,
            initial_plan=initial_nominal_plan,
            campus_config=default_config,
        )

        # Check all past hours t in 0..12
        past_hours = range(trigger_hour)
        for t in past_hours:
            assert np.isclose(reopt_plan.grid_import[t], initial_nominal_plan.grid_import[t], atol=1e-2), (
                f"grid_import not frozen at t={t} for {dtype}"
            )
            assert np.isclose(reopt_plan.solar_used[t], initial_nominal_plan.solar_used[t], atol=1e-2), (
                f"solar_used not frozen at t={t} for {dtype}"
            )
            assert np.isclose(reopt_plan.batt_charge[t], initial_nominal_plan.batt_charge[t], atol=1e-2), (
                f"batt_charge not frozen at t={t} for {dtype}"
            )
            assert np.isclose(reopt_plan.batt_discharge[t], initial_nominal_plan.batt_discharge[t], atol=1e-2), (
                f"batt_discharge not frozen at t={t} for {dtype}"
            )
            assert np.isclose(reopt_plan.batt_soc[t], initial_nominal_plan.batt_soc[t], atol=1e-2), (
                f"batt_soc not frozen at t={t} for {dtype}"
            )
            assert np.isclose(reopt_plan.ev_kw[t], initial_nominal_plan.ev_kw[t], atol=1e-2), (
                f"ev_kw not frozen at t={t} for {dtype}"
            )
            assert np.isclose(reopt_plan.wh_morn_kw[t], initial_nominal_plan.wh_morn_kw[t], atol=1e-2), (
                f"wh_morn_kw not frozen at t={t} for {dtype}"
            )
            assert np.isclose(reopt_plan.wh_eve_kw[t], initial_nominal_plan.wh_eve_kw[t], atol=1e-2), (
                f"wh_eve_kw not frozen at t={t} for {dtype}"
            )

            for b in nominal_scenario.buildings:
                assert np.isclose(
                    reopt_plan.ac_used_kw_by_bldg[b][t],
                    initial_nominal_plan.ac_used_kw_by_bldg[b][t],
                    atol=1e-2,
                ), f"ac_used for {b} not frozen at t={t} for {dtype}"

        # Verify explanation string is non-empty and contains exact numbers
        assert "DISRUPTION RESPONSE" in explanation
        assert f"{trigger_hour}:00" in explanation


def test_04_reoptimization_solve_time_under_two_seconds(nominal_scenario, initial_nominal_plan, default_config):
    """
    Test 4: Verify that the MILP rolling re-optimization solves strictly under 2.0 seconds
    (typically ~0.04-0.10s) across all 4 disruption scenarios.
    """
    trigger_hour = 13
    disruptions = ["cloud_cover", "price_spike", "equipment_failure", "occupancy_surge"]

    for dtype in disruptions:
        t_start = time.perf_counter()
        reopt_plan, _ = reoptimize(
            current_hour=trigger_hour,
            disruption_type=dtype,
            initial_plan=initial_nominal_plan,
            campus_config=default_config,
        )
        wall_time = time.perf_counter() - t_start

        # Wall-clock must be strictly < 2.0 seconds
        assert wall_time < 2.0, f"Re-optimization wall-clock time ({wall_time:.3f}s) exceeded 2.0s for {dtype}"
        assert reopt_plan.solve_time_sec < 2.0, (
            f"Solver reported latency ({reopt_plan.solve_time_sec:.3f}s) exceeded 2.0s for {dtype}"
        )


def test_05_battery_soc_bounds_strictly_enforced(default_config):
    """
    Test 5: Verify that shared BESS state of charge remains strictly within [20.0, 190.0] kWh
    at all 24 hours across nominal and all disruption scenarios, and satisfies the final target.
    """
    scenarios = [None, "cloud_cover", "price_spike", "equipment_failure", "occupancy_surge"]

    min_soc = default_config.battery_min_soc_kwh  # 20.0
    max_soc = default_config.battery_max_soc_kwh  # 190.0
    final_target = default_config.battery_final_soc_kwh  # 80.0

    for dtype in scenarios:
        scen = get_scenario_data(disruption_type=dtype, trigger_hour=13, campus_config=default_config)
        plan = solve_campus_milp(scen)

        for t, soc in enumerate(plan.batt_soc):
            assert soc >= (min_soc - 1e-2), (
                f"Battery SOC ({soc:.2f} kWh) fell below min limit ({min_soc} kWh) at hour {t} in {dtype}"
            )
            assert soc <= (max_soc + 1e-2), (
                f"Battery SOC ({soc:.2f} kWh) exceeded max limit ({max_soc} kWh) at hour {t} in {dtype}"
            )

        # Final hour SOC boundary check
        final_soc = plan.batt_soc[23]
        assert final_soc >= (final_target - 1e-2), (
            f"Final hour 23 SOC ({final_soc:.2f} kWh) below final target ({final_target} kWh) in {dtype}"
        )
