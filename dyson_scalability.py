import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# Dyson-Scale Sunshade / Solar Occluder Scalability Model — 2025 Final
# Features:
#   • True exponential fusion fuel decay via half-life (100–1000 yr missions)
#   • Hybrid solar + p-B11 fusion + beamed microwave power
#   • Von Neumann probes, LFTR, antimatter, L1 halo thrust
#   • Oort Cloud & interstellar ready
# =============================================================================

# Fundamental constants (2025 values)
R_earth = 6.371e6
A_earth_cross_section = np.pi * R_earth**2
S0 = 1362.0                        # W/m² at 1 AU (SORCE 2024 avg)
c = 299792458.0
g0 = 9.80665

def hybrid_power(au_distance,
                 mission_time_yr,
                 solar_area_m2=1e6,
                 solar_eff=0.20,
                 fusion_base_kw=200.0,
                 beamed_microwave_kw=0.0,
                 fusion_half_life_yr=12.0):
    """
    Final deep-space hybrid power model.
    Exponential decay: 0.5^(t / half_life) — true physics
    """
    solar_kw = (S0 / (au_distance ** 2)) * solar_area_m2 * solar_eff / 1000.0
    decay_fraction = 0.5 ** (mission_time_yr / fusion_half_life_yr)
    fusion_remaining_kw = fusion_base_kw * decay_fraction
    return max(solar_kw, fusion_remaining_kw + beamed_microwave_kw)

def optimize_l1_thrust(mass_kg, power_kw, delta_v_mps=75.0, isp_s=1e6):
    thrust_n = power_kw * 0.10
    fuel_kg = mass_kg * (np.exp(delta_v_mps / (isp_s * g0)) - 1) if delta_v_mps > 0 else 0.0
    return {"thrust_n": thrust_n, "annual_fuel_kg": fuel_kg}

def dyson_scalability(eta_target,
                      A_shade_m2=1e6,
                      kappa=0.95,
                      areal_density_kgpm2=0.0005,
                      payload_to_l1_t=50.0,
                      flights_per_year=20.0,
                      launch_cadence_growth_rate=0.20,
                      factory_production_t_per_year_initial=1e5,
                      factory_growth_rate=0.50,
                      mission_years=100,
                      mission_time_yr=100.0,                    # Time from Earth to deployment
                      von_neumann_enabled=False,
                      vn_replication_years=10.0,
                      vn_efficiency=0.20,
                      vn_initial_probes=10,
                      lftr_enabled=False,
                      lftr_mass_ton=2.0,
                      lftr_power_mw_per_ton=250.0,
                      waste_heat_propulsion_eff=0.35,
                      thorium_breeding_ratio=1.05,
                      thorium_concentration_ppm=10.0,
                      antimatter_enabled=False,
                      antimatter_mass_mg_per_probe=10.0,
                      fusion_base_kw=500.0,
                      beamed_microwave_kw=0.0,
                      au_distance=100.0,
                      fusion_half_life_yr=12.0,
                      annual_delta_v_mps=75.0):
    """
    Final interstellar Dyson scalability model.
    mission_time_yr = total time from launch to full swarm deployment
    """
    N_occulter = eta_target * A_earth_cross_section / (A_shade_m2 * kappa)
    mass_per_occulter_kg = A_shade_m2 * areal_density_kgpm2
    total_mass_t = N_occulter * mass_per_occulter_kg / 1000.0

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

    # Von Neumann, LFTR, antimatter (unchanged from prior versions)
    extra_occulters = 0
    total_probe_mass_t = 0
    if von_neumann_enabled:
        N_probes = vn_initial_probes * 2 ** (mission_time_yr / vn_replication_years)
        total_probe_mass_t = N_probes * 1000.0 / 1000.0
        extra_occulters = N_probes * (vn_efficiency * A_earth_cross_section / A_shade_m2)
        N_occulter += extra_occulters
        total_mass_t += total_probe_mass_t

    if lftr_enabled:
        total_lftr_mass_t = lftr_mass_ton * np.ceil(N_occulter / 1000)
        total_mass_t += total_lftr_mass_t

    if antimatter_enabled:
        total_antimatter_t = N_probes * antimatter_mass_mg_per_probe / 1e6
        total_mass_t += total_antimatter_t

    # Hybrid power with exponential decay
    power_per_occulter_kw = hybrid_power(au_distance=au_distance,
                                         mission_time_yr=mission_time_yr,
                                         solar_area_m2=A_shade_m2,
                                         fusion_base_kw=fusion_base_kw,
                                         beamed_microwave_kw=beamed_microwave_kw,
                                         fusion_half_life_yr=fusion_half_life_yr)

    # L1 / deep-space station-keeping fuel
    thrust = optimize_l1_thrust(mass_per_occulter_kg, power_per_occulter_kw, annual_delta_v_mps, 1e6)
    total_fuel_t = (thrust["annual_fuel_kg"] * N_occulter * mission_years) / 1e6
    total_mass_t += total_fuel_t

    power_blocked_TW = eta_target * S0 * A_earth_cross_section / 1e12

    return {
        "eta_target": eta_target,
        "N_occulter": N_occulter,
        "total_mass_t": total_mass_t,
        "launches_required": launches_required,
        "years_constant_cadence": years_at_constant_cadence,
        "years_exponential_launches_20pct": T_exp,
        "years_self_replicating_50pct": year_self_sufficient if year_self_sufficient <= mission_years else np.inf,
        "power_blocked_TW": power_blocked_TW,
        "au_distance": au_distance,
        "mission_time_yr": mission_time_yr,
        "power_per_occulter_kw": power_per_occulter_kw,
        "fusion_survival_fraction": 0.5 ** (mission_time_yr / fusion_half_life_yr),
        "total_fuel_t": total_fuel_t,
        "von_neumann_enabled": von_neumann_enabled,
        "lftr_enabled": lftr_enabled,
        "antimatter_enabled": antimatter_enabled,
        "beamed_microwave_kw": beamed_microwave_kw,
    }

# =============================================================================
# Oort Cloud / Interstellar Swarm Test Suite
# =============================================================================
if __name__ == "__main__":
    print("Dyson Scalability — Oort Cloud / Interstellar Swarm (2025 Final)\n")
    print(f"{'η':>6} {'AU':>6} {'Time':>6} {'Fusion In':>8} {'Power Out':>8} {'Fuel Left':>8} {'Mass Gt':>8} {'Fuel t':>8}")
    print("-" * 80)

    cases = [
        (0.018,  1.0,   1,  200,    0, 12.0),
        (0.50,  10.0,  10,  800, 1000, 12.0),
        (1.00,  50.0,  50, 3000,    0, 18.0),
        (1.00, 100.0, 100, 8000,    0, 12.0),
        (1.00, 100.0, 100, 4000,    0, 30.0),
        (1.00, 100.0, 100, 2500,    0, 100.0),
    ]

    for eta, au, t, fusion, beamed, hl in cases:
        res = dyson_scalability(eta_target=eta,
                                au_distance=au,
                                mission_time_yr=t,
                                fusion_base_kw=fusion,
                                beamed_microwave_kw=beamed,
                                fusion_half_life_yr=hl)
        print(f"{eta:6.3f} {au:6.0f} {t:6.0f} {fusion:8.0f} {res['power_per_occulter_kw']:8.0f} "
              f"{res['fusion_survival_fraction']*100:7.1f}% {res['total_mass_t']/1e9:7.1f} {res['total_fuel_t']/1e3:^8.1f}")
