import tkinter as tk
from tkinter import ttk

from ocean.parameters import default_params, orbit_to_camera_eye, sun_dir_from_angles

DEFAULT_CAMERA = (135.0, 25.0, 1750.0, 0.0)
DEFAULT_SUN = (315.0, 60.0)

SLIDER_STEPS = {
    'wind_speed':           0.5,
    'wind_direction_deg':   1.0,
    'choppiness':           0.05,
    'foam_threshold':       0.05,
    'height_scale':         0.1,
    'time':                 0.1,
    'camera_azimuth_deg':   1.0,
    'camera_elevation_deg': 1.0,
    'camera_distance':      10.0,
    'camera_y_offset':      10.0,
    'sun_azimuth_deg':      1.0,
    'sun_elevation_deg':    1.0,
}

_BG      = '#1e1e2e'
_SECTION = '#2a2a3e'
_FG      = '#cdd6f4'
_ACCENT  = '#89b4fa'
_RESET   = '#6c7086'
_FONT    = 'Segoe UI'

_OCEAN_KEYS  = ['wind_speed', 'wind_direction_deg', 'choppiness',
                'foam_threshold', 'height_scale', 'time']
_COLOUR_KEYS = ['deep_colour', 'shallow_colour']
_SUN_KEYS    = ['sun_azimuth_deg', 'sun_elevation_deg']


def _rgb_to_hex(rgb_0_1):
    return '#%02x%02x%02x' % tuple(min(255, int(round(c * 255))) for c in rgb_0_1)


def _hex_to_rgb01(hex_str):
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def _decimal_places(resolution):
    s = str(resolution)
    if '.' not in s:
        return 0
    return len(s.split('.')[-1].rstrip('0') or '0')


class OceanControls(tk.Frame):
    def __init__(self, parent, params, on_change=None):
        super().__init__(parent, bg=_BG)
        self.params = params
        self.on_change = on_change
        self.vars = {}
        self.fmt_vars = {}        # key → (StringVar, int decimals)
        self.colour_vars = {}     # key → current hex string
        self._colour_swatches = {}
        self._build()

    def _build(self):
        ocean_sliders = [
            ("Wind Speed (m/s)",    'wind_speed',           1.0,   40.0,    1.0),
            ("Wind Direction (°)",  'wind_direction_deg',   0.0,   360.0,   1.0),
            ("Choppiness",          'choppiness',           0.0,   3.0,     0.05),
            ("Foam Threshold",      'foam_threshold',       0.0,   1.0,     0.05),
            ("Height Scale",        'height_scale',         0.0,   10.0,    0.1),
            ("Time (s)",            'time',                 0.0,   20.0,    0.1),
        ]

        colour_params = [
            ("Deep Colour",    'deep_colour'),
            ("Shallow Colour", 'shallow_colour'),
        ]

        camera_sliders = [
            ("Azimuth (°)",         'camera_azimuth_deg',   0.0,   360.0,   1.0),
            ("Elevation (°)",       'camera_elevation_deg', 0.0,   90.0,    1.0),
            ("Distance",            'camera_distance',      100.0, 3000.0,  10.0),
            ("Y Offset",            'camera_y_offset',      0.0,   1000.0,   10.0),
        ]

        sun_sliders = [
            ("Azimuth (°)",   'sun_azimuth_deg',   0.0,  360.0, 1.0),
            ("Elevation (°)", 'sun_elevation_deg',  0.0,   90.0, 1.0),
        ]

        row = self._build_resolution_selector(start_row=0)
        self._build_separator(row)
        row = self._build_slider_section("Ocean Parameters", ocean_sliders,
                                         start_row=row + 1, reset_cmd=self._reset_ocean)
        self._build_separator(row)
        row = self._build_colour_section("Ocean Colour", colour_params,
                                         start_row=row + 1, reset_cmd=self._reset_colours)
        self._build_separator(row)
        row = self._build_slider_section("Camera", camera_sliders,
                                         start_row=row + 1, reset_cmd=self._reset_camera)
        self._build_separator(row)
        self._build_slider_section("Sun", sun_sliders,
                                   start_row=row + 1, reset_cmd=self._reset_sun)

    def _build_resolution_selector(self, start_row):
        self._section_header(start_row, "Resolution")
        frame = tk.Frame(self, bg=_BG)
        frame.grid(row=start_row + 1, column=0, columnspan=3, padx=10, pady=6, sticky='ew')

        self._res_buttons = {}
        for label, value in [('Low  (512)', 512), ('Med  (1024)', 1024), ('High  (2048)', 2048)]:
            btn = tk.Button(
                frame, text=label, font=(_FONT, 9),
                command=lambda v=value: self._set_resolution(v),
                relief='flat', cursor='hand2',
                bd=0, highlightthickness=0, pady=4, padx=10,
            )
            btn.pack(side='left', padx=2, fill='x', expand=True)
            self._res_buttons[value] = btn

        self._update_resolution_buttons()
        return start_row + 2

    def _set_resolution(self, value):
        self.params['grid_resolution'] = value
        self._update_resolution_buttons()
        if self.on_change:
            self.on_change('grid_resolution')

    def _update_resolution_buttons(self):
        current = self.params.get('grid_resolution', 512)
        for value, btn in self._res_buttons.items():
            if value == current:
                btn.configure(bg=_ACCENT, fg='#1e1e2e', font=(_FONT, 9, 'bold'))
            else:
                btn.configure(bg=_SECTION, fg=_FG, font=(_FONT, 9))

    def _section_header(self, row, title, reset_cmd=None):
        frame = tk.Frame(self, bg=_SECTION, padx=6, pady=4)
        frame.grid(row=row, column=0, columnspan=3, padx=4, pady=(12, 2), sticky='ew')
        tk.Label(frame, text=title, font=(_FONT, 9, 'bold'),
                 fg=_ACCENT, bg=_SECTION, anchor='w').pack(side='left', fill='x', expand=True)
        if reset_cmd:
            tk.Button(
                frame, text="↺ Reset", font=(_FONT, 8),
                command=reset_cmd,
                relief='flat', bg=_SECTION, fg=_RESET,
                activebackground='#3a3a5e', activeforeground=_FG,
                cursor='hand2', pady=0, padx=4,
                bd=0, highlightthickness=0,
            ).pack(side='right')

    def _build_slider_section(self, title, sliders, start_row, reset_cmd=None):
        self._section_header(start_row, title, reset_cmd)
        for i, (label, key, min_val, max_val, resolution) in enumerate(sliders):
            row = start_row + 1 + i
            tk.Label(self, text=label, anchor='w', width=18,
                     bg=_BG, fg=_FG, font=(_FONT, 9)).grid(
                row=row, column=0, padx=(10, 4), pady=3, sticky='w'
            )
            var = tk.DoubleVar(value=self.params.get(key, 0.0))
            self.vars[key] = var

            dec = _decimal_places(resolution)
            fmt_var = tk.StringVar(value=f"{var.get():.{dec}f}")
            self.fmt_vars[key] = (fmt_var, dec)

            ttk.Scale(
                self, from_=min_val, to=max_val, variable=var,
                orient='horizontal', length=190,
                command=lambda val, k=key, fv=fmt_var, d=dec: self._on_slider(k, fv, d),
            ).grid(row=row, column=1, padx=4, pady=3)

            tk.Label(self, textvariable=fmt_var, width=6, anchor='e',
                     bg=_BG, fg=_ACCENT, font=(_FONT, 9, 'bold')).grid(
                row=row, column=2, padx=(0, 10), pady=3
            )
        return start_row + 1 + len(sliders)

    def _build_colour_section(self, title, colour_params, start_row, reset_cmd=None):
        self._section_header(start_row, title, reset_cmd)
        for i, (label, key) in enumerate(colour_params):
            row = start_row + 1 + i
            tk.Label(self, text=label, anchor='w', width=18,
                     bg=_BG, fg=_FG, font=(_FONT, 9)).grid(
                row=row, column=0, padx=(10, 4), pady=5, sticky='w'
            )
            hex_color = _rgb_to_hex(self.params.get(key, (0.0, 0.0, 0.0)))
            self.colour_vars[key] = hex_color

            swatch = tk.Label(self, bg=hex_color, width=5, relief='groove', cursor='hand2')
            swatch.grid(row=row, column=1, padx=4, pady=5, sticky='w')
            self._colour_swatches[key] = swatch
            swatch.bind('<Button-1>', lambda _, k=key: self._pick_colour(k))

            tk.Button(
                self, text="Pick", font=(_FONT, 8),
                command=lambda k=key: self._pick_colour(k),
                relief='flat', bg=_SECTION, fg=_FG,
                activebackground='#3a3a5e', activeforeground=_FG,
                cursor='hand2', pady=3, padx=10,
                bd=0, highlightthickness=0,
            ).grid(row=row, column=2, padx=(0, 10), pady=5, sticky='e')
        return start_row + 1 + len(colour_params)

    def _pick_colour(self, key):
        from tkinter.colorchooser import askcolor
        result = askcolor(color=self.colour_vars.get(key, '#000000'), title='Pick colour')
        if result[1] is not None:
            hex_color = result[1]
            self.colour_vars[key] = hex_color
            self._colour_swatches[key].configure(bg=hex_color)
            self.params[key] = _hex_to_rgb01(hex_color)
            if self.on_change:
                self.on_change(key)

    def _build_separator(self, row):
        ttk.Separator(self, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky='ew', padx=8, pady=2
        )

    def _on_slider(self, key, fmt_var, decimals):
        step = SLIDER_STEPS.get(key, 1.0)
        raw = self.vars[key].get()
        snapped = round(round(raw / step) * step, 10)
        self.vars[key].set(snapped)
        self.params[key] = snapped
        fmt_var.set(f"{snapped:.{decimals}f}")
        self._sync_camera()
        self._sync_sun()
        if self.on_change:
            self.on_change(key)

    def _reset_ocean(self):
        defaults = default_params()
        for key in _OCEAN_KEYS:
            val = defaults[key]
            self.vars[key].set(val)
            self.params[key] = val
            if key in self.fmt_vars:
                fmt_var, dec = self.fmt_vars[key]
                fmt_var.set(f"{val:.{dec}f}")
        if self.on_change:
            self.on_change(None)

    def _reset_colours(self):
        defaults = default_params()
        for key in _COLOUR_KEYS:
            rgb = defaults[key]
            hex_color = _rgb_to_hex(rgb)
            self.colour_vars[key] = hex_color
            self._colour_swatches[key].configure(bg=hex_color)
            self.params[key] = rgb
        if self.on_change:
            self.on_change(None)

    def _sync_camera(self):
        self.params['camera_eye'] = orbit_to_camera_eye(
            self.vars['camera_azimuth_deg'].get(),
            self.vars['camera_elevation_deg'].get(),
            self.vars['camera_distance'].get(),
        )

    def _sync_sun(self):
        self.params['sun_dir'] = sun_dir_from_angles(
            self.vars['sun_azimuth_deg'].get(),
            self.vars['sun_elevation_deg'].get(),
        )

    def _reset_camera(self):
        az, el, dist, y_off = DEFAULT_CAMERA
        self.vars['camera_azimuth_deg'].set(az)
        self.vars['camera_elevation_deg'].set(el)
        self.vars['camera_distance'].set(dist)
        self.vars['camera_y_offset'].set(y_off)
        self.params['camera_eye'] = orbit_to_camera_eye(az, el, dist)
        self.params['camera_y_offset'] = y_off
        for key, val in [('camera_azimuth_deg', az),
                         ('camera_elevation_deg', el),
                         ('camera_distance', dist),
                         ('camera_y_offset', y_off)]:
            if key in self.fmt_vars:
                fmt_var, dec = self.fmt_vars[key]
                fmt_var.set(f"{val:.{dec}f}")
        if self.on_change:
            self.on_change(None)

    def _reset_sun(self):
        az, el = DEFAULT_SUN
        self.vars['sun_azimuth_deg'].set(az)
        self.vars['sun_elevation_deg'].set(el)
        self.params['sun_dir'] = sun_dir_from_angles(az, el)
        for key, val in [('sun_azimuth_deg', az), ('sun_elevation_deg', el)]:
            if key in self.fmt_vars:
                fmt_var, dec = self.fmt_vars[key]
                fmt_var.set(f"{val:.{dec}f}")
        if self.on_change:
            self.on_change(None)

    def get_params(self):
        for key, var in self.vars.items():
            self.params[key] = var.get()
        self._sync_camera()
        self._sync_sun()
        return self.params
