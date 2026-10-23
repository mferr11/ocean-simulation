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


def compute_surface_fields(freq_amplitudes, freq_x, freq_y, magnitude, foam_threshold, choppiness, height_scale, grid_resolution):
    magnitude_nonzero = np.where(magnitude == 0, 1e-6, magnitude)

    wave_height = np.real(np.fft.ifft2(freq_amplitudes)) * grid_resolution

    surface_tilt_x = np.real(np.fft.ifft2(1j * freq_x * freq_amplitudes)) * grid_resolution
    surface_tilt_y = np.real(np.fft.ifft2(1j * freq_y * freq_amplitudes)) * grid_resolution

    sideways_shift_x = np.real(np.fft.ifft2(1j * (freq_x / magnitude_nonzero) * freq_amplitudes)) * choppiness * height_scale * grid_resolution
    sideways_shift_y = np.real(np.fft.ifft2(1j * (freq_y / magnitude_nonzero) * freq_amplitudes)) * choppiness * height_scale * grid_resolution

    shift_x_rate_x = np.real(np.fft.ifft2(-freq_x**2 / magnitude_nonzero * freq_amplitudes)) * choppiness * height_scale * grid_resolution
    shift_y_rate_y = np.real(np.fft.ifft2(-freq_y**2 / magnitude_nonzero * freq_amplitudes)) * choppiness * height_scale * grid_resolution
    shift_x_rate_y = np.real(np.fft.ifft2(-freq_x * freq_y / magnitude_nonzero * freq_amplitudes)) * choppiness * height_scale * grid_resolution

    surface_compression = (1 + shift_x_rate_x) * (1 + shift_y_rate_y) - shift_x_rate_y**2
    foam_mask = _foam_from_compression(surface_compression, foam_threshold)

    return wave_height, surface_tilt_x, surface_tilt_y, sideways_shift_x, sideways_shift_y, foam_mask, surface_compression


def _foam_from_compression(surface_compression, foam_threshold):
    foam_margin = max(abs(foam_threshold) * 1.0, 0.01)
    t = np.clip((foam_threshold - surface_compression) / foam_margin, 0.0, 1.0)
    return (t * t * (3.0 - 2.0 * t)).astype(np.float32)


class OceanSimulation:
    """Real-time version of the spectrum -> time_evolve -> compute_surface_fields pipeline.

    Everything that doesn't depend on time is cached and only rebuilt when the
    parameters it depends on change. Each frame then only does the time evolution
    and 4 batched single-precision IFFTs (the 8 real output fields are packed in
    pairs as real + imaginary parts of one complex IFFT).

    `sim_resolution` can be lower than `grid_resolution`: the spectrum is then
    cropped to its low-frequency bins, giving a band-limited copy of the same
    ocean (same large waves, less fine detail) rather than a different random sea.
    """

    def __init__(self):
        self._noise_key = None
        self._spectrum_key = None
        self._noise = None

    def _update_noise(self, grid_resolution, sim_resolution):
        key = (grid_resolution, sim_resolution)
        if key == self._noise_key:
            return
        # Same random draw as generate_initial_amplitudes, so the full-resolution
        # ocean matches the original pipeline.
        N, M = grid_resolution, sim_resolution
        rng = np.random.RandomState(42)
        complex_noise = (rng.randn(N, N) + 1j * rng.randn(N, N)) / np.sqrt(2)
        keep = np.r_[0:M // 2, N - M // 2:N]
        self._noise = complex_noise[np.ix_(keep, keep)]
        self._noise_key = key
        self._spectrum_key = None

    def _update_spectrum(self, params, sim_resolution):
        key = (params['grid_resolution'], sim_resolution, params['grid_size'],
               params['wind_speed'], params['wind_direction_deg'], params['loop_period'])
        if key == self._spectrum_key:
            return
        from ocean.spectrum import make_spatial_frequency_grid, phillips_spectrum

        M = sim_resolution
        freq_x, freq_y, magnitude = make_spatial_frequency_grid(M, params['grid_size'])
        wave_energy = phillips_spectrum(
            freq_x, freq_y, magnitude, params['wind_speed'], params['wind_direction_deg']
        )
        initial_amplitudes = self._noise * np.sqrt(wave_energy)
        # The Nyquist row/column has no matching negative frequency, which would stop
        # the IFFT outputs from being purely real and break the pair packing below.
        initial_amplitudes[M // 2, :] = 0.0
        initial_amplitudes[:, M // 2] = 0.0
        initial_amplitudes_mirror = np.roll(np.flip(np.conj(initial_amplitudes)), 1, axis=(0, 1))

        self._initial_amplitudes = initial_amplitudes.astype(np.complex64)
        self._initial_amplitudes_mirror = initial_amplitudes_mirror.astype(np.complex64)
        self._oscillation_rate = compute_oscillation_rates(magnitude, params['loop_period']).astype(np.float32)

        # Field pairs (real part, imaginary part) of each packed IFFT:
        #   0: wave_height,       surface_tilt_x
        #   1: surface_tilt_y,    sideways_shift_x
        #   2: sideways_shift_y,  shift_x_rate_x
        #   3: shift_y_rate_y,    shift_x_rate_y
        k = np.where(magnitude == 0, 1e-6, magnitude)
        self._multipliers = np.stack([
            1.0 - freq_x,
            1j * freq_y - freq_x / k,
            1j * (freq_y - freq_x**2) / k,
            -(freq_y**2 + 1j * freq_x * freq_y) / k,
        ]).astype(np.complex64)

        # Matches the original `* grid_resolution` scaling at full resolution, and keeps
        # wave heights the same when the spectrum is cropped.
        self._scale = M * M / params['grid_resolution']
        self._spectrum_key = key

    def compute_fields(self, params, t, sim_resolution=None):
        import scipy.fft

        grid_resolution = params['grid_resolution']
        sim_resolution = min(sim_resolution or grid_resolution, grid_resolution)
        self._update_noise(grid_resolution, sim_resolution)
        self._update_spectrum(params, sim_resolution)

        phase = np.exp(1j * self._oscillation_rate * np.float32(t)).astype(np.complex64)
        freq_amplitudes = (self._initial_amplitudes * phase +
                           self._initial_amplitudes_mirror * np.conj(phase))

        packed = scipy.fft.ifft2(freq_amplitudes * self._multipliers,
                                 axes=(-2, -1), workers=-1, overwrite_x=True)
        packed *= self._scale

        shift_scale = params['choppiness'] * params['height_scale']
        surface_compression = ((1 + packed[2].imag * shift_scale) * (1 + packed[3].real * shift_scale)
                               - (packed[3].imag * shift_scale)**2)

        return {
            'wave_height':      packed[0].real,
            'surface_tilt_x':   packed[0].imag,
            'surface_tilt_y':   packed[1].real,
            'sideways_shift_x': packed[1].imag * shift_scale,
            'sideways_shift_y': packed[2].real * shift_scale,
            'foam_mask':        _foam_from_compression(surface_compression, params['foam_threshold']),
        }