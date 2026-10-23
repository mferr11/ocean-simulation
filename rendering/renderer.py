import math
import os

import moderngl
import numpy as np
import pyrr
from PIL import Image

from ocean.simulation import OceanSimulation
from rendering.mesh import create_grid_mesh
from rendering.textures import create_field_textures, write_field_textures


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


def load_sky_shaders(ctx):
    shader_dir = os.path.join(os.path.dirname(__file__), 'shaders')
    with open(os.path.join(shader_dir, 'sky.vert')) as f:
        vert_src = f.read()
    with open(os.path.join(shader_dir, 'sky.frag')) as f:
        frag_src = f.read()
    return ctx.program(vertex_shader=vert_src, fragment_shader=frag_src)


def create_sky_quad(ctx):
    verts = np.array([-1, -1, 1, -1, 1, 1, -1, 1], dtype=np.float32)
    indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.int32)
    return ctx.buffer(verts.tobytes()), ctx.buffer(indices.tobytes())


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
    # Depth-only FBOs return GL_FRAMEBUFFER_UNSUPPORTED on many Windows drivers
    # unless glDrawBuffer(GL_NONE) is set, which ModernGL doesn't do automatically.
    # A dummy color renderbuffer makes the FBO universally complete.
    dummy_color = ctx.renderbuffer((shadow_size, shadow_size))
    shadow_fbo = ctx.framebuffer(color_attachments=[dummy_color], depth_attachment=shadow_tex)
    return shadow_tex, shadow_fbo


def _dominant_light_dir(params):
    sun = params['sun_dir']
    if sun[1] >= 0.0:
        return sun
    moon = params.get('moon_dir', (-sun[0], -sun[1], -sun[2]))
    mx, my, mz = moon
    min_y = math.sin(math.radians(10))
    if my < min_y:
        moon = (mx, min_y, mz)
    return moon


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

def create_camera_matrices(width, height, eye=(600, 250, 600), target=(0, 0, 0)):
    view = pyrr.matrix44.create_look_at(
        eye=np.array(eye, dtype=np.float32),
        target=np.array(target, dtype=np.float32),
        up=np.array([0, 1, 0], dtype=np.float32),
    )
    projection = pyrr.matrix44.create_perspective_projection(
        fovy=45, aspect=width / height, near=1.0, far=10000.0, dtype=np.float32
    )
    return view, projection


def render(params, width=1024, height=1024):
    renderer = OceanRenderer()
    try:
        return renderer.render_image(params, width, height)
    finally:
        renderer.release()


class OceanRenderer:
    """Keeps the GL context, shaders, mesh, textures and simulation cache alive
    between frames, so each frame only re-runs the time-dependent work.

    Pass `ctx` to draw with an existing context (e.g. a window's); otherwise a
    standalone offscreen context is created and owned by the renderer.
    """

    def __init__(self, ctx=None):
        self._owns_ctx = ctx is None
        self.ctx = ctx or create_context()
        self.simulation = OceanSimulation()

        self._mesh_resolution = None
        self._texture_key = None
        self.textures = {}
        self._fbo = None
        self._fbo_size = None

        with self.ctx:
            self.program = load_shaders(self.ctx)
            self.shadow_prog = load_shadow_shaders(self.ctx)
            self.sky_prog = load_sky_shaders(self.ctx)

            sky_vbo, sky_ibo = create_sky_quad(self.ctx)
            self.sky_vao = self.ctx.vertex_array(self.sky_prog, [(sky_vbo, '2f', 'in_pos')], sky_ibo)
            self.shadow_tex, self.shadow_fbo = create_shadow_map(self.ctx)

            self.shadow_prog['u_height'].value = 0
            self.shadow_prog['u_sideways_shift'].value = 1
            self.program['u_height'].value = 0
            self.program['u_sideways_shift'].value = 1
            self.program['u_surface_tilt'].value = 2
            self.program['u_foam_mask'].value = 3
            self.program['u_shadow_map'].value = 4

    def _ensure_mesh(self, resolution):
        if resolution == self._mesh_resolution:
            return
        if self._mesh_resolution is not None:
            for obj in (self.vao, self.shadow_vao, self._vbo, self._ibo):
                obj.release()
        self._vbo, self._ibo = create_grid_mesh(self.ctx, grid_resolution=resolution)
        self.vao = self.ctx.vertex_array(self.program, [(self._vbo, '2f', 'in_uv')], self._ibo)
        self.shadow_vao = self.ctx.vertex_array(self.shadow_prog, [(self._vbo, '2f', 'in_uv')], self._ibo)
        self._mesh_resolution = resolution

    def _ensure_textures(self, resolution, foam_resolution):
        key = (resolution, foam_resolution)
        if key == self._texture_key:
            return
        for tex in self.textures.values():
            tex.release()
        self.textures = create_field_textures(self.ctx, resolution, foam_resolution)
        self._texture_key = key

    def draw(self, params, fbo, width, height, t=None, sim_resolution=None, foam_upsample=None, origin=(0, 0)):
        """Simulate the ocean at time `t` (default: params['time']) and draw it into a
        `width` x `height` region of `fbo` whose bottom-left corner is at `origin`."""
        if t is None:
            t = params['time']
        if foam_upsample is None:
            foam_upsample = params.get('foam_upsample', 1)

        fields = self.simulation.compute_fields(params, t, sim_resolution)
        resolution = fields['wave_height'].shape[0]

        light_space = create_light_space_matrix(_dominant_light_dir(params), params['grid_size'])
        y_off = params.get('camera_y_offset', 0.0)
        eye = params['camera_eye']
        cam_eye = (eye[0], eye[1] + y_off, eye[2])
        cam_target = (0, y_off, 0)
        view, projection = create_camera_matrices(width, height, eye=cam_eye, target=cam_target)

        ctx = self.ctx
        with ctx:
            self._ensure_mesh(resolution)
            self._ensure_textures(resolution, resolution * foam_upsample)
            write_field_textures(self.textures, fields, foam_upsample)

            # --- Shadow pass ---
            self.textures['height'].use(location=0)
            self.textures['sideways_shift'].use(location=1)
            self.shadow_prog['u_light_space'].write(light_space.tobytes())
            self.shadow_prog['u_grid_size'].value = (params['grid_size'], params['grid_size'])
            self.shadow_prog['u_height_scale'].value = params['height_scale']

            self.shadow_fbo.use()
            ctx.clear(depth=True)
            ctx.enable(moderngl.DEPTH_TEST)
            self.shadow_vao.render()

            # --- Main pass ---
            self.textures['surface_tilt'].use(location=2)
            self.textures['foam_mask'].use(location=3)
            self.shadow_tex.use(location=4)

            fbo.viewport = (origin[0], origin[1], width, height)
            fbo.use()
            ctx.clear(0.0, 0.0, 0.0)

            # --- Sky pass ---
            self.sky_prog['u_sun_dir'].value  = params['sun_dir']
            self.sky_prog['u_moon_dir'].value = params.get('moon_dir', (0.0, 1.0, 0.0))
            self.sky_prog['u_inv_view'].write(np.linalg.inv(view).astype('f4').tobytes())
            self.sky_prog['u_inv_projection'].write(np.linalg.inv(projection).astype('f4').tobytes())
            ctx.disable(moderngl.DEPTH_TEST)
            self.sky_vao.render()

            # --- Ocean pass ---
            program = self.program
            ctx.enable(moderngl.DEPTH_TEST)
            program['u_view'].write(view.astype('f4').tobytes())
            program['u_projection'].write(projection.astype('f4').tobytes())
            program['u_light_space'].write(light_space.tobytes())
            program['u_grid_size'].value = (params['grid_size'], params['grid_size'])
            program['u_height_scale'].value = params['height_scale']
            program['u_camera_pos'].value = cam_eye
            program['u_sun_dir'].value  = params['sun_dir']
            program['u_moon_dir'].value = params.get('moon_dir', (0.0, 1.0, 0.0))
            program['u_deep_colour'].value = params['deep_colour']
            program['u_shallow_colour'].value = params['shallow_colour']
            program['u_depth_scale'].value = params['depth_scale']
            self.vao.render()

    def render_image(self, params, width=1024, height=1024, t=None):
        """Draw into an offscreen framebuffer and return the result as a PIL image."""
        width, height = int(width), int(height)
        if self._fbo_size != (width, height):
            with self.ctx:
                if self._fbo is not None:
                    self._fbo.release()
                self._fbo = create_framebuffer(self.ctx, width, height)
            self._fbo_size = (width, height)

        self.draw(params, self._fbo, width, height, t=t)
        with self.ctx:
            return read_framebuffer(self._fbo, width, height)

    def release(self):
        # A borrowed context (e.g. a window's) frees its objects when it is destroyed.
        if self._owns_ctx:
            self.ctx.release()

