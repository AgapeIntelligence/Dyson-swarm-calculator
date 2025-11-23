import numpy as np
from itertools import combinations

# =============================================================================
# Multi-Layer Reflector Mass Optimizer — 2025 Deep-Space Final
# Features:
#   • p-B11 fusion mass reduction (PowerOption)
#   • True exponential fusion fuel decay via half-life (real physics)
#   • Beamed microwave support
#   • Works from 1 AU to Oort Cloud (100–10,000 yr missions)
# =============================================================================

def combined_reflectivity(layer_reflectivities):
    """Non-coherent multi-layer model: R = 1 - Π(1 - r_i)"""
    r = np.asarray(layer_reflectivities, dtype=float)
    if len(r) == 0:
        return 0.0
    return 1.0 - np.prod(1.0 - r)

class PowerOption:
    """Onboard power system → structural mass savings"""
    def __init__(self, type='p-B11', mass_reduction=0.075):
        self.type = type
        self.mass_reduction = mass_reduction

    def optimize_mass(self, base_mass_kg_m2):
        return base_mass_kg_m2 * (1.0 - self.mass_reduction)

def hybrid_power(au_distance,
                 mission_time_yr,
                 solar_area_m2=1e6,
                 solar_eff=0.20,
                 fusion_base_kw=100.0,
                 beamed_microwave_kw=0.0,
                 fusion_half_life_yr=12.0):
    """
    Final deep-space hybrid power model — exponential decay via real half-life.
    
    fusion_half_life_yr examples:
      12.0  → Tritium-limited (conservative baseline)
      18.0  → Li-6 breeding blanket
      30.0  → D-He3 with advanced tanks
     100.0  → Ideal p-B11 with perfect logistics
    """
    S0 = 1362.0
    solar_kw = (S0 / (au_distance ** 2)) * solar_area_m2 * solar_eff / 1000.0

    decay_fraction = 0.5 ** (mission_time_yr / fusion_half_life_yr)
    fusion_remaining_kw = fusion_base_kw * decay_fraction

    total_floor_kw = fusion_remaining_kw + beamed_microwave_kw
    return max(solar_kw, total_floor_kw)

# =============================================================================
# Optimizers (now with full deep-space power model)
# =============================================================================

def optimize_reflector_bruteforce(R_target,
                                  candidates,
                                  max_layers=None,
                                  power_opt=None,
                                  au_distance=1.0,
                                  mission_time_yr=1.0,
                                  fusion_kw=100.0,
                                  beamed_kw=0.0,
                                  fusion_half_life_yr=12.0):
    n = len(candidates)
    best_mass = np.inf
    best_solution = None

    for size in range(1, (n + 1) if max_layers is None else min(max_layers + 1, n + 1)):
        for subset in combinations(range(n), size):
            rs = [candidates[i][0] for i in subset]
            ms = [candidates[i][1] for i in subset]
            R = combined_reflectivity(rs)
            mass = sum(ms)

            if power_opt:
                mass = power_opt.optimize_mass(mass)

            if R >= R_target and mass < best_mass:
                best_mass = mass
                best_solution = {
                    "total_areal_mass_kg_m2": mass,
                    "achieved_reflectivity": R,
                    "layers_used": size,
                    "selected_layers": [(r, m) for r, m in zip(rs, ms)],
                    "power_option": power_opt.type if power_opt else None,
                    "au_distance": au_distance,
                    "mission_time_yr": mission_time_yr,
                    "fusion_half_life_yr": fusion_half_life_yr,
                    "available_power_kw": hybrid_power(au_distance,
                                                       mission_time_yr,
                                                       fusion_base_kw=fusion_kw,
                                                       beamed_microwave_kw=beamed_kw,
                                                       fusion_half_life_yr=fusion_half_life_yr)
                }

    return best_solution

def optimize_reflector_greedy(R_target,
                              candidates,
                              power_opt=None,
                              au_distance=1.0,
                              mission_time_yr=1.0,
                              fusion_kw=100.0,
                              beamed_kw=0.0,
                              fusion_half_life_yr=12.0):
    candidates = sorted(candidates,
                        key=lambda x: x[0]/x[1] if x[1] > 0 else np.inf,
                        reverse=True)

    selected = []
    current_R = 0.0
    current_mass = 0.0

    while current_R < R_target and candidates:
        best_ratio = -1.0
        best_idx = -1
        for i, (r, m) in enumerate(candidates):
            trial_R = combined_reflectivity([r] + [s[0] for s in selected])
            delta_R = trial_R - current_R
            ratio = delta_R / m if m > 0 else 0
            if ratio > best_ratio:
                best_ratio = ratio
                best_idx = i
        if best_idx == -1:
            break

        r, m = candidates.pop(best_idx)
        selected.append((r, m))
        current_R = combined_reflectivity([s[0] for s in selected])
        current_mass += m

    if current_R >= R_target and power_opt:
        current_mass = power_opt.optimize_mass(current_mass)

    if current_R >= R_target:
        return {
            "total_areal_mass_kg_m2": current_mass,
            "achieved_reflectivity": current_R,
            "layers_used": len(selected),
            "selected_layers": selected,
            "method": "greedy",
            "power_option": power_opt.type if power_opt else None,
            "au_distance": au_distance,
            "mission_time_yr": mission_time_yr,
            "fusion_half_life_yr": fusion_half_life_yr,
            "available_power_kw": hybrid_power(au_distance,
                                               mission_time_yr,
                                               fusion_base_kw=fusion_kw,
                                               beamed_microwave_kw=beamed_kw,
                                               fusion_half_life_yr=fusion_half_life_yr)
        }
    return None

# =============================================================================
# Oort Cloud Mission Test Suite (100–1000 yr class)
# =============================================================================
if __name__ == "__main__":
    candidates = [
        (0.91, 0.00015), (0.88, 0.00006), (0.12, 0.0008), (0.25, 0.0018),
        (0.45, 0.0045), (0.05, 0.00003), (0.60, 0.012),
    ]
    power_opt = PowerOption(type="p-B11", mass_reduction=0.075)

    print("Reflector Optimization — Oort Cloud / Interstellar Swarm (2025 Final)\n")
    print("="*90)

    scenarios = [
        (0.98,   1.0,    1,  200,    0, 12.0, "Inner swarm (1 AU)"),
        (0.98,  10.0,   10,  300, 1000, 12.0, "Mid-zone (10 AU + beamed)"),
        (0.98,  50.0,   50,  600,    0, 12.0, "Kuiper edge (50 AU)"),
        (0.98, 100.0,  100, 1200,    0, 12.0, "Oort 100 yr (tritium limit)"),
        (0.98, 100.0,  100,  600,    0, 30.0, "Oort 100 yr (D-He3)"),
        (0.98, 100.0,  100,  400,    0,100.0, "Oort 100 yr (ideal p-B11)"),
        (0.995,500.0,  500, 2000,    0, 18.0, "500-yr mission (Li-6 breeding)"),
    ]

    for R_t, au, t, fusion, beamed, hl, label in scenarios:
        sol = optimize_reflector_bruteforce(R_t, candidates,
                                            power_opt=power_opt,
                                            au_distance=au,
                                            mission_time_yr=t,
                                            fusion_kw=fusion,
                                            beamed_kw=beamed,
                                            fusion_half_life_yr=hl)
        if sol:
            print(f"{label}")
            print(f"   R ≥ {R_t:.3f} | {au:5.0f} AU | {t:4.0f} yr | Half-life {hl:4.1f} yr")
            print(f"   Power → {sol['available_power_kw']:5.0f} kW  |  Mass {sol['total_areal_mass_kg_m2']*1000:5.2f} g/m²")
            print(f"   Stack: ", end="")
            for r, m in sol['selected_layers']:
                print(f"({r:.2f},{m*1000:4.1f}g)", end=" ")
            print("\n")
