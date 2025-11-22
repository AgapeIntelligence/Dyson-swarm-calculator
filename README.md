# Dyson Swarm Calculator

Open-source Python toolkit for engineering analysis of L1 sunshade constellations — from 1.8% solar radiation management (climate intervention) to full Dyson-swarm-scale stellar occlusion (Kardashev Type II pathway).

All models are order-of-magnitude physics for trade studies, roadmap planning, and back-of-the-envelope scaling — not mission-certified designs.

## Core Modules

- `sunshade_optimizer.py`      → Minimum number of sunshades & launch cadence for target η
- `l1_stationkeeping.py`       → SRP force, Δv, propellant mass (chemical → ion → ultra-light)
- `reflector_optimizer.py`     → Minimum areal mass multi-layer reflectors for target reflectivity
- `dyson_scalability.py`       → Full roadmap: climate fix → 100% Dyson swarm with self-replicating industry timelines
- `config.py`                  → Centralised constants (easy tweaking)

## Quick Start

```bash
git clone https://github.com/YOURUSERNAME/Dyson-swarm-calculator.git
cd Dyson-swarm-calculator
python dyson_scalability.py          # See the full progression in one table
python sunshade_optimizer.py         # Climate case + extreme scenarios

### 2. `config.py` (shared constants — all scripts can import from here)

```python
# config.py — Central constants for the Dyson-swarm-calculator suite
import numpy as np

# Physical
S0                  = 1361.0          # Solar constant at 1 AU [W/m²]
R_EARTH             = 6.371e6          # Earth radius [m]
A_EARTH             = np.pi * R_EARTH**2
T_EFF               = 255.0            # Effective temperature [K]
ECS_MULTIPLIER      = 1.8              # Surface warming ≈ 1.8 × effective (IPCC/GCM average)

# Engineering baselines (override per-script as needed)
DEFAULT_A_SHADE_M2      = 1e6          # 1 km² per occulter
DEFAULT_KAPPA           = 0.95         # Optical efficiency
DEFAULT_DENSITY_KG_M2   = 0.001        # 1 g/m² (near-term ultralight film)
DEFAULT_PAYLOAD_L1_T    = 50.0         # Starship effective payload to L1 [metric tons]
DEFAULT_FLIGHTS_PER_YR  = 20.0

