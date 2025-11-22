from dyson_scalability import dyson_scalability

densities = [0.005, 0.001, 0.0005, 0.0001]  # 5 → 0.1 g/m²
print("Full Dyson (η=1.0) sensitivity to areal density")
for d in densities:
    r = dyson_scalability(1.0, areal_density_kgpm2=d)
    print(f"{d*1000:4.1f} g/m² → {r['total_mass_t']/1e9:.1f} Gt mass, "
          f"{r['years_self_replicating_50pct']:.0f} years to build")
