import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# Dyson Swarm Full Simulation + Monte Carlo + Plotting
# =============================================================================

# -----------------------------
# Simulation parameters
# -----------------------------
years = 2
dt = 1/12  # monthly timestep
steps = int(years / dt)
n_runs = 50  # Monte Carlo simulations

# -----------------------------
# Swarm tile/material parameters
# -----------------------------
materials = {
    "Kapton_SiO2": {"eff": 0.95, "deg": 0.004, "rep_err": 0.02, "area": 1e6, "power": 1.0},
    "Mylar_Al":   {"eff": 0.92, "deg": 0.006, "rep_err": 0.03, "area": 1e6, "power": 0.9},
    "Graphene":   {"eff": 0.98, "deg": 0.002, "rep_err": 0.01, "area": 1e6, "power": 1.1},
}

# Stochastic hazard probabilities
solar_storm_prob = 0.02
micrometeoroid_prob = 0.01
hazard_deg = 0.1

# Self-replication
replication_rate = 0.05
redundancy_factor = 1.1

# Earth and ECS
R_earth = 6.371e6
A_earth = np.pi * R_earth**2
T_eff = 255
ecs_multiplier = 1.8

# -----------------------------
# Monte Carlo simulation
# -----------------------------
all_history_deltaT = []
all_history_power = []

for run in range(n_runs):
    # Initialize swarm state
    tiles = []
    for mat, props in materials.items():
        n_init = 500
        for _ in range(n_init):
            tiles.append({
                "material": mat,
                "eff": props["eff"],
                "area": props["area"],
                "power": props["power"]
            })
    
    # History
    history_deltaT = []
    history_power = []
    
    # Simulation loop
    for step in range(steps):
        # Degrade tiles
        for tile in tiles:
            tile["eff"] *= (1 - materials[tile["material"]]["deg"])
        
        # Apply stochastic hazards
        for tile in tiles:
            if np.random.rand() < solar_storm_prob or np.random.rand() < micrometeoroid_prob:
                tile["eff"] *= (1 - hazard_deg)
        
        # Aggregate shading and power
        eta_total = min(1.0, sum(tile["eff"]*tile["area"] for tile in tiles)/A_earth)
        power_total = sum(tile["eff"]*tile["power"] for tile in tiles)
        dT_eff = -T_eff * 0.25 * eta_total
        dT_surface = dT_eff * ecs_multiplier
        
        history_deltaT.append(dT_surface)
        history_power.append(power_total)
        
        # Self-replication with error
        new_tiles = []
        for tile in tiles:
            n_replicate = int(replication_rate * redundancy_factor)
            for _ in range(n_replicate):
                if np.random.rand() > materials[tile["material"]]["rep_err"]:
                    new_tiles.append(tile.copy())
        tiles.extend(new_tiles)
    
    all_history_deltaT.append(history_deltaT)
    all_history_power.append(history_power)

# -----------------------------
# Convert to arrays for statistics
# -----------------------------
all_history_deltaT = np.array(all_history_deltaT)
all_history_power = np.array(all_history_power)

mean_deltaT = all_history_deltaT.mean(axis=0)
std_deltaT = all_history_deltaT.std(axis=0)
mean_power = all_history_power.mean(axis=0)
std_power = all_history_power.std(axis=0)

months = np.arange(1, steps+1)

# -----------------------------
# Plot results
# -----------------------------
plt.figure(figsize=(12,5))
plt.subplot(1,2,1)
plt.fill_between(months, mean_deltaT - std_deltaT, mean_deltaT + std_deltaT, alpha=0.3)
plt.plot(months, mean_deltaT, label='Mean ΔT')
plt.xlabel("Month")
plt.ylabel("ΔT (K)")
plt.title("Dyson Swarm ΔT over Time (Monte Carlo)")
plt.grid(True)
plt.legend()

plt.subplot(1,2,2)
plt.fill_between(months, mean_power - std_power, mean_power + std_power, alpha=0.3)
plt.plot(months, mean_power, label='Mean Power')
plt.xlabel("Month")
plt.ylabel("Total Power Units")
plt.title("Dyson Swarm Power Output over Time")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()
