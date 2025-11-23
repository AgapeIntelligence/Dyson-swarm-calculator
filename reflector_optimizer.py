import numpy as np
from itertools import combinations

# =============================================================================
# Multi-Layer Reflector Mass Optimizer
# Updated 2025: p-B11 fusion mass reduction + deep-space hybrid power model
# Engineering-level trade tool – finds minimum areal mass to achieve target reflectivity
# Physics are approximate; intended for system comparison only
# =============================================================================

def combined_reflectivity(layer_reflectivities):
    """
    Non-coherent multi-layer reflectivity model.
    R_total = 1 - Π(1 - r_i)  → exact for thin, non-interfering films
    """
    r = np.asarray(layer_reflectivities, dtype=float)
    if len(r) == 0:
        return 0.0
    return 1.0 - np.prod(1.0 - r)

class PowerOption:
    """
    Onboard power system that reduces structural/shielding mass.
    Default: p-B11 aneutronic fusion → ~7.5% total mass reduction
    """
    def __init__(self, type='p-B11', mass_reduction=0.075):
        self.type = type
        self.mass_reduction = mass_reduction  # 0.05–0.10 typical

    def optimize_mass(self, base_mass_kg_m2):
        """Apply mass savings from reduced shielding, cooling, etc."""
        return base_mass_kg_m2 * (1.0 - self.mass_reduction)

def hybrid_power(au_distance,
                 solar_area_m2=1e6,
                 solar_eff=0.20,
                 fusion_base_kw=50.0,
                 beamed_microwave_kw=0.0,
                 travel_time_yr=None,
                 fuel_decay_per_year=0.008):
    """
    Deep-space hybrid power model with optional fuel degradation over time.
    - Solar: 1/au² scaling
    - Fusion + beamed: constant floor, with time-based exponential decay if travel_time_yr provided
    Returns kW per occulter (or per km²)
    """
    S0 = 1362.0  # 2025 solar constant at 1 AU [W/m²]
    solar_kw = (S0 / (au_distance ** 2)) * solar_area_m2 * solar_eff / 1000.0

    fusion_available_kw = fusion_base_kw
    if travel_time_yr is not None:
        surviving_fraction = np.exp(-fuel_decay_per_year * travel_time_yr)
        fusion_available_kw *= surviving_fraction

    floor_kw = fusion_available_kw + beamed_microwave_kw
    return max(solar_kw, floor_kw)

def optimize_reflector_bruteforce(R_target,
                                  candidates,
                                  max_layers=None,
                                  power_opt=None,
                                  au_distance=1.0,
                                  fusion_kw=50.0,
                                  beamed_kw=0.0,
                                  travel_time_yr=None,
                                  fuel_decay_per_year=0.008):
    """
    Exact combinatorial optimizer with power system integration.
    """
    n = len(candidates)
    best_mass = np.inf
    best_solution = None

    for size in range(1, (n + 1) if max_layers is None else min(max_layers + 1, n + 1)):
        for subset in combinations(range(n), size):
            reflectivities = [candidates[i][0] for i in subset]
            masses = [candidates[i][1] for i in subset]

            R = combined_reflectivity(reflectivities)
            total_mass = sum(masses)

            # Apply onboard power mass reduction
            if power_opt:
                total_mass = power_opt.optimize_mass(total_mass)

            if R >= R_target and total_mass < best_mass:
                best_mass = total_mass
                best_solution = {
                    "total_areal_mass_kg_m2": total_mass,
                    "achieved_reflectivity": R,
                    "layers_used": size,
                    "selected_layers": [(r, m) for r, m in zip(reflectivities, masses)],
                    "power_option": power_opt.type if power_opt else None,
                    "au_distance": au_distance,
                    "travel_time_yr": travel_time_yr,
                    "available_power_kw": hybrid_power(au_distance,
                                                       solar_area_m2=1e6,
                                                       fusion_base_kw=fusion_kw,
                                                       beamed_microwave_kw=beamed_kw,
                                                       travel_time_yr=travel_time_yr,
                                                       fuel_decay_per_year=fuel_decay_per_year)
                }

    return best_solution

def optimize_reflector_greedy(R_target,
                              candidates,
                              power_opt=None,
                              au_distance=1.0,
                              fusion_kw=50.0,
                              beamed_kw=0.0,
                              travel_time_yr=None,
                              fuel_decay_per_year=0.008):
    """
    Fast greedy heuristic with power system support.
    """
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
            "travel_time_yr": travel_time_yr,
            "available_power_kw": hybrid_power(au_distance,
                                               solar_area_m2=1e6,
                                               fusion_base_kw=fusion_kw,
                                               beamed_microwave_kw=beamed_kw,
                                               travel_time_yr=travel_time_yr,
                                               fuel_decay_per_year=fuel_decay_per_year)
        }
    return None

# =============================================================================
# Example / Test Cases
# =============================================================================
if __name__ == "__main__":
    candidates = [
        (0.91, 0.00015),   # 30 nm Al on polymer
        (0.88, 0.00006),   # Ultra-thin Al
        (0.12, 0.0008),    # Single dielectric
        (0.25, 0.0018),    # 5-layer stack
        (0.45, 0.0045),    # 15-layer V-coat
        (0.05, 0.00003),   # Protective coating
        (0.60, 0.012),     # Retroreflector film
    ]

    targets = [0.90, 0.95, 0.98, 0.995]
    power_opt = PowerOption(type="p-B11", mass_reduction=0.075)

    print("Multi-Layer Reflector Optimization (2025 Deep-Space Edition)\n")
    print("=" * 80)

    for R_t in targets:
        for au, time_yr in [(1.0, 1.0), (5.0, 5.0), (10.0, 10.0), (100.0, 100.0)]:
            print(f"\nTarget R ≥ {R_t:.3f} | AU = {au:4.1f} | Travel = {time_yr:.1f} yr | Power = {hybrid_power(au, travel_time_yr=time_yr):.0f} kW/km²")
            sol = optimize_reflector_bruteforce(R_t, candidates,
                                                power_opt=power_opt,
                                                au_distance=au,
                                                fusion_kw=100,
                                                beamed_kw=900 if au >= 10 else 0,
                                                travel_time_yr=time_yr)

            if sol:
                print(f"   Mass (optimized) : {sol['total_areal_mass_kg_m2']*1000:6.3f} g/m²")
                print(f"   Achieved R       : {sol['achieved_reflectivity']:.5f}")
                print(f"   Layers           : {sol['layers_used']}")
                print(f"   Power system     : {sol['power_option']} ({sol['available_power_kw']:.0f} kW)")
                print("   Stack            :", end="")
                for r, m in sol['selected_layers']:
                    print(f" ({r:.2f},{m*1000:4.1f}g)", end="")
                print()
            else:
                print("   → Impossible with current tech")
```​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​
