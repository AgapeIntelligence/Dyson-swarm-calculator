import numpy as np

# =============================================================================
# L1 Sunshade Constellation Optimizer
# Pure functional implementation – calculates minimum number of sunshades
# for a desired fractional reduction in solar input (eta_target)
# =============================================================================

# Constants
R_earth = 6.371e6                          # Earth radius [m]
A_earth = np.pi * R_earth**2               # Earth disk area [m²]
T_eff = 255.0                              # Effective temperature [K]
ecs_multiplier = 1.8                       # Surface response factor (approx from GCMs/IPCC)

def sunshade_optimizer(eta_target=0.018,
                       A_shade_m2=1e6,             # 1 km² per shade
                       kappa=0.95,                 # optical efficiency
                       areal_density_kgpm2=0.001,  # kg/m² (1 g/m² baseline)
                       payload_to_l1_t=50.0,       # effective tons per launch to L1
                       flights_per_year=20.0):
    """
    Returns a dictionary with full engineering estimates for the constellation.
    """
    N_sat = eta_target * A_earth / (A_shade_m2 * kappa)

    mass_per_sat_kg = A_shade_m2 * areal_density_kgpm2
    total_mass_t = N_sat * mass_per_sat_kg / 1000.0

    launches = total_mass_t / payload_to_l1_t
    years_constant = launches / flights_per_year

    # Temperature impact
    dT_eff = -T_eff * 0.25 * eta_target
    dT_surface = dT_eff * ecs_multiplier

    return {
        "eta_target": eta_target,
        "N_satellites": N_sat,
        "shade_area_per_sat_km2": A_shade_m2 / 1e6,
        "total_shade_area_km2": N_sat * A_shade_m2 / 1e6,
        "areal_density_g_m2": areal_density_kgpm2 * 1000,
        "mass_per_satellite_kg": mass_per_sat_kg,
        "total_mass_Gt": total_mass_t / 1e9,
        "launches_required": launches,
        "years_at_20_flights_per_year": years_constant,
        "delta_T_effective_K": dT_eff,
        "delta_T_surface_K": dT_surface,
    }

# =============================================================================
# Example usage
# =============================================================================
if __name__ == "__main__":
    cases = [
        ("Climate offset (1.8%)", 0.018),
        ("Strong cooling (10%)", 0.10),
        ("Half Dyson (50%)", 0.50),
        ("Full Dyson (100%)", 1.00),
    ]

    print("L1 Sunshade Constellation Requirements\n")
    for name, eta in cases:
        res = sunshade_optimizer(eta_target=eta,
                                 A_shade_m2=1e6,
                                 areal_density_kgpm2=0.0005)  # optimistic 0.5 g/m²
        print(f"{name}")
        print(f"   Satellites      : {res['N_satellites']/1e6:6.2f} million")
        print(f"   Total mass      : {res['total_mass_Gt']:6.2f} Gt")
        print(f"   Launches        : {res['launches_required']/1000:6.1f} k")
        print(f"   Time (20/yr)    : {res['years_at_20_flights_per_year']:.0f} years")
        print(f"   ΔT_surface      : {res['delta_T_surface_K']:+5.1f} K")
        print()
