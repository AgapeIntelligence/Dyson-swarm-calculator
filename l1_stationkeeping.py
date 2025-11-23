import numpy as np

# =============================================================================
# L1 / Deep-Space Station-Keeping & Propellant Estimator
# Updated 2025: Full time-based fusion fuel decay + beamed microwave support
# Physics are approximate — suitable for system-level and interstellar architecture trades
# =============================================================================

# Constants (2025 values)
S0 = 1362.0                    # Solar constant at 1 AU [W/m²]
c = 299792458.0                # Speed of light [m/s]
g0 = 9.80665                   # Standard gravity [m/s²]

def srp_pressure(reflectivity=0.95, cos_theta=1.0):
    """Solar radiation pressure [N/m²]: P = (1 + R) * (S0/c) * <cosθ>"""
    return (1.0 + reflectivity) * (S0 / c) * cos_theta

def hybrid_power(au_distance,
                 solar_area_m2=1e6,
                 solar_eff=0.20,
                 fusion_base_kw=100.0,
                 beamed_microwave_kw=0.0,
                 travel_time_yr=None,
                 fuel_decay_per_year=0.008):
    """
    Deep-space hybrid power model with time-based fuel degradation.
    - Solar: 1/au² scaling
    - Fusion: degrades exponentially with mission duration
    - Beamed microwave: constant (no decay)
    """
    solar_kw = (S0 / (au_distance ** 2)) * solar_area_m2 * solar_eff / 1000.0

    fusion_kw = fusion_base_kw
    if travel_time_yr is not None:
        surviving_fraction = np.exp(-fuel_decay_per_year * travel_time_yr)
        fusion_kw *= surviving_fraction

    floor_kw = fusion_kw + beamed_microwave_kw
    return max(solar_kw, floor_kw)

def optimize_l1_thrust(mass_kg,
                       power_kw,
                       delta_v_target_mps=75.0,
                       isp_s=1e6):
    """
    High-Isp thrust from available power (fusion/ion hybrid).
    Returns annual fuel mass for given Δv target.
    """
    thrust_n = power_kw * 0.10                    # 1 kW → 0.10 N (realistic 2025–2100)
    a_m_s2 = thrust_n / mass_kg if mass_kg > 0 else 0

    # Tsiolkovsky rocket equation for high-Isp electric/fusion propulsion
    if isp_s > 0 and delta_v_target_mps > 0:
        mass_ratio = np.exp(delta_v_target_mps / (isp_s * g0))
        fuel_mass_kg = mass_kg * (mass_ratio - 1.0)
    else:
        fuel_mass_kg = 0.0

    return {
        "power_kw": power_kw,
        "thrust_n": thrust_n,
        "acceleration_m_s2": a_m_s2,
        "annual_fuel_kg": fuel_mass_kg,
        "delta_v_mps": delta_v_target_mps
    }

def l1_stationkeeping(A_m2,
                      areal_density_kgpm2=0.0005,
                      reflectivity=0.95,
                      cos_theta_avg=0.95,
                      isp_sec=1e6,                      # 1e6 = fusion, <1e5 = chemical/ion
                      lifetime_yr=50.0,
                      safety_margin=2.0,
                      annual_delta_v_mps=75.0,          # Optimized L1 halo or deep-space station-keeping
                      au_distance=1.0,
                      fusion_base_kw=100.0,
                      beamed_microwave_kw=0.0,
                      travel_time_yr=None,
                      fuel_decay_per_year=0.008):
    """
    Full deep-space station-keeping estimator with fuel decay.
    travel_time_yr = time from Earth to deployment (e.g., 100 yr to 100 AU)
    """
    mass_dry_kg = areal_density_kgpm2 * A_m2

    # SRP force and required counter-thrust
    P = srp_pressure(reflectivity, cos_theta_avg)
    F_srp = P * A_m2
    F_required = F_srp * safety_margin
    a_req = F_required / mass_dry_kg

    # Total available power (with decay)
    power_kw = hybrid_power(au_distance=au_distance,
                            solar_area_m2=A_m2,
                            solar_eff=0.20,
                            fusion_base_kw=fusion_base_kw,
                            beamed_microwave_kw=beamed_microwave_kw,
                            travel_time_yr=travel_time_yr,
                            fuel_decay_per_year=fuel_decay_per_year)

    # Annual thrust & fuel requirement
    thrust_data = optimize_l1_thrust(mass_dry_kg, power_kw, annual_delta_v_mps, isp_sec)
    total_fuel_kg = thrust_data["annual_fuel_kg"] * lifetime_yr

    # Chemical fallback (rarely used)
    if isp_sec < 1e5:
        dv_total = a_req * lifetime_yr * 365.25 * 86400
        total_fuel_kg = mass_dry_kg * (1.0 - np.exp(-dv_total / (g0 * isp_sec)))

    propellant_fraction = total_fuel_kg / mass_dry_kg if mass_dry_kg > 0 else 0.0

    return {
        "area_m2": A_m2,
        "areal_density_kg_m2": areal_density_kgpm2,
        "dry_mass_kg": mass_dry_kg,
        "au_distance": au_distance,
        "travel_time_yr": travel_time_yr,
        "power_available_kw": power_kw,
        "srp_force_N": F_srp,
        "thrust_required_N": F_required,
        "acceleration_req_m_s2": a_req,
        "lifetime_years": lifetime_yr,
        "annual_delta_v_m_s": annual_delta_v_mps,
        "isp_s": isp_sec,
        "annual_fuel_kg": thrust_data["annual_fuel_kg"],
        "total_propellant_kg": total_fuel_kg,
        "propellant_fraction": propellant_fraction,
        "total_wet_mass_kg": mass_dry_kg + total_fuel_kg,
        "fusion_survival_fraction": np.exp(-fuel_decay_per_year * (travel_time_yr or 0)),
        "beamed_microwave_kw": beamed_microwave_kw,
        "thrust_data": thrust_data
    }

# =============================================================================
# Example: 1 AU → 100 AU swarm expansion
# =============================================================================
if __name__ == "__main__":
    cases = [
        {"name": "1 km² @ 1 AU (inner swarm)",      "au": 1.0,   "time": 1,    "fusion": 100, "beamed": 0},
        {"name": "1 km² @ 10 AU (mid-zone)",        "au": 10.0,  "time": 10,   "fusion": 100, "beamed": 900},
        {"name": "1 km² @ 50 AU (Kuiper edge)",     "au": 50.0,  "time": 50,   "fusion": 150, "beamed": 0},
        {"name": "1 km² @ 100 AU (long-haul)",      "au": 100.0, "time": 100,  "fusion": 200, "beamed": 0},
    ]

    print("Deep-Space Station-Keeping with Fusion Fuel Decay (2025 Model)\n")
    for case in cases:
        res = l1_stationkeeping(A_m2=1e6,
                                areal_density_kgpm2=0.0005,
                                reflectivity=0.97,
                                isp_sec=1e6,
                                lifetime_yr=100,
                                au_distance=case["au"],
                                fusion_base_kw=case["fusion"],
                                beamed_microwave_kw=case["beamed"],
                                travel_time_yr=case["time"])

        print(f"─ {case['name']}")
        print(f"   Travel time        : {res['travel_time_yr']:4.0f} yr")
        print(f"   Power available    : {res['power_available_kw']:6.1f} kW")
        print(f"   Fusion survival    : {res['fusion_survival_fraction']:.1%}")
        print(f"   Dry mass           : {res['dry_mass_kg']:7.0f} kg")
        print(f"   Total propellant   : {res['total_propellant_kg']:7.0f} kg ({res['propellant_fraction']:.2%})")
        print(f"   Wet mass           : {res['total_wet_mass_kg']:7.0f} kg")
        print()
