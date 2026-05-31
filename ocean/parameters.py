G = 9.81
PHILLIPS_A = 0.0081
WIND_SPEED = 20.0
WIND_DIRECTION_DEG = 0.0
CHOPPINESS = 1.2
FOAM_THRESHOLD = 0.6
GRID_RESOLUTION = 256
GRID_SIZE = 500.0
HEIGHT_SCALE = 500.0
LOOP_PERIOD = 20.0

CAMERA_EYE = (600, 250, 600)
SUN_DIR = (1.0, 1.0, 0.5)
DEEP_COLOUR = (0.02, 0.15, 0.3)
SHALLOW_COLOUR = (0.1, 0.4, 0.5)

DEPTH_SCALE = 0.001

def default_params():
    return {
        'grid_resolution':   GRID_RESOLUTION,
        'grid_size':         GRID_SIZE,
        'wind_speed':        WIND_SPEED,
        'wind_direction_deg': WIND_DIRECTION_DEG,
        'choppiness':        CHOPPINESS,
        'foam_threshold':    FOAM_THRESHOLD,
        'height_scale':      HEIGHT_SCALE,
        'depth_scale':       DEPTH_SCALE,
        'loop_period':       LOOP_PERIOD,
        'time':              0.0,
        'camera_eye':        CAMERA_EYE,
        'sun_dir':           SUN_DIR,
        'deep_colour':       DEEP_COLOUR,
        'shallow_colour':    SHALLOW_COLOUR,
    }