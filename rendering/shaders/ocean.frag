#version 330

in vec2 frag_uv;
in vec3 frag_normal;
in vec3 frag_world_pos;
in vec4 frag_light_space_pos;

uniform vec3 u_camera_pos;
uniform vec3 u_sun_dir;
uniform vec3 u_moon_dir;
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
    vec3 L_sun  = normalize(u_sun_dir);
    vec3 L_moon = normalize(u_moon_dir);

    // Day/night blend factors
    float sun_elev_c  = clamp(L_sun.y,  0.0, 1.0);
    float moon_elev_c = clamp(L_moon.y, 0.0, 1.0);
    float day_t    = smoothstep(-0.1, 0.1, L_sun.y);
    float moon_vis = max(L_moon.y, 0.0);

    // Height-based water colour: crest → shallow, trough → deep
    float height_factor = clamp(0.5 - frag_world_pos.y * u_depth_scale / u_height_scale, 0.0, 1.0);
    vec3 water_colour = mix(u_shallow_colour, u_deep_colour, height_factor);

    // Ambient — drops at night, tinted by the dominant light colour
    float ambient   = mix(mix(0.04, 0.06, moon_elev_c),
                          mix(0.12, 0.18, sun_elev_c),
                          day_t);
    vec3 sun_colour = mix(vec3(1.0, 0.35, 0.05), vec3(1.0, 0.95, 0.85), pow(sun_elev_c, 0.3));
    vec3 moon_col   = vec3(0.70, 0.75, 0.90);
    // Blend light tint so ambient uses moon colour at night, sun colour by day
    vec3 ambient_col = mix(moon_col, sun_colour, day_t);

    // Sun lighting
    float diffuse  = max(dot(N, L_sun), 0.0);
    vec3  R_sun    = reflect(-L_sun, N);
    float specular = pow(max(dot(R_sun, V), 0.0), 512.0);

    // Moon lighting
    float moon_diff = max(dot(N, L_moon), 0.0);
    vec3  R_moon    = reflect(-L_moon, N);
    float moon_r    = max(dot(R_moon, V), 0.0);
    // Medium lobe: visible on well-angled wave faces only (exponent 32 limits coverage)
    float moon_spec_wide  = pow(moon_r, 32.0);
    // Tight Fresnel glint: stark white highlight on best-aligned faces
    float moon_spec_tight = pow(moon_r, 2048.0);

    // Fresnel (Schlick) — used for sun specular and sky reflection only
    float R0 = 0.02;
    float fresnel = R0 + (1.0 - R0) * pow(1.0 - max(dot(V, N), 0.0), 5.0);

    // Sky reflection colours
    vec3 sky_hz_day   = mix(vec3(1.0, 0.55, 0.20), vec3(0.50, 0.75, 0.95), pow(sun_elev_c, 0.5));
    vec3 sky_zn_day   = mix(vec3(0.55, 0.05, 0.50), vec3(0.05, 0.20, 0.75), pow(sun_elev_c, 0.6));
    vec3 sky_hz_night = vec3(0.01, 0.02, 0.05);
    vec3 sky_zn_night = vec3(0.00, 0.01, 0.04);
    vec3 sky_horizon  = mix(sky_hz_night, sky_hz_day, day_t);
    vec3 sky_zenith   = mix(sky_zn_night, sky_zn_day,  day_t);
    vec3 sky_R        = reflect(-V, N);
    vec3 sky_colour   = mix(sky_horizon, sky_zenith, clamp(sky_R.y * 0.5 + 0.5, 0.0, 1.0));

    float shadow        = shadow_factor(frag_light_space_pos);
    float diffuse_scale = mix(0.65, 1.3, sun_elev_c);

    // Sun contribution
    vec3 sun_contrib = water_colour * sun_colour * diffuse * shadow * diffuse_scale * day_t
                     + sun_colour * specular * shadow * fresnel * 8.0 * day_t;

    // Moon contribution: diffuse + broad sheen + Fresnel glints
    vec3 moon_contrib = moon_col * (water_colour * moon_diff * 0.12
                                  + moon_spec_wide  * 0.6
                                  + moon_spec_tight * fresnel * 128.0)
                      * moon_vis * (1.0 - day_t * 0.95);

    vec3 colour = water_colour * ambient_col * ambient
                + sun_contrib
                + moon_contrib
                + sky_colour * fresnel * 0.7;

    // Foam
    float foam = pow(clamp(texture(u_foam_mask, frag_uv).r, 0.0, 1.0), 0.5);
    vec3 foam_col_day   = mix(vec3(1.0), sun_colour, 0.15) * mix(1.0, 2.5, sun_elev_c);
    vec3 foam_col_night = vec3(0.25, 0.28, 0.38) * mix(0.15, 0.30, moon_elev_c);
    vec3 foam_colour    = mix(foam_col_night, foam_col_day, day_t);
    colour = mix(colour, foam_colour, foam * mix(0.85, 0.96, sun_elev_c));

    // Reinhard tone mapping
    colour = colour / (colour + vec3(1.0));

    out_colour = vec4(colour, 1.0);
}
