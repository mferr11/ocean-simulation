"""Launch the Ocean Renderer with a sunset test preset."""
import ocean.parameters as _params_module
from ocean.parameters import (
    default_params as _orig_default_params,
    orbit_to_camera_eye,
    sun_elevation_from_time,
    sun_azimuth_from_time,
    sun_dir_from_angles,
    moon_dir_from_sun_dir,
)

_NIGHT_PRESET = {
    'camera_azimuth_deg':   135.0,
    'camera_elevation_deg': 6.0,
    'camera_distance':      380.0,
    'camera_y_offset':      0.0,
    'sun_azimuth_deg':      315.0,
    'time_of_day':          17.75,  # 17:45
}

def _night_default_params():
    p = _orig_default_params()
    p.update(_NIGHT_PRESET)
    p['camera_eye'] = orbit_to_camera_eye(
        p['camera_azimuth_deg'], p['camera_elevation_deg'], p['camera_distance'],
    )
    el = sun_elevation_from_time(p['time_of_day'])
    az = sun_azimuth_from_time(p['time_of_day']) + p['sun_azimuth_deg']
    p['sun_elevation_deg'] = el
    p['sun_dir']  = sun_dir_from_angles(az, el)
    p['moon_dir'] = moon_dir_from_sun_dir(p['sun_dir'])
    return p

_params_module.default_params = _night_default_params

from ui.app import OceanApp

if __name__ == '__main__':
    app = OceanApp()
    app.run()
