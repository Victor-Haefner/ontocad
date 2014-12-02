varying vec2 texCoord;
varying vec2 ang;
varying vec2 pixelsize_tc;
void main() {
	float r = dot(texCoord, texCoord);
	if (r > 1.0) discard;

	float width = dot(pixelsize_tc, abs(texCoord));
	if (r < 1.0 - 3.0*width) discard;

	// angle
	float a = atan(texCoord.y, texCoord.x) + 3.14159265359;
	if (ang.x < ang.y) {
		if (a < ang.x) discard;
		if (a > ang.y) discard;
	} else if (a < ang.x && a > ang.y) discard;

	gl_FragColor = gl_Color;
	if (r < 1.0 - 1.5*width)
		gl_FragColor[3] = smoothstep(1.0 - 3.0*width, 1.0 - 1.5*width, r);
	if (r > 1.0 - 1.5*width)
		gl_FragColor[3] = 1.0 - smoothstep(1.0 - 1.5*width, 1.0, r);
}
