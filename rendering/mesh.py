import numpy as np

def create_grid_mesh(ctx, grid_resolution):
    N = grid_resolution
    lin = np.linspace(0, 1, N, dtype=np.float32)
    ux, uy = np.meshgrid(lin, lin, indexing='ij')
    uvs = np.stack([ux, uy], axis=-1).reshape(-1, 2)

    i, j = np.meshgrid(np.arange(N - 1), np.arange(N - 1), indexing='ij')
    a = (i * N + j).ravel()
    b = a + 1
    c = a + N
    d = c + 1
    indices = np.stack([a, c, b, b, c, d], axis=-1).astype(np.int32)

    vbo = ctx.buffer(uvs.tobytes())
    ibo = ctx.buffer(indices.tobytes())
    return vbo, ibo
