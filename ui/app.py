import os
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from ocean.parameters import default_params
from rendering.renderer import render
from ui.controls import OceanControls

_BG     = '#1e1e2e'
_FG     = '#cdd6f4'
_ACCENT = '#89b4fa'
_MUTED  = '#6c7086'
_FONT   = 'Segoe UI'


def _configure_style():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('.', background=_BG, foreground=_FG, font=(_FONT, 9))
    style.configure('TScale',
        background=_BG, troughcolor='#313244',
        sliderlength=14, sliderrelief='flat',
    )
    style.map('TScale', background=[('active', _BG)])
    style.configure('TSeparator', background='#313244')
    style.configure('TButton',
        background='#313244', foreground=_FG,
        relief='flat', padding=4,
    )
    style.map('TButton',
        background=[('active', '#45475a')],
        foreground=[('active', _FG)],
    )


class OceanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ocean Renderer")
        self.resizable(False, False)
        self.configure(bg=_BG)

        _configure_style()

        self.params = default_params()
        self.render_image = None
        self.last_image = None
        self._render_job = None
        self._anim_cancel = threading.Event()

        self._build()

    def _build(self):
        # Left panel — controls
        left = tk.Frame(self, bg=_BG, padx=8, pady=10)
        left.grid(row=0, column=0, sticky='ns')

        tk.Label(left, text="Ocean Renderer", font=(_FONT, 13, 'bold'),
                 fg=_ACCENT, bg=_BG).pack(anchor='w', pady=(0, 6))

        self.controls = OceanControls(left, self.params, on_change=self._schedule_render)
        self.controls.pack()

        ttk.Separator(left, orient='horizontal').pack(fill='x', pady=8)

        # FPS row
        fps_frame = tk.Frame(left, bg=_BG)
        fps_frame.pack(fill='x', pady=(0, 8))
        tk.Label(fps_frame, text="Animation FPS", anchor='w', width=16,
                 bg=_BG, fg=_FG, font=(_FONT, 9)).pack(side='left')
        self.fps_var = tk.IntVar(value=24)
        fps_fmt = tk.StringVar(value='24')

        def _fps_update(val):
            v = round(float(val))
            self.fps_var.set(v)
            fps_fmt.set(str(v))

        ttk.Scale(
            fps_frame, from_=1, to=60, variable=self.fps_var,
            orient='horizontal', length=150,
            command=_fps_update,
        ).pack(side='left', padx=6)
        tk.Label(fps_frame, textvariable=fps_fmt, width=4, anchor='w',
                 bg=_BG, fg=_ACCENT, font=(_FONT, 9, 'bold')).pack(side='left')

        # Action buttons
        btn = dict(relief='flat', fg='white', cursor='hand2',
                   bd=0, highlightthickness=0)

        self.save_button = tk.Button(
            left, text="Save Image", command=self._on_save,
            bg='#2e7d32', activebackground='#256027',
            font=(_FONT, 11, 'bold'), pady=7, state='disabled', **btn,
        )
        self.save_button.pack(fill='x', pady=(0, 4))

        self.animate_button = tk.Button(
            left, text="Render Animation", command=self._on_animate,
            bg='#0097a7', activebackground='#00838f',
            font=(_FONT, 11, 'bold'), pady=7, **btn,
        )
        self.animate_button.pack(fill='x')

        self.cancel_anim_button = tk.Button(
            left, text="Cancel Animation", command=self._on_cancel_animate,
            bg='#b71c1c', activebackground='#7f0000',
            font=(_FONT, 11, 'bold'), pady=7, state='disabled', **btn,
        )
        self.cancel_anim_button.pack(fill='x', pady=(4, 0))

        # Status area
        self.status_label = tk.Label(left, text="Ready", fg=_MUTED,
                                     font=(_FONT, 9), bg=_BG)
        self.status_label.pack(pady=(8, 0))
        self.time_label = tk.Label(left, text="", fg=_MUTED,
                                   font=(_FONT, 8), bg=_BG)
        self.time_label.pack()

        # Right panel — render output
        right = tk.Frame(self, bg='#0a0a0a', padx=2, pady=2)
        right.grid(row=0, column=1, sticky='nsew')

        self.canvas = tk.Label(right, bg='#0a0a0a')
        self.canvas.pack()

        self._show_placeholder()
        self.after(100, self._on_render)

    def _show_placeholder(self):
        placeholder = Image.new('RGB', (768, 768), color=(10, 10, 20))
        self._display_image(placeholder)

    def _display_image(self, image):
        self.render_image = ImageTk.PhotoImage(image)
        self.canvas.configure(image=self.render_image)

    def _schedule_render(self, *_):
        if self._render_job is not None:
            self.after_cancel(self._render_job)
        self._render_job = self.after(400, self._on_render)

    def _on_render(self):
        self._render_job = None
        self.status_label.configure(text='Rendering...', fg='#fab387')
        self.time_label.configure(text='')
        self.update()

        try:
            params = self.controls.get_params()
            t_start = time.time()
            image = render(params, width=768, height=768)
            elapsed = time.time() - t_start

            self.last_image = image
            self._display_image(image)
            self.status_label.configure(text='Done', fg='#a6e3a1')
            self.time_label.configure(text=f'Render time: {elapsed:.2f}s', fg=_MUTED)
            self.save_button.configure(state='normal')

        except Exception as e:
            self.status_label.configure(text=f'Error: {e}', fg='#f38ba8')
            raise

    def _on_save(self):
        if self.last_image is None:
            return
        os.makedirs('images', exist_ok=True)
        p = self.controls.get_params()
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = (
            f"images/ocean_"
            f"wind{p['wind_speed']:.0f}_"
            f"dir{p['wind_direction_deg']:.0f}_"
            f"chop{p['choppiness']:.2f}_"
            f"t{p['time']:.1f}_"
            f"{ts}.png"
        )
        self.last_image.save(filename)
        self.status_label.configure(text=f'Saved: {filename}', fg='#a6e3a1')

    def _load_latest_frame(self, frame_index):
        frame_path = f'images/frames/frame_{frame_index - 1:04d}.png'
        if os.path.exists(frame_path):
            image = Image.open(frame_path)
            self._display_image(image)

    def _on_animate(self):
        from rendering.animation import render_animation

        self._anim_cancel.clear()
        self.animate_button.configure(state='disabled', text='Rendering...')
        self.cancel_anim_button.configure(state='normal')
        self.save_button.configure(state='disabled')
        self.status_label.configure(text='Rendering animation...', fg='#fab387')
        self.time_label.configure(text='')

        params = self.controls.get_params()
        fps = self.fps_var.get()

        os.makedirs('videos', exist_ok=True)
        p = params
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        video_path = (
            f"videos/ocean_"
            f"wind{p['wind_speed']:.0f}_"
            f"dir{p['wind_direction_deg']:.0f}_"
            f"chop{p['choppiness']:.2f}_"
            f"foam{p['foam_threshold']:.2f}_"
            f"fps{fps}_"
            f"{ts}.mp4"
        )

        def progress(frame, total, frame_time):
            remaining = (total - frame) * frame_time
            self.after(0, lambda f=frame, t=total, r=remaining: self.status_label.configure(
                text=f'Frame {f}/{t} — ~{r:.0f}s remaining', fg='#fab387',
            ))
            self.after(0, self._load_latest_frame, frame)

        def run():
            try:
                result = render_animation(
                    params,
                    fps=fps,
                    output_dir='images/frames',
                    video_path=video_path,
                    progress_callback=progress,
                    cancel_event=self._anim_cancel,
                )
                if result is not None:
                    self.after(0, lambda r=result: self.status_label.configure(
                        text=f'Saved: {r}', fg='#a6e3a1',
                    ))
                else:
                    self.after(0, lambda: self.status_label.configure(
                        text='Animation cancelled', fg=_MUTED,
                    ))
            except Exception as e:
                self.after(0, lambda err=str(e): self.status_label.configure(
                    text=f'Error: {err}', fg='#f38ba8',
                ))
            finally:
                self.after(0, self._on_animate_done)

        threading.Thread(target=run, daemon=True).start()

    def _on_cancel_animate(self):
        self._anim_cancel.set()
        self.cancel_anim_button.configure(state='disabled')
        self.status_label.configure(text='Cancelling...', fg='#fab387')

    def _on_animate_done(self):
        self.animate_button.configure(state='normal', text='Render Animation')
        self.cancel_anim_button.configure(state='disabled')
        self.save_button.configure(state='normal')

    def run(self):
        self.mainloop()


if __name__ == '__main__':
    app = OceanApp()
    app.run()
