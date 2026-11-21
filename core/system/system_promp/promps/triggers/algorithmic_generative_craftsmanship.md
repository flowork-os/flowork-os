# Context & Activation Scope
Active when engineering algorithmic art, canvas shaders, procedural geometry, p5.js scripts, SVG math graphics, audio-reactive visuals, or cellular automata.

# Mandatory Behavioral Invariants
1. **Deterministic Seeded PRNG:** Always implement or use a seeded pseudo-random number generator (PRNG) so generative systems reproduce identical states with the same seed.
2. **Organic Mathematical Variation:** Prefer smooth noise functions (Simplex/Perlin), harmonic trigonometry, and particle vectors over raw chaotic grid random noise.
3. **Harmonic Color Physics:** Design deliberate palettes using HSL/Oklab color spaces with calculated hue steps and optical weight balance, rather than random RGB clashing primaries.
4. **Canvas Performance & Lifecycle:** Scale canvases cleanly by `devicePixelRatio`, use `requestAnimationFrame` with delta time, and dispose of offscreen buffers/listeners to prevent memory leaks.

# Strict Prohibitions
- PROHIBITED: Unseeded chaotic randomness that renders visual output unrepeatable or buggy.
- PROHIBITED: Unbounded object/particle arrays that continuously allocate memory without pooling or culling.
- PROHIBITED: Blurry non-retina canvas rendering caused by ignoring `devicePixelRatio`.
