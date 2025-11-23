import numpy as np

# =============================================================================
# L1 Sunshade Station-Keeping & Propellant Estimator (Engineering Order-of-Magnitude)
# Updated 2025: Integrates fusion thrust, optimized L1 halo orbits, and beamed microwave power
# Physics are approximate – suitable for system-level comparison only
# =============================================================================

# Constants
S0 = 1362.0                    # Solar constant at 1 AU [W/m²] (2025 SORCE average)
c = 299792458.0                # Speed of light [m/s]
g0 = 9.80665                   # Standard gravity [m/s²]

def srp_pressure(reflectivity=0.95, cos_theta=1.0):
    """
    Solar radiation pressure on a surface [N/m²]
    - reflectivity = 0.0  → perfect absorber  → P = S0/c
    - reflectivity = 1.0  → perfect mirror    → P = 2×S0/c (normal incidence)
    General formula: P = (1 + R) × (S0/c) × <cosθ>
    """
    return (1.0 + reflectivity) * (S0 / c) * cos_theta

def fusion_thrust(mass_kg, delta_v_mps):
    """Calculates fuel mass for fusion thrust (optimized for L1 halo)."""
    energy_req = 0.5 * mass_kg * delta_v_mps**2  # Kinetic energy [J]
    fuel_mass = energy_req / 1e8  # kg, 10⁸ J/kg fusion energy density
    return fuel_mass

def optimize_l1_thrust(mass_kg, power_kw, au_distance, delta_v_target_mps=75.0, isp_s=1e6):
    """Optimizes fuel mass for L1 halo station-keeping."""
    thrust_n = power_kw * 0.1  # 1 kW → 0.1 N (fusion/ion hybrid)
    acceleration_m_s2 = thrust_n / mass_kg if mass_kg > 0 else 0
    time_sec = delta_v_target_mps / acceleration_m_s2 if acceleration_m_s2 > 0 else 0

    if isp_s > 0 and delta_v_target_mps > 0:
        mass_ratio = np.exp(delta_v_target_mps / (isp_s * g0))
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

def l1_stationkeeping(A_m2,
                      areal_density_kgpm2=0.001,
                      reflectivity=0.95,
                      cos_theta_avg=0.95,       # average incidence (halo orbit tilt)
                      isp_sec=300.0,            # baseline (chemical); fusion uses 1e6 s
                      lifetime_yr=10.0,
                      safety_margin=2.0,
                      delta_v_mps=75.0,         # Optimized L1 halo Δv [m/s/year]
                      beamed_microwave_enabled=False,
                      microwave_power_kw=0.0,
                      au_distance=1.0):
    """
    Returns dictionary with engineering estimates, updated with fusion thrust and beamed power.
    """
    mass_dry_kg = areal_density_kgpm2 * A_m2

    P = srp_pressure(reflectivity, cos_theta_avg)  # N/m²
    F_srp = P * A_m2                               # raw SRP force [N]
    F_required = F_srp * safety_margin             # thrust needed [N]

    a = F_required / mass_dry_kg if mass_dry_kg > 0 else 0  # continuous acceleration [m/s²]
    t_sec = lifetime_yr * 365.25 * 24 * 3600
    delta_v_eq = a * t_sec if a > 0 else 0         # equivalent total Δv [m/s]

    # Total power for thrust (fusion + microwave)
    total_power_kw = (50.0 if isp_sec == 1e6 else 0) + microwave_power_kw if beamed_microwave_enabled else (50.0 if isp_sec == 1e6 else 0)
    thrust_data = optimize_l1_thrust(mass_dry_kg, total_power_kw, au_distance, delta_v_mps, isp_sec)
    fuel_mass_kg = thrust_data["fuel_mass_kg"] * lifetime_yr if isp_sec == 1e6 else 0.0

    # Fallback to Tsiolkovsky for non-fusion cases
    if isp_sec != 1e6 and delta_v_eq > 0:
        exp_term = np.exp(-delta_v_eq / (g0 * isp_sec))
        fuel_mass_kg = mass_dry_kg * (1.0 - exp_term)
    else:
        fuel_mass_kg = thrust_data["fuel_mass_kg"] * lifetime_yr if isp_sec == 1e6 else fuel_mass_kg

    propellant_fraction = fuel_mass_kg / mass_dry_kg if mass_dry_kg > 0 else 0.0

    return {
        "area_m2": A_m2,
        "areal_density_kg_m2": areal_density_kgpm2,
        "dry_mass_kg": mass_dry_kg,
        "srp_pressure_Pa": P,
        "srp_force_N": F_srp,
        "thrust_required_N": F_required,
        "acceleration_m_s2": a,
        "lifetime_years": lifetime_yr,
        "equivalent_delta_v_m_s": delta_v_eq,
        "isp_s": isp_sec,
        "propellant_kg": fuel_mass_kg,
        "propellant_fraction": propellant_fraction,
        "total_wet_mass_kg": mass_dry_kg + fuel_mass_kg,
        "beamed_microwave_enabled": beamed_microwave_enabled,
        "microwave_power_kw": microwave_power_kw,
        "optimized_thrust_data": thrust_data
    }

# =============================================================================
# Example runs – typical trade cases
# =============================================================================
if __name__ == "__main__":
    cases = [
        {"A_m2": 1e6, "rho": 0.001, "R": 0.95, "isp": 300,   "yr": 10, "name": "1 km² film, chemical 10 yr"},
        {"A_m2": 1e6, "rho": 0.001, "R": 0.95, "isp": 1e6,   "yr": 10, "name": "1 km² film, fusion 10 yr", "mw_enabled": False, "au": 1.0},
        {"A_m2": 1e6, "rho": 0.0001,"R": 0.95, "isp": 1e6,  "yr": 50, "name": "100 mg/m² graphene, fusion 50 yr", "mw_enabled": True, "au": 10.0, "mw_kw": 900},
        {"A_m2": 100e6,"rho": 0.001, "R": 0.90, "isp": 1e6, "yr": 20, "name": "100 km² sail, fusion 20 yr", "mw_enabled": False, "au": 1.0},
    ]

    print("L1 Sunshade Station-Keeping Estimates (Updated 2025)\n")
    for case in cases:
        res = l1_stationkeeping(A_m2=case["A_m2"],
                                areal_density_kgpm2=case["rho"],
                                reflectivity=case["R"],
                                isp_sec=case["isp"],
                                lifetime_yr=case["yr"],
                                delta_v_mps=75.0,
                                beamed_microwave_enabled=case.get("mw_enabled", False),
                                microwave_power_kw=case.get("mw_kw", 0.0),
                                au_distance=case.get("au", 1.0))
        print(f"─ {case['name']}")
        print(f"   Dry mass           : {res['dry_mass_kg']:8.1f} kg")
        print(f"   SRP force (raw)    : {res['srp_force_N']*1e3:6.2f} mN")
        print(f"   Thrust required    : {res['thrust_required_N']*1e3:6.2f} mN")
        print(f"   Eq. Δv             : {res['equivalent_delta_v_m_s']:6.1f} m/s")
        print(f"   Propellant mass    : {res['propellant_kg']:8.1f} kg ({res['propellant_fraction']:.1%})")
        print(f"   Total wet mass     : {res['total_wet_mass_kg']:8.1f} kg")
        print(f"   Microwave power    : {res​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​
