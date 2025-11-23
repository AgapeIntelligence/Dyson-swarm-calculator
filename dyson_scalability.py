import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# Dyson-Scale Sunshade / Solar Occluder Scalability Model
# Updated 2025: Includes von Neumann probes, LFTR power, thorium breeding, waste heat propulsion
# All physics approximate; intended for trajectory analysis and comparison
# =============================================================================

# Fundamental constants (2025 updates)
R_earth = 6.371e6                  # m
A_earth_cross_section = np.pi * R_earth**2   # m² ≈ 1.274e14 m²
S0 = 1362.0                        # W/m² at 1 AU (SORCE 2024 average, Cycle 25)
c = 299792458.0                    # m/s

def dyson_scalability(eta_target,
                      A_shade_m2=1e6,              # area per occulter (default 1 km²)
                      kappa=0.95,                  # optical effectiveness (reflectivity/transparency)
                      areal_density_kgpm2=0.001,   # kg/m² (1 g/m² baseline ultralight film)
                      payload_to_l1_t=50.0,        # effective delivered mass per launch to L1
                      flights_per_year=20.0,       # initial launch cadence
                      launch_cadence_growth_rate=0.20,  # 20%/yr exponential growth
                      factory_production_t_per_year_initial=1e5,  # initial off-Earth mass [t/yr]
                      factory_growth_rate=0.50,    # 50%/yr self-replicating growth
                      mission_years=100,
                      von_neumann_enabled=False,   # toggle von Neumann probes
                      vn_replication_years=10.0,   # replication cycle
                      vn_efficiency=0.20,          # SiO2 yield from C-type asteroids
                      vn_initial_probes=10,        # starting probe count
                      lftr_enabled=False,          # toggle LFTR power
                      lftr_mass_ton=2.0,           # LFTR unit mass [tons]
                      lftr_power_mw_per_ton=250.0, # MW/ton (average of 200-300 MW/ton)
                      waste_heat_propulsion_eff=0.35,  # efficiency of heat-to-thrust conversion
                      thorium_breeding_ratio=1.05,  # U-233 breeding ratio
                      thorium_concentration_ppm=10.0):  # Th ppm in C-type asteroids
    """
    Returns scalability with von Neumann probes, LFTR power, and thorium breeding.
    von_neumann_enabled: Activates autonomous replication beyond asteroid belt.
    lftr_enabled: Uses LFTR for shadowed ops, with waste heat propulsion.
    thorium_breeding_ratio: Self-sustaining fuel production (e.g., 1.05 doubles fuel every ~15-20 yr).
    """
    # Core requirements (L1 phase)
    N_occulter = eta_target * A_earth_cross_section / (A_shade_m2 * kappa)
    mass_per_occulter_kg = A_shade_m2 * areal_density_kgpm2
    total_mass_t = N_occulter * mass_per_occulter_kg / 1000.0
    total_area_km2 = N_occulter * A_shade_m2 / 1e6

    launches_required = total_mass_t / payload_to_l1_t
    years_at_constant_cadence = launches_required / flights_per_year

    if launch_cadence_growth_rate > 0:
        g = launch_cadence_growth_rate
        T_exp = np.log(1 + launches_required * np.log(1 + g) / flights_per_year) / np.log(1 + g)
    else:
        T_exp = years_at_constant_cadence

    r = factory_growth_rate
    if r > 0 and factory_production_t_per_year_initial > 0:
        cumprod = np.cumsum(np.cumprod(np.ones(mission_years + 1) * (1 + r)) * factory_production_t_per_year_initial)
        year_self_sufficient = np.argmax(cumprod >= total_mass_t)
        if year_self_sufficient == 0 and cumprod[-1] < total_mass_t:
            year_self_sufficient = mission_years + 10
    else:
        year_self_sufficient = np.inf

    # Von Neumann expansion (if enabled)
    extra_occulters = 0
    total_probe_mass_t = 0
    if von_neumann_enabled:
        years = np.arange(mission_years + 1)
        N_probes = vn_initial_probes * 2 ** (years / vn_replication_years)
        mass_per_probe_kg = 1000.0  # 1 ton per probe
        total_probe_mass_t = N_probes[-1] * mass_per_probe_kg / 1000.0
        extra_occulters = N_probes[-1] * (vn_efficiency * A_earth_cross_section / A_shade_m2)
        N_occulter += extra_occulters
        total_mass_t += total_probe_mass_t
        year_vn_dominance = np.argmax(N_probes > N_occulter / vn_initial_probes)
        year_self_sufficient = min(year_self_sufficient, year_vn_dominance) if year_vn_dominance < mission_years else year_self_sufficient

    # LFTR and waste heat propulsion (if enabled)
    lftr_power_kw = 0
    propellant_savings_t = 0
    if lftr_enabled:
        total_lftr_mass_t = lftr_mass_t * np.ceil(N_occulter / 1000)  # 1 LFTR per 1000 occulters
        lftr_power_mw = total_lftr_mass_t * lftr_power_mw_per_ton
        lftr_power_kw = lftr_power_mw * 1000
        waste_heat_power_kw = lftr_power_kw * (1 - waste_heat_propulsion_eff)  # Remaining heat
        # Approx 50% propellant savings from 120-240 kW thrust (per l1_stationkeeping.py)
        propellant_savings_t = total_mass_t * 0.5 * (waste_heat_power_kw / 500)  # Scaled to 500 kW hub
        total_mass_t += total_lftr_mass_t - propellant_savings_t

    # Thorium breeding impact
    if lftr_enabled and thorium_breeding_ratio > 1:
        thorium_mass_t = (total_mass_t * thorium_concentration_ppm / 1e6)  # Th in mined material
        fuel_doubling_years = np.log(2) / np.log(thorium_breeding_ratio)  # ~14-20 years
        cumulative_fuel_t = thorium_mass_t * (1 + thorium_breeding_ratio) ** (mission_years / fuel_doubling_years)
        if cumulative_fuel_t > thorium_mass_t:
            year_self_sufficient = min(year_self_sufficient, mission_years // fuel_doubling_years)

    power_blocked_TW = eta_target * S0 * A_earth_cross_section / 1e12

    return {
        "eta_target": eta_target,
        "N_occulter": N_occulter,
        "total_area_km2": total_area_km2,
        "total_mass_t": total_mass_t,
        "mass_per_occulter_kg": mass_per_occulter_kg,
        "launches_required": launches_required,
        "years_constant_cadence": years_at_constant_cadence,
        "years_exponential_launches_20pct": T_exp,
        "years_self_replicating_50pct": year_self_sufficient if year_self_sufficient <= mission_years else np.inf,
        "power_blocked_TW": power_blocked_TW,
        "von_neumann_enabled": von_neumann_enabled,
        "N_probes_final": N_probes[-1] if von_neumann_enabled else 0,
        "extra_occulters_from_vn": extra_occulters if von_neumann_enabled else 0,
        "lftr_enabled": lftr_enabled,
        "lftr_power_kw": lftr_power_kw,
        "propellant_savings_t": propellant_savings_t,
        "thorium_breeding_ratio": thorium_breeding_ratio,
        "year_fuel_self_sufficiency": year_self_sufficient if lftr_enabled and thorium_breeding_ratio > 1 else np.inf,
    }

# =============================================================================
# Example: From climate SRM to full Dyson Swarm with all options
# =============================================================================
if __name__ == "__main__":
    targets = [
        0.018, 0.10, 0.30, 0.50, 0.99, 1.00,
    ]

    print("DYSON-SCALE OCCLUDER / SUNSHADE SCALABILITY (Updated 2025 w/ VN, LFTR, Th)\n")
    print(f"{'eta':>6} {'Occluders':>14} {'Mass [Gt]':>10} {'Launches':>12} {'Yrs Const':>9} "
          f"{'Yrs Exp20%':>10} {'Yrs Self50%':>11} {'Power[TW]':>10} {'Extra Occ':>12} {'LFTR Pwr [MW]':>13} {'Prop Sav [t]':>12}")
    print("-" * 130)

    for eta in targets:
        res = dyson_scalability(eta,
                                A_shade_m2=1e6,
                                areal_density_kgpm2=0.0005,  # optimistic 0.5 g/m²
                                payload_to_l1_t=50,
                                flights_per_year=20,
                                launch_cadence_growth_rate=0.20,
                                factory_production_t_per_year_initial=1e5,
                                factory_growth_rate=0.50,
                                von_neumann_enabled=True,
                                lftr_enabled=True)
        print(f"{eta:6.3f} "
              f"{res['N_occulter']/1e6:8.2f}M "
              f"{res['total_mass_t']/1e9:7.2f} "
              f"{res['launches_required']/1e6:6.1f}M "
              f"{res['years_constant_cadence']:6.0f}y "
              f"{res['years_exponential_launches_20pct']:6.0f}y "
              f"{'∞' if np.isinf(res['years_self_replicating_50pct']) else res['years_self_replicating_50pct']:6.0f}y "
              f"{res['power_blocked_TW']:8.0f} "
              f"{res['extra_occulters_from_vn']/1e6:9.2f}M "
              f"{res['lftr_power_kw']/1000:9.2f} "
              f"{res['propellant_savings_t']:9.2f}")
