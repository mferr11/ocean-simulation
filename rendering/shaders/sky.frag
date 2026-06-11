#version 330

in vec3 frag_view_dir;

uniform vec3 u_sun_dir;
uniform vec3 u_moon_dir;

out vec4 out_colour;

// Sin-free hash — avoids precision artefacts on some GPUs
vec2 star_hash(vec2 p) {
    p = fract(p * vec2(0.1031, 0.1030));
    p += dot(p, p.yx + 33.33);
    return fract((p.xx + p.yx) * p.xy);
}

float star_field(vec3 ray_dir, float scale) {
    // Cylindrical projection: uniform azimuth, slight compression near zenith
    float phi   = atan(ray_dir.z, ray_dir.x);
    float theta = asin(clamp(ray_dir.y, -1.0, 1.0));
    vec2 uv = vec2(phi, theta) * (1.0 / 3.14159265) * scale;

    vec2 cell_id    = floor(uv);
    vec2 cell_local = fract(uv);

    float min_dist = 1.0;
    for (int gx = -1; gx <= 1; gx++) {
        for (int gy = -1; gy <= 1; gy++) {
            vec2 nb  = vec2(float(gx), float(gy));
            vec2 pt  = nb + star_hash(cell_id + nb);
            min_dist = min(min_dist, length(cell_local - pt));
        }
    }

    float rand = star_hash(cell_id).x;
    if (rand < 0.62) return 0.0;
    float brightness = (rand - 0.62) / 0.38;
    float star_size  = mix(0.004, 0.010, brightness);
    return exp(-min_dist * min_dist / (star_size * star_size)) * brightness;
}

void main() {
    vec3 dir    = normalize(frag_view_dir);
    vec3 L_sun  = normalize(u_sun_dir);
    vec3 L_moon = normalize(u_moon_dir);

    float sun_elev_c = clamp(L_sun.y, 0.0, 1.0);
    float day_t      = smoothstep(-0.1, 0.1, L_sun.y);
    float moon_vis   = smoothstep(-0.05, 0.05, L_moon.y);

    // Sky gradient — blended between day and night palettes
    vec3 sky_hz_day   = mix(vec3(1.0, 0.55, 0.20), vec3(0.50, 0.75, 0.95), pow(sun_elev_c, 0.5));
    vec3 sky_zn_day   = mix(vec3(0.05, 0.10, 0.30), vec3(0.05, 0.20, 0.75), pow(sun_elev_c, 0.6));
    vec3 sky_hz_night = vec3(0.01, 0.02, 0.06);
    vec3 sky_zn_night = vec3(0.00, 0.01, 0.04);

    vec3 sky_horizon = mix(sky_hz_night, sky_hz_day, day_t);
    vec3 sky_zenith  = mix(sky_zn_night, sky_zn_day,  day_t);

    float t   = pow(clamp(dir.y, 0.0, 1.0), 0.5);
    vec3  sky = mix(sky_horizon, sky_zenith, t);

    // Sun glow (naturally disappears once sun is below horizon)
    float sun_dot    = max(dot(dir, L_sun), 0.0);
    vec3  sun_colour = mix(vec3(1.0, 0.35, 0.05), vec3(1.0, 0.95, 0.85), pow(sun_elev_c, 0.3));
    sky += sun_colour * pow(sun_dot, 1024.0) * 3.0 * day_t;

    // Moon disc — smoothstep over a sub-degree angular range gives a hard edge
    // cos(0.25°) ≈ 0.999990 (inner), cos(0.30°) ≈ 0.999986 (outer) for ~0.5° diameter
    float moon_dot  = dot(dir, L_moon);
    vec3  moon_col  = vec3(0.92, 0.95, 1.00);
    float moon_disc = smoothstep(0.9995, 0.999990, moon_dot) * 1.8;
    float moon_halo = pow(max(moon_dot, 0.0), 32.0) * 0.05;
    sky += moon_col * (moon_disc + moon_halo) * moon_vis * (1.0 - day_t * 0.9);

    // Stars — two Voronoi layers at different densities
    float above_horizon = smoothstep(-0.05, 0.05, dir.y);
    float star_alpha    = (1.0 - day_t) * above_horizon;
    float stars = star_field(dir, 40.0) + star_field(dir, 68.0) * 0.55;
    sky += vec3(0.90, 0.92, 1.0) * stars * star_alpha * 3.5;

    out_colour = vec4(sky, 1.0);
}
