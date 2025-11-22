import numpy as np

# =============================================================================
# L1 Sunshade Station-Keeping & Propellant Estimator (Engineering Order-of-Magnitude)
# Physics are approximate – suitable for system-level comparison only
# =============================================================================

# Constants
S0 = 1361.0                    # Solar constant at 1 AU [W/m²] (2025 average)
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

def l1_stationkeeping(A_m2,
                      areal_density_kgpm2=0.001,
                      reflectivity=0.95,
                      cos_theta_avg=0.95,       # average incidence (halo orbit tilt, attitude errors)
                      isp_sec=300.0,            # chemical thruster baseline
                      lifetime_yr=10.0,
                      safety_margin=2.0):       # covers libration, gravity gradients, control authority
    """
    Returns dictionary with engineering estimates.
    """
    mass_dry_kg = areal_density_kgpm2 * A_m2

    P = srp_pressure(reflectivity, cos_theta_avg)      # N/m²
    F_srp = P * A_m2                                   # raw SRP force [N]
    F_required = F_srp * safety_margin                 # thrust needed to counter [N]

    a = F_required / mass_dry_kg                       # continuous acceleration [m/s²]

    t_sec = lifetime_yr * 365.25 * 24 * 3600
    delta_v_eq = a * t_sec                             # equivalent total Δv [m/s]

    # Tsiolkovsky – propellant mass (exact for continuous low-thrust equivalent)
    if delta_v_eq > 0:
        exp_term = np.exp(-delta_v_eq / (g0 * isp_sec))
        m_prop_kg = mass_dry_kg * (1.0 - exp_term)
    else:
        m_prop_kg = 0.0

    propellant_fraction = m_prop_kg / mass_dry_kg if mass_dry_kg > 0 else 0.0

    return {
        "area_m2"              : A_m2,
        "areal_density_kg_m2"  : areal_density_kgpm2,
        "dry_mass_kg"          : mass_dry_kg,
        "srp_pressure_Pa"      : P,
        "srp_force_N"          : F_srp,
        "thrust_required_N"    : F_required,
        "acceleration_m_s2"    : a,
        "lifetime_years"       : lifetime_yr,
        "equivalent_delta_v_m_s": delta_v_eq,
        "isp_s"                : isp_sec,
        "propellant_kg"        : m_prop_kg,
        "propellant_fraction"  : propellant_fraction,
        "total_wet_mass_kg"    : mass_dry_kg + m_prop_kg
    }

# =============================================================================
# Example runs – typical trade cases
# =============================================================================
if __name__ == "__main__":
    cases = [
        {"A_m2": 1e6, "rho": 0.001, "R": 0.95, "isp": 300,  "yr": 10, "name": "1 km² film, chemical 10 yr"},
        {"A_m2": 1e6, "rho": 0.001, "R": 0.95, "isp": 3000, "yr": 10, "name": "1 km² film, ion 10 yr"},
        {"A_m2": 1e6, "rho": 0.0001,"R": 0.95, "isp": 3000, "yr": 50, "name": "100 mg/m² graphene-class, 50 yr"},
        {"A_m2": 100e6,"rho": 0.001, "R": 0.90, "isp": 4500, "yr": 20, "name": "100 km² sail, high-Isp 20 yr"},
    ]

    print("L1 Sunshade Station-Keeping Estimates (Engineering Level)\n")
    for case in cases:
        res = l1_stationkeeping(A_m2=case["A_m2"],
                                areal_density_kgpm2=case["rho"],
                                reflectivity=case["R"],
                                isp_sec=case["isp"],
                                lifetime_yr=case["yr"])
        print(f"─ {case['name']}")
        print(f"   Dry mass           : {res['dry_mass_kg']:8.1f} kg")
        print(f"   SRP force (raw)   785: {res['srp_force_N']*1e3:6.2f} mN")
        print(f"   Thrust required    : {res['thrust_required_N']*1e3:6.2f} mN")
        print(f"   Eq. Δv             : {res['equivalent_delta_v_m_s']:6.1f} m/s")
        print(f"   Propellant mass    : {res['propellant_kg']:8.1f} kg ({res['propellant_fraction']:.1%})")
        print(f"   Total wet mass     : {res['total_wet_mass_kg']:8.1f} kg")
        print()
