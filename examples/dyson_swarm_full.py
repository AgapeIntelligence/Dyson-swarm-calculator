import numpy as np

# ===============================
# Dyson Swarm Simulator
# Multi-material + Stochastic Hazards + Self-replication + Power Output
# ===============================

# --- Simulation parameters ---
years = 5
dt = 1/12  # monthly timestep
steps = int(years/dt)

# --- Earth constants ---
R_earth = 6.371e6  # m
A_earth = np.pi * R_earth**2
T_eff = 255
ecs_multiplier = 1.8  # effective climate sensitivity multiplier

# --- Tile / Material properties ---
materials = [
    {"name": "Kapton+SiO2", "area": 1e6, "efficiency": 0.95, "degradation": 0.005, "power_density": 1e3},
    {"name": "Al-coated Mylar", "area": 1e6, "efficiency": 0.92, "degradation": 0.007, "power_density": 950},
    {"name": "Graphene", "area": 0.5e6, "efficiency": 0.97, "degradation": 0.003, "power_density": 1200}
]

N_init_per_mat = [300, 300, 200]  # initial deployed tiles per material

# --- Swarm dynamics ---
replication_rate = 0.05
p_err = 0.02
redundancy_factor = 1.1

# --- Hazard probabilities ---
p_solar_storm = 0.01  # monthly chance of temporary efficiency hit
p_micrometeor = 0.005 # chance per tile of destruction per month

# Initialize tiles
tiles = []
for mat, N in zip(materials, N_init_per_mat):
    for _ in range(N):
        tiles.append({
            "material": mat["name"],
            "efficiency": mat["efficiency"],
            "area": mat["area"],
            "power_density": mat["power_density"]
        })

tiles = np.array(tiles)

# History records
history_efficiency = []
history_shading = []
history_deltaT = []
history_power = []

for step in range(steps):
    # --- 1. Apply material degradation ---
    for i, tile in enumerate(tiles):
        mat = next(m for m in materials if m["name"] == tile["material"])
        tiles[i]["efficiency"] *= (1 - mat["degradation"])
    
    # --- 2. Stochastic hazards ---
    # Solar storm: temporary efficiency drop
    if np.random.rand() < p_solar_storm:
        for tile in tiles:
            tile["efficiency"] *= 0.95  # 5% hit

    # Micrometeor impacts
    hits = np.random.rand(len(tiles)) < p_micrometeor
    tiles = np.array([tile for i, tile in enumerate(tiles) if not hits[i]])

    # --- 3. Compute swarm metrics ---
    total_shading = sum(tile["efficiency"] * tile["area"] for tile in tiles) / A_earth
    total_shading = min(total_shading, 1.0)
    total_power = sum(tile["efficiency"] * tile["power_density"] for tile in tiles)

    dT_eff = -T_eff * 0.25 * total_shading
    dT_surface = dT_eff * ecs_multiplier

    history_efficiency.append(np.mean([t["efficiency"] for t in tiles]))
    history_shading.append(total_shading)
    history_deltaT.append(dT_surface)
    history_power.append(total_power)

    # --- 4. Self-replication ---
    n_replicate = int(len(tiles) * replication_rate * redundancy_factor)
    replicated = np.random.choice(tiles, n_replicate)
    success = np.random.rand(n_replicate) > p_err
    tiles = np.concatenate([tiles, replicated[success]])

# --- Output results ---
for month, (eff, shading, dT, power) in enumerate(zip(
        history_efficiency, history_shading, history_deltaT, history_power)):
    print(f"Month {month+1:3d}: Tiles={len(tiles):5d}, "
          f"Shading={shading*100:6.3f}%, ΔT={dT:+.3f} K, Power={power/1e9:6.2f} GW")

# Optional: plot results if matplotlib is available
try:
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12,6))
    plt.plot(history_deltaT, label="ΔT Surface [K]")
    plt.plot(np.array(history_power)/1e9, label="Total Power [GW]")
    plt.xlabel("Month")
    plt.ylabel("ΔT / Power")
    plt.title("Dyson Swarm Simulation")
    plt.legend()
    plt.show()
except ImportError:
    pass
