import math
import tkinter as tk
from tkinter import ttk

from ocean.parameters import orbit_to_camera_eye

DEFAULT_CAMERA = (135.0, 15.0, 850.0)   # azimuth, elevation, distance

SLIDER_STEPS = {
    'wind_speed':           0.5,
    'wind_direction_deg':   1.0,
    'choppiness':           0.05,
    'foam_threshold':       0.05,
    'height_scale':         10.0,
    'time':                 0.1,
    'camera_azimuth_deg':   1.0,
    'camera_elevation_deg': 1.0,
    'camera_distance':      10.0,
}


class OceanControls(tk.Frame):
    def __init__(self, parent, params, on_change=None):
        super().__init__(parent)
        self.params = params
        self.on_change = on_change
        self.vars = {}
        self._build()

    def _build(self):
        ocean_sliders = [
            ("Wind Speed (m/s)",    'wind_speed',           1.0,   40.0,    0.5),
            ("Wind Direction (°)",  'wind_direction_deg',   0.0,   360.0,   1.0),
            ("Choppiness",          'choppiness',           0.0,   3.0,     0.05),
            ("Foam Threshold",      'foam_threshold',       0.0,   1.0,     0.01),
            ("Height Scale",        'height_scale',         0.0,   2000.0,  10.0),
            ("Time (s)",            'time',                 0.0,   20.0,    0.1),
        ]

        camera_sliders = [
            ("Azimuth (°)",         'camera_azimuth_deg',   0.0,   360.0,   1.0),
            ("Elevation (°)",       'camera_elevation_deg', 5.0,   89.0,    1.0),
            ("Distance",            'camera_distance',      100.0, 3000.0,  10.0),
        ]

        row = self._build_section("Ocean Parameters", ocean_sliders, start_row=0)
        self._build_separator(row)
        row = self._build_section("Camera", camera_sliders, start_row=row + 1)

        tk.Button(
            self, text="Reset Camera",
            command=self._reset_camera,
            relief='flat', bg='#e0e0e0',
            cursor='hand2', pady=3
        ).grid(row=row + 1, column=0, columnspan=3, padx=8, pady=(4, 0), sticky='ew')

    def _build_section(self, title, sliders, start_row):
        tk.Label(self, text=title, font=('Helvetica', 10, 'bold'), anchor='w').grid(
            row=start_row, column=0, columnspan=3, padx=8, pady=(10, 2), sticky='w'
        )
        for i, (label, key, min_val, max_val, resolution) in enumerate(sliders):
            row = start_row + 1 + i
            tk.Label(self, text=label, anchor='w', width=20).grid(
                row=row, column=0, padx=8, pady=4, sticky='w'
            )
            var = tk.DoubleVar(value=self.params.get(key, 0.0))
            self.vars[key] = var

            ttk.Scale(
                self, from_=min_val, to=max_val, variable=var,
                orient='horizontal', length=250,
                command=lambda val, k=key: self._on_slider(k)
            ).grid(row=row, column=1, padx=8, pady=4)

            tk.Label(self, textvariable=var, width=8, anchor='w').grid(
                row=row, column=2, padx=4, pady=4
            )
        return start_row + 1 + len(sliders)

    def _build_separator(self, row):
        ttk.Separator(self, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky='ew', padx=8, pady=4
        )

    def _on_slider(self, key):
        step = SLIDER_STEPS.get(key, 1.0)
        raw = self.vars[key].get()
        snapped = round(round(raw / step) * step, 10)
        self.vars[key].set(snapped)
        self.params[key] = snapped
        self._sync_camera()
        if self.on_change:
            self.on_change(key)

    def _sync_camera(self):
        self.params['camera_eye'] = orbit_to_camera_eye(
            self.vars['camera_azimuth_deg'].get(),
            self.vars['camera_elevation_deg'].get(),
            self.vars['camera_distance'].get(),
        )

    def _reset_camera(self):
        az, el, dist = DEFAULT_CAMERA
        self.vars['camera_azimuth_deg'].set(az)
        self.vars['camera_elevation_deg'].set(el)
        self.vars['camera_distance'].set(dist)
        self.params['camera_eye'] = orbit_to_camera_eye(az, el, dist)

    def get_params(self):
        for key, var in self.vars.items():
            self.params[key] = var.get()
        self._sync_camera()
        return self.params