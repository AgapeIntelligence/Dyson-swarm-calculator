import numpy as np

# =============================================================================
# L1 / Deep-Space Station-Keeping & Propellant Estimator — 2025 Final
# True exponential fusion fuel decay via half-life (for 100–1000 yr missions)
# =============================================================================

S0 = 1362.0
g0 = 9.80665

def srp_pressure(reflectivity=0.95, cos_theta=1.0):
    return (1.0 + reflectivity) * (S0 / 299792458.0) * cos_theta

def hybrid_power(au_distance,
                 mission_time_yr,
                 solar_area_m2=1e6,
                 solar_eff=0.20,
                 fusion_base_kw=200.0,
                 beamed_microwave_kw=0.0,
                 fusion_half_life_yr=12.0):
    solar_kw = (S0 / (au_distance ** 2)) * solar_area_m2 * solar_eff / 1000.0
    decay_fraction = 0.5 ** (mission_time_yr / fusion_half_life_yr)
    fusion_remaining_kw = fusion_base_kw * decay_fraction
    return max(solar_kw, fusion_remaining_kw + beamed_microwave_kw)

def optimize_l1_thrust(mass_kg, power_kw, delta_v_mps=75.0, isp_s=1e6):
    thrust_n = power_kw * 0.10
    fuel_kg = mass_kg * (np.exp(delta_v_mps / (isp_s * g0)) - 1) if delta_v_mps > 0 else 0.0
    return {"thrust_n": thrust_n, "annual_fuel_kg": fuel_kg}

def l1_stationkeeping(A_m2=1e6,
                      areal_density_kgpm2=0.0005,
                      reflectivity=0.97,
                      mission_time_yr=100.0,
                      lifetime_yr=100.0,
                      au_distance=100.0,
                      fusion_base_kw=500.0,
                      beamed_microwave_kw=0.0,
                      fusion_half_life_yr=12.0,
                      annual_delta_v_mps=75.0):
    mass_dry_kg = areal_density_kgpm2 * A_m2
    power_kw = hybrid_power(au_distance, mission_time_yr, A_m2, 0.20,
                            fusion_base_kw, beamed_microwave_kw, fusion_half_life_yr)
    thrust = optimize_l1_thrust(mass_dry_kg, power_kw, annual_delta_v_mps, 1e6)
    total_fuel_kg = thrust["annual_fuel_kg"] * lifetime_yr

    return {
        "au_distance": au_distance,
        "mission_time_yr": mission_time_yr,
        "power_kw": power_kw,
        "fusion_survival": 0.5 ** (mission_time_yr / fusion_half_life_yr),
        "dry_mass_kg": mass_dry_kg,
        "total_fuel_kg": total_fuel_kg,
        "wet_mass_kg": mass_dry_kg + total_fuel_kg,
        "propellant_fraction": total_fuel_kg / mass_dry_kg,
        "thrust_n": thrust["thrust_n"]
    }

# Example: 100-yr Oort mission
if __name__ == "__main__":
    print("Oort Cloud Station-Keeping (100-yr mission)\n")
    res = l1_stationkeeping(au_distance=100, mission_time_yr=100,
                            fusion_base_kw=800, fusion_half_life_yr=18)
    print(f"Power: {res['power_kw']:.0f} kW | Fuel left: {res['fusion_survival']:.1%} | Propellant: {res['propellant_fraction']:.1%}")
