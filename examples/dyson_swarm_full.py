import numpy as np

# ===============================
# Dyson Swarm Full Simulator + Optimization
# ===============================

years = 5
dt = 1/12
steps = int(years/dt)

R_earth = 6.371e6
A_earth = np.pi * R_earth**2
T_eff = 255
ecs_multiplier = 1.8

# --- Tile materials ---
materials = [
    {"name": "Kapton+SiO2", "area": 1e6, "eff": 0.95, "deg": 0.005, "power": 1e3},
    {"name": "AlMylar", "area": 1e6, "eff": 0.92, "deg": 0.007, "power": 950},
    {"name": "Graphene", "area": 0.5e6, "eff": 0.97, "deg": 0.003, "power": 1200}
]
N_init = [300, 300, 200]

p_solar_storm = 0.01
p_meteoroid = 0.005
p_err = 0.02

# --- Swarm init ---
def init_tiles():
    tiles = []
    for mat, N in zip(materials, N_init):
        tiles.extend([mat.copy() for _ in range(N)])
    return np.array(tiles)

# --- Simulation ---
def simulate(rep_rate, redundancy):
    tiles = init_tiles()
    history_dT = []
    history_power = []
    for _ in range(steps):
        # Degrade
        for i, tile in enumerate(tiles):
            mat = next(m for m in materials if m["name"] == tile["name"])
            tiles[i]["eff"] *= (1 - mat["deg"])
        # Hazards
        if np.random.rand() < p_solar_storm:
            for tile in tiles: tile["eff"] *= 0.95
        hits = np.random.rand(len(tiles)) < p_meteoroid
        tiles = np.array([tile for i, tile in enumerate(tiles) if not hits[i]])
        # Metrics
        shading = sum(t["eff"]*t["area"] for t in tiles)/A_earth
        shading = min(shading,1.0)
        total_power = sum(t["eff"]*t["power"] for t in tiles)
        dT = -T_eff*0.25*shading*ecs_multiplier
        history_dT.append(dT)
        history_power.append(total_power)
        # Replication
        n_repl = int(len(tiles)*rep_rate*redundancy)
        if n_repl>0:
            repl_tiles = np.random.choice(tiles,n_repl)
            success = np.random.rand(n_repl) > p_err
            tiles = np.concatenate([tiles, repl_tiles[success]])
    return np.array(history_dT), np.array(history_power)

# --- Optimization loop ---
rep_candidates = np.linspace(0.01,0.1,5)
red_candidates = np.linspace(1.0,1.2,5)
best_score = -np.inf
best_params = None
for r in rep_candidates:
    for f in red_candidates:
        dT, power = simulate(r,f)
        score = power.mean() - 10*np.std(dT)  # maximize power, minimize ΔT variance
        if score>best_score:
            best_score = score
            best_params = (r,f)
print(f"Optimal rep_rate={best_params[0]:.3f}, redundancy={best_params[1]:.3f}, score={best_score:.2e}")

# --- Run final sim with optimized params ---
dT, power = simulate(*best_params)
for month, (dt_val, pw) in enumerate(zip(dT,power)):
    print(f"Month {month+1:3d}: ΔT={dt_val:+.3f} K, Power={pw/1e9:6.2f} GW")
