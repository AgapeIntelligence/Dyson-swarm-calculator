import numpy as np
from scipy.optimize import differential_evolution
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# -----------------------------
# Dyson Swarm Dashboard Simulation
# -----------------------------

years = 2
dt = 1/12
steps = int(years/dt)
n_runs = 10

R_earth = 6.371e6
A_earth = np.pi * R_earth**2
T_eff = 255
ecs_multiplier = 1.8

# Multi-material parameters
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
    
    history_material = {mat: [] for mat in materials}
    history_deltaT = []
    history_power = []

    for run in range(n_runs):
        tiles = []
        for mat, n in tile_counts.items():
            for _ in range(n):
                tiles.append({"material": mat,
                              "eff": materials[mat]["eff"],
                              "area": materials[mat]["area"],
                              "power": materials[mat]["power"]})

        for step in range(steps):
            # Degrade
            for tile in tiles:
                tile["eff"] *= (1 - materials[tile["material"]]["deg"])
            # Stochastic hazards
            for tile in tiles:
                if np.random.rand() < solar_storm_prob or np.random.rand() < micrometeoroid_prob:
                    tile["eff"] *= (1 - hazard_deg)
            # Aggregate
            eta_total = min(1.0, sum(tile["eff"]*tile["area"] for tile in tiles)/A_earth)
            power_total = sum(tile["eff"]*tile["power"] for tile in tiles)
            dT_eff = -T_eff * 0.25 * eta_total
            dT_surface = dT_eff * ecs_multiplier
            history_deltaT.append(dT_surface)
            history_power.append(power_total)
            # Material count
            counts = {mat: sum(1 for t in tiles if t["material"]==mat) for mat in materials}
            for mat in materials:
                history_material[mat].append(counts[mat])
            # Self-replication
            new_tiles = []
            for tile in tiles:
                n_repl = int(replication_rate * redundancy_factor)
                for _ in range(n_repl):
                    if np.random.rand() > materials[tile["material"]]["rep_err"]:
                        new_tiles.append(tile.copy())
            tiles.extend(new_tiles)

    if return_history:
        return history_deltaT, history_power, history_material
    return np.var(history_deltaT) - 0.1*np.mean(history_power)

# -----------------------------
# Optimization
# -----------------------------
bounds = [
    (0.01, 0.2),
    (1.0, 1.5),
    (0.0, 1.0),
    (0.0, 1.0)
]

result = differential_evolution(run_sim, bounds, maxiter=20, popsize=10, tol=0.01)
print("Optimal parameters:")
print(f"Replication rate   : {result.x[0]:.3f}")
print(f"Redundancy factor  : {result.x[1]:.3f}")
print(f"Kapton fraction    : {result.x[2]:.3f}")
print(f"Mylar fraction     : {result.x[3]:.3f}")
print(f"Graphene fraction  : {max(0,1-result.x[2]-result.x[3]):.3f}")
print(f"Fitness score      : {result.fun:.4f}")

# -----------------------------
# Final simulation for dashboard
# -----------------------------
history_deltaT, history_power, history_material = run_sim(result.x, return_history=True)
time_axis = np.arange(1, steps+1)

# -----------------------------
# Create dashboard figure
# -----------------------------
fig = plt.figure(figsize=(16,12))

# Subplot 1: ΔT
ax1 = fig.add_subplot(221)
ax1.plot(time_axis, history_deltaT, color="red")
ax1.set_xlabel("Month")
ax1.set_ylabel("ΔT [K]")
ax1.set_title("Surface Temperature Impact Over Time")

# Subplot 2: Power output
ax2 = fig.add_subplot(222)
ax2.plot(time_axis, history_power, color="blue")
ax2.set_xlabel("Month")
ax2.set_ylabel("Total Swarm Power")
ax2.set_title("Swarm Power Output Over Time")

# Subplot 3: 3D Material distribution
ax3 = fig.add_subplot(212, projection='3d')
x = np.arange(steps)
y = np.zeros(steps)
colors = {"Kapton_SiO2":"orange", "Mylar_Al":"green", "Graphene":"purple"}
bottom = np.zeros(steps)
for mat in ["Kapton_SiO2","Mylar_Al","Graphene"]:
    dz = history_material[mat]
    ax3.bar(x, dz, zs=y, zdir='y', bottom=bottom, color=colors[mat], alpha=0.8, label=mat)
    bottom += dz
ax3.set_xlabel("Month")
ax3.set_ylabel("Material Stack")
ax3.set_zlabel("Tile count")
ax3.set_title("3D Dyson Swarm Material Distribution")
ax3.legend()

plt.tight_layout()
plt.show()
