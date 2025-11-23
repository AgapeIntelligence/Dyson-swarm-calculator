import numpy as np

# =============================================================================
# L1 Sunshade Station-Keeping & Propellant Estimator (Engineering Order-of-Magnitude)
# Updated 2025: Deep-space hybrid power (solar + fusion + beamed microwave floor)
# Physics are approximate – suitable for system-level comparison only
# =============================================================================

# Constants (2025 values)
S0 = 1362.0                    # Solar constant at 1 AU [W/m²] (SORCE 2024 avg)
c = 299792458.0                # Speed of light [m/s]
g0 = 9.80665                   # Standard gravity [m/s²]

def srp_pressure(reflectivity=0.95, cos_theta=1.0):
    """Solar radiation pressure [N/m²]: P = (1 + R) * (S0/c) * <cosθ>"""
    return (1.0 + reflectivity) * (S0 / c) * cos_theta

def hybrid_power(au_distance,
                 solar_area_m2=1e6,
                 solar_eff=0.20,
                 fusion_base_kw=50.0,
                 beamed_microwave_kw=0.0):
    """
    Deep-space hybrid power model.
    - Solar scales as 1/au²
    - Fusion + beamed microwave provide constant floor
    Returns total available power in kW per occulter (or per km²)
    """
    solar_kw = (S0 / (au_distance ** 2)) * solar_area_m2 * solar_eff / 1000.0
    floor_kw = fusion_base_kw + beamed_microwave_kw
    return max(solar_kw, floor_kw)

def fusion_thrust(mass_kg, delta_v_mps):
    """Fuel mass for pure fusion propulsion (10⁸ J/kg energy density)."""
    energy_req = 0.5 * mass_kg * delta_v_mps**2
    return energy_req / 1e8  # kg

def optimize_l1_thrust(mass_kg, power_kw, delta_v_target_mps=75.0, isp_s=1e6):
    """High-Isp thrust from available power (fusion/ion hybrid)."""
    thrust_n = power_kw * 0.1                     # 1 kW → ~0.1 N (realistic)
    a_m_s2 = thrust_n / mass_kg if mass_kg > 0 else 0

    if isp_s > 0 and delta_v_target_mps > 0:
        mass_ratio = np.exp(delta_v_target_mps / (isp_s * g0))
        fuel_mass_kg = mass_kg * (mass_ratio - 1)
    else:
        fuel_mass_kg = 0.0

    return {
        "power_kw": power_kw,
        "thrust_n": thrust_n,
        "acceleration_m_s2": a_m_s2,
        "fuel_mass_kg": fuel_mass_kg,
        "delta_v_mps": delta_v_target_mps
    }

def l1_stationkeeping(A_m2,
                      areal_density_kgpm2=0.001,
                      reflectivity=0.95,
                      cos_theta_avg=0.95,
                      isp_sec=300.0,                     # 300 = chemical, 1e6 = fusion
                      lifetime_yr=10.0,
                      safety_margin=2.0,
                      delta_v_mps=75.0,                  # Optimized annual Δv [m/s/yr]
                      au_distance=1.0,
                      fusion_base_kw=50.0,               # Onboard p-B11 floor
                      beamed_microwave_kw=0.0):          # Beamed power from inner swarm
    """
    Full deep-space station-keeping estimator.
    """
    mass_dry_kg = areal_density_kgpm2 * A_m2

    # SRP force & required counter-thrust
    P = srp_pressure(reflectivity, cos_theta_avg)
    F_srp = P * A_m2
    F_required = F_srp * safety_margin
    a_req = F_required / mass_dry_kg

    # Total available power (solar + fusion + beamed)
    power_kw = hybrid_power(au_distance=au_distance,
                            solar_area_m2=A_m2,
                            solar_eff=0.20,
                            fusion_base_kw=fusion_base_kw,
                            beamed_microwave_kw=beamed_microwave_kw)

    # Thrust & fuel calculation
    thrust_data = optimize_l1_thrust(mass_dry_kg, power_kw, delta_v_mps, isp_sec)
    annual_fuel_kg = thrust_data["fuel_mass_kg"]
    total_fuel_kg = annual_fuel_kg * lifetime_yr

    # Fallback Tsiolkovsky for chemical/ion (rarely used now)
    if isp_sec < 1e5:
        dv_total = a_req * lifetime_yr * 365.25 * 86400
        total_fuel_kg = mass_dry_kg * (1.0 - np.exp(-dv_total / (g0 * isp_sec)))

    propellant_fraction = total_fuel_kg / mass_dry_kg if mass_dry_kg > 0 else 0.0

    return {
        "area_m2": A_m2,
        "areal_density_kg_m2": areal_density_kgpm2,
        "dry_mass_kg": mass_dry_kg,
        "au_distance": au_distance,
        "power_available_kw": power_kw,
        "srp_pressure_Pa": P,
        "srp_force_N": F_srp,
        "thrust_required_N": F_required,
        "acceleration_req_m_s2": a_req,
        "lifetime_years": lifetime_yr,
        "annual_delta_v_m_s": delta_v_mps,
        "isp_s": isp_sec,
        "annual_fuel_kg": annual_fuel_kg,
        "total_propellant_kg": total_fuel_kg,
        "propellant_fraction": propellant_fraction,
        "total_wet_mass_kg": mass_dry_kg + total_fuel_kg,
        "beamed_microwave_kw": beamed_microwave_kw,
        "thrust_data": thrust_data
    }

# =============================================================================
# Example runs – from 1 AU to Kuiper Belt
# =============================================================================
if __name__ == "__main__":
    cases = [
        {"A_m2": 1e6, "rho": 0.0005, "R": 0.95, "au": 1.0,  "fusion": 50, "mw": 0,    "name": "1 km² @ 1 AU (solar dominant)"},
        {"A_m2": 1e6, "rho": 0.0005, "R": 0.95, "au": 5.0,  "fusion": 50, "mw": 0,    "name": "1 km² @ 5 AU (crossover)"},
        {"A_m2": 1e6, "rho": 0.0005, "R": 0.95, "au": 10.0, "fusion": 50, "mw": 900,  "name": "1 km² @ 10 AU (beamed + fusion)"},
        {"A_m2": 1e6, "rho": 0.0001, "R": 0.98, "au": 50.0, "fusion": 100,"mw": 0,    "name": "Graphene-class @ 50 AU (pure fusion)"},
    ]

    print("L1 / Deep-Space Station-Keeping Estimates (2025 Hybrid Power Model)\n")
    for case in cases:
        res = l1_stationkeeping(A_m2=case["A_m2"],
                                areal_density_kgpm2=case["rho"],
                                reflectivity=case["R"],
                                isp_sec=1e6,
                                lifetime_yr=50,
                                au_distance=case["au"],
                                fusion_base_kw=case["fusion"],
                                beamed_microwave_kw=case["mw"])

        print(f"─ {case['name']}")
        print(f"   Power available    : {res['power_available_kw']:6.1f} kW")
        print(f"   Dry mass           : {res['dry_mass_kg']:8.1f} kg")
        print(f"   SRP force          : {res['srp_force_N']*1e3:6.2f} mN")
        print(f"   Thrust required    : {res['thrust_required_N']*1e3:6.2f} mN")
        print(f"   Total propellant   : {res['total_propellant_kg']:8.1f} kg ({res['propellant_fraction']:.2%})")
        print(f"   Wet mass           : {res['total_wet_mass_kg']:8.1f} kg")
        print()
