from imgui_bundle import imgui

from ocean.parameters import default_params

# (label, key, min, max, display format)
OCEAN_SLIDERS = [
    ("Wind Speed (m/s)",   'wind_speed',         1.0, 100.0, '%.1f'),
    ("Wind Direction (deg)", 'wind_direction_deg', 0.0, 360.0, '%.0f'),
    ("Choppiness",         'choppiness',         0.0,   5.0, '%.2f'),
    ("Foam Threshold",     'foam_threshold',     0.0,   1.0, '%.2f'),
    ("Height Scale",       'height_scale',       0.0,  50.0, '%.1f'),
]

CAMERA_SLIDERS = [
    ("Azimuth (deg)##camera", 'camera_azimuth_deg',      0.0,  360.0, '%.0f'),
    ("Elevation (deg)",       'camera_elevation_deg',    0.0,   90.0, '%.0f'),
    ("Distance",            'camera_distance',       100.0, 3000.0, '%.0f'),
    ("Y Offset",            'camera_y_offset',     -1000.0, 1000.0, '%.0f'),
]

LOOP_PERIOD_STEP = 5.0

_OCEAN_KEYS  = [key for _, key, *_ in OCEAN_SLIDERS] + ['loop_period']
_COLOUR_KEYS = ['deep_colour', 'shallow_colour']
_CAMERA_KEYS = [key for _, key, *_ in CAMERA_SLIDERS]
_SUN_KEYS    = ['sun_azimuth_deg', 'time_of_day']

_MUTED = imgui.ImVec4(0.42, 0.44, 0.53, 1.0)


def _format_time_of_day(hours):
    h = int(hours) % 24
    m = int((hours - int(hours)) * 60)
    return f"{h:02d}:{m:02d}"


class OceanControls:
    """ImGui panel for the ocean, colour, camera, sun and quality settings.

    Edits `params` in place every frame; the caller is responsible for
    recomputing derived values (see `update_derived`).
    """

    def __init__(self, params):
        self.params = params

    def draw(self, live_resolution):
        """Draw all sections. Returns the (possibly changed) live grid resolution."""
        live_resolution = self._draw_quality(live_resolution)
        self._draw_ocean()
        self._draw_colours()
        self._draw_sliders("Camera", CAMERA_SLIDERS, _CAMERA_KEYS,
                           hint="Drag the ocean to orbit, scroll to zoom")
        self._draw_sun()
        return live_resolution

    # --- Sections ---

    def _header(self, title, reset_keys):
        open_ = imgui.collapsing_header(title, imgui.TreeNodeFlags_.default_open)
        if open_ and reset_keys and imgui.small_button(f"Reset##{title}"):
            self._reset(reset_keys)
        return open_

    def _draw_quality(self, live_resolution):
        if not self._header("Quality", None):
            return live_resolution
        imgui.text("Live grid")
        for value in (128, 256, 512):
            imgui.same_line()
            if imgui.radio_button(f"{value}##live", live_resolution == value):
                live_resolution = value

        imgui.text("Export grid")
        for value in (512, 1024, 2048):
            imgui.same_line()
            if imgui.radio_button(f"{value}##export", self.params['grid_resolution'] == value):
                self.params['grid_resolution'] = value

        imgui.text("Export foam")
        for value in (1, 2, 4):
            imgui.same_line()
            if imgui.radio_button(f"{value}x##foam", self.params['foam_upsample'] == value):
                self.params['foam_upsample'] = value
        imgui.text_colored(_MUTED, "Export settings apply to saved images and videos.")
        return live_resolution

    def _draw_ocean(self):
        if not self._header("Ocean", _OCEAN_KEYS):
            return
        self._sliders(OCEAN_SLIDERS)
        changed, value = imgui.slider_float("Loop Period (s)", self.params['loop_period'], 5.0, 60.0, '%.0f')
        if changed:
            self.params['loop_period'] = max(LOOP_PERIOD_STEP, round(value / LOOP_PERIOD_STEP) * LOOP_PERIOD_STEP)

    def _draw_colours(self):
        if not self._header("Ocean Colour", _COLOUR_KEYS):
            return
        for label, key in (("Deep", 'deep_colour'), ("Shallow", 'shallow_colour')):
            changed, colour = imgui.color_edit3(label, list(self.params[key]))
            if changed:
                self.params[key] = tuple(colour)

    def _draw_sliders(self, title, sliders, keys, hint=None):
        if not self._header(title, keys):
            return
        self._sliders(sliders)
        if hint:
            imgui.text_colored(_MUTED, hint)

    def _draw_sun(self):
        if not self._header("Sun", _SUN_KEYS):
            return
        self._sliders([("Azimuth (deg)##sun", 'sun_azimuth_deg', 0.0, 360.0, '%.0f')])
        tod = self.params['time_of_day']
        changed, value = imgui.slider_float("Time of Day", tod, 0.0, 24.0, _format_time_of_day(tod))
        if changed:
            self.params['time_of_day'] = value

    # --- Helpers ---

    def _sliders(self, sliders):
        for label, key, min_val, max_val, fmt in sliders:
            changed, value = imgui.slider_float(label, self.params[key], min_val, max_val, fmt)
            if changed:
                self.params[key] = value

    def _reset(self, keys):
        defaults = default_params()
        for key in keys:
            self.params[key] = defaults[key]
