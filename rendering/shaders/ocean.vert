#version 330

in vec2 in_uv;

uniform mat4 u_view;
uniform mat4 u_projection;
uniform vec2 u_grid_size;
uniform float u_choppiness;
uniform float u_height_scale;

uniform sampler2D u_height;
uniform sampler2D u_sideways_shift;

void main() {
    float h = texture(u_height, in_uv).r;
    vec2 shift = texture(u_sideways_shift, in_uv).rg * u_choppiness;

    vec3 world_pos = vec3(
        (in_uv.x - 0.5) * u_grid_size.x + shift.x,
        h * u_height_scale,
        (in_uv.y - 0.5) * u_grid_size.y + shift.y
    );

    gl_Position = u_projection * u_view * vec4(world_pos, 1.0);
}