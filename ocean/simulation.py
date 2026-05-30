import numpy as np
from ocean.parameters import G


def compute_oscillation_rates(magnitude):
    oscillation_rate = np.sqrt(G * np.where(magnitude == 0, 0.0, magnitude))
    return oscillation_rate


def time_evolve(initial_amplitudes, initial_amplitudes_mirror, oscillation_rate, t):
    freq_amplitudes = (
        initial_amplitudes * np.exp(1j * oscillation_rate * t) +
        initial_amplitudes_mirror * np.exp(-1j * oscillation_rate * t)
    )
    return freq_amplitudes


def compute_surface_fields(freq_amplitudes, freq_x, freq_y, magnitude, foam_threshold):
    magnitude_nonzero = np.where(magnitude == 0, 1e-6, magnitude)

    height = np.real(np.fft.ifft2(freq_amplitudes))

    surface_tilt_x = np.real(np.fft.ifft2(1j * freq_x * freq_amplitudes))
    surface_tilt_y = np.real(np.fft.ifft2(1j * freq_y * freq_amplitudes))

    sideways_shift_x = np.real(np.fft.ifft2(1j * (freq_x / magnitude_nonzero) * freq_amplitudes))
    sideways_shift_y = np.real(np.fft.ifft2(1j * (freq_y / magnitude_nonzero) * freq_amplitudes))

    shift_x_rate_x = np.real(np.fft.ifft2(-freq_x**2 / magnitude_nonzero * freq_amplitudes))
    shift_y_rate_y = np.real(np.fft.ifft2(-freq_y**2 / magnitude_nonzero * freq_amplitudes))
    shift_x_rate_y = np.real(np.fft.ifft2(-freq_x * freq_y / magnitude_nonzero * freq_amplitudes))

    surface_compression = (1 + shift_x_rate_x) * (1 + shift_y_rate_y) - shift_x_rate_y**2
    foam_mask = (surface_compression < foam_threshold).astype(np.float32)

    return height, surface_tilt_x, surface_tilt_y, sideways_shift_x, sideways_shift_y, foam_mask, surface_compression