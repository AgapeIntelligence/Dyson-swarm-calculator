from dyson_scalability import dyson_scalability

etas = [0.018, 0.1, 0.3, 0.5, 0.99, 1.0]
for eta in etas:
    r = dyson_scalability(eta, areal_density_kgpm2=0.0005)
    print(f"η={eta:4.2%} → {r['total_mass_t']/1e9:.1f} Gt | "
          f"{r['years_exponential_launches_20pct']:.0f} yr (launches) | "
          f"{r['years_self_replicating_50pct'] if r['years_self_replicating_50pct']<1e6 else '∞'} yr (self-rep)")
