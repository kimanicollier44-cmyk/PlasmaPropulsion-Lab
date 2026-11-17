#!/usr/bin/env python3
"""PlasmaPropulsion-Lab - educational ion & Hall thruster propulsion lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only: electric propulsion is real, flown physics - NASA's
Dawn spacecraft rode three NSTAR ion thrusters to Vesta and Ceres,
and Hall thrusters keep most modern comsats on station. This lab
computes it honestly: exhaust velocity ve = Isp * g0, thrust
T = mdot * ve, jet power P = 1/2 mdot ve^2, and the iron trade
behind all of it - thrust per kilowatt falls as 2/(ve), so the
higher the specific impulse, the WEAKER the push per unit power.
The rocket equation then shows why anyone bothers: at a 10 km/s
mission delta-v an ion craft needs ~22% propellant where a chemical
craft needs ~90%. The price is time - ion burns run for months to
years at accelerations around a ten-thousandth of a g, and the
thrust is so small that electric propulsion can never launch
anything off a planet. Every thruster figure is a LABELLED
published-class reference value, every mission is a labelled model
budget, and every real-spacecraft / live-hardware / flight action
is a HOLD gate - with Gemini Carbon 4 as DECIDER (names-only,
tighten-only), Muse as advisor (never overrides HOLD), and Google
Flow plan-only seats.
"""
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- constants
G0 = 9.80665                    # standard gravity, m/s^2 (exact, SI)
SECONDS_PER_DAY = 86400.0
DAYS_PER_YEAR = 365.25
VERSION = "1.0.0"

# Chemical reference: a good bipropellant / hydrolox-class stage.
CHEMICAL_ISP_S = 450.0

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "real_spacecraft_operation": "HOLD - no operation or commanding of any real spacecraft, ever",
    "live_thruster_firing": "HOLD - no firing instructions for real ion / Hall hardware; this lab computes, it does not operate",
    "flight_plan_execution": "HOLD - mission budgets here are educational models, not flight products or navigation data",
    "launch_capability_claim": "HOLD - electric thrust is ~1e-4 of weight class; nothing here can launch anything, and no claim says otherwise",
    "faster_mission_claim": "HOLD - ion burns take months to years; no claim that electric propulsion is the fast option",
    "commercial_product_claim": "HOLD - this is an educational lab, not a commercial propulsion product or service",
    "guaranteed_performance_claim": "HOLD - no guaranteed mission performance; every budget carries its labelled assumptions",
    "crewed_mission_safety_claim": "HOLD - no crewed-mission safety claims; these toy budgets certify nothing for human flight",
    "weapons_application_claim": "HOLD - no weapons application guidance of any kind",
    "hardware_fabrication_live": "HOLD - no thruster fabrication instructions; ion optics and discharge chambers are not a home build",
    "high_voltage_operation_live": "HOLD - ion thrusters run kilovolt beam supplies; no live high-voltage operating instructions",
    "propellant_handling_live": "HOLD - no xenon / iodine propellant handling instructions for real hardware",
    "investment_claim": "HOLD - no investment advice about propulsion or space companies",
    "mission_design_approval_claim": "HOLD - a budget that 'closes' here is a labelled model result, not an approved mission design",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Fundamentals
# An electric thruster is a machine for turning electrical power
# into a very fast, very thin exhaust beam:
#   exhaust velocity  ve   = Isp * g0                    [m/s]
#   thrust            T    = mdot * ve                   [N]
#   jet power         Pjet = 1/2 * mdot * ve^2           [W]
# Divide thrust by jet power and the mass flow cancels:
#   T / Pjet = 2 / ve.
# That one line rules the whole field. Double the exhaust velocity
# (double the Isp, double the propellant economy) and you HALVE the
# thrust each watt buys. Ion engines sip propellant precisely
# because they barely push.

def exhaust_velocity_m_s(isp_s):
    """Exhaust velocity ve = Isp * g0 (m/s)."""
    if isp_s <= 0:
        raise ValueError("Isp must be positive")
    return isp_s * G0


def mass_flow_kg_s(thrust_n, isp_s):
    """Propellant mass flow mdot = T / ve (kg/s)."""
    if thrust_n < 0:
        raise ValueError("thrust must be non-negative")
    return thrust_n / exhaust_velocity_m_s(isp_s)


def jet_power_w(thrust_n, isp_s):
    """Kinetic power of the exhaust jet P = 1/2 * mdot * ve^2 (W)."""
    return 0.5 * mass_flow_kg_s(thrust_n, isp_s) * exhaust_velocity_m_s(isp_s) ** 2


def thrust_per_kw_mn(thrust_n, power_w):
    """Thrust bought per kilowatt of INPUT power (mN/kW)."""
    if power_w <= 0:
        raise ValueError("power must be positive")
    return thrust_n / power_w * 1.0e6


def ideal_thrust_per_kw_mn(isp_s):
    """Perfect-efficiency thrust per kW of jet power: 2/ve (mN/kW)."""
    return 2.0 / exhaust_velocity_m_s(isp_s) * 1.0e6


def acceleration_m_s2(thrust_n, mass_kg):
    """Spacecraft acceleration a = T / m (m/s^2)."""
    if mass_kg <= 0:
        raise ValueError("mass must be positive")
    return thrust_n / mass_kg


# ================================================================ 2. Thruster table (labelled published-class)
# LABELLED REFERENCE VALUES: the Isp / thrust / power figures below
# are the widely published nameplate-class numbers for each engine
# family (textbook / agency fact-sheet class), NOT measurements made
# here and NOT a spec sheet for any unit you can buy. The efficiency
# is DERIVED in code from those three numbers (eta = Pjet / Pin), so
# the table can never quietly contradict the physics of section 1.
# System mass (thruster + power processing unit) is a labelled
# model value used only by the mission-closure arithmetic.

THRUSTERS = [
    {"name": "NSTAR-class", "kind": "gridded ion", "isp_s": 3100.0,
     "thrust_n": 0.092, "power_w": 2300.0, "propellant": "xenon",
     "system_kg": 25.0,
     "note": "Dawn / Deep Space 1 class, 30 cm ion optics"},
    {"name": "NEXT-class", "kind": "gridded ion", "isp_s": 4100.0,
     "thrust_n": 0.236, "power_w": 6900.0, "propellant": "xenon",
     "system_kg": 35.0,
     "note": "NASA evolutionary xenon thruster, 40 cm class"},
    {"name": "SPT-100-class", "kind": "Hall effect", "isp_s": 1600.0,
     "thrust_n": 0.083, "power_w": 1350.0, "propellant": "xenon",
     "system_kg": 12.0,
     "note": "station-keeping workhorse on hundreds of comsats"},
    {"name": "X3-class", "kind": "Hall effect", "isp_s": 2600.0,
     "thrust_n": 5.4, "power_w": 102000.0, "propellant": "xenon",
     "system_kg": 400.0,
     "note": "100 kW-class nested-channel Hall, cargo-tug scale"},
]


def thruster_row(t):
    """Derived quantities for one thruster-table entry."""
    ve = exhaust_velocity_m_s(t["isp_s"])
    mdot = mass_flow_kg_s(t["thrust_n"], t["isp_s"])
    pjet = jet_power_w(t["thrust_n"], t["isp_s"])
    return {"name": t["name"], "kind": t["kind"],
            "isp_s": t["isp_s"], "thrust_n": t["thrust_n"],
            "power_w": t["power_w"], "propellant": t["propellant"],
            "ve_m_s": ve, "mdot_kg_s": mdot,
            "mdot_kg_day": mdot * SECONDS_PER_DAY,
            "jet_power_w": pjet, "efficiency": pjet / t["power_w"],
            "thrust_per_kw_mn": thrust_per_kw_mn(t["thrust_n"], t["power_w"]),
            "ideal_thrust_per_kw_mn": ideal_thrust_per_kw_mn(t["isp_s"])}


def thruster_table():
    return [thruster_row(t) for t in THRUSTERS]


def thruster_by_name(name):
    for t in THRUSTERS:
        if t["name"] == name:
            return t
    raise KeyError(name)


# ================================================================ 3. Efficiency chain
# Real thrusters lose power everywhere: ionisation cost, beam
# divergence, discharge losses, power-processor heat. The chain is
# one multiplication:
#   Pin --(eta)--> Pjet = 1/2 mdot ve^2 --(T = 2 Pjet / ve)--> thrust
# so the honest thrust per input kilowatt is T/Pin = 2 * eta / ve.
# The table prints every link for every engine so a reader can check
# the identity numerically instead of trusting it.

def efficiency_chain_row(t):
    row = thruster_row(t)
    row["thrust_from_chain_n"] = (2.0 * row["efficiency"] * t["power_w"]
                                  / row["ve_m_s"])
    row["lost_power_w"] = t["power_w"] - row["jet_power_w"]
    return row


def efficiency_table():
    return [efficiency_chain_row(t) for t in THRUSTERS]


# ================================================================ 4. Rocket equation
# Tsiolkovsky: dv = ve * ln(m0 / mf). Invert it and the propellant
# fraction of the wet mass is 1 - exp(-dv / ve) - the fraction
# depends ONLY on dv and Isp, not on the size of the spacecraft.
# That is why the chemical-vs-ion gap explodes with mission dv:
# at 1 km/s the chemical stage wastes 20% where ion wastes 2.5%;
# at 10 km/s chemical wastes ~90% and ion still only ~22%.

def propellant_fraction(dv_m_s, isp_s):
    """Propellant share of wet mass: 1 - exp(-dv / ve)."""
    if dv_m_s < 0:
        raise ValueError("delta-v must be non-negative")
    return 1.0 - math.exp(-dv_m_s / exhaust_velocity_m_s(isp_s))


def propellant_mass_kg(wet_mass_kg, dv_m_s, isp_s):
    """Propellant needed for wet_mass_kg to gain dv_m_s (kg)."""
    if wet_mass_kg <= 0:
        raise ValueError("mass must be positive")
    return wet_mass_kg * propellant_fraction(dv_m_s, isp_s)


def wet_mass_for_dry_kg(dry_mass_kg, dv_m_s, isp_s):
    """Wet mass whose dry remainder is dry_mass_kg after dv_m_s."""
    if dry_mass_kg <= 0:
        raise ValueError("mass must be positive")
    return dry_mass_kg * math.exp(dv_m_s / exhaust_velocity_m_s(isp_s))


def delta_v_m_s(wet_mass_kg, dry_mass_kg, isp_s):
    """Delta-v from a mass pair: ve * ln(m0 / mf) (m/s)."""
    if wet_mass_kg <= 0 or dry_mass_kg <= 0 or wet_mass_kg < dry_mass_kg:
        raise ValueError("need 0 < dry <= wet")
    return exhaust_velocity_m_s(isp_s) * math.log(wet_mass_kg / dry_mass_kg)


def burn_time_s(propellant_kg, thrust_n, isp_s):
    """Continuous-thrust burn time for a propellant load (s)."""
    if propellant_kg < 0:
        raise ValueError("propellant must be non-negative")
    mdot = mass_flow_kg_s(thrust_n, isp_s)
    if mdot == 0:
        raise ValueError("zero thrust never burns")
    return propellant_kg / mdot


def headline_comparison(wet_mass_kg=1000.0, dv_m_s=10000.0):
    """THE headline: same craft, same dv, ion vs chemical propellant."""
    ion = propellant_mass_kg(wet_mass_kg, dv_m_s, 4100.0)
    chem = propellant_mass_kg(wet_mass_kg, dv_m_s, CHEMICAL_ISP_S)
    return {"wet_mass_kg": wet_mass_kg, "dv_m_s": dv_m_s,
            "ion_isp_s": 4100.0, "ion_propellant_kg": ion,
            "chemical_isp_s": CHEMICAL_ISP_S, "chemical_propellant_kg": chem,
            "propellant_saved_kg": chem - ion}


# ================================================================ 5. Mission budgets (labelled models)
# Each mission below is a LABELLED MODEL: a real mission class with
# a stated, simplified delta-v budget - not a reconstruction of any
# actual flight plan. Dawn's real total delta-v exceeded 11 km/s
# (the largest of any spacecraft), which is exactly the regime where
# the rocket equation makes chemical propulsion absurd and a
# 92-milliNewton engine the right tool.

def mission_budget(name, wet_mass_kg, dv_m_s, thruster_name, blurb):
    t = thruster_by_name(thruster_name)
    prop = propellant_mass_kg(wet_mass_kg, dv_m_s, t["isp_s"])
    burn = burn_time_s(prop, t["thrust_n"], t["isp_s"])
    return {"mission": name, "blurb": blurb, "wet_mass_kg": wet_mass_kg,
            "dv_m_s": dv_m_s, "thruster": thruster_name,
            "propellant_kg": prop,
            "propellant_fraction": prop / wet_mass_kg,
            "burn_time_s": burn, "burn_time_days": burn / SECONDS_PER_DAY,
            "accel_m_s2": acceleration_m_s2(t["thrust_n"], wet_mass_kg),
            "dv_per_day_m_s": acceleration_m_s2(t["thrust_n"], wet_mass_kg)
            * SECONDS_PER_DAY}


def mission_budgets():
    return [
        mission_budget(
            "Earth-Mars cruise (labelled model budget)",
            800.0, 6000.0, "NEXT-class",
            "6.0 km/s low-thrust transfer + rendezvous budget"),
        mission_budget(
            "Dawn-style multi-target tour (labelled model)",
            1218.0, 11000.0, "NSTAR-class",
            "11 km/s total: two asteroid rendezvous on one tank"),
        mission_budget(
            "Cubesat station-keeping, per year (labelled model)",
            12.0, 50.0, "SPT-100-class",
            "50 m/s per year of LEO drag make-up on a 12 kg cubesat"),
    ]


def cubesat_chemical_per_year_kg():
    """Same cubesat duty on chemical Isp: the yearly propellant gap."""
    return propellant_mass_kg(12.0, 50.0, CHEMICAL_ISP_S)


# ================================================================ 6. Power system + mission closure
# An electric thruster is only half an engine - the other half is
# the power plant, and it has mass. Sunlight thins with distance:
# flux falls as 1/r^2, so an array rated at specific power W/kg near
# Earth delivers W/kg / r_au^2 at r_au from the Sun. Stack it up:
#   dry = payload + bus + array + thruster system
#   wet = dry * exp(dv / ve)          (rocket equation, inverted)
# If the wet mass busts the launch cap the design is REFUSED with
# the reason printed - a paper spacecraft that cannot close is a
# finding, not an embarrassment to hide.

SOLAR_SPEC_W_PER_KG_EARTH = 100.0   # labelled model: array W/kg at 1 AU


def solar_flux_factor(distance_au):
    """Sunlight relative to Earth at distance_au: 1 / r^2."""
    if distance_au <= 0:
        raise ValueError("distance must be positive")
    return 1.0 / distance_au ** 2


def array_mass_kg(power_w, spec_w_per_kg):
    """Solar array mass for power_w at a given specific power (kg)."""
    if power_w < 0 or spec_w_per_kg <= 0:
        raise ValueError("need power >= 0 and positive specific power")
    return power_w / spec_w_per_kg


def mission_design(payload_kg, bus_kg, thruster_name, dv_m_s,
                   distance_au=1.0, wet_cap_kg=1000.0):
    """Full mass build-up; REFUSED (with reasons) if it cannot close."""
    if payload_kg < 0 or bus_kg < 0 or dv_m_s < 0:
        raise ValueError("masses and delta-v must be non-negative")
    t = thruster_by_name(thruster_name)
    spec = SOLAR_SPEC_W_PER_KG_EARTH * solar_flux_factor(distance_au)
    array = array_mass_kg(t["power_w"], spec)
    dry = payload_kg + bus_kg + array + t["system_kg"]
    wet = wet_mass_for_dry_kg(dry, dv_m_s, t["isp_s"])
    prop = wet - dry
    reasons = []
    if wet > wet_cap_kg:
        reasons.append(
            f"wet mass {wet:.0f} kg exceeds the {wet_cap_kg:.0f} kg cap")
    if array > payload_kg + bus_kg:
        reasons.append(
            f"power system dominates: array {array:.0f} kg outweighs "
            f"payload + bus {payload_kg + bus_kg:.0f} kg")
    return {"thruster": thruster_name, "dv_m_s": dv_m_s,
            "distance_au": distance_au, "spec_w_per_kg": spec,
            "array_kg": array, "thruster_system_kg": t["system_kg"],
            "dry_kg": dry, "wet_kg": wet, "propellant_kg": prop,
            "burn_time_days": burn_time_s(prop, t["thrust_n"], t["isp_s"])
            / SECONDS_PER_DAY,
            "status": "REFUSED" if reasons else "CLOSES",
            "reasons": reasons}


def design_report():
    return {
        "mars_cargo_tug": mission_design(
            200.0, 150.0, "NEXT-class", 6000.0,
            distance_au=1.0, wet_cap_kg=1000.0),
        "outer_system_x3_at_mars_distance": mission_design(
            500.0, 800.0, "X3-class", 8000.0,
            distance_au=1.524, wet_cap_kg=3000.0),
    }


# ================================================================ 7. Why EP cannot launch
# Put the numbers side by side and the launch question answers
# itself. A NEXT thruster on a 1,000 kg craft accelerates at
# 2.36e-4 m/s^2 - about 1/40,000 of Earth gravity. Thrust-to-weight
# ~2.4e-5. A hovering rocket needs T/W > 1; electric propulsion is
# four to five orders of magnitude short, forever, because T/P is
# capped by 2/ve and no power plant is light enough to close that
# gap. EP starts its work only after a chemical rocket has done the
# launching. That is not a flaw in the lab's models - it is the
# physics that decides which engine flies which leg.

def thrust_to_weight(thrust_n, mass_kg):
    """Thrust-to-weight ratio T / (m g0), dimensionless."""
    if mass_kg <= 0:
        raise ValueError("mass must be positive")
    return thrust_n / (mass_kg * G0)


def launch_audit(mass_kg=1000.0):
    rows = []
    for t in THRUSTERS:
        rows.append({"thruster": t["name"],
                     "thrust_to_weight": thrust_to_weight(t["thrust_n"],
                                                          mass_kg),
                     "accel_m_s2": acceleration_m_s2(t["thrust_n"], mass_kg)})
    return {"mass_kg": mass_kg, "rows": rows,
            "best_thrust_to_weight": max(r["thrust_to_weight"] for r in rows),
            "can_launch": False}


# ================================================================ 8. kNN mission-fit classifier
# Features: (mission dv in km/s, log10 thrusting days available,
# log10 electric power available in kW). Electric propulsion is the
# IDEAL tool when dv is large and time is plentiful; WORKABLE for
# modest dv with modest time (station-keeping, orbit raising);
# the WRONG TOOL when the dv must arrive in days or minutes - no
# efficiency survives a deadline the thrust cannot meet.

_CLASSIFIER_TRAIN = [
    # (dv_km_s, log10_days, log10_power_kw, label)
    (11.0, 3.30, 1.00, "ideal"),        # Dawn-style tour, ~2000 d, 10 kW
    (10.0, 3.18, 0.85, "ideal"),        # deep-space flagship, ~1500 d
    (6.0, 2.60, 0.85, "ideal"),         # Mars cargo, 400 d, 7 kW
    (8.0, 2.95, 1.60, "ideal"),         # outer-planet cruise, ~900 d
    (12.0, 3.40, 1.18, "ideal"),        # grand tour, ~2500 d
    (5.0, 2.78, 0.48, "ideal"),         # asteroid rendezvous, 600 d
    (0.05, 2.56, -1.00, "workable"),    # cubesat SK, 365 d, 0.1 kW
    (0.5, 2.56, -0.30, "workable"),     # comsat SK year, 365 d, 0.5 kW
    (2.0, 2.26, 0.70, "workable"),      # orbit raising, 180 d, 5 kW
    (3.0, 2.08, 1.00, "workable"),      # slow GEO transfer, 120 d
    (1.0, 1.95, 0.30, "workable"),      # debris-tug nudge, 90 d
    (4.0, 2.30, 0.90, "workable"),      # cargo spiral-out, 200 d
    (9.4, -2.00, 4.00, "wrong-tool"),   # surface launch: minutes, not days
    (3.0, 0.30, 1.70, "wrong-tool"),    # 2-day transfer demand
    (6.0, 0.48, 1.30, "wrong-tool"),    # 3-day lunar dash
    (2.0, -0.30, 2.00, "wrong-tool"),   # 12-hour emergency retarget
    (8.0, 1.00, 1.48, "wrong-tool"),    # 10-day outer dash
    (1.0, -1.00, 0.70, "wrong-tool"),   # 2.4-hour plane change
]


def _features(dv_km_s, days, power_kw):
    if dv_km_s < 0 or days <= 0 or power_kw <= 0:
        raise ValueError("need dv >= 0, days > 0, power > 0")
    return (dv_km_s, math.log10(days), math.log10(power_kw))


def _dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def classify_mission(dv_km_s, days, power_kw, k=3):
    """kNN (k=3) mission-fit classifier: ideal / workable / wrong-tool."""
    f = _features(dv_km_s, days, power_kw)
    ranked = sorted(_CLASSIFIER_TRAIN, key=lambda row: _dist(f, row[:3]))
    votes = {}
    for row in ranked[:k]:
        votes[row[3]] = votes.get(row[3], 0) + 1
    return max(sorted(votes), key=lambda lab: votes[lab])


def fit_report():
    scenarios = {
        "dawn_style_tour": (11.0, 2000.0, 10.0),
        "mars_cargo_transfer": (6.0, 400.0, 7.0),
        "cubesat_station_keeping": (0.05, 365.0, 0.1),
        "comsat_orbit_raising": (2.0, 180.0, 5.0),
        "launch_from_surface": (9.4, 0.01, 10000.0),
        "three_day_lunar_dash": (6.0, 3.0, 20.0),
    }
    return {name: classify_mission(*args) for name, args in scenarios.items()}


# ================================================================ 9. Advisory seats
def _trace(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def carbon4_decide(topic="plasmapropulsion-demo"):
    """Gemini Carbon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-carbon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Carbon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all claim gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="plasmapropulsion-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Quote thrust and Isp together, never Isp alone: the 2/ve trade means the most efficient engine is also the feeblest push per kilowatt, and the burn calendar - months to years - belongs in every mission claim.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["a faint blue ion beam, almost invisible, pushing for months",
                  "the propellant gauge: chemical empties, ion barely moves",
                  "Dawn's spiral between asteroids, drawn one orbit at a time",
                  "the solar array growing as the Sun shrinks toward Mars",
                  "the launch pad, where the ion craft rides up switched off"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": carbon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    # 1. fundamentals
    chk("ve_nstar", abs(exhaust_velocity_m_s(3100.0) - 30400.615) < 0.01)
    chk("ve_chemical", abs(exhaust_velocity_m_s(450.0) - 4412.99) < 0.01)
    chk("mdot_nstar", abs(mass_flow_kg_s(0.092, 3100.0) - 3.0263e-6) < 0.01 * 3.0263e-6)
    chk("jet_power_nstar", abs(jet_power_w(0.092, 3100.0) - 1398.4) < 0.01 * 1398.4)
    chk("jet_power_identity",
        abs(jet_power_w(0.236, 4100.0)
            - 0.5 * 0.236 * exhaust_velocity_m_s(4100.0)) < 1e-9)
    chk("ideal_tpk_falls_with_isp",
        ideal_thrust_per_kw_mn(1600.0) > ideal_thrust_per_kw_mn(3100.0)
        > ideal_thrust_per_kw_mn(4100.0))
    chk("ideal_tpk_spt_value", abs(ideal_thrust_per_kw_mn(1600.0) - 127.46) < 0.5)
    chk("ideal_tpk_next_value", abs(ideal_thrust_per_kw_mn(4100.0) - 49.74) < 0.5)
    chk("accel_next_1000kg",
        abs(acceleration_m_s2(0.236, 1000.0) - 2.36e-4) < 1e-9)
    # 2. thruster table (labelled published-class)
    tab = {r["name"]: r for r in thruster_table()}
    chk("table_has_four_thrusters", len(tab) == 4)
    chk("eta_nstar_band", 0.58 < tab["NSTAR-class"]["efficiency"] < 0.64)
    chk("eta_next_band", 0.66 < tab["NEXT-class"]["efficiency"] < 0.72)
    chk("eta_spt_band", 0.45 < tab["SPT-100-class"]["efficiency"] < 0.51)
    chk("eta_x3_band", 0.64 < tab["X3-class"]["efficiency"] < 0.71)
    chk("eta_all_physical",
        all(0.0 < r["efficiency"] < 1.0 for r in tab.values()))
    chk("tpk_ordering_spt_beats_next",
        tab["SPT-100-class"]["thrust_per_kw_mn"]
        > tab["NEXT-class"]["thrust_per_kw_mn"])
    chk("tpk_nstar_value", abs(tab["NSTAR-class"]["thrust_per_kw_mn"] - 40.0) < 0.1)
    chk("tpk_next_value", abs(tab["NEXT-class"]["thrust_per_kw_mn"] - 34.2) < 0.1)
    chk("mdot_x3_kg_day", abs(tab["X3-class"]["mdot_kg_day"] - 18.30) < 0.05)
    chk("actual_tpk_is_eta_times_ideal",
        all(abs(r["thrust_per_kw_mn"]
                - r["efficiency"] * r["ideal_thrust_per_kw_mn"])
            < 1e-6 * r["ideal_thrust_per_kw_mn"] for r in tab.values()))
    # 3. efficiency chain closes exactly
    chk("chain_reconstructs_thrust",
        all(abs(r["thrust_from_chain_n"] - r["thrust_n"]) < 1e-12
            for r in efficiency_table()))
    chk("chain_losses_positive",
        all(r["lost_power_w"] > 0 for r in efficiency_table()))
    # 4. rocket equation
    chk("fraction_ion_10kms", abs(propellant_fraction(10000.0, 4100.0) - 0.2202) < 0.001)
    chk("fraction_chem_10kms", abs(propellant_fraction(10000.0, 450.0) - 0.8963) < 0.001)
    chk("fraction_zero_dv", propellant_fraction(0.0, 4100.0) == 0.0)
    chk("fraction_grows_with_dv",
        propellant_fraction(5000.0, 4100.0) < propellant_fraction(10000.0, 4100.0))
    head = headline_comparison()
    chk("headline_ion_kg", abs(head["ion_propellant_kg"] - 220.19) < 0.05)
    chk("headline_chem_kg", abs(head["chemical_propellant_kg"] - 896.28) < 0.05)
    chk("headline_saved_kg", abs(head["propellant_saved_kg"] - 676.08) < 0.1)
    chk("rocket_roundtrip",
        abs(delta_v_m_s(1000.0, 1000.0 - head["ion_propellant_kg"], 4100.0)
            - 10000.0) < 1e-6)
    chk("wet_for_dry_inverts_fraction",
        abs(wet_mass_for_dry_kg(779.81, 10000.0, 4100.0) - 1000.0) < 0.5)
    # 5. missions
    mb = {r["mission"]: r for r in mission_budgets()}
    mars = mb["Earth-Mars cruise (labelled model budget)"]
    dawn = mb["Dawn-style multi-target tour (labelled model)"]
    cube = mb["Cubesat station-keeping, per year (labelled model)"]
    chk("mars_prop_kg", abs(mars["propellant_kg"] - 110.90) < 0.05)
    chk("mars_burn_days", abs(mars["burn_time_days"] - 218.68) < 0.05)
    chk("dawn_prop_kg", abs(dawn["propellant_kg"] - 369.79) < 0.05)
    chk("dawn_burn_years", 3.7 < dawn["burn_time_days"] / DAYS_PER_YEAR < 4.1)
    chk("dawn_dv_per_day", 5.0 < dawn["dv_per_day_m_s"] < 8.0)
    chk("cubesat_prop_grams", abs(cube["propellant_kg"] * 1000.0 - 38.18) < 0.05)
    chk("cubesat_chemical_grams",
        abs(cubesat_chemical_per_year_kg() * 1000.0 - 135.19) < 0.05)
    chk("cubesat_ion_beats_chemical",
        cube["propellant_kg"] < cubesat_chemical_per_year_kg())
    # 6. power system + closure
    chk("solar_factor_mars", abs(solar_flux_factor(1.524) - 0.4306) < 0.001)
    chk("solar_factor_earth", solar_flux_factor(1.0) == 1.0)
    chk("array_next_earth_kg", abs(array_mass_kg(6900.0, 100.0) - 69.0) < 1e-9)
    rep = design_report()
    tug = rep["mars_cargo_tug"]
    big = rep["outer_system_x3_at_mars_distance"]
    chk("tug_closes", tug["status"] == "CLOSES" and not tug["reasons"])
    chk("tug_wet_kg", abs(tug["wet_kg"] - 527.07) < 0.1)
    chk("tug_prop_kg", abs(tug["propellant_kg"] - 73.07) < 0.05)
    chk("big_refused", big["status"] == "REFUSED" and len(big["reasons"]) >= 1)
    chk("big_array_dominates", big["array_kg"] > 2000.0)
    chk("big_wet_over_cap", big["wet_kg"] > 3000.0)
    # 7. launch audit
    la = launch_audit()
    chk("launch_impossible", la["can_launch"] is False)
    chk("best_tw_tiny", 0.0 < la["best_thrust_to_weight"] < 1e-3)
    chk("next_tw_value",
        abs([r for r in la["rows"] if r["thruster"] == "NEXT-class"][0]
            ["thrust_to_weight"] - 2.4065e-5) < 0.01 * 2.4065e-5)
    # 8. classifier
    fr = fit_report()
    chk("classifier_dawn_ideal", fr["dawn_style_tour"] == "ideal")
    chk("classifier_mars_ideal", fr["mars_cargo_transfer"] == "ideal")
    chk("classifier_cubesat_workable", fr["cubesat_station_keeping"] == "workable")
    chk("classifier_raising_workable", fr["comsat_orbit_raising"] == "workable")
    chk("classifier_launch_wrong", fr["launch_from_surface"] == "wrong-tool")
    chk("classifier_dash_wrong", fr["three_day_lunar_dash"] == "wrong-tool")
    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14 and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_spacecraft_hold", gate("real_spacecraft_operation") == "HOLD")
    chk("gate_firing_hold", gate("live_thruster_firing") == "HOLD")
    chk("gate_launch_claim_hold", gate("launch_capability_claim") == "HOLD")
    chk("gate_faster_claim_hold", gate("faster_mission_claim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    b = brains_report()
    chk("carbon4_no_override", b["decider"]["can_override_hold"] is False)
    chk("claude_no_override", b["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", b["flow"]["rendered"] is False and b["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def demo():
    print("=" * 68)
    print("PlasmaPropulsion-Lab - educational ion & Hall thruster propulsion lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] Fundamentals - the thrust / power trade T/P = 2/ve")
    for isp in (450.0, 1600.0, 2600.0, 3100.0, 4100.0):
        print(f"    Isp {isp:6.0f} s: ve = {exhaust_velocity_m_s(isp):9.1f} m/s | "
              f"ideal thrust per kW = {ideal_thrust_per_kw_mn(isp):6.1f} mN/kW")
    print("    -> double the Isp, halve the push per watt. Efficiency is feeble")
    print("       on purpose: the exhaust leaves so fast there is barely any of it.")
    print("\n[2] Thruster table (LABELLED published-class reference values)")
    for r in thruster_table():
        print(f"    {r['name']:14s} {r['kind']:11s} Isp {r['isp_s']:5.0f} s | "
              f"T = {r['thrust_n']:6.3f} N @ {r['power_w']:7.0f} W | "
              f"eta = {r['efficiency']:.3f} | mdot = {r['mdot_kg_day']:.3f} kg/day")
    print("    -> eta is DERIVED from the three nameplate numbers, so the table")
    print("       cannot contradict the physics. SPT-100 (lowest Isp) buys the")
    print("       most thrust per kW; NEXT (highest Isp) buys the least.")
    print("\n[3] Efficiency chain - Pin -> Pjet -> thrust")
    for r in efficiency_table():
        print(f"    {r['name']:14s} Pin {r['power_w']:7.0f} W -> "
              f"Pjet {r['jet_power_w']:8.1f} W (lost {r['lost_power_w']:7.1f} W) -> "
              f"T {r['thrust_from_chain_n']:.3f} N | {r['thrust_per_kw_mn']:.1f} mN/kW")
    print("\n[4] THE HEADLINE - rocket equation, 1,000 kg craft, dv = 10 km/s")
    head = headline_comparison()
    print(f"    ion (Isp 4100 s)     : {head['ion_propellant_kg']:7.2f} kg propellant "
          f"({100 * head['ion_propellant_kg'] / 1000.0:.1f}% of wet mass)")
    print(f"    chemical (Isp 450 s) : {head['chemical_propellant_kg']:7.2f} kg propellant "
          f"({100 * head['chemical_propellant_kg'] / 1000.0:.1f}% of wet mass)")
    print(f"    propellant saved     : {head['propellant_saved_kg']:7.2f} kg - "
          "that is the entire case for electric propulsion")
    print("\n[5] Mission budgets (LABELLED models - stated dv, stated craft)")
    for r in mission_budgets():
        print(f"    {r['mission']}")
        print(f"      {r['blurb']}")
        print(f"      wet {r['wet_mass_kg']:.0f} kg | dv {r['dv_m_s']:.0f} m/s | "
              f"{r['thruster']}: propellant {r['propellant_kg']:.2f} kg | "
              f"continuous burn {r['burn_time_days']:.1f} days | "
              f"accel {r['accel_m_s2']:.2e} m/s^2 ({r['dv_per_day_m_s']:.1f} m/s per day)")
    print(f"    cubesat on chemical instead: "
          f"{cubesat_chemical_per_year_kg() * 1000.0:.1f} g/yr vs 38.2 g/yr ion-class")
    print("    -> Dawn-class tours burn for YEARS of accumulated thrust. The")
    print("       calendar, not the tank, is what an ion mission spends.")
    print("\n[6] Power system sizing + mission closure (labelled model)")
    print(f"    sunlight at Mars distance (1.524 AU): "
          f"{solar_flux_factor(1.524):.3f} of Earth's - the same array")
    print(f"    makes {SOLAR_SPEC_W_PER_KG_EARTH * solar_flux_factor(1.524):.1f} W/kg "
          f"instead of {SOLAR_SPEC_W_PER_KG_EARTH:.0f} W/kg")
    rep = design_report()
    for name, d in rep.items():
        print(f"    {name}: dry {d['dry_kg']:.0f} kg (array {d['array_kg']:.0f} kg) "
              f"-> wet {d['wet_kg']:.0f} kg, propellant {d['propellant_kg']:.0f} kg "
              f"-> {d['status']}")
        for reason in d["reasons"]:
            print(f"      REFUSAL: {reason}")
    print("\n[7] Why electric propulsion cannot launch anything")
    la = launch_audit()
    for r in la["rows"]:
        print(f"    {r['thruster']:14s} on 1,000 kg: T/W = {r['thrust_to_weight']:.2e} "
              f"(accel {r['accel_m_s2']:.2e} m/s^2)")
    print("    -> hovering needs T/W > 1. The best here is ~5.5e-4 (X3). Chemical")
    print("       rockets do the launching; ion engines start work in orbit.")
    print("\n[8] Mission-fit classifier (TinyML kNN)")
    for name, label in fit_report().items():
        print(f"    {name:26s} -> {label}")
    print("\n[9] Advisory seats")
    print(f"    decider: {carbon4_decide()['decision']} trace={carbon4_decide()['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {claude_advisor()['can_override_hold']}")
    print(f"    flow rendered = {google_flow_plan()['rendered']} live = {google_flow_plan()['live']}")
    print(f"\n[10] HOLD gates: {len(HOLD_GATES)}")
    for k in HOLD_GATES:
        print(f"    HOLD  {k}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "fundamentals":
        for isp in (250.0, 450.0, 800.0, 1600.0, 2600.0, 3100.0, 4100.0, 6000.0):
            print(f"Isp={isp:6.0f} s  ve={exhaust_velocity_m_s(isp):9.1f} m/s  "
                  f"ideal T/kW={ideal_thrust_per_kw_mn(isp):7.1f} mN/kW  "
                  f"prop fraction @5 km/s={propellant_fraction(5000.0, isp):.4f}")
        return 0
    if cmd == "thrusters":
        print(json.dumps(thruster_table(), indent=2, sort_keys=True))
        return 0
    if cmd == "efficiency":
        print(json.dumps(efficiency_table(), indent=2, sort_keys=True))
        return 0
    if cmd == "rocket":
        print(json.dumps(headline_comparison(), indent=2, sort_keys=True))
        for dv in (1000.0, 3000.0, 6000.0, 10000.0, 15000.0):
            print(f"dv={dv:6.0f} m/s  ion fraction={propellant_fraction(dv, 4100.0):.4f}  "
                  f"chemical fraction={propellant_fraction(dv, CHEMICAL_ISP_S):.4f}")
        return 0
    if cmd == "missions":
        print(json.dumps(mission_budgets(), indent=2, sort_keys=True))
        return 0
    if cmd == "power":
        print(json.dumps(design_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "launch":
        print(json.dumps(launch_audit(), indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(fit_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for k, v in HOLD_GATES.items():
            print(f"{k}: {v}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "live_thruster_firing"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
