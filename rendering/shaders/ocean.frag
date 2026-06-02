#version 330

in vec2 frag_uv;
in vec3 frag_normal;
in vec3 frag_world_pos;
in vec4 frag_light_space_pos;

uniform vec3 u_camera_pos;
uniform vec3 u_sun_dir;
uniform vec3 u_deep_colour;
uniform vec3 u_shallow_colour;
uniform float u_depth_scale;
uniform float u_height_scale;
uniform sampler2D u_foam_mask;
uniform sampler2D u_shadow_map;

out vec4 out_colour;

float shadow_factor(vec4 light_space_pos) {
    vec3 proj = light_space_pos.xyz / light_space_pos.w;
    proj = proj * 0.5 + 0.5;

    if (proj.z > 1.0) return 1.0;

    float bias = 0.005;
    float shadow = 0.0;
    vec2 texel = 1.0 / textureSize(u_shadow_map, 0);

    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            float d = texture(u_shadow_map, proj.xy + vec2(x, y) * texel).r;
            shadow += (proj.z - bias > d) ? 0.0 : 1.0;
        }
    }
    return shadow / 9.0;
}

void main() {
    vec3 N = normalize(frag_normal);
    vec3 V = normalize(u_camera_pos - frag_world_pos);
    vec3 L = normalize(u_sun_dir);

    // Height-based water colour: crest → shallow, trough → deep
    // Normalise by height_scale * 10 (expected FFT amplitude range before scaling)
    float height_factor = clamp(0.5 - frag_world_pos.y * u_depth_scale / u_height_scale, 0.0, 1.0);
    vec3 water_colour = mix(u_shallow_colour, u_deep_colour, height_factor);

    // Ambient + diffuse (Lambert)
    float sun_elev = clamp(L.y, 0.0, 1.0);
    float ambient = mix(0.12, 0.18, sun_elev);
    float diffuse = max(dot(N, L), 0.0);

    // Specular (Phong)
    vec3 R = reflect(-L, N);
    float specular = pow(max(dot(R, V), 0.0), 512.0);

    // Fresnel (Schlick approximation)
    float R0 = 0.02;
    float fresnel = R0 + (1.0 - R0) * pow(1.0 - max(dot(V, N), 0.0), 5.0);

    // Sun and sky colour driven by sun elevation (L.y = sin(elevation))
    vec3 sun_colour  = mix(vec3(1.0, 0.35, 0.05), vec3(1.0, 0.95, 0.85), pow(sun_elev, 0.3));
    vec3 sky_horizon = mix(vec3(1.0, 0.55, 0.20), vec3(0.50, 0.75, 0.95), pow(sun_elev, 0.5));
    vec3 sky_zenith  = mix(vec3(0.55, 0.05, 0.50), vec3(0.05, 0.20, 0.75), pow(sun_elev, 0.6));
    vec3 sky_R       = reflect(-V, N);
    vec3 sky_colour  = mix(sky_horizon, sky_zenith, clamp(sky_R.y * 0.5 + 0.5, 0.0, 1.0));

    // Shadow (ambient and Fresnel are unshadowed — indirect/sky light)
    float shadow = shadow_factor(frag_light_space_pos);

    // Combine — all lighting tinted by sun colour so ocean shifts warm at low elevation
    float diffuse_scale = mix(0.65, 1.3, sun_elev);
    vec3 colour = water_colour * sun_colour * (ambient + diffuse * shadow * diffuse_scale)
                + sun_colour * specular * shadow * fresnel * 6.0
                + sky_colour * fresnel * 0.7;

    // Foam — tinted by sun colour so it picks up warmth at low sun angles
    float foam = pow(clamp(texture(u_foam_mask, frag_uv).r, 0.0, 1.0), 0.5);
    vec3 foam_colour = mix(vec3(1.0), sun_colour, 0.15) * mix(1.0, 2.5, sun_elev);
    colour = mix(colour, foam_colour, foam * mix(0.85, 0.96, sun_elev));

    // Reinhard tone mapping — compresses HDR values instead of hard-clamping
    colour = colour / (colour + vec3(1.0));

    out_colour = vec4(colour, 1.0);
}
