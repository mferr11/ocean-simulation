import os
import time

import numpy as np

from ocean.parameters import orbit_to_camera_eye
from rendering.renderer import render


def render_animation(params, fps=24, output_dir='images/frames', video_path='images/ocean.mp4', progress_callback=None, cancel_event=None):
    os.makedirs(output_dir, exist_ok=True)

    loop_period = params['loop_period']
    total_frames = int(loop_period * fps)

    print(f"Rendering {total_frames} frames at {fps}fps ({loop_period}s loop)")

    frame_params = dict(params)

    for frame_index in range(total_frames):
        if cancel_event is not None and cancel_event.is_set():
            print("Animation cancelled.")
            return None

        t = (frame_index / total_frames) * loop_period
        frame_params['time'] = t

        t_start = time.time()
        image = render(frame_params, width=768, height=768)
        elapsed = time.time() - t_start

        frame_path = os.path.join(output_dir, f'frame_{frame_index:04d}.png')
        image.save(frame_path)

        print(f"  Frame {frame_index + 1}/{total_frames} — t={t:.2f}s — {elapsed:.2f}s")

        if progress_callback:
            progress_callback(frame_index + 1, total_frames, elapsed)

    stitch_video(output_dir, video_path, fps, total_frames)
    return video_path


def stitch_video(frame_dir, video_path, fps, total_frames):
    try:
        import imageio.v2 as imageio
        import glob

        frame_files = sorted(glob.glob(os.path.join(frame_dir, 'frame_*.png')))[:total_frames]
        print(f"Stitching {len(frame_files)} frames into {video_path}...")

        writer = imageio.get_writer(video_path, fps=fps, codec='libx264', quality=8)
        for frame_path in frame_files:
            writer.append_data(imageio.imread(frame_path))
        writer.close()

        print(f"Video saved to {video_path}")

    except ImportError:
        print("imageio not installed — frames saved but video not stitched.")
        print("Install with: pip install imageio[ffmpeg]")