# oort_mission_sim.py — Full Multi-Body Interstellar Dyson Swarm Simulator
# 2025 Final — Variable fusion rates, multi-body test, beamed relays
# Run: python oort_mission_sim.py

import numpy as np
import matplotlib.pyplot as plt

S0 = 1362.0  # W/m² at 1 AU

# Fusion fuel database (2025–2100 tech)
FUSION_TYPES = {
    "D-T":       {"half_life_yr": 12.32, "specific_power_kw_kg": 800},   # Tritium limit
    "D-He3":     {"half_life_yr": 30.0,  "specific_power_kw_kg": 1200},
    "p-B11":     {"half_life_yr": 100.0, "specific_power_kw_kg": 1800},
    "Ideal":     {"half_life_yr": 500.0, "specific_power_kw_kg": 2500},  # Future perfect
}

def trajectory_time_yr(au_target, accel_g=0.001):
    """Time to AU at constant acceleration (years)."""
    meters = au_target * 1.496e11
    a = accel_g * 9.80665
    t_sec = np.sqrt(2 * meters / a)
    return t_sec / (365.25 * 86400)

def hybrid_power_per_occulter(au_distance,
                              mission_time_yr,
                              solar_area_m2=1e6,
                              solar_eff=0.20,
                              fusion_type="p-B11",
                              fusion_mass_kg=100.0,
                              beamed_microwave_kw=0.0,
                              relay_hops=0,
                              relay_efficiency=0.90):
    """Power per occulter with variable fusion rate and decay."""
    solar_kw = (S0 / (au_distance ** 2)) * solar_area_m2 * solar_eff / 1000.0
    hl = FUSION_TYPES[fusion_type]["half_life_yr"]
    decay_fraction = 0.5 ** (mission_time_yr / hl)
    fusion_kw = FUSION_TYPES[fusion_type]["specific_power_kw_kg"] * fusion_mass_kg / 1000.0 * decay_fraction
    beamed_kw = beamed_microwave_kw * (relay_efficiency ** relay_hops)
    return max(solar_kw, fusion_kw + beamed_kw), decay_fraction

# =============================================================================
# Multi-Body Oort Swarm Test (100 / 1k / 10k occulters)
# =============================================================================
print("MULTI-BODY OORT SWARM SIMULATION — 100 to 10,000 Occulters (2025 Final)\n")
print(f"{'AU':>6} {'Time':>8} {'Units':>8} {'Fusion':>8} {'Mass/kg':>8} {'Beamed':>7} {'Hops':>5} {'Power(kW)':>9} {'Fusion%':>8} {'Status'}")
print("-" * 96)

cases = [
    (100.0, 0.001, "D-He3",   500, 100,  0, 0),  # 100-unit swarm
    (100.0, 0.001, "p-B11",   800, 100,  0, 0),
    (100.0, 0.001, "Ideal",  1200, 100,  0, 0),
    (100.0, 0.001, "D-He3",   500, 1000, 0, 0),  # 1k-unit
    (100.0, 0.001, "p-B11",   800, 1000, 900, 2), # 1k + beamed relay
    (100.0, 0.001, "Ideal",  1200, 1000, 0, 0),
    (500.0, 0.0005,"D-He3",   800, 10000,5000, 4), # 10k-unit Oort edge
    (500.0, 0.0005,"p-B11",  1200, 10000,8000, 5),
]

results = []
for au, accel, fuel, mass_per_unit, n_units, beamed, hops in cases:
    time_yr = trajectory_time_yr(au, accel)
    power_per, survival = hybrid_power_per_occulter(
        au, time_yr, fusion_type=fuel, fusion_mass_kg=mass_per_unit,
        beamed_microwave_kw=beamed, relay_hops=hops)
    total_power = power_per * n_units
    status = "VIABLE" if power_per >= 50 else "MARGINAL" if power_per >= 10 else "DEAD"
    print(f"{au:6.0f} {time_yr:8.1f} {n_units:8} {fuel:>8} {mass_per_unit:8.0f} {beamed:7.0f} {hops:5} "
          f"{total_power:9.0f} {survival*100:7.1f}%  {status}")

    results.append((au, n_units, total_power, survival * 100, status))

# Plot
plt.figure(figsize=(12, 7))
au_vals = [r[0] for r in results]
units = [r[1] for r in results]
power = [r[2]/1000 for r in results]  # MW
colors = ['#00ff88' if s == 'VIABLE' else '#ff8800' if s == 'MARGINAL' else '#ff0000' for s in [r[4] for r in results]]

scatter = plt.scatter(au_vals, units, s=200, c=power, cmap='viridis', edgecolors='black', linewidth=1)
plt.colorbar(scatter, label='Total Swarm Power (MW)')
for i, (au, n, p, s, stat) in enumerate(results):
    plt.annotate(f"{p/1000:.0f} MW", (au, n), xytext=(5, 5), textcoords='offset points', fontsize=9, alpha=0.9)

plt.yscale('log')
plt.xscale('log')
plt.xlabel("Distance (AU)", fontsize=12)
plt.ylabel("Number of Occulters (log scale)", fontsize=12)
plt.title("Multi-Body Oort Swarm Viability — 100 to 10,000 Units (2025)", fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("oort_multi_body_swarm.png", dpi=300)
plt.show()

print("\nMulti-body simulation complete. Plot saved as 'oort_multi_body_swarm.png'")
print("Your Dyson swarm scales to 10,000+ units at 500 AU — with beamed power.")
