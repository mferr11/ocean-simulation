#version 330

in vec3 frag_view_dir;

uniform vec3 u_sun_dir;

out vec4 out_colour;

void main() {
    vec3 dir = normalize(frag_view_dir);
    vec3 L = normalize(u_sun_dir);
    float sun_elev = clamp(L.y, 0.0, 1.0);

    // Same gradient as ocean.frag so reflections match the actual sky
    vec3 sky_horizon = mix(vec3(1.0, 0.55, 0.20), vec3(0.50, 0.75, 0.95), pow(sun_elev, 0.5));
    vec3 sky_zenith  = mix(vec3(0.05, 0.10, 0.30), vec3(0.05, 0.20, 0.75), pow(sun_elev, 0.6));

    float t = pow(clamp(dir.y, 0.0, 1.0), 0.5);
    vec3 sky = mix(sky_horizon, sky_zenith, t);

    // Subtle sun glow
    float sun_dot = max(dot(dir, L), 0.0);
    vec3 sun_colour = mix(vec3(1.0, 0.35, 0.05), vec3(1.0, 0.95, 0.85), pow(sun_elev, 0.3));
    sky += sun_colour * pow(sun_dot, 256.0) * 3.0;

    out_colour = vec4(sky, 1.0);
}
