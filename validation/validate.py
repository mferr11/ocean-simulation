import numpy as np
import matplotlib.pyplot as plt
import os
from ocean.spectrum import make_spatial_frequency_grid, phillips_spectrum, generate_initial_amplitudes
from ocean.simulation import compute_oscillation_rates, time_evolve, compute_surface_fields
from ocean.parameters import GRID_RESOLUTION, GRID_SIZE, WIND_SPEED, WIND_DIRECTION_DEG, FOAM_THRESHOLD, PHILLIPS_A, CHOPPINESS

freq_x, freq_y, magnitude = make_spatial_frequency_grid(GRID_RESOLUTION, GRID_SIZE)
wave_energy = phillips_spectrum(freq_x, freq_y, magnitude, WIND_SPEED, WIND_DIRECTION_DEG)
initial_amplitudes, initial_amplitudes_mirror = generate_initial_amplitudes(wave_energy)
oscillation_rate = compute_oscillation_rates(magnitude)

freq_amplitudes = time_evolve(initial_amplitudes, initial_amplitudes_mirror, oscillation_rate, t=0.0)
height, surface_tilt_x, surface_tilt_y, sideways_shift_x, sideways_shift_y, foam_mask, surface_compression = \
    compute_surface_fields(freq_amplitudes, freq_x, freq_y, magnitude, FOAM_THRESHOLD)

assert np.allclose(np.fft.ifft2(freq_amplitudes).imag, 0, atol=1e-10), \
    "heightmap has imaginary residue — check initial_amplitudes_mirror"

print("--- Parameters ---")
print(f"  GRID_RESOLUTION:    {GRID_RESOLUTION}")
print(f"  GRID_SIZE:          {GRID_SIZE} m")
print(f"  WIND_SPEED:         {WIND_SPEED} m/s")
print(f"  WIND_DIRECTION_DEG: {WIND_DIRECTION_DEG}°")
print(f"  PHILLIPS_A:         {PHILLIPS_A}")
print(f"  CHOPPINESS:         {CHOPPINESS}")
print(f"  FOAM_THRESHOLD:     {FOAM_THRESHOLD}")
print("--- Surface compression ---")
print(f"  min: {surface_compression.min():.4f}")
print(f"  max: {surface_compression.max():.4f}")

fig, axes = plt.subplots(2, 3, figsize=(15, 11))
fig.suptitle(
    f"wind={WIND_SPEED}m/s  dir={WIND_DIRECTION_DEG}°  A={PHILLIPS_A}  "
    f"choppiness={CHOPPINESS}  foam_threshold={FOAM_THRESHOLD}  "
    f"grid={GRID_RESOLUTION}  patch={GRID_SIZE}m",
    fontsize=10
)

axes[0,0].imshow(height, cmap='RdBu');               axes[0,0].set_title('height')
axes[0,1].imshow(surface_tilt_x, cmap='RdBu');       axes[0,1].set_title('surface_tilt_x')
axes[0,2].imshow(surface_tilt_y, cmap='RdBu');       axes[0,2].set_title('surface_tilt_y')
axes[1,0].imshow(sideways_shift_x, cmap='RdBu');     axes[1,0].set_title('sideways_shift_x')
axes[1,1].imshow(surface_compression, cmap='viridis'); axes[1,1].set_title('surface_compression')
axes[1,2].imshow(foam_mask, cmap='gray');             axes[1,2].set_title('foam_mask')

plt.tight_layout()
output_path = 'images/validation.png'
os.makedirs('images', exist_ok=True)
plt.savefig(output_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved to {output_path}")