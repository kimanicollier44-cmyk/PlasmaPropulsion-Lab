"""Tests for PlasmaPropulsion-Lab: every number checked against analytics."""
import math

import pytest

import main as m


# ---- fundamentals
def test_exhaust_velocity_values():
    assert abs(m.exhaust_velocity_m_s(3100.0) - 30400.615) < 0.01
    assert abs(m.exhaust_velocity_m_s(450.0) - 4412.9925) < 0.01


def test_mass_flow_nstar():
    assert abs(m.mass_flow_kg_s(0.092, 3100.0) - 3.0263e-6) < 0.01 * 3.0263e-6


def test_jet_power_nstar():
    assert abs(m.jet_power_w(0.092, 3100.0) - 1398.4) < 0.01 * 1398.4


def test_jet_power_is_half_thrust_times_ve():
    for t, isp in ((0.092, 3100.0), (0.236, 4100.0), (5.4, 2600.0)):
        assert abs(m.jet_power_w(t, isp)
                   - 0.5 * t * m.exhaust_velocity_m_s(isp)) < 1e-9


def test_ideal_thrust_per_kw_falls_with_isp():
    vals = [m.ideal_thrust_per_kw_mn(i) for i in (450.0, 1600.0, 3100.0, 4100.0)]
    assert vals == sorted(vals, reverse=True)
    assert abs(vals[1] - 127.46) < 0.5
    assert abs(vals[3] - 49.74) < 0.5


def test_invalid_isp_raises():
    with pytest.raises(ValueError):
        m.exhaust_velocity_m_s(0.0)
    with pytest.raises(ValueError):
        m.mass_flow_kg_s(-1.0, 3000.0)


def test_acceleration_next_on_1000kg():
    assert abs(m.acceleration_m_s2(0.236, 1000.0) - 2.36e-4) < 1e-9


# ---- thruster table (labelled published-class)
def test_table_has_four_thrusters():
    assert len(m.thruster_table()) == 4


def test_derived_efficiency_bands():
    tab = {r["name"]: r for r in m.thruster_table()}
    assert 0.58 < tab["NSTAR-class"]["efficiency"] < 0.64
    assert 0.66 < tab["NEXT-class"]["efficiency"] < 0.72
    assert 0.45 < tab["SPT-100-class"]["efficiency"] < 0.51
    assert 0.64 < tab["X3-class"]["efficiency"] < 0.71


def test_all_efficiencies_physical():
    for r in m.thruster_table():
        assert 0.0 < r["efficiency"] < 1.0


def test_thrust_per_kw_ordering():
    tab = {r["name"]: r for r in m.thruster_table()}
    # lowest Isp buys the most thrust per kW - the 2/ve trade
    assert tab["SPT-100-class"]["thrust_per_kw_mn"] > \
        tab["X3-class"]["thrust_per_kw_mn"] > \
        tab["NSTAR-class"]["thrust_per_kw_mn"] > \
        tab["NEXT-class"]["thrust_per_kw_mn"]


def test_thrust_per_kw_values():
    tab = {r["name"]: r for r in m.thruster_table()}
    assert abs(tab["NSTAR-class"]["thrust_per_kw_mn"] - 40.0) < 0.1
    assert abs(tab["NEXT-class"]["thrust_per_kw_mn"] - 34.2) < 0.1
    assert abs(tab["SPT-100-class"]["thrust_per_kw_mn"] - 61.5) < 0.1


def test_actual_tpk_is_eta_times_ideal():
    for r in m.thruster_table():
        assert abs(r["thrust_per_kw_mn"]
                   - r["efficiency"] * r["ideal_thrust_per_kw_mn"]) \
            < 1e-6 * r["ideal_thrust_per_kw_mn"]


def test_x3_mdot_kg_day():
    tab = {r["name"]: r for r in m.thruster_table()}
    assert abs(tab["X3-class"]["mdot_kg_day"] - 18.30) < 0.05


# ---- efficiency chain
def test_chain_reconstructs_nameplate_thrust():
    for r in m.efficiency_table():
        assert abs(r["thrust_from_chain_n"] - r["thrust_n"]) < 1e-12


def test_chain_losses_positive_and_sum():
    for r in m.efficiency_table():
        assert r["lost_power_w"] > 0
        assert abs(r["lost_power_w"] + r["jet_power_w"] - r["power_w"]) < 1e-9


# ---- rocket equation
def test_propellant_fractions_10kms():
    assert abs(m.propellant_fraction(10000.0, 4100.0) - 0.2202) < 0.001
    assert abs(m.propellant_fraction(10000.0, 450.0) - 0.8963) < 0.001


def test_propellant_fraction_edges():
    assert m.propellant_fraction(0.0, 4100.0) == 0.0
    assert m.propellant_fraction(5000.0, 4100.0) \
        < m.propellant_fraction(10000.0, 4100.0) < 1.0


def test_headline_comparison():
    head = m.headline_comparison()
    assert abs(head["ion_propellant_kg"] - 220.19) < 0.05
    assert abs(head["chemical_propellant_kg"] - 896.28) < 0.05
    assert abs(head["propellant_saved_kg"] - 676.08) < 0.1


def test_rocket_equation_roundtrip():
    head = m.headline_comparison()
    dv = m.delta_v_m_s(1000.0, 1000.0 - head["ion_propellant_kg"], 4100.0)
    assert abs(dv - 10000.0) < 1e-6


def test_wet_for_dry_inverts_fraction():
    wet = m.wet_mass_for_dry_kg(779.81, 10000.0, 4100.0)
    assert abs(wet - 1000.0) < 0.5
    assert abs(m.propellant_mass_kg(wet, 10000.0, 4100.0)
               - (wet - 779.81)) < 0.5


def test_delta_v_rejects_bad_masses():
    with pytest.raises(ValueError):
        m.delta_v_m_s(500.0, 1000.0, 4100.0)


# ---- missions (labelled models)
def _missions():
    return {r["mission"]: r for r in m.mission_budgets()}


def test_mars_cruise_budget():
    mars = _missions()["Earth-Mars cruise (labelled model budget)"]
    assert abs(mars["propellant_kg"] - 110.90) < 0.05
    assert abs(mars["burn_time_days"] - 218.68) < 0.05


def test_dawn_tour_budget():
    dawn = _missions()["Dawn-style multi-target tour (labelled model)"]
    assert abs(dawn["propellant_kg"] - 369.79) < 0.05
    assert 3.7 < dawn["burn_time_days"] / m.DAYS_PER_YEAR < 4.1
    assert 5.0 < dawn["dv_per_day_m_s"] < 8.0


def test_cubesat_budget_ion_vs_chemical():
    cube = _missions()["Cubesat station-keeping, per year (labelled model)"]
    assert abs(cube["propellant_kg"] * 1000.0 - 38.18) < 0.05
    assert abs(m.cubesat_chemical_per_year_kg() * 1000.0 - 135.19) < 0.05
    assert cube["propellant_kg"] < m.cubesat_chemical_per_year_kg()


def test_burn_time_zero_thrust_raises():
    with pytest.raises(ValueError):
        m.burn_time_s(10.0, 0.0, 3000.0)


# ---- power system + closure
def test_solar_flux_factor():
    assert m.solar_flux_factor(1.0) == 1.0
    assert abs(m.solar_flux_factor(1.524) - 0.4306) < 0.001
    assert abs(m.solar_flux_factor(2.0) - 0.25) < 1e-12


def test_array_mass():
    assert abs(m.array_mass_kg(6900.0, 100.0) - 69.0) < 1e-9


def test_tug_design_closes():
    tug = m.design_report()["mars_cargo_tug"]
    assert tug["status"] == "CLOSES"
    assert tug["reasons"] == []
    assert abs(tug["wet_kg"] - 527.07) < 0.1
    assert abs(tug["propellant_kg"] - 73.07) < 0.05
    assert abs(tug["array_kg"] - 69.0) < 1e-9


def test_x3_design_refused_with_reasons():
    big = m.design_report()["outer_system_x3_at_mars_distance"]
    assert big["status"] == "REFUSED"
    assert len(big["reasons"]) >= 1
    assert big["wet_kg"] > 3000.0
    assert big["array_kg"] > 2000.0


# ---- launch audit
def test_launch_impossible_for_whole_table():
    la = m.launch_audit()
    assert la["can_launch"] is False
    assert 0.0 < la["best_thrust_to_weight"] < 1e-3
    for row in la["rows"]:
        assert row["thrust_to_weight"] < 1.0


def test_next_thrust_to_weight_value():
    la = m.launch_audit()
    row = [r for r in la["rows"] if r["thruster"] == "NEXT-class"][0]
    assert abs(row["thrust_to_weight"] - 2.4065e-5) < 0.01 * 2.4065e-5


# ---- classifier
def test_classifier_scenarios():
    rep = m.fit_report()
    assert rep["dawn_style_tour"] == "ideal"
    assert rep["mars_cargo_transfer"] == "ideal"
    assert rep["cubesat_station_keeping"] == "workable"
    assert rep["comsat_orbit_raising"] == "workable"
    assert rep["launch_from_surface"] == "wrong-tool"
    assert rep["three_day_lunar_dash"] == "wrong-tool"


def test_classifier_rejects_bad_inputs():
    with pytest.raises(ValueError):
        m.classify_mission(5.0, 0.0, 10.0)


# ---- gates + seats
def test_hold_gates_all_present():
    assert len(m.HOLD_GATES) == 14
    assert all(v.startswith("HOLD") for v in m.HOLD_GATES.values())


def test_claim_gates_hold():
    for action in ("real_spacecraft_operation", "live_thruster_firing",
                   "flight_plan_execution", "launch_capability_claim",
                   "faster_mission_claim", "mission_design_approval_claim"):
        assert m.gate(action) == "HOLD"


def test_sandbox_proceeds():
    assert m.gate("run_simulation") == "PROCEED"


def test_seats_never_override():
    b = m.brains_report()
    assert b["decider"]["can_override_hold"] is False
    assert b["advisor"]["can_override_hold"] is False
    assert b["flow"]["rendered"] is False and b["flow"]["live"] == 0


def test_demo_checks_all_pass():
    checks = m.run_checks()
    assert all(ok for _, ok in checks), [n for n, ok in checks if not ok]


def test_demo_deterministic():
    import io
    import contextlib
    out1, out2 = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out1):
        m.demo()
    with contextlib.redirect_stdout(out2):
        m.demo()
    assert out1.getvalue() == out2.getvalue()
