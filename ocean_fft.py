import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

# Grid Parameters #
NUMBER_OF_GRIDPOINTS = 256                  # Grid Resolution
OCEAN_SIZE = 500.0                          # Grid Size (m)

# Physical Parameters #
WIND_SPEED = 20.0                           #m/s
WIND_DIRECTION = np.array([1.0, 0.0])       # Normalised Unit Vector
GRAVITY = 9.81

# Utility #
SMALL = 1e-6                                #Avoid division by 0

# ---------------------------------------------------------------------------
# Wave Vector Grid
# ---------------------------------------------------------------------------

# These frequency grid steps are just indices, not actual frequencies. We're 
# pretty much just setting up coordinates
frequency_indices_1d = np.fft.fftfreq(NUMBER_OF_GRIDPOINTS, d=1.0 / NUMBER_OF_GRIDPOINTS)

frequency_indices_x, frequency_indices_y = np.meshgrid(
    frequency_indices_1d, 
    frequency_indices_1d
)

# Convert from our coordinates into wave vectors. Each cell now tells us "this 
# wave completes this many radians per metre"
wave_vector_x = (2.0 * np.pi / OCEAN_SIZE) * frequency_indices_x
wave_vector_y = (2.0 * np.pi / OCEAN_SIZE) * frequency_indices_y

# The wave number is the magnitude of the wave vector, and tells us the wave's 
# spatial frequency. 
# High magnitude = short wavelength, low magnitude = long wavelength
wave_number = np.sqrt(wave_vector_x**2 + wave_vector_y**2)

# Avoid division by zero later
wave_number[wave_number < SMALL] = SMALL