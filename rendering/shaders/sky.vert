#version 330

in vec2 in_pos;

uniform mat4 u_inv_view;
uniform mat4 u_inv_projection;

out vec3 frag_view_dir;

void main() {
    vec4 clip = vec4(in_pos, 1.0, 1.0);
    vec4 vs = u_inv_projection * clip;
    vec3 view_dir = normalize(vs.xyz / vs.w);
    frag_view_dir = normalize((u_inv_view * vec4(view_dir, 0.0)).xyz);
    gl_Position = vec4(in_pos, 1.0, 1.0);
}
