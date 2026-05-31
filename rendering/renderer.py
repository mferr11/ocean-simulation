import os

import moderngl
import numpy as np
import pyrr
from PIL import Image



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


def load_shadow_shaders(ctx):
    shader_dir = os.path.join(os.path.dirname(__file__), 'shaders')
    with open(os.path.join(shader_dir, 'shadow.vert')) as f:
        vert_src = f.read()
    with open(os.path.join(shader_dir, 'shadow.frag')) as f:
        frag_src = f.read()
    program = ctx.program(vertex_shader=vert_src, fragment_shader=frag_src)
    return program


# --- Shadow map ---

def create_shadow_map(ctx, shadow_size=2048):
    shadow_tex = ctx.depth_texture((shadow_size, shadow_size))
    shadow_fbo = ctx.framebuffer(depth_attachment=shadow_tex)
    return shadow_tex, shadow_fbo


def create_light_space_matrix(sun_dir, grid_size):
    sun_dir = np.array(sun_dir, dtype=np.float32)
    sun_dir = sun_dir / np.linalg.norm(sun_dir)
    sun_pos = sun_dir * 2000.0

    up = np.array([0, 1, 0], dtype=np.float32)
    if abs(np.dot(sun_dir, up)) > 0.99:
        up = np.array([0, 0, 1], dtype=np.float32)

    light_view = pyrr.matrix44.create_look_at(
        eye=sun_pos,
        target=np.array([0, 0, 0], dtype=np.float32),
        up=up,
    )
    half = grid_size * 0.65
    light_proj = pyrr.matrix44.create_orthogonal_projection(
        left=-half, right=half, bottom=-half, top=half,
        near=0.1, far=4000.0, dtype=np.float32,
    )
    return (light_proj @ light_view).astype(np.float32)


# --- Camera ---

def create_camera_matrices(width, height, eye=(600, 250, 600)):
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


def test_mesh(width=1024, height=1024):
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


def test_textures(width=1024, height=1024):
    from ocean.parameters import default_params
    params = default_params()
    image = render(params, width, height)
    os.makedirs('images', exist_ok=True)
    image.save('images/test_textures.png')
    print("Texture render saved")

def run_ocean_pipeline(params):
    from ocean.simulation import compute_oscillation_rates, compute_surface_fields, time_evolve
    from ocean.spectrum import generate_initial_amplitudes, make_spatial_frequency_grid, phillips_spectrum

    freq_x, freq_y, magnitude = make_spatial_frequency_grid(
        params['grid_resolution'], params['grid_size']
    )
    wave_energy = phillips_spectrum(
        freq_x, freq_y, magnitude, params['wind_speed'], params['wind_direction_deg']
    )
    initial_amplitudes, initial_amplitudes_mirror = generate_initial_amplitudes(wave_energy)
    oscillation_rate = compute_oscillation_rates(magnitude, params['loop_period'])
    freq_amplitudes = time_evolve(
        initial_amplitudes, initial_amplitudes_mirror, oscillation_rate, t=params['time']
    )
    wave_height, surface_tilt_x, surface_tilt_y, sideways_shift_x, sideways_shift_y, foam_mask, _ = \
        compute_surface_fields(
            freq_amplitudes, freq_x, freq_y, magnitude,
            params['foam_threshold'], params['choppiness'], params['height_scale'], params['grid_resolution']
        )
    return wave_height, surface_tilt_x, surface_tilt_y, sideways_shift_x, sideways_shift_y, foam_mask


def render(params, width=1024, height=1024):
    from rendering.mesh import create_grid_mesh
    from rendering.textures import upload_all_textures

    wave_height, surface_tilt_x, surface_tilt_y, sideways_shift_x, sideways_shift_y, foam_mask = \
        run_ocean_pipeline(params)

    ctx = create_context()
    fbo = create_framebuffer(ctx, width, height)
    program = load_shaders(ctx)
    vbo, ibo = create_grid_mesh(ctx, grid_resolution=params['grid_resolution'])

    textures = upload_all_textures(
        ctx, wave_height, surface_tilt_x, surface_tilt_y, sideways_shift_x, sideways_shift_y, foam_mask
    )

    light_space = create_light_space_matrix(params['sun_dir'], params['grid_size'])

    # --- Shadow pass ---
    shadow_tex, shadow_fbo = create_shadow_map(ctx)
    shadow_prog = load_shadow_shaders(ctx)
    shadow_vao = ctx.vertex_array(shadow_prog, [(vbo, '2f', 'in_uv')], ibo)

    textures['height'].use(location=0)
    textures['sideways_shift'].use(location=1)
    shadow_prog['u_height'].value = 0
    shadow_prog['u_sideways_shift'].value = 1
    shadow_prog['u_light_space'].write(light_space.tobytes())
    shadow_prog['u_grid_size'].value = (params['grid_size'], params['grid_size'])
    shadow_prog['u_height_scale'].value = params['height_scale']

    shadow_fbo.use()
    ctx.clear(depth=True)
    ctx.enable(moderngl.DEPTH_TEST)
    shadow_vao.render()

    # --- Main pass ---
    vao = ctx.vertex_array(program, [(vbo, '2f', 'in_uv')], ibo)

    textures['height'].use(location=0)
    textures['sideways_shift'].use(location=1)
    textures['surface_tilt'].use(location=2)
    textures['foam_mask'].use(location=3)
    shadow_tex.use(location=4)
    program['u_height'].value = 0
    program['u_sideways_shift'].value = 1
    program['u_surface_tilt'].value = 2
    program['u_foam_mask'].value = 3
    program['u_shadow_map'].value = 4

    view, projection = create_camera_matrices(width, height, eye=params['camera_eye'])

    fbo.use()
    ctx.clear(0.05, 0.05, 0.05)
    ctx.enable(moderngl.DEPTH_TEST)
    program['u_view'].write(view.astype('f4').tobytes())
    program['u_projection'].write(projection.astype('f4').tobytes())
    program['u_light_space'].write(light_space.tobytes())
    program['u_grid_size'].value = (params['grid_size'], params['grid_size'])
    program['u_height_scale'].value = params['height_scale']
    program['u_camera_pos'].value = params['camera_eye']
    program['u_sun_dir'].value = params['sun_dir']
    program['u_deep_colour'].value = params['deep_colour']
    program['u_shallow_colour'].value = params['shallow_colour']
    program['u_depth_scale'].value = params['depth_scale']
    vao.render()

    return read_framebuffer(fbo, width, height)


if __name__ == '__main__':
    test_textures()
    test_mesh()