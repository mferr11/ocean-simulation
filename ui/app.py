import os
import threading
from datetime import datetime

import moderngl
import moderngl_window as mglw
from imgui_bundle import imgui
from moderngl_window.integrations.imgui_bundle import ModernglWindowRenderer

from ocean.parameters import LIVE_SIM_RESOLUTION, default_params, update_derived
from rendering.renderer import OceanRenderer, render
from ui.controls import OceanControls

PANEL_WIDTH = 400
EXPORT_SIZE = 768

_OK    = imgui.ImVec4(0.65, 0.89, 0.63, 1.0)
_BUSY  = imgui.ImVec4(0.98, 0.70, 0.53, 1.0)
_ERROR = imgui.ImVec4(0.95, 0.55, 0.66, 1.0)
_MUTED = imgui.ImVec4(0.42, 0.44, 0.53, 1.0)


class OceanApp(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Ocean Renderer"
    window_size = (1400, 820)
    aspect_ratio = None
    vsync = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        imgui.create_context()
        imgui.get_io().set_ini_filename("")
        self.imgui = ModernglWindowRenderer(self.wnd)

        self.params = update_derived(default_params())
        self.controls = OceanControls(self.params)
        self.ocean = OceanRenderer(self.ctx)

        self.live_resolution = LIVE_SIM_RESOLUTION
        self.playing = True
        self.playback_speed = 1.0
        self.anim_fps = 24
        self._orbiting = False

        self.status = ("Ready", _MUTED)
        self._anim_cancel = threading.Event()
        self._anim_thread = None
        self._anim_progress = None
        self._saving = False

    # --- Frame ---

    def on_render(self, time, frame_time):
        if self.playing:
            step = min(frame_time, 0.1) * self.playback_speed
            self.params['time'] = (self.params['time'] + step) % self.params['loop_period']
        update_derived(self.params)

        buffer_w, buffer_h = self.wnd.buffer_size
        panel_px = int(PANEL_WIDTH * self.wnd.pixel_ratio)
        view_w = buffer_w - panel_px
        self.ctx.clear(0.0, 0.0, 0.0)
        if view_w > 0 and buffer_h > 0:
            # The ImGui pass leaves blending on; the ocean shaders expect it off.
            self.ctx.disable(moderngl.BLEND)
            self.ocean.draw(self.params, self.wnd.fbo, view_w, buffer_h,
                            sim_resolution=self.live_resolution, foam_upsample=1,
                            origin=(panel_px, 0))

        self.wnd.fbo.viewport = (0, 0, buffer_w, buffer_h)
        self.wnd.fbo.use()
        self._draw_ui()

    def _draw_ui(self):
        imgui.new_frame()
        display_w, display_h = self.wnd.size
        imgui.set_next_window_pos(imgui.ImVec2(0, 0))
        imgui.set_next_window_size(imgui.ImVec2(PANEL_WIDTH, display_h))
        flags = (imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_resize |
                 imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_title_bar)
        imgui.begin("Controls", None, flags)
        imgui.push_item_width(-150)

        imgui.text("Ocean Renderer")
        imgui.same_line()
        imgui.text_colored(_MUTED, f"{imgui.get_io().framerate:.0f} fps")
        imgui.separator()

        self._draw_playback()
        self.live_resolution = self.controls.draw(self.live_resolution)
        imgui.separator()
        self._draw_export()

        imgui.pop_item_width()
        imgui.end()
        imgui.render()
        self.imgui.render(imgui.get_draw_data())

    def _draw_playback(self):
        if imgui.button("Pause" if self.playing else "Play", imgui.ImVec2(70, 0)):
            self.playing = not self.playing
        imgui.same_line()
        imgui.text_colored(_MUTED, "(Space)")
        changed, value = imgui.slider_float("Time (s)", self.params['time'], 0.0,
                                            self.params['loop_period'], '%.2f')
        if changed:
            self.params['time'] = value
        _, self.playback_speed = imgui.slider_float("Speed", self.playback_speed, 0.0, 4.0, '%.2fx')

    def _draw_export(self):
        busy = self._saving or self._anim_thread is not None

        imgui.begin_disabled(busy)
        if imgui.button("Save Image", imgui.ImVec2(-1, 0)):
            self._on_save()
        _, self.anim_fps = imgui.slider_int("Animation FPS", self.anim_fps, 1, 60)
        if imgui.button("Render Animation", imgui.ImVec2(-1, 0)):
            self._on_animate()
        imgui.end_disabled()

        if self._anim_thread is not None:
            if self._anim_progress:
                frame, total, remaining = self._anim_progress
                imgui.progress_bar(frame / total, imgui.ImVec2(-1, 0),
                                   f"Frame {frame}/{total} (~{remaining:.0f}s left)")
            imgui.begin_disabled(self._anim_cancel.is_set())
            if imgui.button("Cancel Animation", imgui.ImVec2(-1, 0)):
                self._anim_cancel.set()
                self.status = ("Cancelling...", _BUSY)
            imgui.end_disabled()

        text, colour = self.status
        imgui.push_text_wrap_pos(0.0)
        imgui.text_colored(colour, text)
        imgui.pop_text_wrap_pos()

    # --- Export ---

    def _export_name(self, folder, extension, extra=''):
        p = self.params
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        return (
            f"{folder}/ocean_"
            f"wind{p['wind_speed']:.0f}_"
            f"dir{p['wind_direction_deg']:.0f}_"
            f"chop{p['choppiness']:.2f}_"
            f"{extra}"
            f"{ts}.{extension}"
        )

    def _on_save(self):
        os.makedirs('images', exist_ok=True)
        filename = self._export_name('images', 'png', extra=f"t{self.params['time']:.1f}_")
        params = dict(self.params)
        self._saving = True
        self.status = ("Rendering image...", _BUSY)

        def run():
            try:
                render(params, width=EXPORT_SIZE, height=EXPORT_SIZE).save(filename)
                self.status = (f"Saved: {filename}", _OK)
            except Exception as e:
                self.status = (f"Error: {e}", _ERROR)
            finally:
                self._saving = False

        threading.Thread(target=run, daemon=True).start()

    def _on_animate(self):
        from rendering.animation import render_animation

        os.makedirs('videos', exist_ok=True)
        fps = self.anim_fps
        video_path = self._export_name(
            'videos', 'mp4', extra=f"foam{self.params['foam_threshold']:.2f}_fps{fps}_"
        )
        params = dict(self.params)
        self._anim_cancel.clear()
        self._anim_progress = None
        self.status = ("Rendering animation...", _BUSY)

        def progress(frame, total, frame_time):
            self._anim_progress = (frame, total, (total - frame) * frame_time)

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
                    self.status = (f"Saved: {result}", _OK)
                else:
                    self.status = ("Animation cancelled", _MUTED)
            except Exception as e:
                self.status = (f"Error: {e}", _ERROR)
            finally:
                self._anim_thread = None

        self._anim_thread = threading.Thread(target=run, daemon=True)
        self._anim_thread.start()

    # --- Input: ImGui gets every event; the rest orbits the camera ---

    def on_resize(self, width, height):
        self.imgui.resize(width, height)

    def on_key_event(self, key, action, modifiers):
        self.imgui.key_event(key, action, modifiers)
        keys = self.wnd.keys
        if (key == keys.SPACE and action == keys.ACTION_PRESS
                and not imgui.get_io().want_capture_keyboard):
            self.playing = not self.playing

    def on_mouse_position_event(self, x, y, dx, dy):
        self.imgui.mouse_position_event(x, y, dx, dy)

    def on_mouse_press_event(self, x, y, button):
        self.imgui.mouse_press_event(x, y, button)
        # ImGui's hover state lags a frame behind, so also check the click is right of the panel.
        self._orbiting = (button == self.wnd.mouse.left and x >= PANEL_WIDTH
                          and not imgui.get_io().want_capture_mouse)

    def on_mouse_release_event(self, x, y, button):
        self.imgui.mouse_release_event(x, y, button)
        if button == self.wnd.mouse.left:
            self._orbiting = False

    def on_mouse_drag_event(self, x, y, dx, dy):
        self.imgui.mouse_drag_event(x, y, dx, dy)
        if self._orbiting:
            p = self.params
            p['camera_azimuth_deg'] = (p['camera_azimuth_deg'] - dx * 0.3) % 360.0
            p['camera_elevation_deg'] = min(90.0, max(0.0, p['camera_elevation_deg'] + dy * 0.3))

    def on_mouse_scroll_event(self, x_offset, y_offset):
        self.imgui.mouse_scroll_event(x_offset, y_offset)
        if not imgui.get_io().want_capture_mouse:
            p = self.params
            p['camera_distance'] = min(3000.0, max(100.0, p['camera_distance'] * 0.9 ** y_offset))

    def on_unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)


def main():
    mglw.run_window_config(OceanApp, args=['--window', 'glfw'])


if __name__ == '__main__':
    main()
