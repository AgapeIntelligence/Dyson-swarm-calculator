import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# Dyson-Scale Sunshade / Solar Occluder Scalability Model
# Updated 2025: Includes von Neumann probe expansion beyond asteroid belt
# All physics approximate; intended for trajectory analysis and comparison
# =============================================================================

# Fundamental constants (2025 updates)
R_earth = 6.371e6                  # m
A_earth_cross_section = np.pi * R_earth**2   # m² ≈ 1.274e14 m²
S0 = 1362.0                        # W/m² at 1 AU (SORCE 2024 average, Cycle 25)
c = 299792458.0                    # m/s

def dyson_scalability(eta_target,
                      A_shade_m2=1e6,              # area per occulter (default 1 km²)
                      kappa=0.95,                  # optical effectiveness
                      areal_density_kgpm2=0.001,   # kg/m² (1 g/m² baseline)
                      payload_to_l1_t=50.0,        # effective delivered mass per launch to L1
                      flights_per_year=20.0,       # initial launch cadence
                      launch_cadence_growth_rate=0.20,  # 20%/yr exponential growth
                      factory_production_t_per_year_initial=1e5,  # initial off-Earth mass [t/yr]
                      factory_growth_rate=0.50,    # 50%/yr self-replicating growth
                      mission_years=100,
                      von_neumann_enabled=False,   # toggle von Neumann probes
                      vn_replication_years=10.0,   # replication cycle
                      vn_efficiency=0.20,          # SiO2 yield from C-type asteroids
                      vn_initial_probes=10):       # starting probe count
    """
    Returns scalability with optional von Neumann probe expansion.
    von_neumann_enabled: Activates autonomous replication beyond asteroid belt.
    vn_replication_years: Time for one replication cycle.
    vn_efficiency: Fraction of local material converted to new probes/shades.
    vn_initial_probes: Number of initial self-replicating probes.
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
    if von_neumann_enabled:
        # Exponential growth of probes: N(t) = N0 * 2^(t / T_rep)
        years = np.arange(mission_years + 1)
        N_probes = vn_initial_probes * 2 ** (years / vn_replication_years)
        # Mass contribution: each probe builds occulters from local material
        mass_per_probe_kg = 1000.0  # Assume 1 ton per probe (scalable)
        total_probe_mass_t = N_probes[-1] * mass_per_probe_kg / 1000.0
        # Additional occulters from replication: efficiency-limited by yield
        extra_occulters = N_probes[-1] * (vn_efficiency * A_earth_cross_section / A_shade_m2)
        N_occulter += extra_occulters
        total_mass_t += total_probe_mass_t
        year_vn_dominance = np.argmax(N_probes > N_occulter / vn_initial_probes)
        year_self_sufficient = min(year_self_sufficient, year_vn_dominance) if year_vn_dominance < mission_years else year_self_sufficient

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
    }

# =============================================================================
# Example: From climate SRM to full Dyson Swarm with von Neumann option
# =============================================================================
if __name__ == "__main__":
    targets = [
        0.018, 0.10, 0.30, 0.50, 0.99, 1.00,
    ]

    print("DYSON-SCALE OCCLUDER / SUNSHADE SCALABILITY (w/ Von Neumann Option)\n")
    print(f"{'eta':>6} {'Occluders':>14} {'Mass [Gt]':>10} {'Launches':>12} {'Yrs Const':>9} "
          f"{'Yrs Exp20%':>10} {'Yrs Self50%':>11} {'Power[TW]':>10} {'Extra Occ':>12}")
    print("-" * 100)

    for eta in targets:
        # Baseline (no VN)
        res_no_vn = dyson_scalability(eta, areal_density_kgpm2=0.0005)
        # With VN
        res_vn = dyson_scalability(eta, areal_density_kgpm2=0.0005, von_neumann_enabled=True)
        print(f"{eta:6.3f} "
              f"{res_vn['N_occulter']/1e6:8.2f}M "
              f"{res_vn['total_mass_t']/1e9:7.2f} "
              f"{res_vn['launches_required']/1e6:6.1f}M "
              f"{res_vn['years_constant_cadence']:6.0f}y "
              f"{res_vn['years_exponential_launches_20pct']:6.0f}y "
              f"{'∞' if np.isinf(res_vn['years_self_replicating_50pct']) else res_vn['years_self_replicating_50pct']:6.0f}y "
              f"{res_vn['power_blocked_TW']:8.0f} "
              f"{res_vn['extra_occulters_from_vn']/1e6:9.2f}M")
