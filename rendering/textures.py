import numpy as np
import moderngl
from scipy.ndimage import zoom

def create_texture(ctx, size, components=1):
    tex = ctx.texture((size, size), components, dtype='f4')
    tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
    tex.repeat_x = True
    tex.repeat_y = True
    return tex

def create_field_textures(ctx, resolution, foam_resolution):
    return {
        'height':         create_texture(ctx, resolution),
        'surface_tilt':   create_texture(ctx, resolution, components=2),
        'sideways_shift': create_texture(ctx, resolution, components=2),
        'foam_mask':      create_texture(ctx, foam_resolution),
    }

def write_field_textures(textures, fields, foam_upsample=1):
    foam_mask = fields['foam_mask']
    if foam_upsample > 1:
        foam_mask = np.clip(zoom(foam_mask, foam_upsample, order=3), 0.0, 1.0)

    def write(name, array):
        textures[name].write(np.ascontiguousarray(array, dtype=np.float32))

    write('height',         fields['wave_height'])
    write('surface_tilt',   np.stack([fields['surface_tilt_x'], fields['surface_tilt_y']], axis=-1))
    write('sideways_shift', np.stack([fields['sideways_shift_x'], fields['sideways_shift_y']], axis=-1))
    write('foam_mask',      foam_mask)
