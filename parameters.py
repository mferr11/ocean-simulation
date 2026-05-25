# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import numpy as np

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