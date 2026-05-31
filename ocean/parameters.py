import math

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
CAMERA_AZIMUTH_DEG = 135.0
CAMERA_ELEVATION_DEG = 15.0
CAMERA_DISTANCE = 850.0
SUN_DIR = (1.0, 1.0, 0.5)
DEEP_COLOUR = (0.02, 0.15, 0.3)
SHALLOW_COLOUR = (0.1, 0.4, 0.5)

DEPTH_SCALE = 0.001

def orbit_to_camera_eye(azimuth_deg, elevation_deg, distance):
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    x = distance * math.cos(el) * math.sin(az)
    y = distance * math.sin(el)
    z = distance * math.cos(el) * math.cos(az)
    return (x, y, z)

def default_params():
    return {
        'grid_resolution':    GRID_RESOLUTION,
        'grid_size':          GRID_SIZE,
        'wind_speed':         WIND_SPEED,
        'wind_direction_deg': WIND_DIRECTION_DEG,
        'choppiness':         CHOPPINESS,
        'foam_threshold':     FOAM_THRESHOLD,
        'height_scale':       HEIGHT_SCALE,
        'depth_scale':        DEPTH_SCALE,
        'loop_period':        LOOP_PERIOD,
        'time':               0.0,
        'camera_azimuth_deg': CAMERA_AZIMUTH_DEG,
        'camera_elevation_deg': CAMERA_ELEVATION_DEG,
        'camera_distance':    CAMERA_DISTANCE,
        'camera_eye':         orbit_to_camera_eye(CAMERA_AZIMUTH_DEG, CAMERA_ELEVATION_DEG, CAMERA_DISTANCE),
        'sun_dir':            SUN_DIR,
        'deep_colour':        DEEP_COLOUR,
        'shallow_colour':     SHALLOW_COLOUR,
    }