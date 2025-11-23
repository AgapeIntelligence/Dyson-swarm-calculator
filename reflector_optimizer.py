import numpy as np
from itertools import combinations

# =============================================================================
# Multi-Layer Reflector Mass Optimizer
# Updated 2025: Adds p-B11 fusion power option for 5-10% mass reduction
# Engineering-level trade tool – finds minimum areal mass to achieve target reflectivity
# Physics are approximate; intended for system comparison only
# =============================================================================

def combined_reflectivity(layer_reflectivities):
    """
    Multi-layer reflectivity model (non-coherent, statistical approximation).
    Each layer reflects fraction r_i of incident light that reaches it.
    Total reflectivity R = 1 - product_over_layers (1 - r_i)
    """
    r = np.asarray(layer_reflectivities, dtype=float)
    if len(r) == 0:
        return 0.0
    transmitted_fraction = np.prod(1.0 - r)
    return 1.0 - transmitted_fraction

class PowerOption:
    def __init__(self, type='p-B11', mass_reduction=0.075):
        """Power option with mass reduction (e.g., 7.5% for p-B11 fusion)."""
        self.type = type
        self.mass_reduction = mass_reduction  # 5-10% reduction, default 7.5%

    def optimize_mass(self, base_mass):
        """Reduces base mass by mass_reduction factor."""
        return base_mass * (1 - self.mass_reduction)

def hybrid_power(au, solar_area_km2=1, fusion_kw=50, factor=0.7):
    """Calculates hybrid power (solar + p-B11 fusion) in kW."""
    solar = 1362 / au**2 * solar_area_km2 * 1e6 * 0.2  # W, 20% efficiency (updated S0 2025)
    return (solar / 1000 + fusion_kw) * factor  # kW

def optimize_reflector_bruteforce(R_target, candidates, max_layers=None, power_opt=None):
    """Brute-force/combinatorial optimizer with power option."""
    n = len(candidates)
    best_mass = np.inf
    best_solution = None

    for size in range(1, n + 1 if max_layers is None else min(max_layers, n) + 1):
        for subset_idx in combinations(range(n), size):
            rs = [candidates[i][0] for i in subset_idx]
            ms = [candidates[i][1] for i in subset_idx]
            R = combined_reflectivity(rs)
            total_mass = sum(ms)

            if power_opt:
                total_mass = power_opt.optimize_mass(total_mass)

            if R >= R_target and total_mass < best_mass:
                best_mass = total_mass
                best_solution = {
                    "total_areal_mass_kg_m2": total_mass,
                    "achieved_reflectivity": R,
                    "layers_used": size,
                    "selected_indices": subset_idx,
                    "selected_layers": [(candidates[i][0], candidates[i][1]) for i in subset_idx],
                    "power_option": power_opt.type if power_opt else None
                }

    return best_solution

def optimize_reflector_greedy(R_target, candidates, steps=1000, power_opt=None):
    """Fast greedy heuristic with power option."""
    candidates = sorted(candidates, key=lambda x: x[0]/x[1] if x[1]>0 else np.inf, reverse=True)
    selected = []
    current_R = 0.0
    current_mass = 0.0

    while current_R < R_target and candidates:
        best_ratio = -1
        best_idx = -1
        for i, (r, m) in enumerate(candidates):
            if m <= 0:
                continue
            new_R = combined_reflectivity([r] + [s[0] for s in selected])
            delta_R = new_R - current_R
            ratio = delta_R / m
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
            "power_option": power_opt.type if power_opt else None
        }
    return None

# =============================================================================
# Example / Test Cases
# =============================================================================
if __name__ == "__main__":
    candidates = [
        (0.91, 0.00015), (0.88, 0.00006), (0.12, 0.0008), (0.25, 0.0018),
        (0.45, 0.0045), (0.05, 0.00003), (0.60, 0.012),
    ]
    targets = [0.90, 0.95, 0.98, 0.995]
    power_opt = PowerOption()

    print("Multi-Layer Reflector Optimization Results (Updated 2025 w/ p-B11 Fusion)\n")
    print("="*70)
    for R_t in targets:
        print(f"\nTarget reflectivity: {R_t:.3f}")
        sol = optimize_reflector_bruteforce(R_t, candidates, power_opt=power_opt)
        if sol:
            print(f"   Min areal mass    : {sol['total_areal_mass_kg_m2']*1000:6.3f} g/m²")
            print(f"   Achieved R        : {sol['achieved_reflectivity']:.5f}")
            print(f"   Layers used       : {sol['layers_used']}")
            print(f"   Power option      : {sol['power_option']}")
            print("   Composition       :", end="")
            for r, m in sol['selected_layers']:
                print(f" ({r:.2f}, {m*1000:.1f}g)", end="")
            print()
        else:
            print("   Impossible with available layers")
