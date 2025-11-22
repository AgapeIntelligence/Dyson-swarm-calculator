"""
swarm_dashboard.py
------------------
Full Dyson Swarm Simulation Dashboard with:
- Multi-material tiles with different degradation/error rates
- Stochastic solar storms / micrometeoroid hits
- Self-replication with redundancy & AI oversight
- Total swarm power output
- ΔT and energy projections
"""

import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, IntSlider, FloatSlider

# -----------------------------
# Simulation Parameters
# -----------------------------
# Time
years = 5
dt = 1/12
steps = int(years/dt)

# Earth & swarm
R_earth = 6.371e6
A_earth = np.pi * R_earth**2

# Materials: dict of name -> (area per tile [m²], efficiency, degradation rate per month, replication error)
materials = {
    "Kapton-SiO2": (1e6, 0.95, 0.005, 0.02),
    "AluminumFilm": (1e6, 0.92, 0.008, 0.03),
    "GrapheneMesh": (1e6, 0.97, 0.003, 0.01)
}

# Replication & redundancy
replication_rate = 0.05
redundancy_factor = 1.1

# ECS multiplier for ΔT
T_eff = 255
ecs_multiplier = 1.8

# Stochastic hazards
storm_prob = 0.01          # monthly probability of storm
storm_damage = 0.10        # fraction of tiles degraded
micrometeor_prob = 0.005
micrometeor_damage = 0.15

# Power output per tile (MW)
power_per_tile = 0.25

# -----------------------------
# Initialize Tiles
# -----------------------------
tile_list = []
for mat, (A_tile, eff, degrade, err) in materials.items():
    n_init = 1000  # initial per material
    for _ in range(n_init):
        tile_list.append({
            "material": mat,
            "efficiency": eff,
            "degradation": degrade,
            "error": err
        })
tile_list = np.array(tile_list, dtype=object)

# -----------------------------
# Simulation Function
# -----------------------------
def run_sim(replication_rate=0.05, redundancy_factor=1.1):
    history_efficiency = []
    history_tiles = []
    history_deltaT = []
    history_power = []

    tiles = tile_list.copy()

    for step in range(steps):
        # Degrade tiles
        for t in tiles:
            t["efficiency"] *= (1 - t["degradation"])

        # Stochastic hazards
        if np.random.rand() < storm_prob:
            affected = np.random.choice(len(tiles), int(len(tiles)*storm_damage), replace=False)
            for idx in affected:
                tiles[idx]["efficiency"] *= 0.9
        if np.random.rand() < micrometeor_prob:
            affected = np.random.choice(len(tiles), int(len(tiles)*micrometeor_damage), replace=False)
            for idx in affected:
                tiles[idx]["efficiency"] *= 0.85

        # Aggregate shading & ΔT
        total_area_eff = sum(t["efficiency"]*materials[t["material"]][0] for t in tiles)
        eta_total = min(1.0, total_area_eff / A_earth)
        dT_eff = -T_eff*0.25*eta_total
        dT_surface = dT_eff*ecs_multiplier
        history_efficiency.append(eta_total)
        history_tiles.append(len(tiles))
        history_deltaT.append(dT_surface)
        history_power.append(len(tiles)*power_per_tile)

        # Self-replication
        n_replicate = int(len(tiles)*replication_rate*redundancy_factor)
        new_tiles = []
        for _ in range(n_replicate):
            parent = np.random.choice(tiles)
            eff = parent["efficiency"]
            mat = parent["material"]
            err_prob = parent["error"]
            if np.random.rand() > err_prob:  # AI oversight removes failures
                new_tiles.append({"material": mat, "efficiency": eff, "degradation": parent["degradation"], "error": err_prob})
        tiles = np.concatenate([tiles, new_tiles])

    return history_efficiency, history_tiles, history_deltaT, history_power

# -----------------------------
# Dashboard / Visualization
# -----------------------------
def visualize(rep_rate=0.05, red_factor=1.1):
    eta, tiles, dT, power = run_sim(rep_rate, red_factor)
    months = np.arange(1, len(eta)+1)

    plt.figure(figsize=(12,6))
    plt.subplot(2,1,1)
    plt.plot(months, [e*100 for e in eta], label="Shading (%)")
    plt.plot(months, dT, label="ΔT Surface (K)")
    plt.ylabel("Climate Impact")
    plt.legend()
    plt.grid(True)

    plt.subplot(2,1,2)
    plt.plot(months, tiles, label="Number of tiles")
    plt.plot(months, power, label="Total Power (MW)")
    plt.xlabel("Month")
    plt.ylabel("Swarm Stats")
    plt.legend()
    plt.grid(True)

    plt.suptitle("Dyson Swarm Simulation: Multi-Material, Stochastic, Self-Replicating")
    plt.show()

# Interactive controls
interact(visualize,
         rep_rate=FloatSlider(min=0.01,max=0.1,step=0.005,value=replication_rate,description="Replication Rate"),
         red_factor=FloatSlider(min=1.0,max=1.3,step=0.01,value=redundancy_factor,description="Redundancy Factor"))
