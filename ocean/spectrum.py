import numpy as np

from ocean.parameters import G, PHILLIPS_A


def make_spatial_frequency_grid(grid_resolution, grid_size):
    spatial_freq_x = np.fft.fftfreq(grid_resolution) * (2 * np.pi * grid_resolution / grid_size)
    spatial_freq_y = np.fft.fftfreq(grid_resolution) * (2 * np.pi * grid_resolution / grid_size)
    freq_x, freq_y = np.meshgrid(spatial_freq_x, spatial_freq_y, indexing='ij')
    magnitude = np.sqrt(freq_x**2 + freq_y**2)
    return freq_x, freq_y, magnitude


def phillips_spectrum(freq_x, freq_y, magnitude, wind_speed, wind_direction_degrees):
    wind_direction = np.radians(wind_direction_degrees)
    wind_direction_x, wind_direction_y = np.cos(wind_direction), np.sin(wind_direction)

    dominant_wave_length = wind_speed**2 / G

    magnitude_nonzero = np.where(magnitude == 0, 1e-6, magnitude)

    wave_energy = PHILLIPS_A * np.exp(-1.0 / (magnitude_nonzero * dominant_wave_length)**2) / magnitude_nonzero**4

    wave_direction_x = freq_x / magnitude_nonzero
    wave_direction_y = freq_y / magnitude_nonzero

    alignment = wave_direction_x * wind_direction_x + wave_direction_y * wind_direction_y

    wave_energy *= alignment**2
    wave_energy[alignment < 0] = 0.0
    wave_energy[0,0] = 0.0

    return wave_energy

def generate_initial_amplitudes(wave_energy, seed=42):
    np.random.seed(seed)
    grid_resolution = wave_energy.shape[0]
    complex_noise = (np.random.randn(grid_resolution, grid_resolution) + 1j * np.random.randn(grid_resolution, grid_resolution)) / np.sqrt(2)
    initial_amplitudes = complex_noise * np.sqrt(wave_energy)
    initial_amplitudes_mirror = np.roll(np.flip(np.conj(initial_amplitudes)), 1, axis=(0, 1))
    return initial_amplitudes, initial_amplitudes_mirror