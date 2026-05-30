import os

import moderngl
import numpy as np
import pyrr
from PIL import Image

from ocean.parameters import (
    CHOPPINESS,
    FOAM_THRESHOLD,
    GRID_RESOLUTION,
    GRID_SIZE,
    HEIGHT_SCALE,
    WIND_DIRECTION_DEG,
    WIND_SPEED,
)


# --- Context and framebuffer ---

def create_context():
    ctx = moderngl.create_standalone_context()
    return ctx


def create_framebuffer(ctx, width, height):
    width, height = int(width), int(height)
    color_buffer = ctx.renderbuffer((width, height))
    depth_buffer = ctx.depth_renderbuffer((width, height))
    fbo = ctx.framebuffer(color_attachments=[color_buffer], depth_attachment=depth_buffer)
    return fbo


def read_framebuffer(fbo, width, height):
    raw = fbo.read(components=3)
    image = Image.frombytes('RGB', (width, height), raw)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    return image


# --- Shaders ---

def load_shaders(ctx):
    shader_dir = os.path.join(os.path.dirname(__file__), 'shaders')
    with open(os.path.join(shader_dir, 'ocean.vert')) as f:
        vert_src = f.read()
    with open(os.path.join(shader_dir, 'ocean.frag')) as f:
        frag_src = f.read()
    program = ctx.program(vertex_shader=vert_src, fragment_shader=frag_src)
    return program


# --- Camera ---

def create_camera_matrices(width, height, eye=(0, 300, 400)):
    view = pyrr.matrix44.create_look_at(
        eye=np.array(eye, dtype=np.float32),
        target=np.array([0, 0, 0], dtype=np.float32),
        up=np.array([0, 1, 0], dtype=np.float32),
    )
    projection = pyrr.matrix44.create_perspective_projection(
        fovy=45, aspect=width / height, near=1.0, far=10000.0, dtype=np.float32
    )
    return view, projection


# --- Tests ---

def test_render(width=800, height=600):
    ctx = create_context()
    fbo = create_framebuffer(ctx, width, height)
    fbo.use()
    ctx.clear(0.1, 0.3, 0.6)
    image = read_framebuffer(fbo, width, height)
    os.makedirs('images', exist_ok=True)
    image.save('images/test_render.png')
    print("Test render saved — context is working")


def test_shaders():
    ctx = create_context()
    program = load_shaders(ctx)
    print(f"Shaders loaded — uniforms: {list(program)}")


def test_mesh(width=800, height=600):
    from rendering.mesh import create_grid_mesh

    ctx = create_context()
    fbo = create_framebuffer(ctx, width, height)
    program = load_shaders(ctx)
    vbo, ibo = create_grid_mesh(ctx, grid_resolution=32)
    vao = ctx.vertex_array(program, [(vbo, '2f', 'in_uv')], ibo)
    view, projection = create_camera_matrices(width, height)

    fbo.use()
    ctx.clear(0.05, 0.05, 0.05)
    ctx.enable(moderngl.DEPTH_TEST)
    program['u_view'].write(view.astype('f4').tobytes())
    program['u_projection'].write(projection.astype('f4').tobytes())
    program['u_grid_size'].value = (500.0, 500.0)
    vao.render()

    image = read_framebuffer(fbo, width, height)
    os.makedirs('images', exist_ok=True)
    image.save('images/test_mesh.png')
    print("Mesh render saved")


def test_textures(width=800, height=600):
    from ocean.simulation import compute_oscillation_rates, compute_surface_fields, time_evolve
    from ocean.spectrum import generate_initial_amplitudes, make_spatial_frequency_grid, phillips_spectrum
    from rendering.mesh import create_grid_mesh
    from rendering.textures import upload_all_textures

    # Phase 1 pipeline
    freq_x, freq_y, magnitude = make_spatial_frequency_grid(GRID_RESOLUTION, GRID_SIZE)
    wave_energy = phillips_spectrum(freq_x, freq_y, magnitude, WIND_SPEED, WIND_DIRECTION_DEG)
    initial_amplitudes, initial_amplitudes_mirror = generate_initial_amplitudes(wave_energy)
    oscillation_rate = compute_oscillation_rates(magnitude)
    freq_amplitudes = time_evolve(initial_amplitudes, initial_amplitudes_mirror, oscillation_rate, t=0.0)
    wave_height, surface_tilt_x, surface_tilt_y, sideways_shift_x, sideways_shift_y, foam_mask, _ = \
        compute_surface_fields(freq_amplitudes, freq_x, freq_y, magnitude, FOAM_THRESHOLD)

    print(f"wave_height min: {wave_height.min():.4f}, max: {wave_height.max():.4f}")

    ctx = create_context()
    fbo = create_framebuffer(ctx, width, height)
    program = load_shaders(ctx)
    vbo, ibo = create_grid_mesh(ctx, grid_resolution=GRID_RESOLUTION)
    vao = ctx.vertex_array(program, [(vbo, '2f', 'in_uv')], ibo)

    textures = upload_all_textures(
        ctx, wave_height, surface_tilt_x, surface_tilt_y, sideways_shift_x, sideways_shift_y, foam_mask
    )
    textures['height'].use(location=0)
    textures['sideways_shift'].use(location=1)
    program['u_height'].value = 0
    program['u_sideways_shift'].value = 1

    view, projection = create_camera_matrices(width, height)

    fbo.use()
    ctx.clear(0.05, 0.05, 0.05)
    ctx.enable(moderngl.DEPTH_TEST)
    program['u_view'].write(view.astype('f4').tobytes())
    program['u_projection'].write(projection.astype('f4').tobytes())
    program['u_grid_size'].value = (GRID_SIZE, GRID_SIZE)
    program['u_choppiness'].value = CHOPPINESS
    program['u_height_scale'].value = HEIGHT_SCALE
    vao.render()

    image = read_framebuffer(fbo, width, height)
    os.makedirs('images', exist_ok=True)
    image.save('images/test_textures.png')
    print("Texture render saved")


if __name__ == '__main__':
    test_textures()