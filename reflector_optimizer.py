import numpy as np
from itertools import combinations

# =============================================================================
# Multi-Layer Reflector Mass Optimizer
# Engineering-level trade tool – finds minimum areal mass to achieve target reflectivity
# Physics are approximate; intended for system comparison only
# =============================================================================

def combined_reflectivity(layer_reflectivities):
    """
    Multi-layer reflectivity model (non-coherent, statistical approximation).
    Each layer reflects fraction r_i of incident light that reaches it.
    Total reflectivity R = 1 - product_over_layers (1 - r_i)
    This is exact for lossless, randomly phased partial reflections (valid for thin films).
    """
    r = np.asarray(layer_reflectivities, dtype=float)
    if len(r) == 0:
        return 0.0
    transmitted_fraction = np.prod(1.0 - r)
    return 1.0 - transmitted_fraction


def optimize_reflector_bruteforce(R_target, candidates, max_layers=None):
    """
    Brute-force/combinatorial optimizer (exact for small n ≤ 20).

    Parameters
    ----------
    R_target : float
        Desired total reflectivity [0–1]
    candidates : list of tuples (r_i, m_i)
        r_i : reflectivity added by this layer type (0–1)
        m_i : areal mass of this layer type [kg/m²]
    max_layers : int or None
        Optional cap on number of layers (for performance)

    Returns
    -------
    dict with best solution or None if impossible
    """
    n = len(candidates)
    best_mass = np.inf
    best_solution = None

    # Generate all possible non-empty subsets (order doesn't matter for reflectivity)
    for size in range(1, n + 1 if max_layers is None else min(max_layers, n) + 1):
        for subset_idx in combinations(range(n), size):
            rs = [candidates[i][0] for i in subset_idx]
            ms = [candidates[i][1] for i in subset_idx]

            R = combined_reflectivity(rs)
            total_mass = sum(ms)

            if R >= R_target and total_mass < best_mass:
                best_mass = total_mass
                best_solution = {
                    "total_areal_mass_kg_m2": total_mass,
                    "achieved_reflectivity": R,
                    "layers_used": size,
                    "selected_indices": subset_idx,
                    "selected_layers": [(candidates[i][0], candidates[i][1]) for i in subset_idx]
                }

    return best_solution


def optimize_reflector_greedy(R_target, candidates, steps=1000):
    """
    Fast greedy heuristic – useful when n is large.
    Repeatedly adds the layer giving the highest ΔR / Δm until target is met.
    """
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

    if current_R >= R_target:
        return {
            "total_areal_mass_kg_m2": current_mass,
            "achieved_reflectivity": current_R,
            "layers_used": len(selected),
            "selected_layers": selected,
            "method": "greedy"
        }
    else:
        return None


# =============================================================================
# Example / Test Cases
# =============================================================================
if __name__ == "__main__":
    # Candidate layer technologies (realistic near-term values)
    candidates = [
        (0.91, 0.00015),   # 30 nm Al on polymer (150 mg/m²) – baseline space mirror
        (0.88, 0.00006),   # 12 nm Al (ultra-thin, experimental)
        (0.12, 0.0008),    # Single dielectric layer (e.g., SiO2)
        (0.25, 0.0018),    # 5-layer dielectric stack
        (0.45, 0.0045),    # 15-layer V-coated dielectric mirror
        (0.05, 0.00003),   # Protective fluoropolymer coating (almost free mass)
        (0.60, 0.012),     # Micro-structured retroreflector film (higher mass, high R)
    ]

    targets = [0.90, 0.95, 0.98, 0.995]

    print("Multi-Layer Reflector Optimization Results")
    print("="*70)
    for R_t in targets:
        print(f"\nTarget reflectivity: {R_t:.3f}")
        sol = optimize_reflector_bruteforce(R_t, candidates)
        if sol:
            print(f"   Min areal mass    : {sol['total_areal_mass_kg_m2']*1000:6.3f} g/m²")
            print(f"   Achieved R        : {sol['achieved_reflectivity']:.5f}")
            print(f"   Layers used       : {sol['layers_used']}")
            print( "   Composition       :", end="")
            for r, m in sol['selected_layers']:
                print(f" ({r:.2f}, {m*1000:.1f}g)", end="")
            print()
        else:
            print("   Impossible with available layers")
