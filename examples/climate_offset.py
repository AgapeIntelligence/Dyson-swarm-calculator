from sunshade_optimizer import sunshade_optimizer

res = sunshade_optimizer(eta_target=0.018, areal_density_kgpm2=0.0005)
print("1.8% Climate Offset Case")
for k, v in res.items():
    print(f"{k:30}: {v:,.2f}")
