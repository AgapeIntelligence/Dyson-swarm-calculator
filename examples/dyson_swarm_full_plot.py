import numpy as np
from scipy.optimize import differential_evolution
import matplotlib.pyplot as plt

# -----------------------------
# Dyson Swarm Monte Carlo + Optimization + Full Plotting
# -----------------------------

years = 2
dt = 1/12
steps = int(years/dt)
n_runs = 20

# Earth constants
R_earth = 6.371e6
A_earth = np.pi * R_earth**2
T_eff = 255
ecs_multiplier = 1.8

# Materials
materials = {
    "Kapton_SiO2": {"eff": 0.95, "deg": 0.004, "rep_err": 0.02, "area": 1e6, "power": 1.0},
    "Mylar_Al":   {"eff": 0.92, "deg": 0.006, "rep_err": 0.03, "area": 1e6, "power": 0.9},
    "Graphene":   {"eff": 0.98, "deg": 0.002, "rep_err": 0.01, "area": 1e6, "power": 1.1},
}

solar_storm_prob = 0.02
micrometeoroid_prob = 0.01
hazard_deg = 0.1

# -----------------------------
# Simulation function
# -----------------------------
def run_sim(params, return_history=False):
    replication_rate, redundancy_factor, kap_frac, mylar_frac = params
    graph_frac = max(0, 1 - kap_frac - mylar_frac)
    
    tile_counts = {
        "Kapton_SiO2": int(500 * kap_frac),
        "Mylar_Al":   int(500 * mylar_frac),
        "Graphene":   int(500 * graph_frac)
    }
    
    mean_dT = []
    mean_power = []
    all_histories = []

    for run in range(n_runs):
        tiles = []
        for mat, n in tile_counts.items():
            for _ in range(n):
                tiles.append({"material": mat,
                              "eff": materials[mat]["eff"],
                              "area": materials[mat]["area"],
                              "power": materials[mat]["power"]})
        history_deltaT = []
        history_power = []
        history_tiles = []
        history_eta = []

        for step in range(steps):
            # degrade
            for tile in tiles:
                tile["eff"] *= (1 - materials[tile["material"]]["deg"])
            # stochastic hazards
            for tile in tiles:
                if np.random.rand() < solar_storm_prob or np.random.rand() < micrometeoroid_prob:
                    tile["eff"] *= (1 - hazard_deg)
            # aggregate
            eta_total = min(1.0, sum(tile["eff"]*tile["area"] for tile in tiles)/A_earth)
            power_total = sum(tile["eff"]*tile["power"] for tile in tiles)
            dT_eff = -T_eff * 0.25 * eta_total
            dT_surface = dT_eff * ecs_multiplier
            # record
            history_deltaT.append(dT_surface)
            history_power.append(power_total)
            history_tiles.append(len(tiles))
            history_eta.append(eta_total)
            # replication
            new_tiles = []
            for tile in tiles:
                n_repl = int(replication_rate * redundancy_factor)
                for _ in range(n_repl):
                    if np.random.rand() > materials[tile["material"]]["rep_err"]:
                        new_tiles.append(tile.copy())
            tiles.extend(new_tiles)
        mean_dT.append(np.mean(history_deltaT))
        mean_power.append(np.mean(history_power))
        all_histories.append((history_deltaT, history_power, history_tiles, history_eta))

    avg_dT_var = np.var(mean_dT)
    avg_power = np.mean(mean_power)
    fitness = avg_dT_var - 0.1 * avg_power

    if return_history:
        return all_histories[0]
    return fitness

# -----------------------------
# Optimization bounds
# -----------------------------
bounds = [
    (0.01, 0.2),    # replication_rate
    (1.0, 1.5),     # redundancy_factor
    (0.0, 1.0),     # kapton fraction
    (0.0, 1.0)      # mylar fraction
]

result = differential_evolution(run_sim, bounds, maxiter=20, popsize=10, tol=0.01)
print("Optimal parameters found:")
print(f"Replication rate   : {result.x[0]:.3f}")
print(f"Redundancy factor  : {result.x[1]:.3f}")
print(f"Kapton fraction    : {result.x[2]:.3f}")
print(f"Mylar fraction     : {result.x[3]:.3f}")
print(f"Graphene fraction  : {max(0,1-result.x[2]-result.x[3]):.3f}")
print(f"Fitness score      : {result.fun:.4f}")

# -----------------------------
# Run final simulation for plotting
# -----------------------------
history_deltaT, history_power, history_tiles, history_eta = run_sim(result.x, return_history=True)
time_axis = np.arange(1, steps+1)

plt.figure(figsize=(15,6))

plt.subplot(2,2,1)
plt.plot(time_axis, history_deltaT, label="ΔT surface (K)", color='orange')
plt.xlabel("Month"); plt.ylabel("ΔT (K)")
plt.title("Temperature Reduction over Time")
plt.grid(True)

plt.subplot(2,2,2)
plt.plot(time_axis, history_power, label="Total Swarm Power", color='green')
plt.xlabel("Month"); plt.ylabel("Power units")
plt.title("Total Swarm Power")
plt.grid(True)

plt.subplot(2,2,3)
plt.plot(time_axis, history_tiles, label="Total Deployed Tiles", color='blue')
plt.xlabel("Month"); plt.ylabel("Tile count")
plt.title("Total Deployed Tiles")
plt.grid(True)

plt.subplot(2,2,4)
plt.plot(time_axis, history_eta, label="Shading fraction η", color='purple')
plt.xlabel("Month"); plt.ylabel("Shading fraction")
plt.title("Shading Fraction over Time")
plt.grid(True)

plt.tight_layout()
plt.show()
