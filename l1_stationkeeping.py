import numpy as np

# =============================================================================
# L1 / Deep-Space Station-Keeping & Propellant Estimator
# Final 2025 Version: True exponential fusion fuel decay (half-life based)
# =============================================================================

S0 = 1362.0
c = 299792458.0
g0 = 9.80665

def srp_pressure(reflectivity=0.95, cos_theta=1.0):
    return (1.0 + reflectivity) * (S0 / c) * cos_theta

def hybrid_power(au_distance,
                 mission_time_yr,
                 solar_area_m2=1e6,
                 solar_eff=0.20,
                 fusion_base_kw=100.0,
                 beamed_microwave_kw=0.0,
                 fusion_half_life_yr=12.0):
    solar_kw = (S0 / (au_distance ** 2)) * solar_area_m2 * solar_eff / 1000.0
    decay_fraction = 0.5 ** (mission_time_yr / fusion_half_life_yr)
    fusion_available_kw = fusion_base_kw * decay_fraction
    return max(solar_kw, fusion_available_kw + beamed_microwave_kw)

def optimize_l1_thrust(mass_kg, power_kw, delta_v_mps=75.0, isp_s=1e6):
    thrust_n = power_kw * 0.10
    a = thrust_n / mass_kg if mass_kg > 0 else 0
    fuel_kg = mass_kg * (np.exp(delta_v_mps / (isp_s * g0)) - 1) if delta_v_mps > 0 else 0.0
    return {"thrust_n": thrust_n, "fuel_kg": fuel_kg, "power_kw": power_kw}

def l1_stationkeeping(A_m2=1e6,
                      areal_density_kgpm2=0.0005,
                      reflectivity=0.97,
                      mission_time_yr=100.0,
                      lifetime_yr=100.0,
                      au_distance=100.0,
                      fusion_base_kw=200.0,
                      beamed_microwave_kw=0.0,
                      fusion_half_life_yr=12.0,
                      annual_delta_v_mps=75.0):
    mass_dry_kg = areal_density_kgpm2 * A_m2
    P = srp_pressure(reflectivity, 0.95)
    F_srp = P * A_m2
    F_req = F_srp * 2.0
    a_req = F_req / mass_dry_kg

    power_kw = hybrid_power(au_distance=au_distance,
                            mission_time_yr=mission_time_yr,
                            solar_area_m2=A_m2,
                            fusion_base_kw=fusion_base_kw,
                            beamed_microwave_kw=beamed_microwave_kw,
                            fusion_half_life_yr=fusion_half_life_yr)

    thrust = optimize_l1_thrust(mass_dry_kg, power_kw, annual_delta_v_mps, 1e6)
    total_fuel_kg = thrust["fuel_kg"] * lifetime_yr

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

# =============================================================================
# 100-Year Oort Cloud Mission Simulations
# =============================================================================
if __name__ == "__main__":
    print("100-Year Oort Cloud Swarm Deployment Scenarios (Exponential Decay)\n")
    print(f"{'AU':>4} {'Time':>6} {'Half-Life':>8} {'Fusion In':>8} {'Power Out':>8} {'Fuel Left':>8} {'Prop/Mass':>8}")
    print("-" * 70)

    cases = [
        (1.0,   1,   12,  100,  0),
        (10.0, 10,   12,  150,  800),
        (50.0, 50,   12,  300,  0),
        (100.0,100,  12,  500,  0),
        (100.0,100,  18,  400,  0),   # Better fuel (Li-6 breeding)
        (100.0,100, 100,  300,  0),   # p-B11 dream fuel
    ]

    for au, t, hl, fusion, beamed in cases:
        res = l1_stationkeeping(au_distance=au,
                                mission_time_yr=t,
                                fusion_base_kw=fusion,
                                beamed_microwave_kw=beamed,
                                fusion_half_life_yr=hl)
        print(f"{au:4.0f} {t:6.0f} {hl:8.0f} {fusion:8.0f} {res['power_kw']:8.0f} "
              f"{res['fusion_survival']*100:7.1f}% {res['propellant_fraction']*100:7.1f}%")
