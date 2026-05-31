import os
import time
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk

from ocean.parameters import default_params
from rendering.renderer import render
from ui.controls import OceanControls


class OceanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ocean Renderer")
        self.resizable(False, False)

        self.params = default_params()
        self.render_image = None
        self.last_image = None

        self._build()

    def _build(self):
        # Left panel — controls
        left = tk.Frame(self, padx=10, pady=10)
        left.grid(row=0, column=0, sticky='ns')

        self.controls = OceanControls(left, self.params)
        self.controls.pack()

        ttk.Separator(left, orient='horizontal').pack(fill='x', pady=10)

        self.render_button = tk.Button(
            left, text="Render", command=self._on_render,
            bg='#1a6fad', fg='white', font=('Helvetica', 11, 'bold'),
            padx=12, pady=6, relief='flat', cursor='hand2'
        )
        self.render_button.pack(fill='x')

        self.save_button = tk.Button(
            left, text="Save Image", command=self._on_save,
            bg='#2e7d32', fg='white', font=('Helvetica', 10),
            padx=12, pady=4, relief='flat', cursor='hand2',
            state='disabled'
        )
        self.save_button.pack(fill='x', pady=(6, 0))

        self.status_label = tk.Label(left, text="Ready", fg='gray', font=('Helvetica', 9))
        self.status_label.pack(pady=(6, 0))

        self.time_label = tk.Label(left, text="", fg='gray', font=('Helvetica', 9))
        self.time_label.pack()

        # Right panel — render output
        right = tk.Frame(self, bg='#0a0a0a', padx=2, pady=2)
        right.grid(row=0, column=1, sticky='nsew')

        self.canvas = tk.Label(right, bg='#0a0a0a')
        self.canvas.pack()

        self._show_placeholder()
        self.after(100, self._on_render)

    def _show_placeholder(self):
        from PIL import Image
        placeholder = Image.new('RGB', (768, 768), color=(10, 10, 20))
        self._display_image(placeholder)

    def _display_image(self, image):
        self.render_image = ImageTk.PhotoImage(image)
        self.canvas.configure(image=self.render_image)

    def _on_render(self):
        self.render_button.configure(state='disabled', text='Rendering...')
        self.status_label.configure(text='Running FFT pipeline...', fg='orange')
        self.time_label.configure(text='')
        self.update()

        try:
            params = self.controls.get_params()
            t_start = time.time()
            image = render(params, width=768, height=768)
            elapsed = time.time() - t_start

            self.last_image = image
            self._display_image(image)
            self.status_label.configure(text='Done', fg='green')
            self.time_label.configure(text=f'Render time: {elapsed:.2f}s', fg='gray')
            self.save_button.configure(state='normal')

        except Exception as e:
            self.status_label.configure(text=f'Error: {e}', fg='red')
            raise
        finally:
            self.render_button.configure(state='normal', text='Render')

    def _on_save(self):
        if self.last_image is None:
            return
        os.makedirs('images', exist_ok=True)
        p = self.controls.get_params()
        filename = (
            f"images/ocean_"
            f"wind{p['wind_speed']:.0f}_"
            f"dir{p['wind_direction_deg']:.0f}_"
            f"chop{p['choppiness']:.2f}_"
            f"t{p['time']:.1f}.png"
        )
        self.last_image.save(filename)
        self.status_label.configure(text=f'Saved: {filename}', fg='green')

    def run(self):
        self.mainloop()


if __name__ == '__main__':
    app = OceanApp()
    app.run()