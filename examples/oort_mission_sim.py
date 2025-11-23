# oort_mission_sim.py — Full Standalone Interstellar Dyson Swarm Simulator
# 2025 Final — For 1 AU to Oort Cloud (100–10,000 AU) missions
# Run: python oort_mission_sim.py

import numpy as np
import matplotlib.pyplot as plt

S0 = 1362.0  # W/m² at 1 AU (2025 SORCE)

def trajectory_time_yr(au_target, accel_g=0.001):
    """Constant acceleration time to target (years). 0.001g = realistic fusion drive."""
    meters = au_target * 1.496e11
    a = accel_g * 9.80665
    t_sec = np.sqrt(2 * meters / a)
    return t_sec / (365.25 * 86400)

def hybrid_power(au_distance,
                 mission_time_yr,
                 solar_area_m2=1e6,
                 solar_eff=0.20,
                 fusion_base_kw=500.0,
                 beamed_microwave_kw=0.0,
                 relay_hops=0,
                 relay_efficiency=0.90,
                 fusion_half_life_yr=12.0):
    """Deep-space power with multi-hop beamed relay + exponential decay."""
    solar_kw = (S0 / (au_distance ** 2)) * solar_area_m2 * solar_eff / 1000.0

    # Beamed power degrades per hop
    beamed_final_kw = beamed_microwave_kw * (relay_efficiency ** relay_hops)

    # Fusion decays exponentially
    decay_fraction = 0.5 ** (mission_time_yr / fusion_half_life_yr)
    fusion_remaining_kw = fusion_base_kw * decay_fraction

    total_floor_kw = fusion_remaining_kw + beamed_final_kw
    return max(solar_kw, total_floor_kw), decay_fraction

# =============================================================================
# Full Oort Mission Sweep
# =============================================================================
print("OORT CLOUD DYSON SWARM MISSION SIMULATION (2025 Final)\n")
print(f"{'AU':>6} {'Time(yr)':>9} {'Accel':>7} {'Fuel':>8} {'Beamed':>7} {'Hops':>5} {'Power(kW)':>9} {'Fusion%':>8} {'Status'}")
print("-" * 80)

cases = [
    (1.0,   0.001, "p-B11",  500,     0, 0),
    (10.0,  0.001, "p-B11",  800,  1000, 1),
    (50.0,  0.001, "D-He3", 2000,     0, 0),
    (100.0, 0.001, "D-T",   5000,     0, 0),
    (100.0, 0.001, "D-He3", 3000,     0, 0),
    (100.0, 0.001, "Ideal", 2000,     0, 0),
    (500.0, 0.0005,"D-He3", 8000,  5000, 3),
]

results = []
for au, accel, fuel, fusion_in, beamed_in, hops in cases:
    time_yr = trajectory_time_yr(au, accel)
    hl = {"D-T": 12.32, "D-He3": 30.0, "p-B11": 100.0, "Ideal": 500.0}[fuel]

    power, survival = hybrid_power(au, time_yr,
                                   fusion_base_kw=fusion_in,
                                   beamed_microwave_kw=beamed_in,
                                   relay_hops=hops,
                                   fusion_half_life_yr=hl)

    status = "VIABLE" if power >= 50 else "MARGINAL" if power >= 10 else "DEAD"
    print(f"{au:6.0f} {time_yr:9.1f} {accel:7.4f} {fuel:>8} {beamed_in:7.0f} {hops:5} {power:9.0f} {survival*100:7.1f}%  {status}")

    results.append((au, time_yr, power, survival * 100, status))

# Plot
au_vals = [r[0] for r in results]
power_vals = [r[2] for r in results]
plt.figure(figsize=(10, 6))
plt.semilogx(au_vals, power_vals, 'o-', color='#00ff88', linewidth=3, markersize=8)
plt.axhline(50, color='orange', linestyle='--', label="Minimum viable (50 kW)")
plt.axhline(10, color='red', linestyle='--', label="Survival threshold (10 kW)")
plt.title("Oort Cloud Dyson Swarm Power vs Distance (2025 Realistic Model)", fontsize=14)
plt.xlabel("Distance (AU)", fontsize=12)
plt.ylabel("Available Power per 1 km² Occulter (kW)", fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("oort_power_curve.png", dpi=200)
plt.show()

print("\nSimulation complete. Plot saved as 'oort_power_curve.png'")
print("Your Dyson swarm survives the void.")
