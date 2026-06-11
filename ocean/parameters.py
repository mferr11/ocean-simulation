import math

G = 9.81
PHILLIPS_A = 0.0081
WIND_SPEED = 20.0
WIND_DIRECTION_DEG = 0.0
CHOPPINESS = 1.2
FOAM_THRESHOLD = 0.5
FOAM_UPSAMPLE = 2
GRID_RESOLUTION = 512
GRID_SIZE = 512.0
HEIGHT_SCALE = 2.0
LOOP_PERIOD = 30.0

CAMERA_EYE = (600, 250, 600)
CAMERA_AZIMUTH_DEG = 135.0
CAMERA_ELEVATION_DEG = 25.0
CAMERA_DISTANCE = 1250.0
CAMERA_Y_OFFSET = 0.0
SUN_AZIMUTH_DEG = 315.0
SUN_ELEVATION_DEG = 60.0
TIME_OF_DAY = 12.0
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

def sun_elevation_from_time(time_of_day_hours):
    return 90.0 * math.sin(
        (time_of_day_hours / 24.0) * 2.0 * math.pi - math.pi / 2.0
    )

def sun_azimuth_from_time(time_of_day_hours):
    # East (90°) at 6h, south (180°) at noon, west (270°) at 18h
    return 90.0 + (time_of_day_hours - 6.0) * 15.0

def moon_dir_from_sun_dir(sun_dir):
    sx, sy, sz = sun_dir
    return (-sx, -sy, -sz)

def sun_dir_from_angles(azimuth_deg, elevation_deg):
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    x = math.cos(el) * math.sin(az)
    y = math.sin(el)
    z = math.cos(el) * math.cos(az)
    return (x, y, z)

def default_params():
    _sun_el  = sun_elevation_from_time(TIME_OF_DAY)
    _sun_az  = sun_azimuth_from_time(TIME_OF_DAY)  # auto-derived; azimuth slider is offset
    _sun_dir = sun_dir_from_angles(_sun_az, _sun_el)
    return {
        'grid_resolution':    GRID_RESOLUTION,
        'grid_size':          GRID_SIZE,
        'wind_speed':         WIND_SPEED,
        'wind_direction_deg': WIND_DIRECTION_DEG,
        'choppiness':         CHOPPINESS,
        'foam_threshold':     FOAM_THRESHOLD,
        'foam_upsample':      FOAM_UPSAMPLE,
        'height_scale':       HEIGHT_SCALE,
        'depth_scale':        DEPTH_SCALE,
        'loop_period':        LOOP_PERIOD,
        'time':               0.0,
        'camera_azimuth_deg': CAMERA_AZIMUTH_DEG,
        'camera_elevation_deg': CAMERA_ELEVATION_DEG,
        'camera_distance':    CAMERA_DISTANCE,
        'camera_y_offset':    CAMERA_Y_OFFSET,
        'camera_eye':         orbit_to_camera_eye(CAMERA_AZIMUTH_DEG, CAMERA_ELEVATION_DEG, CAMERA_DISTANCE),
        'sun_azimuth_deg':    SUN_AZIMUTH_DEG,
        'sun_elevation_deg':  _sun_el,
        'time_of_day':        TIME_OF_DAY,
        'sun_dir':            _sun_dir,
        'moon_dir':           moon_dir_from_sun_dir(_sun_dir),
        'deep_colour':        DEEP_COLOUR,
        'shallow_colour':     SHALLOW_COLOUR,
    }