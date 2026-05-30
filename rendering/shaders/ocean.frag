#version 330

in vec2 frag_uv;
in vec3 frag_normal;
in vec3 frag_world_pos;

uniform vec3 u_camera_pos;
uniform vec3 u_sun_dir;
uniform vec3 u_deep_colour;
uniform vec3 u_shallow_colour;
uniform float u_depth_scale;
uniform sampler2D u_foam_mask;

out vec4 out_colour;

void main() {
    vec3 N = normalize(frag_normal);
    vec3 V = normalize(u_camera_pos - frag_world_pos);
    vec3 L = normalize(u_sun_dir);

    // Depth-based water colour
    float depth_factor = clamp(-frag_world_pos.y * u_depth_scale, 0.0, 1.0);
    vec3 water_colour = mix(u_shallow_colour, u_deep_colour, depth_factor);

    // Ambient + diffuse (Lambert)
    float ambient = 0.3;
    float diffuse = max(dot(N, L), 0.0);

    // Specular (Phong)
    vec3 R = reflect(-L, N);
    float specular = pow(max(dot(R, V), 0.0), 64.0);

    // Fresnel (Schlick approximation)
    float R0 = 0.02;
    float fresnel = R0 + (1.0 - R0) * pow(1.0 - max(dot(V, N), 0.0), 5.0);

    // Sky colour for Fresnel reflection
    vec3 sky_colour = mix(vec3(0.6, 0.8, 1.0), vec3(0.1, 0.3, 0.8), N.y * 0.5 + 0.5);

    // Combine
    vec3 colour = water_colour * (ambient + diffuse * 0.6)
                + vec3(1.0) * specular * 0.5
                + sky_colour * fresnel;

    // Foam
    float foam = texture(u_foam_mask, frag_uv).r;
    colour = mix(colour, vec3(1.0), foam * 0.8);

    out_colour = vec4(colour, 1.0);
}