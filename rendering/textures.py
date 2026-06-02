import numpy as np
import moderngl
from scipy.ndimage import zoom

def upload_texture(ctx, array, components=1):
    data = array.astype(np.float32).tobytes()
    height, width = array.shape[:2]
    tex = ctx.texture((width, height), components, data, dtype='f4')
    tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
    tex.repeat_x = True
    tex.repeat_y = True
    return tex

def upload_all_textures(ctx, height, surface_tilt_x, surface_tilt_y,
                        sideways_shift_x, sideways_shift_y, foam_mask, foam_upsample=1):
    if foam_upsample > 1:
        foam_mask = np.clip(zoom(foam_mask, foam_upsample, order=3), 0.0, 1.0)
    textures = {
        'height':         upload_texture(ctx, height),
        'surface_tilt':   upload_texture(ctx, np.stack([surface_tilt_x, surface_tilt_y], axis=-1), components=2),
        'sideways_shift': upload_texture(ctx, np.stack([sideways_shift_x, sideways_shift_y], axis=-1), components=2),
        'foam_mask':      upload_texture(ctx, foam_mask),
    }
    return textures