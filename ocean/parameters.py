import math

G = 9.81
PHILLIPS_A = 0.0081
WIND_SPEED = 20.0
WIND_DIRECTION_DEG = 0.0
CHOPPINESS = 1.2
FOAM_THRESHOLD = 0.5
GRID_RESOLUTION = 512
GRID_SIZE = 500.0
HEIGHT_SCALE = 2.0
LOOP_PERIOD = 10.0

CAMERA_EYE = (600, 250, 600)
CAMERA_AZIMUTH_DEG = 135.0
CAMERA_ELEVATION_DEG = 25.0
CAMERA_DISTANCE = 850.0
SUN_AZIMUTH_DEG = 315.0
SUN_ELEVATION_DEG = 60.0
DEEP_COLOUR = (0.02, 0.15, 0.3)
SHALLOW_COLOUR = (0.1, 0.4, 0.5)

DEPTH_SCALE = 0.05

def orbit_to_camera_eye(azimuth_deg, elevation_deg, distance):
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    x = distance * math.cos(el) * math.sin(az)
    y = distance * math.sin(el)
    z = distance * math.cos(el) * math.cos(az)
    return (x, y, z)

def sun_dir_from_angles(azimuth_deg, elevation_deg):
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    x = math.cos(el) * math.sin(az)
    y = math.sin(el)
    z = math.cos(el) * math.cos(az)
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
        'sun_azimuth_deg':    SUN_AZIMUTH_DEG,
        'sun_elevation_deg':  SUN_ELEVATION_DEG,
        'sun_dir':            sun_dir_from_angles(SUN_AZIMUTH_DEG, SUN_ELEVATION_DEG),
        'deep_colour':        DEEP_COLOUR,
        'shallow_colour':     SHALLOW_COLOUR,
    }