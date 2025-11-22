import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import ipywidgets as widgets
from IPython.display import display, clear_output

# --- Base simulation function ---
def run_swarm(replication_rate=0.05, redundancy_factor=1.1,
              frac_kapton=0.33, frac_mylar=0.33, frac_graphene=0.34,
              storm_prob=0.01):
    years = 1
    dt = 1/12
    steps = int(years/dt)
    R_earth = 6.371e6
    A_earth = np.pi * R_earth**2
    T_eff = 255
    ecs_multiplier = 1.8
    N_init = 1000

    # Normalize fractions
    total_frac = frac_kapton + frac_mylar + frac_graphene
    frac_kapton /= total_frac
    frac_mylar /= total_frac
    frac_graphene /= total_frac

    # Tile definitions
    materials = {
        "Kapton_SiO2": {"eff":0.95, "deg":0.004, "rep_err":0.02, "area":1e6, "power":1.0},
        "Mylar_Al": {"eff":0.92, "deg":0.006, "rep_err":0.03, "area":1e6, "power":0.9},
        "Graphene": {"eff":0.98, "deg":0.002, "rep_err":0.01, "area":1e6, "power":1.1},
    }

    n_tiles = [int(N_init*frac_kapton), int(N_init*frac_mylar), int(N_init*frac_graphene)]
    
    tiles = []
    for mat, n in zip(materials, n_tiles):
        for _ in range(n):
            tiles.append({"material": mat, "eff": materials[mat]["eff"],
                          "area": materials[mat]["area"], "power": materials[mat]["power"]})

    history_deltaT = []
    history_power = []
    history_material = {mat: [] for mat in materials}

    for step in range(steps):
        # Degrade tiles + stochastic hazards
        for tile in tiles:
            tile["eff"] *= (1 - materials[tile["material"]]["deg"])
            if np.random.rand() < storm_prob:
                tile["eff"] *= 0.9  # solar storm hit reduces efficiency by 10%

        eta_total = min(1.0, sum(tile["eff"]*tile["area"] for tile in tiles)/A_earth)
        power_total = sum(tile["eff"]*tile["power"] for tile in tiles)
        dT_eff = -T_eff*0.25*eta_total
        dT_surface = dT_eff*ecs_multiplier

        history_deltaT.append(dT_surface)
        history_power.append(power_total)
        for mat in materials:
            history_material[mat].append(sum(1 for t in tiles if t["material"]==mat))

        # Self-replication
        new_tiles = []
        for tile in tiles:
            n_repl = int(replication_rate*redundancy_factor)
            for _ in range(n_repl):
                if np.random.rand() > materials[tile["material"]]["rep_err"]:
                    new_tiles.append(tile.copy())
        tiles.extend(new_tiles)

    return history_deltaT, history_power, history_material

# --- Interactive dashboard ---
def update_dashboard(replication_rate, redundancy_factor,
                     frac_kapton, frac_mylar, frac_graphene, storm_prob):
    clear_output(wait=True)
    deltaT, power, mat_hist = run_swarm(replication_rate, redundancy_factor,
                                        frac_kapton, frac_mylar, frac_graphene,
                                        storm_prob)
    steps = len(deltaT)
    time_axis = np.arange(1, steps+1)

    fig = plt.figure(figsize=(12,8))
    
    # ΔT
    ax1 = fig.add_subplot(221)
    ax1.plot(time_axis, deltaT, color="red")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("ΔT [K]")
    ax1.set_title("Surface Temperature ΔT")
    
    # Power
    ax2 = fig.add_subplot(222)
    ax2.plot(time_axis, power, color="blue")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Swarm Power")
    ax2.set_title("Swarm Power Output")
    
    # 3D Material
    ax3 = fig.add_subplot(212, projection='3d')
    x = np.arange(steps)
    y = np.zeros(steps)
    colors = {"Kapton_SiO2":"orange", "Mylar_Al":"green", "Graphene":"purple"}
    bottom = np.zeros(steps)
    for mat in ["Kapton_SiO2","Mylar_Al","Graphene"]:
        dz = mat_hist[mat]
        ax3.bar(x, dz, zs=y, zdir='y', bottom=bottom, color=colors[mat], alpha=0.8, label=mat)
        bottom += dz
    ax3.set_xlabel("Month")
    ax3.set_ylabel("Material Stack")
    ax3.set_zlabel("Tile count")
    ax3.set_title("3D Material Distribution")
    ax3.legend()
    
    plt.tight_layout()
    plt.show()

# --- Widgets ---
rep_slider = widgets.FloatSlider(value=0.05, min=0.01, max=0.2, step=0.005, description='Replication rate')
red_slider = widgets.FloatSlider(value=1.1, min=1.0, max=1.5, step=0.05, description='Redundancy factor')
kap_slider = widgets.FloatSlider(value=0.33, min=0.0, max=1.0, step=0.01, description='Kapton fraction')
mylar_slider = widgets.FloatSlider(value=0.33, min=0.0, max=1.0, step=0.01, description='Mylar fraction')
graphene_slider = widgets.FloatSlider(value=0.34, min=0.0, max=1.0, step=0.01, description='Graphene fraction')
storm_slider = widgets.FloatSlider(value=0.01, min=0.0, max=0.1, step=0.005, description='Storm prob')

widgets.interact(update_dashboard,
                 replication_rate=rep_slider,
                 redundancy_factor=red_slider,
                 frac_kapton=kap_slider,
                 frac_mylar=mylar_slider,
                 frac_graphene=graphene_slider,
                 storm_prob=storm_slider)
