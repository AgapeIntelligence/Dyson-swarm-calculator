import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# Dyson-Scale Sunshade / Solar Occluder Scalability Model
# Updated 2025: Optimized L1 halo thrust with hybrid solar-fusion, von Neumann,
# LFTR, thorium breeding, and antimatter drives
# All physics approximate; intended for trajectory analysis and comparison
# =============================================================================

# Fundamental constants (2025 updates)
R_earth = 6.371e6                  # m
A_earth_cross_section = np.pi * R_earth**2   # m² ≈ 1.274e14 m²
S0 = 1362.0                        # W/m² at 1 AU (SORCE 2024 average, Cycle 25)
c = 299792458.0                    # m/s
G0 = 9.80665                       # m/s² (standard gravity)

def optimize_l1_thrust(mass_kg, power_kw, au_distance, delta_v_target_mps=75.0, isp_s=1e6):
    """
    Optimizes fuel mass for L1 halo station-keeping using hybrid power.
    delta_v_target_mps: Annual Δv (optimized to ~75 m/s/year per Science.gov).
    isp_s: Fusion-specific impulse (10⁶ s for p-B11).
    """
    # Power-based thrust scaling (assuming 1 kW → 0.1 N for ion/fusion hybrid)
    thrust_n = power_kw * 0.1  # Approximate thrust from power (adjustable)
    acceleration_m_s2 = thrust_n / mass_kg if mass_kg > 0 else 0
    time_sec = delta_v_target_mps / acceleration_m_s2 if acceleration_m_s2 > 0 else 0

    # Tsiolkovsky for fuel mass
    if isp_s > 0 and delta_v_target_mps > 0:
        mass_ratio = np.exp(delta_v_target_mps / (isp_s * G0))
        fuel_mass_kg = mass_kg * (mass_ratio - 1)
    else:
        fuel_mass_kg = 0.0

    return {
        "thrust_n": thrust_n,
        "acceleration_m_s2": acceleration_m_s2,
        "time_sec": time_sec,
        "fuel_mass_kg": fuel_mass_kg,
        "delta_v_mps": delta_v_target_mps
    }

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
                      vn_initial_probes=10,        # starting probe count
                      lftr_enabled=False,          # toggle LFTR power
                      lftr_mass_ton=2.0,           # LFTR unit mass [tons]
                      lftr_power_mw_per_ton=250.0, # MW/ton (average of 200-300 MW/ton)
                      waste_heat_propulsion_eff=0.35,  # efficiency of heat-to-thrust conversion
                      thorium_breeding_ratio=1.05,  # U-233 breeding ratio
                      thorium_concentration_ppm=10.0,  # Th ppm in C-type asteroids
                      antimatter_enabled=False,    # toggle antimatter drives
                      antimatter_mass_mg_per_probe=10.0,  # mg per probe
                      fusion_power_kw=50.0,        # p-B11 baseline power
                      au_distance=1.0,             # Distance from Sun in AU
                      l1_halo_delta_v_mps=75.0):   # Optimized annual Δv for L1 halo
    """
    Returns scalability with optimized L1 halo thrust using hybrid solar-fusion.
    l1_halo_delta_v_mps: Optimized to ~75 m/s/year for minimal fuel.
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
        waste_heat_power_kw = lftr_power_kw * (1 - waste_heat_propulsion_eff)
        propellant_savings_t = total_mass_t * 0.5 * (waste_heat_power_kw / 500)
        total_mass_t += total_lftr_mass_t - propellant_savings_t

    # Thorium breeding impact
    if lftr_enabled and thorium_breeding_ratio > 1:
        thorium_mass_t = (total_mass_t * thorium_concentration_ppm / 1e6)
        fuel_doubling_years = np.log(2) / np.log(thorium_breeding_ratio)
        cumulative_f​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​
