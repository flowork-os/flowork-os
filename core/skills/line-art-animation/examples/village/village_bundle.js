// ../../lib/ink.ts
var NS = "http://www.w3.org/2000/svg";
var INK = "currentColor";
var PAPER = "#fdfdfc";
var INK_DAY = "#1c1c1c";
var PEN = 1.35;
function el(tag, attrs = {}, parent) {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) n.setAttribute(k, String(attrs[k]));
  if (attrs.fill === PAPER) n.classList.add("pp");
  if (parent) parent.appendChild(n);
  return n;
}
var f = (n) => n.toFixed(2);
var pt = (p) => `${f(p[0])} ${f(p[1])}`;
var pen = (parent, w = PEN) => el("path", { fill: "none", stroke: INK, "stroke-width": w, "stroke-linecap": "round", "stroke-linejoin": "round" }, parent);
var shape = (parent, w = PEN) => el("path", { fill: PAPER, stroke: INK, "stroke-width": w, "stroke-linejoin": "round", "stroke-linecap": "round" }, parent);
var blot = (parent) => el("path", { fill: INK }, parent);
function limb(parent, width, w = PEN) {
  const g = el("g", {}, parent);
  const fill = el("path", { fill: PAPER }, g);
  const a = pen(g, w), b = pen(g, w);
  const half = (width - w) / 2;
  return {
    g,
    draw(joints, endGap = [0.4, 0.9]) {
      const s = joints[0], e = joints[joints.length - 1];
      let c = [(s[0] + e[0]) / 2, (s[1] + e[1]) / 2];
      if (joints.length === 3) {
        const m = joints[1];
        c = [m[0] + 0.55 * (m[0] - c[0]), m[1] + 0.55 * (m[1] - c[1])];
      }
      const P3 = [];
      for (let i = 0; i <= 16; i++) {
        const t = i / 16, u = 1 - t;
        P3.push([u * u * s[0] + 2 * u * t * c[0] + t * t * e[0], u * u * s[1] + 2 * u * t * c[1] + t * t * e[1]]);
      }
      const side = (sgn) => P3.map((p, i) => {
        const q2 = P3[Math.min(P3.length - 1, i + 1)], o = P3[Math.max(0, i - 1)];
        const dx = q2[0] - o[0], dy = q2[1] - o[1], l = Math.hypot(dx, dy) || 1;
        return [p[0] - dy / l * half * sgn, p[1] + dx / l * half * sgn];
      });
      const L = side(1), R = side(-1);
      fill.setAttribute("d", "M" + L.map(pt).join("L") + "L" + R.slice().reverse().map(pt).join("L") + "Z");
      const cut = (arr, gap) => arr.slice(0, arr.length - Math.round(gap * 2));
      a.setAttribute("d", "M" + cut(L, endGap[0]).map(pt).join("L"));
      b.setAttribute("d", "M" + cut(R, endGap[1]).map(pt).join("L"));
    }
  };
}
function joint(a, b, l1, l2, bend = 1) {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const d = Math.min(Math.hypot(dx, dy), l1 + l2 - 0.01);
  const th = Math.atan2(dy, dx);
  const al = Math.acos(Math.max(-1, Math.min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))));
  const c1 = [a[0] + l1 * Math.cos(th - al), a[1] + l1 * Math.sin(th - al)];
  const c2 = [a[0] + l1 * Math.cos(th + al), a[1] + l1 * Math.sin(th + al)];
  return (c1[0] - c2[0]) * bend > 0 ? c1 : c2;
}
function curve(keys, period2) {
  return (x) => {
    x = (x % period2 + period2) % period2;
    const n = keys.length;
    let i = n - 1;
    for (let j = 0; j < n; j++) if (keys[j][0] <= x) i = j;
    const k = (j) => {
      const w = Math.floor(j / n);
      const e = keys[(j % n + n) % n];
      return [e[0] + w * period2, e[1]];
    };
    const p0 = k(i - 1), p1 = k(i), p2 = k(i + 1), p3 = k(i + 2);
    const span = p2[0] - p1[0];
    const u = (x - p1[0]) / span;
    const m1 = (p2[1] - p0[1]) / (p2[0] - p0[0]) * span;
    const m2 = (p3[1] - p1[1]) / (p3[0] - p1[0]) * span;
    const u2 = u * u, u3 = u2 * u;
    return (2 * u3 - 3 * u2 + 1) * p1[1] + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * p2[1] + (u3 - u2) * m2;
  };
}
function inkDefs(svg2, id = "ink") {
  if (!svg2.style.color) svg2.style.color = INK_DAY;
  const defs2 = el("defs", {}, svg2);
  const flt = el("filter", { id: `${id}-edge`, x: "-2%", y: "-2%", width: "104%", height: "104%" }, defs2);
  el("feTurbulence", { type: "fractalNoise", baseFrequency: "0.6", numOctaves: 1, seed: 7, result: "n" }, flt);
  el("feDisplacementMap", { in: "SourceGraphic", in2: "n", scale: 0.45, xChannelSelector: "R", yChannelSelector: "G", result: "d" }, flt);
  el("feGaussianBlur", { in: "d", stdDeviation: 0.12 }, flt);
  const stripes = el("pattern", { id: `${id}-stripes`, width: 4, height: 2.2, patternUnits: "userSpaceOnUse", patternTransform: "rotate(-12)" }, defs2);
  el("rect", { width: 4, height: 2.2, fill: PAPER }, stripes);
  el("rect", { width: 4, height: 1, fill: INK }, stripes);
  return { defs: defs2, filter: `url(#${id}-edge)`, stripes: `url(#${id}-stripes)` };
}
function run(draw) {
  const q2 = new URLSearchParams(location.search);
  if (q2.has("debug")) {
    let t = 0;
    draw(t, 1 / 60);
    window.__step = (s = 1) => {
      for (let i = 0, n = Math.round(s * 60); i < n; i++) draw(t += 1 / 60, 1 / 60);
      return t;
    };
    return () => {
    };
  }
  const frozen = q2.has("t") ? Number(q2.get("t")) : null;
  const still = frozen !== null || matchMedia("(prefers-reduced-motion: reduce)").matches;
  const t0 = performance.now();
  let id = 0, prev = 0;
  const tick = (now) => {
    const t = frozen ?? (now - t0) / 1e3;
    draw(t, Math.min(0.05, t - prev));
    prev = t;
    if (!still) id = requestAnimationFrame(tick);
  };
  id = requestAnimationFrame(tick);
  return () => cancelAnimationFrame(id);
}

// kit.ts
var W = 960;
var H = 480;
var BASE = 344;
var LANE = { back: 360, mid: 366, front: 372 };
var EDGE = 384;
var WATER = 400;
var SP = 0.8;
var FS = 0.5;
var rnd = (a, b) => a + Math.random() * (b - a);
var pick = (arr) => arr[Math.random() * arr.length | 0];
var clamp = (x, a, b) => Math.max(a, Math.min(b, x));
var lerp = (a, b, t) => a + (b - a) * t;
var smooth = (e0, e1, x) => {
  const t = clamp((x - e0) / (e1 - e0), 0, 1);
  return t * t * (3 - 2 * t);
};
var ease = (t) => smooth(0, 1, t);
var oval = (cx, cy, rx, ry) => `M${(cx - rx).toFixed(2)} ${cy.toFixed(2)} a${rx} ${ry} 0 1 0 ${2 * rx} 0 a${rx} ${ry} 0 1 0 ${-2 * rx} 0Z`;
var seed = 11;
var srnd = (a, b) => {
  seed = seed * 16807 % 2147483647;
  return a + (seed - 1) / 2147483646 * (b - a);
};
var hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
var rgb = (c) => `rgb(${c.map((v) => Math.round(v)).join(",")})`;
var mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
var lum = (c) => (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255;
function ramp(keys, u) {
  u = (u % 1 + 1) % 1;
  const n = keys.length;
  let i = n - 1;
  for (let j = 0; j < n; j++) if (keys[j][0] <= u) i = j;
  const [p0, c0] = keys[i], [p1, c1] = keys[(i + 1) % n];
  const span = (i + 1 < n ? p1 : p1 + 1) - p0;
  let x = u - p0;
  if (x < 0) x += 1;
  return mix(hex(c0), hex(c1), ease(x / span));
}
var wobble = (t, k = 1) => Math.sin(t * 1.3 * k) * 0.6 + Math.sin(t * 2.7 * k + 1.7) * 0.3 + Math.sin(t * 5.1 * k + 4.1) * 0.1;

// sky.ts
var SKY_TOP = [[0, "#0d1222"], [0.19, "#131a30"], [0.235, "#3d4066"], [0.27, "#cfd8e2"], [0.33, "#f3f2ee"], [0.5, "#f6f5f1"], [0.68, "#f3eee4"], [0.735, "#e3c6a6"], [0.762, "#5a5279"], [0.8, "#1b2140"], [0.86, "#0d1222"]];
var SKY_BOT = [[0, "#1a2240"], [0.19, "#283050"], [0.235, "#d49884"], [0.27, "#f3d0b3"], [0.33, "#faf6ee"], [0.5, "#fcfbf7"], [0.68, "#f9efdc"], [0.735, "#f0a379"], [0.762, "#d47f68"], [0.8, "#383a60"], [0.86, "#1a2240"]];
var PAPERS = [[0, "#1a2036"], [0.19, "#1f263e"], [0.235, "#4a4561"], [0.27, "#ede4d8"], [0.33, "#fbf8f1"], [0.5, "#fdfcf8"], [0.68, "#faf4e8"], [0.735, "#f0dbc4"], [0.756, "#5d5571"], [0.8, "#262c48"], [0.86, "#1a2036"]];
var INK_DARK = hex("#1c1c1c");
var INK_LIGHT = hex("#efe6cf");
function palette(tau2) {
  const top = ramp(SKY_TOP, tau2), bot = ramp(SKY_BOT, tau2), paper = ramp(PAPERS, tau2);
  const L = lum(paper);
  const inkT = smooth(0.56, 0.36, L);
  return {
    top,
    bot,
    paper,
    ink: mix(INK_DARK, INK_LIGHT, inkT),
    inkT,
    lamp: smooth(0.78, 0.4, L),
    // how dark it is for lamps (windows add their own threshold)
    night: smooth(0.42, 0.1, lum(top)),
    // stars, moon glow, fireflies
    sunset: Math.max(smooth(0.67, 0.735, tau2) * smooth(0.79, 0.745, tau2), smooth(0.215, 0.245, tau2) * smooth(0.3, 0.26, tau2))
  };
}
var sunArc = (u) => [40 + 880 * u, 300 - 236 * Math.sin(Math.PI * u)];
var moonArc = (u) => [60 + 840 * u, 290 - 205 * Math.sin(Math.PI * u)];
var SUN_SPAN = [0.225, 0.55];
var MOON_SPAN = [0.775, 0.45];
function createSky(svg2, root, defs2, { onScrub, onShoot }) {
  const grad2 = el("linearGradient", { id: "v-sky", x1: 0, y1: 0, x2: 0, y2: 1 }, defs2);
  const s0 = el("stop", { offset: 0 }, grad2), s1 = el("stop", { offset: 1 }, grad2);
  const glowSun = el("radialGradient", { id: "v-sunglow" }, defs2);
  el("stop", { offset: 0, "stop-color": "#ffd9a0", "stop-opacity": 0.55 }, glowSun);
  el("stop", { offset: 1, "stop-color": "#ffd9a0", "stop-opacity": 0 }, glowSun);
  const glowMoon = el("radialGradient", { id: "v-moonglow" }, defs2);
  el("stop", { offset: 0, "stop-color": "#e9e4ff", "stop-opacity": 0.35 }, glowMoon);
  el("stop", { offset: 1, "stop-color": "#e9e4ff", "stop-opacity": 0 }, glowMoon);
  const g = el("g", {}, root);
  el("rect", { x: -20, y: -20, width: W + 40, height: 520, fill: "url(#v-sky)" }, g);
  const starG = el("g", {}, g);
  const stars = Array.from({ length: 90 }, () => {
    const x = srnd(0, W), y = srnd(6, 250), r = srnd(0.35, 1.05);
    return { n: el("circle", { cx: f(x), cy: f(y), r: f(r), fill: "#f5efda" }, starG), ph: srnd(0, 6), sp: srnd(0.6, 2.4), big: r > 0.9, spark: null };
  });
  stars.filter((s) => s.big).forEach((s) => {
    const x = +s.n.getAttribute("cx"), y = +s.n.getAttribute("cy");
    s.spark = el("path", { d: `M${x - 2.6} ${y} L${x + 2.6} ${y} M${x} ${y - 2.6} L${x} ${y + 2.6}`, stroke: "#f5efda", "stroke-width": 0.35, opacity: 0.6 }, starG);
  });
  const shoots = [];
  const sunG = el("g", { class: "drag", style: "cursor:grab" }, g);
  const sunGlow = el("circle", { r: 70, fill: "url(#v-sunglow)" }, sunG);
  const sunDisk = el("circle", { r: 21, stroke: "currentColor", "stroke-width": SP }, sunG);
  el("title", {}, sunG).textContent = "Drag the sun to change the time";
  const moonG = el("g", { class: "drag", style: "cursor:grab" }, g);
  el("circle", { r: 60, fill: "url(#v-moonglow)" }, moonG);
  const moonDisk = el("path", { fill: "#f3ecd6", stroke: "#f3ecd6", "stroke-width": 0.6 }, moonG);
  const moonShade = el("path", { fill: "none", stroke: "#cfc6ad", "stroke-width": 0.5, opacity: 0.7 }, moonG);
  el("title", {}, moonG).textContent = "Drag the moon to change the time";
  const mist = el("g", {}, g);
  const bands = [[120, 92, 150], [520, 64, 190], [760, 120, 130], [330, 140, 100]].map(([x, y, w]) => ({ x, y, w, v: rnd(1.2, 2.6), n: pen(mist, SP * 0.75) }));
  const cloudD = (x, y, w) => {
    const curlR = (cx, cy, s) => `M${f(cx)} ${f(cy)} q${5 * s} 0 ${5 * s} -4 q0 -3.2 ${-3.2 * s} -3.2 q-2.2 0 -2.2 2.2 q0 1.4 1.4 1.4`;
    return `M${f(x)} ${f(y)} L${f(x + w)} ${f(y)} ${curlR(x + w, y, 1)} ${curlR(x, y, -1)} M${f(x + w * 0.18)} ${f(y - 7)} L${f(x + w * 0.66)} ${f(y - 7)} ${curlR(x + w * 0.66, y - 7, 1)} M${f(x + w * 0.42)} ${f(y + 6.5)} L${f(x + w * 0.92)} ${f(y + 6.5)} ${curlR(x + w * 0.42, y + 6.5, -1)}`;
  };
  const far = el("g", { opacity: 0.42 }, g);
  pen(far, SP * 0.8).setAttribute("d", "M0 262 Q80 238 170 222 Q240 206 300 214 Q360 222 420 208 Q470 196 520 188 Q600 176 660 198 Q720 218 790 206 Q860 192 960 214");
  pen(far, SP * 0.55).setAttribute("d", "M140 228 q20 -6 40 -4 M300 216 q16 -2 30 2 M560 186 q26 -4 44 4 M820 202 q18 -4 32 0");
  drawPagoda(far, 640, 236);
  let drag = null;
  const toSvg2 = (e) => {
    const p = svg2.createSVGPoint();
    p.x = e.clientX;
    p.y = e.clientY;
    return p.matrixTransform(svg2.getScreenCTM().inverse());
  };
  const start = (kind) => (e) => {
    e.preventDefault();
    e.stopPropagation();
    drag = kind;
    svg2.setPointerCapture?.(e.pointerId);
    svg2.classList.add("scrubbing");
  };
  sunG.addEventListener("pointerdown", start("sun"));
  moonG.addEventListener("pointerdown", start("moon"));
  svg2.addEventListener("pointermove", (e) => {
    if (!drag) return;
    const p = toSvg2(e);
    if (drag === "sun") onScrub(SUN_SPAN[0] + SUN_SPAN[1] * clamp((p.x - 40) / 880, 0, 1));
    else onScrub((MOON_SPAN[0] + MOON_SPAN[1] * clamp((p.x - 60) / 840, 0, 1)) % 1);
  });
  const end = () => {
    if (drag) {
      drag = null;
      svg2.classList.remove("scrubbing");
      onScrub(null);
    }
  };
  svg2.addEventListener("pointerup", end);
  svg2.addEventListener("pointercancel", end);
  const skyHit = el("rect", { x: 0, y: 0, width: W, height: 160, fill: "transparent" }, g);
  skyHit.addEventListener("pointerdown", (e) => {
    if (onShoot()) {
      const p = toSvg2(e);
      shoot(p.x, p.y);
    }
  });
  g.insertBefore(skyHit, sunG);
  function shoot(x, y) {
    shoots.push({ x: x - 30, y: y - 18, t: 0, dir: Math.random() < 0.5 ? -1 : 1, n: el("path", { stroke: "#fff6dc", "stroke-width": 0.9, "stroke-linecap": "round", fill: "none" }, starG) });
  }
  return {
    shoot,
    draw(tau2, t, dt, P3, wind2) {
      s0.setAttribute("stop-color", rgb(P3.top));
      s1.setAttribute("stop-color", rgb(P3.bot));
      starG.setAttribute("opacity", f(P3.night));
      if (P3.night > 0.01) stars.forEach((s) => {
        const tw = 0.55 + 0.45 * Math.sin(t * s.sp + s.ph);
        s.n.setAttribute("opacity", f(tw));
        if (s.spark) s.spark.setAttribute("opacity", f(tw * 0.7));
      });
      if (P3.night > 0.6 && Math.random() < dt * 0.04) shoot(rnd(100, 860), rnd(30, 110));
      for (let i = shoots.length - 1; i >= 0; i--) {
        const s = shoots[i];
        s.t += dt;
        const u = s.t / 0.9, x = s.x + s.dir * 120 * u, y = s.y + 60 * u;
        s.n.setAttribute("d", `M${f(x)} ${f(y)} L${f(x - s.dir * 34 * (1 - u))} ${f(y - 17 * (1 - u))}`);
        s.n.setAttribute("opacity", f(Math.sin(Math.PI * Math.min(1, u))));
        if (u >= 1) {
          s.n.remove();
          shoots.splice(i, 1);
        }
      }
      const su = (tau2 - SUN_SPAN[0]) / SUN_SPAN[1];
      if (su > -0.05 && su < 1.05) {
        const [x, y] = sunArc(clamp(su, 0, 1));
        sunG.setAttribute("transform", `translate(${f(x)} ${f(y + (su < 0 || su > 1 ? 30 : 0))})`);
        sunG.style.display = "";
        sunDisk.setAttribute("fill", rgb(mix(hex("#fbf3df"), hex("#df5a3a"), P3.sunset)));
        sunGlow.setAttribute("opacity", f(0.35 + 0.65 * P3.sunset));
      } else sunG.style.display = "none";
      const mu = ((tau2 - MOON_SPAN[0]) % 1 + 1) % 1 / MOON_SPAN[1];
      if (mu <= 1.02) {
        const [x, y] = moonArc(clamp(mu, 0, 1));
        moonG.setAttribute("transform", `translate(${f(x)} ${f(y)}) rotate(-24)`);
        moonG.style.display = "";
        moonG.setAttribute("opacity", f(smooth(0, 0.08, mu) * smooth(1.02, 0.94, mu)));
        const r = 15;
        moonDisk.setAttribute("d", `M0 ${-r} A${r} ${r} 0 1 1 0 ${r} A${r * 0.62} ${r} 0 1 0 0 ${-r}Z`);
        moonShade.setAttribute("d", `M3 -6 a2.4 1.8 0 1 0 0.1 0 M8 4 a1.6 1.3 0 1 0 0.1 0`);
      } else moonG.style.display = "none";
      mist.setAttribute("opacity", f(0.75 - 0.45 * P3.night));
      bands.forEach((b) => {
        b.x += (b.v + wind2 * 3) * dt;
        if (b.x > W + 40) b.x = -b.w - 40;
        if (b.x < -b.w - 60) b.x = W + 30;
        b.n.setAttribute("d", cloudD(b.x, b.y, b.w));
      });
    }
  };
}
function drawPagoda(g, cx, baseY) {
  let y = baseY;
  for (let i = 0; i < 5; i++) {
    const w = 36 - i * 4.2, bodyH = 9 - i * 0.6;
    shape(g, SP * 0.75).setAttribute("d", `M${cx - w * 0.42} ${y} L${cx + w * 0.42} ${y} L${cx + w * 0.42} ${y - bodyH} L${cx - w * 0.42} ${y - bodyH}Z`);
    pen(g, SP * 0.5).setAttribute("d", `M${cx - w * 0.18} ${y} L${cx - w * 0.18} ${y - bodyH} M${cx + w * 0.18} ${y} L${cx + w * 0.18} ${y - bodyH}`);
    y -= bodyH;
    shape(g, SP * 0.75).setAttribute("d", `M${cx - w} ${y + 1} Q${cx - w * 0.6} ${y - 1} ${cx - w * 0.35} ${y - 5} L${cx + w * 0.35} ${y - 5} Q${cx + w * 0.6} ${y - 1} ${cx + w} ${y + 1} Q${cx} ${y - 2} ${cx - w} ${y + 1}Z`);
    y -= 5;
  }
  pen(g, SP * 0.8).setAttribute("d", `M${cx} ${y} L${cx} ${y - 26}`);
  pen(g, SP * 0.5).setAttribute("d", Array.from({ length: 6 }, (_, k) => `M${cx - 2.6} ${y - 4 - k * 3} L${cx + 2.6} ${y - 4 - k * 3}`).join(" "));
}

// houses.ts
var JP = '"Hiragino Mincho ProN","Yu Mincho","YuMincho","Noto Serif JP","Songti SC",serif';
var RED = hex("#b3412d");
var RED_NIGHT = hex("#6e2a22");
var WARM = hex("#ffcf7e");
var WARM_DEEP = hex("#f3a54d");
var P = (g, d, w = SP) => {
  const n = pen(g, w);
  n.setAttribute("d", d);
  return n;
};
var S = (g, d, w = SP) => {
  const n = shape(g, w);
  n.setAttribute("d", d);
  return n;
};
var B = (g, d) => {
  const n = blot(g);
  n.setAttribute("d", d);
  return n;
};
var rect = (x0, y0, x1, y1) => `M${x0} ${y0} L${x1} ${y0} L${x1} ${y1} L${x0} ${y1}Z`;
function text(g, x, y, s, size, { vertical = false, weight = 600, anchor = "middle", fill = "currentColor" } = {}) {
  const n = el("text", { x, y, "font-size": size, "font-family": JP, "font-weight": weight, fill, "text-anchor": anchor, "dominant-baseline": "central" }, g);
  if (vertical) {
    n.setAttribute("writing-mode", "vertical-rl");
    n.setAttribute("glyph-orientation-vertical", "0");
  }
  n.textContent = s;
  return n;
}
function roof(g, { x0, x1, eave, ridge, inset, tile = 5.6, sori = 2.8, depth = 2.6, oni = true, rafters = true }) {
  const cx = (x0 + x1) / 2;
  const eaveY = (x) => eave - sori * Math.pow(Math.abs(x - cx) / ((x1 - x0) / 2), 2.2);
  S(g, `M${x0} ${eaveY(x0)} Q${cx} ${eave + sori * 0.6} ${x1} ${eaveY(x1)} L${x1 - inset} ${ridge} L${x0 + inset} ${ridge}Z`);
  const ch = [], ends = [];
  for (let x = x0 + tile * 0.8; x < x1 - tile * 0.4; x += tile) {
    const t = (x - x0) / (x1 - x0), ey = eaveY(x) - 0.4;
    const top = lerp(x0 + inset, x1 - inset, t);
    ch.push(`M${f(x)} ${f(ey - 1.6)} Q${f(lerp(x, top, 0.5) + (t - 0.5) * 2)} ${f(lerp(ey, ridge, 0.55))} ${f(top)} ${ridge + 1}`);
    ends.push(oval(x, ey, 1.35, 1.35));
  }
  P(g, ch.join(" "), SP * 0.5);
  const tiles = el("path", { d: ends.join(" "), fill: PAPER, stroke: "currentColor", "stroke-width": SP * 0.55 }, g);
  P(g, `M${x0 + 1} ${eaveY(x0) + depth} Q${cx} ${eave + sori * 0.6 + depth} ${x1 - 1} ${eaveY(x1) + depth}`, SP * 0.7);
  if (rafters) {
    const r = [];
    for (let x = x0 + 5; x < x1 - 3; x += 4.2) r.push(`M${f(x)} ${f(eaveY(x) + depth + 0.6)} l0 1.8`);
    P(g, r.join(" "), SP * 0.6);
  }
  const rx0 = x0 + inset - 4, rx1 = x1 - inset + 4;
  S(g, rect(rx0, ridge - 5.5, rx1, ridge + 0.5), SP * 0.9);
  P(g, `M${rx0} ${ridge - 2.6} L${rx1} ${ridge - 2.6}`, SP * 0.5);
  if (oni) [rx0, rx1].forEach((x, i) => {
    const s = i ? 1 : -1;
    S(g, `M${x} ${ridge + 0.5} L${x} ${ridge - 6} Q${x + s * 0.5} ${ridge - 11} ${x + s * 4.5} ${ridge - 12} Q${x + s * 6.5} ${ridge - 9} ${x + s * 5} ${ridge - 6} L${x + s * 5} ${ridge + 0.5}Z`, SP * 0.85);
    P(g, `M${x + s * 1.6} ${ridge - 4} q${s * 1.4} -1 ${s * 1.8} 1`, SP * 0.5);
  });
  return { tiles };
}
function koshi(g, x0, x1, y0, y1, { gap = 2.3 } = {}) {
  const top = y0 + (y1 - y0) * 0.16;
  S(g, rect(x0, y0, x1, y1), SP * 0.9);
  const d = [`M${x0} ${f(top)} L${x1} ${f(top)}`, `M${x0} ${y1 - 3} L${x1} ${y1 - 3}`];
  let k = 0;
  for (let x = x0 + gap; x < x1 - 0.5; x += gap, k++) {
    if (k % 4 === 3) d.push(`M${f(x)} ${y0} L${f(x)} ${y1}`);
    else d.push(`M${f(x)} ${f(top)} L${f(x)} ${y1 - 3}`);
  }
  P(g, d.join(" "), SP * 0.55);
}
function mushiko(g, x0, y0, x1, y1) {
  S(g, `M${x0 + 3} ${y0} L${x1 - 3} ${y0} Q${x1} ${y0} ${x1} ${y0 + 3} L${x1} ${y1 - 3} Q${x1} ${y1} ${x1 - 3} ${y1} L${x0 + 3} ${y1} Q${x0} ${y1} ${x0} ${y1 - 3} L${x0} ${y0 + 3} Q${x0} ${y0} ${x0 + 3} ${y0}Z`, SP);
  const d = [];
  for (let x = x0 + 4; x < x1 - 3; x += 5) d.push(`M${x} ${y0 + 2.5} Q${x - 0.6} ${(y0 + y1) / 2} ${x} ${y1 - 2.5} M${x + 2.4} ${y0 + 2.5} Q${x + 1.8} ${(y0 + y1) / 2} ${x + 2.4} ${y1 - 2.5}`);
  P(g, d.join(" "), SP * 0.55);
}
function inuyarai(g, x0, x1, y0) {
  const d = [`M${x0} ${y0 + 1} Q${(x0 + x1) / 2} ${y0 - 1} ${x1} ${y0 + 1}`, `M${x0 - 1} ${BASE - 1} L${x1 + 1} ${BASE - 1}`];
  for (let x = x0 + 1.5; x < x1; x += 2.6) d.push(`M${f(x)} ${y0 + 1} Q${f(x + 0.4)} ${f((y0 + BASE) / 2 + 3)} ${f(x - 0.6)} ${BASE - 1}`);
  P(g, d.join(" "), SP * 0.5);
}
function pane(g, glowG, x0, y0, x1, y1, { thr = srnd(0.15, 0.6), lateOff = srnd(0, 1) < 0.45 ? srnd(0.93, 1.12) : 9, warmth = srnd(0, 1) } = {}) {
  const n = el("path", { d: rect(x0, y0, x1, y1), fill: PAPER }, g);
  const glow2 = el("ellipse", { cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, rx: (x1 - x0) * 0.9 + 10, ry: (y1 - y0) * 0.9 + 10, fill: "url(#v-warmglow)", opacity: 0 }, glowG);
  return { n, glow: glow2, thr, lateOff, warmth, x0, y0, x1, y1, lit: 0 };
}
function noren(g, x0, x1, y, len, panels, label, { open = [0.28, 0.88], red = false } = {}) {
  const grp = el("g", {}, g);
  P(grp, `M${x0 - 2} ${y} L${x1 + 2} ${y}`, SP * 1.2);
  const w = (x1 - x0) / panels;
  const cloth = Array.from({ length: panels }, (_, i) => ({ x: x0 + i * w, w: w - 0.8, n: el("path", { fill: red ? rgb(RED) : PAPER, stroke: "currentColor", "stroke-width": SP * 0.8, "stroke-linejoin": "round" }, grp), a: 0, v: 0, ph: srnd(0, 6) }));
  const label_ = text(grp, (x0 + x1) / 2, y + len * 0.48, label, Math.min(len * 0.42, w * 0.95), { weight: 700, fill: red ? "#fbf3e6" : "currentColor" });
  return {
    grp,
    cloth,
    label: label_,
    y,
    len,
    open,
    red,
    x0,
    x1,
    show: 1,
    draw(t, dt, wind2, tau2, P_) {
      const [o0, o1] = this.open;
      const isOpen = o1 > 1 ? tau2 > o0 || tau2 < o1 - 1 : tau2 > o0 && tau2 < o1;
      this.show = this.first === void 0 ? (this.first = 1, isOpen ? 1 : 0) : clamp(this.show + (isOpen ? dt : -dt) * 0.8, 0, 1);
      this.grp.setAttribute("opacity", f(this.show));
      this.grp.setAttribute("transform", `translate(0 ${f(-(1 - ease(this.show)) * 6)})`);
      if (this.red) this.cloth.forEach((c) => c.n.setAttribute("fill", rgb(mix(RED, RED_NIGHT, P_.inkT))));
      let sw = 0;
      this.cloth.forEach((c, i) => {
        c.v += (-c.a * 22 + wind2 * 2.2 + Math.sin(t * 1.7 + c.ph) * 0.6 - c.v * 3.2) * dt;
        c.a += c.v * dt;
        const s = c.a * this.len * 0.45, flt = Math.sin(t * 3.1 + i) * 0.5;
        c.n.setAttribute("d", `M${f(c.x)} ${this.y} L${f(c.x + c.w)} ${this.y} Q${f(c.x + c.w + s * 0.4)} ${f(this.y + this.len * 0.6)} ${f(c.x + c.w + s + flt)} ${f(this.y + this.len)} L${f(c.x + s + flt)} ${f(this.y + this.len - 0.6)} Q${f(c.x + s * 0.4)} ${f(this.y + this.len * 0.6)} ${f(c.x)} ${this.y}Z`);
        sw += s;
      });
      this.label.setAttribute("transform", `translate(${f(sw / this.cloth.length * 0.6)} 0)`);
    },
    poke() {
      this.cloth.forEach((c) => c.v += 3 + Math.random() * 2);
    }
  };
}
function chochin(g, glowG, x, y, { r = 7, h = 16, label = "", red = false } = {}) {
  const grp = el("g", {}, g);
  const body = el("path", { d: `M${-r * 0.75} 4 Q${-r * 1.18} ${4 + h / 2} ${-r * 0.75} ${4 + h} L${r * 0.75} ${4 + h} Q${r * 1.18} ${4 + h / 2} ${r * 0.75} 4Z`, fill: red ? rgb(RED) : PAPER, stroke: "currentColor", "stroke-width": SP * 0.8 }, grp);
  const ribs = [];
  for (let k = 1; k < 5; k++) {
    const yy = 4 + h * k / 5, wv = r * (1.18 - 0.3 * Math.abs(k / 5 - 0.5) * 2);
    ribs.push(`M${f(-wv * 0.95)} ${f(yy)} Q0 ${f(yy + 1)} ${f(wv * 0.95)} ${f(yy)}`);
  }
  P(grp, ribs.join(" "), SP * 0.4);
  B(grp, `M${-r * 0.6} 2 L${r * 0.6} 2 L${r * 0.6} 4.4 L${-r * 0.6} 4.4Z M${-r * 0.6} ${4 + h - 0.4} L${r * 0.6} ${4 + h - 0.4} L${r * 0.6} ${6.4 + h} L${-r * 0.6} ${6.4 + h}Z`);
  P(grp, "M0 -4 L0 2", SP * 0.5);
  const lbl = label ? text(grp, 0, 4 + h / 2, label, h * 0.42, { vertical: label.length > 1, weight: 700, fill: red ? "#fbf3e6" : "currentColor" }) : null;
  const glow2 = el("circle", { r: 30 + r, fill: "url(#v-warmglow)", opacity: 0 }, glowG);
  return {
    grp,
    body,
    glow: glow2,
    lbl,
    x,
    y,
    h,
    red,
    a: srnd(-0.05, 0.05),
    v: 0,
    ph: srnd(0, 6),
    thr: srnd(0.1, 0.3),
    draw(t, dt, wind2, P_) {
      this.v += (-this.a * 10 + wind2 * 0.5 + Math.sin(t * 0.9 + this.ph) * 0.15 - this.v * 1.1) * dt;
      this.a += this.v * dt;
      this.grp.setAttribute("transform", `translate(${this.x} ${this.y}) rotate(${f(-this.a * 57.3)})`);
      const lit = smooth(this.thr, this.thr + 0.2, P_.lamp);
      const base = this.red ? mix(RED, RED_NIGHT, P_.inkT * (1 - lit)) : P_.paper;
      this.body.setAttribute("fill", rgb(mix(base, this.red ? hex("#ff8a4a") : WARM, lit * 0.95)));
      const cx = this.x + Math.sin(this.a) * -(this.h / 2 + 4), cy = this.y + Math.cos(this.a) * (this.h / 2 + 4);
      this.glow.setAttribute("cx", f(cx));
      this.glow.setAttribute("cy", f(cy));
      this.glow.setAttribute("opacity", f(lit * (0.85 + 0.15 * Math.sin(t * 7 + this.ph) * Math.sin(t * 3.3))));
    },
    poke() {
      this.v += (Math.random() < 0.5 ? -1 : 1) * (1.8 + Math.random());
    }
  };
}
function buildStreet(layers, defs2) {
  const { back: back2, houses: hg, front: front2, glow: glow2 } = layers;
  const g = (parent) => el("g", {}, parent);
  const glowGrad = el("radialGradient", { id: "v-warmglow" }, defs2);
  el("stop", { offset: 0, "stop-color": "#ffd58a", "stop-opacity": 0.75 }, glowGrad);
  el("stop", { offset: 0.45, "stop-color": "#ffb85c", "stop-opacity": 0.28 }, glowGrad);
  el("stop", { offset: 1, "stop-color": "#ffb85c", "stop-opacity": 0 }, glowGrad);
  const windows = [], lanterns = [], norens = [];
  const tree = g(back2);
  P(tree, "M452 344 Q450 300 446 268 Q440 236 420 214 M462 344 Q463 300 468 262 Q474 236 500 214 M447 262 Q458 248 456 226 Q455 206 462 192", SP * 1.1);
  P(tree, "M430 224 l-10 -6 M490 222 l12 -4 M456 212 l-8 -10 M468 236 q10 -4 14 -12", SP * 0.7);
  const canopy = g(tree);
  const blossoms = [];
  [[414, 206, 26], [502, 200, 28], [458, 176, 30], [434, 186, 22], [486, 180, 22], [460, 204, 26], [520, 216, 18], [400, 222, 18]].forEach(([cx, cy, r]) => {
    const pts = [];
    for (let i = 0; i <= 60; i++) {
      const a = i / 60 * Math.PI * 2;
      const rr = r + 2 * Math.abs(Math.sin(a * 6.5)) - 0.6 * Math.sin(a * 3);
      pts.push([cx + rr * Math.cos(a), cy + rr * 0.78 * Math.sin(a)]);
    }
    S(canopy, "M" + pts.map(pt).join("L") + "Z", SP * 0.8);
  });
  const fl = [];
  for (let i = 0; i < 110; i++) {
    const a = srnd(0, 6.28), d = Math.sqrt(srnd(0, 1));
    const [cx, cy, r] = [[458, 196, 54], [414, 210, 26], [502, 204, 28]][i % 3];
    const x = cx + Math.cos(a) * r * d * 0.95, y = cy + Math.sin(a) * r * 0.62 * d;
    blossoms.push([x, y]);
    const s = srnd(0.8, 1.3);
    fl.push(`M${f(x)} ${f(y - s)} l${f(s * 0.95)} ${f(s * 0.7)} l${f(-s * 0.4)} ${f(s * 1.1)} l${f(-s * 1.1)} 0 l${f(-s * 0.4)} ${f(-s * 1.1)}Z`);
  }
  P(canopy, fl.join(" "), SP * 0.45);
  const alley = g(back2);
  S(alley, rect(432, 250, 482, BASE), SP * 0.6);
  S(alley, "M432 258 L449 286 L449 306 L432 344Z", SP * 0.6);
  S(alley, "M482 258 L465 286 L465 306 L482 344Z", SP * 0.6);
  P(alley, "M436 265 L436 337 M440 271 L440 330 M444 278 L444 322 M478 265 L478 337 M474 271 L474 330 M470 278 L470 322", SP * 0.4);
  S(alley, rect(449, 288, 465, 306), SP * 0.7);
  S(alley, "M446 289 L468 289 L465 283 L449 283Z", SP * 0.7);
  P(alley, "M457 289 L457 306", SP * 0.5);
  [[457, 339, 7, 2.4], [456, 328, 5.6, 1.9], [458, 319, 4.4, 1.5], [457, 312, 3.4, 1.1]].forEach(([x, y, rx, ry]) => S(alley, oval(x, y, rx, ry), SP * 0.5));
  const alleyLamp = pane(alley, glow2, 453.5, 293, 460.5, 301, { thr: 0.05, lateOff: 9 });
  P(alley, "M457 293 L457 301 M453.5 297 L460.5 297", SP * 0.4);
  const h1 = g(hg);
  [[26, 206], [220, 206]].forEach(([x, y]) => {
    S(h1, rect(x, y + 4, x + 8, 262), SP * 0.8);
    S(h1, `M${x - 3} ${y + 5} L${x + 11} ${y + 5} L${x + 8} ${y} L${x} ${y}Z`, SP * 0.7);
  });
  S(h1, rect(32, 214, 222, 262));
  roof(h1, { x0: 12, x1: 242, eave: 218, ridge: 184, inset: 28 });
  mushiko(h1, 46, 230, 128, 252);
  S(h1, rect(140, 228, 212, 250), SP * 1.1);
  P(h1, rect(142.5, 230.5, 209.5, 247.5), SP * 0.5);
  text(h1, 176, 239.5, "\u767D\u6885 \u9152", 11.5, { weight: 800 });
  S(h1, rect(20, 270, 234, BASE));
  roof(h1, { x0: 14, x1: 240, eave: 274, ridge: 262, inset: 6, tile: 5, sori: 1.4, oni: false });
  windows.push(pane(h1, glow2, 28, 284, 88, 336));
  koshi(h1, 26, 90, 280, 340);
  S(h1, rect(114, 280, 166, BASE), SP * 0.9);
  windows.push(pane(h1, glow2, 117, 283, 163, BASE - 1, { thr: 0.05, lateOff: 0.9 }));
  P(h1, "M117 314 L163 314 M140 283 L140 344", SP * 0.45);
  norens.push(noren(h1, 116, 164, 281, 26, 3, "\u9152", { open: [0.29, 0.86] }));
  const barrel = (x, y, w, h) => {
    S(h1, `M${x} ${y + 2} Q${x + w / 2} ${y - 1} ${x + w} ${y + 2} L${x + w} ${y + h - 2} Q${x + w / 2} ${y + h + 1} ${x} ${y + h - 2}Z`, SP * 0.9);
    P(h1, `M${x} ${y + 6} Q${x + w / 2} ${y + 3.5} ${x + w} ${y + 6} M${x} ${y + h - 6} Q${x + w / 2} ${y + h - 3.5} ${x + w} ${y + h - 6} M${x + 3} ${y + 1} L${x + 3} ${y + h - 1} M${x + w - 3} ${y + 1} L${x + w - 3} ${y + h - 1}`, SP * 0.5);
    S(h1, oval(x + w / 2, y + h / 2, w * 0.24, h * 0.24), SP * 0.6);
    text(h1, x + w / 2, y + h / 2, "\u9152", w * 0.26, { weight: 800 });
  };
  barrel(172, 318, 28, 26);
  barrel(202, 318, 28, 26);
  barrel(187, 292, 28, 26);
  P(h1, "M102 274 L102 280", SP * 0.6);
  const sug = [];
  for (let i = 0; i < 360; i++) {
    const a = srnd(0, 6.28), d = Math.sqrt(srnd(0, 1)) * 11.2;
    const x = 102 + Math.cos(a) * d, y = 292 + Math.sin(a) * d;
    const b = srnd(0, 6.28);
    sug.push(`M${f(x)} ${f(y)} l${f(Math.cos(b) * 1.6)} ${f(Math.sin(b) * 1.6)}`);
  }
  S(h1, oval(102, 292, 12, 12), SP * 0.8);
  P(h1, sug.join(" "), SP * 0.45);
  P(h1, "M97 303 l10 0 M100 303 l-1 5 M105 303 l1 5", SP * 0.5);
  const h2 = g(hg);
  S(h2, rect(246, 200, 424, 260));
  roof(h2, { x0: 230, x1: 438, eave: 204, ridge: 168, inset: 26 });
  const shojiWin = pane(h2, glow2, 262, 212, 318, 250, { thr: 0.12, lateOff: 1.08 });
  windows.push(shojiWin);
  const interior = g(h2);
  const room = el("path", { d: rect(262, 212, 318, 250), fill: "#3a2c22" }, interior);
  const person = g(interior);
  S(person, "M294 250 Q295 236 304 234 Q313 236 314 250Z", SP * 0.8);
  const face = S(person, oval(304, 227, 5, 6), SP * 0.8);
  B(person, "M298.6 226 Q299 219 304 219 Q309.4 219 309.4 226 Q307 222.5 304 223 Q301 222.5 298.6 226Z M302 219.4 a2.6 2.2 0 1 1 4 0Z");
  const waveArm = limb(person, 3, SP * 0.7);
  const slide = g(h2);
  const shojiGrid = (gg, x0, y0, x1, y1, cols, rows) => {
    const d = [rect(x0, y0, x1, y1)];
    for (let i = 1; i < cols; i++) {
      const x = lerp(x0, x1, i / cols);
      d.push(`M${f(x)} ${y0} L${f(x)} ${y1}`);
    }
    for (let j = 1; j < rows; j++) {
      const y = lerp(y0, y1, j / rows);
      d.push(`M${x0} ${f(y)} L${x1} ${f(y)}`);
    }
    P(gg, d.join(" "), SP * 0.5);
  };
  const slidePane = el("path", { d: rect(290, 212, 318, 250), fill: PAPER }, slide);
  shojiGrid(slide, 290, 212, 318, 250, 3, 5);
  shojiGrid(h2, 262, 212, 290, 250, 3, 5);
  P(h2, rect(262, 212, 318, 250), SP);
  windows.push(pane(h2, glow2, 340, 212, 404, 250, { thr: 0.3 }));
  shojiGrid(h2, 340, 212, 372, 250, 3, 5);
  shojiGrid(h2, 372, 212, 404, 250, 3, 5);
  P(h2, rect(340, 212, 404, 250), SP);
  const rail = g(h2);
  S(rail, rect(250, 238, 418, 258), SP * 0.8);
  const bal = [];
  for (let x = 254; x < 416; x += 5.2) bal.push(`M${f(x)} 241 L${f(x)} 256`);
  P(rail, bal.join(" ") + " M250 241 L418 241", SP * 0.5);
  S(h2, rect(240, 268, 428, BASE));
  roof(h2, { x0: 232, x1: 436, eave: 272, ridge: 260, inset: 6, tile: 5, sori: 1.4, oni: false });
  windows.push(pane(h2, glow2, 246, 282, 294, 322));
  koshi(h2, 244, 296, 278, 324);
  windows.push(pane(h2, glow2, 366, 282, 422, 322, { thr: 0.25 }));
  koshi(h2, 364, 424, 278, 324);
  inuyarai(h2, 244, 296, 326);
  inuyarai(h2, 364, 424, 326);
  S(h2, rect(304, 278, 356, BASE), SP * 0.9);
  windows.push(pane(h2, glow2, 306, 280, 354, BASE - 1, { thr: 0.2 }));
  const dd = [];
  for (let x = 308; x < 354; x += 3.4) dd.push(`M${f(x)} 280 L${f(x)} 343`);
  for (let y = 290; y < 342; y += 12) dd.push(`M306 ${y} L354 ${y}`);
  P(h2, dd.join(" ") + " M330 280 L330 344", SP * 0.45);
  S(h2, rect(316, 270, 344, 276), SP * 0.6);
  text(h2, 330, 273, "\u4F0A \u85E4", 4.6, { weight: 700 });
  [[298, "pine"], [360, "asagao"]].forEach(([x, kind]) => {
    S(h2, `M${x - 5} 336 L${x + 5} 336 L${x + 4} ${BASE} L${x - 4} ${BASE}Z`, SP * 0.7);
    if (kind === "pine") {
      P(h2, `M${x} 336 Q${x - 3} 330 ${x + 1} 325 Q${x + 4} 321 ${x - 1} 316 M${x + 1} 325 Q${x + 5} 324 ${x + 7} 321`, SP * 0.8);
      [[x - 4, 324, 5.2], [x + 6, 319.5, 4], [x - 1, 314, 4.4]].forEach(([px, py, r]) => {
        S(h2, `M${px - r} ${py} Q${px - r * 0.8} ${py - 2.6} ${px - r * 0.3} ${py - 2.2} Q${px} ${py - 3.4} ${px + r * 0.4} ${py - 2.4} Q${px + r} ${py - 2.2} ${px + r} ${py} Q${px} ${py + 1} ${px - r} ${py}Z`, SP * 0.6);
        P(h2, Array.from({ length: 4 }, (_, k) => `M${f(px - r * 0.6 + k * r * 0.4)} ${py - 0.5} l0.6 -1.4`).join(" "), SP * 0.35);
      });
    } else {
      P(h2, `M${x - 2} 336 L${x - 2} 300 M${x + 2} 336 L${x + 2} 300 M${x - 3} 312 L${x + 3} 312 M${x - 3} 324 L${x + 3} 324`, SP * 0.5);
      P(h2, `M${x} 334 q-4 -8 1 -14 q4 -6 -1 -12 q-3 -4 1 -8`, SP * 0.5);
      [[x - 3, 316], [x + 3, 306], [x - 2, 326]].forEach(([fx, fy]) => S(h2, oval(fx, fy, 2.2, 1.8), SP * 0.5));
    }
  });
  const furinG = g(h2);
  const h3 = g(hg);
  S(h3, rect(496, 224, 690, 256));
  roof(h3, { x0: 476, x1: 710, eave: 228, ridge: 196, inset: 24 });
  mushiko(h3, 520, 232, 668, 250);
  S(h3, rect(486, 264, 700, BASE));
  roof(h3, { x0: 478, x1: 708, eave: 268, ridge: 256, inset: 5, tile: 5, sori: 1.6, oni: false });
  windows.push(pane(h3, glow2, 492, 272, 614, 330, { thr: 0.02, lateOff: 0.94 }));
  P(h3, "M496 308 L610 308", SP * 0.55);
  const tags = ["\u3060\u3093\u3054", "\u7518\u9152", "\u62B9\u8336", "\u304A\u3057\u308B\u3053", "\u8349\u9905"];
  tags.forEach((s, i) => {
    const x = 506 + i * 22;
    P(h3, `M${x} 283 L${x} 285.5`, SP * 0.4);
    S(h3, rect(x - 5, 285.5, x + 5, 307), SP * 0.6);
    text(h3, x, 296.2, s, 4.6, { vertical: true, weight: 700 });
  });
  S(h3, rect(490, 318, 616, 324), SP * 0.9);
  P(h3, "M494 324 L494 344 M612 324 L612 344", SP * 0.7);
  [528, 574].forEach((x) => {
    S(h3, `M${x - 9} 318 Q${x} 321 ${x + 9} 318 Z`, SP * 0.6);
    P(h3, `M${x - 7} 315 L${x + 8} 307`, SP * 0.6);
    [0, 1, 2].forEach((k) => S(h3, oval(x - 4 + k * 4.4, 313.5 - k * 2.4, 2.3, 2.3), SP * 0.6));
  });
  const sudare = g(h3);
  S(sudare, rect(490, 270, 616, 282), SP * 0.7);
  P(sudare, Array.from({ length: 5 }, (_, i) => `M490 ${272 + i * 2} L616 ${272 + i * 2}`).join(" ") + " M520 268 L520 284 M586 268 L586 284", SP * 0.35);
  S(sudare, `M488 268.5 a2.5 2.5 0 0 0 0 5 L618 273.5 a2.5 2.5 0 0 0 0 -5Z`, SP * 0.7);
  S(h3, rect(620, 270, 694, BASE), SP * 0.9);
  windows.push(pane(h3, glow2, 622, 272, 692, BASE - 1, { thr: 0.02, lateOff: 0.95 }));
  norens.push(noren(h3, 624, 690, 271, 24, 4, "\u8336", { open: [0.31, 0.9] }));
  lanterns.push(chochin(h3, glow2, 498, 268, { r: 6.4, h: 15, label: "\u8336", red: true }));
  lanterns.push(chochin(h3, glow2, 696, 268, { r: 6.4, h: 15, label: "\u8336", red: true }));
  const out = g(front2);
  S(out, `M586 351 L586 296 M589 351 L589 296`, SP * 0.6);
  P(out, "M587.5 352 L587.5 262", SP * 0.9);
  let rimD = "M536 273 Q548 256 587.5 252 Q627 256 639 273";
  for (let i = 12; i > 0; i--) {
    const xa = lerp(536, 639, i / 12), xb = lerp(536, 639, (i - 1) / 12);
    rimD += ` Q${f((xa + xb) / 2)} 276.4 ${f(xb)} 273`;
  }
  const parasol = el("path", { d: rimD + "Z", fill: rgb(RED), stroke: "currentColor", "stroke-width": SP * 0.8 }, out);
  P(out, Array.from({ length: 13 }, (_, i) => `M587.5 252.6 L${f(lerp(538, 637, i / 12))} 272.4`).join(" "), SP * 0.35);
  S(out, oval(587.5, 252, 3.2, 1.6), SP * 0.6);
  const benchTop = el("path", { d: rect(516, 330, 600, 336), fill: rgb(RED), stroke: "currentColor", "stroke-width": SP * 0.8 }, out);
  S(out, rect(514, 336, 602, 339), SP * 0.7);
  P(out, "M520 339 L520 352 M596 339 L596 352 M522 339 L522 352 M594 339 L594 352 M520 348 L596 348", SP * 0.7);
  S(out, "M584 330 L585 325 L591 325 L592 330Z", SP * 0.6);
  const h4 = g(hg);
  const chim = g(back2);
  S(chim, "M893 252 L895 72 L907 72 L909 252Z", SP);
  P(chim, "M894.3 100 L907.7 100 M894 130 L908 130 M893.7 170 L908.3 170 M893.4 210 L908.6 210", SP * 0.55);
  S(chim, rect(892, 66, 910, 72), SP * 0.9);
  text(chim, 901, 150, "\u3086", 9, { weight: 800 });
  S(h4, rect(708, 252, 944, BASE));
  roof(h4, { x0: 700, x1: 952, eave: 256, ridge: 214, inset: 44 });
  S(h4, "M766 262 Q780 262 790 250 Q806 226 826 222 Q846 226 862 250 Q872 262 886 262 L882 268 Q870 268 860 258 Q846 236 826 232 Q806 236 792 258 Q782 268 770 268Z", SP);
  P(h4, "M790 252 Q806 230 826 226 Q846 230 862 252", SP * 0.5);
  S(h4, "M821 222 Q826 214 831 222Z", SP * 0.7);
  P(h4, "M800 262 L800 344 M852 262 L852 344", SP);
  windows.push(pane(h4, glow2, 803, 266, 849, BASE - 1, { thr: 0, lateOff: 9 }));
  norens.push(noren(h4, 804, 848, 266, 30, 2, "\u3086", { open: [0.6, 1.08], red: false }));
  windows.push(pane(h4, glow2, 716, 266, 774, 292, { thr: 0.05, lateOff: 9 }));
  windows.push(pane(h4, glow2, 878, 266, 936, 292, { thr: 0.05, lateOff: 9 }));
  [[716, 774], [878, 936]].forEach(([a, b]) => shojiGrid(h4, a, 266, b, 292, 6, 2));
  S(h4, rect(714, 300, 734, 344), SP * 0.9);
  text(h4, 724, 322, "\u677E\u306E\u6E6F", 9, { vertical: true, weight: 800 });
  const ws = [];
  for (let x = 740; x < 800; x += 4) ws.push(`M${x} 304 L${x} 344`);
  for (let x = 856; x < 940; x += 4) ws.push(`M${x} 304 L${x} 344`);
  P(h4, ws.join(" ") + " M738 304 L800 304 M852 304 L940 304", SP * 0.5);
  const pail = (x, y) => {
    const n = el("path", { d: `M${x - 6} ${y} L${x + 6} ${y} L${x + 5} ${y + 9} L${x - 5} ${y + 9}Z`, fill: "#e9c45a", stroke: "currentColor", "stroke-width": SP * 0.7 }, h4);
    P(h4, `M${x - 5.6} ${y + 2.4} L${x + 5.6} ${y + 2.4}`, SP * 0.4);
    return n;
  };
  const pails = [pail(902, 335), pail(915, 335), pail(928, 335), pail(908.5, 326), pail(921.5, 326), pail(915, 317)];
  lanterns.push(chochin(h4, glow2, 790, 262, { r: 5.6, h: 13, label: "\u3086" }));
  lanterns.push(chochin(h4, glow2, 862, 262, { r: 5.6, h: 13, label: "\u3086" }));
  const pole = g(front2);
  S(pole, "M465 352 L466.5 98 L470.5 98 L472 352Z", SP * 0.9);
  P(pole, "M466 140 L471 140 M466 200 L471 200 M466 260 L471 260 M466 320 L471 320", SP * 0.5);
  S(pole, rect(446, 110, 490, 114), SP * 0.8);
  [450, 458, 478, 486].forEach((x) => S(pole, `M${x - 1.6} 110 L${x + 1.6} 110 L${x + 1.2} 105 L${x - 1.2} 105Z`, SP * 0.5));
  S(pole, "M472 140 Q480 140 480 146 L480 170 Q480 176 472 176Z", SP * 0.8);
  P(pole, "M472 150 L479 150 M472 160 L479 160", SP * 0.45);
  P(pole, "M466 226 Q452 222 446 230", SP * 0.8);
  S(pole, "M439 230 L453 230 L450 236 L442 236Z", SP * 0.8);
  const streetLamp = el("ellipse", { cx: 446, cy: 237, rx: 3, ry: 1.6, fill: PAPER, stroke: "currentColor", "stroke-width": SP * 0.5 }, pole);
  const lampCone = el("path", { d: "M441 237 L451 237 L496 352 L396 352Z", fill: "url(#v-cone)", opacity: 0 }, glow2);
  const cone = el("linearGradient", { id: "v-cone", x1: 0, y1: 0, x2: 0, y2: 1 }, defs2);
  el("stop", { offset: 0, "stop-color": "#ffe2a8", "stop-opacity": 0.5 }, cone);
  el("stop", { offset: 1, "stop-color": "#ffe2a8", "stop-opacity": 0.06 }, cone);
  const lampGlow = el("circle", { cx: 446, cy: 237, r: 34, fill: "url(#v-warmglow)", opacity: 0 }, glow2);
  const wireY = (x) => {
    if (x >= 488) {
      const u2 = (x - 488) / (970 - 488);
      return 112 + (108 - 112) * u2 + 26 * 4 * u2 * (1 - u2);
    }
    const u = (446 - x) / (446 + 10);
    return 112 + (104 - 112) * u + 22 * 4 * u * (1 - u);
  };
  const wires = g(back2);
  const wd = [];
  for (const [a, b, off] of [[488, 970, 0], [446, -10, 0], [488, 970, 7], [446, -10, 7]]) {
    const pts = [];
    for (let k = 0; k <= 30; k++) {
      const x = lerp(a, b, k / 30);
      pts.push([x, wireY(x) + off * (1 + 0.3 * Math.sin(k))]);
    }
    wd.push("M" + pts.map(pt).join("L"));
  }
  P(wires, wd.join(" "), SP * 0.5);
  const street2 = g(front2);
  P(street2, `M0 ${BASE} L960 ${BASE}`, SP);
  const cracks = [];
  for (let i = 0; i < 34; i++) {
    const x = srnd(0, 960), y = srnd(350, 380);
    cracks.push(`M${f(x)} ${f(y)} l${f(srnd(6, 16))} ${f(srnd(-0.4, 0.4))}`);
  }
  P(street2, cracks.join(" "), SP * 0.45);
  const gut = [];
  for (let x = 0; x < 960; x += srnd(16, 26)) gut.push(`M${f(x)} ${BASE} L${f(x)} ${BASE + 4}`);
  P(street2, `M0 ${BASE + 4} L960 ${BASE + 4} ` + gut.join(" "), SP * 0.5);
  const furin = (() => {
    const x = 412, y = 207;
    const grp = g(furinG);
    const cord = pen(grp, SP * 0.45), bell = el("path", { fill: "#e8f2f4", stroke: "currentColor", "stroke-width": SP * 0.7 }, grp);
    const clap = pen(grp, SP * 0.45), strip = el("path", { fill: PAPER, stroke: "currentColor", "stroke-width": SP * 0.55 }, grp);
    const rings = pen(grp, SP * 0.5);
    let a = 0, v = 0, sa = 0, sv = 0, ring = 0;
    return {
      x,
      y,
      draw(t, dt, wind2) {
        v += (-a * 14 + wind2 * 0.9 + wobble(t * 0.7) * 0.4 - v * 1.4) * dt;
        a += v * dt;
        sv += (-(sa - a * 1.6) * 9 + wind2 * 2.2 + Math.sin(t * 2.3) * 0.6 - sv * 1.6) * dt;
        sa += sv * dt;
        ring = Math.max(0, ring - dt * 0.9);
        const bx = x + Math.sin(a) * 6, by = y + Math.cos(a) * 6;
        cord.setAttribute("d", `M${x} ${y - 3} L${f(bx)} ${f(by)}`);
        bell.setAttribute("d", `M${f(bx - 4)} ${f(by + 5)} Q${f(bx - 4.2)} ${f(by - 0.6)} ${f(bx)} ${f(by - 0.6)} Q${f(bx + 4.2)} ${f(by - 0.6)} ${f(bx + 4)} ${f(by + 5)}Z`);
        const cx = bx + Math.sin(sa) * 4, cy = by + 5 + Math.cos(sa) * 4;
        clap.setAttribute("d", `M${f(bx)} ${f(by)} L${f(cx)} ${f(cy)} M${f(cx - 0.8)} ${f(cy)} l1.6 0`);
        const sx = cx + Math.sin(sa) * 9, sy = cy + Math.cos(sa) * 9;
        strip.setAttribute("d", `M${f(cx - 1.6)} ${f(cy + 1)} L${f(cx + 1.6)} ${f(cy + 1)} L${f(sx + 1.6)} ${f(sy)} L${f(sx - 1.6)} ${f(sy)}Z`);
        rings.setAttribute("d", ring > 0.02 ? [7, 11].map((r) => `M${f(bx - r * 0.7)} ${f(by - r * 0.1 - 4)} Q${f(bx)} ${f(by - r - 4)} ${f(bx + r * 0.7)} ${f(by - r * 0.1 - 4)}`).join(" ") : "");
        rings.setAttribute("opacity", f(ring));
      },
      poke() {
        v += 2.4;
        sv += 6;
        ring = 1;
      },
      ring() {
        ring = 1;
      },
      get swing() {
        return sv;
      }
    };
  })();
  const shoji = (() => {
    let s = -1;
    return {
      hit: rect(260, 210, 320, 252),
      poke() {
        if (s < 0) s = 0;
      },
      draw(t, dt, P_) {
        let open = 0;
        if (s >= 0) {
          s += dt;
          open = s < 0.6 ? ease(s / 0.6) : s < 4.4 ? 1 : 1 - ease((s - 4.4) / 0.6);
          if (s > 5) s = -1;
        }
        slide.setAttribute("transform", `translate(${f(-open * 27.5)} 0)`);
        interior.setAttribute("opacity", f(open > 1e-3 ? 1 : 0));
        const lit = shojiWin.lit;
        room.setAttribute("fill", rgb(mix(hex("#4a3a2c"), hex("#f0a85a"), lit * 0.85)));
        const lean = ease(clamp((s - 0.4) / 0.6, 0, 1)) * (1 - ease(clamp((s - 4) / 0.5, 0, 1)));
        person.setAttribute("transform", `translate(${f((1 - lean) * 22)} 0)`);
        const wv = Math.sin(Math.max(0, s - 1) * 9) * 0.5 * lean;
        const sh = [297, 238], el2 = [293, 231], hand = [293 + Math.sin(wv) * 5, 222 - Math.cos(wv) * 2];
        waveArm.draw([sh, el2, hand], [0.2, 0.2]);
        slidePane.setAttribute("fill", rgb(mix(P_.paper, WARM, lit * 0.9)));
      }
    };
  })();
  return {
    windows,
    lanterns,
    norens,
    furin,
    shoji,
    blossoms,
    canopy,
    pails,
    parasol,
    benchTop,
    alleyLamp,
    bench: { x0: 518, x1: 598, y: 330 },
    chimney: [901, 64],
    wireY,
    lamp: { node: streetLamp, cone: lampCone, glow: lampGlow, x: 446, y: 237 },
    applyRed(P_) {
      const c = rgb(mix(RED, RED_NIGHT, P_.inkT));
      parasol.setAttribute("fill", c);
      benchTop.setAttribute("fill", c);
      pails.forEach((p) => p.setAttribute("fill", rgb(mix(hex("#e9c45a"), hex("#6d6240"), P_.inkT))));
    }
  };
}

// canal.ts
var WARM2 = hex("#ffcf7e");
function buildCanal({ ground: ground2, canalL: canalL2, willowL: willowL2, glow: glow2 }, defs2) {
  el("path", { d: `M-10 ${BASE} L${W + 10} ${BASE} L${W + 10} ${EDGE} L-10 ${EDGE}Z`, fill: PAPER }, ground2);
  const wall = el("g", {}, canalL2);
  shape(wall, SP).setAttribute("d", `M-10 ${EDGE} L${W + 10} ${EDGE} L${W + 10} ${WATER} L-10 ${WATER}Z`);
  const d = [`M-10 ${EDGE + 5} L${W + 10} ${EDGE + 5}`, `M-10 ${EDGE + 10.5} Q${W / 2} ${EDGE + 10} ${W + 10} ${EDGE + 10.6}`];
  for (let x = srnd(0, 20); x < W; x += srnd(28, 44)) d.push(`M${f(x)} ${EDGE} l0.4 5`);
  [[EDGE + 5, EDGE + 10.5, 0], [EDGE + 10.5, WATER, 8]].forEach(([y0, y1, o]) => {
    for (let x = srnd(0, 14) + o; x < W; x += srnd(12, 24)) d.push(`M${f(x)} ${f(y0 + 0.4)} Q${f(x + srnd(-1, 1))} ${f((y0 + y1) / 2)} ${f(x + srnd(-0.6, 0.6))} ${f(y1 - 0.4)}`);
  });
  for (let i = 0; i < 40; i++) {
    const x = srnd(4, W - 4), y = srnd(EDGE + 6, WATER - 2);
    d.push(`M${f(x)} ${f(y)} l${f(srnd(1, 2.6))} ${f(srnd(-0.3, 0.3))}`);
  }
  pen(wall, SP * 0.5).setAttribute("d", d.join(" "));
  const moss = [];
  for (let i = 0; i < 26; i++) {
    const x = srnd(0, W);
    moss.push(`M${f(x)} ${EDGE + 5} q-1 3 0.4 5 M${f(x + 2)} ${EDGE + 5} q1 2.6 -0.2 4.4`);
  }
  pen(wall, SP * 0.45).setAttribute("d", moss.join(" "));
  const water = el("path", { d: `M-10 ${WATER} L${W + 10} ${WATER} L${W + 10} ${H + 10} L-10 ${H + 10}Z` }, canalL2);
  pen(canalL2, SP * 0.8).setAttribute("d", `M-10 ${WATER} L${W + 10} ${WATER}`);
  const reflG = el("g", {}, canalL2);
  const ripG = el("g", {}, canalL2);
  const lines = Array.from({ length: 46 }, (_, i) => ({ x: rnd(-40, W), y: WATER + 5 + i % 9 * 8.4 + rnd(-2, 2), len: rnd(10, 34), v: rnd(4, 9), n: pen(ripG, SP * 0.5) }));
  const rings = [];
  const ringG = el("g", {}, canalL2);
  const ring = (x, y, n = 1, big = 1) => {
    for (let i = 0; i < n; i++) rings.push({ x, y, t: -i * 0.22, big, n: el("ellipse", { fill: "none", stroke: "currentColor", "stroke-width": SP * 0.55 }, ringG) });
  };
  const refl = [];
  const addRefl = (src, x, w, warm = true) => {
    const strokes = Array.from({ length: 9 }, (_, k) => el("path", { stroke: warm ? "#ffcf7e" : "#f3ecd6", "stroke-width": 1.4 - k * 0.08, "stroke-linecap": "round", fill: "none" }, reflG));
    refl.push({ src, x, w, strokes, warm });
  };
  const floating = [];
  const floatG = el("g", {}, canalL2);
  const koiG = el("g", { opacity: 0 }, canalL2);
  const koiBody = el("path", { fill: "#f4ede0", stroke: "currentColor", "stroke-width": SP * 0.8 }, koiG);
  const koiSpots = el("path", { fill: "#d4552f" }, koiG);
  const koiFin = shape(koiG, SP * 0.6), koiEye = el("circle", { r: 0.9, fill: "currentColor" }, koiG);
  let koi = null;
  const jump = (x) => {
    if (koi) return;
    koi = { x: clamp(x, 60, W - 60), t: 0, dir: Math.random() < 0.5 ? -1 : 1 };
    ring(koi.x, WATER + 14, 2);
  };
  const willow = el("g", {}, willowL2);
  shape(willow, SP).setAttribute("d", "M14 384 Q20 340 16 300 Q12 262 34 236 Q46 222 40 206 L46 206 Q54 226 42 244 Q24 270 28 306 Q32 344 28 384Z");
  pen(willow, SP * 0.8).setAttribute("d", "M36 238 Q66 214 104 212 M30 260 Q60 246 86 252 M40 222 Q22 204 -4 202 M42 214 Q56 196 82 190");
  pen(willow, SP * 0.45).setAttribute("d", "M20 330 q3 -6 0 -12 M24 290 q-3 -6 1 -12 M18 360 q2 -4 -1 -8");
  const strands = [];
  const roots = [[104, 212], [86, 252], [-4, 202], [82, 190], [64, 216], [52, 252], [20, 206], [70, 196], [94, 230], [40, 226], [6, 214]];
  roots.forEach(([rx, ry], i) => {
    const n = 4;
    for (let k = 0; k < n; k++) {
      const x = rx + srnd(-10, 10), y = ry + srnd(-3, 5), len = srnd(80, 150);
      strands.push({ x, y, len, ph: srnd(0, 6), stiff: srnd(0.7, 1.3), n: pen(willow, SP * 0.5), leaves: pen(willow, SP * 0.45), a: 0, v: 0 });
    }
  });
  let willowKick = 0;
  const flies = Array.from({ length: 22 }, (_, i) => ({
    cx: srnd(20, W - 20),
    cy: srnd(300, 460),
    ph: srnd(0, 50),
    sp: srnd(0.4, 0.9),
    blink: srnd(2, 5),
    n: el("circle", { r: 5.5, fill: "url(#v-fly)" }, glow2),
    dot: el("circle", { r: 0.9, fill: "#f1ffb4" }, glow2)
  }));
  const fly = el("radialGradient", { id: "v-fly" }, defs2);
  el("stop", { offset: 0, "stop-color": "#e9ff9a", "stop-opacity": 0.9 }, fly);
  el("stop", { offset: 1, "stop-color": "#c8ff6a", "stop-opacity": 0 }, fly);
  const moths = Array.from({ length: 4 }, () => ({ ph: rnd(0, 6), r: rnd(5, 12), sp: rnd(3, 6), n: el("circle", { r: 0.7, fill: "#fff4d2" }, glow2) }));
  return {
    ring,
    jump,
    addRefl,
    floatPetal(p) {
      floating.push({ x: p.x, y: WATER + rnd(3, 40), r: p.r, life: 0, n: el("ellipse", { rx: 1.5, ry: 0.7, fill: "#f6dfe4", stroke: "currentColor", "stroke-width": SP * 0.4 }, floatG) });
    },
    poke(x, y) {
      if (y > WATER) {
        if (Math.random() < 0.7 || !koi) jump(x);
        ring(x, y, 3);
      }
    },
    willowPoke() {
      willowKick = 1;
      strands.forEach((s) => s.v += rnd(1.5, 3));
    },
    draw(t, dt, P3, wind2, lights, tau2, lampOn, moonX) {
      water.setAttribute("fill", rgb(mix(P3.paper, P3.inkT > 0.5 ? hex("#0f1730") : hex("#bfd0d8"), P3.inkT > 0.5 ? 0.45 : 0.32)));
      lines.forEach((l) => {
        l.x += (l.v + wind2 * 4) * dt;
        if (l.x > W + 20) l.x = -40;
        if (l.x < -50) l.x = W + 10;
        const y = l.y + Math.sin(t * 1.3 + l.x * 0.04) * 0.7;
        l.n.setAttribute("d", `M${f(l.x)} ${f(y)} Q${f(l.x + l.len / 2)} ${f(y - 1.2)} ${f(l.x + l.len)} ${f(y)}`);
      });
      if (Math.random() < dt * 0.5) ring(rnd(40, W - 40), rnd(WATER + 10, H - 10), 1, 0.6);
      if (P3.night < 0.5 && Math.random() < dt * 0.03) jump(rnd(120, W - 120));
      for (let i = rings.length - 1; i >= 0; i--) {
        const r = rings[i];
        r.t += dt;
        if (r.t < 0) {
          r.n.setAttribute("opacity", 0);
          continue;
        }
        r.n.setAttribute("cx", f(r.x));
        r.n.setAttribute("cy", f(r.y));
        r.n.setAttribute("rx", f((2 + r.t * 12) * r.big));
        r.n.setAttribute("ry", f((0.6 + r.t * 2.2) * r.big));
        r.n.setAttribute("opacity", f(Math.max(0, 1 - r.t / 1.6)));
        if (r.t > 1.6) {
          r.n.remove();
          rings.splice(i, 1);
        }
      }
      refl.forEach((r) => {
        const lit = r.src();
        r.strokes.forEach((s, k) => {
          if (lit < 0.02) {
            s.setAttribute("d", "");
            return;
          }
          const y = WATER + 6 + k * 6.5, jit = Math.sin(t * 2.2 + k * 1.7 + r.x * 0.1) * (2 + k * 0.5);
          const w = r.w * (1 - k * 0.07) * (0.7 + 0.3 * Math.sin(t * 1.7 + k));
          s.setAttribute("d", `M${f(r.x - w / 2 + jit)} ${f(y)} L${f(r.x + w / 2 + jit)} ${f(y)}`);
          s.setAttribute("opacity", f(lit * (0.75 - k * 0.07)));
        });
      });
      for (let i = floating.length - 1; i >= 0; i--) {
        const p = floating[i];
        p.life += dt;
        p.x += (6 + wind2 * 3) * dt;
        p.r += dt * 0.3;
        p.n.setAttribute("cx", f(p.x));
        p.n.setAttribute("cy", f(p.y + Math.sin(t + p.x * 0.05) * 0.6));
        p.n.setAttribute("transform", `rotate(${f(p.r * 40)} ${f(p.x)} ${f(p.y)})`);
        p.n.setAttribute("opacity", f(Math.min(1, (12 - p.life) / 2)));
        if (p.life > 12 || p.x > W + 10) {
          p.n.remove();
          floating.splice(i, 1);
        }
      }
      if (koi) {
        koi.t += dt;
        const u = koi.t / 1.1;
        if (u >= 1) {
          ring(koi.x + koi.dir * 30, WATER + 14, 3, 1.2);
          koi = null;
          koiG.setAttribute("opacity", 0);
        } else {
          const x = koi.x + koi.dir * 30 * u, y = WATER + 14 - 26 * Math.sin(Math.PI * u);
          const ang = Math.atan2(-26 * Math.PI * Math.cos(Math.PI * u), 30) * 57.3;
          const bend = Math.sin(u * 18) * 2;
          koiG.setAttribute("opacity", 1);
          koiG.setAttribute("transform", `translate(${f(x)} ${f(y)}) rotate(${f(ang * koi.dir)}) scale(${koi.dir} 1)`);
          koiBody.setAttribute("d", `M-11 0 Q-4 -5.4 6 -3.6 Q11 -2 12 0 Q11 2 6 3.6 Q-4 5.4 -11 0Z M-11 0 L-17 ${f(-4.5 + bend)} Q-15 0 -17 ${f(4.5 + bend)}Z`);
          koiSpots.setAttribute("d", `${oval(2, -1.5, 3.2, 1.8)} ${oval(-5, 1, 2.6, 1.6)} ${oval(8.6, -0.8, 1.6, 1.2)}`);
          koiFin.setAttribute("d", `M-1 3 L-4 7.5 L2 4Z`);
          koiEye.setAttribute("cx", 9);
          koiEye.setAttribute("cy", -0.8);
          if (u > 0.08 && u < 0.12 && !koi.dripped) {
            koi.dripped = true;
            ring(koi.x, WATER + 12, 2, 0.9);
          }
        }
      }
      willowKick = Math.max(0, willowKick - dt);
      strands.forEach((s) => {
        s.v += (-s.a * 3.2 * s.stiff + wind2 * 0.32 + wobble(t * 0.6 + s.ph) * 0.12 - s.v * 0.9) * dt;
        s.a += s.v * dt;
        const pts = [];
        for (let k = 0; k <= 10; k++) {
          const u = k / 10, sway = s.a * s.len * u * u * 0.9 + Math.sin(t * 1.6 + s.ph + u * 3) * 1.2 * u;
          pts.push([s.x + sway + u * 2, s.y + s.len * u - Math.abs(s.a) * s.len * u * u * 0.12]);
        }
        s.n.setAttribute("d", "M" + pts.map(pt).join("L"));
        s.leaves.setAttribute("d", pts.slice(2).map(([x, y], k) => `M${f(x)} ${f(y)} l${k % 2 ? 2 : -2} 2.4`).join(" "));
      });
      flies.forEach((fl, i) => {
        const tt = t * fl.sp + fl.ph;
        const x = fl.cx + Math.sin(tt * 0.7) * 30 + Math.sin(tt * 1.9) * 8, y = fl.cy + Math.sin(tt * 0.9 + 1) * 16 + Math.cos(tt * 2.3) * 5;
        const b = Math.pow(Math.max(0, Math.sin(t * fl.blink + fl.ph)), 3);
        fl.n.setAttribute("cx", f(x));
        fl.n.setAttribute("cy", f(y));
        fl.dot.setAttribute("cx", f(x));
        fl.dot.setAttribute("cy", f(y));
        fl.n.setAttribute("opacity", f(P3.night * b));
        fl.dot.setAttribute("opacity", f(P3.night * (0.3 + 0.7 * b)));
      });
      moths.forEach((m, i) => {
        const a = t * m.sp + m.ph, x = 446 + Math.cos(a) * m.r + Math.sin(a * 2.7) * 3, y = 240 + Math.sin(a * 1.3) * m.r * 0.6;
        m.n.setAttribute("cx", f(x));
        m.n.setAttribute("cy", f(y));
        m.n.setAttribute("opacity", f(lampOn * (0.6 + 0.4 * Math.sin(a * 5))));
      });
    }
  };
}

// people.ts
var RAD = Math.PI / 180;
var place = (g, X, Y, dir, s = FS) => g.setAttribute("transform", `translate(${f(X)} ${f(Y)}) scale(${f(dir * s)} ${f(s)}) translate(-40 -120)`);
var world = (X, Y, dir, lx, ly, s = FS) => [X + dir * s * (lx - 40), Y + s * (ly - 120)];
var fillOf = (c, P3, k = 0.55) => rgb(mix(hex(c), mix(hex(c), [12, 16, 30], 0.6), P3.inkT * k));
var solid = (lb, c = "currentColor") => {
  const n = lb.g.querySelector("path");
  n.classList.remove("pp");
  n.setAttribute("fill", c);
  return lb;
};
var paintPath = (g, c, w = PEN) => el("path", { fill: c, stroke: "currentColor", "stroke-width": w, "stroke-linejoin": "round", "stroke-linecap": "round" }, g);
function createKimono(parent, glow2, { dir = 1, x, y, lantern = false }) {
  const g = el("g", { style: "cursor:pointer" }, parent);
  const T = 1, DUTY = 0.62, S2 = 24, LEG = 45.2;
  const speed = S2 / (DUTY * T) * FS;
  const colours = pick([["#34507a", "#d3a24c"], ["#7a4766", "#cfd3c2"], ["#4f6b55", "#c58a4a"], ["#8a5a3c", "#2f3f5f"]]);
  const [kimonoC, obiC] = colours;
  const parasolC = pick(["#2f4d5c", "#7b2f2f", "#2f3d2f"]);
  const feet = [0, 1].map(() => ({ tabi: shape(g, PEN * 0.75), geta: blot(g) }));
  const farSleeve = paintPath(g, kimonoC);
  const lower = paintPath(g, kimonoC);
  const okumi = pen(g, PEN * 0.6), crease = pen(g, PEN * 0.45);
  const patternLow = el("path", { fill: "none", stroke: "#f2ead8", "stroke-width": PEN * 0.5 }, g);
  const upperG = el("g", {}, g);
  const upper = paintPath(upperG, kimonoC);
  const pattern = el("path", { fill: "none", stroke: "#f2ead8", "stroke-width": PEN * 0.5 }, upperG);
  const obi = paintPath(upperG, obiC), taiko = paintPath(upperG, obiC), cord = el("path", { stroke: "#b3412d", "stroke-width": 1.1, fill: "none" }, upperG);
  const collar = shape(upperG, PEN * 0.8);
  const neck = limb(upperG, 3.2);
  const head = el("ellipse", { cx: 41, cy: 32, rx: 4.2, ry: 5.1, fill: PAPER, stroke: "currentColor", "stroke-width": PEN }, upperG);
  const hair = blot(upperG);
  const pin = pen(upperG, PEN * 0.7), pinBall = el("circle", { r: 1.1, fill: "#c9a24a", stroke: "currentColor", "stroke-width": 0.5 }, upperG);
  const sleeve = paintPath(upperG, kimonoC);
  const hand = el("ellipse", { rx: 1.8, ry: 1.5, fill: PAPER, stroke: "currentColor", "stroke-width": PEN * 0.7 }, upperG);
  const prop = el("g", {}, upperG);
  const pole = pen(prop, PEN * 0.9);
  const canopyG = el("g", {}, prop);
  const canopy = paintPath(canopyG, parasolC, PEN * 0.9), ring_ = el("path", { fill: "none", stroke: "#f1e7d0", "stroke-width": 2.4 }, canopyG), ribs = pen(canopyG, PEN * 0.4), cap = blot(canopyG);
  const lanternG = el("g", {}, prop);
  const lBody = el("path", { stroke: "currentColor", "stroke-width": PEN * 0.8 }, lanternG), lCaps = blot(lanternG), lRibs = pen(lanternG, PEN * 0.4);
  const lGlow = el("circle", { r: 22, fill: "url(#v-warmglow)", opacity: 0 }, glow2);
  const mj = (s) => s * s * s * (10 - 15 * s + 6 * s * s);
  const foot = (u) => {
    u = (u % 1 + 1) % 1;
    if (u < DUTY) {
      const x2 = 40 + S2 / 2 - S2 * u / DUTY;
      const heel = smooth(DUTY - 0.14, DUTY, u);
      const th = 15 * heel * RAD, px = x2 + 4.2, py = 120;
      const ox = -4.2, oy = -4;
      return { a: [px + ox * Math.cos(th) - oy * Math.sin(th), py + ox * Math.sin(th) + oy * Math.cos(th)], pitch: 15 * heel, stance: true };
    }
    const s = (u - DUTY) / (1 - DUTY);
    return { a: [40 - S2 / 2 + S2 * mj(s), 116 - 3.4 * Math.pow(Math.sin(Math.PI * s), 1.2)], pitch: 15 * Math.pow(1 - smooth(0, 0.55, s), 1.4), stance: false };
  };
  const getaPath = (ank, pitch) => {
    const r = pitch * RAD, c = Math.cos(r), s = Math.sin(r);
    const R = (px, py) => pt([ank[0] + px * c - py * s, ank[1] + px * s + py * c]);
    return {
      geta: `M${R(-4.4, 0.2)} L${R(5.2, 0.2)} L${R(5.2, 1.5)} L${R(3.8, 1.5)} L${R(3.8, 4)} L${R(2.4, 4)} L${R(2.4, 1.5)} L${R(-1.4, 1.5)} L${R(-1.4, 4)} L${R(-2.8, 4)} L${R(-2.8, 1.5)} L${R(-4.4, 1.5)}Z`,
      tabi: `M${R(-3.4, 0.2)} Q${R(-3.7, -5)} ${R(-0.7, -5.6)} L${R(1.6, -5)} Q${R(4.7, -3.4)} ${R(4.8, 0.2)}Z`
    };
  };
  let ph = rnd(0, 1), hipS = 70.8, slv = 0, slvV = 0, tiltS = 0, tiltV = 0, lanA = 0, lanV = 0, bowT = -1, stop = 0;
  return {
    g,
    x,
    y,
    dir,
    speed,
    done: false,
    poke() {
      if (bowT < 0) bowT = 0;
    },
    draw(t, dt, P3) {
      let bow = 0;
      if (bowT >= 0) {
        bowT += dt;
        bow = bowT < 0.7 ? 0 : bowT < 1.15 ? ease((bowT - 0.7) / 0.45) : bowT < 1.9 ? 1 : 1 - ease((bowT - 1.9) / 0.5);
        if (bowT > 2.6) bowT = -1;
      }
      stop = clamp(stop + (bowT >= 0 && bowT < 2.4 ? dt : -dt) * 2.4, 0, 1);
      const go = 1 - ease(stop);
      ph += dt / T * go;
      this.x += dir * speed * dt * go;
      if (this.x < -80 || this.x > 1040) this.done = true;
      place(g, this.x, this.y, dir);
      const F = [foot(ph), foot(ph + 0.5)];
      if (go < 1) F.forEach((fo, i) => {
        const rest = 40 + (i ? -2 : 2);
        fo.a = [lerp(rest, fo.a[0], go), lerp(116, fo.a[1], go)];
        fo.pitch *= go;
      });
      let hipY = 70.8;
      F.forEach((fo) => {
        if (fo.stance || go < 1) {
          const dx = fo.a[0] - 40;
          hipY = Math.max(hipY, fo.a[1] - Math.sqrt(Math.max(1, LEG * LEG - dx * dx)));
        }
      });
      hipS = lerp(hipS, hipY, Math.min(1, dt * 18));
      const hip = [40, hipS], b = hipS - 70.8;
      const K = F.map((fo) => joint(hip, fo.a, 23, 23, 1));
      F.forEach((fo, i) => {
        const p = getaPath(fo.a, fo.pitch);
        feet[i].geta.setAttribute("d", p.geta);
        feet[i].tabi.setAttribute("d", p.tabi);
      });
      const iF = F[0].a[0] >= F[1].a[0] ? 0 : 1, iR = 1 - iF;
      const aF = F[iF].a, aR = F[iR].a;
      const kF = K[0][0] >= K[1][0] ? K[0] : K[1], kR = K[0][0] >= K[1][0] ? K[1] : K[0];
      g.insertBefore(feet[iF].geta, farSleeve);
      g.insertBefore(feet[iF].tabi, feet[iF].geta);
      const wB = [31.8, 69 + b], wF = [47.8, 69.4 + b];
      const hemF = [Math.max(46.6, aF[0] + 4.2), 112.6], hemR = [Math.min(31.4, aR[0] - 2.4), 113];
      const kx = Math.max(kF[0] + 2.6, 47.4);
      lower.setAttribute("d", `M${pt(wB)} L${pt(wF)} C${f(48.6)} ${f(80 + b)} ${f(kx)} ${f(kF[1] - 9)} ${f(kx)} ${f(kF[1])} Q${f(kx - 0.2)} ${f((kF[1] + hemF[1]) / 2 + 2)} ${pt(hemF)} Q${f((hemF[0] + hemR[0]) / 2)} ${f(113.6)} ${pt(hemR)} Q${f(Math.min(30.8, hemR[0] + 1.6))} ${f(92 + b * 0.5)} ${pt(wB)}Z`);
      okumi.setAttribute("d", `M${f(44.4)} ${f(72 + b)} Q${f(kF[0] - 0.6)} ${f(kF[1] + 3)} ${f(Math.max(42, aF[0] + 0.8))} ${f(112.6)}`);
      crease.setAttribute("d", `M${f(kR[0] + 1.6)} ${f(kR[1] - 4)} Q${f(kR[0] + 0.4)} ${f(kR[1] + 6)} ${f(Math.max(hemR[0] + 3, aR[0] + 1.4))} ${f(112.4)}`);
      patternLow.setAttribute("d", [[36.4, 84], [41.6, 96], [36, 104], [42, 79]].map(([px, py]) => `M${px} ${f(py + b * 0.6)} a1.1 1.1 0 1 0 0.1 0`).join(" "));
      const stepPh = 4 * Math.PI * ph;
      slvV += (40 * ((-1.4 + Math.sin(stepPh - 1.1) * 0.9) * go - slv) - 6 * slvV) * dt;
      slv += slvV * dt;
      tiltV += (30 * (Math.sin(stepPh - 0.8) * 1.6 * go - tiltS) - 5 * tiltV) * dt;
      tiltS += tiltV * dt;
      farSleeve.setAttribute("d", `M${f(34)} ${f(47 + b)} Q${f(30 + slv * 0.5)} ${f(56 + b)} ${f(28.8 + slv)} ${f(74 + b)} Q${f(31 + slv)} ${f(77.6 + b)} ${f(34)} ${f(76 + b)}Z`);
      upperG.setAttribute("transform", `translate(0 ${f(b)}) rotate(${f(bow * 34 + 1.4 * go)} 40 68)`);
      upper.setAttribute("d", "M36 43 Q32 45.5 32.2 52 Q31.6 60 32 69 L47.6 69 Q48.4 56 46.6 48 Q45.4 44 43.4 43Z");
      pattern.setAttribute("d", [[36, 55], [42, 50]].map(([px, py]) => `M${px} ${py} a1.1 1.1 0 1 0 0.1 0`).join(" "));
      obi.setAttribute("d", "M31.8 59 L47.8 59.5 L47.9 69.4 L31.7 69Z");
      cord.setAttribute("d", "M31.8 64.4 L47.9 64.6");
      taiko.setAttribute("d", "M32 57.5 L25.4 58.6 Q24.4 66 25.6 75 L32 74Z");
      collar.setAttribute("d", "M37.4 43.4 L41.6 53.4 L44.8 43.6 L43 43 L41.4 49 L39.2 43.2Z");
      neck.draw([[40.6, 44], [40.8, 37]], [0.2, 0.2]);
      hair.setAttribute("d", `M36.6 31 Q35.4 23.6 41 22.6 Q46.4 22.4 46 28.6 Q43.2 25.6 39.8 27 Q37.8 28.4 36.6 31Z ${oval(35.4, 31.4, 3, 3.8)} ${oval(40.2, 20.6, 3.8, 2.3)}`);
      pin.setAttribute("d", "M42.6 21.2 L47.4 17.6");
      pinBall.setAttribute("cx", 47.6);
      pinBall.setAttribute("cy", 17.4);
      sleeve.setAttribute("d", `M43.6 46 Q49.6 49 50.4 55 L${f(50.6 + slv * 0.5)} 72 Q${f(46 + slv)} 75.6 ${f(41.6 + slv)} 72.4 L41.6 54Z`);
      if (!lantern && P3.lamp > 0.62) lantern = true;
      const night = lantern;
      const hx = 50.4, hy = night ? 57.4 : 54.6;
      hand.setAttribute("cx", hx);
      hand.setAttribute("cy", hy);
      canopyG.style.display = night ? "none" : "";
      lanternG.style.display = night ? "" : "none";
      if (!night) {
        const tilt = -14 + tiltS - bow * 10;
        const apex = [hx - 15, hy - 50];
        pole.setAttribute("d", `M${hx + 1} ${hy + 3} L${f(apex[0])} ${f(apex[1])}`);
        canopyG.setAttribute("transform", `translate(${f(apex[0])} ${f(apex[1])}) rotate(${f(tilt)})`);
        canopy.setAttribute("d", "M-27 10 Q-25 -1.6 0 -4 Q25 -1.6 27 10 Q22 8 18 9.6 Q13 7.6 9 9 Q4.6 7.4 0 8.8 Q-4.6 7.4 -9 9 Q-13 7.6 -18 9.6 Q-22 8 -27 10Z");
        ring_.setAttribute("d", "M-18.6 2.8 Q0 -3 18.6 2.8");
        ribs.setAttribute("d", Array.from({ length: 9 }, (_, k) => {
          const xx = lerp(-24, 24, k / 8);
          return `M0 -3.6 L${f(xx)} ${f(8.8 - Math.abs(xx) * 0.02)}`;
        }).join(" "));
        cap.setAttribute("d", oval(0, -4.2, 2.6, 1.4));
        lGlow.setAttribute("opacity", 0);
      } else {
        const tip = [hx + 15, hy - 9];
        pole.setAttribute("d", `M${hx - 1} ${hy + 1} Q${hx + 8} ${hy - 6} ${tip[0]} ${tip[1]}`);
        lanV += (-lanA * 22 - Math.sin(stepPh) * 2.2 * go - lanV * 2.2) * dt;
        lanA += lanV * dt;
        lanternG.setAttribute("transform", `translate(${tip[0]} ${tip[1]}) rotate(${f(lanA * 57.3)})`);
        lBody.setAttribute("d", "M-3.6 5 Q-5.4 10.5 -3.6 16 L3.6 16 Q5.4 10.5 3.6 5Z M0 0 L0 3");
        lBody.setAttribute("fill", rgb(mix(P3.paper, hex("#ffd38a"), 1)));
        lCaps.setAttribute("d", "M-2.6 3 L2.6 3 L2.6 5 L-2.6 5Z M-2.6 15.6 L2.6 15.6 L2.6 17.4 L-2.6 17.4Z");
        lRibs.setAttribute("d", "M-4.4 8 Q0 9 4.4 8 M-4.8 11 Q0 12 4.8 11 M-4.4 14 Q0 15 4.4 14");
        const [wx, wy] = world(this.x, this.y, dir, tip[0] - Math.sin(lanA) * 10, tip[1] + b + 10.5);
        lGlow.setAttribute("cx", f(wx));
        lGlow.setAttribute("cy", f(wy));
        lGlow.setAttribute("opacity", f(0.9 + 0.1 * Math.sin(t * 9)));
      }
      [lower, upper, sleeve].forEach((n) => n.setAttribute("fill", fillOf(kimonoC, P3)));
      farSleeve.setAttribute("fill", rgb(mix(hex(kimonoC), [10, 12, 20], 0.18 + P3.inkT * 0.4)));
      [obi, taiko].forEach((n) => n.setAttribute("fill", fillOf(obiC, P3)));
      canopy.setAttribute("fill", fillOf(parasolC, P3));
    },
    remove() {
      g.remove();
      lGlow.remove();
    }
  };
}
function createCyclist(parent, glow2, { dir = -1, x, y }) {
  const g = el("g", { style: "cursor:pointer" }, parent);
  const speed = 66;
  const R = 13.5, REAR = [18, 106.5], FRONT = [71, 106.5], BB = [41, 108];
  const wheels = [REAR, FRONT].map((c) => ({ c, tyre: el("circle", { cx: c[0], cy: c[1], r: R, fill: "none", stroke: "currentColor", "stroke-width": PEN * 1.1 }, g), rim: el("circle", { cx: c[0], cy: c[1], r: R - 1.6, fill: "none", stroke: "currentColor", "stroke-width": PEN * 0.45 }, g), spokes: pen(g, PEN * 0.32), hub: el("circle", { cx: c[0], cy: c[1], r: 1.4, fill: "currentColor" }, g) }));
  const farLeg = solid(limb(g, 4.2));
  const farShoe = blot(g);
  const frame = pen(g, PEN * 1.05);
  pen(g, PEN * 0.6).setAttribute("d", `M${REAR[0] - 15} ${REAR[1] - 2} Q${REAR[0]} ${REAR[1] - 18} ${REAR[0] + 14} ${REAR[1] - 5} M${FRONT[0] - 13} ${FRONT[1] - 5} Q${FRONT[0]} ${FRONT[1] - 18} ${FRONT[0] + 14} ${FRONT[1] - 3}`);
  frame.setAttribute("d", `M64 79 Q52 103 ${BB[0]} ${BB[1]} L${REAR[0]} ${REAR[1]} L31 80 L${BB[0]} ${BB[1]} M31 80 L30 74 M64 79 L66.6 89 Q68.4 97 ${FRONT[0]} ${FRONT[1]} M64 79 L62.4 70 Q58 68 54.4 69.6`);
  const guard = shape(g, PEN * 0.6);
  guard.setAttribute("d", `M${BB[0] + 3} ${BB[1] - 3.6} L${REAR[0] + 1} ${REAR[1] - 3} Q${REAR[0] - 2} ${REAR[1]} ${REAR[0] + 1} ${REAR[1] + 3} L${BB[0] + 3} ${BB[1] + 3.6} Q${BB[0] + 6.4} ${BB[1]} ${BB[0] + 3} ${BB[1] - 3.6}Z`);
  const saddle = blot(g);
  saddle.setAttribute("d", "M25 73 Q30 70.6 35.6 72.4 L34.6 75 L26 75Z");
  const basket = shape(g, PEN * 0.7);
  basket.setAttribute("d", "M66 71 L82 71 L80.6 84 L67.4 84Z");
  pen(g, PEN * 0.35).setAttribute("d", "M66.5 75 L81.6 75 M66.9 79.4 L81 79.4 M70 71 L70.6 84 M74 71 L74 84 M78 71 L77.4 84");
  const bag = el("path", { d: "M68 71 Q68.5 64 74 64 Q80 64 80 71Z", fill: "#4a3a2c", stroke: "currentColor", "stroke-width": PEN * 0.6 }, g);
  const lamp = el("path", { d: "M81.6 84 L85.4 84 L85.4 88 L81.6 88Z", fill: PAPER, stroke: "currentColor", "stroke-width": PEN * 0.6 }, g);
  const bell = el("path", { d: "M56 66.6 a1.8 1.8 0 0 1 3.6 0Z", fill: "#d8d2c0", stroke: "currentColor", "stroke-width": 0.5 }, g);
  const crank = pen(g, PEN * 0.9);
  const torso = blot(g);
  const collarB = pen(g, PEN * 0.6);
  const head = el("ellipse", { rx: 4.3, ry: 5, fill: PAPER, stroke: "currentColor", "stroke-width": PEN }, g);
  const capC = blot(g);
  const nearLeg = solid(limb(g, 4.4));
  const nearShoe = blot(g);
  const arm = solid(limb(g, 3.6));
  const handC = el("ellipse", { rx: 1.7, ry: 1.4, fill: PAPER, stroke: "currentColor", "stroke-width": PEN * 0.7 }, g);
  const rings = pen(g, PEN * 0.6);
  const beam = el("path", { fill: dir > 0 ? "url(#v-beamR)" : "url(#v-beamL)", opacity: 0 }, glow2);
  const beamGlow = el("circle", { r: 10, fill: "url(#v-warmglow)", opacity: 0 }, glow2);
  let dist = 0, ringT = -1;
  return {
    g,
    x,
    y,
    dir,
    done: false,
    kind: "bike",
    poke() {
      ringT = 0;
    },
    get ringing() {
      return ringT >= 0 && ringT < 0.8;
    },
    draw(t, dt, P3) {
      this.x += dir * speed * dt;
      dist += speed * dt / FS;
      if (this.x < -80 || this.x > 1040) this.done = true;
      place(g, this.x, this.y, dir);
      const wa = dist / R;
      wheels.forEach((w) => {
        const d = [];
        for (let k = 0; k < 8; k++) {
          const a = wa + k * Math.PI / 8;
          d.push(`M${f(w.c[0] + Math.cos(a) * (R - 1.6))} ${f(w.c[1] + Math.sin(a) * (R - 1.6))} L${f(w.c[0] - Math.cos(a) * (R - 1.6))} ${f(w.c[1] - Math.sin(a) * (R - 1.6))}`);
        }
        w.spokes.setAttribute("d", d.join(" "));
      });
      const ca = wa * 0.42, CR = 6.2;
      const pN = [BB[0] + Math.cos(ca) * CR, BB[1] + Math.sin(ca) * CR], pF = [BB[0] - Math.cos(ca) * CR, BB[1] - Math.sin(ca) * CR];
      crank.setAttribute("d", `M${pt(pF)} L${pt(pN)} M${f(pN[0] - 2)} ${f(pN[1])} l4 0 M${f(pF[0] - 2)} ${f(pF[1])} l4 0`);
      const bob = Math.sin(ca * 2) * 0.35;
      const hip = [31, 70.6 + bob];
      [[farLeg, farShoe, pF], [nearLeg, nearShoe, pN]].forEach(([L, S2, p]) => {
        const ank = [p[0] - 0.6, p[1] - 2.2];
        L.draw([hip, joint(hip, ank, 21, 21, 1), ank], [0.2, 0.4]);
        S2.setAttribute("d", `M${f(ank[0] - 2.6)} ${f(ank[1] + 0.6)} L${f(ank[0] + 4.4)} ${f(ank[1] + 0.6)} Q${f(ank[0] + 5.4)} ${f(ank[1] + 2.6)} ${f(ank[0] + 3)} ${f(ank[1] + 2.8)} L${f(ank[0] - 2.4)} ${f(ank[1] + 2.8)}Z`);
      });
      const sh = [44.6, 43 + bob];
      torso.setAttribute("d", `M${f(hip[0] - 3.6)} ${f(hip[1] + 2)} Q${f(hip[0] - 4.4)} ${f(hip[1] - 14)} ${f(sh[0] - 6)} ${f(sh[1] + 1)} Q${f(sh[0] - 1)} ${f(sh[1] - 3.4)} ${f(sh[0] + 3.4)} ${f(sh[1] + 1.6)} Q${f(sh[0] - 2)} ${f(hip[1] - 12)} ${f(hip[0] + 6)} ${f(hip[1] + 2)}Z`);
      collarB.setAttribute("d", `M${f(sh[0] - 2)} ${f(sh[1] - 1)} l3 1.6`);
      collarB.setAttribute("stroke", rgb(P3.paper));
      const hc = [sh[0] + 4.2, sh[1] - 9.4];
      head.setAttribute("cx", f(hc[0]));
      head.setAttribute("cy", f(hc[1]));
      capC.setAttribute("d", `M${f(hc[0] - 4.6)} ${f(hc[1] - 1.6)} Q${f(hc[0] - 4.4)} ${f(hc[1] - 7)} ${f(hc[0] + 0.4)} ${f(hc[1] - 6.8)} Q${f(hc[0] + 4.8)} ${f(hc[1] - 6.4)} ${f(hc[0] + 4.6)} ${f(hc[1] - 2)} L${f(hc[0] + 8)} ${f(hc[1] - 1.2)} L${f(hc[0] + 4.4)} ${f(hc[1] - 0.6)}Z`);
      const grip = [55.4, 69.6];
      arm.draw([[sh[0], sh[1] + 2], joint([sh[0], sh[1] + 2], grip, 11.5, 11.5, -1), grip], [0.2, 0.4]);
      handC.setAttribute("cx", grip[0]);
      handC.setAttribute("cy", grip[1]);
      bag.setAttribute("fill", fillOf("#4a3a2c", P3));
      if (ringT >= 0) {
        ringT += dt;
        if (ringT > 0.9) ringT = -1;
      }
      const rr = ringT >= 0 ? ringT : 0;
      rings.setAttribute("d", ringT >= 0 ? [5, 9].map((r) => `M${57.8 - r * 0.6} ${f(64 - r * 0.5)} Q57.8 ${f(64 - r * 1.1)} ${57.8 + r * 0.6} ${f(64 - r * 0.5)}`).join(" ") : "");
      rings.setAttribute("opacity", f(1 - rr));
      bell.setAttribute("transform", ringT >= 0 ? `rotate(${f(Math.sin(rr * 60) * 14 * (1 - rr))} 57.8 66.6)` : "");
      const on2 = smooth(0.35, 0.6, P3.lamp);
      lamp.style.fill = rgb(mix(P3.paper, hex("#fff1c2"), on2));
      const [lx, ly] = world(this.x, this.y, dir, 85, 86);
      beamGlow.setAttribute("cx", f(lx));
      beamGlow.setAttribute("cy", f(ly));
      beamGlow.setAttribute("opacity", f(on2));
      beam.setAttribute("d", `M${f(lx)} ${f(ly - 1)} L${f(lx + dir * 70)} ${f(this.y - 5)} L${f(lx + dir * 70)} ${f(this.y + 6)} L${f(lx)} ${f(ly + 1)}Z`);
      beam.setAttribute("opacity", f(on2 * 0.7));
    },
    remove() {
      g.remove();
      beam.remove();
      beamGlow.remove();
    }
  };
}
function createKid(parent, glow2, { dir = 1, x, y }) {
  const g = el("g", { style: "cursor:pointer" }, parent);
  const T = 0.5, STRIDE = 8, DUTY = 0.36;
  const speed = 2 * STRIDE / (DUTY * T) * FS;
  const legs = [0, 1].map(() => ({ L: limb(g, 3.6), S: blot(g) }));
  const farArm = limb(g, 3);
  const shorts = el("path", { fill: "#33465e", stroke: "currentColor", "stroke-width": PEN }, g);
  const shirt = el("path", { fill: "url(#v-stripes)", stroke: "currentColor", "stroke-width": PEN }, g);
  const head = el("ellipse", { rx: 6.4, ry: 6.9, fill: PAPER, stroke: "currentColor", "stroke-width": PEN }, g);
  const hair = blot(g);
  const hat = el("path", { fill: "#e6cf8e", stroke: "currentColor", "stroke-width": PEN * 0.8 }, g);
  const band = el("path", { fill: "#b3412d" }, g);
  const arm = limb(g, 3);
  const stick = pen(g, PEN * 0.7);
  const wheel = el("g", {}, g);
  const blades = ["#d4552f", "#3f6ea8", "#e3b33d", "#4e8a5a"].map((c, k) => el("path", { d: "M0 0 L0 -7.6 Q4.8 -6.2 4.8 -3.2Z", transform: `rotate(${k * 90})`, fill: c, stroke: "currentColor", "stroke-width": PEN * 0.5, "stroke-linejoin": "round" }, wheel));
  const pinDot = el("circle", { r: 1, fill: "currentColor" }, wheel);
  const footKey = (u) => {
    u = (u % 1 + 1) % 1;
    if (u < DUTY) return { x: STRIDE - 2 * STRIDE * u / DUTY, y: 0 };
    const s = (u - DUTY) / (1 - DUTY);
    const xs = s * s * s * (10 - 15 * s + 6 * s * s);
    return { x: -STRIDE + 2 * STRIDE * xs - 3.5 * Math.sin(Math.PI * Math.min(1, s * 1.6)), y: -12 * Math.pow(Math.sin(Math.PI * Math.pow(s, 0.7)), 1.1) };
  };
  let ph = rnd(0, 1), spin = 0, hopT = -1;
  return {
    g,
    x,
    y,
    dir,
    done: false,
    poke() {
      if (hopT < 0) hopT = 0;
    },
    draw(t, dt, P3, wind2) {
      ph += dt / T;
      this.x += dir * speed * dt;
      if (this.x < -60 || this.x > 1020) this.done = true;
      let hop = 0;
      if (hopT >= 0) {
        hopT += dt;
        hop = Math.sin(Math.PI * Math.min(1, hopT / 0.55)) * 14;
        if (hopT > 0.55) hopT = -1;
      }
      place(g, this.x, this.y - hop * FS, dir);
      const bounce = -3 * Math.pow(Math.abs(Math.sin(2 * Math.PI * ph + 0.6)), 1.4) + 0.8;
      const hip = [40, 94 + bounce];
      [footKey(ph), footKey(ph + 0.5)].forEach((k, i) => {
        const a = [40 + k.x, 118 + k.y];
        legs[i].L.draw([hip, joint(hip, a, 13, 13, 1), a], [0.2, 0.4]);
        legs[i].S.setAttribute("d", `M${f(a[0] - 2)} ${f(a[1])} L${f(a[0] + 4)} ${f(a[1])} Q${f(a[0] + 5)} ${f(a[1] + 2)} ${f(a[0] + 3)} ${f(a[1] + 2)} L${f(a[0] - 2)} ${f(a[1] + 2)}Z`);
      });
      g.appendChild(legs[footKey(ph).x > footKey(ph + 0.5).x ? 0 : 1].L.g);
      g.insertBefore(farArm.g, shorts);
      const sh = [47, 72.6 + bounce];
      shorts.setAttribute("d", `M34.6 ${f(hip[1] - 4)} L46 ${f(hip[1] - 4)} L47 ${f(hip[1] + 4)} L41 ${f(hip[1] + 4.6)} L40 ${f(hip[1] + 1)} L37.6 ${f(hip[1] + 4.6)} L33.8 ${f(hip[1] + 3.6)}Z`);
      shirt.setAttribute("d", `M35 ${f(hip[1] - 3.6)} Q34.2 ${f(sh[1] + 6)} ${f(sh[0] - 6)} ${f(sh[1])} Q${f(sh[0])} ${f(sh[1] - 2.6)} ${f(sh[0] + 3)} ${f(sh[1] + 1)} Q47.4 ${f(sh[1] + 10)} 46.4 ${f(hip[1] - 3.6)}Z`);
      const hc = [sh[0] + 2.4, sh[1] - 11];
      head.setAttribute("cx", f(hc[0]));
      head.setAttribute("cy", f(hc[1]));
      hair.setAttribute("d", `M${f(hc[0] - 6.2)} ${f(hc[1] + 1)} Q${f(hc[0] - 6.6)} ${f(hc[1] - 6)} ${f(hc[0])} ${f(hc[1] - 6.6)} Q${f(hc[0] - 3)} ${f(hc[1] - 2)} ${f(hc[0] - 6.2)} ${f(hc[1] + 1)}Z`);
      hat.setAttribute("d", `M${f(hc[0] - 12)} ${f(hc[1] - 4)} Q${f(hc[0])} ${f(hc[1] - 8)} ${f(hc[0] + 12)} ${f(hc[1] - 4)} Q${f(hc[0])} ${f(hc[1] - 1)} ${f(hc[0] - 12)} ${f(hc[1] - 4)}Z M${f(hc[0] - 5.6)} ${f(hc[1] - 5.4)} Q${f(hc[0] - 5)} ${f(hc[1] - 12)} ${f(hc[0])} ${f(hc[1] - 12)} Q${f(hc[0] + 5)} ${f(hc[1] - 12)} ${f(hc[0] + 5.6)} ${f(hc[1] - 5.6)}Z`);
      band.setAttribute("d", `M${f(hc[0] - 5.5)} ${f(hc[1] - 7.6)} L${f(hc[0] + 5.5)} ${f(hc[1] - 7.6)} L${f(hc[0] + 5.6)} ${f(hc[1] - 5.8)} L${f(hc[0] - 5.6)} ${f(hc[1] - 5.8)}Z`);
      const swing = Math.sin(2 * Math.PI * ph) * 52;
      const fsh = [sh[0] - 2.5, sh[1] + 1.5];
      const fe = [fsh[0] + Math.sin(swing * RAD) * 8, fsh[1] + Math.cos(swing * RAD) * 8];
      farArm.draw([fsh, fe, [fe[0] + Math.sin((swing - 50) * RAD) * 8, fe[1] + Math.cos((swing - 50) * RAD) * 8]], [0.2, 0.4]);
      const hand = [56, sh[1] - 5];
      arm.draw([[sh[0], sh[1] + 1.5], [sh[0] + 4.6, sh[1] + 5], hand], [0.2, 0.4]);
      const top = [hand[0] + 3, hand[1] - 22];
      stick.setAttribute("d", `M${hand[0] - 0.6} ${f(hand[1] + 2)} L${f(top[0])} ${f(top[1])}`);
      spin += (8 + speed * 0.12 + Math.abs(wind2) * 6 + (hopT >= 0 ? 30 : 0)) * dt;
      wheel.setAttribute("transform", `translate(${f(top[0])} ${f(top[1])}) rotate(${f(spin * 57.3)})`);
      blades.forEach((b, k) => b.setAttribute("fill", fillOf(["#d4552f", "#3f6ea8", "#e3b33d", "#4e8a5a"][k], P3)));
      shorts.setAttribute("fill", fillOf("#33465e", P3));
      hat.setAttribute("fill", fillOf("#e6cf8e", P3));
    },
    remove() {
      g.remove();
    }
  };
}
function createBoat(parent, glow2, { onRipple }) {
  const g = el("g", { style: "cursor:pointer" }, parent);
  const Y = WATER + 30;
  const hull = el("path", { fill: "#8b6a48", stroke: "currentColor", "stroke-width": PEN }, g);
  const planks = pen(g, PEN * 0.45);
  const cargo = el("g", {}, g);
  const bales = [[120, 106], [146, 106], [172, 106], [133, 94], [159, 94]].map(([bx, by]) => {
    const n = el("path", { d: `M${bx - 12} ${by} Q${bx - 12} ${by - 6} ${bx} ${by - 6.5} Q${bx + 12} ${by - 6} ${bx + 12} ${by} Q${bx + 12} ${by + 6} ${bx} ${by + 6.5} Q${bx - 12} ${by + 6} ${bx - 12} ${by}Z`, fill: "#e2cf95", stroke: "currentColor", "stroke-width": PEN * 0.8 }, cargo);
    pen(cargo, PEN * 0.45).setAttribute("d", `M${bx - 6} ${by - 6} Q${bx - 7.4} ${by} ${bx - 6} ${by + 6} M${bx + 6} ${by - 6} Q${bx + 7.4} ${by} ${bx + 6} ${by + 6} M${bx - 12} ${by} L${bx + 12} ${by}`);
    return n;
  });
  const post = pen(g, PEN * 0.9);
  const lan = el("path", { stroke: "currentColor", "stroke-width": PEN * 0.7 }, g);
  const lanGlow = el("circle", { r: 26, fill: "url(#v-warmglow)", opacity: 0 }, glow2);
  const man = el("g", {}, g);
  const legs = [limb(man, 4.2), limb(man, 4.2)];
  legs.forEach((l) => solid(l, "#2b3446"));
  const coat = el("path", { fill: "#34507a", stroke: "currentColor", "stroke-width": PEN }, man);
  const coatMark = pen(man, PEN * 0.5);
  const head = el("ellipse", { rx: 4, ry: 4.8, fill: PAPER, stroke: "currentColor", "stroke-width": PEN }, man);
  const kasa = el("path", { fill: "#cdb57a", stroke: "currentColor", "stroke-width": PEN * 0.8 }, man);
  const kasaL = pen(man, PEN * 0.4);
  const arms = [limb(man, 3.4), limb(man, 3.4)];
  const pole = pen(g, PEN * 1.4);
  const poleWet = el("path", { stroke: "currentColor", "stroke-width": PEN * 0.9, "stroke-dasharray": "2 2.4", fill: "none", opacity: 0.6 }, g);
  const notes = el("g", {}, g);
  let X = 140, anchor = null, ph = 0, songT = -1, lastTip = [40, 160];
  const noteN = [];
  const T = 3.6;
  const lean = curve([[0, -4], [0.45, 26], [0.62, 14], [0.8, 2]], 1);
  return {
    g,
    get x() {
      return X;
    },
    poke() {
      if (songT < 0) {
        songT = 0;
        for (let i = 0; i < 4; i++) noteN.push({ t: -i * 0.35, x0: rnd(-4, 4), n: el("text", { "font-size": 11, fill: "currentColor", "font-family": "serif" }, notes) });
        noteN.slice(-4).forEach((n, i) => n.n.textContent = i % 2 ? "\u266A" : "\u266B");
      }
    },
    draw(t, dt, P3, wind2) {
      ph = (ph + dt / T) % 1;
      const push = ph > 0.1 && ph < 0.62 ? Math.sin(Math.PI * (ph - 0.1) / 0.52) : 0;
      const v = 7 + 15 * push;
      X += v * dt;
      if (X > 1120) {
        X = -170;
        anchor = null;
      }
      g.setAttribute("transform", `translate(${f(X)} ${f(Y - 120 * FS + Math.sin(t * 1.4) * 0.6)}) scale(${FS}) translate(-40 0)`);
      hull.setAttribute("d", "M14 112 L232 112 Q250 110 258 96 Q252 116 236 124 L30 124 Q18 122 14 112Z");
      hull.setAttribute("fill", fillOf("#8b6a48", P3));
      planks.setAttribute("d", "M18 116 L240 116 M24 120 L236 120 M60 112 L60 124 M110 112 L110 124 M200 112 L200 124");
      bales.forEach((b) => b.setAttribute("fill", fillOf("#e2cf95", P3)));
      post.setAttribute("d", "M244 112 L244 86 Q244 82 248 82");
      const on2 = smooth(0.3, 0.55, P3.lamp);
      lan.setAttribute("d", "M245 84 L251 84 Q253 89 251 94 L245 94 Q243 89 245 84Z");
      lan.setAttribute("fill", rgb(mix(P3.paper, hex("#ffd38a"), on2)));
      const lw = [X + (248 - 40) * FS, Y - 120 * FS + 89 * FS];
      lanGlow.setAttribute("cx", f(lw[0]));
      lanGlow.setAttribute("cy", f(lw[1]));
      lanGlow.setAttribute("opacity", f(on2));
      const ln = lean(ph) * RAD;
      const hip = [40, 86];
      legs[0].draw([hip, [44 + Math.sin(ln) * 6, 99], [46, 111]], [0.2, 0.4]);
      legs[1].draw([hip, [36, 99], [32, 111]], [0.2, 0.4]);
      const sh = [hip[0] + Math.sin(ln) * 22, hip[1] - Math.cos(ln) * 22];
      coat.setAttribute("d", `M${f(hip[0] - 5)} ${f(hip[1] + 4)} L${f(sh[0] - 5)} ${f(sh[1] + 1)} Q${f(sh[0])} ${f(sh[1] - 2.6)} ${f(sh[0] + 5)} ${f(sh[1] + 1)} L${f(hip[0] + 6)} ${f(hip[1] + 4)}Z`);
      coat.setAttribute("fill", fillOf("#34507a", P3));
      coatMark.setAttribute("d", `M${f((hip[0] + sh[0]) / 2 - 3)} ${f((hip[1] + sh[1]) / 2)} l6 0`);
      coatMark.setAttribute("stroke", rgb(P3.paper));
      const hc = [sh[0] + Math.sin(ln) * 9 + 1, sh[1] - Math.cos(ln) * 9];
      head.setAttribute("cx", f(hc[0]));
      head.setAttribute("cy", f(hc[1]));
      kasa.setAttribute("d", `M${f(hc[0] - 15)} ${f(hc[1] - 1)} L${f(hc[0] + 0.5)} ${f(hc[1] - 12)} L${f(hc[0] + 16)} ${f(hc[1] - 1)} Q${f(hc[0])} ${f(hc[1] - 3.6)} ${f(hc[0] - 15)} ${f(hc[1] - 1)}Z`);
      kasa.setAttribute("fill", fillOf("#cdb57a", P3));
      kasaL.setAttribute("d", [-10, -5, 0, 5, 10].map((k2) => `M${f(hc[0] + 0.5)} ${f(hc[1] - 11)} L${f(hc[0] + k2)} ${f(hc[1] - 2.6)}`).join(" "));
      const toLocal = (wx) => (wx - X) / FS + 40;
      const bed = Y - 120 * FS + 160 * FS;
      let tip;
      if (ph < 0.62) {
        if (!anchor) {
          anchor = X + (100 - 40) * FS;
          onRipple(anchor, WATER + 30);
        }
        tip = [toLocal(anchor), 160];
        lastTip = tip;
      } else {
        anchor = null;
        const u = (ph - 0.62) / 0.38;
        tip = [lerp(lastTip[0], 100, ease(u)), 160 - 58 * Math.sin(Math.PI * u)];
      }
      const hiHand = [sh[0] + 9, sh[1] + 4 + lean(ph) * 0.2];
      const dirx = hiHand[0] - tip[0], diry = hiHand[1] - tip[1], dl = Math.hypot(dirx, diry);
      const top = [hiHand[0] + dirx / dl * 46, hiHand[1] + diry / dl * 46];
      const loHand = [hiHand[0] - dirx / dl * 13, hiHand[1] - diry / dl * 13];
      arms[0].draw([[sh[0] + 1, sh[1] + 2], joint([sh[0] + 1, sh[1] + 2], hiHand, 10, 10, 1), hiHand], [0.2, 0.3]);
      arms[1].draw([[sh[0] - 1, sh[1] + 2], joint([sh[0] - 1, sh[1] + 2], loHand, 10, 11, 1), loHand], [0.2, 0.3]);
      const wl = (WATER - (Y - 120 * FS)) / FS;
      const k = (wl - top[1]) / (tip[1] - top[1]);
      const surf = k > 0 && k < 1 ? [lerp(top[0], tip[0], k), wl] : tip;
      pole.setAttribute("d", `M${pt(top)} L${pt(surf)}`);
      poleWet.setAttribute("d", k > 0 && k < 1 ? `M${pt(surf)} L${pt(tip)}` : "");
      if (songT >= 0) songT += dt;
      if (songT > 3.4) songT = -1;
      for (let i = noteN.length - 1; i >= 0; i--) {
        const n = noteN[i];
        n.t += dt;
        if (n.t < 0) {
          n.n.setAttribute("opacity", 0);
          continue;
        }
        n.n.setAttribute("x", f(hc[0] + 6 + n.x0 + n.t * 10));
        n.n.setAttribute("y", f(hc[1] - 10 - n.t * 18 + Math.sin(n.t * 6) * 2));
        n.n.setAttribute("opacity", f(Math.max(0, 1 - n.t / 1.8)));
        if (n.t > 1.8) {
          n.n.remove();
          noteN.splice(i, 1);
        }
      }
    }
  };
}

// critters.ts
var L2 = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
var POSES = {
  sleep: { S: [-7, -6.4], H: [7, -6.6], Bc: [0, -9.4], C: [-9, -0.2], Bt: [9.6, -0.2], hd: [-10.6, -3.6], tilt: 30, ear: 0.4, eye: 0, mouth: 0, F1: [-11, 0], F2: [-8.6, 0], T0: [9, -2], T1: [6, 3], T2: [-5, 1.2], paw: 0 },
  sit: { S: [-4.4, -12.6], H: [4.6, -5.4], Bc: [2.2, -11.4], C: [-6.4, -1.4], Bt: [6.6, -0.2], hd: [-5.4, -17.6], tilt: 0, ear: 1, eye: 1, mouth: 0, F1: [-5.6, 0], F2: [-3.4, 0], T0: [6.6, -1], T1: [13, 0.6], T2: [15.6, -4.4], paw: 0 },
  yawn: { S: [-4.4, -12.8], H: [4.6, -5.4], Bc: [2.2, -11.6], C: [-6.4, -1.4], Bt: [6.6, -0.2], hd: [-5.6, -18.6], tilt: -18, ear: 0.6, eye: 0, mouth: 1, F1: [-5.6, 0], F2: [-3.4, 0], T0: [6.6, -1], T1: [13, 0.6], T2: [15.6, -4.4], paw: 0 },
  stretch: { S: [-9.4, -4.6], H: [5.4, -11.6], Bc: [-1, -8.6], C: [-11, -1], Bt: [7.4, -3.6], hd: [-15.6, -6.6], tilt: -6, ear: 0.7, eye: 0.3, mouth: 0, F1: [-17.6, 0], F2: [-15, 0], T0: [7, -9.6], T1: [10, -17], T2: [8.6, -22], paw: 0 },
  groom: { S: [-4.4, -12.6], H: [4.6, -5.4], Bc: [2.2, -11.4], C: [-6.4, -1.4], Bt: [6.6, -0.2], hd: [-5.2, -16.4], tilt: 22, ear: 1, eye: 0, mouth: 0, F1: [-5.6, 0], F2: [-6.6, -13.6], T0: [6.6, -1], T1: [13, 0.6], T2: [15.6, -3.4], paw: 1 }
};
var lerpPose = (a, b, t) => {
  const o = {};
  for (const k in a) o[k] = Array.isArray(a[k]) ? L2(a[k], b[k], t) : lerp(a[k], b[k], t);
  return o;
};
var SEQ = [["sit", 0.7], ["yawn", 0.9], ["sit", 0.4], ["stretch", 1.5], ["sit", 0.6], ["groom", 0.45], ["sit", 0.35], ["groom", 0.45], ["sit", 0.35], ["groom", 0.45], ["sit", 0.9], ["sleep", 1.1]];
function createCat(parent, glow2, { x, y }) {
  const g = el("g", { style: "cursor:pointer" }, parent);
  const tailOut = el("path", { fill: "none", stroke: "currentColor", "stroke-width": 3.1, "stroke-linecap": "round" }, g);
  const tailIn = el("path", { fill: "none", stroke: "#d08a4a", "stroke-width": 1.5, "stroke-linecap": "round" }, g);
  const legs = pen(g, SP * 1.6);
  const body = shape(g, SP);
  const patch = el("path", { fill: "#d08a4a" }, g), patch2 = blot(g);
  const paws = shape(g, SP * 0.7);
  const headG = el("g", {}, g);
  const ears = el("path", { fill: PAPER, stroke: "currentColor", "stroke-width": SP * 0.9, "stroke-linejoin": "round" }, headG);
  el("ellipse", { cx: 0, cy: 0, rx: 4.6, ry: 4.1, fill: PAPER, stroke: "currentColor", "stroke-width": SP }, headG);
  const capPatch = blot(headG);
  const face = pen(headG, SP * 0.6);
  const mouth = el("path", { fill: "#6a2a2a", stroke: "currentColor", "stroke-width": SP * 0.5 }, headG);
  const eyesGlow = [0, 1].map(() => el("circle", { r: 2.4, fill: "url(#v-cateye)", opacity: 0 }, glow2));
  let seqT = -1, idle = 0, flick = 0, ear = 0;
  const hit = el("rect", { x: x - 20, y: y - 26, width: 42, height: 28, fill: "transparent" }, g);
  return {
    g,
    hit,
    poke() {
      if (seqT < 0) seqT = 0;
    },
    draw(t, dt, P3) {
      const awakeAtNight = P3.night > 0.55;
      let pose;
      if (seqT >= 0) {
        seqT += dt;
        let acc = 0, prev = awakeAtNight ? "sit" : "sleep", cur = SEQ[0][0], u = 1;
        for (let i = 0; i < SEQ.length; i++) {
          const [name, d] = SEQ[i];
          if (seqT < acc + d) {
            cur = name;
            u = (seqT - acc) / d;
            break;
          }
          acc += d;
          prev = name;
          cur = name;
        }
        if (seqT > SEQ.reduce((a, s) => a + s[1], 0)) seqT = -1;
        pose = lerpPose(POSES[prev], POSES[cur], ease(Math.min(1, u * 1.6)));
      } else pose = lerpPose(POSES.sleep, POSES.sit, ease(clamp((P3.night - 0.4) * 4, 0, 1)));
      const breathe = Math.sin(t * 1.8) * 0.35;
      idle -= dt;
      if (idle < 0) {
        idle = rnd(2, 6);
        if (Math.random() < 0.6) flick = 1;
        else ear = 1;
      }
      flick = Math.max(0, flick - dt * 1.6);
      ear = Math.max(0, ear - dt * 3);
      const X = (p) => x + p[0], Y = (p) => y + p[1];
      const S2 = [X(pose.S), Y(pose.S) - breathe], H2 = [X(pose.H), Y(pose.H) - breathe * 0.6], Bc = [X(pose.Bc), Y(pose.Bc) - breathe * 1.2];
      const C = [X(pose.C), Y(pose.C)], Bt = [X(pose.Bt), Y(pose.Bt)];
      body.setAttribute("d", `M${pt(C)} Q${f(C[0] - 2)} ${f((C[1] + S2[1]) / 2)} ${pt(S2)} Q${pt(Bc)} ${pt(H2)} Q${f(H2[0] + 4)} ${f((H2[1] + Bt[1]) / 2)} ${pt(Bt)} Q${f((Bt[0] + C[0]) / 2)} ${f(Math.max(Bt[1], C[1]) + 1)} ${pt(C)}Z`);
      const mid = L2(S2, H2, 0.55);
      patch.setAttribute("d", `M${f(mid[0] - 3.4)} ${f(mid[1] + 0.6)} Q${f(mid[0])} ${f(mid[1] - 3)} ${f(mid[0] + 4)} ${f(mid[1] + 0.2)} Q${f(mid[0] + 1)} ${f(mid[1] + 3.6)} ${f(mid[0] - 3.4)} ${f(mid[1] + 0.6)}Z`);
      patch.setAttribute("fill", rgb(mix(hex("#d08a4a"), hex("#5a3a28"), P3.inkT * 0.6)));
      tailIn.setAttribute("stroke", rgb(mix(hex("#d08a4a"), hex("#5a3a28"), P3.inkT * 0.6)));
      const hb = L2(S2, H2, 0.85);
      patch2.setAttribute("d", oval(hb[0], hb[1] + 1.4, 1.8, 1.2));
      const fl = Math.sin(t * 14) * 2.5 * flick;
      const T0 = [X(pose.T0), Y(pose.T0)], T1 = [X(pose.T1), Y(pose.T1)], T2 = [X(pose.T2) + fl, Y(pose.T2) - fl * 0.4];
      tailOut.setAttribute("d", `M${pt(T0)} Q${pt(T1)} ${pt(T2)}`);
      tailIn.setAttribute("d", `M${pt(T0)} Q${pt(T1)} ${pt(T2)}`);
      const sh = [S2[0] + 1.4, S2[1] + 4];
      const F1 = [X(pose.F1), Y(pose.F1)], F2 = [X(pose.F2), Y(pose.F2)];
      legs.setAttribute("d", `M${pt(sh)} L${pt(F1)} M${f(sh[0] + 1.6)} ${f(sh[1])} L${pt(F2)}`);
      paws.setAttribute("d", `${oval(F1[0] - 0.4, F1[1] - 0.6, 1.5, 0.9)} ${oval(F2[0] - 0.4, F2[1] - 0.6, 1.5, 0.9)}`);
      const hd = [X(pose.hd), Y(pose.hd) - breathe];
      headG.setAttribute("transform", `translate(${pt(hd)}) rotate(${f(pose.tilt)})`);
      const e = pose.ear, tw = ear * 0.6;
      ears.setAttribute("d", `M-4 -2 L${f(-4.2 - (1 - e) * 1.4)} ${f(-7.4 + (1 - e) * 3 + tw)} L-1 -3.6Z M1.4 -3.8 L${f(3.6 + (1 - e) * 1.6)} ${f(-7.2 + (1 - e) * 3)} L4.4 -1.8Z`);
      capPatch.setAttribute("d", "M-4.4 -1.2 Q-3.6 -3.8 -0.6 -4 Q-1.6 -1.6 -4.4 -1.2Z");
      const open = pose.eye;
      face.setAttribute("d", (open > 0.5 ? "M-2.6 -0.4 a0.6 0.8 0 1 0 0.1 0 M1 -0.4 a0.6 0.8 0 1 0 0.1 0" : "M-3.2 -0.2 q0.7 0.7 1.4 0 M0.6 -0.2 q0.7 0.7 1.4 0") + " M-1.2 1.4 l0.6 0.5 l0.6 -0.5 M-4.4 1.6 l-3.6 -0.4 M-4.4 2.4 l-3.4 0.8 M2.6 1.8 l3.4 -0.2");
      mouth.setAttribute("d", pose.mouth > 0.1 ? oval(-0.6, 2.6, 1.2 * pose.mouth, 1.5 * pose.mouth) : "");
      eyesGlow.forEach((n, i) => {
        n.setAttribute("cx", f(hd[0] - 2.2 + i * 3.6));
        n.setAttribute("cy", f(hd[1] - 0.4));
        n.setAttribute("opacity", f(P3.night * (open > 0.5 ? 0.9 : 0)));
      });
    }
  };
}
function createSparrows(parent, { wireY, count = 7 }) {
  const g = el("g", {}, parent);
  const spots = [540, 575, 610, 660, 720, 790, 850, 905];
  const birds = Array.from({ length: count }, (_, i) => {
    const bg = el("g", {}, g);
    return {
      x: spots[i] + rnd(-6, 6),
      dir: Math.random() < 0.5 ? -1 : 1,
      state: "perch",
      t: 0,
      next: rnd(1, 5),
      hopT: -1,
      tail: 0,
      peck: 0,
      g: bg,
      tailN: pen(bg, SP * 0.9),
      body: shape(bg, SP * 0.7),
      cap: el("path", { fill: "#7a5a3c" }, bg),
      cheek: blot(bg),
      beak: blot(bg),
      wing: pen(bg, SP * 0.5),
      legs: pen(bg, SP * 0.4),
      wings: pen(bg, SP * 0.8),
      fx: 0,
      fy: 0,
      path: null,
      hopFrom: 0,
      hopTo: 0
    };
  });
  const hit = el("path", { fill: "transparent", style: "cursor:pointer", d: "" }, g);
  const flush = () => birds.forEach((b) => {
    if (b.state === "perch") takeOff(b, false);
  });
  function takeOff(b, away) {
    const y0 = wireY(b.x) - 2.5;
    const nx = away ? Math.random() < 0.5 ? -40 : 1e3 : clamp(spots[Math.random() * spots.length | 0] + rnd(-8, 8), 520, 930);
    const up = rnd(40, 80);
    b.path = { p0: [b.x, y0], c1: [b.x + rnd(-80, 80), y0 - up], c2: [nx + rnd(-60, 60), y0 - up * rnd(0.6, 1.2)], p1: [nx, away ? rnd(20, 80) : wireY(nx) - 2.5], dur: rnd(1.8, 3.2), away };
    b.state = "fly";
    b.t = 0;
  }
  const bez = (p, u) => {
    const a = 1 - u;
    return [0, 1].map((k) => a * a * a * p.p0[k] + 3 * a * a * u * p.c1[k] + 3 * a * u * u * p.c2[k] + u * u * u * p.p1[k]);
  };
  return {
    g,
    hit,
    flush,
    draw(t, dt, P3) {
      const roost = P3.night > 0.5;
      hit.setAttribute("d", `M520 ${wireY(520) - 14} L940 ${wireY(940) - 14} L940 ${wireY(940) + 6} L520 ${wireY(520) + 6}Z`);
      birds.forEach((b, i) => {
        if (b.state === "perch" && roost) takeOff(b, true);
        if (b.state === "gone") {
          if (!roost && Math.random() < dt * 0.5) {
            b.x = spots[i];
            b.path = { p0: [rnd(0, 1) < 0.5 ? -30 : 990, rnd(30, 90)], c1: [rnd(300, 700), rnd(40, 100)], c2: [b.x + rnd(-60, 60), wireY(b.x) - 50], p1: [b.x, wireY(b.x) - 2.5], dur: rnd(2.2, 3.4) };
            b.state = "fly";
            b.t = 0;
          }
          b.g.setAttribute("opacity", 0);
          return;
        }
        b.g.setAttribute("opacity", 1);
        let x, y, flying = false, ang = 0;
        if (b.state === "fly") {
          b.t += dt;
          const u = clamp(b.t / b.path.dur, 0, 1);
          [x, y] = bez(b.path, ease(u));
          const [x2] = bez(b.path, ease(Math.min(1, u + 0.02)));
          b.dir = x2 >= x ? 1 : -1;
          flying = u < 0.97;
          if (u >= 1) {
            if (b.path.away) {
              b.state = "gone";
            } else {
              b.state = "perch";
              b.x = x;
              b.next = rnd(0.6, 3);
            }
          }
        } else {
          b.next -= dt;
          if (b.next < 0) {
            b.next = rnd(0.8, 3.6);
            const r = Math.random();
            if (r < 0.35) {
              b.hopT = 0;
              b.hopFrom = b.x;
              b.hopTo = clamp(b.x + b.dir * rnd(4, 9), 520, 935);
            } else if (r < 0.6) b.dir *= -1;
            else if (r < 0.8) b.peck = 1;
            else b.tail = 1;
          }
          if (b.hopT >= 0) {
            b.hopT += dt / 0.22;
            b.x = lerp(b.hopFrom, b.hopTo, ease(Math.min(1, b.hopT)));
            if (b.hopT >= 1) b.hopT = -1;
          }
          x = b.x;
          y = wireY(b.x) - 2.5 - (b.hopT >= 0 ? Math.sin(Math.PI * b.hopT) * 3.2 : 0);
        }
        b.peck = Math.max(0, b.peck - dt * 2);
        b.tail = Math.max(0, b.tail - dt * 3);
        const d = b.dir, pk = Math.sin(Math.PI * b.peck) * 1.6;
        const X = (dx) => f(x + dx * d);
        b.body.setAttribute("d", oval(x, y - 2.8, 3.1, 2.4));
        b.cap.setAttribute("d", `M${X(0.8)} ${f(y - 5.6 + pk)} a2 1.8 0 0 1 ${f(3.6 * d)} 0Z`);
        b.cap.setAttribute("fill", rgb(mix(hex("#7a5a3c"), hex("#3a2c22"), P3.inkT * 0.5)));
        b.cheek.setAttribute("d", oval(x + 2.6 * d, y - 4.4 + pk, 0.6, 0.6));
        b.beak.setAttribute("d", `M${X(4.4)} ${f(y - 5.2 + pk)} L${X(6)} ${f(y - 4.8 + pk)} L${X(4.4)} ${f(y - 4.3 + pk)}Z`);
        const tf = Math.sin(b.tail * 20) * 1.6 * b.tail;
        b.tailN.setAttribute("d", `M${X(-2.4)} ${f(y - 2.6)} L${X(-6)} ${f(y - 0.6 - tf)}`);
        b.wing.setAttribute("d", flying ? "" : `M${X(-1.6)} ${f(y - 3.6)} Q${X(0.6)} ${f(y - 2.2)} ${X(-2.2)} ${f(y - 1.4)}`);
        b.legs.setAttribute("d", flying ? "" : `M${X(-0.4)} ${f(y - 0.6)} l0 1.2 M${X(0.8)} ${f(y - 0.6)} l0 1.2`);
        const fl = Math.sin(t * 34 + i) * 4;
        b.wings.setAttribute("d", flying ? `M${X(0)} ${f(y - 3.4)} L${X(-2)} ${f(y - 3.4 - fl)} M${X(0.6)} ${f(y - 3)} L${X(2.4)} ${f(y - 3 - fl * 0.8)}` : "");
      });
    }
  };
}
function createSwallows(parent) {
  const birds = [0, 1].map((i) => ({ n: blot(parent), a: rnd(0, 6), b: rnd(0, 6), sp: rnd(0.8, 1.1) * (i ? -1 : 1), lx: 0, ly: 0 }));
  return {
    draw(t, dt, P3) {
      birds.forEach((s) => {
        const tt = t * 0.32 * s.sp;
        const x = 480 + 440 * Math.sin(tt + s.a), y = 150 + 55 * Math.sin(tt * 2.3 + s.b) + 18 * Math.sin(tt * 5.1);
        const vx = x - (s.lx || x), vy = y - (s.ly || y);
        s.lx = x;
        s.ly = y;
        const ang = Math.atan2(vy, vx) * 57.3;
        const flap = Math.sin(t * 22 + s.a) > 0.4 ? 0.55 : 1;
        s.n.setAttribute("d", `M7 0 L2.4 -1 L${-3} ${-6.4 * flap} L-0.6 -1.2 L-7 -2.6 L-4.6 0 L-7 2.6 L-0.6 1.2 L${-3} ${6.4 * flap} L2.4 1Z`);
        s.n.setAttribute("transform", `translate(${f(x)} ${f(y)}) rotate(${f(ang)}) scale(0.8)`);
        s.n.setAttribute("opacity", f(1 - P3.night));
      });
    }
  };
}
function createPetals(parent, { blossoms, canal: canal2 }) {
  const petals2 = [];
  const add = (burst) => {
    const [x, y] = blossoms[Math.random() * blossoms.length | 0];
    const toWater = Math.random() < 0.35;
    petals2.push({
      x,
      y,
      vx: rnd(-6, 6),
      vy: burst ? rnd(-10, 2) : rnd(2, 7),
      r: rnd(0, 6),
      ph: rnd(0, 6),
      life: 0,
      rest: 0,
      land: toWater ? WATER + rnd(4, 40) : rnd(BASE + 2, EDGE - 2),
      toWater,
      n: el("path", { fill: "#f6dfe4", stroke: "currentColor", "stroke-width": SP * 0.4 }, parent)
    });
  };
  return {
    burst(n = 40) {
      for (let i = 0; i < n; i++) add(true);
    },
    draw(t, dt, P3, wind2) {
      if (Math.random() < dt * (1.4 + Math.abs(wind2) * 1.4)) add(false);
      for (let i = petals2.length - 1; i >= 0; i--) {
        const p = petals2[i];
        p.life += dt;
        if (p.y < p.land) {
          p.vy = lerp(p.vy, 11, dt * 1.4);
          p.x += (p.vx + wind2 * 22 + Math.sin(p.life * 2.6 + p.ph) * 9) * dt;
          p.y += p.vy * dt;
          p.r += dt * 3.4;
        } else if (p.toWater) {
          canal2.floatPetal(p);
          p.n.remove();
          petals2.splice(i, 1);
          continue;
        } else p.rest += dt;
        const op = p.rest > 3 ? Math.max(0, 1 - (p.rest - 3)) : 1;
        const sx = Math.abs(Math.cos(p.r * 1.3)) * 0.8 + 0.25;
        p.n.setAttribute("d", `M${f(p.x - 1.8 * sx)} ${f(p.y)} Q${f(p.x)} ${f(p.y - 1.4)} ${f(p.x + 1.8 * sx)} ${f(p.y)} L${f(p.x + 1.2 * sx)} ${f(p.y + 0.4)} L${f(p.x + 1.8 * sx)} ${f(p.y + 0.9)} Q${f(p.x)} ${f(p.y + 1.6)} ${f(p.x - 1.8 * sx)} ${f(p.y)}Z`);
        p.n.setAttribute("transform", `rotate(${f(Math.sin(p.r) * 70)} ${f(p.x)} ${f(p.y)})`);
        p.n.setAttribute("opacity", f(op));
        p.n.setAttribute("fill", rgb(mix(hex("#f6dfe4"), hex("#8a7480"), P3.inkT * 0.6)));
        if (op <= 0 || p.x > W + 20 || p.x < -20) {
          p.n.remove();
          petals2.splice(i, 1);
        }
      }
    }
  };
}
function createSmoke(parent, [cx, cy]) {
  const puffs = [];
  let acc = 0;
  return {
    draw(t, dt, P3, wind2, tau2) {
      const firing = tau2 > 0.55 || tau2 < 0.08;
      acc += dt;
      if (firing && acc > 0.55) {
        acc = 0;
        puffs.push({ x: cx + rnd(-2, 2), y: cy, r: rnd(3, 4.5), life: 0, ph: rnd(0, 6), n: shape(parent, SP * 0.7) });
      }
      for (let i = puffs.length - 1; i >= 0; i--) {
        const p = puffs[i];
        p.life += dt;
        p.x += (4 + wind2 * 10 + Math.sin(p.life * 1.2 + p.ph) * 2) * dt;
        p.y -= (9 - p.life * 0.6) * dt;
        p.r += dt * 2.2;
        const pts = [];
        for (let k = 0; k <= 14; k++) {
          const a = k / 14 * Math.PI * 2;
          const rr = p.r * (1 + 0.16 * Math.sin(a * 3 + p.ph + p.life));
          pts.push([p.x + Math.cos(a) * rr, p.y + Math.sin(a) * rr * 0.8]);
        }
        p.n.setAttribute("d", "M" + pts.map(pt).join("L") + "Z");
        p.n.setAttribute("opacity", f(Math.max(0, 0.9 - p.life / 7)));
        if (p.life > 6.3) {
          p.n.remove();
          puffs.splice(i, 1);
        }
      }
    }
  };
}

// main.ts
var q = new URLSearchParams(location.search);
var svg = el("svg", {
  viewBox: `0 0 ${W} ${H}`,
  class: "village",
  role: "img",
  "aria-label": "An ink drawing of a Japanese street with machiya houses, a tea house and a public bath beside a canal, through day and night."
});
var ink = inkDefs(svg, "v");
document.querySelector("#village").appendChild(svg);
var defs = ink.defs;
var grad = (id, stops, attrs = {}) => {
  const g = el(attrs.radial ? "radialGradient" : "linearGradient", attrs.radial ? { id } : { id, x1: attrs.x1 ?? 0, y1: 0, x2: attrs.x2 ?? 1, y2: 0 }, defs);
  stops.forEach(([o, c, a]) => el("stop", { offset: o, "stop-color": c, "stop-opacity": a }, g));
};
grad("v-beamR", [[0, "#fff1c2", 0.55], [1, "#fff1c2", 0]]);
grad("v-beamL", [[0, "#fff1c2", 0], [1, "#fff1c2", 0.55]]);
grad("v-cateye", [[0, "#e8ff9a", 1], [1, "#c8ff6a", 0]], { radial: true });
var layer = (parent = svg, attrs = {}) => el("g", attrs, parent);
var skyL = layer();
var scene = layer(svg, { filter: ink.filter });
var back = layer(scene);
var birdsL = layer(scene);
var ground = layer(scene);
var houses = layer(scene);
var front = layer(scene);
var catL = layer(scene);
var walkers = layer(scene);
var canalL = layer(scene);
var boatL = layer(scene);
var willowL = layer(scene);
var petalL = layer(scene, { style: "pointer-events:none" });
var glow = layer(svg, { style: "mix-blend-mode:screen;pointer-events:none" });
var tau = q.has("tau") ? +q.get("tau") : q.has("start") ? +q.get("start") : 0.66;
var scrub = null;
var frozenTau = q.has("tau");
var DAY_SECONDS = q.has("day") ? +q.get("day") : 180;
var LIFE = q.has("life") ? +q.get("life") : 1;
var TRAFFIC = Math.max(1, Math.sqrt(180 / DAY_SECONDS));
var card = document.querySelector("#card");
if (q.has("capture")) document.body.classList.add("capture");
var wind = 0.3;
var windTarget = 0.3;
var lastX = null;
var lastT = 0;
svg.addEventListener("pointermove", (e) => {
  const now = performance.now();
  if (lastX !== null && !svg.classList.contains("scrubbing")) windTarget = clamp(windTarget + (e.clientX - lastX) / Math.max(8, now - lastT) * 0.8, -2.4, 2.4);
  lastX = e.clientX;
  lastT = now;
});
var on = (node, fn) => node.addEventListener("pointerdown", (e) => {
  e.stopPropagation();
  fn(e);
  hint.done();
});
var toSvg = (e) => {
  const p = svg.createSVGPoint();
  p.x = e.clientX;
  p.y = e.clientY;
  return p.matrixTransform(svg.getScreenCTM().inverse());
};
var sky = createSky(svg, skyL, defs, {
  onScrub: (v) => {
    scrub = v;
    if (v !== null) {
      tau = v;
      frozenTau = false;
      hint.done();
    }
  },
  onShoot: () => palette(tau).night > 0.4
});
var street = buildStreet({ back, houses, front, glow }, defs);
var canal = buildCanal({ ground, canalL, willowL, glow }, defs);
var smoke = createSmoke(back, street.chimney);
var sparrows = createSparrows(birdsL, { wireY: street.wireY });
var swallows = createSwallows(birdsL);
var petals = createPetals(petalL, { blossoms: street.blossoms, canal });
var cat = createCat(catL, glow, { x: 548, y: 330 });
var boat = createBoat(boatL, glow, { onRipple: (x, y) => canal.ring(x, y, 2) });
street.windows.forEach((w) => canal.addRefl(() => w.lit, (w.x0 + w.x1) / 2, Math.min(40, (w.x1 - w.x0) * 0.8)));
street.lanterns.forEach((l) => canal.addRefl(() => smooth(l.thr, l.thr + 0.2, P2.lamp), l.x, 8));
canal.addRefl(() => smooth(0.2, 0.45, P2.lamp), 446, 14);
street.lanterns.forEach((l) => {
  l.grp.style.cursor = "pointer";
  on(l.grp, () => l.poke());
});
street.norens.forEach((n) => {
  n.grp.style.cursor = "pointer";
  on(n.grp, () => n.poke());
});
var hits = layer(scene);
var hitPath = (d, title, fn) => {
  const n = el("path", { d, fill: "transparent", style: "cursor:pointer" }, hits);
  el("title", {}, n).textContent = title;
  on(n, fn);
  return n;
};
hitPath(street.shoji.hit, "Knock on the window", () => street.shoji.poke());
hitPath("M402 202 L422 202 L422 236 L402 236Z", "Ring the wind chime", () => street.furin.poke());
var shake = 0;
street.canopy.style.cursor = "pointer";
on(street.canopy, () => {
  shake = 1;
  petals.burst(46);
});
on(sparrows.hit, () => sparrows.flush());
on(cat.hit, () => cat.poke());
on(boat.g, () => boat.poke());
willowL.style.cursor = "pointer";
on(willowL, () => canal.willowPoke());
var waterHit = el("rect", { x: 0, y: WATER, width: W, height: H - WATER, fill: "transparent", style: "cursor:pointer" }, canalL);
on(waterHit, (e) => {
  const p = toSvg(e);
  canal.poke(p.x, p.y);
});
canalL.insertBefore(waterHit, canalL.children[2] || null);
var people = [];
var spawn = { kimono: 0, bike: 7, kid: 4 };
function addPerson(kind, x) {
  const dir = Math.random() < 0.5 ? 1 : -1;
  const sx = x ?? (dir > 0 ? -60 : W + 60);
  let p;
  if (kind === "kimono") p = createKimono(walkers, glow, { dir, x: sx, y: LANE.back + rnd(-1, 1), lantern: P2.lamp > 0.5 });
  if (kind === "bike") p = createCyclist(walkers, glow, { dir, x: sx, y: LANE.front + rnd(-1, 1) });
  if (kind === "kid") p = createKid(walkers, glow, { dir, x: sx, y: LANE.mid + rnd(-1, 1) });
  on(p.g, () => {
    p.poke();
    if (p.kind === "bike") setTimeout(() => sparrows.flush(), 150);
  });
  people.push(p);
}
var clock = document.querySelector("#clock");
var hintN = document.querySelector("#hint");
var hint = { shown: true, done() {
  if (this.shown) {
    this.shown = false;
    hintN.classList.add("gone");
  }
} };
setTimeout(() => hint.done(), 14e3);
var period = (h) => h < 4 ? "\u6DF1\u591C" : h < 6 ? "\u591C\u660E\u3051" : h < 10 ? "\u671D" : h < 15 ? "\u663C" : h < 17.5 ? "\u5348\u5F8C" : h < 19.5 ? "\u5915\u66AE\u308C" : "\u591C";
var P2 = palette(tau);
var started = false;
run((t, dt) => {
  dt = dt || 1 / 60;
  if (scrub === null && !frozenTau) tau = (tau + dt / DAY_SECONDS) % 1;
  P2 = palette(tau);
  svg.style.color = rgb(P2.ink);
  svg.style.setProperty("--paper", rgb(P2.paper));
  card.style.setProperty("--ink", rgb(P2.ink));
  windTarget = lerp(windTarget, 0.3 + 0.25 * Math.sin(t * 0.21) + 0.15 * Math.sin(t * 0.67), 0.012);
  wind = lerp(wind, windTarget, 0.05);
  sky.draw(tau, t, dt, P2, wind);
  street.applyRed(P2);
  const sinceDusk = (tau - 0.75 + 1) % 1;
  street.windows.forEach((w) => {
    let lit = smooth(w.thr, w.thr + 0.25, P2.lamp);
    if (w.lateOff < 9 && sinceDusk > w.lateOff - 0.75 && sinceDusk < 0.5) lit = 0;
    w.lit = lerp(w.lit, lit, 0.08);
    w.n.style.fill = rgb(mix(P2.paper, mix(hex("#ffd58a"), hex("#f0a24e"), w.warmth), w.lit * 0.92));
    w.glow.setAttribute("opacity", f(w.lit * 0.8));
  });
  const L = street.lamp, lampOn = smooth(0.2, 0.45, P2.lamp);
  L.node.style.fill = rgb(mix(P2.paper, hex("#fff1c9"), lampOn));
  L.cone.setAttribute("opacity", f(lampOn * 0.75));
  L.glow.setAttribute("opacity", f(lampOn));
  street.norens.forEach((n) => n.draw(t, dt, wind, tau, P2));
  street.lanterns.forEach((l) => l.draw(t, dt, wind, P2));
  street.furin.draw(t, dt, wind);
  street.shoji.draw(t, dt, P2);
  shake = Math.max(0, shake - dt * 1.5);
  street.canopy.setAttribute("transform", `translate(${f(Math.sin(t * 40) * shake * 2.4 + wind * 0.9)} ${f(Math.cos(t * 31) * shake * 1.2)})`);
  smoke.draw(t, dt, P2, wind, tau);
  sparrows.draw(t, dt, P2);
  swallows.draw(t, dt, P2);
  petals.draw(t, dt, P2, wind);
  cat.draw(t, dt, P2);
  canal.draw(t, dt, P2, wind, null, tau, lampOn);
  boat.draw(t, dt * LIFE, P2, wind);
  if (!started) {
    started = true;
    addPerson("kimono", 300);
    addPerson("kimono", 760);
    addPerson("bike", 560);
  }
  const dayish = tau > 0.28 && tau < 0.72, lateNight = tau > 0.96 || tau < 0.22;
  for (const k in spawn) {
    spawn[k] -= dt * TRAFFIC;
    if (spawn[k] < 0) {
      if (k === "kimono") {
        spawn[k] = rnd(10, 18);
        if (!lateNight || Math.random() < 0.3) addPerson("kimono");
      }
      if (k === "bike") {
        spawn[k] = rnd(9, 16);
        if (!lateNight) addPerson("bike");
      }
      if (k === "kid") {
        spawn[k] = rnd(14, 24);
        if (dayish) addPerson("kid");
      }
    }
  }
  for (let i = people.length - 1; i >= 0; i--) {
    const p = people[i];
    p.draw(t, dt * LIFE, P2, wind);
    if (p.done) {
      p.remove();
      people.splice(i, 1);
    } else if (p.ringing && Math.random() < dt * 4) sparrows.flush();
  }
  people.slice().sort((a, b) => a.y - b.y).forEach((p) => walkers.appendChild(p.g));
  const hrs = tau * 24, h = Math.floor(hrs), m = Math.floor((hrs - h) * 60);
  clock.innerHTML = `<b>${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}</b> <span>${period(hrs)}</span>`;
});
window.__village = { addPerson, setTau: (v) => {
  tau = v;
  frozenTau = true;
}, get tau() {
  return tau;
}, people, sparrows, cat, boat, canal, street, petals };
