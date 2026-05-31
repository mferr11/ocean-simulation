import numpy as np
from ocean.parameters import G


def compute_oscillation_rates(magnitude, loop_period=20.0):
    import math
    raw_rate = np.sqrt(G * np.where(magnitude == 0, 0.0, magnitude))
    base_frequency = 2 * math.pi / loop_period
    # Snap each rate to nearest multiple of base_frequency
    snapped_rate = np.round(raw_rate / base_frequency) * base_frequency
    return snapped_rate


def time_evolve(initial_amplitudes, initial_amplitudes_mirror, oscillation_rate, t):
    freq_amplitudes = (
        initial_amplitudes * np.exp(1j * oscillation_rate * t) +
        initial_amplitudes_mirror * np.exp(-1j * oscillation_rate * t)
    )
    return freq_amplitudes


def compute_surface_fields(freq_amplitudes, freq_x, freq_y, magnitude, foam_threshold, choppiness, height_scale):
    magnitude_nonzero = np.where(magnitude == 0, 1e-6, magnitude)

    wave_height = np.real(np.fft.ifft2(freq_amplitudes))

    surface_tilt_x = np.real(np.fft.ifft2(1j * freq_x * freq_amplitudes))
    surface_tilt_y = np.real(np.fft.ifft2(1j * freq_y * freq_amplitudes))

    sideways_shift_x = np.real(np.fft.ifft2(1j * (freq_x / magnitude_nonzero) * freq_amplitudes)) * choppiness * height_scale
    sideways_shift_y = np.real(np.fft.ifft2(1j * (freq_y / magnitude_nonzero) * freq_amplitudes)) * choppiness * height_scale

    shift_x_rate_x = np.real(np.fft.ifft2(-freq_x**2 / magnitude_nonzero * freq_amplitudes)) * choppiness * height_scale
    shift_y_rate_y = np.real(np.fft.ifft2(-freq_y**2 / magnitude_nonzero * freq_amplitudes)) * choppiness * height_scale
    shift_x_rate_y = np.real(np.fft.ifft2(-freq_x * freq_y / magnitude_nonzero * freq_amplitudes)) * choppiness * height_scale

    surface_compression = (1 + shift_x_rate_x) * (1 + shift_y_rate_y) - shift_x_rate_y**2
    foam_mask = (surface_compression < foam_threshold).astype(np.float32)

    return wave_height, surface_tilt_x, surface_tilt_y, sideways_shift_x, sideways_shift_y, foam_mask, surface_compression