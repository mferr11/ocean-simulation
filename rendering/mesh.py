import numpy as np

def create_grid_mesh(ctx, grid_resolution):
    N = grid_resolution
    lin = np.linspace(0, 1, N, dtype=np.float32)
    ux, uy = np.meshgrid(lin, lin, indexing='ij')
    uvs = np.stack([ux, uy], axis=-1).reshape(-1, 2)

    indices = []
    for i in range(N - 1):
        for j in range(N - 1):
            a = i * N + j
            b = i * N + j + 1
            c = (i + 1) * N + j
            d = (i + 1) * N + j + 1
            indices += [a, c, b, b, c, d]

    vbo = ctx.buffer(uvs.tobytes())
    ibo = ctx.buffer(np.array(indices, dtype=np.int32).tobytes())
    return vbo, ibo