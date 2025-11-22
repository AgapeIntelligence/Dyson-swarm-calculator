import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# Dyson-Scale Sunshade / Solar Occluder Scalability Model
# Engineering-level parametric tool – from climate SRM to full Dyson Swarm
# All physics approximate; intended for trajectory analysis and comparison
# =============================================================================

# Fundamental constants
R_earth = 6.371e6                  # m
A_earth_cross_section = np.pi * R_earth**2   # m² ≈ 1.274e14 m²
S0 = 1361.0                        # W/m² at 1 AU

def dyson_scalability(eta_target,
                      A_shade_m2=1e6,              # area per occulter (default 1 km²)
                      kappa=0.95,                  # optical effectiveness (reflectivity/transparency)
                      areal_density_kgpm2=0.001,   # kg/m² (1 g/m² baseline ultralight film)
                      payload_to_l1_t=50.0,        # effective delivered mass per launch to L1
                      flights_per_year=20.0,       # initial launch cadence
                      launch_cadence_growth_rate=0.20,  # 20%/yr exponential growth (Starship-like)
                      factory_production_t_per_year_initial=1e5,   # initial off-Earth mass production [t/yr]
                      factory_growth_rate=0.50,    # 50%/yr (self-replicating industrial base)
                      mission_years=100):          # simulation horizon
    """
    Returns comprehensive scalability dictionary for arbitrary occlusion fraction eta_target (0–1).
    """
    # Core requirements
    N_occulter = eta_target * A_earth_cross_section / (A_shade_m2 * kappa)
    mass_per_occulter_kg = A_shade_m2 * areal_density_kgpm2
    total_mass_t = N_occulter * mass_per_occulter_kg / 1000.0
    total_area_km2 = N_occulter * A_shade_m2 / 1e6

    # Launch-only scenario (no off-Earth industry)
    launches_required = total_mass_t / payload_to_l1_t
    years_at_constant_cadence = launches_required / flights_per_year

    # Exponential launch growth scenario
    # Solve N_launches_total = integral_0^T cadence_0 * (1+g)^t dt = (cadence_0 / ln(1+g)) * ((1+g)^T - 1)
    if launch_cadence_growth_rate > 0:
        g = launch_cadence_growth_rate
        T_exp = np.log(1 + launches_required * np.log(1+g) / flights_per_year) / np.log(1+g)
    else:
        T_exp = years_at_constant_cadence

    # Full self-replicating industry scenario (mass produced off-Earth)
    # Available mass in year t: M(t) = M0 * (1 + r)^t  (compound growth)
    r = factory_growth_rate
    if r > 0 and factory_production_t_per_year_initial > 0:
        # Year when cumulative production exceeds required mass
        cumprod = np.cumprod(np.ones(mission_years) * (1 + r)) * factory_production_t_per_year_initial
        cumprod = np.cumsum(cumprod)
        year_self_sufficient = np.argmax(cumprod >= total_mass_t)
        if year_self_sufficient == 0 and cumprod[-1] < total_mass_t:
            year_self_sufficient = mission_years + 10  # never
    else:
        year_self_sufficient = np.inf

    power_blocked_TW = eta_target * S0 * A_earth_cross_section / 1e12   # TW blocked

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
    }

# =============================================================================
# Example: From climate SRM to full Dyson Swarm
# =============================================================================
if __name__ == "__main__":
    targets = [
        0.018,       # Current climate offset (~2.7 W/m² forcing)
        0.10,        # Full Ice Age prevention / deep cooling
        0.30,        # 30% Dyson swarm (significant energy capture)
        0.50,        # Half Dyson
        0.99,        # Near-complete stellar occlusion
        1.00,        # Theoretical full Dyson sphere equivalent (statite swarm)
    ]

    print("DYSON-SCALE OCCLUDER / SUNSHADE SCALABILITY\n")
    print(f"{'eta':>6} {'Occluders':>14} {'Mass [Gt]':>10} {'Launches':>12} {'Yrs Const':>9} {'Yrs Exp20%':>10} {'Yrs Self50%':>11} {'Power[TW]':>10}")
    print("-" * 90)

    for eta in targets:
        res = dyson_scalability(eta,
                                A_shade_m2=1e6,
                                areal_density_kgpm2=0.0005,   # optimistic 0.5 g/m²
                                payload_to_l1_t=50,
                                flights_per_year=20,
                                launch_cadence_growth_rate=0.20,
                                factory_production_t_per_year_initial=1e5,
                                factory_growth_rate=0.50)
        print(f"{eta:6.3f} "
              f"{res['N_occulter']/1e6:8.2f}M "
              f"{res['total_mass_t']/1e9:7.2f} "
              f"{res['launches_required']/1e6:6.1f}M "
              f"{res['years_constant_cadence']:6.0f}y "
              f"{res['years_exponential_launches_20pct']:6.0f}y "
              f"{'∞' if np.isinf(res['years_self_replicating_50pct']) else res['years_self_replicating_50pct']:6.0f}y "
              f"{res['power_blocked_TW']:8.0f}")
